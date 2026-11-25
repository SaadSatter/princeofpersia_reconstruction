"""T16 Gate 1 (QA): end-to-end checks of the #47 error accounting. Tiny runs only."""

from __future__ import annotations

import json
import sys

import pytest

pytest.importorskip("numpy")

from agents.rl import encoder as enc_mod  # noqa: E402
from agents.rl import policy as pol  # noqa: E402
from tools.rl import env, ppo, train  # noqa: E402


def _cfg(out, **kw):
    base = dict(seed=0, total_seconds=60, episodes_per_iter=2, workers=1, max_iters=1,
                max_frames=200, out_dir=out, hidden=(8, 8), eval_episodes=0, final_eval_seeds=0)
    base.update(kw)
    return train.TrainConfig(**base)


def _w(tmp_path):
    p = tmp_path / "w.json"
    return p, ppo.export_json(ppo.init_params((enc_mod.N_FEATURES, 8, len(enc_mod.MACRO_SLOTS)), 0), p)


def _break_greedy(monkeypatch):
    orig = env.TrainPolicy._choose

    def maybe(self, obs, legal, status):
        if self.greedy:
            raise RuntimeError("eval boom")
        return orig(self, obs, legal, status)
    monkeypatch.setattr(env.TrainPolicy, "_choose", maybe)


def test_one_late_error_in_the_exported_policy_is_still_counted(tmp_path, monkeypatch):
    """A single error in a later duel (not the first) must not be lost."""
    monkeypatch.setattr(env, "COMBOS", env.COMBOS[:3])
    p, sha = _w(tmp_path)
    orig = pol.Net.act
    calls = {"n": 0}

    def late(self, x, mask):
        calls["n"] += 1
        if calls["n"] == 40:
            raise RuntimeError("one late error")
        return orig(self, x, mask)
    monkeypatch.setattr(pol.Net, "act", late)
    r = train.final_check(p, sha, 1)
    assert calls["n"] > 40 and r["policy_errors"] == 1 and r["failed"] is True


def test_final_check_error_keeps_weights_marks_summary_and_main_exits_2(tmp_path, monkeypatch):
    monkeypatch.setattr(env, "COMBOS", env.COMBOS[:2])

    def boom(self, x, mask):
        raise RuntimeError("injected")
    monkeypatch.setattr(pol.Net, "act", boom)
    s = train.train(_cfg(tmp_path, final_eval_seeds=1))
    assert (tmp_path / "weights.json").exists()          # fact: weights are still written
    assert s["stopped"] == "final_check_policy_error"
    assert s["policy_errors"] >= s["final_check_vs_baseline_tuning_pure_python"]["policy_errors"] > 0
    monkeypatch.setattr(train, "train", lambda cfg: s)
    monkeypatch.setattr(sys, "argv", ["train", "--out", str(tmp_path)])
    with pytest.raises(SystemExit) as e:
        train.main()
    assert e.value.code == 2


def test_clean_summary_does_not_exit_2(tmp_path, monkeypatch):
    monkeypatch.setattr(train, "train", lambda cfg: {"stopped": "max_iters", "policy_errors": 0})
    monkeypatch.setattr(sys, "argv", ["train", "--out", str(tmp_path)])
    train.main()


def test_in_loop_eval_error_stops_run_without_weights_and_summary_says_so(tmp_path, monkeypatch):
    _break_greedy(monkeypatch)
    with pytest.raises(train.TrainingError):
        train.train(_cfg(tmp_path, eval_episodes=2))
    s = json.loads((tmp_path / "summary.json").read_text())
    assert s["stopped"] == "policy_error" and s["policy_errors"] > 0 and s["weights_sha256"] is None
    assert not (tmp_path / "weights.json").exists()


def test_eval_errors_with_failfast_off_are_summed_into_summary(tmp_path, monkeypatch):
    _break_greedy(monkeypatch)
    s = train.train(_cfg(tmp_path, eval_episodes=2, fail_on_policy_error=False))
    rows = [json.loads(l) for l in (tmp_path / "log.jsonl").read_text().splitlines()]
    assert s["stopped"] == "max_iters" and s["policy_errors"] == sum(r["policy_errors"] for r in rows) > 0
