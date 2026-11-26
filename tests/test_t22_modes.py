"""T22: one mode list (AI Model, Baseline, Human vs Human), the shipped PPO rival by hash,
honest labels (#88), the AI seat's boundary, the web bridge and the build.

Decisions #87 to #90, #3, #24, #45, #49, #55. No network, no keys, no browser.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import zipfile
from pathlib import Path

import pytest

from agents import modes
from agents.rl import policy
from pop.versus import arena_episode

ROOT = Path(__file__).resolve().parent.parent
AI_LABEL, BASE_LABEL, HUMAN_LABEL = "AI Model (trained)", "Baseline (scripted)", "Human vs Human"


# --- the one list --------------------------------------------------------------------
def test_there_are_exactly_three_modes_with_the_agreed_labels():
    assert modes.MODE_IDS == ("ai", "baseline", "human")
    assert [m.label for m in modes.MODES] == [AI_LABEL, BASE_LABEL, HUMAN_LABEL]
    assert modes.label("ai") == AI_LABEL and modes.label("baseline") == BASE_LABEL
    assert [m.ai for m in modes.MODES] == [True, True, False]
    with pytest.raises(modes.ModeError):
        modes.label("model")


def test_pop_never_imports_the_mode_list():
    for p in (ROOT / "pop").glob("*.py"):
        assert "agents.modes" not in p.read_text(), p


# --- the shipped weights, by hash ----------------------------------------------------------
def test_ai_mode_loads_the_shipped_weights_by_hash():
    c = modes.make_controller("ai")
    assert c.kind == "policy" and c.name == f"ppo-{policy.SHIPPED_SHA256[:8]}"
    assert hashlib.sha256(Path(policy.SHIPPED_WEIGHTS).read_bytes()).hexdigest() == policy.SHIPPED_SHA256


def test_ai_mode_refuses_a_wrong_hash_and_does_not_fall_back_to_the_baseline(monkeypatch):
    with pytest.raises(policy.WeightsError, match="hash"):
        modes.make_controller("ai", sha256="0" * 64)
    monkeypatch.setattr(policy, "SHIPPED_SHA256", "f" * 64)
    with pytest.raises(policy.WeightsError, match="hash"):
        modes.make_controller("ai")
    with pytest.raises(policy.WeightsError, match="hash"):
        modes.make_seat_rival("ai")
    with pytest.raises(policy.WeightsError):
        modes.verify_shipped()


def test_ai_mode_refuses_missing_weights_with_a_clear_error(tmp_path):
    with pytest.raises(policy.WeightsError, match="missing"):
        modes.make_controller("ai", weights=tmp_path / "nope.json")


def test_baseline_mode_is_the_scripted_baseline_and_human_has_no_controller():
    c = modes.make_controller("baseline")
    assert c.kind == "scripted"
    with pytest.raises(modes.ModeError):
        modes.make_controller("human")


# --- the AI seat's boundary (every AI mode) ------------------------------------------------
class Spy:
    """Wraps a controller; checks every call is exactly seat B's own observation and legal list."""

    def __init__(self, inner, ep):
        self.inner, self.ep, self.calls = inner, ep, []
        self.name, self.kind = inner.name, inner.kind

    def reset(self, seed):
        self.inner.reset(seed)

    def decide(self, obs, legal):
        assert obs == self.ep.observe("B"), "the AI seat got something other than its own observation"
        assert tuple(legal) == tuple(self.ep.legal_actions("B"))
        assert isinstance(legal, tuple)
        self.calls.append((copy.deepcopy(obs), tuple(legal)))
        return self.inner.decide(obs, legal)


@pytest.mark.parametrize("mode", ["ai", "baseline"])
def test_the_ai_seat_sees_only_its_own_observation_and_legal_actions(mode):
    ep = arena_episode(5)
    rival = modes.make_seat_rival(mode)
    rival.controller = Spy(rival.controller, ep)
    rival.reset(5)
    for t in range(180):
        modes.step_ai_seat(ep, rival)
        ep.step("A", "WAIT") if t % 3 == 0 else None
        ep.tick()
    assert rival.controller.calls
    for obs, _ in rival.controller.calls:
        text = json.dumps(obs)
        assert "seed" not in obs and "owner" not in text and "token" not in text
        assert set(obs) <= set(ep.observe("B"))


def test_a_failed_answer_is_a_labelled_fallback_with_no_input():
    ep = arena_episode(1)
    rival = modes.make_seat_rival("baseline")

    def boom(obs, legal):
        raise RuntimeError("x")
    rival.controller.decide = boom
    assert modes.step_ai_seat(ep, rival) is None
    assert rival.fallback_log and all(f["source"] == "fallback" and f["seat"] == "B"
                                      for f in rival.fallback_log)


def test_a_policy_error_is_a_labelled_fallback_too():
    ep = arena_episode(1)
    rival = modes.make_seat_rival("ai")

    def boom(obs):
        raise RuntimeError("x")
    rival.controller.policy_macro.encoder.update = boom
    modes.step_ai_seat(ep, rival)
    assert rival.policy_errors == 1
    assert rival.fallback_log[-1]["source"] == "fallback"
    assert rival.fallback_log[-1]["reason"] == "policy_error"


# --- deterministic duel with scripted human input ---------------------------------------------
def _duel(mode, seed, script):
    from server.trace import state_hash
    ep = arena_episode(seed)
    rival = modes.make_seat_rival(mode)
    rival.reset(seed)
    for i in range(240):
        act = script[i % len(script)]
        if act in ep.legal_actions("A"):
            ep.step("A", act)
        modes.step_ai_seat(ep, rival)
        ep.tick()
    return state_hash(ep), ep.outcome()["inputs"]


@pytest.mark.parametrize("mode", ["ai", "baseline"])
def test_an_ai_duel_with_scripted_input_is_reproducible(mode):
    script = ["RIGHT", "RIGHT", "WAIT", "LEFT", "STEP_RIGHT", "WAIT", "DRAW", "LUNGE"]
    a, b = _duel(mode, 7, script), _duel(mode, 7, script)
    assert a == b and a[1]["B"] > 0


# --- the web bridge -------------------------------------------------------------------------
def test_the_bridge_picks_the_controller_and_the_honest_label_per_mode():
    from web.bridge import make_game
    g = make_game("human_vs_ai", "A", 0, "ai")
    assert g.tick()["rival"] == AI_LABEL
    assert g.rival.controller.kind == "policy"
    b = make_game("human_vs_ai", "A", 0, "baseline", honest=True)
    assert b.tick()["rival"] == BASE_LABEL and b.rival.controller.kind == "scripted"
    assert make_game("human_vs_ai", "A", 0, "ai", neutral=True).tick()["rival"] == "Rival"
    assert "fallback" not in json.dumps(g.tick()).lower()


def test_the_legacy_baseline_label_is_unchanged_without_honest():
    from web.bridge import make_game
    assert "AI rival" in make_game("human_vs_ai", "A", 0, "baseline").tick()["rival"]


def test_the_bridge_refuses_a_wrong_hash(monkeypatch):
    from web.bridge import make_game
    monkeypatch.setattr(policy, "SHIPPED_SHA256", "e" * 64)
    with pytest.raises(policy.WeightsError):
        make_game("human_vs_ai", "A", 0, "ai")


def test_the_bridge_ai_duel_is_reproducible_and_the_payload_has_only_the_human_seat():
    from web.bridge import make_game
    from server.trace import state_hash

    def run():
        g = make_game("human_vs_ai", "A", 3, "ai")
        for i in range(120):
            g.press({"d": i % 5 != 0})
            p = g.tick()
        return state_hash(g.episode), set(p)
    assert run() == run()
    assert "seats" not in run()[1] and "seed" not in json.dumps(sorted(run()[1]))


# --- the build ------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def dist(tmp_path_factory):
    from tools.web import build
    out = tmp_path_factory.mktemp("t22-dist")
    return out, build.build(out)


def test_the_bundle_holds_the_weights_with_the_right_hash_and_the_stdlib_policy(dist):
    out, manifest = dist
    z = zipfile.ZipFile(out / "game.zip")
    names = set(z.namelist())
    assert {"agents/modes.py", "agents/rl/__init__.py", "agents/rl/encoder.py",
            "agents/rl/policy.py", "agents/rl/weights/ppo-run-1.json"} <= names
    assert hashlib.sha256(z.read("agents/rl/weights/ppo-run-1.json")).hexdigest() == policy.SHIPPED_SHA256
    assert manifest["weights_sha256"] == policy.SHIPPED_SHA256
    assert not {"agents/model_player.py", "agents/providers.py"} & names
    for n in names:
        if n.startswith("agents/") and n.endswith(".py"):
            src = z.read(n).decode()
            assert not re.search(r"^\s*(import|from)\s+(anthropic|openai|numpy|torch|pygame|requests)",
                                 src, re.M), n


def test_the_unpacked_bundle_plays_the_ai_mode_by_the_same_hash_check(dist, tmp_path):
    import subprocess
    import sys
    out, _ = dist
    zipfile.ZipFile(out / "game.zip").extractall(tmp_path)
    code = ("import sys; sys.path.insert(0, '.'); from web.bridge import make_game; "
            "g = make_game('human_vs_ai', 'A', 3, 'ai'); "
            "ps = [g.tick() for _ in range(120)]; o = g.episode.outcome(); "
            "assert o['inputs']['B'] > 0, o; assert ps[-1]['rival'] == 'AI Model (trained)'; "
            "bad = [m for m in ('pygame', 'numpy', 'anthropic') if m in sys.modules]; "
            "assert not bad, bad; "
            "from agents.rl import policy; policy.SHIPPED_SHA256 = '0' * 64; "
            "\ntry:\n    make_game('human_vs_ai', 'A', 3, 'ai')\n    raise SystemExit('no refusal')\n"
            "except policy.WeightsError:\n    print('ok')\n")
    r = subprocess.run([sys.executable, "-I", "-c", code], cwd=tmp_path, capture_output=True,
                       text=True, timeout=180)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "ok"


# --- every front end reads the one list --------------------------------------------------------
def test_the_manifest_carries_the_mode_list(dist):
    _, manifest = dist
    assert manifest["modes"] == [{"id": m.id, "label": m.label, "ai": m.ai} for m in modes.MODES]


def test_the_pages_take_their_modes_and_labels_from_the_manifest_not_their_own_text():
    for name in ("main.js", "online.js"):
        src = (ROOT / "web" / name).read_text()
        assert "manifest.modes" in src, name
        for label in (AI_LABEL, BASE_LABEL, HUMAN_LABEL):
            assert label not in src, (name, label)
    for name in ("index.html", "online.html"):
        html = (ROOT / "web" / name).read_text()
        for label in (AI_LABEL, BASE_LABEL, HUMAN_LABEL):
            assert label not in html, (name, label)


def test_the_hosted_page_links_online_play_and_the_online_page_sends_the_chosen_mode():
    assert 'href="online.html"' in (ROOT / "web" / "index.html").read_text()
    online = (ROOT / "web" / "online.js").read_text()
    assert "mode:" in online and "create: true" in online


def test_the_options_parser_reads_play_modes():
    import shutil
    import subprocess
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")

    def js(expr):
        code = f"const K = require('./web/keys.js'); console.log(JSON.stringify({expr}));"
        r = subprocess.run([node, "-e", code], capture_output=True, text=True, cwd=ROOT, timeout=30)
        assert r.returncode == 0, r.stderr
        return json.loads(r.stdout)
    ai = js('K.parseOptions("?play=ai")')
    assert (ai["mode"], ai["rival"]) == ("human_vs_ai", "ai")
    assert js('K.currentPlay(K.parseOptions("?play=ai"))') == "ai"
    bl = js('K.parseOptions("?play=baseline")')
    assert (bl["mode"], bl["rival"]) == ("human_vs_ai", "baseline")
    assert js('K.currentPlay(K.parseOptions(""))') == "baseline"
    hu = js('K.parseOptions("?play=human")')
    assert hu["mode"] == "local_two_players"
    assert js('K.currentPlay(K.parseOptions("?play=human"))') == "human"
    assert js('K.parseOptions("")')["rival"] == "baseline"       # the bare page is unchanged
    assert js('K.parseOptions("?play=zzz")')["rival"] == "baseline"
