"""Gate 2 probes for T07-fix1 (Evaluation Specialist). No training run; tiny smoke only."""
import inspect
import json

import pytest

pytest.importorskip("numpy")

from tools.rl import env, train  # noqa: E402


def test_multi_worker_error_is_counted_and_stops_the_run(tmp_path, monkeypatch):
    """QA ran workers=1 only. With a fork pool the count travels in the episode dict."""
    from agents.rl import encoder

    def boom(self, *a, **k):
        raise RuntimeError("injected")
    monkeypatch.setattr(encoder.Encoder, "features", boom)
    cfg = train.TrainConfig(out_dir=str(tmp_path), workers=2, max_iters=2, total_seconds=120,
                            episodes_per_iter=4, max_frames=120, eval_episodes=0, final_eval_seeds=0)
    with pytest.raises(train.TrainingError):
        train.train(cfg)
    s = json.loads((tmp_path / "summary.json").read_text())
    assert s["stopped"] == "policy_error" and s["policy_errors"] > 0 and s["weights_sha256"] is None
    assert not (tmp_path / "weights.json").exists()


def test_final_check_counts_an_exported_policy_error_and_fails(tmp_path, monkeypatch):
    """T07-fix1-E1, fixed in T16: an error in the exported pure-Python path is counted and fails the check."""
    from agents.rl import encoder as enc_mod, policy as pol
    from tools.rl import ppo
    monkeypatch.setattr(env, "COMBOS", env.COMBOS[:2])
    p = tmp_path / "w.json"
    sha = ppo.export_json(ppo.init_params((enc_mod.N_FEATURES, 8, len(enc_mod.MACRO_SLOTS)), 0), p)

    def boom(self, x, mask):
        raise RuntimeError("injected")
    monkeypatch.setattr(pol.Net, "act", boom)
    r = train.final_check(p, sha, 1)
    assert r["policy_errors"] > 0 and r["failed"] is True


def test_in_loop_eval_error_is_counted_logged_and_stops_the_run(tmp_path, monkeypatch):
    """T07-fix1-E2, fixed in T16: greedy eval-episode errors are summed, logged, and stop the run (#47)."""
    orig = env.TrainPolicy._choose

    def maybe(self, obs, legal, status):
        if self.greedy:
            raise RuntimeError("eval boom")
        return orig(self, obs, legal, status)
    monkeypatch.setattr(env.TrainPolicy, "_choose", maybe)
    cfg = train.TrainConfig(out_dir=str(tmp_path), workers=1, max_iters=2, total_seconds=120,
                            episodes_per_iter=2, max_frames=120, eval_episodes=2, final_eval_seeds=0,
                            hidden=(8, 8))
    with pytest.raises(train.TrainingError):
        train.train(cfg)
    s = json.loads((tmp_path / "summary.json").read_text())
    assert s["stopped"] == "policy_error" and s["policy_errors"] > 0 and s["weights_sha256"] is None
    rows = [json.loads(x) for x in (tmp_path / "log.jsonl").read_text().splitlines()]
    assert rows[-1]["eval_policy_errors"] > 0


def test_start_balance_baseline_vs_baseline():
    """Scripted baseline vs itself on each of the 8 tuning starts, both orders (info, printed)."""
    from agents.versus_baseline import make_baseline
    from pop import arena
    from pop.versus import VersusEpisode
    from pop.versus_runner import VersusRunner
    rows = []
    for pi, (a, b) in enumerate(env.TUNING_STARTS):
        for first in (True, False):
            place = {"A": a, "B": b} if first else {"A": b, "B": a}
            res = VersusRunner(lambda place=place: VersusEpisode(arena.situation("A"), place, 0, 3600,
                                                                 arena.GUARD_POSTS),
                               {"A": make_baseline(), "B": make_baseline()}, copy_mode="json",
                               threaded=False, clock=lambda: 0.0).run(7)
            rows.append((pi, first, res["outcome"]["reason"], res["frames"]))
    print("BALANCE", rows)
    assert len(rows) == 16
