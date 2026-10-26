"""Download the original Prince of Persia (DOS) images for local use only.

    uv run python tools/fetch_assets.py          # working directory: the project folder

Fetches three image folders from SDLPoP (https://github.com/NagyD/SDLPoP) at
a pinned commit into vendor/SDLPoP/ (git-ignored). SDLPoP's GPLv3 covers its
program code, not these images; they are the original game's graphics and
nobody has granted us rights to redistribute them. Never commit them, copy
them into the course repository, or ship them. See docs/ASSETS.md.

Without these files the frontend draws placeholder shapes instead.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO = "https://github.com/NagyD/SDLPoP.git"
COMMIT = "3c5add5fb7f83d4ceb542823ab66d00146c4271b"   # 2025-12-24
FOLDERS = ("data/KID", "data/VDUNGEON", "data/PRINCE")
DEST = Path(__file__).resolve().parent.parent / "vendor" / "SDLPoP"


def run(*args: str, cwd: Path | None = None) -> None:
    subprocess.run(args, cwd=cwd, check=True)


def fetch(dest: Path = DEST) -> Path:
    if shutil.which("git") is None:
        sys.exit("git is required to fetch the assets.")
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    run("git", "init", "-q", cwd=dest)
    run("git", "remote", "add", "origin", REPO, cwd=dest)
    run("git", "sparse-checkout", "set", "--no-cone", *FOLDERS, cwd=dest)
    run("git", "fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", COMMIT, cwd=dest)
    run("git", "checkout", "-q", "FETCH_HEAD", cwd=dest)
    shutil.rmtree(dest / ".git")          # keep only the images
    return dest


def main() -> None:
    dest = fetch()
    counts = {f: len(list((dest / f).glob("*.png"))) for f in FOLDERS}
    print(f"Fetched SDLPoP {COMMIT[:7]} images into {dest.relative_to(Path.cwd()) if dest.is_relative_to(Path.cwd()) else dest}:")
    for folder, n in counts.items():
        print(f"  {folder}: {n} PNG files")
    print("Local use only. Do not commit or redistribute (docs/ASSETS.md).")


if __name__ == "__main__":
    main()
