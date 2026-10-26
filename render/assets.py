"""Find the bundled original images (pure; no pygame).

The images the frontend draws are committed in `assets/original/` (student
decision, docs/ASSET_PROVENANCE.md); nothing is downloaded at run time.
`POP_ASSETS` may point at another folder with the same layout. If any
required image is missing the frontend draws placeholder shapes (R-D02).
"""

from __future__ import annotations

import os
from pathlib import Path

from . import anim

PROJECT = Path(__file__).resolve().parent.parent
DEFAULT_DIR = PROJECT / "assets" / "original"
MANIFEST = DEFAULT_DIR / "MANIFEST.tsv"

# Our own piece choices from the DOS image set (identified by eye; docs/ASSETS.md).
KID_HEARTS = {"full": 617, "empty": 618}
DUNGEON = {
    "floor": 241, "floor_right": 242, "base": 243,
    "loose": 269, "loose_shake": 270, "loose_right": 271, "loose_right_shake": 272,
    "rubble": 297, "rubble_right": 298,
    "pillar": 286, "pillar_right": 287,
    "gate": 246, "gate_bars": 252, "gate_bottom": 250,
    "plate_up": 347, "plate_down": 348, "plate_base": 349,
    "spike_floor": 327, "spike_floor_right": 333,
    "spikes_low": 328, "spikes_out": 331,
    "exit_left": 214, "exit_right": 216, "exit_top_left": 215, "exit_top_right": 217,
    "exit_panel": 300, "exit_stairs": 344,
    "torch_bracket": 346,
    "decor": (244, 245, 324, 325),
}
# Kid frame -> DOS image. The DOS image set is not in frame order; these
# shifts (image index = frame + shift, file = res(401 + index)) cover only the
# frames render/anim.py uses. Read from SDLPoP's frame table (src/seg006.c,
# frame_table_kid) and checked by eye; the table itself is not copied.
FRAME_SHIFTS = (
    (1, 52, -1), (67, 85, 13), (87, 99, 12), (102, 119, 10), (121, 132, 12),
    (135, 148, 10), (177, 177, -99), (179, 183, 32), (185, 185, -106),
    (191, 205, 1), (217, 228, -165),
)


def image_for(frame: int) -> int:
    """The KID/resNNN.png number that shows this original frame."""
    for lo, hi, shift in FRAME_SHIFTS:
        if lo <= frame <= hi:
            return 401 + frame + shift
    raise KeyError(f"no DOS image mapped for kid frame {frame}")


WALLS = ((364, 363), (366, 365), (368, 367), (370, 369))    # (face, base)
FLAMES = tuple(range(151, 160))
POTION = 162
BUBBLES = tuple(range(166, 173))


def asset_dir() -> Path | None:
    """The image folder if every image we use is there, else None."""
    root = Path(os.environ.get("POP_ASSETS", DEFAULT_DIR))
    return root if not missing(root) else None


def required_files(root: Path) -> list[Path]:
    files = [root / "KID" / f"res{image_for(n)}.png" for n in sorted(anim.ALL_FRAMES)]
    files += [root / "KID" / f"res{n}.png" for n in KID_HEARTS.values()]
    ids: list[int] = []
    for v in DUNGEON.values():
        ids.extend(v if isinstance(v, tuple) else [v])
    for face, base in WALLS:
        ids += [face, base]
    files += [root / "VDUNGEON" / f"res{n}.png" for n in sorted(set(ids))]
    files += [root / "PRINCE" / f"res{n}.png" for n in (*FLAMES, POTION, *BUBBLES)]
    return files


def missing(root: Path) -> list[Path]:
    return [p for p in required_files(root) if not p.is_file()]
