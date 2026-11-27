"""Build the hosted web page into web/dist/ (T14). Standard library only.

    python3 tools/web/build.py                 # writes web/dist/
    python3 tools/web/build.py --out /tmp/site
    cd web/dist && python3 -m http.server 8000 # then open http://localhost:8000

Writes:

* index.html  web/index.html with the pinned CDN URLs from web/versions.json
* online.html  the online page (T13): no Pyodide, served by `python -m server`
* main.js, keys.js, draw.js, ui.js, online.js  the pages' JavaScript (copied)
* game.zip    the Python the page runs in Pyodide: pop/ (all of it), the
              pygame-free render/ modules the draw list needs, web/bridge.py,
              and web/art.json (the art pack's measured sizes)
* art/        the generated art pack's images, the crimson rival's strips
              (render/webart.py crimson_pixel, as render/dungeon.py recolours
              at load time) and the spike states
* manifest.json  every file above with its SHA-256, the versions, the sheets and
              `build`, an 8-hex-digit hash of the file hashes (shown on the page,
              for the playtest log)

game.zip also holds agents/ (the scripted baseline rival and what it imports:
standard library only; the model providers are not shipped). It is public.

Reproducible: files are written in a fixed order, the zip has fixed
timestamps and permissions, and PNGs are encoded with fixed settings, so the
same inputs give byte-identical output. The hashes are printed.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents import modes  # noqa: E402
from render import webart  # noqa: E402

WEB = ROOT / "web"
PACK = ROOT / "assets" / "generated"
DEFAULT_OUT = WEB / "dist"
# render/ modules the draw list imports (no pygame): checked by
# tests/test_web_build.py::test_the_archive_runs_on_its_own.
RENDER_MODULES = ("__init__.py", "anim.py", "genart.py", "versus_view.py", "draw_list.py",
                  "webart.py")
WEB_MODULES = ("__init__.py", "bridge.py")
# The scripted rival the page plays against; stdlib only (tests/test_web_rival.py).
AGENT_MODULES = ("__init__.py", "baseline.py", "macros.py", "versus_baseline.py", "modes.py")
# T22: the trained rival, stdlib inference and the shipped weights. The page loads them through
# agents.modes / make_rl_rival, which refuses a file whose SHA-256 is not the shipped one.
RL_FILES = ("__init__.py", "encoder.py", "policy.py", "weights/ppo-run-1.json")
PAGE_FILES = ("main.js", "keys.js", "draw.js", "ui.js", "online.js")
ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def versions() -> dict:
    v = json.loads((WEB / "versions.json").read_text())
    if f"/v{v['pyodide']}/" not in v["pyodide_url"] or f"@{v['phaser']}/" not in v["phaser_url"]:
        raise SystemExit("web/versions.json: a URL does not match its pinned version")
    return v


def python_files() -> list[tuple[str, bytes]]:
    files = [(f"pop/{p.name}", p.read_bytes()) for p in sorted((ROOT / "pop").glob("*.py"))]
    files += [(f"render/{n}", (ROOT / "render" / n).read_bytes()) for n in RENDER_MODULES]
    files += [(f"web/{n}", (WEB / n).read_bytes()) for n in WEB_MODULES]
    files += [(f"agents/{n}", (ROOT / "agents" / n).read_bytes()) for n in AGENT_MODULES]
    files += [(f"agents/rl/{n}", (ROOT / "agents" / "rl" / n).read_bytes()) for n in RL_FILES]
    art = json.dumps(webart.art_meta(PACK), sort_keys=True, separators=(",", ":"))
    files.append(("web/art.json", art.encode()))
    return sorted(files)


def game_zip(files: list[tuple[str, bytes]]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, data in files:
            info = zipfile.ZipInfo(name, date_time=ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            info.create_system = 3
            z.writestr(info, data, compresslevel=9)
    return buf.getvalue()


def art_files() -> list[tuple[str, bytes]]:
    sprites = json.loads((PACK / "sprites.json").read_text())
    out = [("art/tiles.png", (PACK / "tiles" / "platform.png").read_bytes()),
           ("art/spikes.png", webart.spikes_sheet())]
    for name in ("pillar", "torch", "door"):
        out.append((f"art/props/{name}.png", (PACK / "props" / f"{name}.png").read_bytes()))
    for who, strips in sorted(sprites.items()):
        for strip, m in sorted(strips.items()):
            data = (PACK / m["file"]).read_bytes()
            out.append((f"art/{who}/{strip}.png", data))
            if who == "rival":
                out.append((f"art/rival_crimson/{strip}.png", webart.crimson_png(data)))
    return sorted(out)


def page(v: dict, name: str = "index.html") -> bytes:
    src = (WEB / name).read_text()
    html = (src.replace("{{PYODIDE_URL}}", v["pyodide_url"])
            .replace("{{PHASER_URL}}", v["phaser_url"]))
    if "{{" in html:
        raise SystemExit(f"web/{name}: unknown placeholder left")
    return html.encode()


def build_hash(file_hashes: dict[str, str]) -> str:
    """Short id of a build: the first 8 hex digits of the hash of every file's hash."""
    text = "".join(f"{h}  {n}\n" for n, h in sorted(file_hashes.items()))
    return hashlib.sha256(text.encode()).hexdigest()[:8]


def build(out: Path = DEFAULT_OUT) -> dict:
    out = Path(out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    v = versions()
    files: list[tuple[str, bytes]] = [("index.html", page(v)),
                                      ("online.html", page(v, "online.html"))]
    files += [(n, (WEB / n).read_bytes()) for n in PAGE_FILES]
    files.append(("game.zip", game_zip(python_files())))
    files += art_files()
    for name, data in files:
        p = out / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    weights_sha = modes.verify_shipped()           # refuses to build around a wrong file
    sheets = sorted(n[len("art/"):-len(".png")] for n, _ in files if n.startswith("art/"))
    hashes = {n: hashlib.sha256(d).hexdigest() for n, d in sorted(files)}
    manifest = {
        "build": build_hash(hashes),
        "files": hashes,
        "versions": v,
        "sheets": sheets,
        "modes": modes.manifest_modes(),           # the one mode list both pages read (T22)
        "weights_sha256": weights_sha,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return manifest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)
    m = build(args.out)
    for name, digest in m["files"].items():
        print(f"{digest}  {name}")
    whole = hashlib.sha256((args.out / "manifest.json").read_bytes()).hexdigest()
    print(f"{whole}  manifest.json")
    print(f"built {len(m['files'])} files into {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
