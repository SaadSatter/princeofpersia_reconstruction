"""Authored room layouts and the frozen evaluation situations.

These layouts are our own (R-D13). They must match docs/EVALUATION_SUITE.md
exactly; tests/test_situations.py checks that the two agree.
"""

from __future__ import annotations

from dataclasses import dataclass, field

Cell = tuple[int, int, int]  # (room, row, col)

TASK = ("Escape the dungeon: reach the exit door and climb its stairs "
        "(UP while standing on an open exit).")


@dataclass(frozen=True)
class Situation:
    id: str
    rooms: dict[int, tuple[str, str, str]]
    # room -> (left, right, up, down); 0 = no room
    links: dict[int, tuple[int, int, int, int]]
    start: tuple[int, int, int, int]  # room, row, col, facing (+1 right, -1 left)
    plate_links: dict[Cell, tuple[Cell, ...]] = field(default_factory=dict)
    exits_open: bool = True
    max_actions: int = 40
    max_calls: int = 40
    held_out: bool = False
    task: str = TASK


SITUATIONS: dict[str, Situation] = {}


def _add(s: Situation) -> None:
    for room, rows in s.rooms.items():
        assert len(rows) == 3 and all(len(r) == 10 for r in rows), (s.id, room)
    SITUATIONS[s.id] = s


_add(Situation(
    id="S1",
    rooms={
        1: ("##########",
            "_t___.____",
            "#####^####"),
        2: ("##########",
            "__L_..._Ee",
            "##.#...###"),
    },
    links={1: (0, 2, 0, 0), 2: (1, 0, 0, 0)},
    start=(1, 1, 1, +1),
    exits_open=True, max_actions=40, max_calls=40,
))

_add(Situation(
    id="S2",
    rooms={
        1: ("##########",
            "_u__^^^___",
            "##########"),
        2: ("##########",
            "__p__G_Ee_",
            "##########"),
    },
    links={1: (0, 2, 0, 0), 2: (1, 0, 0, 0)},
    start=(1, 1, 0, +1),
    plate_links={(1, 1, 1): ((2, 1, 5),), (2, 1, 2): ((2, 1, 5),)},
    exits_open=True, max_actions=50, max_calls=50,
))

_add(Situation(
    id="S3",
    rooms={
        1: ("#__t__.###",
            "######_f__",
            "##########"),
        2: ("##########",
            "__.__L.___",
            "##^##__###"),
        3: ("##########",
            "_u___^^_G_",
            "##########"),
        4: ("u.....####",
            "____Ee__##",
            "##########"),
    },
    links={1: (0, 2, 0, 0), 2: (1, 3, 0, 0), 3: (2, 4, 0, 0), 4: (3, 0, 0, 0)},
    start=(1, 0, 1, +1),
    plate_links={(3, 1, 1): ((3, 1, 8),), (4, 0, 0): ((4, 1, 4),)},
    exits_open=False, max_actions=80, max_calls=80,
))

_add(Situation(
    id="H1",
    rooms={
        1: ("##########",
            "_Ee..._L__",
            "###...#.##"),
        2: ("##########",
            "___..__t__",
            "###^^#####"),
    },
    links={1: (0, 2, 0, 0), 2: (1, 0, 0, 0)},
    start=(2, 1, 8, -1),
    exits_open=True, max_actions=40, max_calls=40, held_out=True,
))

_add(Situation(
    id="H2",
    rooms={
        1: ("##########",
            "__u_^^_p__",
            "##########"),
        2: ("##########",
            "___G_^_Ee_",
            "##########"),
    },
    links={1: (0, 2, 0, 0), 2: (1, 0, 0, 0)},
    start=(1, 1, 0, +1),
    plate_links={(1, 1, 2): ((2, 1, 3),), (1, 1, 7): ((2, 1, 3),)},
    exits_open=True, max_actions=50, max_calls=50, held_out=True,
))

_add(Situation(
    id="H3",
    rooms={
        1: ("##########",
            "#__f__L__.",
            "######.#__"),
        2: ("##########",
            "##########",
            "__._u_^^__"),
        3: ("##########",
            "##.___G___",
            "___#######"),
        4: ("#####...u#",
            "_____.____",
            "#####Ee__#"),
    },
    links={1: (0, 2, 0, 0), 2: (1, 3, 0, 0), 3: (2, 4, 0, 0), 4: (3, 0, 0, 0)},
    start=(1, 1, 1, +1),
    plate_links={(2, 2, 4): ((3, 1, 6),), (4, 0, 8): ((4, 2, 5),)},
    exits_open=False, max_actions=80, max_calls=80, held_out=True,
))
