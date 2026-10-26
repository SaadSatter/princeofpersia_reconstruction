"""Find a route through the original Level 1 with the real engine (maintainers, local).

    uv run python tools/solve_level1.py                  # default waypoints, prints the route
    uv run python tools/solve_level1.py --via 1,2,3,9    # any room sequence

A breadth-first search over the 11 actions, one segment per waypoint: from
the current state until the kid stands in the next room (or, for the
sword/exit goals, has the sword / has won). Only the segment's two rooms
are searched, which keeps it small. The engine is the real one (pop/), so
a route it finds is playable as is; it is a reachability check for
docs/LEVEL1.md, not a player (players never see the engine).
Prints to the terminal only. Needs the local file (tools/fetch_level1.py).
"""

from __future__ import annotations

import argparse
import copy
import sys
from collections import deque
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from pop.interface import Episode  # noqa: E402

# Start -> sword room 15 -> back to the exit in room 9 (rooms by link).
DEFAULT_VIA = "1,2,6,8,7,20,12,15,sword,12,20,7,8,6,2,3,9,won"


def key(g):
    k = g.kid
    return (k.cell, k.facing, k.posture, k.hp, k.sword,
            tuple(tuple(r) for room in sorted(g.geom.grid) for r in g.geom.grid[room]),
            tuple((x.state, x.pos // 12, x.hold // 10) for _, x in sorted(g.mech.gates.items())),
            tuple(e.opening for _, e in sorted(g.mech.exits.items())),
            tuple(sorted(g.mech.loose)))


def segment(ep: Episode, goal: str, allowed: set[int], cap: int):
    def done(e):
        g = e._game
        if goal == "won":
            return g.terminal == "won"
        if goal == "sword":
            return g.kid.sword and g.kid.posture == "standing"
        return g.kid.room == int(goal) and g.kid.posture == "standing" and g.terminal is None
    q, seen, n = deque([(ep, ())]), {key(ep._game)}, 0
    while q and n < cap:
        e, path = q.popleft()
        n += 1
        for a in e.legal_actions("kid"):
            f = copy.deepcopy(e)
            f.step("kid", a)
            g = f._game
            if done(f):
                return f, path + (a,), n
            if g.terminal is not None or g.kid.room not in allowed:
                continue
            k = key(g)
            if k not in seen:
                seen.add(k)
                q.append((f, path + (a,)))
    return None, None, n


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--via", default=DEFAULT_VIA)
    ap.add_argument("--cap", type=int, default=200000, help="max states per segment")
    args = ap.parse_args(argv)
    ep = Episode("L1", max_actions=None)
    ep.reset(0)
    route: list[str] = []
    room = ep._game.kid.room
    for goal in args.via.split(",")[1:]:
        allowed = {room} | ({int(goal)} if goal.isdigit() else set())
        ep2, path, n = segment(ep, goal, allowed, args.cap)
        if ep2 is None:
            print(f"no route from room {room} to {goal} within {n} states", file=sys.stderr)
            print("route so far:", " ".join(route))
            return 1
        route += path
        ep, room = ep2, ep2._game.kid.room
        k = ep._game.kid
        print(f"-> {goal:>5}: {len(path):3d} actions, {n:6d} states; "
              f"room {k.room} ({k.row},{k.col}) hp {k.hp} sword {k.sword}")
    print(f"total {len(route)} actions, {ep._game.frames} frames, outcome {ep.outcome()['reason']}")
    print(" ".join(route))
    return 0


if __name__ == "__main__":
    sys.exit(main())
