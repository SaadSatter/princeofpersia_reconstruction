"""T14: the page's JavaScript parses, and its pure key helpers agree with play.py.

Needs Node.js (skipped without it). No browser: the real page is checked by
.github/workflows/web-smoke.yml.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

import play

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
NODE = shutil.which("node")
needs_node = pytest.mark.skipif(NODE is None, reason="node not installed")


@needs_node
@pytest.mark.parametrize("name", ["main.js", "keys.js", "keys.test.js"])
def test_js_parses(name):
    out = subprocess.run([NODE, "--check", str(WEB / name)], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr


@needs_node
def test_js_unit_tests_pass():
    out = subprocess.run([NODE, str(WEB / "keys.test.js")], capture_output=True, text=True,
                         timeout=60)
    assert out.returncode == 0, out.stdout + out.stderr


@needs_node
def test_js_key_names_cover_play_py_versus_keys():
    code = ("const k = require(%s); process.stdout.write(JSON.stringify(k.CODE_TO_KEY));"
            % json.dumps(str(WEB / "keys.js")))
    out = subprocess.run([NODE, "-e", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    names = set(json.loads(out.stdout).values())
    wanted = {v for m in play.VERSUS_KEYS.values() for v in m.values()} | {"r"}
    assert wanted <= names


def test_main_js_holds_no_game_rules():
    """The page only maps keys, calls the bridge and blits its draw list."""
    src = (WEB / "main.js").read_text()
    for word in ("LUNGE", "SWEEP", "TAKE", "suspicion", "disguised", "legal_actions",
                 "observe(", "hp -", "hearts"):
        assert word not in src, word


@needs_node
def test_browser_smoke_script_parses():
    out = subprocess.run([NODE, "--check", str(ROOT / "tools" / "web" / "smoke.cjs")],
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr


def test_page_asks_for_no_missing_favicon():
    """A 404 for /favicon.ico is a console error, which fails the browser smoke test."""
    assert 'rel="icon"' in (WEB / "index.html").read_text()


# --- T13: the online page's scripts follow the same rule --------------------------
@pytest.mark.parametrize("name", ["draw.js", "ui.js", "online.js"])
def test_t13_page_scripts_hold_no_game_rules(name):
    src = (WEB / name).read_text()
    for word in ("LUNGE", "SWEEP", "TAKE", "suspicion", "legal_actions", "observe(", "hp -"):
        assert word not in src, (name, word)
