"""The generated art pack (assets/generated/): where it is and which frame to show.

Pure Python, no pygame. The pack is our own art made with PixelLab plus
hand-drawn frames (Saad's decision OQ-8, 2026-11-16; provenance in
docs/final/ART_PROVENANCE.md). Built by tools/build_generated_art.py.

render/anim.py describes every display frame by the original frame number
it would show (so clip timing stays exactly the engine's). `frame_for` maps
each of those numbers to a frame of one of our strips, by its position in
the original sequence; anim.py itself is unchanged by the art choice.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import anim as A

PROJECT = Path(__file__).resolve().parent.parent
PACK_DIR = PROJECT / "assets" / "generated"
MANIFEST = PACK_DIR / "MANIFEST.tsv"

# Display frame held for a dead kid (the last frames of our death strip lift again).
DEAD_FRAME = 6

# original sequence -> our strip; the frame's place in the sequence picks the strip frame
_SEQUENCES: tuple[tuple[tuple[int, ...], str, bool], ...] = (
    (A.START_RUN, "run", False),
    (A.RUN_CYCLE, "run", False),
    (A.STAND_JUMP, "jump", False),
    (A.RUN_JUMP, "leap", False),
    (A.JUMP_UP, "jump", False),
    (A.CROUCH, "crouch", False),
    (A.STAND_UP, "crouch", True),            # standing up: the crouch backwards
    (A.FULL_STEP, "step", False),
    (A.CLIMB_UP, "climb", False),            # CLIMB_DOWN reuses these frame numbers
    (A.DRINK, "drink", False),
    (A.STAIRS, "step", False),
)
_SINGLE = {
    A.STAND: ("stand", 0),
    A.HANG: ("climb", 0),                    # the hang is the climb's first frame
    A.IMPALED: ("death", DEAD_FRAME),
    A.DEAD: ("death", DEAD_FRAME),
}


def manifest_rows() -> list[dict]:
    lines = MANIFEST.read_text().splitlines()
    keys = lines[0].split("\t")
    return [dict(zip(keys, line.split("\t"))) for line in lines[1:] if line]


def pack_dir(root: Path = PACK_DIR) -> Path | None:
    """The pack folder if every manifest file is present and unchanged, else None."""
    try:
        rows = manifest_rows() if root == PACK_DIR else []
    except OSError:
        return None
    for row in rows:
        p = root / row["path"]
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != row["sha256"]:
            return None
    return root if rows else None


def sprites(root: Path = PACK_DIR) -> dict:
    return json.loads((root / "sprites.json").read_text())


def frame_for(frame: int, counts: dict[str, int]) -> tuple[str, int]:
    """(strip, frame index) of our art for original frame number `frame`.
    counts: frames per strip (sprites.json "n")."""
    if frame in _SINGLE:
        return _SINGLE[frame]
    if frame in A.HANG_DROP_FRAMES or frame in A.FALL:
        return "jump", min(5, counts["jump"] - 1)          # airborne, legs down
    if frame in A.TURN:
        return "stand", 0
    if frame in A.DROP_DEAD:
        i = A.DROP_DEAD.index(frame)
        return "death", min(DEAD_FRAME, i * (DEAD_FRAME + 1) // len(A.DROP_DEAD))
    for seq, strip, backwards in _SEQUENCES:
        if frame in seq:
            i = seq.index(frame)
            n = counts[strip]
            k = i * n // len(seq)
            return strip, (n - 1 - k) if backwards else k
    raise KeyError(f"no generated frame for original frame {frame}")
