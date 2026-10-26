"""Regression tests for bugs actually observed during development."""

from pop.engine import Game
from pop.situations import Situation


def test_regression_fall_death_reported_full_hp():
    """Observed 2026-10-26 (first run of tests/test_rules.py): a kid killed by a
    3-row fall stayed at hp=3, so the observation would show a dead kid at
    full health. Fix: Game._die sets hp to 0."""
    rooms = {1: ("__________", "_.________", "_.________"),
             2: ("_.________", "__________", "##########")}
    s = Situation(id="fixture", rooms=rooms, links={1: (0, 0, 0, 2), 2: (0, 0, 1, 0)},
                  start=(1, 1, 0, +1))
    g = Game(s)
    g.perform("RIGHT")
    while g.terminal is None:
        g.perform("WAIT")
    assert g.terminal == "died:fall"
    assert g.kid.hp == 0


# ---------------------------------------------------------------------------
# Session-02 audit findings (docs/audits/AUDIT-2026-10-26-session02-agents.md)

import json
import threading

import evaluate
from agents.model_player import ModelPlayer
from agents.providers import Completion, FakeProvider
from pop.runner import Limits, run_episode


class _GatedProvider:
    """Call 1 blocks until call 2 releases it, so its reply arrives late.
    Call 2 waits for that late reply to finish, then fails. Call 3+ reply WAIT."""

    name = "fake"

    def __init__(self):
        self.prompts: list[str] = []
        self.release = threading.Event()
        self.late_done = threading.Event()

    def complete(self, system, user):
        self.prompts.append(user)
        n = len(self.prompts)
        if n == 1:
            self.release.wait(5)
            return Completion('{"action": "RUN_JUMP_RIGHT", "reason": "late"}',
                              "claude-haiku-4-5", 100, 10)
        if n == 2:
            self.release.set()
            assert self.late_done.wait(5)
            raise RuntimeError("503 overloaded")
        return Completion('{"action": "WAIT", "reason": "ok"}', "claude-haiku-4-5", 100, 10)


class _SignallingPlayer(ModelPlayer):
    def __init__(self, provider):
        super().__init__(provider)
        self._decides = 0

    def decide(self, observation, legal_actions):
        self._decides += 1
        first = self._decides == 1
        try:
            return super().decide(observation, legal_actions)
        finally:
            if first:
                self.provider.late_done.set()


def test_regression_late_reply_after_timeout_rewrote_player_memory():
    """Audit F-1 (2026-10-26, session-02 audit of e91e9b0): the runner abandons a
    decision thread on timeout but the thread keeps running. A ModelPlayer reply
    that arrived late still set the player's pending action, so the next prompt
    told the model it had played RUN_JUMP_RIGHT when the runner had submitted a
    fallback WAIT. Fix: decide() no longer writes player memory; the runner
    commits memory in its own thread, and late replies are only logged."""
    provider = _GatedProvider()
    player = _SignallingPlayer(provider)
    res = run_episode(player, "S1", seed=0, limits=Limits(max_calls=3, call_timeout_s=0.3))

    trace = res["trace"]
    assert [r["source"] for r in trace] == ["fallback", "fallback", "model"]
    assert trace[0]["error"] == "timeout"
    assert all(r["action"] != "RUN_JUMP_RIGHT" for r in trace)
    # The model's own history never shows the late action.
    assert "RUN_JUMP_RIGHT ->" not in provider.prompts[2]
    assert [s["action"] for s in player.steps] == ["WAIT (failed call)", "WAIT (failed call)"]
    # The late reply is billed, so it is logged, but not as a step.
    assert res["late_replies"] == [{"i": 0, "status": "arrived", "tokens_in": 100,
                                    "tokens_out": 10, "cost_usd": 0.00015}]
    assert res["usage"]["tokens_in"] == 200            # late call 1 + call 3


def test_regression_unknown_model_price_reported_as_free():
    """Audit F-2 (2026-10-26): a model with no entry in agents/providers.py PRICES
    was traced with cost_usd 0.0 and summed as $0.0000 in the comparison table,
    which reads as "free". Fix: unknown cost is null in the trace, the episode
    usage and the summary, and the table prints "unknown"."""
    fake = FakeProvider([json.dumps({"action": "WAIT", "reason": "x"})], model="mystery-model")
    res = run_episode(ModelPlayer(fake), "S1", seed=0, limits=Limits(max_calls=2))
    assert res["trace"][0]["meta"]["cost_usd"] is None
    assert res["trace"][0]["meta"]["cost_known"] is False
    assert res["usage"]["cost_usd"] is None
    assert res["usage"]["tokens_in"] == 100             # tokens are still counted

    header = {k: v for k, v in res.items() if k != "trace"}
    rows = evaluate.summarize([header])
    assert rows[0]["cost_usd"] is None
    assert rows[0]["player"] == "model-history"
    assert "| unknown |" in evaluate.table_md(rows)


def test_late_reply_still_pending_at_episode_end_has_unknown_cost():
    """R-D23/R-D24: an abandoned call that has not returned may still be billed,
    so the episode cost is unknown rather than $0."""
    gate = threading.Event()

    class Hung:
        name = "fake"

        def complete(self, system, user):
            gate.wait(5)
            return Completion('{"action": "WAIT"}', "claude-haiku-4-5", 10, 1)

    try:
        res = run_episode(ModelPlayer(Hung()), "S1", seed=0,
                          limits=Limits(max_calls=1, call_timeout_s=0.05))
    finally:
        gate.set()
    assert res["late_replies"] == [{"i": 0, "status": "pending", "tokens_in": 0,
                                    "tokens_out": 0, "cost_usd": None}]
    assert res["usage"]["cost_usd"] is None
