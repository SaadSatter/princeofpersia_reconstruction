"""T13: the browser side of online play: the page, its rematch button and its limits.

No browser here (the visual check is for QA or Saad). These tests pin what the
code must and must not contain.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
NODE = shutil.which("node")
needs_node = pytest.mark.skipif(NODE is None, reason="node not installed")
FILES = ("online.html", "online.js", "draw.js", "ui.js", "keys.js", "main.js")


@needs_node
@pytest.mark.parametrize("name", ["online.js", "draw.js", "ui.js", "ui.test.js"])
def test_new_js_parses(name):
    out = subprocess.run([NODE, "--check", str(WEB / name)], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr


@needs_node
def test_ui_unit_tests_pass():
    out = subprocess.run([NODE, str(WEB / "ui.test.js")], capture_output=True, text=True,
                         timeout=60)
    assert out.returncode == 0, out.stdout + out.stderr


def test_the_online_page_loads_no_pyodide_and_no_game_zip():
    html = (WEB / "online.html").read_text()
    assert "pyodide" not in html.lower() and "game.zip" not in html.lower()
    assert "{{PHASER_URL}}" in html and "online.js" in html
    js = (WEB / "online.js").read_text()
    assert "pyodide" not in js.lower() and "game.zip" not in js.lower()
    assert "WebSocket" in js


def test_online_js_holds_no_game_logic_and_sends_no_outcomes():
    src = (WEB / "online.js").read_text() + (WEB / "ui.js").read_text()
    for word in ("LUNGE", "SWEEP", "TAKE", "suspicion", "disguised", "legal_actions",
                 "observe(", "hp -", "hearts", "seed", "outcome:"):
        assert word not in src, word
    sends = re.findall(r"send\(([^;]*)\)", src)
    assert sends
    for s in sends:
        assert "type" in s or "msg" in s.lower() or "JSON" in s


def test_the_page_sends_only_keys_a_join_and_a_rematch_request():
    src = (WEB / "online.js").read_text()
    types = set(re.findall(r'type:\s*"(\w+)"', src))
    assert types == {"join", "keys", "rematch"}


def test_the_rematch_button_is_drawn_in_the_games_style_not_a_default_button():
    css = (WEB / "ui.js").read_text()
    assert "appearance: none" in css or "appearance:none" in css
    assert "image-rendering: pixelated" in css
    assert "art/" in css                                  # the generated dungeon art
    assert "border-radius: 0" in css
    assert "font-smooth" in css or "-webkit-font-smoothing: none" in css
    assert "linear-gradient" not in css and "box-shadow: 0 0 " not in css
    assert "Rematch" in css


@needs_node
def test_rematch_button_shows_only_when_the_duel_has_ended_and_names_its_state():
    code = f"""
    const U = require({json.dumps(str(WEB / "ui.js"))});
    const out = {{
      running: U.rematchView({{status: "ongoing"}}, "none"),
      ended: U.rematchView({{status: "terminal"}}, "none"),
      waiting: U.rematchView({{status: "terminal"}}, "waiting"),
      wants: U.rematchView({{status: "terminal"}}, "rival_wants"),
    }};
    process.stdout.write(JSON.stringify(out));
    """
    r = subprocess.run([NODE, "-e", code], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    v = json.loads(r.stdout)
    assert v["running"]["visible"] is False
    assert v["ended"]["visible"] is True and "Rematch" in v["ended"]["label"]
    assert "R" in v["ended"]["hint"] or "Enter" in v["ended"]["hint"]
    assert v["waiting"]["label"].startswith("Waiting for rival")
    assert v["waiting"]["disabled"] is True
    assert "Rival wants a rematch" in v["wants"]["note"]


def test_the_local_page_uses_the_same_button():
    main = (WEB / "main.js").read_text()
    assert "SMUi" in main and "rematch" in main
    online = (WEB / "online.js").read_text()
    assert "SMUi" in online and "SMDraw" in online


def test_the_online_page_draws_with_draw_js():
    """draw.js is main.js's drawer, copied (tests/test_gate_t14_qa_main_contract.py pins
    main.js as one self-contained file, so it was not refactored to share it)."""
    drawer = (WEB / "draw.js").read_text()
    assert "function makeDrawer" in drawer
    for fragment in ("setDisplaySize(d.w, d.h)", "setFillStyle(colour(d.color))",
                     "setStrokeStyle(1, colour(d.color))"):
        assert fragment in drawer and fragment in (WEB / "main.js").read_text()


def test_the_build_ships_the_online_page_and_its_scripts(tmp_path):
    from tools.web import build
    m = build.build(tmp_path)
    assert {"online.html", "online.js", "draw.js", "ui.js", "keys.js"} <= set(m["files"])
    html = (tmp_path / "online.html").read_text()
    assert "{{" not in html and "phaser" in html.lower()


def test_the_key_hints_cover_both_seats_in_online_mode():
    online = (WEB / "online.js").read_text()
    assert "keyHints" in online


def test_the_page_cannot_choose_or_learn_the_rival_kind():
    """E1: the server picks the rival (--rival); the page passes no query option through."""
    js = (WEB / "online.js").read_text()
    assert "location.search" not in js and "parseOptions" not in js
    assert "agents/" not in js and ".zip" not in js
