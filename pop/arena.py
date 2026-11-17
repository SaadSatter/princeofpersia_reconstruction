"""Shadow Masque arena A: six rooms of our own layouts (Saad, OQ-4, 2026-11-16).

Layout data only; it adds no rule. Tile symbols are pop/tiles.py's, each room
is 3 rows x 10 columns (row 0 at the top), as in pop/situations.py. No
original level data is used (AGENTS.md).

    [1 West Cells] - [2 Gatehouse ] - [3 East Tower]
          |                |                |
    [4 Barracks  ] - [6 Undercroft] - [5 Pit Hall  ]

Rooms 1/3 and 4/5 are mirror images, so the two rival starts (rooms 1 and 3)
are equally far from everything. The middle column holds the two gate-plate
trap spots: each gate starts open between two drop plates that slam it.

The rival starts and guard posts below are annotations for the two-seat
engine (not built yet; its interface is CQ-1). Today `situation()` gives the
single-kid engine one start, so the arena can be walked in `play.py ARENA`
and checked for reachability (tests/test_arena.py).
"""

from __future__ import annotations

from .situations import Situation

ROOMS: dict[int, tuple[str, str, str]] = {
    1: ("#t___P__._",      # West Cells: upper walk, gap at col 8 down to the middle floor
        "#..___L___",      # middle floor, loose tile at col 6, air at cols 1-2
        "#______.__"),     # bottom floor, shaft at col 7 down to the Barracks
    2: ("___t__t___",      # Gatehouse: upper bridge between the towers
        "_._p_G_p._",      # gate at col 5 between two drop plates (trap spot 1)
        "__^_.._^__"),     # lower hall, spikes, shaft at cols 4-5 down to the Undercroft
    3: ("_.__P___t#",      # East Tower: mirror of room 1
        "___L___..#",
        "__.______#"),
    4: ("#_t__L____",      # Barracks: loose tile at col 5 drops to the middle floor
        "#___P__.__",      # gap at col 7
        "#__r__^___"),     # guard post, bottom floor
    5: ("____L__t_#",      # Pit Hall: mirror of room 4
        "__.__P___#",
        "___^__r__#"),
    6: ("_._P__P_._",      # Undercroft: lands from the Gatehouse shaft at cols 4-5
        "___.__.___",      # gaps at cols 3 and 6
        "__p_G__p__"),     # gate at col 4 (the room's centre) between drop plates (trap spot 2)
}
# room -> (left, right, up, down); 0 = no room
LINKS: dict[int, tuple[int, int, int, int]] = {
    1: (0, 2, 0, 4), 2: (1, 3, 0, 6), 3: (2, 0, 0, 5),
    4: (0, 6, 1, 0), 6: (4, 5, 2, 0), 5: (6, 0, 3, 0),
}
PLATE_LINKS = {
    (2, 1, 3): ((2, 1, 5),), (2, 1, 7): ((2, 1, 5),),
    (6, 2, 2): ((6, 2, 4),), (6, 2, 7): ((6, 2, 4),),
}
GATES_OPEN = ((2, 1, 5), (6, 2, 4))

NAMES = {1: "West Cells", 2: "Gatehouse", 3: "East Tower",
         4: "Barracks", 5: "Pit Hall", 6: "Undercroft"}
# Two-seat annotations (not read by the engine yet).
STARTS = {"A": (1, 2, 2, +1), "B": (3, 2, 7, -1)}            # room, row, col, facing
GUARD_POSTS = {"barracks": (4, 2, (1, 8)), "pit_hall": (5, 2, (1, 8))}   # room, row, patrol cols


def situation(seat: str = "A") -> Situation:
    """The arena for the single-kid engine, starting at one rival's start."""
    return Situation(id="ARENA", rooms=ROOMS, links=LINKS, start=STARTS[seat],
                     plate_links=PLATE_LINKS, gates_open=GATES_OPEN,
                     max_actions=400, max_calls=400)
