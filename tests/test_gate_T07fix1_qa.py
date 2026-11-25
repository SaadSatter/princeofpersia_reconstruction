"""Gate 1 QA tests for T07-fix1 (independent of the tech lead's tests)."""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

import tests.test_versus_baseline as vb
from tools.rl import env, train

ROOT = Path(__file__).resolve().parents[1]
# Candidate H6, orch/wip-T08 @ 25e4587 (unreviewed WIP; cells read with git show, facts only).
H6 = [((4, 2, 8, -1), (5, 2, 1, 1)), ((1, 2, 5, 1), (4, 2, 2, -1)),
      ((5, 2, 7, -1), (3, 2, 4, 1)), ((3, 2, 5, -1), (1, 2, 3, 1))]


def _cells(pairs):
    return {tuple(s[:3]) for p in pairs for s in p}


def test_all_new_starts_are_unique_and_disjoint_from_every_list_here_and_h6():
    new = env.TUNING_STARTS[2:]
    assert len(_cells(new)) == 12                                    # no cell reused inside the six
    others = (list(vb.HELD_OUT_STARTS) + list(vb.LOWER_HELD_OUT_STARTS) + H6
              + list(vb.LOWER_TUNING_STARTS) + env.TUNING_STARTS[:2])
    assert _cells(new).isdisjoint(_cells(others)), _cells(new) & _cells(others)


def test_finding_midterm_tuning_start_equals_a_candidate_h6_4_cell():
    # T08 must either change H6-4 or drop the start. Not decided here.
    shared = _cells(env.TUNING_STARTS[:2]) & _cells(H6)
    assert shared == {(1, 2, 3)}
    assert (1, 2, 3, 1) in {s for p in env.TUNING_STARTS[:2] for s in p}
    assert (1, 2, 3, 1) == H6[3][1]          # it is the B rival of H6-4 (the brief said "A cell")


def test_every_start_lies_in_arena_rooms_and_on_the_floor_row():
    for p in env.TUNING_STARTS:
        for room, row, col, face in p:
            assert 1 <= room <= 6 and row == 2 and 0 <= col <= 9 and face in (-1, 1)


def test_per_update_eval_sees_only_the_two_midterm_starts_but_training_sees_all():
    eval_pairs = {train._combo(k)[0] for k in range(8)}             # default eval_episodes
    assert eval_pairs == set(env.TUNING_STARTS[:2])
    train_pairs = {train._combo(i)[0] for i in range(len(env.COMBOS))}
    assert train_pairs == set(env.TUNING_STARTS)
    # final_check loops over every combo, so it is NOT limited to the first 8 (the tech lead's
    # report and RL_POLICY.md around line 124 say it is: a documentation inaccuracy).
    src = (ROOT / "tools/rl/train.py").read_text()
    assert "for i in range(len(env.COMBOS))" in src.split("def final_check")[1].split("def train")[0]


def _cli(tmp_path, body):
    script = textwrap.dedent(f"""
        import sys
        sys.path.insert(0, {str(ROOT)!r})
        from agents.rl import encoder as e
        {body}
        import tools.rl.train as t
        sys.argv = ["train", "--out", {str(tmp_path)!r}, "--seconds", "30", "--workers", "1"]
        orig = t.TrainConfig
        t.TrainConfig = lambda **kw: orig(**{{**kw, "max_iters": 2, "episodes_per_iter": 2,
            "max_frames": 200, "hidden": (8, 8), "eval_episodes": 2, "final_eval_seeds": 0}})
        t.main()
    """)
    return subprocess.run([sys.executable, "-I", "-c", script], capture_output=True, text=True,
                          cwd=ROOT, timeout=120)


def test_cli_exit_status_2_stderr_message_and_no_weights_on_encoder_error(tmp_path):
    r = _cli(tmp_path, "e.Encoder.features = lambda self,o,l,s: 1/0")
    assert r.returncode == 2, (r.returncode, r.stderr[-400:])
    assert "TRAINING STOPPED" in r.stderr and "error" in r.stderr.lower()
    assert not (tmp_path / "weights.json").exists()
    s = json.loads((tmp_path / "summary.json").read_text())
    assert s["stopped"] == "policy_error" and s["weights_sha256"] is None and s["policy_errors"] > 0


def test_cli_clean_run_exits_zero_and_reports_zero_errors(tmp_path):
    r = _cli(tmp_path, "pass")
    assert r.returncode == 0, r.stderr[-400:]
    s = json.loads((tmp_path / "summary.json").read_text())
    assert s["policy_errors"] == 0 and s["weights_sha256"]
    assert (tmp_path / "weights.json").exists()


def test_a_single_late_error_is_still_caught(monkeypatch, tmp_path):
    from agents.rl import encoder as enc_mod
    real, n = enc_mod.Encoder.features, {"k": 0}

    def flaky(self, obs, legal, status):
        n["k"] += 1
        if n["k"] == 7:
            raise ValueError("one-off")
        return real(self, obs, legal, status)
    monkeypatch.setattr(enc_mod.Encoder, "features", flaky)
    cfg = train.TrainConfig(seed=0, total_seconds=40, episodes_per_iter=2, workers=1, max_iters=2,
                            max_frames=300, out_dir=tmp_path, hidden=(8, 8), eval_episodes=0,
                            final_eval_seeds=0)
    with pytest.raises(train.TrainingError):
        train.train(cfg)
    assert json.loads((tmp_path / "summary.json").read_text())["policy_errors"] >= 1


@pytest.mark.xfail(strict=True, reason="T07-fix1-QA-1: _batch crashes when every episode is empty")
def test_fail_on_policy_error_false_keeps_running_but_still_counts(monkeypatch, tmp_path):
    from agents.rl import encoder as enc_mod

    def boom(self, o, l, s):
        raise RuntimeError("x")
    monkeypatch.setattr(enc_mod.Encoder, "features", boom)
    cfg = train.TrainConfig(seed=0, total_seconds=40, episodes_per_iter=2, workers=1, max_iters=1,
                            max_frames=200, out_dir=tmp_path, hidden=(8, 8), eval_episodes=0,
                            final_eval_seeds=0, fail_on_policy_error=False)
    s = train.train(cfg)
    assert s["policy_errors"] > 0
    assert (tmp_path / "log.jsonl").read_text().strip()
