"""Gate 2 (T08-fix2): the real shipped weights record policy_errors == 0 on a policy seat and
null on scripted seats. Tuning split, dry run, temp dir, no H6, no network."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_shipped_weights_policy_errors_zero_and_null_on_scripted(tmp_path):
    spec = importlib.util.spec_from_file_location("run_versus_suite_t08fix2_eval",
                                                  ROOT / "tools" / "eval" / "run_versus_suite.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    rc = mod.main(["--split", "tuning", "--scenarios", "D1", "--configs", "SvS,MvS,SvM", "--trials", "1",
                   "--dry-run", "--max-frames", "300", "--out", str(tmp_path)])
    assert rc == 0
    doc = json.loads((tmp_path / "results.json").read_text())
    rows = doc["rows"] if isinstance(doc, dict) else doc
    assert rows
    seen_policy = 0
    for r in rows:
        assert r["split"] == "tuning"
        for seat, s in r["seats"].items():
            assert "policy_errors" in s
            if r["controllers"][seat]["kind"] == "policy":
                assert s["policy_errors"] == 0
                seen_policy += 1
            else:
                assert s["policy_errors"] is None
    assert seen_policy >= 2
