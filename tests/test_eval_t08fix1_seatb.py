"""T08-fix1 items 3 and 4 (decision #65, QA F-2 and F-4): mirrored seat-B starts and
per-seat analysis, aborted rows that have no controllers, and `--replay` reading the
split from the trace's `meta.json`.

A mirrored start swaps the two rivals (cell, facing, hearts, disguise) and keeps the
guards; the subject is seat B and seat A is the forced stand-in. Tuning split only.
No policy runs here (scripted seats, short frame caps).
"""

from __future__ import annotations

import copy
import json

import pytest

from evaluation import analysis, manifest, spec, suite
from tools.eval import analyze_results, run_versus_suite as cli

MIRRORED = {"D1": ["D1-a", "D1-b", "D1-c"], "B2": ["B2-a", "B2-b", "B2-c"],
            "I3": ["I3-a", "I3-b", "I3-c"], "F5": ["F5-a", "F5-b"]}


def tuning():
    return manifest.load_tuning()


# --- the data --------------------------------------------------------------------------------------
@pytest.mark.parametrize("scenario,source", [(s, i) for s, ids in MIRRORED.items() for i in ids])
def test_every_listed_start_has_a_mirror_with_the_subject_in_seat_b(scenario, source):
    sc = tuning()[scenario]
    src, mir = sc.start(source), sc.start(f"{source}-B")
    assert src.subject == "A" and mir.subject == "B"
    assert mir.rivals["A"] == src.rivals["B"] and mir.rivals["B"] == src.rivals["A"]
    assert mir.hearts == {"A": src.hearts["B"], "B": src.hearts["A"]}
    assert mir.disguised == {"A": src.disguised["B"], "B": src.disguised["A"]}
    assert mir.guards == src.guards
    assert mir.other_controller == src.other_controller and mir.other_controller is not None


def test_f5_c_the_rival_against_rival_start_is_not_mirrored_and_nothing_else_is_added():
    sc = tuning()
    assert "F5-c-B" not in [s.id for s in sc["F5"].starts]
    for scenario, ids in MIRRORED.items():
        mirrored = [s.id for s in sc[scenario].starts if s.subject == "B"]
        assert mirrored == [f"{i}-B" for i in ids]
        assert [s.id for s in sc[scenario].starts if s.subject == "A"] == \
            [s.id for s in sc[scenario].starts if not s.id.endswith("-B")]


def test_mirrors_use_no_cell_the_originals_do_not_and_stay_off_h6():
    t = tuning()
    held = {tuple(s.rivals[x][:3]) for s in manifest.load_heldout()["H6"].starts for x in "AB"}
    for sc in t.values():
        for st in sc.starts:
            for seat in "AB":
                assert tuple(st.rivals[seat][:3]) not in held


def test_the_subject_must_be_a_seat_and_the_forced_seat_is_the_other_one():
    raw = json.loads(manifest.TUNING_PATH.read_text())
    bad = copy.deepcopy(raw)
    bad["scenarios"][0]["starts"][0]["subject"] = "C"
    with pytest.raises(spec.SpecError):
        spec.parse_scenarios(bad, "tuning")
    start = tuning()["D1"].start("D1-a-B")
    assert start.forced_seat == "A"
    assert tuning()["D1"].start("D1-a").forced_seat == "B"


def test_a_free_start_has_no_forced_seat():
    assert tuning()["F5"].start("F5-c").forced_seat is None


# --- planning and controllers ---------------------------------------------------------------------------
def test_a_seat_b_subject_runs_the_configurations_whose_forced_seat_letter_is_s():
    trials = suite.plan_trials(tuning(), ["D1"], ["SvS", "MvS", "SvM", "MvM"], 1, 0)
    cells = {(t.start_id, t.config) for t in trials}
    assert ("D1-a-B", "SvS") in cells and ("D1-a-B", "SvM") in cells
    assert ("D1-a-B", "MvS") not in cells and ("D1-a-B", "MvM") not in cells
    assert ("D1-a", "MvS") in cells and ("D1-a", "SvM") not in cells


def test_the_forced_stand_in_sits_in_seat_a_for_a_mirrored_start():
    [t] = [t for t in suite.plan_trials(tuning(), ["I3"], ["SvS"], 1, 0) if t.start_id == "I3-a-B"]
    ctrls, forced = t.build_controllers()
    assert forced == {"A": "decoy"}
    assert ctrls["A"].kind == "scripted" and ctrls["A"].name.startswith("decoy")
    assert ctrls["B"].name.startswith("versus-baseline")


def test_a_policy_subject_in_seat_b_is_built_from_the_factory(tmp_path):
    class Probe:
        kind, name = "policy", "probe"

        def decide(self, observation, legal):
            return "WAIT"

    [t] = [t for t in suite.plan_trials(tuning(), ["D1"], ["SvM"], 1, 0, policy_factory=Probe)
           if t.start_id == "D1-a-B"]
    ctrls, forced = t.build_controllers()
    assert ctrls["B"].name == "probe" and forced == {"A": "wait"}


# --- one real (short) row ------------------------------------------------------------------------------
def test_a_mirrored_start_runs_with_the_subject_in_seat_b_and_a_monitor_for_seat_b(tmp_path):
    sc = tuning()
    [t] = [t for t in suite.plan_trials(sc, ["B2"], ["SvS"], 1, 0) if t.start_id == "B2-a-B"]
    row = suite.run_trial(t, tmp_path, seed_key=suite.DRY_RUN_KEY, key_id="k", run_id="r",
                          git={"commit": "0" * 40, "dirty": False}, dry_run=True)
    assert row["subject_seat"] == "B" and row["forced_controllers"] == {"A": "wait"}
    assert row["controllers"]["A"]["kind"] == "fallback"
    assert row["outcome"]["result_subject"] == row["outcome"]["result_B"]
    assert row["aborted"] is False and isinstance(row["success"], bool)
    # B2 starts disguised in seat B now, and the monitor watches B
    assert row["metrics"]["subject_disguised_end"] in (True, False)


def test_i3_mirror_counts_the_hearts_of_the_other_seat_as_the_rivals_start_value():
    sc = tuning()["I3"]
    start = sc.start("I3-b-B")
    mon = spec.make_monitor(sc, start)
    assert mon.subject == "B" and mon.rival_hp_start == start.hearts["A"]


def test_the_dry_run_covers_every_start_and_the_mirrors_complete(tmp_path):
    assert cli.main(["--dry-run", "--trials", "1", "--max-frames", "60", "--out", str(tmp_path)]) == 0
    rows = json.loads((tmp_path / "results.json").read_text())["rows"]
    assert {r["start_id"] for r in rows if r["subject_seat"] == "B"} == \
        {f"{i}-B" for ids in MIRRORED.values() for i in ids}
    assert len(rows) == sum(len(sc.starts) for sc in tuning().values())


# --- per-seat analysis --------------------------------------------------------------------------------
S = {"name": "versus-baseline", "kind": "scripted"}
M = {"name": "ppo", "kind": "policy"}
W = {"name": "wait", "kind": "fallback"}


def srow(start, config, subject, success, a, b, n=0):
    forced = {"B": "wait"} if subject == "A" else {"A": "wait"}
    return {"row_id": f"D1/{start}/{config}/t{n}", "scenario": "D1", "scenario_kind": "disguise",
            "start_id": start, "config": config, "trial": n, "dry_run": False, "aborted": False,
            "abort_reason": None, "error": None, "harness_error": False, "success": success,
            "success_reason": "x", "subject_seat": subject, "forced_controllers": forced,
            "controllers": {"A": a, "B": b}, "outcome": {"result_A": "draw", "result_B": "draw"},
            "final_snapshot_sha256": f"{start}-{config}-{n}"}


def test_success_is_reported_per_subject_seat_with_the_subjects_own_controller_label():
    rows = [srow("D1-a", "MvS", "A", True, M, W), srow("D1-b", "MvS", "A", False, M, W),
            srow("D1-a-B", "SvM", "B", True, W, M), srow("D1-b-B", "SvM", "B", True, W, M),
            srow("D1-c-B", "SvM", "B", False, W, M)]
    got = {(r["config"], r["subject_seat"]): r for r in analysis.success_by_scenario(rows)}
    assert got[("MvS", "A")]["subject"] == "M" and (got[("MvS", "A")]["k"], got[("MvS", "A")]["n"]) == (1, 2)
    assert got[("SvM", "B")]["subject"] == "M" and (got[("SvM", "B")]["k"], got[("SvM", "B")]["n"]) == (2, 3)


def test_the_same_configuration_in_two_subject_seats_is_two_lines_not_one():
    rows = [srow("D1-a", "SvS", "A", True, S, W), srow("D1-a-B", "SvS", "B", False, W, S)]
    got = analysis.success_by_scenario(rows)
    assert sorted((r["subject_seat"], r["k"], r["n"]) for r in got) == [("A", 1, 1), ("B", 0, 1)]
    text = analysis.render(rows, [{"run_id": "r", "split": "tuning", "commit": "c" * 40,
                                   "dry_run": False, "seed_key_id": "abcd1234"}])
    assert "subject seat" in text.lower()


def test_rows_without_a_subject_seat_are_read_as_seat_a():
    old = srow("D1-a", "SvS", "A", True, S, W)
    del old["subject_seat"]
    assert analysis.success_by_scenario([old])[0]["subject_seat"] == "A"


# --- QA F-2: an aborted row with no controllers --------------------------------------------------------
def exception_row(kind="fight", scenario="F5", start="F5-c", config="MvS"):
    return {"row_id": f"{scenario}/{start}/{config}/t0", "scenario": scenario,
            "scenario_kind": kind, "start_id": start, "config": config, "trial": 0,
            "dry_run": False, "forced_controllers": {}, "controllers": {}, "aborted": True,
            "abort_reason": "exception", "harness_error": True,
            "error": "RuntimeError: cannot build", "success": None, "success_reason": None}


def test_duel_results_lists_a_row_with_no_controllers_as_aborted_instead_of_crashing():
    got = analysis.duel_results([exception_row()])
    assert len(got) == 1
    d = got[0]
    assert d["scenario"] == "F5" and d["aborted"] == 1 and d["n"] == 1
    assert (d["win"], d["draw"], d["loss"]) == (0, 0, 0)
    assert d["controller"] == "none built"


def test_such_rows_sit_in_the_denominator_beside_rows_that_did_run():
    ok = {**exception_row(), "controllers": {"A": M, "B": S}, "aborted": False,
          "abort_reason": None, "error": None, "harness_error": False,
          "outcome": {"result_A": "win", "result_B": "loss"},
          "final_snapshot_sha256": "x", "row_id": "F5/F5-c/MvS/t1", "trial": 1}
    got = {d["controller"]: d for d in analysis.duel_results([ok, exception_row()])}
    assert got["M"]["win"] == 1 and got["none built"]["aborted"] == 1


def test_the_cli_summary_prints_the_aborted_section_for_such_a_file(tmp_path, capsys):
    path = tmp_path / "results.json"
    path.write_text(json.dumps({"run": {"run_id": "r", "split": "tuning", "commit": "c" * 40,
                                        "dry_run": False, "seed_key_id": "abcd1234"},
                                "rows": [exception_row()]}))
    assert analyze_results.main([str(path), "--json", str(tmp_path / "s.json")]) == 0
    out = capsys.readouterr().out
    assert "Aborted rounds" in out and "cannot build" in out
    assert json.loads((tmp_path / "s.json").read_text())["aborted"] == 1


# --- QA F-4: --replay reads the split from meta.json ------------------------------------------------------
def test_replay_of_a_heldout_trace_finds_its_split_in_meta_json(tmp_path):
    out = tmp_path / "h"
    assert cli.main(["--dry-run", "--split", "heldout", "--trials", "1", "--max-frames", "30",
                     "--scenarios", "H6", "--out", str(out)]) == 0
    metas = sorted((out / "traces").rglob("meta.json"))
    assert metas and json.loads(metas[0].read_text())["split"] == "heldout"
    assert cli.main(["--replay", str(metas[0].parent)]) == 0


def test_replay_of_a_seat_b_tuning_trace_works_without_a_split_flag(tmp_path):
    out = tmp_path / "t"
    assert cli.main(["--dry-run", "--scenarios", "D1", "--trials", "1", "--max-frames", "60",
                     "--out", str(out)]) == 0
    meta = next((out / "traces" / "D1" / "D1-a-B").rglob("meta.json"))
    assert cli.main(["--replay", str(meta.parent)]) == 0


def test_replay_of_a_trace_with_an_unknown_split_fails_cleanly(tmp_path, capsys):
    out = tmp_path / "t"
    assert cli.main(["--dry-run", "--scenarios", "D1", "--trials", "1", "--max-frames", "60",
                     "--out", str(out)]) == 0
    meta = next((out / "traces").rglob("meta.json"))
    data = json.loads(meta.read_text())
    data["split"] = "nonsense"
    meta.write_text(json.dumps(data))
    assert cli.main(["--replay", str(meta.parent)]) == 2
    assert "split" in capsys.readouterr().err
