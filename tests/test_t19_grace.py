"""T19, decision #54 (Saad, 2026-11-24): a 2-tick grace window for direction + jump.

A direction and a jump pressed within 2 ticks of each other, in either order, give one
directional jump (a flip, #53) in that direction; a press made late in a move waits for
the move to end and starts then (VERSUS_SPEC 2.1: one pending input). The rule lives in
the engine (`Duel._grace_jump`), so every seat and every front end gets it.
"""

from __future__ import annotations

import pytest

from pop import arena
from pop import physics as P
from pop import versus as V
from pop.versus import VersusEpisode

FAR = (3, 2, 7, -1)


def episode(a, b=FAR) -> VersusEpisode:
    return VersusEpisode(arena.situation("A"), {"A": a, "B": b}, 0, guard_posts={})


def drive(ep, script, ticks):
    """Submit script[t] before tick t. Returns (effects seen per tick, final (col, posture))."""
    seen = []
    for t in range(ticks):
        if t in script:
            assert ep.step("A", script[t])["accepted"], (t, script[t])
        ep.tick()
        m = ep.observe("A")["me"]["motion"]
        seen.append(m["effect"] if m else None)
    me = ep.observe("A")["me"]
    return seen, (me["col"], me["posture"])


def test_the_window_is_two_ticks():
    assert V.GRACE_TICKS == 2


@pytest.mark.parametrize("facing", [+1, -1])
@pytest.mark.parametrize("gap", [0, 1, 2])
@pytest.mark.parametrize("jump_input", ["JUMP", "RUN_JUMP", "UP"])
def test_direction_then_jump_within_the_window_is_one_flip(gap, facing, jump_input):
    """left then up (and right then up), `gap` ticks apart. The front end sends RUN_JUMP
    once it sees the run, or a bare UP when the direction key was released first."""
    d = "RIGHT" if facing == +1 else "LEFT"
    start = 2 if facing == +1 else 6
    ep = episode((2, 0, start, facing))
    second = "UP" if jump_input == "UP" else f"{jump_input}_{d}"
    if gap == 0:
        script = {0: f"JUMP_{d}"}
    else:
        script = {0: d, gap: second}
    seen, (col, posture) = drive(ep, script, gap + P.JUMP + 3)
    assert "flipped" in seen and "moved" not in seen[gap:], seen
    assert (col, posture) == (start + 3 * facing, "standing")          # one standing jump from the start cell


def test_the_jump_after_the_direction_starts_at_once_with_no_wait_for_the_run():
    ep = episode((2, 0, 2, +1))
    drive(ep, {0: "RIGHT"}, 1)
    ep.step("A", "JUMP_RIGHT")
    ep.tick()
    m = ep.observe("A")["me"]["motion"]
    assert m["effect"] == "flipped" and m["frame"] == 1


def test_direction_then_jump_three_ticks_apart_is_two_separate_inputs():
    """The run (4 frames) finishes, then the jump starts from the next cell."""
    ep = episode((2, 0, 2, +1))
    seen, (col, posture) = drive(ep, {0: "RIGHT", 3: "JUMP_RIGHT"}, 3 + P.RUN + P.JUMP + 3)
    assert (col, posture) == (2 + 1 + 3, "standing")
    assert seen.index("flipped") >= P.RUN                              # not before the run ended


@pytest.mark.parametrize("gap", [0, 1, 2])
@pytest.mark.parametrize("facing", [+1, -1])
def test_jump_then_direction_within_the_window_is_one_flip(gap, facing):
    d = "RIGHT" if facing == +1 else "LEFT"
    start = 2 if facing == +1 else 6
    ep = episode((2, 0, start, facing))
    script = {0: "UP", gap: d} if gap else {0: f"JUMP_{d}"}
    seen, (col, posture) = drive(ep, script, gap + P.JUMP + 3)
    assert "flipped" in seen
    assert (col, posture) == (start + 3 * facing, "standing")


def test_jump_then_the_opposite_direction_flips_that_way():
    ep = episode((2, 0, 5, +1))
    seen, (col, _) = drive(ep, {0: "UP", 2: "LEFT"}, 2 + P.JUMP + 3)
    assert "flipped" in seen and col == 2 and ep.observe("A")["me"]["facing"] == "left"


def test_a_press_during_a_moves_last_frames_waits_and_starts_when_it_ends():
    """JUMP_RIGHT pressed on frame 3 of a 4-frame run: the run ends, the jump starts
    that same tick (no gap, no loss)."""
    ep = episode((2, 0, 2, +1))
    seen, _ = drive(ep, {0: "RIGHT", 3: "JUMP_RIGHT"}, P.RUN + 1)
    assert seen[:P.RUN] == ["moved"] * P.RUN
    assert seen[P.RUN] == "flipped"


def test_continuing_a_run_keeps_the_running_jump():
    """A jump pressed mid-run when the run began long ago is the ordinary running jump
    (5 cells from the start of the jump), not a standing jump."""
    ep = episode((2, 0, 1, +1))
    script = {0: "RIGHT", 4: "RIGHT", 5: "RUN_JUMP_RIGHT"}      # second run of a chain, jump 1 tick in
    seen, (col, posture) = drive(ep, script, 8 + P.RUN + P.RUN_JUMP_FLIGHT + 4)
    assert (col, posture) == (1 + 2 + 1 + 4, "standing")


def test_up_under_a_ledge_is_not_turned_into_a_jump():
    ep = episode((2, 2, 1, -1))                    # facing away: RIGHT is a turn, then a ledge is ahead
    seen, _ = drive(ep, {0: "RIGHT", 1: "UP"}, P.TURN + 16)
    assert "climbed" in seen and "flipped" not in seen


def test_a_lone_direction_starts_on_the_press_tick_with_no_added_latency():
    ep = episode((2, 0, 2, +1))
    ep.step("A", "RIGHT")
    ep.tick()
    m = ep.observe("A")["me"]["motion"]
    assert m["effect"] == "moved" and m["frame"] == 1


def test_an_ai_seat_gets_the_same_rule():
    """Seat B goes through the same engine step: same result, mirrored."""
    ep = episode((3, 2, 7, -1), (2, 0, 6, -1))
    ep.step("B", "LEFT")
    ep.tick()
    ep.step("B", "JUMP_LEFT")
    ep.tick()
    assert ep.observe("B")["me"]["motion"]["effect"] == "flipped"


def test_the_same_inputs_give_the_same_trace():
    def trace():
        ep = episode((2, 0, 2, +1))
        out = []
        for t in range(20):
            if t == 0:
                ep.step("A", "RIGHT")
            if t == 2:
                ep.step("A", "RUN_JUMP_RIGHT")
            ep.tick()
            out.append(ep._duel.snapshot())
        return out
    assert trace() == trace()
