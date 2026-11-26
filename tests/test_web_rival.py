"""T14-fix1: the AI rival plugs into the web bridge, and the page shows what a playtest log needs.

CPython only (no browser): the adapter, the page factory, the build hash, the
neutral label, the key hints and the smoke script's checks.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
NODE = shutil.which("node")

from agents.versus_baseline import make_baseline  # noqa: E402
from pop.seats import WAIT  # noqa: E402
from web.bridge import IdleRival, RandomRival, SeatControllerRival, WebGame, make_game  # noqa: E402


class Spy:
    """A controller that records what the adapter hands it."""
    name, kind = "spy", "scripted"

    def __init__(self, answers):
        self.answers, self.calls, self.resets = list(answers), [], []

    def reset(self, seed):
        self.resets.append(seed)

    def decide(self, observation, legal):
        self.calls.append((observation, legal))
        a = self.answers.pop(0) if self.answers else WAIT
        if isinstance(a, Exception):
            raise a
        return a


# --- the adapter ------------------------------------------------------------------------
def test_adapter_asks_the_controller_every_n_ticks_with_a_tuple():
    spy = Spy(["LEFT"] * 5)
    r = SeatControllerRival(spy, every=6)
    got = [r({"n": i}, ["LEFT", "WAIT"]) for i in range(13)]
    assert len(spy.calls) == 3                      # ticks 0, 6, 12
    assert all(isinstance(legal, tuple) for _, legal in spy.calls)
    assert [i for i, g in enumerate(got) if g is not None] == [0, 6, 12]


def test_adapter_maps_wait_to_no_input():
    r = SeatControllerRival(Spy([WAIT]), every=1)
    assert r({}, ["LEFT", WAIT]) is None


def test_adapter_replaces_an_illegal_or_failing_answer_and_counts_it():
    r = SeatControllerRival(Spy(["FLY", RuntimeError("boom"), 7]), every=1)
    assert [r({}, ["LEFT", WAIT]) for _ in range(3)] == [None, None, None]
    assert r.fallbacks == 3
    assert "fallback" in r.label.lower()


def test_adapter_label_names_the_controller_and_its_kind():
    r = SeatControllerRival(make_baseline())
    assert "baseline" in r.label.lower() and "scripted" in r.label.lower()
    assert "not the ai" not in r.label.lower() or "scripted" in r.label.lower()


def test_adapter_reset_resets_the_controller_and_the_cadence():
    spy = Spy([])
    r = SeatControllerRival(spy, every=6)
    for i in range(4):
        r({}, [WAIT])
    r.reset(9)
    assert spy.resets == [9]
    r({}, [WAIT])
    assert len(spy.calls) == 2                      # the first tick after reset is a decision tick


def test_adapter_rejects_a_bad_cadence():
    with pytest.raises(ValueError):
        SeatControllerRival(Spy([]), every=0)


# --- the baseline in the bridge ----------------------------------------------------------
@pytest.mark.parametrize("seat", ["A", "B"])
def test_baseline_plays_600_ticks_with_no_invalid_input(seat):
    g = WebGame(seed=3, human_seat=seat, rival=SeatControllerRival(make_baseline()))
    for _ in range(600):
        g.press({})
        g.tick()
        if g.episode.outcome()["status"] == "terminal":
            break
    o = g.episode.outcome()
    assert o["invalid_inputs"] == {"A": 0, "B": 0}
    assert o["inputs"][g.ai_seat] > 0
    assert g.rival.fallbacks == 0


def test_rematch_resets_the_baseline_and_replays_the_same_duel():
    def run(g, n=120):
        out = []
        for _ in range(n):
            g.press({})
            out.append(json.dumps(g.tick(), sort_keys=True))
        return out

    g = WebGame(seed=2, rival=SeatControllerRival(make_baseline()))
    first = run(g)
    g.rematch()
    assert run(g) == first                          # rematch keeps the seed (decision #25)


def test_the_rival_seat_sees_only_its_own_view_through_the_adapter():
    seen = []

    class Peek(Spy):
        def decide(self, observation, legal):
            seen.append(observation)
            return WAIT

    g = WebGame(seed=1, rival=SeatControllerRival(Peek([]), every=1))
    for _ in range(12):
        g.tick()
    assert seen and all("_duel" not in o and "seed" not in o for o in seen)
    assert seen[-1] == g.episode.observe("B")       # seat B's view, not A's


def test_one_controller_per_game():
    a = make_game("human_vs_ai", "A", 0, "baseline")
    b = make_game("human_vs_ai", "A", 0, "baseline")
    assert a.rival is not b.rival and a.rival.controller is not b.rival.controller


# --- the page factory ------------------------------------------------------------------
def test_make_game_default_rival_is_the_baseline():
    g = make_game("human_vs_ai", "A", 0)
    assert isinstance(g.rival, SeatControllerRival)
    assert "baseline" in g.tick()["rival"].lower()


def test_make_game_keeps_idle_and_random_as_labelled_options():
    assert isinstance(make_game("human_vs_ai", "A", 0, "idle").rival, IdleRival)
    r = make_game("human_vs_ai", "A", 0, "random").rival
    assert isinstance(r, RandomRival)
    assert "placeholder" in make_game("human_vs_ai", "A", 0, "idle").tick()["rival"].lower()


def test_unknown_rival_name_falls_back_to_the_baseline():
    assert isinstance(make_game("human_vs_ai", "A", 0, "gpt").rival, SeatControllerRival)


def test_neutral_label_says_only_rival_in_every_rival_kind():
    for kind in ("baseline", "idle", "random"):
        p = make_game("human_vs_ai", "A", 0, kind, neutral=True).tick()
        assert p["rival"] == "Rival"
    assert "baseline" not in json.dumps(make_game("human_vs_ai", "A", 0, neutral=True).tick()).lower()


def test_neutral_label_does_not_change_play():
    def stream(neutral):
        g = make_game("human_vs_ai", "A", 4, "baseline", neutral=neutral)
        out = []
        for i in range(100):
            g.press({"d": i % 9 < 5})
            p = g.tick()
            p.pop("rival")
            out.append(json.dumps(p, sort_keys=True))
        return out

    assert stream(True) == stream(False)


def test_local_two_player_mode_has_no_rival_object():
    g = make_game("local_two_players", "A", 0)
    assert "rival" not in g.tick()


# --- the build -----------------------------------------------------------------------
@pytest.fixture(scope="module")
def dist(tmp_path_factory):
    from tools.web import build as webbuild
    out = tmp_path_factory.mktemp("fix1-dist")
    return out, webbuild.build(out)


def test_archive_ships_the_baseline_and_nothing_that_needs_a_network(dist):
    out, _ = dist
    names = set(zipfile.ZipFile(out / "game.zip").namelist())
    assert {"agents/__init__.py", "agents/baseline.py", "agents/macros.py",
            "agents/versus_baseline.py"} <= names
    assert not {"agents/model_player.py", "agents/providers.py"} & names
    for n in names:
        if n.startswith("agents/"):
            src = zipfile.ZipFile(out / "game.zip").read(n).decode()
            assert not re.search(r"^\s*(import|from)\s+(anthropic|openai|numpy|pygame|requests)",
                                 src, re.M), n


def test_archive_plays_the_baseline_on_its_own(dist, tmp_path):
    out, _ = dist
    zipfile.ZipFile(out / "game.zip").extractall(tmp_path)
    code = ("import sys, json; sys.path.insert(0, '.'); from web.bridge import make_game; "
            "g = make_game('human_vs_ai', 'A', 3); "
            "[g.tick_json() for _ in range(300)]; o = g.episode.outcome(); "
            "assert o['invalid_inputs'] == {'A': 0, 'B': 0} and o['inputs']['B'] > 0, o; "
            "bad = [m for m in ('pygame', 'numpy', 'anthropic') if m in sys.modules]; "
            "assert not bad, bad; print('ok')")
    r = subprocess.run([sys.executable, "-I", "-c", code], cwd=tmp_path, capture_output=True,
                       text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "ok"


def test_manifest_has_a_short_build_hash_that_follows_the_files(dist, tmp_path):
    from tools.web import build as webbuild
    out, m = dist
    assert re.fullmatch(r"[0-9a-f]{8}", m["build"])
    assert m["build"] == webbuild.build_hash(m["files"])
    changed = dict(m["files"], **{"game.zip": "0" * 64})
    assert webbuild.build_hash(changed) != m["build"]


def test_page_has_slots_for_the_build_hash_and_the_key_hints():
    html = (ROOT / "web" / "index.html").read_text()
    assert 'id="build"' in html and 'id="keys"' in html


def test_the_page_fetches_the_rival_and_label_options_through_make_game():
    main = (ROOT / "web" / "main.js").read_text()
    assert "make_game" in main and "opts.neutral" in main and "manifest.build" in main
    assert "window.__smLast" in main


# --- the smoke script proves input reaches the engine --------------------------------------
def test_smoke_script_checks_the_position_and_the_picture_change():
    s = (ROOT / "tools" / "web" / "smoke.cjs").read_text()
    after_key = s.split("keyboard.down")[1]
    assert "__smLast" in s and "Buffer.compare" in s
    assert re.search(r"\.me\b", s) and "room" in s and "row" in s and "col" in s
    assert "errors.push" in after_key and "position" in after_key


# --- key hints and options (Node) -------------------------------------------------------------
needs_node = pytest.mark.skipif(NODE is None, reason="node not installed")


def _js(expr: str):
    code = (f"const K = require({json.dumps(str(ROOT / 'web' / 'keys.js'))}); "
            f"process.stdout.write(JSON.stringify({expr}));")
    r = subprocess.run([NODE, "-e", code], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


@needs_node
def test_key_hints_name_the_seat_actually_played():
    a, b = _js('K.keyHints("human_vs_ai", "A")'), _js('K.keyHints("human_vs_ai", "B")')
    assert "A/D" in a and "arrow" not in a.lower()
    assert "arrow" in b.lower() and "A/D" not in b
    both = _js('K.keyHints("local_two_players", "A")')
    assert "A/D" in both and "arrow" in both.lower()


@needs_node
def test_options_default_to_the_baseline_and_read_the_label():
    d = _js('K.parseOptions("")')
    assert d["rival"] == "baseline" and d["neutral"] is False
    assert _js('K.parseOptions("?rival=idle")')["rival"] == "idle"
    assert _js('K.parseOptions("?rival=random")')["rival"] == "random"
    assert _js('K.parseOptions("?rival=zzz")')["rival"] == "baseline"
    assert _js('K.parseOptions("?label=neutral")')["neutral"] is True
    assert _js('K.parseOptions("?label=other")')["neutral"] is False
