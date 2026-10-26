"""evaluate.py guards and outputs (no network)."""

import json

import pytest

import evaluate


def test_model_players_require_live_flag(tmp_path):
    with pytest.raises(SystemExit):
        evaluate.main(["--suite", "tuning", "--players", "model-history", "--out", str(tmp_path)])


def test_held_out_cases_are_not_in_the_tuning_suite(tmp_path):
    with pytest.raises(SystemExit):
        evaluate.main(["--suite", "tuning", "--situations", "H1", "--out", str(tmp_path)])


def test_baseline_tuning_run_writes_traces_results_and_table(tmp_path):
    assert evaluate.main(["--suite", "tuning", "--players", "baseline", "--out", str(tmp_path)]) == 0
    results = json.loads(next(tmp_path.glob("*-results.json")).read_text())
    assert len(results["episodes"]) == 6                      # S1-S3 x seeds 0, 1
    assert all(e["outcome"]["reason"] == "won" for e in results["episodes"])
    assert len(list(tmp_path.glob("*-baseline-S*-*.jsonl"))) == 6
    assert "| baseline-explorer | S3 |" in next(tmp_path.glob("*-table.md")).read_text()


# tools/smoke_provider.py: the one-call provider check (no network here)

def test_smoke_tool_needs_live_and_a_key_and_sends_one_request(monkeypatch, tmp_path):
    import sys
    sys.path.insert(0, "tools")
    import smoke_provider
    from agents.providers import FakeProvider

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(SystemExit) as exc:
        smoke_provider.main(["--live"])
    assert exc.value.code == 2                                   # stops before any request
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-FAKE-not-real")
    assert smoke_provider.main(["--check-only"]) == 0
    with pytest.raises(SystemExit):
        smoke_provider.main([])                                  # paid call needs --live
    fake = FakeProvider(["OK"], model="claude-haiku-4-5", tokens=(14, 1))
    assert smoke_provider.main(["--live", "--out", str(tmp_path)], provider=fake) == 0
    assert fake.calls == 1
    rec = json.loads(next(tmp_path.glob("*-provider-smoke.json")).read_text())
    assert rec["ok"] and rec["tokens_in"] == 14 and rec["cost_usd"] == 0.000019
    assert "FAKE" not in json.dumps(rec)
