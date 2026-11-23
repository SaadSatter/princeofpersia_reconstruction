"""QA T02: independent probes of R-V23 "step in and settle" (commit 13c7488).

Written by the QA subagent, which did not write R-V23. Each test plays the
duel through the seat interface (`step`, `tick`, `observe`); the engine is
read only to say where a body ended up. Arena A (pop/arena.py):

    room 2 row 0  "___t__t___"   open floor
    room 2 row 1  "_._p_G_p._"   hole at cols 1 and 8, gate at col 5
    room 2 row 2  "__^_.._^__"   spikes at cols 2 and 7
    room 1 col 9 leads right into room 2 col 0; room 3 col 0 leads left into
    room 2 col 9.

Deterministic, offline, no keys.
"""

from __future__ import annotations

import json

import pytest

from pop import arena
from pop import physics as P
from pop import tiles as T
from pop.versus import VersusEpisode

PARKED = (3, 2, 7, -1)                     # out of everyone's way (room 3, row 2)


def episode(a, b, posts=None, hold=True) -> VersusEpisode:
    ep = VersusEpisode(arena.situation("A"), {"A": a, "B": b}, 0, guard_posts=posts or {})
    if hold:
        for g in ep._duel.guards.values():
            g.pause = 10_000                  # each guard stands still at its post
    return ep


def where(ep, seat):
    return ep._duel.rivals[seat].kid.cell


def run(ep, n):
    for _ in range(n):
        ep.tick()


# --- both rivals arriving together ------------------------------------------------
@pytest.mark.parametrize("mover, holder", [("A", "B"), ("B", "A")])
def test_qa_t02_two_rivals_arriving_in_one_doorway_cell_both_stay_out(mover, holder):
    """R-V00 kept under R-V23: one rival runs from room 1 into room 2 col 0 while
    the other, in room 2, runs left into the same cell. Neither could see the
    other. Both go back where they were, for either seat assignment."""
    st = {mover: (1, 0, 9, +1), holder: (2, 0, 1, -1)}
    ep = episode(st["A"], st["B"])
    assert ep.step(mover, "RIGHT")["accepted"]
    assert ep.step(holder, "LEFT")["accepted"]
    run(ep, P.RUN + 2)
    assert where(ep, mover) == (1, 0, 9)
    assert where(ep, holder) == (2, 0, 1)
    assert ep.observe("A")["me"]["hp"] == ep.observe("B")["me"]["hp"] == 3


def test_qa_t02_two_jumpers_whose_settle_cells_coincide_both_go_back():
    """R-V23: 'so do two whose settle cells would be the same'. A jumps from
    room 1 onto a guard at (2,0,2); B jumps from room 3 onto a guard at (2,0,7).
    Guards fill every other cell but col 3 (and col 0, behind A's way back), so
    both would settle in col 3: both go back where they were."""
    posts = {f"g{c}": (2, 0, (c, c), +1) for c in (1, 2, 4, 5, 6, 7, 8, 9)}
    ep = episode((1, 0, 9, +1), (3, 0, 0, -1), posts)
    assert ep.step("A", "JUMP_RIGHT")["accepted"]
    assert ep.step("B", "JUMP_LEFT")["accepted"]
    run(ep, P.JUMP + 2)
    assert where(ep, "A") == (1, 0, 9) and where(ep, "B") == (3, 0, 0)


# --- settling never ends on spikes, a hole, or past a closed gate ---------------
def test_qa_t02_settle_skips_a_hole():
    """A runs from room 1 into room 2 row 1 col 0, onto B. Col 1 is a hole: A must
    not settle there (it settles at col 2; see the review for the crossing)."""
    ep = episode((1, 1, 9, +1), (2, 1, 0, -1))
    ep.step("A", "RIGHT")
    run(ep, P.RUN + 2)
    cell = where(ep, "A")
    assert cell[0] == 2 and cell != (2, 1, 1)
    assert ep._duel.geom.supported(cell)
    assert ep._duel.rivals["A"].kid.posture == "standing"


def test_qa_t02_settle_skips_spikes():
    """Room 2 row 2: B at col 0, a guard at col 1, spikes at col 2. A arriving
    from room 1 onto B must not settle on the spikes, and keeps all its hearts."""
    ep = episode((1, 2, 9, +1), (2, 2, 0, -1), {"g": (2, 2, (1, 1), -1)})
    ep.step("A", "RIGHT")
    run(ep, P.RUN + 2)
    cell = where(ep, "A")
    assert cell[0] == 2 and ep._duel.geom.tile(cell) != T.SPIKES
    assert ep.observe("A")["me"]["hp"] == 3


def test_qa_t02_settle_never_passes_a_closed_gate():
    """A arrives from room 3 onto B at (2,1,9). Col 8 is a hole and guards stand
    at cols 7 and 6; the only other cells lie past the gate at col 5, which is
    closed. A must not end anywhere left of the gate."""
    ep = episode((3, 1, 0, -1), (2, 1, 9, +1),
                 {"g1": (2, 1, (7, 7), -1), "g2": (2, 1, (6, 6), -1)})
    ep._duel.mech.gates[(2, 1, 5)].pos = 0
    assert ep._duel.mech.gate_bars((2, 1, 5))
    ep.step("A", "LEFT")
    run(ep, P.RUN + 2)
    cell = where(ep, "A")
    assert not (cell[0] == 2 and cell[1] == 1 and cell[2] <= 5)


# --- room edges -------------------------------------------------------------------
@pytest.mark.parametrize("start, body, action", [
    ((1, 0, 9, +1), (2, 0, 0, -1), "RIGHT"),       # arrives at col 0: back is room 1
    ((3, 0, 0, -1), (2, 0, 9, +1), "LEFT"),        # arrives at col 9: back is room 3
])
def test_qa_t02_settle_at_a_room_edge_stays_in_the_room_it_arrived_in(start, body, action):
    ep = episode(start, body)
    ep.step("A", action)
    run(ep, P.RUN + 2)
    cell = where(ep, "A")
    assert cell[0] == 2 and abs(cell[2] - body[2]) == 1
    assert where(ep, "B") == body[:3]


# --- hidden information ---------------------------------------------------------
@pytest.mark.parametrize("action, frames", [("RIGHT", P.RUN), ("STEP_RIGHT", P.STEP)])
def test_qa_t02_a_move_into_a_doorway_does_not_reveal_who_stands_there(action, frames):
    """Until it arrives, everything A observes while running or stepping from
    room 1 into room 2 col 0 is the same whether B stands there or not."""
    def frames_seen(b):
        ep = episode((1, 0, 9, +1), b)
        assert ep.step("A", action)["accepted"]
        seen = []
        for _ in range(frames):
            ep.tick()
            seen.append(json.dumps(ep.observe("A"), sort_keys=True))
        return seen
    assert frames_seen((2, 0, 0, -1)) == frames_seen(PARKED)


def test_qa_t02_settling_on_a_disguised_rival_looks_like_settling_on_a_guard():
    """R-V18 with R-V23: A runs into room 2 col 0. In one game the disguised rival
    stands there; in the other a real guard does (the disguised rival is parked
    where A cannot see it). Both face away from A's settle cell, so neither
    reacts. A's whole observation, every frame, must be the same."""
    def frames_seen(body_is_guard):
        if body_is_guard:
            ep = episode((1, 0, 9, +1), PARKED, {"g": (2, 0, (0, 0), -1)})
        else:
            ep = episode((1, 0, 9, +1), (2, 0, 0, -1))
        ep._duel.rivals["B"].disguised = True
        ep.step("A", "RIGHT")
        seen = []
        for _ in range(P.RUN + 8):
            ep.tick()
            seen.append(json.dumps(ep.observe("A"), sort_keys=True))
        return seen, where(ep, "A")
    (rival_frames, rival_end), (guard_frames, guard_end) = frames_seen(False), frames_seen(True)
    assert rival_end == guard_end == (2, 0, 1)
    assert rival_frames == guard_frames


@pytest.mark.parametrize("disguised", [False, True])
def test_qa_t02_settling_does_not_change_the_disguise_or_suspicion(disguised):
    """A jumps from room 1 onto a guard standing at its landing cell (2,0,2),
    facing away. It settles beside the guard; settling is not an act: the
    disguise stays as it was and no suspicion is added."""
    ep = episode((1, 0, 9, +1), PARKED, {"g": (2, 0, (2, 2), +1)})
    ep._duel.rivals["A"].disguised = disguised
    ep.step("A", "JUMP_RIGHT")
    run(ep, P.JUMP + 3)
    assert where(ep, "A") == (2, 0, 1)
    assert ep._duel.rivals["A"].disguised is disguised
    assert ep.observe("A")["suspicion"] == []
    assert ep.observe("A")["me"]["hp"] == 3


@pytest.mark.parametrize("a, b, acts, posts", [
    ((1, 0, 9, +1), (2, 0, 1, -1), (("X", "RIGHT"), ("Y", "LEFT")), None),
    ((1, 0, 9, +1), (2, 0, 0, -1), (("X", "RIGHT"), ("Y", "LEFT")), None),
    ((1, 1, 9, +1), (2, 1, 0, -1), (("X", "RIGHT"),), None),
    ((1, 0, 9, +1), (2, 0, 0, -1), (("X", "RIGHT"),), {"g": (2, 0, (1, 1), -1)}),
    ((1, 0, 9, +1), (2, 0, 0, -1), (("X", "RUN_JUMP_RIGHT"),), None),
])
def test_qa_t02_settling_does_not_depend_on_the_seat_id(a, b, acts, posts):
    def play(x, y):
        st = {x: a, y: b}
        ep = episode(st["A"], st["B"], posts)
        for who, act in acts:
            ep.step({"X": x, "Y": y}[who], act)
        trace = []
        for _ in range(P.JUMP + 4):
            ep.tick()
            trace.append((where(ep, x), where(ep, y),
                          json.dumps(ep.observe(x), sort_keys=True),
                          json.dumps(ep.observe(y), sort_keys=True)))
        return trace
    assert play("A", "B") == play("B", "A")
