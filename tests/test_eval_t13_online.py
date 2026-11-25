"""T13 Gate 2 (evaluation specialist): server-to-client knowledge boundary probes.

Localhost only, injected clocks, no network beyond 127.0.0.1. Tests marked
xfail(strict=True) reproduce a finding; whoever fixes it removes the mark.
"""

from __future__ import annotations

import json

import pytest

from server.match import FORFEIT_GRACE_S, TICK_S, Match
from server.trace import replay


def run_ticks(m: Match, n: int, now: float) -> float:
    for _ in range(n):
        now += TICK_S
        m.advance(now)
    return now


class Spy:
    """Controller that records exactly what the server's AI seat is given."""
    name, kind = "spy", "scripted"

    def __init__(self, fail=False):
        self.calls, self.fail = [], fail

    def reset(self, seed):
        pass

    def decide(self, obs, legal):
        self.calls.append((json.dumps(obs, sort_keys=True), tuple(legal)))
        if self.fail:
            raise RuntimeError("boom")
        return "WAIT"


def ai_match(controller, seed=0):
    m = Match(seed=seed, rival="baseline", rival_budget_s=1.0)
    m.game.rival.inner.controller = controller
    return m


def test_ai_seat_receives_only_its_own_observation_and_legal_list():
    spy = Spy()
    m = ai_match(spy)
    m.join(None, 0.0)
    run_ticks(m, 60, 0.0)
    assert spy.calls
    obs0 = json.loads(spy.calls[0][0])
    assert set(obs0) == set(m.episode.observe("B"))
    text = "\n".join(c[0] for c in spy.calls)
    assert '"seed"' not in text and "GameState" not in text and "token" not in text
    assert all(isinstance(c[1], tuple) and all(isinstance(a, str) for a in c[1]) for c in spy.calls)


def test_fallbacks_of_a_second_duel_are_logged_and_not_mixed_with_the_first():
    spy = Spy(fail=True)
    m = ai_match(spy)
    m.join(None, 0.0)
    now = run_ticks(m, 120, 0.0)                  # about 20 failed decisions
    first = len(m._fallbacks)
    assert first >= 10
    m.state = "ended"
    m._press_rematch("A", now)
    assert m.state == "playing"
    now = run_ticks(m, 60, now)                   # about 10 failed decisions in duel 2
    new = len(m._fallbacks) - first
    assert new == 10, f"duel 2 logged {new} of 10 fallbacks"
    assert len(m.trace()["fallbacks"]) == new, "trace of duel 2 carries duel 1's fallbacks"


@pytest.mark.parametrize("ai", [False, True])
def test_a_trace_after_a_rematch_replays_to_the_same_outcome_and_hash(ai):
    m = Match(seed=3, rival="baseline" if ai else None, rival_budget_s=1.0)
    m.join(None, 0.0)
    if not ai:
        m.join(None, 0.0)
    m.receive("A", json.dumps({"type": "keys", "keys": ["d"]}), 0.0)
    now = run_ticks(m, 80, 0.0)
    m.state = "ended"
    m.rematch_pressed = set() if ai else {"B"}
    m._press_rematch("A", now)
    assert m.state == "playing"
    m.receive("A", json.dumps({"type": "keys", "keys": ["a"]}), now)
    run_ticks(m, 80, now)
    tr = m.trace()
    outcome, h = replay(tr)
    assert h == tr["state_hash"] and outcome == tr["outcome"]


def test_pause_messages_to_the_watching_seat_are_the_same_for_every_hidden_state():
    def run(hidden):
        m = Match(seed=1)
        m.join(None, 0.0)
        m.join(None, 0.0)
        if hidden:
            m.episode._duel.rivals["B"].disguised = True
            m.episode.step("B", "RIG")
        now = run_ticks(m, 5, 0.0)
        m.drain("A")
        m.connection_lost("B", now)
        out = m.drain("A")
        run_ticks(m, 30, now + FORFEIT_GRACE_S - 1)
        return json.dumps(out + m.drain("A"), sort_keys=True)
    assert run(False) == run(True)
