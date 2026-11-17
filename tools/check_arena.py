"""Full reachability check of arena A with the real engine (maintainers, local).

    uv run python tools/check_arena.py

Breadth-first search over every engine action from each rival start, run to
exhaustion (about 24,000 states and 1.5 minutes per start), printing which rows
of which rooms the kid can stand on without dying. The test suite runs a
shorter version (tests/test_arena.py: stops once all six rooms are reached).
A reachability check of our layouts, not a player.
"""

from __future__ import annotations

import copy
import sys
from collections import deque
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from pop import arena  # noqa: E402
from pop.interface import Episode  # noqa: E402


def key(g):
    k = g.kid
    return (k.cell, k.facing, k.posture, k.hp,
            tuple(tuple(r) for room in sorted(g.geom.grid) for r in g.geom.grid[room]),
            tuple((x.state, x.pos // 12, x.hold // 10) for _, x in sorted(g.mech.gates.items())),
            tuple(sorted(g.mech.loose)))


def reach(seat: str) -> tuple[dict[int, set[int]], int]:
    ep = Episode(arena.situation(seat))
    ep.reset(0)
    q, seen, stood, n = deque([ep]), {key(ep._game)}, {}, 0
    while q:
        e = q.popleft()
        n += 1
        g = e._game
        if g.kid.posture == "standing" and g.terminal is None:
            stood.setdefault(g.kid.room, set()).add(g.kid.row)
        for a in e.legal_actions("kid"):
            f = copy.deepcopy(e)
            f.step("kid", a)
            if f._game.terminal is None and (k := key(f._game)) not in seen:
                seen.add(k)
                q.append(f)
    return stood, n


def main() -> int:
    ok = True
    for seat in arena.STARTS:
        stood, n = reach(seat)
        print(f"start {seat} {arena.STARTS[seat]}: {n} states")
        for room in sorted(arena.ROOMS):
            rows = sorted(stood.get(room, ()))
            ok &= rows == [0, 1, 2]
            print(f"  room {room} {arena.NAMES[room]:<11} rows stood on: {rows or 'UNREACHED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
