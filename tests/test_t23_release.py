"""T23, decision #93 (Saad, 2026-11-25): a released direction never runs after landing.

Saad's sequence: left, jump and flip left, hold left during the flight, release before
landing. The queued left must not start after the landing (and must not be logged as a
move). Holding the direction through the landing still runs on; AI seats, which press no
keys, keep their one-pending-input rule. The shared input path is `VersusEpisode.release`
(pop/versus.py), called by `WebGame.tick` (hosted page and server).
"""

from __future__ import annotations

from pop import arena
from pop.versus import VersusEpisode
from web import bridge

START = {"A": (2, 0, 8, -1), "B": (3, 2, 7, -1)}
N = 30


def game():
    ep = VersusEpisode(arena.situation("A"), START, 0, guard_posts={})
    return bridge.WebGame(mode="local_two_players", seed=0, episode=ep), ep


def keys(*held):
    return {k: k in held for k in ("a", "d", "w", "s", "f", "g", "t")}


def play(script, n=N):
    """script(t) -> physical keys held on tick t. Returns per-tick (col, started) and ep."""
    g, ep = game()
    rows = []
    for t in range(n):
        g.press(keys(*script(t)))
        g.tick()
        s = ep.started_move("A")
        rows.append((ep.observe("A")["me"]["col"], None if s is None else str(s)))
    return rows, ep


def flight(release_at):
    """left+up (a flip left) for 2 ticks, then left held until `release_at`."""
    def script(t):
        if t < 2:
            return ("a", "w")
        return ("a",) if t < release_at else ()
    return script


def test_released_direction_does_not_run_after_landing():
    held, _ = play(flight(10**6))
    rel, ep = play(flight(6))
    assert rel[-1][0] > held[-1][0]                      # holding on ran further left
    starts = [i for i, (_, s) in enumerate(rel) if s]
    assert len(starts) == 1, rel                         # only the flip started
    after = [col for col, _ in rel[starts[0] + 14:]]     # after the flip has landed
    assert len(set(after)) == 1, rel                     # no movement after the landing
    assert [a for _, _, a in ep.log].count("LEFT") >= 1  # the key was accepted while held


def test_holding_through_the_landing_still_runs_on():
    rows, _ = play(flight(10**6))
    starts = [i for i, (_, s) in enumerate(rows) if s]
    assert len(starts) >= 4, rows                        # the run goes on after the flip


def test_release_clears_only_that_seats_pending_input():
    ep = VersusEpisode(arena.situation("A"), START, 0, guard_posts={})
    ep.step("A", "LEFT")
    ep.release("B")
    assert ep._duel.pending["A"] == "LEFT"
    ep.release("A")
    assert ep._duel.pending["A"] is None
    ep.tick()
    assert ep.observe("A")["me"]["col"] == 8
    assert len(ep.log) == 1                              # the accepted input stays in the trace
