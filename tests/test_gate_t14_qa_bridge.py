"""GATE-T14 QA: bridge, build, workflow and doc checks beyond tests/test_web_*.py.

CPython only. What these cannot show is listed in the gate report (no browser,
no Pyodide, no Phaser).
"""

from __future__ import annotations

import json
import re
import struct
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pop.versus import SEATS  # noqa: E402
from tools.web import build as webbuild  # noqa: E402
from web.bridge import KEY_MAP, RandomRival, WebGame  # noqa: E402


@pytest.fixture(scope="module")
def dist(tmp_path_factory):
    out = tmp_path_factory.mktemp("qa-dist")
    return out, webbuild.build(out)


def png_size(path: Path) -> tuple[int, int]:
    head = path.read_bytes()[:24]
    assert head[:8] == b"\x89PNG\r\n\x1a\n", path
    return struct.unpack(">II", head[16:24])


def script(i):
    return {"d": i % 20 < 12, "a": i % 40 > 30, "w": i % 23 == 0, "f": i % 17 == 0,
            "g": i % 29 == 0, "left": i % 13 < 4, ".": i % 11 == 0, "up": i % 19 == 0}


def stream(mode, seed, n, human_seat="A", rival=None):
    g = WebGame(mode=mode, seed=seed, human_seat=human_seat, rival=rival)
    out = []
    for i in range(n):
        g.press(script(i))
        out.append(json.dumps(g.tick(), sort_keys=True))
    return out


# --- determinism ---------------------------------------------------------------------
@pytest.mark.parametrize("seat", SEATS)
def test_same_seed_and_keys_give_the_same_stream_both_seats_and_modes(seat):
    assert stream("human_vs_ai", 5, 150, seat, RandomRival(5)) == \
        stream("human_vs_ai", 5, 150, seat, RandomRival(5))
    assert stream("local_two_players", 5, 150) == stream("local_two_players", 5, 150)


def test_rematch_replays_the_same_stream():
    g = WebGame(seed=4, rival=RandomRival(4))
    first = []
    for i in range(80):
        g.press(script(i))
        first.append(json.dumps(g.tick(), sort_keys=True))
    g.rematch()
    second = []
    for i in range(80):
        g.press(script(i))
        second.append(json.dumps(g.tick(), sort_keys=True))
    assert first == second


def test_payload_is_strict_json_with_no_nan():
    """JSON.parse rejects NaN and Infinity, which Python's json.dumps writes by default."""
    g = WebGame(seed=1, rival=RandomRival(1))
    for i in range(400):
        g.press(script(i))
        json.dumps(g.tick(), allow_nan=False)


# --- the key map: the two players' keys do not interfere -------------------------------
def test_local_mode_each_seat_obeys_only_its_own_keys():
    def run(keys):
        g = WebGame(mode="local_two_players", seed=2)
        out = []
        for _ in range(30):
            g.press(keys)
            p = g.tick()
            out.append({s: json.dumps(p["seats"][s]["seat_view"]["me"], sort_keys=True)
                        for s in SEATS})
        return out

    idle = run({})
    a_only = run({"d": True, "lshift": True})
    b_only = run({"left": True, "rshift": True})
    assert any(x["A"] != y["A"] for x, y in zip(idle, a_only)), "A's keys did nothing"
    assert any(x["B"] != y["B"] for x, y in zip(idle, b_only)), "B's keys did nothing"
    assert all(x["B"] == y["B"] for x, y in zip(idle, a_only)), "A's keys moved B"
    assert all(x["A"] == y["A"] for x, y in zip(idle, b_only)), "B's keys moved A"


def test_key_names_are_disjoint_between_seats():
    a, b = set(KEY_MAP["A"].values()), set(KEY_MAP["B"].values())
    assert not a & b


def test_human_on_seat_b_uses_seat_b_keys_only():
    def me(keys, seat):
        g = WebGame(seed=2, human_seat="B")
        for _ in range(30):
            g.press(keys)
            p = g.tick()
        return json.dumps(p["seat_view"]["me"], sort_keys=True)

    assert me({"left": True}, "B") != me({}, "B")
    assert me({"d": True, "a": True, "w": True}, "B") == me({}, "B")


def test_unknown_and_falsey_keys_do_nothing():
    g = WebGame(seed=1)
    assert g.press({"zzz": True, "d": False, "lshift": 0}) == {"A": {"held": [], "shift": False}}


# --- terminal state --------------------------------------------------------------------
def test_keys_after_the_duel_ends_change_nothing():
    g = WebGame(seed=1, rival=RandomRival(1))
    while g.episode.outcome()["status"] != "terminal":
        g.tick()
    before = json.dumps(g.payload(), sort_keys=True)
    inputs = dict(g.episode.outcome()["inputs"])
    g.press({"d": True, "f": True, "w": True})
    for _ in range(10):
        g.tick()
    assert g.payload()["outcome"] == json.loads(before)["outcome"]
    assert g.episode.outcome()["inputs"] == inputs


# --- build: everything the page loads is in the build -----------------------------------
def test_every_sheet_drawn_is_loaded_and_its_source_rect_is_inside_the_png(dist):
    out, manifest = dist
    sheets = set(manifest["sheets"])
    sizes = {s: png_size(out / "art" / f"{s}.png") for s in sheets}
    seen = set()
    for mode, kw in (("human_vs_ai", {"rival": RandomRival(3)}), ("local_two_players", {})):
        g = WebGame(mode=mode, seed=3, **kw)
        for i in range(600):
            g.press(script(i))
            p = g.tick()
            panels = [p] if mode == "human_vs_ai" else list(p["seats"].values())
            for panel in panels:
                for d in panel["draw"]:
                    if "img" not in d:
                        continue
                    seen.add(d["img"])
                    assert d["img"] in sheets, d["img"]
                    sx, sy, sw, sh = d["src"]
                    w, h = sizes[d["img"]]
                    assert sw > 0 and sh > 0 and d["w"] > 0 and d["h"] > 0, d
                    assert 0 <= sx and sx + sw <= w and 0 <= sy and sy + sh <= h, (d, (w, h))
    assert {"tiles", "rival", "guard"} <= {s.split("/")[0] for s in seen}


def test_page_files_the_js_fetches_exist_in_the_build(dist):
    out, _ = dist
    html = (out / "index.html").read_text()
    for src in re.findall(r'<script src="([^"]+)"', html):
        if not src.startswith("http"):
            assert (out / src).is_file(), src
    main = (ROOT / "web" / "main.js").read_text()
    for name in re.findall(r'fetch\("([^"]+)"\)', main):
        assert (out / name).is_file(), name
    assert 'load.image(s, "art/" + s + ".png")' in main


def test_build_is_independent_of_the_working_directory(dist, tmp_path):
    out, manifest = dist
    other = tmp_path / "o"
    subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "web" / "build.py"), "--out", str(other)],
                   cwd=tmp_path, check=True, capture_output=True, text=True, timeout=120)
    assert json.loads((other / "manifest.json").read_text()) == manifest


# --- workflows -------------------------------------------------------------------------
yaml = pytest.importorskip("yaml")


def load_wf(name):
    wf = yaml.safe_load((ROOT / ".github" / "workflows" / name).read_text())
    wf["on"] = wf.get("on", wf.get(True))        # PyYAML reads the key `on` as True
    return wf


@pytest.mark.parametrize("name", ["pages.yml", "web-smoke.yml"])
def test_workflow_is_least_privilege_and_has_no_secrets(name):
    text = (ROOT / ".github" / "workflows" / name).read_text()
    wf = load_wf(name)
    assert wf["permissions"] == {"contents": "read"}
    assert "${{ secrets." not in text and "GITHUB_TOKEN" not in text
    for job in wf["jobs"].values():
        extra = job.get("permissions", {})
        assert set(extra) <= {"pages", "id-token"}, extra
        for step in job["steps"]:
            if "uses" in step:
                assert re.fullmatch(r"[\w./-]+@v\d+", step["uses"]), step["uses"]


def test_pages_deploys_only_from_main_and_smoke_runs_on_pull_requests():
    pages, smoke = load_wf("pages.yml"), load_wf("web-smoke.yml")
    assert pages["on"]["push"]["branches"] == ["main"] and "pull_request" not in pages["on"]
    assert "pull_request" in smoke["on"]
    deploy = pages["jobs"]["deploy"]
    assert deploy["needs"] == "build" and deploy["permissions"] == {"pages": "write", "id-token": "write"}
    assert "pages" not in pages["jobs"]["build"].get("permissions", {})


def test_smoke_script_asserts_frames_errors_and_a_ready_page():
    s = (ROOT / "tools" / "web" / "smoke.cjs").read_text()
    for needle in ('data-state="ready"', "pageerror", "m.type() === \"error\"", "process.exit(1)"):
        assert needle in s, needle


def test_smoke_script_checks_that_a_key_changes_the_game():
    s = (ROOT / "tools" / "web" / "smoke.cjs").read_text()
    assert re.search(r"(hud|textContent\(\"#hud\"\)|screenshot.*compare|pixel)", s.split("keyboard.down")[1]), \
        "no assertion after the key press other than the frame counter"


# --- docs ------------------------------------------------------------------------------
def test_web_build_md_commands_work_as_written(dist, tmp_path):
    md = (ROOT / "docs" / "final" / "WEB_BUILD.md").read_text()
    assert "python3 tools/web/build.py" in md
    assert "cd web/dist && python3 -m http.server 8000" in md
    assert (ROOT / "tools" / "web" / "build.py").is_file()
    out, _ = dist
    for mode_url in ("?mode=ai", "?mode=local", "&rival=random", "&seat=B", "&seed=N"):
        assert mode_url in md
    # The documented query options are the ones keys.js parses.
    js = (ROOT / "web" / "keys.js").read_text()
    for opt in ("mode", "seat", "seed", "rival"):
        assert f'q.get("{opt}")' in js
