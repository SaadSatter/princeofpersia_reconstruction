"""R-V22: a jump to the side can flip over someone, and every running jump is a
flip (Saad, 2026-11-17).

A standing or running jump may pass over a cell holding the other rival or a
standing guard in the jumper's own room. It never lands on anyone; walls and
closed gates still stop it, and a body in another room still blocks (the
jumper cannot see it, so the jump must not reveal it). A jump that passes over
someone is shown as a 360-degree flip: its motion effect is "flipped".

Deterministic, offline. Room 2 row 0 and room 3 row 0 of arena A are open floor
(pop/arena.py); room 3 has a wall at col 9.
"""

from __future__ import annotations

import math

from pop import arena
from pop import physics as P
from pop.versus import VersusEpisode
from render import versus_view


def episode(a, b, posts=None) -> VersusEpisode:
    return VersusEpisode(arena.situation("A"), {"A": a, "B": b}, 0, guard_posts=posts or {})


def run(ep, n):
    for _ in range(n):
        ep.tick()


def me(ep, seat):
    return ep.observe(seat)["me"]


def jump_and_land(ep, seat, action, frames):
    assert ep.step(seat, action)["accepted"]
    run(ep, 1)
    motion = me(ep, seat)["motion"]
    run(ep, frames)
    return motion


def test_a_standing_jump_flips_over_the_adjacent_rival_and_lands_beyond():
    ep = episode((2, 0, 3, +1), (2, 0, 4, -1))
    motion = jump_and_land(ep, "A", "JUMP_RIGHT", P.JUMP)
    assert motion["effect"] == "flipped" and motion["to"] == [0, 6]
    assert (me(ep, "A")["row"], me(ep, "A")["col"]) == (0, 6)
    assert me(ep, "A")["posture"] == "standing"
    assert (me(ep, "B")["col"], me(ep, "B")["hp"]) == (4, 3)          # B untouched


def test_the_other_rival_sees_the_flip():
    ep = episode((2, 0, 3, +1), (2, 0, 4, -1))
    ep.step("A", "JUMP_RIGHT")
    run(ep, 3)
    (fig,) = ep.observe("B")["figures"]
    assert fig["kind"] == "rival" and fig["motion"]["effect"] == "flipped"


def test_a_running_jump_flips_over_a_rival_two_cells_ahead():
    ep = episode((2, 0, 1, +1), (2, 0, 3, -1))
    assert ep.step("A", "RUN_JUMP_RIGHT")["accepted"]
    run(ep, P.RUN + 2)                                   # past the run-up, in the air
    assert me(ep, "A")["motion"]["effect"] == "flipped"
    run(ep, P.RUN_JUMP_FLIGHT)
    assert me(ep, "A")["col"] == 6 and me(ep, "A")["posture"] == "standing"


def test_every_running_jump_is_a_flip_even_with_nobody_to_pass():
    """Saad, 2026-11-17: a running jump flips at any point, over holes and spikes
    too. Room 1 row 0 has a gap at col 8 (pop/arena.py)."""
    ep = episode((1, 0, 4, +1), (3, 2, 7, -1))
    ep.step("A", "RUN_JUMP_RIGHT")
    run(ep, P.RUN + 1)
    assert me(ep, "A")["motion"]["effect"] == "flipped"
    run(ep, P.RUN_JUMP_FLIGHT)
    assert me(ep, "A")["col"] == 9 and me(ep, "A")["posture"] == "standing"


def test_a_running_flip_clears_spikes():
    """Room 5 row 2 has spikes at col 3: the flip flies over them unhurt."""
    ep = episode((5, 2, 0, +1), (3, 2, 7, -1))
    ep.step("A", "RUN_JUMP_RIGHT")
    run(ep, P.RUN + 1)
    assert me(ep, "A")["motion"]["effect"] == "flipped"
    run(ep, P.RUN_JUMP_FLIGHT)
    assert (me(ep, "A")["col"], me(ep, "A")["hp"], me(ep, "A")["posture"]) == (5, 3, "standing")


def test_a_standing_jump_with_nobody_to_pass_does_not_flip():
    ep = episode((1, 0, 2, +1), (3, 2, 7, -1))
    motion = jump_and_land(ep, "A", "JUMP_RIGHT", P.JUMP)
    assert motion["effect"] == "jumped"


def test_regression_running_jump_flight_counts_its_own_frames():
    """The flight of a running jump is planned after the 4-frame run-up; its motion
    used to report frames 5-12 of 8, so the picture started mid-flight and froze
    on the landing pose. It now counts 1-8 from take-off."""
    ep = episode((1, 0, 4, +1), (3, 2, 7, -1))
    ep.step("A", "RUN_JUMP_RIGHT")
    seen = []
    for _ in range(P.RUN + P.RUN_JUMP_FLIGHT):
        ep.tick()
        m = me(ep, "A")["motion"]
        seen.append((m["effect"], m["frame"], m["frames"]))
    assert seen[:P.RUN] == [("moved", i, P.RUN) for i in range(1, P.RUN + 1)]
    assert seen[P.RUN:] == [("flipped", i, P.RUN_JUMP_FLIGHT)
                            for i in range(1, P.RUN_JUMP_FLIGHT + 1)]


def test_a_jump_flips_over_a_standing_guard():
    # The guard faces away (a guard facing A would see it and stab it, R-V15).
    ep = episode((2, 0, 3, +1), (3, 2, 7, -1), posts={"g": (2, 0, (4, 4), +1)})
    motion = jump_and_land(ep, "A", "JUMP_RIGHT", P.JUMP)
    assert motion["effect"] == "flipped"
    assert me(ep, "A")["col"] == 6 and ep._duel.guards["g"].col == 4


def test_a_jump_with_nobody_in_the_way_is_an_ordinary_jump():
    ep = episode((2, 0, 1, +1), (3, 2, 7, -1))
    motion = jump_and_land(ep, "A", "JUMP_RIGHT", P.JUMP)
    assert motion["effect"] == "jumped" and me(ep, "A")["col"] == 4


def test_a_flip_never_lands_on_the_rival_nor_passes_a_wall():
    # B at col 8, wall at col 9: nowhere to land beyond B, so no flip.
    ep = episode((3, 0, 7, +1), (3, 0, 8, -1))
    motion = jump_and_land(ep, "A", "JUMP_RIGHT", P.JUMP_IN_PLACE)
    assert motion["effect"] == "bumped"
    assert me(ep, "A")["col"] == 7 and me(ep, "B")["col"] == 8
    # B at col 7, wall at col 9: lands at col 8, between B and the wall.
    ep = episode((3, 0, 6, +1), (3, 0, 7, -1))
    motion = jump_and_land(ep, "A", "JUMP_RIGHT", P.JUMP)
    assert motion["effect"] == "flipped" and me(ep, "A")["col"] == 8


def test_a_rival_in_the_next_room_still_blocks_and_is_not_revealed():
    """B stands just inside the next room, out of A's sight: A's jump stops at the
    room edge as before, and nothing A observes names a flip."""
    ep = episode((2, 0, 8, +1), (3, 0, 0, -1))
    room = ep.observe("A")["room"]
    motion = jump_and_land(ep, "A", "JUMP_RIGHT", P.JUMP)
    assert motion["effect"] == "jumped" and motion["to"] == [0, 9]
    assert me(ep, "A")["col"] == 9 and ep.observe("A")["room"] == room
    assert ep.observe("A")["figures"] == []


def test_a_dive_kick_is_legal_during_a_flip():
    ep = episode((2, 0, 3, +1), (2, 0, 4, -1))
    ep.step("A", "JUMP_RIGHT")
    run(ep, P.JUMP_DEPART + 2)
    assert "KICK" in ep.legal_actions("A")


def test_a_guard_does_not_walk_into_a_flipping_rivals_landing_cell():
    """The flipper keeps its cell until it lands; its landing cell is claimed for
    the whole flight so a patrolling guard cannot step into it meanwhile."""
    ep = episode((2, 0, 3, +1), (3, 2, 7, -1), posts={"g": (2, 0, (4, 4), -1)})
    ep.step("A", "JUMP_RIGHT")
    run(ep, 1)
    duel = ep._duel
    assert not duel.cell_free_for_guard(duel.guards["g"], (2, 0, 6))
    assert duel.cell_free_for_guard(duel.guards["g"], (2, 0, 5))


# --- the picture -------------------------------------------------------------
def _poses(effect, frames=P.JUMP):
    view = {"row": 0, "col": 3, "facing": "right", "posture": "standing",
            "motion": {"effect": effect, "frame": 1, "frames": frames, "to": [0, 6],
                       "to_posture": "standing", "to_facing": "right"}}
    out = []
    for f in range(1, frames + 1):
        view["motion"]["frame"] = f
        out.append(versus_view.pose(view, "2"))
    return out


def test_a_flip_turns_once_around_and_rises_over_the_head():
    flip, plain = _poses("flipped"), _poses("jumped")
    spins = [p.spin for p in flip]
    assert spins[0] == 0 and spins[-1] in (0, 360)
    assert max(spins) >= 300 and spins == sorted(spins)               # one full turn, forward
    assert all(p.spin == 0 for p in plain)
    lift = [q.y - p.y for p, q in zip(flip, plain)]
    assert max(lift) >= 12 and lift[0] == 0 and lift[-1] == 0          # higher arc, same ends
    assert [p.x for p in flip] == [p.x for p in plain]
    assert not any(math.isnan(p.spin) for p in flip)
