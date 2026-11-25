"""T20-fix1 (decision #81): `VersusEpisode.started_move(seat)`, the move the engine
actually started for a seat on the last tick, after the R-V10 kick swap, the R-V22 hop
turn, the R-V35 grace cancel and stale-input drops. Read-only: it changes no rule and is
not part of any observation."""

from __future__ import annotations

import json

from pop import arena
from pop import versus as V
from pop.versus import VersusEpisode


def episode(a, b) -> VersusEpisode:
    return VersusEpisode(arena.situation("A"), dict(arena.STARTS, A=a, B=b), 0)


def run(ep, n):
    for _ in range(n):
        ep.tick()


def armed(a=(2, 0, 3, +1), b=(2, 0, 4, -1)):
    ep = episode(a, b)
    for seat in ("A", "B"):
        ep.step(seat, "DRAW")
    run(ep, V.DRAW_FRAMES + 1)
    return ep


def test_none_before_any_tick_and_when_nothing_started():
    ep = episode((2, 0, 1, +1), (3, 2, 7, -1))
    assert ep.started_move("A") is None and ep.started_move("B") is None
    ep.tick()
    assert ep.started_move("A") is None


def test_the_move_shows_for_the_tick_that_started_it_only():
    ep = episode((2, 0, 1, +1), (3, 2, 7, -1))
    ep.step("A", "RIGHT")
    ep.tick()
    assert ep.started_move("A") == "RIGHT" and ep.started_move("B") is None
    ep.tick()
    assert ep.started_move("A") is None            # still running: not a new start


def test_a_held_input_is_one_start():
    ep = episode((2, 0, 1, +1), (3, 2, 7, -1))
    starts = []
    for _ in range(10):
        if "RUN_JUMP_RIGHT" in ep.legal_actions("A"):
            ep.step("A", "RUN_JUMP_RIGHT")
        ep.tick()
        starts.append(ep.started_move("A"))
    assert [s for s in starts if s] == ["RUN_JUMP_RIGHT"]


def test_a_queued_input_is_logged_when_it_starts_not_when_asked():
    ep = episode((2, 0, 1, +1), (3, 2, 7, -1))
    ep.step("A", "UP")
    ep.tick()
    assert ep.started_move("A") == "UP"
    ep.step("A", "RIGHT")                          # asked during the hop: queued
    ep.tick()
    assert ep.started_move("A") in (None, "_HOP_FLIP_RIGHT")


def test_r_v22_a_direction_during_a_hop_is_the_flip_the_engine_started():
    ep = episode((2, 0, 1, +1), (3, 2, 7, -1))
    ep.step("A", "UP")
    ep.tick()
    ep.step("A", "JUMP_RIGHT")
    ep.tick()
    assert ep.started_move("A") == "_HOP_FLIP_RIGHT"


def test_r_v35_grace_logs_the_jump_the_engine_started():
    ep = episode((2, 0, 1, +1), (3, 2, 7, -1))
    ep.step("A", "RIGHT")
    ep.tick()
    assert ep.started_move("A") == "RIGHT"
    ep.step("A", "RUN_JUMP_RIGHT")
    ep.tick()
    assert ep.started_move("A") == "JUMP_RIGHT"    # not the submitted RUN_JUMP_RIGHT


def test_r_v10_a_kick_replaces_the_rest_of_a_jump():
    ep = armed((2, 0, 2, +1), (2, 0, 4, -1))
    ep.step("A", "JUMP_RIGHT")
    ep.tick()
    assert ep.started_move("A") == "JUMP_RIGHT"
    run(ep, 6)
    ep.step("A", "KICK")
    ep.tick()
    assert ep.started_move("A") == "KICK"


def test_a_stale_input_started_nothing():
    ep = episode((2, 0, 1, +1), (3, 2, 7, -1))
    ep.step("A", "RIGHT")
    run(ep, 1)
    before = ep.outcome()["stale_inputs"]["A"]
    # Queue something that stops being legal before it can start.
    ep.step("A", "DRAW")
    ep._duel.rivals["A"].sword = "drawn"           # a test-only change of legality
    ep.tick()
    run(ep, 3)
    assert ep.started_move("A") is None or ep.outcome()["stale_inputs"]["A"] >= before


def test_reading_it_changes_nothing_and_is_not_in_an_observation():
    a, b = episode((2, 0, 1, +1), (3, 2, 7, -1)), episode((2, 0, 1, +1), (3, 2, 7, -1))
    for ep, read in ((a, True), (b, False)):
        for i in range(30):
            if i % 7 == 0:
                ep.step("A", "RIGHT")
            ep.tick()
            if read:
                ep.started_move("A"), ep.started_move("B")
    assert a._duel.rng.getstate() == b._duel.rng.getstate()
    assert json.dumps(a.observe("A"), sort_keys=True) == json.dumps(b.observe("A"), sort_keys=True)
    assert "started" not in json.dumps(a.observe("A"))
