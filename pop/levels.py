"""Reconstructed original levels, kept apart from the frozen evaluation suite.

`L1` is the original 1989 Level 1, built at run time from the original level
file. The file is never committed (student decision D1, 2026-10-26): a
maintainer fetches it once with `tools/fetch_level1.py`, which checks the
pinned source and SHA-256 below. Without it, `L1` is unavailable and the
rest of the game is unaffected.

`L1` is not in `pop.situations.SITUATIONS`, so the evaluation suite,
evaluate.py and the suite tests never see it. Players see it only through
pop/observation.py (current room only), like any other situation.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from . import levelfile as LF
from . import tiles as T
from .situations import SITUATIONS, Situation

PROJECT = Path(__file__).resolve().parent.parent
LEVEL_DIR = PROJECT / "vendor" / "levels"      # git-ignored (vendor/)


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    sha256: str
    size: int
    filename: str


APPLE2 = Source(
    name="Apple II LEVEL1 (historicalsource/princeofpersia @2b4ddb5)",
    url=("https://raw.githubusercontent.com/historicalsource/princeofpersia/"
         "2b4ddb5377f905840bf64f32e2f543a79f434222/01%20POP%20Source/Levels/LEVEL1"),
    sha256="600205ef325329002ff9fa25b473f05df48b082ac6282150c9e655014decd316",
    size=LF.SIZE_APPLE2, filename="LEVEL1")
DOS = Source(
    name="DOS level 1 (NagyD/SDLPoP @3c5add5, data/LEVELS/res2001.bin)",
    url=("https://raw.githubusercontent.com/NagyD/SDLPoP/"
         "3c5add5fb7f83d4ceb542823ab66d00146c4271b/data/LEVELS/res2001.bin"),
    sha256="ae8dd7787c65e2ecd2a21c6126c751c47e9a614edde0a80af0c86d8afeadc06c",
    size=LF.SIZE_DOS, filename="res2001.bin")

SETUP_HINT = ("The original Level 1 file is not in this repository. Fetch it once "
              "(network, pinned source, SHA-256 checked) with:\n"
              "    uv run python tools/fetch_level1.py\n"
              "(working directory: the project folder). See docs/LEVEL1.md.")

# Original rules that only reconstructed levels switch on (engine checks
# `rule in situation.rules`). The frozen suite has none.
RULES = frozenset({
    "sword",          # sword tile can be picked up (R-C21)
    "ceiling_loose",  # hopping up under a loose floor knocks it down (R-C31)
})

LEVEL1_LIMITS = 600   # actions and model calls for exhibition runs (R-D27)

# Tile id -> our symbol. Ids outside this map are refused (LF.LevelFormatError).
_SYMBOL = {
    LF.SPACE: T.SPACE, LF.FLOOR: T.FLOOR, LF.SPIKES: T.SPIKES, LF.POSTS: T.PILLAR,
    LF.GATE: T.GATE, LF.PRESSPLATE: T.DROP_PLATE, LF.FLASK: T.POTION, LF.LOOSE: T.LOOSE,
    LF.RUBBLE: T.RUBBLE, LF.UPRESSPLATE: T.RAISE_PLATE, LF.EXIT: T.EXIT_LEFT,
    LF.EXIT2: T.EXIT_RIGHT, LF.TORCH: T.TORCH, LF.BLOCK: T.WALL, LF.BONES: T.BONES,
    LF.SWORD: T.SWORD,
}


class LevelDataMissing(FileNotFoundError):
    pass


class LevelDataMismatch(ValueError):
    pass


def level1_path() -> Path:
    return Path(os.environ.get("POP_LEVEL1", LEVEL_DIR / APPLE2.filename))


def to_situation(level: LF.Level, sid: str, *, max_actions: int = LEVEL1_LIMITS,
                 special_start: bool = True) -> Situation:
    """Build a playable situation from a parsed level file."""
    rooms, plate_links, gates_open = {}, {}, []
    used = [r for r in range(1, LF.ROOMS + 1)
            if any(level.types[r]) or any(level.links[r])]
    for r in used:
        rows = []
        for row in range(3):
            line = ""
            for col in range(10):
                block = row * 10 + col
                tid = level.tile_id(r, block)
                if tid not in _SYMBOL:
                    raise LF.LevelFormatError(f"room {r} block {block}: tile id {tid} not supported")
                spec = level.specs[r][block]
                if tid == LF.GATE:                        # R-C29: 1 = up, 2 = down
                    if spec not in (1, 2):
                        raise LF.LevelFormatError(f"room {r} block {block}: gate spec {spec}")
                    if spec == 1:
                        gates_open.append((r, row, col))
                if tid == LF.LOOSE and level.required(r, block):
                    # Never breaks (Source/MOVER.S:394-397); unused in Level 1 (R-C35).
                    raise LF.LevelFormatError(f"room {r} block {block}: required loose floor")
                if tid == LF.FLASK and spec != 1:         # R-A03: Level 1 potions heal
                    raise LF.LevelFormatError(f"room {r} block {block}: potion type {spec}")
                if tid in (LF.PRESSPLATE, LF.UPRESSPLATE):
                    plate_links[(r, row, col)] = tuple(
                        (tr, tb // 10, tb % 10) for tr, tb in level.link_chain(spec))
                line += _SYMBOL[tid]
            rows.append(line)
        rooms[r] = tuple(rows)
    links = {r: tuple(x if x in rooms else 0 for x in level.links[r]) for r in used}
    room, block = level.start_room, level.start_block
    start = (room, block // 10, block % 10, level.start_facing)
    presses: tuple = ()
    if special_start:
        # Level 1 only (Source/SUBS.S:1540-1550): the kid enters falling and the
        # game presses the drop plate at screen 5, block 2, slamming the gate.
        presses = ((5, 0, 2),)
        if rooms.get(5, ("",))[0][2:3] != T.DROP_PLATE:
            raise LF.LevelFormatError("Level 1 special start expects a drop plate at room 5 block 2")
    return Situation(
        id=sid, rooms=rooms, links=links, start=start, plate_links=plate_links,
        exits_open=False, max_actions=max_actions, max_calls=max_actions,
        gates_open=tuple(gates_open), start_falling=special_start,
        start_presses=presses, rules=RULES)


_CACHE: dict[str, Situation] = {}


def load_level1(path: Path | None = None) -> Situation:
    """The original Level 1 as situation `L1`. Raises LevelDataMissing or
    LevelDataMismatch (with setup instructions) if the file is absent or not
    the pinned one."""
    path = Path(path) if path else level1_path()
    key = str(path)
    if key in _CACHE:
        return _CACHE[key]
    if not path.is_file():
        raise LevelDataMissing(SETUP_HINT)
    data = path.read_bytes()
    level = LF.parse(data)
    if level.sha256 not in (APPLE2.sha256, DOS.sha256):
        raise LevelDataMismatch(f"{path} is not the pinned original Level 1 "
                                f"(sha256 {level.sha256}).\n" + SETUP_HINT)
    _CACHE[key] = to_situation(level, "L1")
    return _CACHE[key]


EXHIBITION_IDS = ("L1",)


def available() -> bool:
    try:
        load_level1()
    except (LevelDataMissing, LevelDataMismatch):
        return False
    return True


def get(situation_id: str) -> Situation:
    """Any playable situation by id: the frozen suite, or a reconstructed level."""
    if situation_id in SITUATIONS:
        return SITUATIONS[situation_id]
    if situation_id == "L1":
        return load_level1()
    raise KeyError(situation_id)
