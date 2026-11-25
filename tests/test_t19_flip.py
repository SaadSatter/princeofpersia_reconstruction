"""T19, decision #53 (Saad, 2026-11-24): flip is the default jump.

Every directional jump, standing or running, is a flip in that direction. Distances,
landing rules, claims, walls, gates and R-V23 stay as they were. `UP` under a ledge
still climbs; `UP` on open floor with no direction is still a hop. Deterministic,
offline. Room 2 row 0 is open floor (pop/arena.py); room 2 row 2 col 1 has a ledge
above it (a climb).
"""

from __future__ import annotations

from pop import arena
from pop import physics as P
from pop.versus import VersusEpisode


def episode(a, b) -> VersusEpisode:
    return VersusEpisode(arena.situation("A"), {"A": a, "B": b}, 0, guard_posts={})


def run(ep, n):
    for _ in range(n):
        ep.tick()


def me(ep, seat="A"):
    return ep.observe(seat)["me"]


FAR = (3, 2, 7, -1)           # B, out of the way


def jump(a, action):
    ep = episode(a, FAR)
    assert ep.step("A", action)["accepted"]
    run(ep, 1)
    motion = me(ep)["motion"]
    run(ep, P.JUMP + 1)
    return ep, motion


def test_a_standing_jump_right_over_open_floor_is_a_flip_with_todays_distance():
    ep, motion = jump((2, 0, 1, +1), "JUMP_RIGHT")
    assert motion["effect"] == "flipped" and motion["to"] == [0, 4]
    assert ep._duel.last_result["A"]["effect"] == "flipped"
    assert (me(ep)["col"], me(ep)["posture"]) == (4, "standing")


def test_a_standing_jump_left_over_open_floor_is_a_flip_with_todays_distance():
    ep, motion = jump((2, 0, 5, -1), "JUMP_LEFT")
    assert motion["effect"] == "flipped" and motion["to"] == [0, 2]
    assert ep._duel.last_result["A"]["effect"] == "flipped"
    assert me(ep)["col"] == 2


def test_a_jump_against_a_wall_is_still_a_bump_not_a_flip():
    ep, motion = jump((3, 0, 8, +1), "JUMP_RIGHT")      # room 3 has a wall at col 9
    assert motion["effect"] == "bumped"


def test_a_jump_opposite_the_facing_flips_that_way_with_no_separate_turn():
    """Jump pressed toward the other way: one flip in that direction, not a turn then a jump."""
    ep = episode((2, 0, 5, +1), FAR)
    assert ep.step("A", "JUMP_LEFT")["accepted"]
    run(ep, 1)
    m = me(ep)["motion"]
    assert m["effect"] == "flipped" and m["to"] == [0, 2] and me(ep)["facing"] == "left"
    run(ep, P.JUMP + 1)
    assert me(ep)["col"] == 2


def test_a_hop_on_open_floor_is_still_a_hop():
    ep = episode((2, 0, 1, +1), FAR)
    ep.step("A", "UP")
    run(ep, 1)
    assert me(ep)["motion"]["effect"] == "none"
    run(ep, P.JUMP_IN_PLACE + 1)
    assert (me(ep)["row"], me(ep)["col"]) == (0, 1)


def test_up_under_a_ledge_still_climbs():
    ep = episode((2, 2, 1, +1), FAR)
    ep.step("A", "UP")
    run(ep, 1)
    assert me(ep)["motion"]["effect"] == "climbed"


def test_a_direction_during_a_hop_still_flips_that_way():
    ep = episode((2, 0, 3, +1), FAR)
    ep.step("A", "UP")
    run(ep, 2)
    ep.step("A", "LEFT")
    run(ep, 1)
    m = me(ep)["motion"]
    assert m["effect"] == "flipped" and m["to"] == [0, 0]


def test_a_running_jump_is_still_a_flip():
    ep = episode((2, 0, 1, +1), FAR)
    ep.step("A", "RUN_JUMP_RIGHT")
    run(ep, P.RUN + 2)
    assert me(ep)["motion"]["effect"] == "flipped"
    run(ep, P.RUN_JUMP_FLIGHT)
    assert me(ep)["col"] == 6


def test_the_other_seat_sees_the_flip_in_its_own_room():
    ep = episode((2, 0, 1, +1), (2, 0, 8, -1))
    ep.step("A", "JUMP_RIGHT")
    run(ep, 3)
    (fig,) = ep.observe("B")["figures"]
    assert fig["motion"]["effect"] == "flipped"


def test_flips_are_deterministic():
    def trace():
        ep = episode((2, 0, 1, +1), FAR)
        out = []
        for t, act in enumerate(["JUMP_RIGHT"] + [None] * 14 + ["JUMP_LEFT"] + [None] * 14):
            if act:
                ep.step("A", act)
            ep.tick()
            out.append(ep._duel.snapshot())
        return out
    assert trace() == trace()
