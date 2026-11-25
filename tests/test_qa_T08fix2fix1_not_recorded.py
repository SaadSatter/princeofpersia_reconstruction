"""QA probes for T08-fix2-fix1: unrecorded policy errors are never printed as 0."""

from __future__ import annotations

from evaluation import analysis


def _row(rid, cfg, seats, kinds, split="heldout"):
    return {"row_id": rid, "scenario": "H6", "start_id": "s", "config": cfg, "split": split,
            "aborted": False, "seats": seats,
            "controllers": {k: {"kind": v} for k, v in kinds.items()}}


def _table(rows):
    return [ln for ln in "\n".join(analysis.policy_error_lines(rows)).splitlines() if ln.startswith("| H6")]


def _rec(i, n):
    return _row(f"r{i}", "MvS", {"A": {"policy_errors": n}, "B": {"policy_errors": None}},
                {"A": "policy", "B": "scripted"})


def test_every_cell_kind_in_one_table():
    rows = [
        _row("a", "MvS", {"A": {"errors": 0}, "B": {"errors": 0}}, {"A": "policy", "B": "scripted"}),
        _row("b", "SvS", {"A": {"errors": 0, "policy_errors": None}, "B": {"errors": 0, "policy_errors": None}},
             {"A": "scripted", "B": "scripted"}),
    ]
    t = _table(rows)
    assert "| H6 | s | MvS | not recorded | not recorded |" in t
    assert "| H6 | s | SvS | n/a | n/a |" in t


def test_mixed_and_fully_recorded_conditions():
    old = _row("o", "MvS", {"A": {}, "B": {"policy_errors": None}}, {"A": "policy", "B": "scripted"})
    mixed = analysis.policy_error_totals([_rec(1, 2), _rec(2, 0), old])[0]
    assert mixed["policy_errors"] == 2 and mixed["rows_with_errors"] == 1 and mixed["not_recorded"] == 1
    assert "| H6 | s | MvS | 2 (1 not recorded) | 1 (1 not recorded) |" in _table([_rec(1, 2), _rec(2, 0), old])
    full = analysis.policy_error_totals([_rec(1, 2), _rec(2, 0)])[0]
    assert full == {"scenario": "H6", "start_id": "s", "config": "MvS", "policy_errors": 2, "rows_with_errors": 1}
    assert "| H6 | s | MvS | 2 | 1 |" in _table([_rec(1, 2), _rec(2, 0)])


def test_recorded_zero_is_zero_not_none():
    r = _row("z", "MvS", {"A": {"policy_errors": 0}}, {"A": "policy"})
    assert analysis.policy_error_totals([r])[0]["policy_errors"] == 0
    assert "| H6 | s | MvS | 0 | 0 |" in _table([r])


def test_mvm_one_seat_unrecorded_is_not_zero():
    r = _row("m", "MvM", {"A": {"policy_errors": 0}, "B": {}}, {"A": "policy", "B": "policy"})
    t = analysis.policy_error_totals([r])[0]
    assert t["policy_errors"] == 0 and t["not_recorded"] == 1


def test_null_on_scripted_seat_is_skipped_and_null_on_policy_seat_is_not_recorded():
    s = _row("s", "MvS", {"A": {"policy_errors": None}}, {"A": "scripted"})
    p = _row("p", "MvS", {"A": {"policy_errors": None}}, {"A": "policy"})
    assert analysis._seat_errors(s) == []
    assert analysis._seat_errors(p) == [("A", None, False)]


def test_edge_no_controllers_and_null_field_is_skipped_and_prints_na():
    r = {"row_id": "e", "scenario": "H6", "start_id": "s", "config": "MvS", "split": "heldout",
         "aborted": False, "seats": {"A": {"policy_errors": None}}}
    assert analysis._seat_errors(r) == []
    assert "| H6 | s | MvS | n/a | n/a |" in _table([r])


def test_a_non_integer_value_is_not_counted_as_a_number():
    r = _row("b", "MvS", {"A": {"policy_errors": "3"}}, {"A": "policy"})
    assert analysis.policy_error_totals([r])[0]["policy_errors"] is None
