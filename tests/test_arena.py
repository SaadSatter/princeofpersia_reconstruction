"""Arena A (pop/arena.py): six rooms of our own layouts (OQ-4, Saad 2026-11-16)."""

from __future__ import annotations

import copy
from collections import deque

import pytest

from pop import arena, tiles as T
from pop.interface import Episode

ARENA_TILES = T.ALL - {T.SWORD, T.BONES}


def test_six_rooms_of_three_rows_by_ten():
    assert sorted(arena.ROOMS) == [1, 2, 3, 4, 5, 6]
    for n, rows in arena.ROOMS.items():
        assert len(rows) == 3 and all(len(r) == 10 for r in rows), n
        assert set("".join(rows)) <= ARENA_TILES, n


def test_links_go_both_ways():
    opposite = {0: 1, 1: 0, 2: 3, 3: 2}
    for n, links in arena.LINKS.items():
        for side, m in enumerate(links):
            if m:
                assert arena.LINKS[m][opposite[side]] == n, (n, side, m)


def test_mirrored_rooms_and_starts():
    for a, b in ((1, 3), (4, 5)):
        assert arena.ROOMS[b] == tuple(r[::-1] for r in arena.ROOMS[a])
    (ra, row_a, ca, fa), (rb, row_b, cb, fb) = arena.STARTS["A"], arena.STARTS["B"]
    assert (ra, rb) == (1, 3) and row_a == row_b and ca == 9 - cb and fa == -fb
    for room, row, col, _ in arena.STARTS.values():
        assert arena.ROOMS[room][row][col] in T.HAS_FLOOR


def test_plates_close_gates_that_start_open():
    for plate, gates in arena.PLATE_LINKS.items():
        room, row, col = plate
        assert arena.ROOMS[room][row][col] == T.DROP_PLATE
        for g in gates:
            assert arena.ROOMS[g[0]][g[1]][g[2]] == T.GATE and g in arena.GATES_OPEN


def _key(g):
    k = g.kid
    return (k.cell, k.facing, k.posture,
            tuple(tuple(r) for room in sorted(g.geom.grid) for r in g.geom.grid[room]),
            tuple((x.state, x.pos // 12) for _, x in sorted(g.mech.gates.items())))


@pytest.mark.parametrize("seat", ["A", "B"])
def test_every_room_is_reachable_from_each_start(seat):
    """Breadth-first over the real engine's actions until the kid has stood in
    all six rooms. (tools/check_arena.py runs the full search: every row.)"""
    ep = Episode(arena.situation(seat))
    ep.reset(0)
    q, seen, stood = deque([ep]), {_key(ep._game)}, set()
    while q and len(stood) < 6:
        e = q.popleft()
        g = e._game
        if g.kid.posture == "standing":
            stood.add(g.kid.room)
        for a in e.legal_actions("kid"):
            f = copy.deepcopy(e)
            f.step("kid", a)
            if f._game.terminal is None and (k := _key(f._game)) not in seen:
                seen.add(k)
                q.append(f)
    assert stood == set(arena.ROOMS)
