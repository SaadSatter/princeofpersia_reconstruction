"""Gate 2 (T19): the macro layer, baseline, R-V25, the PPO encoder and the shipped
rival against the post-T19 dynamics (decisions #53, #54, #71). Written by the
Evaluation Specialist. Tuning starts only; the H6 held-out set is never read here
(decision #61: its single run belongs to T09). No training, no network, no --live.
"""
from __future__ import annotations

import copy
from collections import Counter

import pytest

from agents import macros
from agents.baseline import Pose
from agents.macros import FieldView
from agents.rl.encoder import Encoder
from agents.rl.policy import SHIPPED_SHA256, SHIPPED_WEIGHTS, make_rl_rival
from agents.versus_baseline import make_baseline
from pop import arena
from pop import versus as V
from pop.versus import VersusEpisode
from pop.versus_runner import VersusRunner
from tools.rl import env

FAR = (3, 2, 7, -1)


def episode(a, b=FAR, posts=None, seed=0) -> VersusEpisode:
    return VersusEpisode(arena.situation("A"), {"A": a, "B": b}, seed,
                         guard_posts={} if posts is None else posts)


def _duel(seat, mine, theirs, me_ctrl, other_ctrl, seed=10_000):
    other = "B" if seat == "A" else "A"
    return VersusRunner(
        lambda: VersusEpisode(arena.situation("A"), {seat: mine, other: theirs}, 0, 3600,
                              arena.GUARD_POSTS),
        {seat: me_ctrl, other: other_ctrl}, copy_mode="json", threaded=False,
        clock=lambda: 0.0).run(seed)


def _combos():
    for p, seat, first in env.COMBOS:
        a, b = env.TUNING_STARTS[p]
        yield seat, (a, b) if first else (b, a)


# --- 1. planner pricing of JUMP against the facing (decision #71) ----------------------------
def test_planner_still_models_jump_against_facing_as_a_turn_but_the_engine_jumps_at_once():
    """FINDING (minor, efficiency only): `RoomView.predict` returns a turn with no
    displacement for `JUMP_LEFT` while facing right; `Rival._directional` now faces and
    jumps in one move, 3 cells. Characterisation: this test changes when the model does."""
    ep = episode((2, 2, 4, +1))
    obs = ep.observe("A")
    p = Pose(obs["me"]["row"], obs["me"]["col"], +1, -1)
    pred, _ = FieldView(obs).predict(p, "JUMP_LEFT")
    assert (pred.col, pred.facing) == (4, -1)                    # the model: turned, did not move
    ep.step("A", "JUMP_LEFT")
    for _ in range(40):
        ep.tick()
    me = ep.observe("A")["me"]
    assert me["col"] == 1 and me["facing"] == "left"             # the engine: flew three cells


def test_no_macro_ever_emits_a_jump_against_the_facing_so_the_stale_price_is_unreachable():
    """plan_path ties `JUMP_x` against the facing with `x` (a turn) and LEFT/RIGHT come
    first, so it is never chosen: over every tuning combo, both rivals, zero emitted."""
    seen: Counter = Counter()
    orig = macros.MacroController.decide

    def decide(self, obs, legal):
        a = orig(self, obs, legal)
        face = 1 if obs["me"]["facing"] == "right" else -1
        if a.startswith(("JUMP_", "RUN_JUMP_")):
            seen["against" if (1 if a.endswith("RIGHT") else -1) != face else "with"] += 1
        return a

    macros.MacroController.decide = decide
    try:
        for seat, (mine, theirs) in _combos():
            for ctrl in (make_baseline(), make_rl_rival(SHIPPED_WEIGHTS, SHIPPED_SHA256)):
                _duel(seat, mine, theirs, ctrl, make_baseline())
    finally:
        macros.MacroController.decide = orig
    assert seen["with"] > 100 and seen["against"] == 0, seen


# --- 2. the shipped rival on the post-T19 engine (tuning starts only) ------------------------
def test_shipped_rival_on_tuning_starts_matches_the_pre_t19_result_with_no_fallbacks():
    """32 combos (8 start pairs x 2 seats x 2 orders), seat-swapped. Pre-T19 (fc02687),
    measured in this session with evaluation/t19_compare.py: 30 W / 2 D / 0 L, final
    snapshot hashes identical to the post-T19 engine for every combo. Not a strength claim."""
    w = d = l = fb = 0
    for seat, (mine, theirs) in _combos():
        res = _duel(seat, mine, theirs, make_rl_rival(SHIPPED_WEIGHTS, SHIPPED_SHA256),
                    make_baseline())
        assert res["status"] in ("won:A", "won:B", "draw:time_up"), res["status"]
        r = env.terminal_reward(res["outcome"]["reason"], seat)
        w += r > 0; d += r == 0; l += r < 0
        fb += sum(res["seats"][s]["fallbacks"] for s in "AB")
    assert (w, d, l, fb) == (30, 2, 0, 0)


# --- 3. R-V19 / R-V25: the discarded run frames of the grace window --------------------------
POSTS = {"g": (2, 0, (6, 6), -1)}


def _suspicion_trace(script, ticks=14):
    ep = episode((2, 0, 2, +1), posts=POSTS)
    ep._duel.rivals["A"].disguised = True
    out = []
    for t in range(ticks):
        if t in script:
            ep.step("A", script[t])
        ep.tick()
        out.append(sum(ep._duel.suspicion.values()))
    return out


@pytest.mark.parametrize("gap", [1, 2])
def test_grace_flip_pays_the_discarded_run_frames_a_small_unadvertised_surcharge(gap):
    """QA minor 1, reproduced and bounded: RIGHT then JUMP_RIGHT `gap` ticks later costs
    exactly 4 x (frames the run lasted) more suspicion than JUMP_RIGHT alone, and the kid
    never moved. After the flip is under way the two meters rise by the same amount."""
    plain = _suspicion_trace({0: "JUMP_RIGHT"})
    grace = _suspicion_trace({0: "RIGHT", gap: "JUMP_RIGHT"})
    # align on the flip's own frames: plain[k] is flip frame k+1, grace[gap + k] likewise
    diffs = [grace[gap + k] - plain[k] for k in range(8)]
    assert diffs == [V.SUSPICION_RUN * gap] * 8, diffs


def test_surcharge_is_invisible_to_the_other_seat_and_adds_no_tell_beyond_the_flip():
    """The meter is never observed by the other seat. What B sees of a disguised A is the
    figure (kind guard) and, for a run or flip, a suspicion-raising motion: the same
    effect names a plain disguised jump shows. Position never changes in the window."""
    def seen(script):
        ep = episode((3, 0, 3, +1), (3, 2, 7, -1))
        ep._duel.rivals["A"].disguised = True
        effects, cols = [], []
        for t in range(24):
            if t in script:
                ep.step("A", script[t])
            ep.tick()
            fig = [f for f in ep.observe("B")["figures"]][0]
            assert fig["kind"] == "guard"
            effects.append(fig["motion"]["effect"] if fig["motion"] else None)
            cols.append(fig["col"])
        return effects, cols

    plain_e, _ = seen({0: "JUMP_RIGHT"})
    grace_e, grace_c = seen({0: "RIGHT", 2: "JUMP_RIGHT"})
    assert set(grace_e) - {None} <= set(plain_e) | {"moved"}
    assert "jumped" not in grace_e and "jumped" not in plain_e
    assert grace_c[0] == grace_c[1] == 3                       # no creep during the discarded run


# --- 4. the PPO encoder against `jumped` versus `flipped` -------------------------------------
def test_duel_never_reports_jumped_any_more_every_directional_jump_is_flipped():
    effects = set()
    for act in ("JUMP_LEFT", "JUMP_RIGHT", "RUN_JUMP_LEFT", "RUN_JUMP_RIGHT"):
        ep = episode((2, 2, 4, +1))
        ep.step("A", act)
        for _ in range(40):
            ep.tick()
            m = ep.observe("A")["me"]["motion"]
            if m:
                effects.add(m["effect"])
    assert "flipped" in effects and "jumped" not in effects


def test_encoder_features_are_identical_when_jumped_and_flipped_are_swapped():
    """The encoder lists both names in one tuple (LEAPS). Take a live observation where
    the other rival is mid-leap and my own move is a leap, rename the effect, and compare
    the whole feature vector: no weight can tell the two apart."""
    ep = episode((2, 2, 3, +1), (2, 2, 6, -1))
    ep.step("A", "JUMP_RIGHT")
    ep.step("B", "JUMP_LEFT")
    obs = None
    for _ in range(40):
        ep.tick()
        o = ep.observe("A")
        if o["me"]["motion"] and o["me"]["motion"]["effect"] == "flipped" and \
                any(f["motion"] and f["motion"]["effect"] == "flipped" for f in o["figures"]):
            obs = o
            break
    assert obs is not None, "never saw both rivals mid-flip"
    alt = copy.deepcopy(obs)
    alt["me"]["motion"]["effect"] = "jumped"
    for f in alt["figures"]:
        if f["motion"] and f["motion"]["effect"] == "flipped":
            f["motion"]["effect"] = "jumped"
    legal = ep.legal_actions("A")
    assert Encoder().encode(obs, legal) == Encoder().encode(alt, legal)


# --- 5. baseline fairness is unchanged ------------------------------------------------------
def test_baseline_tracker_counts_flipped_like_jumped_as_a_leap():
    from agents import versus_baseline as vb
    assert "flipped" in vb.LEAPS and "jumped" in vb.LEAPS


def test_baseline_never_needs_a_fallback_in_tuning_duels_against_a_random_input_seat():
    """Random inputs exercise jump-against-facing and rapid direction/jump pairs, which
    the macro layers never emit. Both rivals stay fallback-free (legal inputs only)."""
    from pop.seats import RandomController
    fb = 0
    for seat, (mine, theirs) in list(_combos())[:8]:
        res = _duel(seat, mine, theirs, make_rl_rival(SHIPPED_WEIGHTS, SHIPPED_SHA256),
                    RandomController())
        assert not res["status"].startswith("aborted"), res["status"]
        fb += res["seats"][seat]["fallbacks"]
    assert fb == 0
