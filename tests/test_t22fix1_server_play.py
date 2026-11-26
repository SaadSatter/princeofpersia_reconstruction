"""T22-fix1: decision #91 (no legacy label) and decision #92 (menu by default, hosted chooser).
Written before the fixes.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from agents import modes                      # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
NODE = shutil.which("node")


# --- #91 ----------------------------------------------------------------------------------
def test_the_server_cli_has_no_legacy_label_path():
    src = (ROOT / "server" / "__main__.py").read_text()
    assert "legacy" not in src
    assert "honest=" not in src or "honest=not" not in src


# --- #92: pygame -----------------------------------------------------------------------------
@pytest.fixture
def pg():
    return pytest.importorskip("pygame")


def test_a_bare_play_py_shows_the_menu_and_escape_quits(pg, monkeypatch):
    import play
    shown = []
    from render import menu
    real = menu.run_menu
    monkeypatch.setattr(menu, "run_menu", lambda *a, **k: (shown.append(1), real(*a, **k))[1])
    assert play.main(["--menu-keys", "escape", "--scale", "1"]) == 0
    assert shown == [1]


def test_a_bare_play_py_menu_choice_starts_that_mode(pg, monkeypatch, tmp_path):
    import play
    made = []
    real = modes.make_seat_rival
    monkeypatch.setattr(modes, "make_seat_rival", lambda m, **k: (made.append(m), real(m, **k))[1])
    assert play.main(["--menu-keys", "down,return", "--scale", "1",
                      "--screenshot", str(tmp_path / "s.png")]) == 0
    assert made == ["baseline"]


def test_the_old_single_player_level_stays_reachable(pg, tmp_path):
    import play
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    assert play.main(["S3", "--screenshot", str(a), "--keys", "RIGHT,RIGHT"]) == 0     # situation argument
    assert play.main(["--classic", "--screenshot", str(b), "--keys", "RIGHT,RIGHT"]) == 0   # the flag
    assert a.read_bytes() == b.read_bytes()


def test_the_help_names_the_classic_flag():
    out = subprocess.run(["python3", str(ROOT / "play.py"), "--help"], capture_output=True, text=True,
                         cwd=ROOT, timeout=60)
    assert "--classic" in out.stdout


# --- #92: hosted page --------------------------------------------------------------------------
needs_node = pytest.mark.skipif(NODE is None, reason="node not installed")


@needs_node
@pytest.mark.parametrize("search, chooser", [
    ("", True), ("?", True), ("?seed=3", True), ("?seat=B", True),
    ("?play=ai", False), ("?play=baseline", False), ("?play=human", False),
    ("?mode=ai", False), ("?mode=local", False), ("?rival=idle", False), ("?mode=ai&rival=random", False),
])
def test_the_page_opens_on_the_chooser_only_without_a_game_choice(search, chooser):
    code = ("const K=require(process.argv[1]);"
            "console.log(JSON.stringify(K.needsChooser(process.argv[2])))")
    out = subprocess.run([NODE, "-e", code, str(ROOT / "web" / "keys.js"), search],
                         capture_output=True, text=True, timeout=30)
    assert out.stdout.strip() == ("true" if chooser else "false"), out.stderr


def test_main_js_does_not_start_python_while_the_chooser_is_up():
    main = (ROOT / "web" / "main.js").read_text()
    assert "needsChooser" in main
    i = main.index("needsChooser")
    assert "startPython" in main[i:i + 600] or "return" in main[i:i + 400]


def test_smoke_script_picks_a_mode_first():
    s = (ROOT / "tools" / "web" / "smoke.cjs").read_text()
    assert re.search(r'#modes a|a\.mode|\?play=', s)
    assert s.index("#modes") < s.index('waitForSelector(\'#status')
