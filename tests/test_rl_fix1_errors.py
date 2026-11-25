"""T07-fix1: policy and encoder errors must be counted, visible and fatal in training (T07-E4)."""

from __future__ import annotations

import json

import pytest

from agents.rl import encoder as enc_mod
from tools.rl import env, train


def _cfg(out, **kw):
    base = dict(seed=0, total_seconds=40, episodes_per_iter=2, workers=1, max_iters=2,
                max_frames=300, out_dir=out, hidden=(8, 8), eval_episodes=2, snapshot_every=1,
                final_eval_seeds=0)
    base.update(kw)
    return train.TrainConfig(**base)


def test_a_clean_run_reports_zero_policy_errors_in_log_and_summary(tmp_path):
    summary = train.train(_cfg(tmp_path))
    rows = [json.loads(l) for l in (tmp_path / "log.jsonl").read_text().splitlines()]
    assert rows and all(r["policy_errors"] == 0 for r in rows)
    assert summary["policy_errors"] == 0
    assert json.loads((tmp_path / "summary.json").read_text())["policy_errors"] == 0


def _break_features(monkeypatch):
    def boom(self, obs, legal, status):
        raise RuntimeError("injected encoder failure")
    monkeypatch.setattr(enc_mod.Encoder, "features", boom)


def test_an_injected_encoder_error_is_counted_in_the_episode(monkeypatch):
    from tools.rl import ppo
    params = ppo.init_params((enc_mod.N_FEATURES, 8, len(enc_mod.MACRO_SLOTS)), seed=1)
    _break_features(monkeypatch)
    ep = env.play_episode(params, env.baseline_opponent(), env.TUNING_STARTS[0], seed=1,
                          learner_seat="A", rng_seed=1, max_frames=120)
    assert ep["policy_errors"] > 0


def test_an_injected_error_is_logged_and_stops_training_loudly(monkeypatch, tmp_path):
    _break_features(monkeypatch)
    with pytest.raises(train.TrainingError) as exc:
        train.train(_cfg(tmp_path))
    assert "policy" in str(exc.value).lower() and "error" in str(exc.value).lower()
    rows = [json.loads(l) for l in (tmp_path / "log.jsonl").read_text().splitlines()]
    assert len(rows) == 1 and rows[0]["policy_errors"] > 0       # stopped on the first update
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["policy_errors"] > 0 and summary["stopped"] == "policy_error"
    assert summary["weights_sha256"] is None                       # no weights from a broken run


def test_the_command_line_exits_non_zero_on_a_policy_error(monkeypatch, tmp_path, capsys):
    _break_features(monkeypatch)
    monkeypatch.setattr("sys.argv", ["train", "--out", str(tmp_path), "--seconds", "20",
                                     "--workers", "1"])
    cfg = _cfg(tmp_path, max_iters=1, total_seconds=20)
    monkeypatch.setattr(train, "TrainConfig", lambda **kw: cfg)
    with pytest.raises(SystemExit) as exc:
        train.main()
    assert exc.value.code not in (0, None)
    assert "policy" in capsys.readouterr().err.lower()


def test_the_shipped_policy_counts_errors_where_the_controller_exposes_them(tmp_path):
    from agents.rl.policy import PolicyMacro, make_rl_rival
    from tools.rl import ppo
    params = ppo.init_params((enc_mod.N_FEATURES, 8, len(enc_mod.MACRO_SLOTS)), seed=2)
    path = tmp_path / "w.json"
    sha = ppo.export_json(params, path)
    rival = make_rl_rival(path, sha)
    assert isinstance(rival.policy_macro, PolicyMacro) and rival.policy_macro.errors == 0
    assert rival.policy_errors() == 0
    rival.policy_macro.errors = 3
    assert rival.policy_errors() == 3
