"""Gate 2 probes for T16 (Evaluation Specialist): multi-worker error injection. Tiny runs only."""
import json

import pytest

pytest.importorskip("numpy")

from tools.rl import env, train  # noqa: E402


def _cfg(out, **kw):
    base = dict(out_dir=str(out), workers=2, max_iters=2, total_seconds=120, episodes_per_iter=2,
                max_frames=120, hidden=(8, 8), eval_episodes=0, final_eval_seeds=0)
    base.update(kw)
    return train.TrainConfig(**base)


def test_multi_worker_in_loop_eval_error_is_counted_and_stops(tmp_path, monkeypatch):
    orig = env.TrainPolicy._choose

    def maybe(self, obs, legal, status):
        if self.greedy:
            raise RuntimeError("eval boom")
        return orig(self, obs, legal, status)
    monkeypatch.setattr(env.TrainPolicy, "_choose", maybe)
    with pytest.raises(train.TrainingError):
        train.train(_cfg(tmp_path, eval_episodes=4))
    s = json.loads((tmp_path / "summary.json").read_text())
    assert s["stopped"] == "policy_error" and s["weights_sha256"] is None
    rows = [json.loads(x) for x in (tmp_path / "log.jsonl").read_text().splitlines()]
    assert rows[-1]["eval_policy_errors"] >= 4 and s["policy_errors"] == rows[-1]["eval_policy_errors"]
    assert not (tmp_path / "weights.json").exists()


def test_multi_worker_final_check_error_fails_the_run(tmp_path, monkeypatch):
    """With workers=2 training, final_check runs in the parent on the exported file and still fails."""
    from agents.rl import policy as pol
    monkeypatch.setattr(env, "COMBOS", env.COMBOS[:2])

    def boom(self, x, mask):
        raise RuntimeError("injected")
    monkeypatch.setattr(pol.Net, "act", boom)
    s = train.train(_cfg(tmp_path, max_iters=1, final_eval_seeds=1))
    assert s["stopped"] == "final_check_policy_error"
    f = s["final_check_vs_baseline_tuning_pure_python"]
    assert f["failed"] is True and f["policy_errors"] > 0
