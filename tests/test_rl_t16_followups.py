"""T16: follow-ups from T07-fix1's gates (E1-fix1, E2-fix1, QA M1). Tiny smoke runs only."""

from __future__ import annotations

import json

import pytest

pytest.importorskip("numpy")

from agents.rl import encoder as enc_mod  # noqa: E402
from agents.rl import policy as pol  # noqa: E402
from tools.rl import env, ppo, train  # noqa: E402


def _weights(tmp_path):
    p = tmp_path / "w.json"
    sha = ppo.export_json(ppo.init_params((enc_mod.N_FEATURES, 8, len(enc_mod.MACRO_SLOTS)), 0), p)
    return p, sha


def _cfg(out, **kw):
    base = dict(seed=0, total_seconds=60, episodes_per_iter=2, workers=1, max_iters=1,
                max_frames=200, out_dir=out, hidden=(8, 8), eval_episodes=0, final_eval_seeds=0)
    base.update(kw)
    return train.TrainConfig(**base)


def _short_final_check(monkeypatch):
    monkeypatch.setattr(env, "COMBOS", env.COMBOS[:2])      # keep the smoke runs short


def test_final_check_reports_zero_policy_errors_for_a_working_policy(tmp_path, monkeypatch):
    _short_final_check(monkeypatch)
    p, sha = _weights(tmp_path)
    r = train.final_check(p, sha, 1)
    assert r["policy_errors"] == 0 and r["failed"] is False


def test_final_check_counts_an_injected_error_in_the_exported_policy(tmp_path, monkeypatch):
    _short_final_check(monkeypatch)
    p, sha = _weights(tmp_path)

    def boom(self, x, mask):
        raise RuntimeError("injected")
    monkeypatch.setattr(pol.Net, "act", boom)
    r = train.final_check(p, sha, 1)
    assert r["policy_errors"] > 0 and r["failed"] is True


def test_an_error_in_final_check_is_written_to_summary_and_fails_the_check(tmp_path, monkeypatch):
    # Only the exported (pure-Python) path uses Net.act, so training itself stays clean.
    _short_final_check(monkeypatch)

    def boom(self, x, mask):
        raise RuntimeError("injected")
    monkeypatch.setattr(pol.Net, "act", boom)
    s = train.train(_cfg(tmp_path, final_eval_seeds=1))
    on_disk = json.loads((tmp_path / "summary.json").read_text())
    assert on_disk == json.loads(json.dumps(s))
    fc = on_disk["final_check_vs_baseline_tuning_pure_python"]
    assert fc["policy_errors"] > 0 and fc["failed"] is True
    assert on_disk["stopped"] == "final_check_policy_error"


def _break_greedy_only(monkeypatch):
    orig = env.TrainPolicy._choose

    def maybe(self, obs, legal, status):
        if self.greedy:
            raise RuntimeError("injected eval error")
        return orig(self, obs, legal, status)
    monkeypatch.setattr(env.TrainPolicy, "_choose", maybe)


def test_in_loop_evaluation_errors_are_logged_and_stop_the_run(tmp_path, monkeypatch):
    _break_greedy_only(monkeypatch)
    with pytest.raises(train.TrainingError):
        train.train(_cfg(tmp_path, eval_episodes=2))
    rows = [json.loads(l) for l in (tmp_path / "log.jsonl").read_text().splitlines()]
    assert rows[-1]["eval_policy_errors"] > 0 and rows[-1]["policy_errors"] >= rows[-1]["eval_policy_errors"]
    assert json.loads((tmp_path / "summary.json").read_text())["policy_errors"] > 0


def test_in_loop_evaluation_errors_are_logged_even_with_fail_fast_off(tmp_path, monkeypatch):
    _break_greedy_only(monkeypatch)
    train.train(_cfg(tmp_path, eval_episodes=2, fail_on_policy_error=False))
    rows = [json.loads(l) for l in (tmp_path / "log.jsonl").read_text().splitlines()]
    assert rows[0]["eval_policy_errors"] > 0


def test_clean_run_logs_zero_eval_errors(tmp_path):
    train.train(_cfg(tmp_path, eval_episodes=2))
    rows = [json.loads(l) for l in (tmp_path / "log.jsonl").read_text().splitlines()]
    assert rows[0]["eval_policy_errors"] == 0


def test_an_empty_batch_is_not_a_crash():
    assert train._batch([], 0.99, 0.95) is None
    empty = {"actions": [], "rewards": [], "values": [], "features": None, "masks": None, "logps": []}
    assert train._batch([empty, empty], 0.99, 0.95) is None
