"""Fetch the original Level 1 file for local play (one-time setup, network).

    uv run python tools/fetch_level1.py            # fetch + verify (working directory: the project folder)
    uv run python tools/fetch_level1.py --check    # verify what is there, no network
    uv run python tools/fetch_level1.py --show     # print the rooms to this terminal only

Downloads the Apple II `LEVEL1` (historicalsource/princeofpersia, pinned
commit) and, as a cross-check, the DOS level 1 resource (NagyD/SDLPoP,
pinned commit) into the git-ignored `vendor/levels/`. Each file must match
its pinned size and SHA-256 (pop/levels.py), and the two must describe the
same layout. Nothing is written anywhere else, and the game never
downloads at run time. The original level data is never committed
(docs/LEVEL1.md, student decision D1 of 2026-10-26).
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from pop import levelfile as LF  # noqa: E402
from pop import levels  # noqa: E402

SOURCES = (levels.APPLE2, levels.DOS)


def _verify(src: levels.Source, data: bytes) -> str | None:
    if len(data) != src.size:
        return f"{src.filename}: {len(data)} bytes, expected {src.size}"
    digest = hashlib.sha256(data).hexdigest()
    if digest != src.sha256:
        return f"{src.filename}: sha256 {digest}, expected {src.sha256}"
    return None


def fetch(dest: Path) -> int:
    dest.mkdir(parents=True, exist_ok=True)
    for src in SOURCES:
        with urllib.request.urlopen(src.url, timeout=30) as resp:   # noqa: S310 (pinned https URL)
            data = resp.read()
        problem = _verify(src, data)
        if problem:
            print("refused:", problem, file=sys.stderr)
            return 1
        (dest / src.filename).write_bytes(data)
        print(f"ok  {src.name} -> {(dest / src.filename).relative_to(PROJECT)}")
    return check(dest)


def check(dest: Path) -> int:
    parsed = []
    for src in SOURCES:
        path = dest / src.filename
        if not path.is_file():
            print(f"missing {path.relative_to(PROJECT)}; run without --check to fetch", file=sys.stderr)
            return 1
        problem = _verify(src, path.read_bytes())
        if problem:
            print("bad:", problem, file=sys.stderr)
            return 1
        parsed.append(LF.parse(path.read_bytes()))
    if not LF.same_layout(*parsed):
        print("bad: the Apple II and DOS files describe different layouts", file=sys.stderr)
        return 1
    levels.to_situation(parsed[0], "L1")      # every tile id is supported
    print("ok  both files verified; Apple II and DOS layouts are identical; L1 loads")
    return 0


def show(dest: Path) -> int:
    s = levels.load_level1(dest / levels.APPLE2.filename)
    for room in sorted(s.rooms):
        l, r, u, d = s.links[room]
        print(f"room {room:2d}  left {l} right {r} up {u} down {d}")
        for row in s.rooms[room]:
            print("   ", row)
    print("start (room, row, col, facing):", s.start)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="verify the local files (no network)")
    ap.add_argument("--show", action="store_true", help="print the decoded rooms to the terminal")
    args = ap.parse_args(argv)
    if args.show:
        return show(levels.LEVEL_DIR)
    if args.check:
        return check(levels.LEVEL_DIR)
    return fetch(levels.LEVEL_DIR)


if __name__ == "__main__":
    sys.exit(main())
