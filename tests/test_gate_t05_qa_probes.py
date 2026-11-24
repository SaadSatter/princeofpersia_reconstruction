"""Gate 1 QA probes for T05 (macro layer and scripted versus baseline), commit 19b5da2.

Findings are marked xfail(strict=True, reason="GATE-T05-qa-<n>"); the rest pass.
Deterministic, offline.
"""

from __future__ import annotations

import copy
import random

import pytest

from agents.macros import MACROS, MacroController, MacroExecutor
from agents.versus_baseline import make_baseline
from pop import arena
from pop.seats import RandomController, WaitController
from pop.versus import VersusEpisode
from pop.versus_runner import VersusLimits, VersusRunner

SLOW = lambda: 0.0                                                    # noqa: E731


def _floor_cells(room):
    return [(room, 2, c) for c, ch in enumerate(arena.ROOMS[room][2]) if ch in "_tP"]


def _episode(a, b, posts=None, limit=3600):
    return lambda: VersusEpisode(arena.situation("A"), {"A": a, "B": b}, 0, limit,
                                 arena.GUARD_POSTS if posts is None else posts)


# --- the executor never sends an illegal input -----------------------------------
def test_qa_baseline_never_needs_a_fallback_over_randomised_duels_in_every_room():
    rng = random.Random(11)
    decisions = games = 0
    rooms_seen = set()
    for k in range(36):
        ra, rb = rng.sample(range(1, 7), 2)
        a = rng.choice(_floor_cells(ra)) + (rng.choice((-1, 1)),)
        b = rng.choice(_floor_cells(rb)) + (rng.choice((-1, 1)),)
        rooms_seen |= {ra, rb}
        other = (RandomController, WaitController, make_baseline)[k % 3]()
        ctrls = {"A": make_baseline("a"), "B": other}
        res = VersusRunner(_episode(a, b), ctrls, swap_seats=bool(k % 2), clock=SLOW,
                           limits=VersusLimits(max_frames=1800)).run(k)
        games += 1
        for seat in "AB":
            st = res["seats"][seat]
            decisions += st["decisions"]
            if st["kind"] == "scripted" and st["controller"] != "random":
                assert st["fallbacks"] == 0, (k, a, b, seat, st)
    assert rooms_seen == set(range(1, 7)) and games == 36 and decisions > 5000


# --- failure reporting and cooldown --------------------------------------------------
class _Always:
    def __init__(self, choice):
        self.choice, self.asked = choice, 0

    def choose(self, obs, legal, status):
        self.asked += 1
        return self.choice


@pytest.mark.parametrize("macro,reason", [("STRIKE", "no_target"), ("DISGUISE", "no_target"),
                                           ("FOLLOW", "no_target"), ("RIG_TRAP", "reserved"),
                                           ("strike", "unknown_macro")])
def test_qa_a_policy_that_always_asks_a_failing_macro_is_not_looped(macro, reason):
    ctrl = MacroController(_Always(macro))
    ep = VersusEpisode(arena.situation("A"), arena.STARTS, 0, 3600, {})
    ep.reset(0)
    ctrl.reset(0)
    for _ in range(100):
        obs, legal = ep.observe("A"), tuple(ep.legal_actions("A"))
        assert ctrl.decide(copy.deepcopy(obs), legal) in legal
        for _ in range(6):
            ep.tick()
    fails = [e for e in ctrl.events if e["event"] == "macro_failed"]
    assert fails and all(e["reason"] == reason for e in fails)
    # one failure report per cooldown window, not one per decision
    assert len(fails) <= 100 // 5 + 1, len(fails)
    assert all(row["input"] == "WAIT" for row in ctrl.log)


# --- determinism, including the fast path ----------------------------------------------
def test_qa_fast_path_and_default_runner_give_identical_traces_and_state():
    out = []
    for kw in ({}, {"copy_mode": "json", "threaded": False}):
        res = VersusRunner(_episode(*arena.STARTS.values()),
                           {"A": make_baseline(), "B": RandomController()},
                           clock=SLOW, limits=VersusLimits(max_frames=1500), **kw).run(4)
        out.append((res["final_snapshot_sha256"], res["traces"]))
    assert out[0] == out[1]


def test_qa_two_fresh_baselines_with_the_same_seed_have_identical_macro_logs_both_seats_swapped():
    logs = []
    for _ in range(2):
        base = make_baseline()
        VersusRunner(_episode(*arena.STARTS.values()), {"A": RandomController(), "B": base},
                     clock=SLOW, limits=VersusLimits(max_frames=1500)).run(9)
        logs.append((base.log, base.events))
    assert logs[0] == logs[1] and logs[0][0]


def test_qa_a_reused_controller_instance_repeats_exactly_after_reset():
    base = make_baseline()
    runs = [VersusRunner(_episode(*arena.STARTS.values()), {"A": base, "B": RandomController()},
                         clock=SLOW, limits=VersusLimits(max_frames=1200)).run(2)
            for _ in range(2)]
    assert runs[0]["traces"] == runs[1]["traces"]


# --- swap-a-guard over whole trajectories ------------------------------------------------------
class _Recorder:
    """Wraps a controller and records every (observation, legal, input) it is given."""

    def __init__(self, inner):
        self.inner, self.name, self.kind, self.rows = inner, inner.name, inner.kind, []

    def reset(self, seed):
        self.inner.reset(seed)

    def decide(self, obs, legal):
        out = self.inner.decide(copy.deepcopy(obs), legal)
        self.rows.append((copy.deepcopy(obs), tuple(legal), out))
        return out


@pytest.mark.parametrize("seed,other,starts", [
    (1, RandomController, ((1, 2, 2, 1), (3, 2, 7, -1))),
    (2, WaitController, ((4, 2, 2, 1), (5, 2, 3, -1))),            # both rooms hold a guard
    (3, WaitController, ((6, 2, 1, 1), (2, 2, 8, -1))),
    (4, RandomController, ((5, 2, 2, -1), (1, 2, 5, 1)))])
def test_qa_baseline_is_a_pure_function_of_its_observation_stream_over_a_full_duel(
        seed, other, starts):
    """Replay a recorded duel's observations into a fresh baseline (and with a different
    reset seed): identical inputs at every decision. Anything that peeked at the episode,
    a global, the seed or an id would show up as a difference. No ids exist in the stream
    (a disguised rival and a guard are the same dict), so equal streams mean equal inputs."""
    rec = _Recorder(make_baseline())
    VersusRunner(_episode(*starts), {"A": rec, "B": other()}, clock=SLOW,
                 limits=VersusLimits(max_frames=2400)).run(seed)
    assert len(rec.rows) >= 8
    for reset_seed in (0, 987654321):
        fresh = make_baseline()
        fresh.reset(reset_seed)
        for n, (obs, legal, out) in enumerate(rec.rows):
            assert fresh.decide(copy.deepcopy(obs), legal) == out, (n, reset_seed)


def test_qa_swap_a_guard_disguised_rival_vs_real_guard_agree_until_a_visible_difference():
    """B is a disguised rival standing at `spot`; in the other world a real guard stands
    there. Inputs agree for every decision before A's observation differs; the first
    difference is a visible field (the real guard turns at its post), never an id."""
    a_start, spot = (1, 2, 2, +1), (1, 2, 6, +1)
    ep1 = VersusEpisode(arena.situation("A"), {"A": a_start, "B": spot}, 0, 3600, {})
    ep2 = VersusEpisode(arena.situation("A"), {"A": a_start, "B": (3, 2, 7, -1)}, 0, 3600,
                        {"g": (1, 2, (6, 6), +1)})
    ctrls = [make_baseline(), make_baseline()]
    for ep, c in zip((ep1, ep2), ctrls):
        ep.reset(0)
        c.reset(0)
    ep1._duel.rivals["B"].disguised = True            # after reset: reset rebuilds the duel
    prefix = 0
    for step in range(60):
        obs = [ep.observe("A") for ep in (ep1, ep2)]
        legal = [tuple(ep.legal_actions("A")) for ep in (ep1, ep2)]
        if obs[0] != obs[1] or legal[0] != legal[1]:
            f1, f2 = obs[0]["figures"][0], obs[1]["figures"][0]
            assert set(f1) == set(f2)                        # same fields, differing in value only
            assert {k for k in f1 if f1[k] != f2[k]} <= {"facing", "motion", "armed", "stance"}
            break
        i1 = ctrls[0].decide(copy.deepcopy(obs[0]), legal[0])
        i2 = ctrls[1].decide(copy.deepcopy(obs[1]), legal[1])
        assert i1 == i2, (step, i1, i2)
        for ep, i in ((ep1, i1), (ep2, i2)):
            assert ep.step("A", i)["accepted"]
            ep.step("B", "WAIT")
            for _ in range(6):
                ep.tick()
        prefix += 1
    assert prefix >= 3, prefix          # short by construction: a real guard turns at once


# --- compatibility with the macro layer's own boundary ------------------------------------
def test_qa_macro_modules_import_nothing_from_the_engine_or_runner():
    import ast
    import pathlib
    for name in ("agents/macros.py", "agents/versus_baseline.py"):
        tree = ast.parse(pathlib.Path(name).read_text())
        mods = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        mods |= {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        assert not {m for m in mods if m and (m.startswith("pop.versus") or m == "pop.engine"
                                              or m.startswith("pop.observation"))}, (name, mods)


def test_qa_vocabulary_names_match_macros_md():
    import pathlib
    doc = pathlib.Path("docs/final/MACROS.md").read_text()
    for m in MACROS:
        assert f"`{m}`" in doc, m


# --- the baseline against itself ------------------------------------------------------------
@pytest.mark.xfail(strict=True, reason="GATE-T05-qa-1")
@pytest.mark.parametrize("swap", [False, True])
def test_qa_mirror_match_on_the_arena_starts_is_not_a_frozen_stalemate(swap):
    """Two baselines meet on row 0, both armed and mid, and SWEEP each other until
    the clock runs out: neither loses a heart in 3,600 frames."""
    res = VersusRunner(_episode(*arena.STARTS.values()),
                       {"A": make_baseline("a"), "B": make_baseline("b")},
                       swap_seats=swap, clock=SLOW).run(0)
    assert res["status"] != "draw:time_up", res["status"]


def test_qa_baseline_beats_random_in_most_duels_from_both_seats_and_swapped_starts():
    wins = games = 0
    for seed in range(4):
        for swap in (False, True):
            res = VersusRunner(_episode(*arena.STARTS.values()),
                               {"A": make_baseline(), "B": RandomController()},
                               swap_seats=swap, clock=SLOW, limits=VersusLimits()).run(seed)
            games += 1
            wins += res["winner_slot"] == "A"
    assert wins >= games - 1, (wins, games)


# --- TAKE compatibility (T01-fix1, R-V26: TAKE legal over any downed guard) ------------------
class _Staged(VersusEpisode):
    def __init__(self, *args, setup=None, **kw):
        self._setup = setup
        super().__init__(*args, **kw)

    def reset(self, seed):
        super().reset(seed)
        self._setup(self._duel)


def test_qa_disguise_on_an_already_stripped_body_fails_no_uniform_and_does_not_retake_forever():
    def setup(duel):
        duel.guards["g"].knock_out()
        duel.guards["g"].uniform = False                 # someone already took it
    ep = _Staged(arena.situation("A"), {"A": (1, 2, 2, 1), "B": (3, 2, 7, -1)}, 0, 3600,
                 {"g": (1, 2, (6, 6), 1)}, setup=setup)
    ep.reset(0)
    ctrl = MacroController(_Always("DISGUISE"))
    ctrl.reset(0)
    takes = 0
    for _ in range(60):
        obs, legal = ep.observe("A"), tuple(ep.legal_actions("A"))
        act = ctrl.decide(copy.deepcopy(obs), legal)
        assert act in legal
        takes += act == "TAKE"
        ep.step("A", act)
        ep.step("B", "WAIT")
        for _ in range(6):
            ep.tick()
    assert not ep.observe("A")["me"]["disguised"]
    assert takes <= 4, takes                      # a few tries inside the cooldown, never a loop
    assert any(e["reason"] == "no_uniform" for e in ctrl.events if e["event"] == "macro_failed")


# --- competence outside the curated starts (random rooms, guards live) ---------------------------
# (seed, seat A start, seat B start, swap_seats: the baseline slot plays seat B). Found by a 40-game random-start
# sweep (seed 99): 8 losses to a WAIT controller and 10 timeouts; the curated starts show 16/16.
LOSSES_TO_WAIT = [(4, (4, 2, 2, -1), (3, 2, 0, 1), False), (14, (4, 2, 9, -1), (1, 2, 9, -1), False),
                  (16, (5, 2, 5, 1), (1, 2, 1, 1), False), (22, (5, 2, 1, 1), (2, 2, 0, -1), False)]
TIMEOUTS_VS_WAIT = [(10, (2, 2, 8, -1), (6, 2, 0, 1), False), (21, (6, 2, 9, 1), (1, 2, 8, 1), True),
                    (25, (6, 2, 0, 1), (3, 2, 3, 1), True), (37, (6, 2, 0, 1), (3, 2, 4, 1), True)]


def _vs_wait(seed, a, b, swap):
    """Controller slot A is the baseline; `swap` seats slot A as seat B (start `b`)."""
    return VersusRunner(_episode(a, b), {"A": make_baseline("x"), "B": WaitController()},
                        swap_seats=swap, clock=SLOW).run(seed)


@pytest.mark.xfail(strict=True, reason="GATE-T05-qa-2")
@pytest.mark.parametrize("seed,mine,theirs,swap", LOSSES_TO_WAIT)
def test_qa_baseline_does_not_lose_to_a_wait_controller_by_fighting_a_guard(seed, mine, theirs, swap):
    res = _vs_wait(seed, mine, theirs, swap)
    assert res["winner_slot"] == "A", res["status"]


@pytest.mark.xfail(strict=True, reason="GATE-T05-qa-3")
@pytest.mark.parametrize("seed,mine,theirs,swap", TIMEOUTS_VS_WAIT)
def test_qa_baseline_finds_a_motionless_rival_in_another_room_within_the_limit(seed, mine, theirs, swap):
    res = _vs_wait(seed, mine, theirs, swap)
    assert res["status"] != "draw:time_up", res["status"]
