"""T24-fix1 (Saad, decision #101): at a ledge edge DOWN keeps its hang-down meaning even over a body.

TAKE still takes the uniform there; away from an edge DOWN still takes it (#94).
"""
from __future__ import annotations

from pop import arena
from pop import versus as V
from pop.versus import VersusEpisode

EDGE = (1, 0, 7, +1)                       # the hole is at col 8, ahead
POSTS = {"down": (1, 0, (7, 7), +1)}


def episode(start=EDGE, posts=POSTS):
    ep = VersusEpisode(arena.situation("A"), dict(arena.STARTS, A=start, B=(3, 2, 7, -1)), 0,
                       guard_posts=posts)
    ep._duel.guards["down"].knock_out()
    return ep


def run(ep, n):
    for _ in range(n):
        ep.tick()


def test_down_at_the_edge_over_a_body_hangs_and_takes_nothing():
    ep = episode()
    r = ep._duel.rivals["A"]
    assert r._kneel_target() is None
    ep.step("A", "DOWN")
    run(ep, 30)
    assert r.kid.posture == "hanging" and r.disguised is False
    assert ep.observe("A")["last_result"]["effect"] == "hanging"


def test_take_at_the_edge_over_a_body_still_takes_the_uniform():
    ep = episode()
    r = ep._duel.rivals["A"]
    ep.step("A", "TAKE")
    run(ep, V.TAKE_FRAMES + 2)
    assert r.disguised is True and r.kid.posture == "standing"
    assert ep.observe("A")["last_result"]["effect"] == "took_uniform"


def test_down_away_from_the_edge_still_takes_the_uniform():
    ep = episode(start=(1, 0, 6, +1))      # body at col 7 is ahead, on floor, so ahead is supported
    r = ep._duel.rivals["A"]
    assert r._kneel_target() == "uniform"
