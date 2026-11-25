"""T08-fix2-fix1 (decision #84; T08-fix2 QA F1, N2): an unrecorded policy-error count is
never printed as 0. Constructed rows only; no policy run."""

from __future__ import annotations

from evaluation import analysis


def _row(row_id, config, seats, kinds, split="heldout"):
    return {"row_id": row_id, "scenario": "H6", "start_id": "s", "config": config, "split": split,
            "aborted": False, "seats": {k: {"policy_errors": v} for k, v in seats.items()},
            "controllers": {k: {"kind": kinds[k]} for k in seats}}


def _old(row_id, config="MvS"):
    return {"row_id": row_id, "scenario": "H6", "start_id": "s", "config": config,
            "split": "heldout", "aborted": False, "seats": {"A": {"errors": 0}, "B": {"errors": 0}},
            "controllers": {"A": {"kind": "policy"}, "B": {"kind": "scripted"}}}


def _cell(rows, config):
    lines = analysis.policy_error_lines(rows)
    return [ln for ln in lines if ln.startswith(f"| H6 | s | {config} |")][0]


def test_a_condition_of_only_old_rows_is_none_and_prints_not_recorded():
    rows = [_old("o1"), _old("o2")]
    t = analysis.policy_error_totals(rows)[0]
    assert t["policy_errors"] is None and t["rows_with_errors"] is None and t["not_recorded"] == 2
    cell = _cell(rows, "MvS")
    assert cell.count("not recorded") == 2 and "| 0 |" not in cell


def test_a_mixed_condition_sums_recorded_rows_and_counts_the_rest():
    new = _row("n1", "MvS", {"A": 3, "B": None}, {"A": "policy", "B": "scripted"})
    rows = [new, _old("o1")]
    t = analysis.policy_error_totals(rows)[0]
    assert (t["policy_errors"], t["rows_with_errors"], t["not_recorded"]) == (3, 1, 1)
    assert "3 (1 not recorded)" in _cell(rows, "MvS")


def test_a_condition_with_no_policy_seat_prints_na():
    rows = [_row("s1", "SvS", {"A": None, "B": None}, {"A": "scripted", "B": "scripted"})]
    t = analysis.policy_error_totals(rows)[0]
    assert t["policy_errors"] is None and "not_recorded" not in t
    assert "n/a" in _cell(rows, "SvS") and "not recorded" not in _cell(rows, "SvS")


def test_a_policy_seat_with_a_null_counter_is_not_recorded_not_zero():
    rows = [_row("p1", "MvS", {"A": None, "B": None}, {"A": "policy", "B": "scripted"})]
    t = analysis.policy_error_totals(rows)[0]
    assert t["policy_errors"] is None and t["not_recorded"] == 1
    assert "not recorded" in _cell(rows, "MvS")


def test_recorded_zero_still_prints_zero():
    rows = [_row("z", "MvS", {"A": 0, "B": None}, {"A": "policy", "B": "scripted"})]
    assert analysis.policy_error_totals(rows)[0]["policy_errors"] == 0
    assert "| 0 | 0 |" in _cell(rows, "MvS")


def test_the_footnote_is_kept():
    text = "\n".join(analysis.policy_error_lines([_old("o1")]))
    assert "zero cannot be assumed" in text
