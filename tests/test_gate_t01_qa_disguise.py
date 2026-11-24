"""GATE-T01 (QA, Gate 1): independent checks of T01 at 83127cf.

R-V18 / R-V25 (proposed): the other seat observes a disguised rival exactly as
a guard, unless the move raises suspicion by rule (R-V19, R-V24) or breaks the
disguise (R-V21). These tests probe every disguised-legal input in every
standable arena cell, for both seats, with and without a watching guard, and
compare each observed frame field-for-field with the figures a real
patrolling (sheathed) guard can show.

Tests marked `xfail(strict=True, reason="GATE-T01-QAn")` are QA findings:
they fail against 83127cf on purpose and are reported, not fixed here.
"""

from __future__ import annotations

import json
import random

import pytest

from pop import arena
from pop import guards as G
from pop import physics as P
from pop import versus as V
from pop.versus import VersusEpisode

OTHER = {"A": "B", "B": "A"}
FLOOR = set("_tpPLr")     # tiles a rival can be placed standing on (checked by posture)


def _shape(fig: dict) -> tuple:
    """A figure as a guard-comparable tuple: `to` relative to the figure and its
    facing, `to_facing` as same/different."""
    m = fig["motion"]
    base = (fig["kind"], fig["posture"], fig["stance"], fig["armed"])
    if m is None:
        return base + (None,)
    to = m["to"]
    sign = 1 if fig["facing"] == "right" else -1
    rel = None if to is None else (to[0] - fig["row"], (to[1] - fig["col"]) * sign)
    return base + ((m["effect"], m["frame"], m["frames"], rel, m["to_posture"],
                    m["to_facing"] == fig["facing"]),)


def _real_guard_shapes() -> set:
    """Every shape real sheathed guards show while patrolling the arena
    (measured, not assumed)."""
    shapes = set()
    ep = V.arena_episode(0)
    for _ in range(2000):
        ep.tick()
        for seat in ("A", "B"):
            for fig in ep.observe(seat)["figures"]:
                if fig["kind"] == "guard":
                    shapes.add(_shape(fig))
    # Observers never share a room with a guard at their starts, so read the
    # guards directly through the same observation code path too.
    d = ep._duel
    for _ in range(400):
        ep.tick()
        for g in d.guards.values():
            m = g.motion()
            fig = {"kind": "guard", "row": g.row, "col": g.col,
                   "facing": "right" if g.facing > 0 else "left",
                   "posture": "standing", "stance": g.stance, "armed": g.armed,
                   "motion": None if m is None else {
                       "effect": m["effect"], "frame": m["frame"], "frames": m["frames"],
                       "to": [m["to"][1], m["to"][2]], "to_posture": m["posture"],
                       "to_facing": "right" if m["facing"] > 0 else "left"}}
            shapes.add(_shape(fig))
    return {s for s in shapes if s[3] is False}          # sheathed guards only


REAL = _real_guard_shapes()


def _standable(room: int, row: int, col: int) -> bool:
    return 0 <= col < 10 and arena.ROOMS[room][row][col] in FLOOR


def _cases():
    """(seat, start, observer cell, guard posts) for every standable cell, both
    facings, both seats, and three guard set-ups: none, watching from in front
    of the rival, standing behind it."""
    out = []
    for seat in ("A", "B"):
        for room in arena.ROOMS:
            for row in range(3):
                for col in range(10):
                    if not _standable(room, row, col):
                        continue
                    obs = next(((r2, c2) for r2 in (row, 0, 1, 2) for c2 in range(10)
                                if abs(c2 - col) > 1 and _standable(room, r2, c2)), None)
                    if obs is None:
                        continue
                    for facing in (-1, +1):
                        for mode, offsets in (("none", ()), ("front", (2, 3, -2, -3)),
                                              ("behind", (-2, -3, 2, 3))):
                            posts = {}
                            if offsets:
                                gc = next((col + o for o in offsets
                                           if _standable(room, row, col + o)
                                           and (row, col + o) != obs), None)
                                if gc is None:
                                    continue
                                posts = {"watch": (room, row, (gc, gc), 1 if gc < col else -1)}
                            out.append((seat, (room, row, col, facing),
                                        (room, obs[0], obs[1], +1), posts))
    return out


def _episode(seat, start, observer, posts):
    starts = dict(arena.STARTS)
    starts[seat], starts[OTHER[seat]] = start, observer
    ep = VersusEpisode(arena.situation("A"), starts, 0, guard_posts=posts)
    for g in ep._duel.guards.values():
        g.pause = 10 ** 6                                # holds still: sight stays fixed
    r = ep._duel.rivals[seat]
    r.disguised, r.sword, r.stance, r.stance_change = True, "sheathed", None, None
    return ep


def _observed_frames(seat, start, observer, posts):
    """Yield (input, duel, rival, figure) for each frame of each disguised-legal
    input while the rival and the observer share the start room."""
    probe = _episode(seat, start, observer, posts)
    if probe._duel.rivals[seat].kid.posture != "standing":
        return
    for act in probe.legal_actions(seat):
        ep = _episode(seat, start, observer, posts)
        d, r = ep._duel, ep._duel.rivals[seat]
        assert ep.step(seat, act)["accepted"]
        for _ in range(30):
            ep.tick()
            if r.kid.room != start[0] or d.rivals[OTHER[seat]].kid.room != start[0]:
                break
            figs = [f for f in ep.observe(OTHER[seat])["figures"]
                    if (f["row"], f["col"]) == (r.kid.row, r.kid.col)
                    and not any((g.room, g.row, g.col) == r.kid.cell
                                for g in d.guards.values())]
            assert len(figs) == 1, (seat, start, act)
            yield act, d, r, figs[0]
            if figs[0]["kind"] == "rival" or (not d.busy(seat) and d.pending[seat] is None):
                break


CASES = _cases()


def test_real_guard_shapes_were_measured():
    """The reference set is measured from real guards: wait, patrol step, turn."""
    effects = {s[4] and s[4][0] for s in REAL}
    assert effects == {None, "moved", "turned"}


def test_exhaustive_standing_disguised_figure_is_guard_shaped_or_suspicious():
    """Every disguised-legal input x every standable arena cell x both facings x
    both seats x {no guard, guard in front, guard behind}: each frame the other
    seat sees the standing disguised figure is a real guard's shape, or the move
    raises suspicion by rule that frame (R-V19, R-V24), or the disguise is gone.
    Moves whose end lies in another room are checked separately (QA1)."""
    bad = {}
    frames = 0
    for seat, start, observer, posts in CASES:
        for act, d, r, fig in _observed_frames(seat, start, observer, posts):
            frames += 1
            s = _shape(fig)
            if s[0] == "rival" or s[1] != "standing":
                continue
            if fig["motion"] is not None and fig["motion"]["to"] is None:
                continue                                     # QA1 below
            if s in REAL or d.suspicious_rise(seat):
                continue
            bad.setdefault((act, s), (seat, start, posts))
    assert frames > 100_000
    assert not bad, sorted(bad.items(), key=str)[:10]


def test_masked_moves_never_move_or_turn_the_figure_unseen():
    """R-V25 masks a move as standing still only if it changes neither cell nor
    facing; otherwise the other seat would see a figure jump with no motion."""
    bad = {}
    for seat, start, observer, posts in CASES:
        prev = None
        for act, d, r, fig in _observed_frames(seat, start, observer, posts):
            cur = (act, fig["row"], fig["col"], fig["facing"], fig["posture"])
            if (prev is not None and prev[0] == act and prev[5] is None
                    and prev[4] == cur[4] == "standing" and prev[1:4] != cur[1:4]):
                bad.setdefault(act, (seat, start, prev[1:4], cur[1:4]))
            prev = cur + (fig["motion"],)
    assert not bad, bad


def test_disguised_step_toward_the_next_room_is_guard_shaped():
    # Room 1 row 0 col 9 facing right: STEP_RIGHT ends in room 2.
    ep = _episode("A", (1, 0, 9, +1), (1, 0, 3, +1), {})
    assert ep.step("A", "STEP_RIGHT")["accepted"]
    ep.tick()
    fig = [f for f in ep.observe("B")["figures"] if (f["row"], f["col"]) == (0, 9)][0]
    assert fig["kind"] == "guard"
    assert _shape(fig) in REAL or ep._duel.suspicious_rise("A"), _shape(fig)


@pytest.mark.xfail(strict=True, reason="GATE-T01-QA2 (residual, disclosed by T01): a disguised "
                   "rival is observed as a guard with posture 'hanging' after DOWN at an edge, "
                   "and stays so with no motion and no suspicion; no guard ever hangs")
def test_disguised_hang_is_not_a_free_guard_tell():
    ep = _episode("A", (1, 0, 7, +1), (1, 0, 3, +1), {})
    assert ep.step("A", "DOWN")["accepted"]
    for _ in range(20):
        ep.tick()
    figs = [f for f in ep.observe("B")["figures"] if f["kind"] == "guard"]
    assert all(f["posture"] == "standing" for f in figs), figs


@pytest.mark.xfail(strict=True, reason="GATE-T01-QA3 (pre-existing, disclosed by T01): repeated "
                   "WAIT next to a guard never counts as standing still, so R-V19 lingering "
                   "(+1/frame after 2 s within 1 cell) never applies")
def test_waiting_beside_a_guard_counts_as_lingering():
    ep = _episode("A", (2, 0, 7, +1), (2, 0, 1, +1), {"watch": (2, 0, (8, 8), -1)})
    idle = _episode("A", (2, 0, 7, +1), (2, 0, 1, +1), {"watch": (2, 0, (8, 8), -1)})
    for _ in range(120):
        ep.step("A", "WAIT")
        ep.tick()
        idle.tick()
    idle_level = idle._duel.suspicion[("watch", "A")]
    assert idle_level > 0                                   # standing idle lingers
    assert ep._duel.suspicion.get(("watch", "A"), 0) == idle_level


def test_full_hop_in_sight_adds_6_on_every_hop_frame():
    """R-V24 is per frame of the hop (8 frames), not once per hop: 48 per hop."""
    ep = _episode("A", (2, 0, 5, -1), (3, 2, 7, -1), {"watch": (2, 0, (8, 8), -1)})
    assert ep.step("A", "UP")["accepted"]
    levels = []
    for _ in range(P.JUMP_IN_PLACE):
        ep.tick()
        levels.append(ep._duel.suspicion[("watch", "A")])
    assert levels == [V.SUSPICION_LEAP * i for i in range(1, P.JUMP_IN_PLACE + 1)]
    ep.tick()
    assert ep._duel.motion("A") is None


def test_hop_raises_suspicion_for_seat_b_too():
    ep = _episode("B", (2, 0, 5, -1), (3, 2, 7, -1), {"watch": (2, 0, (8, 8), -1)})
    assert ep.step("B", "UP")["accepted"]
    for _ in range(3):
        ep.tick()
    assert ep._duel.suspicion[("watch", "B")] == 3 * V.SUSPICION_LEAP


def test_masking_only_touches_the_other_seats_view():
    """The disguised seat's own `me` keeps its real motion every frame of a bump."""
    ep = _episode("A", (1, 0, 1, -1), (1, 0, 5, +1), {})
    assert ep.step("A", "LEFT")["accepted"]                 # into the wall: a bump
    ep.tick()
    me = ep.observe("A")["me"]["motion"]
    fig = [f for f in ep.observe("B")["figures"] if (f["row"], f["col"]) == (0, 1)][0]
    assert me is not None and fig["motion"] is None


def _fuzz_trace(seed: int) -> str:
    rng = random.Random(seed)
    ep = V.arena_episode(seed)
    out = []
    for t in range(400):
        for s in ("A", "B"):
            if rng.random() < 0.6:
                legal = ep.legal_actions(s)
                if legal:
                    ep.step(s, rng.choice(legal))
        if t == 30:
            r = ep._duel.rivals["A"]
            r.disguised, r.sword, r.stance = True, "sheathed", None
        ep.tick()
        out.append([ep.outcome(), ep.observe("A"), ep.observe("B")])
        if ep.outcome()["status"] == "terminal":
            break
    return json.dumps(out, sort_keys=True, default=str)


def test_same_seed_twice_gives_the_same_trace_and_counts():
    assert _fuzz_trace(5) == _fuzz_trace(5)


def test_time_up_is_a_draw_for_both_seats_and_refuses_inputs():
    ep = V.arena_episode(1)
    for _ in range(V.DUEL_FRAMES):
        ep.tick()
    out = ep.outcome()
    assert (out["reason"], out["frames"]) == ("draw:time_up", V.DUEL_FRAMES)
    assert ep.observe("A")["minutes_left"] == ep.observe("B")["minutes_left"] == 0
    for seat in ("A", "B"):
        assert not ep.step(seat, "WAIT")["accepted"]
