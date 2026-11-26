"""T24 Gate 2 (evaluation specialist): QA F1, a ledge-edge DOWN with a body on the rival's own cell.

DOWN at an edge is the engine's hang-down (and the macro planner's `_hang_drop`). The T24
posture guard only protects a rival that is already hanging. A *standing* rival at the edge
that shares its cell with a downed uniformed guard now takes the uniform instead of hanging.
This documents the behaviour; it is not a claim that the rule is wrong.
"""
from __future__ import annotations

from agents.macros import ALL_ACTIONS
from pop import arena
from pop import versus as V
from pop.versus import VersusEpisode

EDGE = (1, 0, 7, +1)                       # room 1, top row: the hole is at col 8, ahead
POSTS = {"down": (1, 0, (7, 7), +1)}


def edge_episode(body=True):
    posts = POSTS if body else {}
    ep = VersusEpisode(arena.situation("A"), dict(arena.STARTS, A=EDGE, B=(3, 2, 7, -1)), 0,
                       guard_posts=posts)
    if body:
        ep._duel.guards["down"].knock_out()
    return ep


def run(ep, n):
    for _ in range(n):
        ep.tick()


def test_planner_may_offer_down_so_the_hazard_is_reachable():
    assert "DOWN" in ALL_ACTIONS


def test_down_at_a_ledge_edge_with_no_body_still_hangs():
    ep = edge_episode(body=False)
    ep.step("A", "DOWN")
    run(ep, 30)
    assert ep._duel.rivals["A"].kid.posture == "hanging"
    assert ep._duel.rivals["A"].disguised is False


def test_down_at_a_ledge_edge_standing_over_a_body_takes_the_uniform_instead_of_hanging():
    """QA F1 reproduced: the standing hang-down becomes a take. Rare (needs a body on the edge cell)."""
    ep = edge_episode(body=True)
    r = ep._duel.rivals["A"]
    assert r._kneel_target() == "uniform"
    ep.step("A", "DOWN")
    run(ep, V.TAKE_FRAMES + 2)
    assert r.disguised is True and r.kid.posture == "standing"
    assert ep.observe("A")["last_result"]["effect"] == "took_uniform"
