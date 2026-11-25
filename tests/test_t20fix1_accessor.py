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


def test_starts_never_exceed_accepted_inputs_and_stale_drops_start_nothing():
    import random
    rng = random.Random(5)
    ep = armed((2, 0, 3, +1), (2, 0, 4, -1))
    base_in = dict(ep.outcome()["inputs"])
    starts = {"A": 0, "B": 0}
    for _ in range(600):
        for seat in ("A", "B"):
            legal = ep.legal_actions(seat)
            if rng.random() < 0.6 and legal:
                ep.step(seat, rng.choice(legal))
        ep.tick()
        for seat in ("A", "B"):
            if ep.started_move(seat) is not None:
                starts[seat] += 1
    out = ep.outcome()
    for seat in ("A", "B"):
        accepted = out["inputs"][seat] - base_in[seat]
        # every start came from one accepted input; replaced and stale ones never started
        assert starts[seat] <= accepted - out["stale_inputs"][seat] - out["replaced_inputs"][seat] + 1


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


def test_the_started_move_says_which_engine_rewrite_started_it():
    """R-V35, R-V22 and R-V10 each rewrite an accepted input; `rewrite` names which, so the
    host log marks them exactly instead of guessing from history."""
    ep = episode((2, 0, 1, +1), (3, 2, 7, -1))
    ep.step("A", "RIGHT")
    ep.tick()
    assert ep.started_move("A") == "RIGHT" and ep.started_move("A").rewrite is None
    ep.step("A", "RUN_JUMP_RIGHT")
    ep.tick()
    assert ep.started_move("A") == "JUMP_RIGHT" and ep.started_move("A").rewrite == "grace"

    ep = episode((2, 0, 1, +1), (3, 2, 7, -1))
    ep.step("A", "UP")
    ep.tick()
    ep.step("A", "JUMP_RIGHT")
    ep.tick()
    assert ep.started_move("A").rewrite == "hop_turn"

    ep = armed((2, 0, 2, +1), (2, 0, 4, -1))
    ep.step("A", "JUMP_RIGHT")
    ep.tick()
    assert ep.started_move("A").rewrite is None
    run(ep, 6)
    ep.step("A", "KICK")
    ep.tick()
    assert ep.started_move("A").rewrite == "kick"


def test_a_jump_that_starts_after_the_direction_finished_is_not_grace():
    """Seed 1 of the recorder fuzz: RIGHT bumped (2 frames), JUMP_RIGHT queued behind it
    started the tick it ended. Not a cancel, so no grace."""
    ep = episode((2, 0, 1, +1), (3, 2, 7, -1))
    seen = []
    for t in range(60):
        legal = ep.legal_actions("A")
        ep.step("A", "JUMP_RIGHT" if t % 9 == 4 and "JUMP_RIGHT" in legal else "RIGHT")
        ep.tick()
        m = ep.started_move("A")
        if m and m.startswith("JUMP"):
            seen.append(m.rewrite)
    assert seen and None in seen or seen == []
