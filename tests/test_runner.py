"""Runner limits (3b): calls, failed calls, timeouts, fallbacks, traces."""

import time

from pop.runner import Decision, Limits, ScriptedPlayer, run_episode, save_trace
from solutions import SOLUTIONS


class FakeModel:
    name = "fake-model"
    source = "model"
    uses_model = True

    def __init__(self, behavior):
        self.behavior = behavior
        self.calls = 0

    def decide(self, observation, legal_actions):
        self.calls += 1
        return self.behavior(self, observation, legal_actions)


def test_scripted_route_wins_the_escape_trial_through_the_runner():
    res = run_episode(ScriptedPlayer(SOLUTIONS["S3"]), "S3", seed=100)
    assert res["outcome"]["reason"] == "won"
    assert all(r["source"] == "scripted" and r["accepted"] for r in res["trace"])
    assert res["model_calls"] == 0


def test_step_limit_through_runner():
    res = run_episode(ScriptedPlayer([]), "S1", seed=0)          # WAITs forever
    assert res["outcome"]["reason"] == "step_limit"
    assert res["outcome"]["actions"] == 40


def test_call_limit_counts_every_call():
    model = FakeModel(lambda self, o, la: Decision("WAIT", {"tokens_in": 1}))
    res = run_episode(model, "S1", seed=0, limits=Limits(max_calls=3))
    assert res["outcome"]["reason"] == "call_limit"
    assert res["model_calls"] == 3 and model.calls == 3


def test_failed_calls_count_and_fallbacks_are_labeled():
    def boom(self, o, la):
        raise RuntimeError("provider down")
    res = run_episode(FakeModel(boom), "S1", seed=0, limits=Limits(max_calls=4))
    assert res["outcome"]["reason"] == "call_limit"
    assert res["model_calls"] == 4 and res["failed_calls"] == 4 and res["fallbacks"] == 4
    assert all(r["source"] == "fallback" and r["action"] == "WAIT" for r in res["trace"])
    assert "provider down" in res["trace"][0]["error"]


def test_timeout_produces_labeled_fallback():
    def slow(self, o, la):
        time.sleep(0.5)
        return "RIGHT"
    res = run_episode(FakeModel(slow), "S1", seed=0,
                      limits=Limits(max_calls=2, call_timeout_s=0.05))
    assert res["failed_calls"] == 2
    assert [r["error"] for r in res["trace"]] == ["timeout", "timeout"]
    assert all(r["source"] == "fallback" for r in res["trace"])


def test_model_decisions_are_labeled_model_and_fallbacks_never_are():
    def flaky(self, o, la):
        if self.calls % 2 == 0:
            raise RuntimeError("bad")
        return "WAIT"
    res = run_episode(FakeModel(flaky), "S1", seed=0, limits=Limits(max_calls=6))
    sources = [r["source"] for r in res["trace"]]
    assert sources == ["model", "fallback"] * 3
    assert res["failed_calls"] == 3


def test_invalid_model_actions_hit_the_invalid_limit():
    res = run_episode(FakeModel(lambda s, o, la: "FLY"), "S1", seed=0)
    assert res["outcome"]["reason"] == "invalid_limit"
    assert res["outcome"]["frames"] == 0
    assert all(not r["accepted"] for r in res["trace"])


def test_player_gets_copies_not_the_episode_state():
    def vandal(self, o, la):
        o["kid"]["hp"] = 99
        o["tiles"][1] = "EEEEEEEEEE"
        la.clear()
        return "WAIT"
    res = run_episode(FakeModel(vandal), "S1", seed=0, limits=Limits(max_calls=2))
    assert res["trace"][-1]["kid"]["hp"] == 3


def test_trace_file_round_trip(tmp_path):
    import json
    res = run_episode(ScriptedPlayer(SOLUTIONS["S1"]), "S1", seed=0)
    path = tmp_path / "t.jsonl"
    save_trace(res, path)
    lines = [json.loads(x) for x in path.read_text().splitlines()]
    assert lines[0]["type"] == "episode" and lines[0]["outcome"]["reason"] == "won"
    assert len(lines) == 1 + len(res["trace"])


def test_unparseable_reply_is_a_labeled_fallback_that_keeps_its_metadata():
    """R-D22: a reply with no usable action is a failed call; its tokens stay."""
    def garbled(self, o, la):
        return Decision(None, {"tokens_in": 100, "tokens_out": 7, "cost_usd": 0.001,
                               "raw": "I think I will go right!"},
                        fallback_reason="unparseable reply")
    res = run_episode(FakeModel(garbled), "S1", seed=0, limits=Limits(max_calls=2))
    assert res["fallbacks"] == 2 and res["failed_calls"] == 2
    step = res["trace"][0]
    assert step["source"] == "fallback" and step["action"] == "WAIT" and step["accepted"]
    assert step["error"] == "unparseable reply"
    assert step["meta"]["raw"] == "I think I will go right!"
    assert res["usage"] == {"tokens_in": 200, "tokens_out": 14, "cost_usd": 0.002}


def test_parseable_but_illegal_model_action_is_submitted_and_counted_invalid():
    """R-D22: only unparseable replies fall back; illegal choices are the model's."""
    res = run_episode(FakeModel(lambda s, o, la: Decision("FLY", {"tokens_in": 1})),
                      "S1", seed=0, limits=Limits(max_calls=2))
    assert res["fallbacks"] == 0
    assert [r["source"] for r in res["trace"]] == ["model", "model"]
    assert res["outcome"]["invalid_actions"] == 2


def test_runner_reports_latency_summary():
    res = run_episode(ScriptedPlayer(SOLUTIONS["S1"]), "S1", seed=0)
    assert set(res["latency_ms"]) == {"mean", "max"}
    assert res["usage"] == {"tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0}
