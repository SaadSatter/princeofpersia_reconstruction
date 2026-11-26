"""Gate 2 (T08-fix2-fix1): end to end, rows -> analyze_results CLI -> printed table.
Shipped weights, tuning split, dry run, temp dir, no H6. Recorded zeros print 0; stripped or
null counters print "not recorded"; a condition with no policy seat prints n/a."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _table(out: str) -> dict:
    sec = out.split("## PPO inference errors")[1].split("### Odd rows")[0]
    cells = {}
    for ln in sec.splitlines():
        p = [c.strip() for c in ln.strip("|").split("|")]
        if len(p) == 5 and p[2] in ("SvS", "MvS", "SvM", "MvM"):
            cells[p[2]] = (p[3], p[4])
    return cells


def test_recorded_zero_vs_not_recorded_end_to_end(tmp_path, capsys):
    run = _load("rvs_t08fix2fix1_eval", "tools/eval/run_versus_suite.py")
    assert run.main(["--split", "tuning", "--scenarios", "D1", "--configs", "SvS,MvS,SvM", "--trials", "1",
                     "--dry-run", "--max-frames", "300", "--out", str(tmp_path)]) == 0
    res = tmp_path / "results.json"
    doc = json.loads(res.read_text())
    rows = doc["rows"] if isinstance(doc, dict) else doc
    ana = _load("ana_t08fix2fix1_eval", "tools/eval/analyze_results.py")

    capsys.readouterr()
    assert ana.main([str(res), "--no-rounds"]) == 0
    t = _table(capsys.readouterr().out)
    assert t["SvS"] == ("n/a", "n/a")
    assert t["MvS"] == ("0", "0") and t["SvM"] == ("0", "0")

    # field stripped (a pre-T08-fix2 row) and field nulled on policy seats
    for mode in ("strip", "null"):
        d = copy.deepcopy(doc)
        rs = d["rows"] if isinstance(d, dict) else d
        for r in rs:
            for seat, s in r["seats"].items():
                if r["controllers"][seat]["kind"] == "policy":
                    if mode == "strip":
                        s.pop("policy_errors")
                    else:
                        s["policy_errors"] = None
        p = tmp_path / f"{mode}.json"
        p.write_text(json.dumps(d))
        assert ana.main([str(p), "--no-rounds"]) == 0
        out = capsys.readouterr().out
        t = _table(out)
        assert t["MvS"] == ("not recorded", "not recorded"), (mode, t)
        assert t["SvM"] == ("not recorded", "not recorded"), (mode, t)
        assert t["SvS"] == ("n/a", "n/a")
        assert "zero cannot be assumed" in out
