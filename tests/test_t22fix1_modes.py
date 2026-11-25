"""T22-fix1: EVAL-T22-1 (WAIT is submitted), EVAL-T22-2 (reset clears the log), EVAL-T22-3
(one weights load per process), QA-T22-1 (help text from the list). Written before the fixes.
Headless; no network, no training.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from agents import modes                      # noqa: E402
from agents.rl import policy                  # noqa: E402
from server import modes as smodes            # noqa: E402
from server.match import TICK_S               # noqa: E402
from server.trace import replay               # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


class Scripted:
    """A controller that answers from a list, one answer per decision."""
    name, kind = "scripted", "test"

    def __init__(self, answers):
        self.answers, self.i = list(answers), 0

    def reset(self, seed):
        self.i = 0

    def decide(self, observation, legal):
        a = self.answers[min(self.i, len(self.answers) - 1)]
        self.i += 1
        if isinstance(a, Exception):
            raise a
        return a


def _rival(answers):
    return modes._rival_class()(Scripted(answers), "baseline")


def _ticks(r, n, legal=("RIGHT", "WAIT")):
    return [r({}, list(legal)) for _ in range(n)]


# --- EVAL-T22-1 -------------------------------------------------------------------------
def test_a_wait_answer_is_submitted_on_the_decision_tick_and_none_between():
    r = _rival(["WAIT", "RIGHT", "WAIT"])
    r.reset(0)
    out = _ticks(r, 18)
    assert out[0] == "WAIT" and out[6] == "RIGHT" and out[12] == "WAIT"
    assert all(o is None for i, o in enumerate(out) if i % 6)
    assert r.fallback_log == []


@pytest.mark.parametrize("bad", [RuntimeError("boom"), "NOT_AN_ACTION", 7, None])
def test_a_failed_or_illegal_answer_stays_no_input_and_a_labelled_fallback(bad):
    r = _rival([bad, "RIGHT"])
    r.reset(0)
    out = _ticks(r, 7)
    assert out[0] is None and out[6] == "RIGHT"
    assert len(r.fallback_log) == 1
    e = r.fallback_log[0]
    assert e["source"] == "fallback" and e["seat"] == "B"


def test_a_wait_the_policy_chose_is_not_a_fallback():
    r = _rival(["WAIT"])
    r.reset(0)
    _ticks(r, 13)
    assert r.fallback_log == [] and r.fallbacks == 0


# --- replay of a trace that holds WAIT inputs ----------------------------------------------
def test_a_server_trace_with_wait_inputs_replays_to_the_same_snapshot():
    m = smodes.make_match("ai", seed=3)
    m.join(None, 0.0)
    now = 0.0
    for _ in range(360):
        now += TICK_S
        m.advance(now)
    tr = m.trace()
    waits = [x for t in tr["ticks"] for x in t if x[0] == "B" and x[1] == "WAIT"]
    assert waits, "the AI seat never submitted WAIT: the replay check would be vacuous"
    outcome, h = replay(json.loads(json.dumps(tr)))
    assert h == tr["state_hash"] and outcome == tr["outcome"]


# --- EVAL-T22-2 ---------------------------------------------------------------------------
def test_reset_clears_the_fallback_log():
    r = _rival([RuntimeError("x")])
    r.reset(0)
    _ticks(r, 1)
    assert r.fallback_log
    r.reset(1)
    assert r.fallback_log == []


def test_the_hosted_page_logs_fallbacks_to_the_console_never_the_other_seat():
    main = (ROOT / "web" / "main.js").read_text()
    assert "fallback_log" in main and "console." in main
    for name in ("web/bridge.py", "web/draw.js"):
        assert "fallback_log" not in (ROOT / name).read_text()
    assert "fallback_log" not in json.dumps(
        __import__("web.bridge", fromlist=["x"]).make_game("human_vs_ai", "A", 1, "ai", honest=True).payload())


# --- EVAL-T22-3 ---------------------------------------------------------------------------
def test_the_network_is_loaded_and_hash_checked_once_per_process(monkeypatch):
    calls = []
    real = policy.load_net

    def spy(path, sha256):
        calls.append(path)
        return real(path, sha256)
    monkeypatch.setattr(policy, "load_net", spy)
    modes._NET_CACHE.clear()
    a = modes.make_controller("ai")
    b = modes.make_seat_rival("ai")
    c = modes.make_controller("ai")
    assert len(calls) == 1
    assert a is not b.controller and a is not c            # one controller (and its state) per room
    assert a.policy_macro.net is c.policy_macro.net        # the immutable network is shared


def test_the_cache_does_not_let_a_wrong_hash_through(monkeypatch):
    modes.make_controller("ai")                            # warm the cache with the right hash
    with pytest.raises(policy.WeightsError):
        modes.make_controller("ai", sha256="0" * 64)


# --- QA-T22-1 -----------------------------------------------------------------------------
def test_the_mode_help_is_built_from_the_list():
    out = subprocess.run([sys.executable, str(ROOT / "play.py"), "--help"], capture_output=True,
                         text=True, cwd=ROOT, timeout=60)
    assert out.returncode == 0
    text = " ".join(out.stdout.split())
    for m in modes.MODES:
        assert f"{m.id} = {m.label}" in text
