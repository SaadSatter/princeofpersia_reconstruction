"""T17 (decision #50): a failed final check withholds weights.json."""

from __future__ import annotations

import json

import pytest

from agents.rl import policy as pol
from agents.rl.policy import file_sha256
from tools.rl import env, train


def _cfg(out, **kw):
    base = dict(seed=0, total_seconds=60, episodes_per_iter=2, workers=1, max_iters=1,
                max_frames=200, out_dir=out, hidden=(8, 8), eval_episodes=0, snapshot_every=1,
                final_eval_seeds=1)
    base.update(kw)
    return train.TrainConfig(**base)


def _short(monkeypatch):
    monkeypatch.setattr(env, "COMBOS", env.COMBOS[:2])


def _boom(monkeypatch):
    def boom(self, x, mask):
        raise RuntimeError("injected")
    monkeypatch.setattr(pol.Net, "act", boom)


def test_a_failed_final_check_renames_the_weights_and_points_the_summary_at_them(tmp_path, monkeypatch):
    _short(monkeypatch); _boom(monkeypatch)
    train.train(_cfg(tmp_path))
    assert not (tmp_path / "weights.json").exists()
    failed = tmp_path / "weights.failed.json"
    assert failed.exists()
    s = json.loads((tmp_path / "summary.json").read_text())
    assert s["stopped"] == "final_check_policy_error"
    assert s["weights_file"] == "weights.failed.json" and s["weights_failed"] is True
    assert s["weights_sha256"] == file_sha256(failed)


def test_the_command_line_exits_2_and_withholds_weights_on_a_failed_final_check(tmp_path, monkeypatch):
    _short(monkeypatch); _boom(monkeypatch)
    cfg = _cfg(tmp_path)
    monkeypatch.setattr("sys.argv", ["train", "--out", str(tmp_path)])
    monkeypatch.setattr(train, "TrainConfig", lambda **kw: cfg)
    with pytest.raises(SystemExit) as exc:
        train.main()
    assert exc.value.code == 2
    assert not (tmp_path / "weights.json").exists() and (tmp_path / "weights.failed.json").exists()


def test_a_clean_run_still_writes_weights_json_and_exits_0(tmp_path, monkeypatch, capsys):
    _short(monkeypatch)
    cfg = _cfg(tmp_path)
    monkeypatch.setattr("sys.argv", ["train", "--out", str(tmp_path)])
    monkeypatch.setattr(train, "TrainConfig", lambda **kw: cfg)
    train.main()                                    # no SystemExit on a clean run
    s = json.loads((tmp_path / "summary.json").read_text())
    assert (tmp_path / "weights.json").exists() and not (tmp_path / "weights.failed.json").exists()
    assert s["weights_file"] == "weights.json" and s["weights_failed"] is False
    assert s["weights_sha256"] == file_sha256(tmp_path / "weights.json")
    assert s["stopped"] != "final_check_policy_error"
