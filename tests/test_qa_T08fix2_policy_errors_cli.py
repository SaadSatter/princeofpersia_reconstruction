"""QA probes for T08-fix2 (decision #84). No policy run on H6, no paid call, temp dirs only."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from agents.macros import MacroController
from agents.rl.policy import PolicyMacro
from evaluation import analysis, controllers as C

ROOT = Path(__file__).resolve().parent.parent


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / "eval" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class BrokenNet:
    def act(self, x, mask):
        raise RuntimeError("inference failed")


def _broken():
    pm = PolicyMacro(BrokenNet(), 1, 6)
    ctrl = MacroController(pm, name="ppo-broken", kind="policy", decision_every=6, macro_every=1)
    ctrl.policy_errors = lambda: pm.errors
    ctrl.weights_sha256 = "0" * 64
    ctrl.version = "qa"
    return ctrl


def _run_cli(tmp_path, monkeypatch, configs):
    runner = _load("run_versus_suite")
    monkeypatch.setattr(C, "make_shipped_policy", _broken)
    rc = runner.main(["--split", "tuning", "--scenarios", "D1", "--configs", configs, "--trials", "1",
                      "--dry-run", "--max-frames", "120", "--out", str(tmp_path)])
    assert rc == 0
    return json.loads((tmp_path / "results.json").read_text())


def _rows(doc):
    return doc["rows"] if isinstance(doc, dict) else doc


def test_cli_injected_failure_is_in_the_row_and_the_analyzer_output(tmp_path, monkeypatch, capsys):
    doc = _run_cli(tmp_path, monkeypatch, "MvS,SvM,SvS")
    by = {r["config"]: r for r in _rows(doc)}
    assert by["MvS"]["seats"]["A"]["policy_errors"] > 0 and by["MvS"]["seats"]["B"]["policy_errors"] is None
    assert by["SvM"]["seats"]["B"]["policy_errors"] > 0 and by["SvM"]["seats"]["A"]["policy_errors"] is None
    assert all(v["policy_errors"] is None for v in by["SvS"]["seats"].values())
    # the runner's own counter still reads 0 for the swallowed error (follow-up note)
    assert by["MvS"]["seats"]["A"]["errors"] == 0
    capsys.readouterr()
    analyzer = _load("analyze_results")
    assert analyzer.main([str(tmp_path / "results.json")]) == 0
    out = capsys.readouterr().out
    odd = out.split("### Odd rows: non-zero policy errors")[1].split("\n## ")[0]
    assert by["MvS"]["row_id"] in odd and by["SvM"]["row_id"] in odd and by["SvS"]["row_id"] not in odd
    assert "None." not in odd


def test_wait_seat_is_null_through_the_cli(tmp_path):
    runner = _load("run_versus_suite")
    rc = runner.main(["--split", "heldout", "--dry-run", "--configs", "SvS", "--trials", "1",
                      "--max-frames", "30", "--out", str(tmp_path)])
    assert rc == 0
    for r in _rows(json.loads((tmp_path / "results.json").read_text())):
        assert all(s["policy_errors"] is None for s in r["seats"].values())


def _row(row_id, split, a, b, has_field=True):
    seats = {"A": {"errors": 0}, "B": {"errors": 0}}
    if has_field:
        seats["A"]["policy_errors"], seats["B"]["policy_errors"] = a, b
    return {"row_id": row_id, "scenario": "H6", "start_id": "s", "config": "MvS", "split": split,
            "aborted": False, "controllers": {"A": {"kind": "policy"}, "B": {"kind": "wait"}},
            "seats": seats}


def test_heldout_harness_error_label_and_tuning_has_none():
    text = "\n".join(analysis.policy_error_lines([_row("h1", "heldout", 2, None),
                                                  _row("t1", "tuning", 2, None)]))
    assert "`h1`: seat A: 2 (harness error)" in text
    assert "`t1`: seat A: 2" in text and "`t1`: seat A: 2 (harness error)" not in text


def test_zero_and_null_rows_are_not_odd():
    text = "\n".join(analysis.policy_error_lines([_row("z", "heldout", 0, None)]))
    assert "None." in text and "harness error" not in text


def test_old_rows_are_not_printed_as_zero_in_the_totals_table():
    """Brief: old rows re-analyse as "not recorded" and not 0 (finding F1: the table prints 0)."""
    text = "\n".join(analysis.policy_error_lines([_row("o1", "heldout", None, None, has_field=False)]))
    assert "not recorded" in text
    table = text.split("### Odd rows")[0]
    row = [ln for ln in table.splitlines() if ln.startswith("| H6 ")][0]
    assert "| 0 |" not in row, f"table prints zero for unrecorded rows: {row}"


def test_t09_committed_results_if_present_reanalyse_unchanged_apart_from_the_new_section():
    res = ROOT / "evaluation" / "results" / "T09"
    if not (res / "results.json").exists():
        pytest.skip("T09 results are not on this branch")
    rows, headers = analysis.load_rows([str(res / "results.json")])
    new = analysis.render(rows, headers, every_round=True)
    old = (res / "analysis.txt").read_text()
    start = new.index("\n## PPO inference errors")
    end = new.find("\n## ", start + 1)
    section = new[start:end if end != -1 else len(new)]
    assert "not recorded" in section
    assert new[:start] + (new[end:] if end != -1 else "") == old
