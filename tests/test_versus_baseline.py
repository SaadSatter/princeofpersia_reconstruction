"""The scripted versus baseline (agents/versus_baseline.py; docs/final/MACROS.md, task T05).

Deterministic, offline. Competence numbers use fixed starts with seats
swapped; the tuning starts are the ones MACROS.md records, the held-out starts
were not looked at while the heuristics were set.
"""

from __future__ import annotations

import copy
import time

import pytest

from agents.macros import MacroController
from agents.versus_baseline import VersusBaseline, make_baseline
from pop import arena
from pop.seats import RandomController, WaitController
from pop.versus import VersusEpisode
from pop.versus_runner import VersusLimits, VersusRunner

EVERY = 6
# (A start, B start). Both rivals are always in different rooms (GDD 5.3).
TUNING_STARTS = [
    (arena.STARTS["A"], arena.STARTS["B"]),
    ((1, 2, 3, +1), (3, 2, 6, -1)),
]
HELD_OUT_STARTS = [
    ((1, 2, 5, +1), (3, 2, 8, -1)),
    ((1, 2, 2, +1), (2, 2, 9, -1)),
    ((2, 2, 8, -1), (3, 2, 7, -1)),
    ((1, 2, 4, +1), (3, 2, 4, +1)),
]


def factory(starts, posts=None, limit=3600):
    a, b = starts
    return lambda: VersusEpisode(arena.situation("A"), {"A": a, "B": b}, 0, limit,
                                 arena.GUARD_POSTS if posts is None else posts)


def duel(baseline_ctrl, other, starts, seed, swap, posts=None, **kw):
    """One duel. `swap` puts the baseline in seat B (and its start there too)."""
    a, b = starts
    kw.setdefault("clock", lambda: 0.0)        # latency_ms is wall time; fix it for equality
    pair = ((b, a) if swap else (a, b))
    ctrls = {"A": baseline_ctrl, "B": other}
    runner = VersusRunner(factory(pair, posts), ctrls, swap_seats=False, **kw)
    if swap:
        runner = VersusRunner(factory(pair, posts), {"A": other, "B": baseline_ctrl}, **kw)
    return runner.run(seed)


def baseline_won(result, swap) -> bool:
    return result["outcome"]["reason"] == ("won:B" if swap else "won:A")


class Staged(VersusEpisode):
    """An episode whose reset applies a test setup (the runner resets before play)."""

    def __init__(self, *args, setup=None, **kw):
        self._setup = setup
        super().__init__(*args, **kw)

    def reset(self, seed):
        super().reset(seed)
        if self._setup:
            self._setup(self._duel)


# --- 1. determinism ------------------------------------------------------
def test_same_seed_and_controllers_give_an_identical_result_and_trace():
    def go():
        base = make_baseline()
        res = duel(base, RandomController(), TUNING_STARTS[0], 7, swap=False)
        return res, base.log
    (r1, log1), (r2, log2) = go(), go()
    assert r1 == r2 and log1 == log2


def test_determinism_holds_with_the_trusted_fast_path_too():
    def go():
        return duel(make_baseline(), RandomController(), TUNING_STARTS[0], 3, swap=True,
                    copy_mode="json", threaded=False)["final_snapshot_sha256"]
    assert go() == go()


# --- 2. boundary -----------------------------------------------------------
def test_baseline_decision_is_a_function_of_its_own_observation_history():
    """Two duels differ only in where the rival starts, in a room the baseline
    never enters early on. Until the baseline's observation differs, its inputs
    are identical: it cannot be heading for a rival it cannot see."""
    a = arena.STARTS["A"]
    runs = [duel(make_baseline(), WaitController(), (a, b), 0, swap=False, posts={},
                 limits=VersusLimits(max_frames=240))
            for b in ((3, 2, 7, -1), (5, 2, 7, -1))]
    t1, t2 = (r["traces"]["A"] for r in runs)
    same_obs = 0
    for d1, d2 in zip(t1, t2):
        if d1["obs_sha256"] != d2["obs_sha256"]:
            break
        assert d1["input"] == d2["input"]
        same_obs += 1
    assert same_obs >= 10                           # a real prefix, not a vacuous pass
    # And it moved: it is not simply waiting.
    assert {d["input"] for d in t1[:same_obs]} - {"WAIT"}


def _figure_fields(fig):
    return {k: v for k, v in fig.items() if k != "kind"}


def test_swap_a_guard_a_disguised_rival_and_a_real_guard_get_the_same_decision():
    a_start, spot = (1, 2, 2, +1), (1, 2, 6, +1)
    # Episode 1: rival B stands disguised at `spot`.
    disguised = VersusEpisode(arena.situation("A"), {"A": a_start, "B": spot}, 0, 3600, {})
    disguised._duel.rivals["B"].disguised = True
    # Episode 2: a real guard stands at the same cell, facing the same way; B is far away.
    real = VersusEpisode(arena.situation("A"), {"A": a_start, "B": (3, 2, 7, -1)}, 0, 3600,
                         {"g": (1, 2, (6, 6), +1)})
    o1, o2 = disguised.observe("A"), real.observe("A")
    assert o1["figures"] == o2["figures"] != []     # same kind, same fields, nothing else
    assert o1["figures"][0]["kind"] == "guard"
    assert o1["suspicion"] == o2["suspicion"] == []
    l1, l2 = tuple(disguised.legal_actions("A")), tuple(real.legal_actions("A"))
    assert l1 == l2
    c1, c2 = make_baseline(), make_baseline()
    for ctrl in (c1, c2):
        ctrl.reset(0)
    for _ in range(4):                              # the same follow-up observations
        assert c1.decide(copy.deepcopy(o1), l1) == c2.decide(copy.deepcopy(o2), l2)


def test_the_baseline_only_ever_receives_the_observation_and_the_legal_tuple():
    import inspect
    assert list(inspect.signature(MacroController.decide).parameters) == [
        "self", "observation", "legal"]
    assert list(inspect.signature(VersusBaseline.choose).parameters) == [
        "self", "obs", "legal", "status"]


# --- tells ---------------------------------------------------------------------
def test_a_guard_that_runs_unarmed_or_leaps_is_identified_as_the_rival():
    from agents.versus_baseline import FigureTracker
    base = {"kind": "guard", "row": 2, "col": 5, "facing": "left", "posture": "standing",
            "stance": None, "armed": False, "motion": None}
    me = {"row": 2, "col": 2, "facing": "right", "posture": "standing", "hp": 3, "max_hp": 3,
          "stance": None, "armed": False, "disguised": False, "knocked_down_frames": 0,
          "motion": None}
    obs = {"room": "r", "tiles": ["#_________"] * 3, "me": me, "figures": [base],
           "edges": {"left": False, "right": True}}
    for motion, expect in ((None, False),
                           ({"effect": "moved", "frame": 1, "frames": 8, "to": [2, 4],
                             "to_posture": "standing", "to_facing": "left"}, False),
                           ({"effect": "moved", "frame": 1, "frames": 4, "to": [2, 4],
                             "to_posture": "standing", "to_facing": "left"}, True),
                           ({"effect": "jumped", "frame": 1, "frames": 12, "to": [2, 2],
                             "to_posture": "standing", "to_facing": "left"}, True)):
        tracker = FigureTracker(EVERY)
        o = copy.deepcopy(obs)
        o["figures"][0]["motion"] = motion
        tracker.update(o)
        assert bool(tracker.suspects()) is expect, motion


def test_a_guard_that_does_not_react_to_an_undisguised_prince_is_suspected():
    from agents.versus_baseline import FigureTracker
    fig = {"kind": "guard", "row": 2, "col": 5, "facing": "left", "posture": "standing",
           "stance": None, "armed": False, "motion": None}
    me = {"row": 2, "col": 2, "facing": "right", "posture": "standing", "hp": 3, "max_hp": 3,
          "stance": None, "armed": False, "disguised": False, "knocked_down_frames": 0,
          "motion": None}
    obs = {"room": "r", "tiles": ["#_________"] * 3, "me": me, "figures": [fig],
           "edges": {"left": False, "right": True}}
    tracker = FigureTracker(EVERY)
    verdicts = []
    for _ in range(5):
        tracker.update(copy.deepcopy(obs))
        verdicts.append(bool(tracker.suspects()))
    assert verdicts[0] is False and verdicts[-1] is True
    # A guard that draws its sword at once is a real guard.
    tracker = FigureTracker(EVERY)
    armed = copy.deepcopy(obs)
    armed["figures"][0].update(armed=True, stance="mid")
    for _ in range(5):
        tracker.update(copy.deepcopy(armed))
    assert not tracker.suspects()


# --- behaviours ----------------------------------------------------------------
def test_baseline_takes_the_nearest_visible_uniform_before_anything_else():
    ep_factory = lambda: _with_body()                              # noqa: E731

    def _with_body():
        return Staged(arena.situation("A"), {"A": (1, 2, 2, +1), "B": (3, 2, 7, -1)}, 0, 3600,
                      {"g": (1, 2, (6, 6), +1)},
                      setup=lambda duel: duel.guards["g"].knock_out())
    seen = []
    VersusRunner(ep_factory, {"A": make_baseline(), "B": WaitController()},
                 limits=VersusLimits(max_frames=300),
                 on_frame=lambda f, view: seen.append(view.observe("A")["me"]["disguised"])).run(0)
    assert any(seen) and not seen[0]


def test_baseline_identifies_and_strikes_a_rival_that_arrives_disguised():
    def make():
        # Test setup: B arrives already disguised.
        return Staged(arena.situation("A"), {"A": (1, 2, 1, +1), "B": (1, 2, 7, -1)}, 0, 3600,
                      {}, setup=lambda duel: setattr(duel.rivals["B"], "disguised", True))
    res = VersusRunner(make, {"A": make_baseline(), "B": WaitController()},
                       limits=VersusLimits(max_frames=900)).run(0)
    assert res["outcome"]["reason"] == "won:A", res["status"]


# --- 4. competence ---------------------------------------------------------------
def _score(starts_list, other_factory, seeds=(0, 1)):
    wins = games = 0
    for starts in starts_list:
        for swap in (False, True):
            for seed in seeds:
                res = duel(make_baseline(), other_factory(), starts, seed, swap)
                games += 1
                wins += baseline_won(res, swap)
    return wins, games


@pytest.mark.parametrize("other", [WaitController, RandomController])
def test_baseline_beats_wait_and_random_in_most_duels_on_tuning_starts(other):
    wins, games = _score(TUNING_STARTS, other)
    print(f"tuning vs {other.__name__}: {wins}/{games}")
    assert wins > games / 2


@pytest.mark.parametrize("other", [WaitController, RandomController])
def test_baseline_beats_wait_and_random_in_most_duels_on_held_out_starts(other):
    wins, games = _score(HELD_OUT_STARTS, other)
    print(f"held-out vs {other.__name__}: {wins}/{games}")
    assert wins > games / 2


# --- 5. throughput -------------------------------------------------------------------
def test_decisions_per_second_with_the_fast_path():
    ctrl = make_baseline()
    t0 = time.perf_counter()
    res = VersusRunner(factory(TUNING_STARTS[0]), {"A": ctrl, "B": RandomController()},
                       copy_mode="json", threaded=False,
                       limits=VersusLimits(max_frames=1200)).run(0)
    dt = time.perf_counter() - t0
    decisions = res["seats"]["A"]["decisions"] + res["seats"]["B"]["decisions"]
    rate = decisions / dt
    print(f"decisions per second (both seats, baseline vs random, fast path): {rate:.0f}")
    assert res["seats"]["A"]["fallbacks"] == 0          # the baseline never needs a fallback
    assert rate > 100                                   # loose floor; the real number is in MACROS.md
