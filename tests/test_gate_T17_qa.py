"""T17 QA probes: summary keys cannot mislead a script; clean run unchanged."""

from __future__ import annotations

import json

from agents.rl.policy import file_sha256
from tools.rl import env, train
from tests.test_rl_t17_withhold import _cfg, _short, _boom


def _summary(p):
    return json.loads((p / "summary.json").read_text())


def test_failed_summary_names_a_file_that_exists_and_hash_matches_it(tmp_path, monkeypatch):
    _short(monkeypatch); _boom(monkeypatch)
    ret = train.train(_cfg(tmp_path))
    s = _summary(tmp_path)
    assert s == json.loads(json.dumps(ret))                # returned == written
    f = tmp_path / s["weights_file"]
    assert f.exists() and file_sha256(f) == s["weights_sha256"]
    assert s["weights_file"] != "weights.json" and s["weights_failed"] is True


def test_stopped_and_weights_failed_agree_on_a_failed_run(tmp_path, monkeypatch):
    _short(monkeypatch); _boom(monkeypatch)
    s = train.train(_cfg(tmp_path))
    assert (s["stopped"] == "final_check_policy_error") == s["weights_failed"]
    assert s["policy_errors"] > 0 and s["final_check_vs_baseline_tuning_pure_python"]["failed"] is True


def test_clean_run_keys_are_the_old_keys_plus_two(tmp_path, monkeypatch):
    _short(monkeypatch)
    s = train.train(_cfg(tmp_path))
    assert set(s) - {"weights_file", "weights_failed"} == {
        "commit", "seed", "updates", "episodes", "steps", "wall_seconds", "stopped", "policy_errors",
        "weights_sha256", "checkpoint_chosen_by_score", "final_check_vs_baseline_tuning_pure_python"}
    assert s["weights_failed"] is False and s["policy_errors"] == 0
    assert s["weights_sha256"] == file_sha256(tmp_path / "weights.json")


def test_final_check_disabled_still_ships_weights_json(tmp_path, monkeypatch):
    _short(monkeypatch)
    s = train.train(_cfg(tmp_path, final_eval_seeds=0))
    assert (tmp_path / "weights.json").exists() and s["weights_failed"] is False


def test_clean_rerun_after_a_failed_run_reports_weights_json(tmp_path, monkeypatch):
    _short(monkeypatch)
    with monkeypatch.context() as m:
        _boom(m)
        train.train(_cfg(tmp_path))
    assert (tmp_path / "weights.failed.json").exists()
    s = train.train(_cfg(tmp_path))                        # clean rerun, same directory
    assert s["weights_file"] == "weights.json" and s["weights_failed"] is False
    assert (tmp_path / "weights.json").exists()
    # observation: the stale failed file is left behind; the summary does not point at it


def test_failed_run_after_a_clean_run_removes_the_old_shipping_name(tmp_path, monkeypatch):
    _short(monkeypatch)
    train.train(_cfg(tmp_path))
    assert (tmp_path / "weights.json").exists()
    _boom(monkeypatch)
    train.train(_cfg(tmp_path))
    assert not (tmp_path / "weights.json").exists()


def test_in_training_policy_error_summary_has_no_weights_and_lacks_the_new_keys(tmp_path, monkeypatch):
    orig = env.TrainPolicy._choose

    def maybe(self, obs, legal, status):
        if self.greedy:
            raise RuntimeError("eval boom")
        return orig(self, obs, legal, status)
    monkeypatch.setattr(env.TrainPolicy, "_choose", maybe)
    try:
        train.train(_cfg(tmp_path, eval_episodes=2))
    except train.TrainingError:
        pass
    s = _summary(tmp_path)
    assert s["stopped"] == "policy_error" and s["weights_sha256"] is None
    assert not (tmp_path / "weights.json").exists() and not (tmp_path / "weights.failed.json").exists()
    # documents the limitation: a script reading s["weights_failed"] would KeyError here
    assert "weights_file" not in s and "weights_failed" not in s
