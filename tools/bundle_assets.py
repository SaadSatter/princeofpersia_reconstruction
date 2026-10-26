"""Rebuild the bundled original images in assets/original/ (maintainers only).

    uv run python tools/bundle_assets.py             # working directory: the project folder
    uv run python tools/bundle_assets.py --check     # verify assets/original against MANIFEST.tsv

The game never runs this and never downloads anything: it draws the images
committed in assets/original/. This tool exists so the bundle is
reproducible. It sparse-fetches three image folders from SDLPoP
(https://github.com/NagyD/SDLPoP) at a pinned commit into the git-ignored
vendor/SDLPoP/ (never committed), copies only the images the frontend draws
(render/assets.py `required_files`), and writes MANIFEST.tsv with each
file's source path, size and SHA-256. See docs/ASSET_PROVENANCE.md.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from render import assets  # noqa: E402

REPO = "https://github.com/NagyD/SDLPoP.git"
COMMIT = "3c5add5fb7f83d4ceb542823ab66d00146c4271b"   # 2025-12-24
FOLDERS = ("data/KID", "data/VDUNGEON", "data/PRINCE")
VENDOR = PROJECT / "vendor" / "SDLPoP"
BUNDLE = assets.DEFAULT_DIR
HEADER = "path\tsource\tbytes\tsha256"


def run(*args: str, cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True)


def fetch(dest: Path = VENDOR) -> Path:
    if shutil.which("git") is None:
        sys.exit("git is required.")
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    run("git", "init", "-q", cwd=dest)
    run("git", "remote", "add", "origin", REPO, cwd=dest)
    run("git", "sparse-checkout", "set", "--no-cone", *FOLDERS, cwd=dest)
    run("git", "fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", COMMIT, cwd=dest)
    run("git", "checkout", "-q", "FETCH_HEAD", cwd=dest)
    shutil.rmtree(dest / ".git")
    return dest / "data"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bundle(source: Path) -> list[str]:
    if BUNDLE.exists():
        for sub in ("KID", "VDUNGEON", "PRINCE"):
            shutil.rmtree(BUNDLE / sub, ignore_errors=True)
    rows = [HEADER]
    for src in assets.required_files(source):
        rel = src.relative_to(source)
        dst = BUNDLE / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        rows.append(f"{rel.as_posix()}\tSDLPoP@{COMMIT[:7]}:data/{rel.as_posix()}\t"
                    f"{dst.stat().st_size}\t{sha256(dst)}")
    assets.MANIFEST.write_text("\n".join(rows) + "\n")
    return rows[1:]


def check() -> list[str]:
    """Problems with the bundle, or [] if it matches the manifest exactly."""
    problems = []
    if not assets.MANIFEST.is_file():
        return [f"missing {assets.MANIFEST}"]
    listed = {}
    for line in assets.MANIFEST.read_text().splitlines()[1:]:
        path, _src, size, digest = line.split("\t")
        listed[path] = (int(size), digest)
    on_disk = {p.relative_to(BUNDLE).as_posix() for p in BUNDLE.rglob("*.png")}
    required = {p.relative_to(BUNDLE).as_posix() for p in assets.required_files(BUNDLE)}
    for path in sorted(required - set(listed)):
        problems.append(f"required but not in manifest: {path}")
    for path in sorted(set(listed) - required):
        problems.append(f"in manifest but not used by the game: {path}")
    for path in sorted(on_disk - set(listed)):
        problems.append(f"unlisted file: {path}")
    for path, (size, digest) in sorted(listed.items()):
        f = BUNDLE / path
        if not f.is_file():
            problems.append(f"missing file: {path}")
        elif f.stat().st_size != size or sha256(f) != digest:
            problems.append(f"changed file: {path}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="verify the bundle; no network")
    ap.add_argument("--source", type=Path, help="use an existing SDLPoP data/ folder")
    args = ap.parse_args()
    if args.check:
        problems = check()
        print("\n".join(problems) or f"assets/original matches MANIFEST.tsv")
        return 1 if problems else 0
    source = args.source or fetch()
    rows = bundle(source)
    total = sum(int(r.split("\t")[2]) for r in rows)
    print(f"Bundled {len(rows)} images ({total} bytes) from SDLPoP {COMMIT[:7]} into "
          f"{BUNDLE.relative_to(PROJECT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
