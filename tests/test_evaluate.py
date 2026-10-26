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
