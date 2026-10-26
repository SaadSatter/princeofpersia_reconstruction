"""Reader for the original level-file format (our own code; no tables copied).

Format facts (rule R-C01-R-C06, R-C29):
- Apple II `LEVELn`, 2304 bytes, laid out as `BLUETYPE` 24x30, `BLUESPEC`
  24x30, `LINKLOC` 256, `LINKMAP` 256, `MAP` 24x4, `INFO` 256
  (`Source/EQ.S:258-265`). The DOS resource (SDLPoP `data/LEVELS/res2001.bin`,
  2305 bytes) has the same first 2304-byte layout plus one byte.
- A tile byte's low 5 bits are its id (`Source/EQ.S:484-486`); bit 5 marks a
  "required" piece that never breaks (`Source/MOVER.S:394-397`).
- Plate spec = index into LINKLOC/LINKMAP; entries chain until the
  last-entry flag (`Source/MOVER.S:1543-1580`).
- INFO: 64 bytes, then kid start screen, block, face (`Source/EQ.S:272-284`).

This module only parses bytes. It never fetches or stores level data, and
nothing it returns reaches a player except through pop/observation.py.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

ROOMS = 24
CELLS = 30
SIZE_APPLE2 = 2304
SIZE_DOS = 2305

_TYPE, _SPEC, _LOC, _LMAP, _MAP, _INFO = 0, 720, 1440, 1696, 1952, 2048
_KID = _INFO + 64          # KidStartScrn, KidStartBlock, KidStartFace
_GD_BLOCK = _INFO + 71     # after Sw start (2 bytes) and one spare byte
_GD_FACE = _GD_BLOCK + 24
_GD_PROG = _GD_BLOCK + 4 * 24   # GdStartProg (DOS: guards_skill)

ID_MASK = 0x1F
REQUIRED = 0x20

# Tile ids by name (`Source/BGDATA.S:6-35`). Only the ones Level 1 uses are
# supported; any other id is refused rather than silently drawn as floor.
SPACE, FLOOR, SPIKES, POSTS, GATE = 0, 1, 2, 3, 4
PRESSPLATE, FLASK, LOOSE, RUBBLE, UPRESSPLATE = 6, 10, 11, 14, 15
EXIT, EXIT2, TORCH, BLOCK, BONES, SWORD = 16, 17, 19, 20, 21, 22


class LevelFormatError(ValueError):
    pass


@dataclass(frozen=True)
class Guard:
    room: int
    block: int          # 0-29 = row * 10 + col
    face_byte: int
    program: int


@dataclass(frozen=True)
class Level:
    sha256: str
    types: dict[int, tuple[int, ...]]    # room -> 30 tile bytes (id + flags)
    specs: dict[int, tuple[int, ...]]    # room -> 30 spec bytes
    links: dict[int, tuple[int, int, int, int]]
    start_room: int
    start_block: int
    start_face_byte: int
    guards: tuple[Guard, ...]
    _loc: bytes
    _lmap: bytes

    def tile_id(self, room: int, block: int) -> int:
        return self.types[room][block] & ID_MASK

    def required(self, room: int, block: int) -> bool:
        return bool(self.types[room][block] & REQUIRED)

    def link_chain(self, index: int) -> tuple[tuple[int, int], ...]:
        """(room, block) targets of link entry `index`, up to the last-entry flag."""
        out = []
        for i in range(index, 256):
            loc, lmap = self._loc[i], self._lmap[i]
            room = (((loc & 0x60) >> 2) + (lmap & 0xE0)) >> 3   # MOVER.S:1563-1576
            out.append((room, loc & 0x1F))
            if loc & 0x80:
                return tuple(out)
        raise LevelFormatError(f"link chain from {index} has no last entry")

    @property
    def start_facing(self) -> int:
        """+1 right, -1 left. The stored byte is inverted before use
        (`Source/SUBS.S:1516-1518`; SDLPoP `seg003.c:157`); 0 means right
        (SDLPoP `types.h:401`)."""
        return +1 if (self.start_face_byte ^ 0xFF) == 0 else -1


def parse(data: bytes) -> Level:
    if len(data) not in (SIZE_APPLE2, SIZE_DOS):
        raise LevelFormatError(f"expected {SIZE_APPLE2} or {SIZE_DOS} bytes, got {len(data)}")
    types, specs, links = {}, {}, {}
    for r in range(1, ROOMS + 1):
        base = (r - 1) * CELLS
        types[r] = tuple(data[_TYPE + base:_TYPE + base + CELLS])
        specs[r] = tuple(data[_SPEC + base:_SPEC + base + CELLS])
        m = _MAP + (r - 1) * 4
        links[r] = tuple(x if 1 <= x <= ROOMS else 0 for x in data[m:m + 4])
    guards = tuple(
        Guard(r + 1, data[_GD_BLOCK + r], data[_GD_FACE + r], data[_GD_PROG + r])
        for r in range(ROOMS) if data[_GD_BLOCK + r] < CELLS)
    return Level(
        sha256=hashlib.sha256(data).hexdigest(),
        types=types, specs=specs, links=links,
        start_room=data[_KID], start_block=data[_KID + 1], start_face_byte=data[_KID + 2],
        guards=guards, _loc=bytes(data[_LOC:_LOC + 256]), _lmap=bytes(data[_LMAP:_LMAP + 256]),
    )


def same_layout(a: Level, b: Level) -> bool:
    """True if two files describe the same rooms, specs, links, start and guards."""
    return (a.types == b.types and a.specs == b.specs and a.links == b.links
            and (a.start_room, a.start_block, a.start_face_byte)
            == (b.start_room, b.start_block, b.start_face_byte)
            and a.guards == b.guards and a._loc == b._loc and a._lmap == b._lmap)
