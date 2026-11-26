"""T14: tools/web/build.py writes a reproducible static site (web/dist/)."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _tool():
    spec = importlib.util.spec_from_file_location("web_build", ROOT / "tools" / "web" / "build.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    tool = _tool()
    one, two = tmp_path_factory.mktemp("dist1"), tmp_path_factory.mktemp("dist2")
    return tool, tool.build(one), one, tool.build(two), two


def files(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def test_two_builds_are_identical(built):
    _, m1, d1, m2, d2 = built
    assert m1 == m2
    assert files(d1) == files(d2)


def test_manifest_lists_every_file_with_its_hash(built):
    _, m1, d1, _, _ = built
    on_disk = files(d1)
    on_disk.pop("manifest.json")
    assert m1["files"] == on_disk
    assert json.loads((d1 / "manifest.json").read_text()) == m1


def test_the_site_has_the_page_the_archive_and_the_art(built):
    _, m, _, _, _ = built
    names = set(m["files"])
    assert {"index.html", "main.js", "keys.js", "game.zip", "art/spikes.png"} <= names
    assert "art/rival/run.png" in names and "art/rival_crimson/run.png" in names
    assert "art/guard/walk.png" in names and "art/tiles.png" in names


def test_every_sheet_the_draw_list_can_name_is_shipped(built):
    _, m, _, _, _ = built
    sheets = {n[len("art/"):-len(".png")] for n in m["files"] if n.startswith("art/")}
    assert set(m["sheets"]) == sheets
    sprites = json.loads((ROOT / "assets" / "generated" / "sprites.json").read_text())
    for who, strips in sprites.items():
        for strip in strips:
            assert f"{who}/{strip}" in sheets
            if who == "rival":
                assert f"rival_crimson/{strip}" in sheets
    assert {"tiles", "spikes", "props/pillar", "props/torch", "props/door"} <= sheets


def test_the_archive_holds_the_pure_packages_only(built):
    _, _, d1, _, _ = built
    names = set(zipfile.ZipFile(d1 / "game.zip").namelist())
    assert {"web/__init__.py", "web/bridge.py", "web/art.json", "pop/versus.py",
            "render/draw_list.py", "render/versus_view.py", "render/anim.py"} <= names
    for banned in ("render/draw.py", "render/dungeon.py", "play.py"):
        assert banned not in names
    # agents/ is shipped since T14-fix1, but only the scripted rival (tests/test_web_rival.py).
    assert not any(n.startswith(("tests/", "tools/", "traces/", "docs/")) for n in names)


def test_the_archive_runs_on_its_own(built, tmp_path):
    """Unpacked anywhere, the archive starts a game with the standard library only,
    as Pyodide will (no repository, no assets folder, no pygame)."""
    _, _, d1, _, _ = built
    zipfile.ZipFile(d1 / "game.zip").extractall(tmp_path)
    code = ("import sys, json; sys.path.insert(0, '.'); from web.bridge import WebGame; "
            "g = WebGame(seed=3); p = json.loads(g.tick_json()); "
            "assert p['draw'] and p['seat_view']['me']; "
            "assert 'pygame' not in sys.modules; print('ok', len(p['draw']))")
    out = subprocess.run([sys.executable, "-I", "-c", code], cwd=tmp_path,
                         capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    assert out.stdout.startswith("ok ")


def test_versions_are_pinned_in_one_place_and_used(built):
    _, m, d1, _, _ = built
    versions = json.loads((ROOT / "web" / "versions.json").read_text())
    assert re.fullmatch(r"0\.27\.\d+", versions["pyodide"])
    assert re.fullmatch(r"3\.\d+\.\d+", versions["phaser"])
    page = (d1 / "index.html").read_text()
    assert f"pyodide/v{versions['pyodide']}/full/pyodide.js" in page
    assert f"phaser@{versions['phaser']}/dist/phaser.min.js" in page
    assert "{{" not in page
    assert m["versions"] == versions
    # The source page names no version of its own.
    src = (ROOT / "web" / "index.html").read_text()
    assert versions["pyodide"] not in src and versions["phaser"] not in src


def test_generated_pngs_are_the_format_webart_reads():
    from render import webart
    for p in sorted((ROOT / "assets" / "generated").rglob("*.png")):
        w, h, rows = webart.read_png(p.read_bytes())
        assert (w, h) == webart.png_size(p.read_bytes()) and len(rows) == h


def test_png_reader_matches_a_reference_decoder():
    PIL = pytest.importorskip("PIL.Image")
    from render import webart
    for p in sorted((ROOT / "assets" / "generated").rglob("*.png"))[:12]:
        w, h, rows = webart.read_png(p.read_bytes())
        assert b"".join(rows) == PIL.open(p).convert("RGBA").tobytes(), p


def test_crimson_matches_the_pygame_recolour_formula():
    from render import webart
    assert webart.crimson_pixel(40, 40, 120, 255)[0] > 100       # indigo -> crimson
    r, g, b, a = webart.crimson_pixel(200, 20, 20, 255)            # red sash -> gold
    assert r > b and g > b and a == 255
    assert webart.crimson_pixel(90, 90, 90, 255) == (90, 90, 90, 255)
    assert webart.crimson_pixel(40, 40, 120, 0) == (40, 40, 120, 0)


def test_dist_is_gitignored():
    out = subprocess.run(["git", "check-ignore", "-q", "web/dist/index.html"], cwd=ROOT)
    assert out.returncode == 0


def test_build_prints_the_hashes(tmp_path):
    out = subprocess.run([sys.executable, str(ROOT / "tools" / "web" / "build.py"),
                          "--out", str(tmp_path / "d")], cwd=ROOT, capture_output=True,
                         text=True, timeout=300)
    assert out.returncode == 0, out.stderr
    m = json.loads((tmp_path / "d" / "manifest.json").read_text())
    for name, digest in m["files"].items():
        assert f"{digest}  {name}" in out.stdout
