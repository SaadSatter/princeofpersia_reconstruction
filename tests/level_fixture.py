"""Build level files in the original binary format from our own layouts.

Tests use this so CI never needs the original Level 1 file (decision D1).
The layouts here are authored for tests and are not original rooms.
"""

from __future__ import annotations

from pop import levelfile as LF
from pop import levels

SYMBOL_TO_ID = {sym: tid for tid, sym in levels._SYMBOL.items()}


def link_bytes(room: int, block: int, last: bool, timer: int = 0) -> tuple[int, int]:
    """Encode one LINKLOC/LINKMAP entry (inverse of Level.link_chain)."""
    loc = block | ((room & 0b11) << 5) | (0x80 if last else 0)
    lmap = ((room >> 2) << 5) | (timer & 0x1F)
    return loc, lmap


def build(rooms: dict[int, tuple[str, str, str]],
          links: dict[int, tuple[int, int, int, int]],
          specs: dict[tuple[int, int, int], int] | None = None,
          door_links: list[tuple[int, int, bool]] | None = None,
          start: tuple[int, int, int] = (1, 0, 0xFF),
          guards: dict[int, tuple[int, int, int]] | None = None,
          extra_byte: bool = False,
          raw_ids: dict[tuple[int, int, int], int] | None = None) -> bytes:
    data = bytearray(LF.SIZE_APPLE2)
    for room, rows in rooms.items():
        for r, line in enumerate(rows):
            for c, sym in enumerate(line):
                data[(room - 1) * 30 + r * 10 + c] = SYMBOL_TO_ID[sym]
    for (room, r, c), tid in (raw_ids or {}).items():
        data[(room - 1) * 30 + r * 10 + c] = tid
    for (room, r, c), spec in (specs or {}).items():
        data[720 + (room - 1) * 30 + r * 10 + c] = spec
    for i, (room, block, last) in enumerate(door_links or []):
        data[1440 + i], data[1696 + i] = link_bytes(room, block, last)
    for room, four in links.items():
        data[1952 + (room - 1) * 4:1952 + room * 4] = bytes(four)
    data[2112], data[2113], data[2114] = start
    for i in range(24):
        data[2119 + i] = 255                     # no guard
    for room, (block, face, prog) in (guards or {}).items():
        data[2119 + room - 1] = block
        data[2143 + room - 1] = face
        data[2215 + room - 1] = prog
    if extra_byte:
        data.append(0x09)
    return bytes(data)


# A three-room test level shaped like the original's opening: the kid drops
# in at room 1 block 0, the game slams the open gate in room 5 behind him,
# a sword and a plate lie ahead, and the exit is in room 2 below a loose
# ceiling tile.
MINI_ROOMS = {
    1: (".#########",
        "__S__u____",
        "##########"),
    2: ("##L#######",
        "_____Ee__f",
        "##########"),
    5: ("##p______G",
        "##########",
        "##########"),
}
MINI_LINKS = {1: (5, 2, 0, 0), 2: (1, 0, 0, 0), 5: (0, 1, 0, 0)}
MINI_SPECS = {(1, 1, 5): 0, (5, 0, 2): 1, (5, 0, 9): 1, (2, 1, 9): 1}
MINI_DOOR_LINKS = [(2, 15, True), (5, 9, True)]


def mini_level(**kw) -> bytes:
    return build(MINI_ROOMS, MINI_LINKS, MINI_SPECS, MINI_DOOR_LINKS, **kw)
