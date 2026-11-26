"""Gate 2 (T07-run1): rerun of the shipped weights' tuning-start check, and the
jumped/flipped dependence scan. Tuning starts only: not held-out, not a strength claim."""
import re
from pathlib import Path

from agents.rl import encoder
from agents.rl.policy import SHIPPED_SHA256, SHIPPED_WEIGHTS
from tools.rl import train

ROOT = Path(__file__).resolve().parent.parent


def test_final_check_rerun_matches_summary():
    import json
    summ = json.loads((ROOT / "tools/rl/runs/run-1/summary.json").read_text())
    exp = summ["final_check_vs_baseline_tuning_pure_python"]
    got = train.final_check(SHIPPED_WEIGHTS, SHIPPED_SHA256, 4)
    for k in ("episodes", "wins", "draws", "losses", "policy_errors", "failed"):
        assert got[k] == exp[k], k


def test_encoder_treats_jumped_and_flipped_alike():
    assert "jumped" in encoder.LEAPS and "flipped" in encoder.LEAPS
    src = (ROOT / "agents/rl/encoder.py").read_text()
    assert len(re.findall(r"""["'](jumped|flipped)["']""", src)) == 2   # only the LEAPS tuple
