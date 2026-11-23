"""T01: the arena duel lasts 5 minutes (Saad, 2026-11-23, "Make the duel time
limit 5min"; OQ-3 closed): 3,600 frames at 12 per second."""

from __future__ import annotations

from pop import arena
from pop import physics as P
from pop import versus as V
from pop.versus import VersusEpisode, arena_episode


def test_arena_duel_limit_is_5_minutes_of_frames():
    assert V.DUEL_FRAMES == 5 * 60 * V.TICKS_PER_SECOND == 3600
    assert arena_episode()._duel.time_limit == V.DUEL_FRAMES


def test_arena_duel_ends_in_a_time_up_draw_at_5_minutes():
    ep = arena_episode(seed=3)
    for _ in range(V.DUEL_FRAMES - 1):
        ep.tick()
    assert ep.outcome()["status"] == "ongoing"
    ep.tick()
    out = ep.outcome()
    assert (out["status"], out["reason"], out["frames"]) == ("terminal", "draw:time_up", 3600)


def test_minutes_left_counts_down_from_the_duels_own_limit():
    ep = arena_episode()
    assert ep.observe("A")["minutes_left"] == 5
    for _ in range(12 * 60 + 1):
        ep.tick()
    assert ep.observe("A")["minutes_left"] == ep.observe("B")["minutes_left"] == 3
    short = VersusEpisode(arena.situation("A"), arena.STARTS, 0, time_limit_frames=2 * 720)
    assert short.observe("B")["minutes_left"] == 2


def test_single_player_clock_is_unchanged():
    from pop.interface import Episode
    ep = Episode("S1")
    assert ep.observe("kid")["minutes_left"] == P.GAME_FRAMES // (12 * 60) == 60
