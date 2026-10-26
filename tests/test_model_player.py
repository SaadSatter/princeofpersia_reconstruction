"""Model player (rubric 2b) with a fake provider: no network, no keys."""

import json

import pytest

from agents.model_player import HISTORY_STEPS, ModelPlayer, _parse, build_system_prompt
from agents.providers import FakeProvider, estimate_cost, make_provider
from pop.runner import Limits, run_episode
from pop.situations import SITUATIONS
from solutions import SOLUTIONS


def reply(action, reason="ok"):
    return json.dumps({"action": action, "reason": reason})


def test_model_actions_are_submitted_and_traced_with_usage():
    fake = FakeProvider([reply(a) for a in SOLUTIONS["S1"]], model="claude-haiku-4-5",
                        tokens=(1000, 20))
    res = run_episode(ModelPlayer(fake), "S1", seed=0)
    assert res["outcome"]["reason"] == "won"
    assert res["model_calls"] == len(SOLUTIONS["S1"]) == fake.calls
    step = res["trace"][0]
    assert step["source"] == "model" and step["meta"]["parsed_action"] == "RIGHT"
    assert step["meta"]["model"] == "claude-haiku-4-5" and step["meta"]["cost_known"]
    assert res["usage"]["tokens_in"] == 1000 * fake.calls
    assert res["usage"]["cost_usd"] == pytest.approx(fake.calls * (1000 * 1 + 20 * 5) / 1e6)


def test_prose_reply_becomes_a_labeled_fallback():
    fake = FakeProvider(["I will run right."])
    res = run_episode(ModelPlayer(fake), "S1", seed=0, limits=Limits(max_calls=3))
    assert res["outcome"]["reason"] == "call_limit"
    assert res["fallbacks"] == 3 and res["failed_calls"] == 3
    assert all(r["source"] == "fallback" and r["action"] == "WAIT" for r in res["trace"])
    assert res["trace"][0]["meta"]["raw"] == "I will run right."


def test_provider_error_counts_as_failed_call_and_falls_back():
    fake = FakeProvider([RuntimeError("503 overloaded"), reply("WAIT")])
    res = run_episode(ModelPlayer(fake), "S1", seed=0, limits=Limits(max_calls=2))
    assert [r["source"] for r in res["trace"]] == ["fallback", "model"]
    assert res["failed_calls"] == 1 and res["model_calls"] == 2


def test_illegal_model_action_counts_invalid_not_fallback():
    fake = FakeProvider([reply("STRIKE")])
    res = run_episode(ModelPlayer(fake), "S1", seed=0)
    assert res["outcome"]["reason"] == "invalid_limit"
    assert res["fallbacks"] == 0 and res["outcome"]["invalid_actions"] == 5


def test_parser_accepts_fenced_json_and_rejects_prose():
    assert _parse('```json\n{"action": "UP", "reason": "x"}\n```') == "UP"
    assert _parse('Sure! {"action": "LEFT"}') == "LEFT"
    assert _parse("UP") is None
    assert _parse('{"action": 3}') is None


def test_history_is_bounded_and_obs_only_has_none():
    fake = FakeProvider([reply("WAIT")])
    run_episode(ModelPlayer(fake), "S1", seed=0, limits=Limits(max_calls=12))
    last = fake.prompts[-1][1]
    assert last.count("\n- WAIT ->") == HISTORY_STEPS
    fake2 = FakeProvider([reply("WAIT")])
    run_episode(ModelPlayer(fake2, variant="obs-only"), "S1", seed=0, limits=Limits(max_calls=4))
    assert "Your last" not in fake2.prompts[-1][1]


def test_prompts_reveal_no_situation_ids_links_or_routes():
    for sid in SITUATIONS:
        fake = FakeProvider([reply("RIGHT")])
        run_episode(ModelPlayer(fake), sid, seed=0, limits=Limits(max_calls=6))
        for system, user in fake.prompts:
            assert system == build_system_prompt()           # identical everywhere
            text = system + user
            assert sid not in text and "held" not in text.lower()
            assert "plate_links" not in text and "solution" not in text.lower()


def test_seen_rooms_come_only_from_rooms_already_visited():
    fake = FakeProvider([reply(a) for a in SOLUTIONS["S3"]])
    run_episode(ModelPlayer(fake), "S3", seed=0, limits=Limits(max_calls=10))
    unvisited = SITUATIONS["S3"].rooms[4]
    assert all(row not in user for _, user in fake.prompts for row in unvisited
               if row not in SITUATIONS["S3"].rooms[1] + SITUATIONS["S3"].rooms[2])


def test_cost_table_and_unknown_models():
    assert estimate_cost("claude-haiku-4-5", 1_000_000, 0) == 1.0
    assert estimate_cost("claude-haiku-4-5", 0, 1_000_000) == 5.0
    assert estimate_cost("mystery", 10, 10) is None
    with pytest.raises(ValueError):
        make_provider("nope")
