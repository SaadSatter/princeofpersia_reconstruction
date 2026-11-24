"""Gate 1 QA review of T04 (seat controllers and versus runner), adversarial.

Written by the QA subagent for GATE-T04-qa against commit af76c30. Passing
tests pin behaviour that the T04 tests did not cover (a real won duel through
the runner and its winner mapping under seat swap, decision_every=1, limits
under seat swap, controllers that keep references or fail in reset). Tests
marked xfail(strict=True) reproduce findings GATE-T04-QA-1 to QA-5; they are
expected to fail until the Tech Lead fixes them (or Saad decides otherwise).
"""

from __future__ import annotations

import time

import pytest

from pop import arena
from pop.seats import PolicyController, RandomController, ScriptedController, WaitController
from pop.versus import VersusEpisode, arena_episode
from pop.versus_runner import (VersusLimits, VersusRunner, load_traces, replay,
                               save_traces)


def still(_now=[0.0]):
    return 0.0


def arena_factory(limit: int = 60):
    return lambda: arena_episode(time_limit_frames=limit)


def face_off_factory(limit: int = 900):
    """A and B side by side in the Gatehouse's open top row (as tests/test_swordplay.py)."""
    starts = dict(arena.STARTS, A=(2, 0, 3, +1), B=(2, 0, 4, -1))
    return lambda: VersusEpisode(arena.situation("A"), starts, 0, limit)


def chaser(obs: dict, legal: tuple[str, ...]) -> str:
    """Draw, walk up to the visible rival, lunge. Uses only its own observation."""
    if "DRAW" in legal:
        return "DRAW"
    rivals = [f for f in obs["figures"] if f["kind"] == "rival"]
    if not rivals:
        return "WAIT"
    d = rivals[0]["col"] - obs["me"]["col"]
    facing = 1 if obs["me"]["facing"] == "right" else -1
    if abs(d) <= 1 and (d == 0 or (d > 0) == (facing > 0)) and "LUNGE" in legal:
        return "LUNGE"
    return "STEP_RIGHT" if d > 0 else "STEP_LEFT"


class Answer:
    """Returns whatever `make()` builds, every decision."""

    kind = "policy"

    def __init__(self, make, name: str = "answer") -> None:
        self.make, self.name = make, name

    def decide(self, observation, legal):
        return self.make()


# --- a real won duel and the winner mapping -----------------------------------
@pytest.mark.parametrize("swap", [False, True])
def test_real_won_duel_maps_winner_to_controller_slot_and_replays(swap, tmp_path):
    ctrls = {"A": PolicyController(chaser, name="chaser"), "B": WaitController()}
    res = VersusRunner(face_off_factory(), ctrls, swap_seats=swap, clock=still).run(0)
    seat = "B" if swap else "A"                    # the chaser's seat
    assert res["outcome"]["status"] == "terminal"
    assert res["status"] == f"won:{seat}"
    assert (res["winner_seat"], res["winner_slot"]) == (seat, "A")
    assert res["seats"][seat]["controller"] == "chaser"
    assert replay(face_off_factory(), res) == res["final_snapshot"]
    loaded = load_traces(save_traces(res, tmp_path).values())
    assert replay(face_off_factory(), loaded) == res["final_snapshot"]


def test_draw_has_no_winner_slot():
    res = VersusRunner(arena_factory(30), {"A": WaitController(), "B": WaitController()},
                       clock=still).run(0)
    assert res["status"] == "draw:time_up"
    assert (res["winner_seat"], res["winner_slot"]) == (None, None)


# --- cadence of one frame ---------------------------------------------------------
def test_decision_every_1_is_deterministic_asks_every_frame_and_replays():
    fac = arena_factory(200)
    pair = lambda: {"A": RandomController(), "B": RandomController()}  # noqa: E731
    a = VersusRunner(fac, pair(), decision_every=1, clock=still).run(7)
    b = VersusRunner(fac, pair(), decision_every=1, clock=still).run(7)
    assert a["traces"] == b["traces"] and a["final_snapshot"] == b["final_snapshot"]
    assert a["seats"]["A"]["decisions"] == a["seats"]["B"]["decisions"] == 200
    assert [r["frame"] for r in a["traces"]["A"]] == list(range(200))
    assert replay(fac, a) == a["final_snapshot"]


def test_same_runner_run_twice_is_identical():
    runner = VersusRunner(arena_factory(), {"A": RandomController(), "B": RandomController()},
                          clock=still)
    assert runner.run(4)["traces"] == runner.run(4)["traces"]


# --- limits under seat swap ------------------------------------------------------
@pytest.mark.parametrize("swap", [False, True])
def test_max_fallbacks_names_the_seat_that_the_failing_slot_plays(swap):
    bad = Answer(lambda: "nope", name="bad")
    res = VersusRunner(arena_factory(), {"A": bad, "B": WaitController()}, swap_seats=swap,
                       limits=VersusLimits(max_fallbacks=1), clock=still).run(0)
    seat = "B" if swap else "A"
    assert res["status"] == f"aborted:max_fallbacks:{seat}"
    assert res["seats"][seat]["slot"] == "A" and res["seats"][seat]["fallbacks"] == 2
    assert (res["winner_seat"], res["winner_slot"]) == (None, None)
    assert replay(arena_factory(), res) == res["final_snapshot"]


@pytest.mark.parametrize("swap", [False, True])
def test_max_decisions_under_swap_stops_both_and_replays(swap):
    res = VersusRunner(arena_factory(), {"A": RandomController(), "B": WaitController()},
                       swap_seats=swap, limits=VersusLimits(max_decisions=3),
                       clock=still).run(0)
    assert res["status"] == "aborted:max_decisions:A,B"
    assert res["frames"] == 18
    assert replay(arena_factory(), res) == res["final_snapshot"]


# --- controllers that keep references or fail in reset ----------------------------
def test_kept_observation_is_a_frozen_copy_and_mutating_it_later_changes_nothing():
    kept: list[dict] = []

    def keeper(obs, legal):
        kept.append(obs)
        if len(kept) > 1:
            kept[0]["me"]["hp"] = 0                # vandalise an old copy
            kept[0]["figures"].append({"kind": "rival"})
        return "RIGHT"

    res = VersusRunner(arena_factory(), {"A": PolicyController(keeper), "B": WaitController()},
                       clock=still).run(0)
    clean = VersusRunner(arena_factory(), {"A": ScriptedController(["RIGHT"] * 10),
                                           "B": WaitController()}, clock=still).run(0)
    assert kept[1] is not kept[0] and kept[1]["me"]["hp"] > 0
    assert res["final_snapshot"] == clean["final_snapshot"]


def test_reset_error_is_recorded_redacted_and_the_seat_still_plays():
    class BadReset(ScriptedController):
        def reset(self, seed):
            raise ValueError("sk-ant-api03-ABCDEFGHIJKLMNOPQRSTUV reset failed")

    res = VersusRunner(arena_factory(), {"A": BadReset(["RIGHT"]), "B": WaitController()},
                       clock=still).run(0)
    err = res["seats"]["A"]["reset_error"]
    assert err is not None and "sk-ant" not in err
    assert res["traces"]["A"][0]["input"] == "RIGHT"
    assert res["seats"]["B"]["reset_error"] is None


# --- findings ----------------------------------------------------------------------------
class EqualsEverything(str):
    def __eq__(self, other):
        return True

    __hash__ = str.__hash__


class StripsToStepLeft(str):
    def strip(self, *args):
        return "STEP_LEFT"


class ReprRaises:
    def __repr__(self):
        raise RuntimeError("repr failed")


def test_qa1_str_subclass_with_permissive_eq_is_a_labelled_fallback():
    res = VersusRunner(arena_factory(), {"A": Answer(lambda: EqualsEverything("NOT_AN_ACTION")),
                                         "B": WaitController()}, clock=still).run(0)
    assert res["traces"]["A"][0]["source"] == "fallback"
    assert res["seats"]["B"]["decisions"] == 10


def test_qa2_trace_records_what_the_engine_played(tmp_path):
    episodes = []

    def fac():
        episodes.append(arena_episode(time_limit_frames=60))
        return episodes[-1]

    res = VersusRunner(fac, {"A": Answer(lambda: StripsToStepLeft("JUMP_RIGHT")),
                             "B": WaitController()}, clock=still).run(0)
    played = [a for (_, seat, a) in episodes[0].log if seat == "A"]
    recorded = [r["input"] for r in res["traces"]["A"] if r["source"] == "controller"]
    assert played == recorded
    loaded = load_traces(save_traces(res, tmp_path).values())
    assert replay(arena_factory(), loaded) == res["final_snapshot"]


def test_qa3_non_string_with_raising_repr_is_a_malformed_fallback():
    res = VersusRunner(arena_factory(), {"A": Answer(ReprRaises), "B": WaitController()},
                       clock=still).run(0)
    assert res["traces"]["A"][0]["fallback_reason"] == "malformed"
    assert res["seats"]["B"]["decisions"] == 10


def test_qa4_slow_reset_is_bounded_by_the_timeout():
    class SlowReset(WaitController):
        def reset(self, seed):
            time.sleep(0.6)

    t0 = time.perf_counter()
    VersusRunner(arena_factory(12), {"A": SlowReset(), "B": WaitController()},
                 limits=VersusLimits(timeout_s=0.05)).run(0)
    assert time.perf_counter() - t0 < 0.4


def test_qa5_one_instance_cannot_play_both_seats():
    same = RandomController()
    with pytest.raises(ValueError):
        VersusRunner(arena_factory(), {"A": same, "B": same})
