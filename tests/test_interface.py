"""The five operations, legal/illegal actions, and episode limits (3b, 3c)."""

import pytest

from pop.engine import ACTIONS
from pop.interface import Episode


def test_five_operations_exist():
    ep = Episode("S1")
    for name in ("reset", "observe", "legal_actions", "step", "outcome"):
        assert callable(getattr(ep, name))


def test_unknown_player_is_rejected():
    ep = Episode("S1")
    for op in (ep.observe, ep.legal_actions):
        with pytest.raises(ValueError):
            op("guard")
    with pytest.raises(ValueError):
        ep.step("guard", "WAIT")


def test_initial_outcome_is_ongoing():
    out = Episode("S1").outcome()
    assert out == {"status": "ongoing", "reason": None, "score": 0,
                   "actions": 0, "invalid_actions": 0, "frames": 0}


def test_legal_actions_when_standing_are_the_full_vocabulary():
    assert Episode("S1").legal_actions("kid") == list(ACTIONS)


@pytest.mark.parametrize("bad,error", [
    ("FLY", "unknown action"),
    (42, "action must be a string"),
    (None, "action must be a string"),
    ("", "unknown action"),
    ("STRIKE", "unknown action"),          # combat is not implemented
])
def test_invalid_actions_are_refused_counted_and_change_nothing(bad, error):
    ep = Episode("S1")
    before = ep._game.snapshot()
    res = ep.step("kid", bad)
    assert res["accepted"] is False and res["error"] == error and res["frames"] == 0
    assert ep._game.snapshot() == before
    assert ep.outcome()["invalid_actions"] == 1 and ep.outcome()["actions"] == 0


def test_action_names_are_case_and_space_insensitive():
    ep = Episode("S1")
    assert ep.step("kid", "  right ")["accepted"] is True


def test_action_illegal_for_posture_is_refused():
    ep = Episode("S3")                        # start on a ledge edge facing right
    for a in ["RIGHT"] * 4:
        ep.step("kid", a)
    assert ep.step("kid", "DOWN")["effect"] == "hanging"
    assert ep.legal_actions("kid") == ["WAIT", "UP", "DOWN"]
    before = ep._game.snapshot()
    res = ep.step("kid", "RIGHT")
    assert res["accepted"] is False and res["error"] == "action not legal in the current posture"
    assert ep._game.snapshot() == before


def test_five_consecutive_invalid_actions_end_the_episode():
    ep = Episode("S1")
    for _ in range(4):
        ep.step("kid", "FLY")
    assert ep.outcome()["status"] == "ongoing"
    ep.step("kid", "WAIT")                   # a valid action resets the streak
    for _ in range(5):
        ep.step("kid", "FLY")
    assert ep.outcome()["reason"] == "invalid_limit"


def test_step_limit_ends_the_episode():
    ep = Episode("S1", max_actions=3)
    for _ in range(3):
        ep.step("kid", "WAIT")
    out = ep.outcome()
    assert out["status"] == "terminal" and out["reason"] == "step_limit" and out["actions"] == 3


def test_terminal_episode_refuses_actions_without_counting():
    ep = Episode("S1", max_actions=1)
    ep.step("kid", "WAIT")
    res = ep.step("kid", "WAIT")
    assert res["accepted"] is False and res["error"] == "episode is over"
    assert ep.outcome()["invalid_actions"] == 0
    assert ep.legal_actions("kid") == []


def test_death_is_terminal_with_reason():
    ep = Episode("S1")
    for a in ["RIGHT"] * 4:                  # run into the spike pit
        ep.step("kid", a)
    out = ep.outcome()
    assert out["status"] == "terminal" and out["reason"] == "died:spikes" and out["score"] == 0


def test_reset_restores_the_initial_state():
    ep = Episode("S2")
    first = ep.reset(7)
    ep.step("kid", "RIGHT")
    assert ep.reset(7) == first
    assert ep.outcome()["actions"] == 0
