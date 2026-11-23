"""Regressions from the flip (R-V22) audit and independent review, 2026-11-18
(docs/audits/AUDIT-2026-11-18-flip-r-v22.md,
docs/reviews/INDEPENDENT-REVIEW-flip-r-v22.md), with Saad's decisions of
2026-11-23:

- R-V23 "step in and settle": a body out of sight never stops a move. A mover
  that arrives on someone ends on the nearest free cell of the room it arrived
  in, back toward where it came from first, then forward.
- A landing cell is claimed against the other rival as well as guards, but only
  in the jumper's own room (where every seat that can see it sees `motion.to`).
- Seats plan against the frame's starting positions, so a seat id never
  changes where a move goes.
- An alert guard facing the jumper still stabs it mid-flip (kept).
- A direction on the last visible hop frame still turns the hop (kept).

Arena A: room 2 row 0 is open floor and room 1 col 9 (row 0) leads to room 2
col 0; room 1 row 0 has a gap at col 8. Deterministic, offline.
"""

from __future__ import annotations

import json

import pytest

from pop import arena
from pop import physics as P
from pop.versus import VersusEpisode
from render import versus_view

PARKED = (3, 2, 7, -1)                     # out of everyone's way (room 3, row 2)


def episode(a, b, posts=None) -> VersusEpisode:
    return VersusEpisode(arena.situation("A"), {"A": a, "B": b}, 0, guard_posts=posts or {})


def run(ep, n):
    for _ in range(n):
        ep.tick()


def me(ep, seat):
    return ep.observe(seat)["me"]


def where(ep, seat):
    return (ep._duel.rivals[seat].kid.cell)


def hold(ep, name):
    ep._duel.guards[name].pause = 10_000          # holds still at its post, facing as posted


# --- R-V23: a body out of sight never stops a move (reviewer, blocking) --------
def test_a_body_out_of_sight_does_not_change_the_jump():
    """A jumps from room 1 toward room 2. B stands just inside room 2, out of A's
    sight. Until A lands in room 3, nothing A observes may differ from the same
    jump with B elsewhere (it used to stop at the room edge, motion.to [0, 9])."""
    def frames(b):
        ep = episode((1, 0, 9, +1), b)
        assert ep.step("A", "JUMP_RIGHT")["accepted"]
        seen = []
        for _ in range(P.JUMP):
            ep.tick()
            seen.append(json.dumps(ep.observe("A"), sort_keys=True))
        return seen, ep
    hidden, ep = frames((2, 0, 0, -1))
    empty, _ = frames(PARKED)
    assert hidden == empty
    run(ep, 2)
    assert where(ep, "A") == (2, 0, 2)                        # landed beyond, in room 2
    assert [(f["kind"], f["col"]) for f in ep.observe("A")["figures"]] == [("rival", 0)]


def test_running_into_someone_out_of_sight_steps_in_and_settles():
    """A runs from room 1 col 9 into room 2 col 0, where B stands unseen. A is not
    bumped back; it enters room 2 (now seeing B) on the nearest free cell: none
    behind it in room 2, so just past B."""
    ep = episode((1, 0, 9, +1), (2, 0, 0, +1))
    assert ep.step("A", "RIGHT")["accepted"]
    ep.tick()
    assert me(ep, "A")["motion"]["effect"] == "moved"         # not "bumped"
    run(ep, P.RUN + 1)
    assert where(ep, "A") == (2, 0, 1) and where(ep, "B") == (2, 0, 0)
    assert [f["col"] for f in ep.observe("A")["figures"]] == [0]


def test_running_into_a_guard_out_of_sight_steps_in_and_settles():
    ep = episode((1, 0, 9, +1), PARKED, posts={"g": (2, 0, (0, 0), +1)})
    hold(ep, "g")
    ep.step("A", "RIGHT")
    ep.tick()
    assert me(ep, "A")["motion"]["effect"] == "moved"
    run(ep, P.RUN + 1)
    assert where(ep, "A") == (2, 0, 1) and ep._duel.guards["g"].cell == (2, 0, 0)


def test_a_body_in_sight_still_blocks():
    ep = episode((2, 0, 3, +1), (2, 0, 4, -1))
    ep.step("A", "RIGHT")
    ep.tick()
    assert me(ep, "A")["motion"]["effect"] == "bumped"


# --- landing cells (reviewer should-fix; audit finding 1) -----------------------
@pytest.mark.parametrize("disguised", [False, True])
def test_the_other_rival_cannot_step_into_a_landing_cell_in_sight(disguised):
    """Like a guard, the other rival (disguised or not) cannot step into the cell a
    jumper in its room will land in; it used to, and the jumper snapped back to
    its take-off cell. Guards and rivals now behave the same here (no tell)."""
    ep = episode((2, 0, 3, +1), (2, 0, 7, -1))
    ep._duel.rivals["B"].disguised = disguised
    ep.step("A", "JUMP_RIGHT")
    ep.tick()
    assert me(ep, "A")["motion"]["to"] == [0, 6]
    ep.step("B", "STEP_LEFT")
    ep.tick()
    assert me(ep, "B")["motion"]["effect"] == "bumped"
    run(ep, P.JUMP + 2)
    assert where(ep, "A") == (2, 0, 6) and where(ep, "B") == (2, 0, 7)


def test_a_jumper_landing_on_someone_from_another_room_settles_beside_them():
    """B enters room 2 at col 0 from room 1 (it could not see A's landing cell)
    while A is in the air toward that cell. A lands on the nearest free cell
    back toward its take-off, col 1, not back on its take-off cell, col 3."""
    ep = episode((2, 0, 3, -1), (1, 0, 9, +1))
    ep.step("A", "JUMP_LEFT")
    ep.tick()
    assert me(ep, "A")["motion"]["to"] == [0, 0]
    ep.step("B", "RIGHT")
    run(ep, P.JUMP + 2)
    assert where(ep, "B") == (2, 0, 0)
    assert where(ep, "A") == (2, 0, 1)


def test_a_move_started_on_the_landing_frame_is_planned_from_the_settled_cell():
    """Reviewer: a pending move that starts in the frame the jumper lands was
    planned from the cell it was then moved off. It is planned again from the
    settled cell: here B now stands in front, so the step bumps."""
    ep = episode((2, 0, 3, -1), (1, 0, 9, +1))
    ep.step("A", "JUMP_LEFT")
    ep.tick()
    ep.step("B", "RIGHT")
    run(ep, P.JUMP - 2)
    ep.step("A", "STEP_LEFT")                                 # queued for the landing
    seen = []
    for _ in range(6):
        ep.tick()
        if me(ep, "A")["motion"]:
            seen.append(me(ep, "A")["motion"]["effect"])
    assert where(ep, "A") == (2, 0, 1)
    assert seen and seen[-1] == "bumped" and "moved" not in seen


def test_a_landing_cell_in_another_room_is_not_claimed():
    """A guard in room 2 must not react to a jump it cannot see coming from
    room 1: the claim covers only the jumper's own room (reviewer)."""
    ep = episode((1, 0, 9, +1), PARKED, posts={"g": (2, 0, (4, 4), -1)})
    ep.step("A", "JUMP_RIGHT")
    ep.tick()
    duel = ep._duel
    assert duel.rivals["A"].plan["to"] == (2, 0, 2)
    assert duel.cell_free_for_guard(duel.guards["g"], (2, 0, 2))


# --- seat order (reviewer should-fix; audit finding 1a) ------------------------
@pytest.mark.parametrize("k", range(0, 7))
def test_where_a_jump_goes_does_not_depend_on_the_seat_id(k):
    """The jumper starts on the frame the other rival's run arrives (k = 4 used to
    differ: seat A planned before B's arrival and seat B after A's)."""
    def go(jumper, runner):
        st = {jumper: (2, 0, 2, +1), runner: (2, 0, 5, -1)}
        ep = episode(st["A"], st["B"])
        ep.step(runner, "LEFT")
        run(ep, k)
        ep.step(jumper, "JUMP_RIGHT")
        ep.tick()
        m = me(ep, jumper)["motion"]
        run(ep, P.JUMP + 2)
        return m["effect"], m["to"], where(ep, jumper), where(ep, runner)
    assert go("A", "B") == go("B", "A")


# --- hidden information around the flip -----------------------------------------
def test_flipping_over_a_disguised_rival_looks_like_flipping_over_a_guard():
    """The flipper's whole observation, frame by frame through the flight, is the
    same whether the figure it flips over is a guard or the disguised rival (and
    the other figure is the other one), and so is where it lands. After landing
    a real guard facing it sees it and draws; that is the guard's own sight
    (R-V14), which a disguised rival does not have, not part of the flip."""
    def frames(b_col, g_col):
        ep = episode((2, 0, 3, +1), (2, 0, b_col, +1), posts={"g": (2, 0, (g_col, g_col), +1)})
        hold(ep, "g")
        ep._duel.rivals["B"].disguised = True
        ep.step("A", "JUMP_RIGHT")
        seen = []
        for _ in range(P.JUMP):
            ep.tick()
            seen.append(json.dumps(ep.observe("A"), sort_keys=True))
        ep.tick()
        seen.append(json.dumps(ep.observe("A")["me"], sort_keys=True))     # landed
        return seen
    over_rival, over_guard = frames(4, 8), frames(8, 4)
    assert over_rival == over_guard
    assert '"flipped"' in over_rival[1]


def test_a_seat_in_another_room_never_sees_the_flip():
    ep = episode((2, 0, 3, +1), (3, 0, 5, -1), posts={"g": (2, 0, (4, 4), +1)})
    hold(ep, "g")
    ep.step("A", "JUMP_RIGHT")
    for _ in range(P.JUMP + 2):
        ep.tick()
        obs = ep.observe("B")
        assert obs["figures"] == [] and "flipped" not in json.dumps(obs)


def test_a_seat_cannot_send_the_internal_hop_flip():
    ep = episode((2, 0, 3, +1), PARKED)
    before = json.dumps(ep._duel.snapshot(), sort_keys=True, default=str)
    for action in ("_HOP_FLIP_LEFT", "_HOP_FLIP_RIGHT"):
        res = ep.step("A", action)
        assert res["accepted"] is False
    assert json.dumps(ep._duel.snapshot(), sort_keys=True, default=str) == before
    assert ep.outcome()["invalid_inputs"]["A"] == 2


def test_flips_and_hop_flips_are_deterministic():
    def trace():
        ep = episode((2, 0, 3, +1), (2, 0, 4, -1), posts={"g": (2, 0, (7, 8), +1)})
        script = {0: ("A", "UP"), 2: ("A", "RIGHT"), 1: ("B", "RUN_JUMP_LEFT"),
                  20: ("B", "UP"), 22: ("B", "LEFT")}
        out = []
        for f in range(40):
            if f in script:
                ep.step(*script[f])
            ep.tick()
            out.append(json.dumps([ep.observe("A"), ep.observe("B")], sort_keys=True))
        return out
    assert trace() == trace()


# --- the observation agrees with itself (reviewer note) -------------------------
@pytest.mark.parametrize("action, effect", [("RUN_JUMP_RIGHT", "flipped"),
                                            ("JUMP_RIGHT", "jumped")])
def test_last_result_names_the_same_effect_as_the_motion(action, effect):
    ep = episode((2, 0, 1, +1), PARKED)
    ep.step("A", action)
    shown = set()
    for _ in range(P.RUN + P.JUMP + 2):
        ep.tick()
        if me(ep, "A")["motion"]:
            shown.add(me(ep, "A")["motion"]["effect"])
    assert effect in shown
    assert ep.observe("A")["last_result"]["effect"] == effect


def test_a_hop_flip_reports_a_flip_when_it_ends():
    ep = episode((2, 0, 1, +1), PARKED)
    ep.step("A", "UP")
    run(ep, 2)
    ep.step("A", "RIGHT")
    run(ep, P.JUMP + 2)
    assert ep.observe("A")["last_result"]["effect"] == "flipped"


# --- kept by Saad (2026-11-23), now tested --------------------------------------
def test_a_direction_on_the_last_hop_frame_still_flips():
    """The seat still sees itself hopping on frame 8 of 8, so that frame counts."""
    ep = episode((2, 0, 1, +1), PARKED)
    ep.step("A", "UP")
    run(ep, P.JUMP_IN_PLACE)
    m = me(ep, "A")["motion"]
    assert (m["effect"], m["frame"], m["frames"]) == ("none", P.JUMP_IN_PLACE, P.JUMP_IN_PLACE)
    ep.step("A", "RIGHT")
    ep.tick()
    assert me(ep, "A")["motion"]["effect"] == "flipped"


def test_an_alert_guard_facing_the_jumper_stabs_it_mid_flip():
    """The jumper keeps its take-off cell until it lands, so a guard facing it
    sees it and stabs it there (VERSUS_SPEC R-V22: a lunge into that cell still
    hits it). Flip over a guard that faces away or has not seen you."""
    ep = episode((2, 0, 3, +1), PARKED, posts={"g": (2, 0, (4, 4), -1)})
    ep.step("A", "JUMP_RIGHT")
    run(ep, P.JUMP + 2)
    assert me(ep, "A")["hp"] == 2
    assert where(ep, "A") != (2, 0, 6)


# --- the picture (reviewer note) -------------------------------------------------
def test_a_running_flip_leaves_the_floor_on_its_first_frame():
    """A running jump takes off at once (pop/engine.py: depart 0); its flip used
    the standing jump's timing and stayed on the floor for the first ~20%."""
    def poses(frames):
        view = {"row": 0, "col": 3, "facing": "right", "posture": "standing",
                "motion": {"effect": "flipped", "frame": 1, "frames": frames, "to": [0, 7],
                           "to_posture": "standing", "to_facing": "right"}}
        out = []
        for f in range(1, frames + 1):
            view["motion"]["frame"] = f
            out.append(versus_view.pose(view, "2"))
        return out
    running = poses(P.RUN_JUMP_FLIGHT)
    assert len(running) == P.RUN_JUMP_FLIGHT
    assert running[0].spin > 0
    assert [p.spin for p in running] == sorted(p.spin for p in running)
    assert running[-1].spin in (0, 360)
    standing = poses(P.JUMP)
    assert standing[0].spin == 0                               # unchanged: crouch, then up
