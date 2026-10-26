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

import pytest

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


# ---------------------------------------------------------------------------
# First live attempt, 2026-10-26 (traces/live/20261026T162629Z-model-history-S1-0.jsonl):
# all 40 calls failed with the same SDK error and nothing reached the API.

SDK_NO_KEY = ('Could not resolve authentication method. Expected one of api_key, auth_token, '
              'or credentials to be set. Or for one of the `X-Api-Key` or `Authorization` '
              'headers to be explicitly omitted')
LIVE_S1 = ["--suite", "tuning", "--players", "model-history", "--situations", "S1",
           "--seeds", "0", "--live"]


@pytest.mark.parametrize("value", [None, ""])
def test_regression_missing_api_key_became_40_fallback_waits(value, monkeypatch, tmp_path):
    """Observed 2026-10-26 16:26 UTC: `evaluate.py --live` ran S1 with
    ANTHROPIC_API_KEY unset or empty in the Python process. The SDK client was
    built anyway, and every `messages.create` raised `TypeError: Could not
    resolve authentication method` before any HTTP request. The runner logged
    40 failed calls, 40 WAIT fallbacks and 0 tokens, which looks like an episode.
    Fix: check the credential before any episode starts. A missing or blank
    key stops the run with an error, so no trace is written and no call is counted."""
    if value is None:
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    else:
        monkeypatch.setenv("ANTHROPIC_API_KEY", value)
    with pytest.raises(SystemExit) as exc:
        evaluate.main(LIVE_S1 + ["--out", str(tmp_path)])
    assert exc.value.code == 2
    assert list(tmp_path.glob("*.jsonl")) == []


def test_blank_or_padded_key_is_rejected_without_revealing_it(monkeypatch):
    from agents.providers import ProviderConfigError, check_credentials
    for bad in ["   ", "\n", " sk-ant-FAKE-padded\n"]:
        monkeypatch.setenv("ANTHROPIC_API_KEY", bad)
        with pytest.raises(ProviderConfigError) as exc:
            check_credentials("anthropic")
        assert "FAKE" not in str(exc.value)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-FAKE-well-formed")
    check_credentials("anthropic")                           # no error, no network


def test_regression_failed_calls_had_no_error_category():
    """Same live attempt: each failed step stored only the raw SDK message, so
    the cause had to be read off 40 identical strings. Fix: every failed step
    has a safe `error_kind`, and the episode header counts them."""
    fake = FakeProvider([TypeError(SDK_NO_KEY)])
    res = run_episode(ModelPlayer(fake), "S1", seed=0, limits=Limits(max_calls=3))
    assert [r["error_kind"] for r in res["trace"]] == ["auth_missing"] * 3
    assert res["failed_call_kinds"] == {"auth_missing": 3}


class _StatusError(Exception):
    def __init__(self, status_code, message="api error"):
        super().__init__(message)
        self.status_code = status_code


class APITimeoutError(Exception):       # same class name as the SDK's
    pass


def test_failed_call_kinds_cover_provider_errors_timeouts_and_bad_replies():
    from agents.providers import classify_error
    cases = {401: "auth_rejected", 403: "permission_denied", 404: "model_not_found",
             400: "bad_request", 429: "rate_limited", 529: "overloaded", 500: "server_error"}
    for status, kind in cases.items():
        assert classify_error(_StatusError(status)) == kind
    assert classify_error(APITimeoutError("t")) == "provider_timeout"
    assert classify_error(RuntimeError("?")) == "other"
    fake = FakeProvider(["no json here", _StatusError(529)])
    res = run_episode(ModelPlayer(fake), "S1", seed=0, limits=Limits(max_calls=2))
    assert [r["error_kind"] for r in res["trace"]] == ["unparseable_reply", "overloaded"]
    ok = run_episode(ModelPlayer(FakeProvider([json.dumps({"action": "WAIT"})])), "S1", seed=0,
                     limits=Limits(max_calls=1))
    assert ok["trace"][0]["error_kind"] is None and ok["failed_call_kinds"] == {}


def test_error_text_in_traces_never_contains_a_key():
    leaked = "sk-ant-api03-" + "A1b2" * 20
    fake = FakeProvider([RuntimeError(f"bad header x-api-key: {leaked}")])
    res = run_episode(ModelPlayer(fake), "S1", seed=0, limits=Limits(max_calls=1))
    assert leaked not in json.dumps(res)
    assert "[redacted]" in res["trace"][0]["error"]


def test_regression_wall_side_face_hid_a_one_cell_pit():
    """Student playtest, session 06 (S3 room 2, original art): a wall's shaded
    side face was drawn 25 px into the next cell and covered most of the
    one-cell spike pit at x 64-96, so the kid seemed to fall into the wall.

    Every piece must sit in its own cell's column, except the floor
    surface's right-hand part (perspective; its front edge stays on the cell
    boundary). Checked on the layout plan, so no pygame or images needed."""
    from pop.situations import SITUATIONS
    from render.layout import OVERHANG, room_pieces

    for sit in SITUATIONS.values():
        for room, rows in sit.rooms.items():
            ctx = dict(room=f"{sit.id}:{room}", tick=1, gates={}, exits={},
                       sprung={(r, c) for r in range(3) for c in range(10)},
                       shaking=set(), pressed=set())
            for pc in room_pieces(list(rows), ctx):
                r, c = pc.cell
                col = pc.x // 32
                if pc.name in OVERHANG:
                    assert col == c + 1, (sit.id, room, pc)
                    assert rows[r][col] != "#", (sit.id, room, pc)   # never over a wall
                else:
                    assert col == c, (sit.id, room, pc)
            # A pit cell is drawn only by its own pieces and the floor overhang.
            for r, line in enumerate(rows):
                for c, t in enumerate(line):
                    if t == "." and c > 0 and line[c - 1] == "#":
                        inside = [pc for pc in room_pieces(list(rows), ctx)
                                  if pc.x // 32 == c and pc.cell[0] == r]
                        assert all(pc.cell == (r, c) or pc.name in OVERHANG
                                   for pc in inside), (sit.id, room, r, c)


def test_regression_loose_ledge_fell_during_climb_crashed():
    """Observed 2026-10-26 (session 08, a search over S3's legal actions): the
    kid hangs from a loose floor, presses UP, and the floor falls during the
    8-frame climb. `Game._up` then called `_enter(None)` and `Episode.step`
    raised TypeError, which would have crashed an evaluation run. Fix: if the
    ledge falls during the climb, the kid simply falls (R-C14)."""
    from pop.interface import Episode
    ep = Episode("S3")
    ep.reset(0)
    for a in ("RUN_JUMP_RIGHT", "WAIT", "RIGHT", "JUMP_RIGHT", "RUN_JUMP_RIGHT", "DOWN"):
        assert ep.step("kid", a)["accepted"]
    assert ep.observe("kid")["kid"]["posture"] == "hanging"
    result = ep.step("kid", "UP")                    # raised TypeError before the fix
    assert result["accepted"]
    assert result["effect"] in ("fell", "landed", "hurt", "died")
    assert result["effect"] != "climbed"
    kid = ep.observe("kid")["kid"]
    assert kid["row"] == 2                           # below the fallen ledge, not on it
    while ep.outcome()["status"] != "terminal" and ep.observe("kid")["kid"]["posture"] == "falling":
        ep.step("kid", "WAIT")
    assert ep.observe("kid")["kid"]["posture"] in ("standing", "dead")


def test_regression_kid_hung_from_a_loose_floor_that_had_fallen():
    """Observed 2026-10-26 (session 08, same search as above): standing on a
    loose floor in S3, the kid starts climbing down (DOWN, 6 frames) and the
    floor falls meanwhile. The macro still finished as "hanging", from a cell
    that was now empty air. Fix: if he is already falling, the climb-down
    stops and he falls (R-C14)."""
    from pop.interface import Episode
    ep = Episode("S3")
    ep.reset(0)
    for a in ("RUN_JUMP_RIGHT", "WAIT", "RIGHT", "JUMP_RIGHT", "RUN_JUMP_RIGHT", "WAIT"):
        assert ep.step("kid", a)["accepted"]
    result = ep.step("kid", "DOWN")
    assert result["effect"] != "hanging"             # was "hanging" before the fix
    assert ep.observe("kid")["kid"]["posture"] != "hanging"
