"""Heuristic baseline (rubric 4b): observation-only, deterministic, legal.

Only the tuning situations S1-S3 are used here; held-out H1-H3 are run by
evaluate.py, never used to tune the baseline (docs/EVALUATION_SUITE.md).
"""

import pytest

from agents.baseline import BaselinePlayer, Pose, RoomView, plan
from pop.runner import run_episode


@pytest.mark.parametrize("sid", ["S1", "S2", "S3"])
def test_baseline_wins_tuning_situations_without_invalid_actions(sid):
    res = run_episode(BaselinePlayer(), sid, seed=0)
    assert res["outcome"]["reason"] == "won"
    assert res["outcome"]["invalid_actions"] == 0
    assert res["model_calls"] == 0
    assert all(r["source"] == "baseline" for r in res["trace"])


def test_baseline_is_deterministic():
    a = run_episode(BaselinePlayer(), "S3", seed=0)["trace"]
    b = run_episode(BaselinePlayer(), "S3", seed=0)["trace"]
    strip = lambda t: [(r["action"], r["kid"], r["room"]) for r in t]  # noqa: E731
    assert strip(a) == strip(b)


def _obs(tiles, row=1, col=0, facing="right", left=False, right=True, gates=(), exits=()):
    return {"room": "room-x", "tiles": list(tiles),
            "state": {"gates": list(gates), "exits": list(exits), "spikes_sprung": [],
                      "loose_shaking": [], "plates_pressed": []},
            "edges": {"left": left, "right": right},
            "kid": {"row": row, "col": col, "facing": facing, "posture": "standing",
                    "hp": 3, "max_hp": 3},
            "minutes_left": 60, "actions_left": 10, "last_result": None, "task": "t"}


def test_planner_never_runs_onto_spikes():
    view = RoomView(_obs(["##########", "__^_______", "##########"]))
    path = plan(view, Pose(1, 0, +1), lambda r: r == "leave_right")
    assert path and path[:2] != ["RIGHT", "RIGHT"]          # would run onto col 2
    assert view.predict(Pose(1, 1, +1), "RIGHT")[0] == "dead"
    assert view.predict(Pose(1, 1, +1), "STEP_RIGHT")[0] == Pose(1, 2, +1)


def test_planner_treats_an_unseen_pit_as_deadly():
    view = RoomView(_obs(["##########", "__..______", "##..######"]))
    assert view.predict(Pose(1, 1, +1), "RIGHT")[0] == "dead"
    assert view.predict(Pose(1, 1, +1), "JUMP_RIGHT")[0] == Pose(1, 4, +1)


def test_baseline_waits_while_falling_and_only_uses_legal_actions():
    player = BaselinePlayer()
    obs = _obs(["##########", "__________", "##########"])
    obs["kid"]["posture"] = "falling"
    assert player.decide(obs, ["WAIT"]) == "WAIT"
    obs["kid"]["posture"] = "standing"
    assert player.decide(obs, ["WAIT"]) == "WAIT"        # its choice was not legal


def test_closed_gate_is_a_wall_until_it_stops_barring():
    gate = {"row": 1, "col": 3, "open_pct": 10, "bars": True}
    view = RoomView(_obs(["##########", "___G______", "##########"], gates=[gate]))
    assert plan(view, Pose(1, 0, +1), lambda r: r == "leave_right") is None
    gate = dict(gate, open_pct=80, bars=False)
    view = RoomView(_obs(["##########", "___G______", "##########"], gates=[gate]))
    assert plan(view, Pose(1, 0, +1), lambda r: r == "leave_right")
