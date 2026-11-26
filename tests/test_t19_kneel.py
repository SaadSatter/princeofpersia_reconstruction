"""T19, item 3 of Saad's request (2026-11-24): picking up a dropped sword and taking a
uniform are drawn kneeling, like rigging a trap. Frame counts and what the other seat
is shown do not change (R-V25).

Finding for QA: before T19 nothing in render/ drew `kneeled` specially (the rival
standing idle for the 12 frames). T19 gives all three the one rival `crouch` strip.
"""

from __future__ import annotations

import json

from pop import arena
from pop import versus as V
from render import versus_view

COUNTS = {"crouch": 6, "take": 5, "stand": 1, "lunge_mid": 8}


def episode(a, b, posts):
    return V.VersusEpisode(arena.situation("A"), dict(arena.STARTS, A=a, B=b), 0, guard_posts=posts)


def run(ep, n):
    for _ in range(n):
        ep.tick()


def downed(uniform: bool):
    ep = episode((1, 2, 2, +1), (2, 0, 4, +1), {"g": (2, 0, (5, 5), -1)})
    g = ep._duel.guards["g"]
    g.knock_out()
    g.uniform = uniform
    ep.tick()
    return ep


def strips_while(ep, seat, frames):
    out = []
    for _ in range(frames):
        ep.tick()
        view = ep.observe(seat)["me"]
        if view["motion"] is None:
            break
        spr = versus_view.sprite(view, COUNTS)
        out.append(spr.strip if spr else None)
    return out


def test_taking_a_uniform_kneels_for_all_12_frames():
    ep = downed(True)
    assert ep.step("B", "TAKE")["accepted"]
    strips = strips_while(ep, "B", V.TAKE_FRAMES)
    assert len(strips) == V.TAKE_FRAMES and set(strips) == {"crouch"}


def test_a_take_with_no_uniform_left_kneels_the_same_way():
    ep = downed(False)
    assert ep.step("B", "TAKE")["accepted"]
    strips = strips_while(ep, "B", V.TAKE_FRAMES)
    assert len(strips) == V.TAKE_FRAMES and set(strips) == {"crouch"}
    run(ep, 3)
    assert ep._duel.last_result["B"]["effect"] == "no_uniform"


def test_picking_up_a_sword_kneels_for_all_6_frames():
    ep = V.VersusEpisode(arena.situation("A"), dict(arena.STARTS, A=(2, 0, 7, +1), B=(1, 2, 2, +1)), 0)
    ep.step("A", "DRAW")
    run(ep, V.DRAW_FRAMES + 1)
    ep.step("A", "THROW")
    run(ep, V.THROW_RELEASE + V.THROW_RECOVERY + 4)
    ep._duel.rivals["A"].kid.col = 9                        # stand on the sword
    assert ep.step("A", "DOWN")["accepted"]
    strips = strips_while(ep, "A", V.PICKUP_FRAMES)
    assert V.PICKUP_FRAMES == 6 and len(strips) == 6 and set(strips) == {"crouch"}


def test_rigging_a_trap_uses_the_same_kneel():
    ep = V.VersusEpisode(arena.situation("A"), dict(arena.STARTS, A=(2, 0, 1, +1), B=(1, 2, 2, +1)), 0)
    assert ep.step("A", "RIG")["accepted"]
    strips = strips_while(ep, "A", V.RIG_FRAMES)
    assert set(strips) == {"crouch"}


def test_the_kneel_frame_advances_through_the_strip():
    ep = downed(True)
    ep.step("B", "TAKE")
    idx = []
    for _ in range(V.TAKE_FRAMES):
        ep.tick()
        idx.append(versus_view.sprite(ep.observe("B")["me"], COUNTS).index)
    assert idx == sorted(idx) and idx[0] == 0 and idx[-1] == COUNTS["crouch"] - 1


def test_the_other_seats_view_of_a_take_is_unchanged_with_or_without_a_uniform():
    """R-V25: A sees the same figures whether or not B's TAKE found a uniform, and
    the effect names are the ones before T19."""
    seen = {}
    for uniform in (True, False):
        ep = episode((2, 0, 2, +1), (2, 0, 4, +1), {"g": (2, 0, (5, 5), -1)})
        g = ep._duel.guards["g"]
        g.knock_out()
        g.uniform = uniform
        ep.tick()
        ep.step("B", "TAKE")
        frames = []
        for _ in range(V.TAKE_FRAMES - 1):
            ep.tick()
            frames.append(json.dumps(ep.observe("A")["figures"], sort_keys=True))
        seen[uniform] = frames
    assert seen[True] == seen[False]
    effects = {fig["motion"]["effect"] for f in seen[True] for fig in json.loads(f)
               if fig.get("motion")}
    assert effects == {"took_uniform"}
