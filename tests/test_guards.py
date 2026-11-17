"""Scripted guards, R-V13 to R-V16 (docs/final/VERSUS_SPEC.md Section 4).

The Barracks guard (arena GUARD_POSTS: room 4, row 2, cols 1-8) starts at col
1 facing right; the Pit Hall guard mirrors it. Rivals are placed per test.
"""

from __future__ import annotations

import json

import pytest

from pop import arena
from pop import physics as P
from pop import versus as V
from pop.guards import (ALERT_DRAW_FRAMES, PATROL_PAUSE, REACTION_FRAMES, SIGHT_CELLS,
                        LUNGE_COOLDOWN)
from pop.versus import VersusEpisode

AWAY = {"A": (1, 2, 2, +1), "B": (3, 2, 7, -1)}       # both rivals far from any guard


def episode(a=None, b=None, posts=None, seed=0) -> VersusEpisode:
    starts = dict(AWAY)
    if a:
        starts["A"] = a
    if b:
        starts["B"] = b
    return VersusEpisode(arena.situation("A"), starts, seed,
                         guard_posts=arena.GUARD_POSTS if posts is None else posts)


def run(ep, n):
    for _ in range(n):
        ep.tick()


def guard(ep, name="barracks"):
    return ep._duel.guards[name]


def draw_sword(ep, seat):
    ep.step(seat, "DRAW")
    run(ep, V.DRAW_FRAMES + 1)


# R-V13 -------------------------------------------------------------------
def test_patrol_walks_at_step_speed_and_pauses_at_each_end():
    ep = episode()
    g = guard(ep)
    assert (g.col, g.facing, g.armed) == (1, +1, False)          # patrols sheathed
    run(ep, P.STEP)
    assert g.col == 1                                            # arrival lands next frame
    run(ep, 1)
    assert g.col == 2
    run(ep, (8 - 2) * P.STEP + 1)
    assert g.col == 8
    run(ep, 1 + PATROL_PAUSE + P.TURN + 2)
    assert g.facing == -1
    assert PATROL_PAUSE == 12


# R-V14 -------------------------------------------------------------------
@pytest.mark.parametrize("a,seen", [
    ((4, 2, 6, -1), True),                       # 5 cells in front
    ((4, 2, 7, -1), False),                      # 6 cells: too far
    ((4, 1, 3, -1), False),                      # another row
])
def test_sight_is_same_row_in_front_within_5_cells(a, seen):
    ep = episode(a=a)
    run(ep, 1)
    assert (guard(ep).target == "A") is seen
    assert SIGHT_CELLS == 5


def test_a_guard_does_not_see_behind_itself():
    ep = episode(posts={"g": (2, 0, (4, 8))}, a=(2, 0, 2, +1))    # guard at 4 faces right, A behind
    run(ep, 1)
    assert ep._duel.guards["g"].target is None


def test_a_wall_blocks_sight():
    ep = episode(posts={"g": (1, 2, (1, 3))}, a=(1, 2, 5, -1))    # West Cells row 2: open; then wall test
    run(ep, 1)
    assert ep._duel.guards["g"].target == "A"
    ep = episode(posts={"g": (1, 1, (3, 5))}, a=(1, 1, 8, -1))
    ep._duel.geom.set_tile((1, 1, 6), "#")
    run(ep, 1)
    assert ep._duel.guards["g"].target is None


# R-V15 -------------------------------------------------------------------
def test_alerted_guard_draws_advances_and_lunges_for_a_heart():
    ep = episode(a=(4, 2, 5, -1))                                # A stays sheathed: cannot block
    run(ep, ALERT_DRAW_FRAMES + 3 * (P.RUN + 1) + V.LUNGE_WINDUP + 3)
    assert guard(ep).armed
    assert ep.observe("A")["me"]["hp"] <= 2


def test_guard_copies_the_rivals_stance_after_its_reaction_time():
    ep = episode(a=(4, 2, 3, -1))
    draw_sword(ep, "A")
    g = guard(ep)
    run(ep, ALERT_DRAW_FRAMES + 2)
    assert g.stance == "mid"
    ep.step("A", "STANCE_UP")
    run(ep, V.STANCE_FRAMES)
    assert ep.observe("A")["me"]["stance"] == "high" and g.stance == "mid"
    run(ep, REACTION_FRAMES)
    assert g.stance == "high"
    assert REACTION_FRAMES == 6 and LUNGE_COOLDOWN == 16


def test_guard_lunges_at_most_every_16_frames():
    ep = episode(a=(4, 2, 2, -1))
    draw_sword(ep, "A")
    g = guard(ep)
    starts = []
    for f in range(60):
        ep.tick()
        if g.attack and g.attack["frame"] == 1:                 # the frame a lunge starts
            starts.append(f)
    assert len(starts) >= 2 and all(b - a >= LUNGE_COOLDOWN for a, b in zip(starts, starts[1:]))


def test_guards_are_hostile_to_both_rivals():
    ep = episode(b=(5, 2, 4, +1))                               # in front of the Pit Hall guard
    run(ep, 1)
    assert guard(ep, "pit_hall").target == "B"


# R-V16 -------------------------------------------------------------------
def test_one_clean_lunge_downs_a_guard_for_good():
    ep = episode(posts={"g": (2, 0, (5, 8))}, a=(2, 0, 4, +1))   # behind a guard walking away
    draw_sword(ep, "A")
    ep.step("A", "LUNGE")
    run(ep, V.LUNGE_WINDUP + 1)
    g = ep._duel.guards["g"]
    assert g.downed and g.uniform
    run(ep, 300)
    assert g.downed
    fig = ep.observe("A")["figures"][0]
    assert fig["kind"] == "guard" and fig["posture"] == "downed"


def test_a_matching_guard_blocks_the_lunge():
    ep = episode(a=(4, 2, 2, -1))
    draw_sword(ep, "A")
    run(ep, ALERT_DRAW_FRAMES + 2)                               # guard drawn, mid like A
    ep.step("A", "LUNGE")
    run(ep, V.LUNGE_WINDUP + 1)
    assert not guard(ep).downed


def test_a_thrown_sword_downs_a_guard():
    ep = episode(a=(4, 2, 7, -1))
    draw_sword(ep, "A")
    ep._duel.rivals["A"].stance = "low"
    ep.step("A", "THROW")
    run(ep, V.THROW_RELEASE + 4)
    assert guard(ep).downed


def test_a_falling_floor_downs_a_guard():
    ep = episode(posts={"g": (4, 0, (5, 5))})                   # Barracks row 0: loose tile at col 5
    ep._duel.mech.touch_loose((4, 0, 5))
    run(ep, 30)
    assert ep._duel.guards["g"].downed


def test_rivals_cannot_walk_through_a_standing_guard_but_can_cross_a_downed_one():
    ep = episode(posts={"g": (2, 0, (5, 5))}, a=(2, 0, 4, +1))
    ep.step("A", "RIGHT")
    run(ep, P.RUN + 1)
    assert ep.observe("A")["me"]["col"] == 4
    ep._duel.guards["g"].downed = True
    ep.step("A", "RIGHT")
    run(ep, P.RUN + 1)
    assert ep.observe("A")["me"]["col"] == 5


# observation -------------------------------------------------------------
def test_guards_are_figures_only_in_their_room_and_look_like_any_figure():
    ep = episode(a=(4, 0, 2, +1))
    figs = ep.observe("A")["figures"]
    assert len(figs) == 1 and set(figs[0]) == V.FIGURE_KEYS
    assert figs[0]["kind"] == "guard" and figs[0]["armed"] is False and figs[0]["stance"] is None
    assert ep.observe("B")["figures"] == []


def test_guard_play_is_deterministic():
    def trace():
        ep = episode(a=(4, 2, 4, -1), seed=9)
        out = []
        for f in range(80):
            if f == 5:
                ep.step("A", "DRAW")
            if f == 20:
                ep.step("A", "STANCE_DOWN")
            ep.tick()
            out.append(json.dumps(ep._duel.snapshot(), sort_keys=True, default=str))
        return out
    assert trace() == trace()
