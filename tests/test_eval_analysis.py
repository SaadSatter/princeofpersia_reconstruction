"""T08: analysis of results files: Wilson intervals, every round, distinct outcomes.

Carried notes: report results per seat; a mirror match (the same kind of
controller in both seats) is one trial; seeds are not independent trials unless
the final states differ (T07-run1 Evaluation E3: duels of one start pair gave
identical results across seeds).
"""

from __future__ import annotations

import json

import pytest

from evaluation import analysis, stats
from tools.eval import analyze_results

S = {"name": "versus-baseline", "kind": "scripted"}
M = {"name": "ppo-80e4a110", "kind": "policy"}
W = {"name": "wait", "kind": "fallback"}


def row(n=0, scenario="D1", start="D1-a", config="SvS", success=True, aborted=False, a=S, b=W,
        res_a="draw", res_b="draw", sha=None, forced=None, kind="disguise", dry=False,
        reason="x"):
    return {"row_id": f"{scenario}/{start}/{config}/t{n}", "scenario": scenario,
            "scenario_kind": kind, "start_id": start, "config": config, "trial": n,
            "dry_run": dry, "aborted": aborted, "abort_reason": "max_frames" if aborted else None,
            "error": None, "harness_error": False,
            "success": None if aborted else success,
            "success_reason": reason, "termination": "aborted:max_frames" if aborted else "draw:time_up",
            "forced_controllers": {"B": "wait"} if forced is None and b is W else (forced or {}),
            "controllers": {"A": a, "B": b},
            "outcome": {"result_A": res_a, "result_B": res_b},
            "final_snapshot_sha256": sha if sha is not None else f"sha-{scenario}-{start}-{config}-{n}"}


def header(dry=False):
    return {"run_id": "r", "split": "tuning", "commit": "c" * 40, "dry_run": dry,
            "seed_key_id": "abcd1234"}


# --- Wilson ------------------------------------------------------------------------------------
def test_wilson_matches_known_values_and_handles_edges():
    assert stats.wilson(0, 0) == (0.0, 1.0)
    lo, hi = stats.wilson(5, 10)
    assert lo == pytest.approx(0.2366, abs=1e-3) and hi == pytest.approx(0.7634, abs=1e-3)
    lo, hi = stats.wilson(3, 3)
    assert lo == pytest.approx(0.4385, abs=1e-3) and hi == 1.0
    lo, hi = stats.wilson(0, 4)
    assert lo == 0.0 and hi == pytest.approx(0.4899, abs=1e-3)
    with pytest.raises(ValueError):
        stats.wilson(5, 4)


# --- success rates -------------------------------------------------------------------------------
def test_an_aborted_round_counts_as_a_failure_in_the_denominator_and_is_listed():
    rows = [row(0, success=True), row(1, success=True), row(2, success=False),
            row(3, aborted=True)]
    [r] = analysis.success_by_scenario(rows)
    assert (r["k"], r["n"], r["aborted"]) == (2, 4, 1)
    text = analysis.render(rows, [header()])
    assert "Aborted rounds" in text and "D1/D1-a/SvS/t3" in text


def test_identical_final_states_are_one_trial_not_independent_seeds():
    rows = [row(i, sha="same") for i in range(3)]
    [r] = analysis.success_by_scenario(rows)
    assert r["n_rows"] == 3 and r["n"] == 1 and r["k"] == 1
    assert "n<3" in r["flag"] and r["distinct"] == 1
    [c] = analysis.condition_table(rows)
    assert c["n_rows"] == 3 and c["n_distinct"] == 1


def test_different_final_states_count_as_separate_trials():
    rows = [row(i, sha=f"s{i}", success=i != 2) for i in range(3)]
    [r] = analysis.success_by_scenario(rows)
    assert (r["n_rows"], r["n"], r["k"], r["flag"]) == (3, 3, 2, "")


def test_distinct_outcomes_are_counted_per_start_so_starts_add_up():
    rows = [row(0, start="D1-a", sha="x"), row(1, start="D1-a", sha="x"),
            row(0, start="D1-b", sha="y")]
    [r] = analysis.success_by_scenario(rows)
    assert (r["n_rows"], r["n"]) == (3, 2)


def test_conditions_are_split_by_configuration_and_a_row_without_success_is_not_scored():
    rows = [row(0, config="SvS"), row(0, config="MvS", a=M, success=False)]
    got = {r["config"]: r for r in analysis.success_by_scenario(rows)}
    assert got["SvS"]["k"] == 1 and got["MvS"]["k"] == 0
    assert got["MvS"]["subject"] == "M" and got["SvS"]["subject"] == "S"
    duels = [row(0, scenario="H6", start="H6-1", kind="duel", b=S, forced={})]
    assert analysis.success_by_scenario(duels) == []                   # outcome-only scenario


# --- duels: win, draw, loss per controller, per seat ---------------------------------------------
def duel(n, config, a, b, res_a, res_b, start="H6-1", sha=None):
    return row(n, scenario="H6", start=start, config=config, kind="duel", a=a, b=b, forced={},
               res_a=res_a, res_b=res_b, sha=sha)


def test_a_mirror_match_is_one_trial_reported_by_seat_not_as_two_controllers():
    rows = [duel(0, "SvS", S, S, "win", "loss"), duel(1, "SvS", S, S, "draw", "draw",
                                                       start="H6-2")]
    [d] = analysis.duel_results(rows)
    assert d["mirror"] is True and d["n"] == 2
    assert (d["a_wins"], d["b_wins"], d["draws"]) == (1, 0, 1)


def test_seat_swapped_pair_reports_the_policy_per_seat_and_overall():
    rows = [duel(0, "MvS", M, S, "win", "loss"), duel(0, "SvM", S, M, "draw", "draw"),
            duel(0, "SvM", S, M, "loss", "win", start="H6-2"),
            duel(0, "MvS", M, S, "loss", "win", start="H6-2")]
    got = {d["controller"]: d for d in analysis.duel_results(rows)}
    m, s = got["M"], got["S"]
    assert (m["win"], m["draw"], m["loss"], m["n"]) == (2, 1, 1, 4)
    assert (s["win"], s["draw"], s["loss"]) == (1, 1, 2)
    assert m["by_seat"]["A"] == {"win": 1, "draw": 0, "loss": 1, "n": 2}
    assert m["by_seat"]["B"] == {"win": 1, "draw": 1, "loss": 0, "n": 2}
    assert m["win_ci"][0] < 0.5 < m["win_ci"][1]


def test_duel_rows_with_identical_final_states_are_not_counted_twice():
    rows = [duel(i, "MvS", M, S, "win", "loss", sha="same") for i in range(3)]
    [m, s] = sorted(analysis.duel_results(rows), key=lambda d: d["controller"])
    assert m["n_rows"] == 3 and m["n"] == 1 and m["win"] == 1


def test_aborted_duels_are_counted_as_neither_win_nor_loss_but_stay_in_the_denominator():
    rows = [duel(0, "MvS", M, S, "win", "loss"), duel(1, "MvS", M, S, "win", "loss",
                                                       start="H6-2")]
    rows[1]["aborted"] = True
    got = {d["controller"]: d for d in analysis.duel_results(rows)}
    assert (got["M"]["win"], got["M"]["n"], got["M"]["aborted"]) == (1, 2, 1)


def test_forced_stand_in_rows_are_not_duels():
    assert analysis.duel_results([row(0)]) == []


# --- the rendered report ----------------------------------------------------------------------------
def test_render_lists_every_round_and_labels_dry_runs():
    rows = [row(i, dry=True, sha=f"s{i}") for i in range(4)]
    text = analysis.render(rows, [header(dry=True)])
    assert "DRY RUN" in text
    for r in rows:
        assert r["row_id"] in text
    assert "Every round" in text and "distinct" in text.lower()
    assert "Every round" not in analysis.render(rows, [header()], every_round=False)


def test_the_analysis_cli_reads_a_results_file_and_writes_json(tmp_path, capsys):
    rows = [row(0), row(1, success=False, sha="b"), duel(0, "MvS", M, S, "win", "loss")]
    f = tmp_path / "results.json"
    f.write_text(json.dumps({"run": header(), "rows": rows}))
    out = tmp_path / "s.json"
    assert analyze_results.main([str(f), "--json", str(out)]) == 0
    printed = capsys.readouterr().out
    assert "D1/D1-a/SvS/t1" in printed
    data = json.loads(out.read_text())
    assert data["rows"] == 3 and data["success"][0]["n_rows"] == 2 and data["duels"]
