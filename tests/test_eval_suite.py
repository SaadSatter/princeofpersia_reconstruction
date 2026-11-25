"""T08: the versus suite runner, result rows, trace replay and the CLI.

Decision #24 (runner policy): aborted runs are reported, the seed key is
secret, every trial gets fresh controllers. Decision #61: no policy run on the
held-out split here; held-out checks use WAIT seats with a frame cap.
"""

from __future__ import annotations

import copy
import json
import os
import stat
import time
from pathlib import Path

import pytest

from agents.rl.policy import SHIPPED_SHA256
from evaluation import controllers as C, manifest, spec, suite
from pop.versus_runner import VersusLimits
from tools.eval import run_versus_suite as cli

ROW_KEYS = {
    "schema", "run_id", "row_id", "scenario", "scenario_kind", "split", "start_id", "config",
    "trial", "seed", "subject_seat", "duration_frames", "commit", "dirty", "game_version",
    "dry_run", "forced_controllers", "decision_every", "seed_key_id", "controllers", "outcome",
    "termination", "aborted", "abort_reason", "harness_error", "success", "success_reason",
    "metrics", "seats", "invalid_inputs", "stale_inputs", "replaced_inputs", "latency",
    "final_snapshot_sha256", "trace_paths",
}


def tiny_scenarios(frames=60):
    raw = json.loads(manifest.TUNING_PATH.read_text())
    raw = copy.deepcopy(raw)
    for sc in raw["scenarios"]:
        sc["duration_frames"] = frames
    return spec.parse_scenarios(raw, "tuning")


@pytest.fixture(scope="module")
def dry_run(tmp_path_factory):
    out = tmp_path_factory.mktemp("dry")
    t0 = time.perf_counter()
    code = cli.main(["--dry-run", "--trials", "1", "--out", str(out)])
    elapsed = time.perf_counter() - t0
    data = json.loads((out / "results.json").read_text())
    return {"code": code, "out": out, "data": data, "elapsed": elapsed}


# --- dry run: every scenario, baseline against baseline, complete rows -------------------------
def test_dry_run_writes_one_complete_row_for_every_start_of_every_scenario(dry_run):
    assert dry_run["code"] == 0
    rows = dry_run["data"]["rows"]
    starts = [(sc.id, s.id) for sc in spec.load_scenario_file(manifest.TUNING_PATH).values()
              for s in sc.starts]
    assert [(r["scenario"], r["start_id"]) for r in rows] == starts
    for r in rows:
        assert ROW_KEYS <= set(r), ROW_KEYS - set(r)
        assert r["dry_run"] is True and r["config"] == "SvS" and r["split"] == "tuning"
        assert r["aborted"] is False and r["harness_error"] is False and r["error"] is None
        assert r["termination"] in ("draw:time_up",) or r["termination"].startswith("won:")
        assert r["controllers"]["A"]["kind"] == "scripted"
        assert r["controllers"]["A"]["name"].startswith("versus-baseline")
        assert r["controllers"]["A"]["version"].startswith("source:")


def test_a_dry_run_records_commit_hash_seed_counts_latency_and_trace_paths(dry_run):
    out = dry_run["out"]
    for r in dry_run["data"]["rows"]:
        assert len(r["commit"]) == 40 and isinstance(r["dirty"], bool)
        assert isinstance(r["seed"], int) and r["decision_every"] == 6
        for seat in "AB":
            s = r["seats"][seat]
            assert {"decisions", "fallbacks", "refused", "errors", "timeouts", "busy"} <= set(s)
            assert s["decisions"] > 0
            assert r["latency"][seat]["n"] == s["decisions"]
            assert (out / r["trace_paths"][seat]).is_file()
        assert set(r["invalid_inputs"]) == {"A", "B"} and set(r["stale_inputs"]) == {"A", "B"}
        assert r["outcome"]["result_A"] in ("win", "loss", "draw")
        assert r["outcome"]["frames"] <= r["duration_frames"]


def test_scenario_rows_carry_a_success_flag_computed_from_true_state(dry_run):
    for r in dry_run["data"]["rows"]:
        assert isinstance(r["success"], bool) and r["success_reason"]
        assert "frames_observed" in r["metrics"]


def test_rows_say_provider_token_and_cost_fields_are_not_applicable(dry_run):
    for r in dry_run["data"]["rows"]:
        for seat in "AB":
            c = r["controllers"][seat]
            assert c["provider"] == c["tokens"] == c["cost_usd"] == "N/A"
    assert "N/A" in dry_run["data"]["run"]["provider_fields"]


def test_the_header_marks_the_run_as_a_dry_run_with_the_public_dry_run_key(dry_run):
    h = dry_run["data"]["run"]
    assert h["dry_run"] is True and h["seed_key_id"] == suite.DRY_RUN_KEY_ID
    assert h["scenario_file_sha256"]["tuning"] == spec.file_sha256(manifest.TUNING_PATH)
    assert h["decisions_in_force"]["B2_low_threshold"] == 50


def test_the_full_dry_run_is_fast_enough_for_the_suite(dry_run):
    assert dry_run["elapsed"] < 120


# --- two-seat traces and replay -----------------------------------------------------------------
def trace_dir(dry_run, index=0):
    r = dry_run["data"]["rows"][index]
    return dry_run["out"] / Path(r["trace_paths"]["A"]).parent


def test_replay_reproduces_the_final_snapshot_of_every_row(dry_run):
    scenarios = spec.load_scenario_file(manifest.TUNING_PATH)
    for i, r in enumerate(dry_run["data"]["rows"]):
        rep = suite.replay_dir(trace_dir(dry_run, i), scenarios)
        assert rep["ok"] is True and rep["replayed"] == r["final_snapshot_sha256"]


def test_cli_replay_exits_zero_on_a_good_trace_and_one_on_a_tampered_one(dry_run, tmp_path, capsys):
    good = trace_dir(dry_run, 3)
    assert cli.main(["--replay", str(good)]) == 0
    assert json.loads(capsys.readouterr().out.strip().splitlines()[-1])["ok"] is True
    bad = tmp_path / "bad"
    bad.mkdir()
    for f in good.iterdir():
        (bad / f.name).write_text(f.read_text())
    meta = json.loads((bad / "meta.json").read_text())
    meta["final_snapshot_sha256"] = "0" * 64
    (bad / "meta.json").write_text(json.dumps(meta))
    assert cli.main(["--replay", str(bad)]) == 1


def test_a_changed_recorded_input_does_not_replay_to_the_same_snapshot(dry_run, tmp_path):
    src = trace_dir(dry_run, 0)
    bad = tmp_path / "edited"
    bad.mkdir()
    for f in src.iterdir():
        (bad / f.name).write_text(f.read_text())
    lines = [json.loads(x) for x in (bad / "seat-A.jsonl").read_text().splitlines()]
    moved = False
    for rec in lines:
        if rec.get("type") == "decision" and rec["input"] not in (None, "WAIT"):
            rec["input"] = "WAIT"
            moved = True
            break
    assert moved
    (bad / "seat-A.jsonl").write_text("\n".join(json.dumps(x) for x in lines) + "\n")
    try:
        rep = suite.replay_dir(bad, spec.load_scenario_file(manifest.TUNING_PATH))
    except ValueError:
        return
    assert rep["ok"] is False


def test_trace_files_hold_one_file_per_seat_and_no_seed_key(dry_run):
    d = trace_dir(dry_run, 0)
    assert {p.name for p in d.iterdir()} == {"seat-A.jsonl", "seat-B.jsonl", "meta.json"}


# --- controllers: fresh per trial, M seats use the shipped weights ---------------------------------
def test_each_trial_builds_fresh_distinct_controllers_for_both_seats():
    sc = tiny_scenarios()
    t = suite.plan_trials(sc, ["F5"], ["SvS"], 1, 0)[-1]           # F5-c: free seat B
    a, _ = t.build_controllers()
    b, _ = t.build_controllers()
    assert a["A"] is not a["B"] and a["A"] is not b["A"] and a["B"] is not b["B"]


def test_forced_stand_in_controllers_are_recorded(dry_run):
    by_id = {r["start_id"]: r for r in dry_run["data"]["rows"]}
    assert by_id["D1-a"]["forced_controllers"] == {"B": "wait"}
    assert by_id["I3-a"]["forced_controllers"] == {"B": "decoy"}
    assert by_id["F5-c"]["forced_controllers"] == {}
    assert by_id["D1-a"]["controllers"]["B"]["kind"] == "fallback"


def test_plan_skips_a_config_whose_other_seat_would_be_forced_anyway():
    sc = tiny_scenarios()
    trials = suite.plan_trials(sc, ["F5"], ["SvS", "MvS", "SvM", "MvM"], 2, 0)
    cells = {(t.start_id, t.config) for t in trials}
    assert ("F5-a", "SvM") not in cells and ("F5-a", "MvM") not in cells
    assert ("F5-a", "MvS") in cells and ("F5-a", "SvS") in cells
    assert all((("F5-c", c) in cells) for c in ("SvS", "MvS", "SvM", "MvM"))
    assert sum(1 for t in trials if (t.start_id, t.config) == ("F5-c", "SvM")) == 2   # trials
    assert [t.trial for t in trials if (t.start_id, t.config) == ("F5-c", "SvM")] == [0, 1]


def test_mvm_is_flagged_test_only_and_refused_on_the_heldout_split(capsys):
    trials = suite.plan_trials(tiny_scenarios(), ["F5"], ["MvM"], 1, 0)
    assert all(t.test_only for t in trials)
    assert cli.main(["--dry-run", "--split", "heldout", "--configs", "MvM"]) == 2


def test_policy_seats_use_the_shipped_weights_and_record_their_hash(tmp_path):
    code = cli.main(["--dry-run", "--scenarios", "F5", "--configs", "MvS,SvM", "--trials", "1",
                     "--max-frames", "120", "--out", str(tmp_path)])
    assert code == 0
    rows = json.loads((tmp_path / "results.json").read_text())["rows"]
    c = next(r for r in rows if r["start_id"] == "F5-c" and r["config"] == "MvS")
    d = next(r for r in rows if r["start_id"] == "F5-c" and r["config"] == "SvM")
    assert c["controllers"]["A"]["kind"] == "policy" and c["controllers"]["B"]["kind"] == "scripted"
    assert c["controllers"]["A"]["weights_sha256"] == SHIPPED_SHA256
    assert d["controllers"]["B"]["kind"] == "policy" and d["controllers"]["A"]["kind"] == "scripted"
    assert d["controllers"]["B"]["weights_sha256"] == SHIPPED_SHA256
    assert c["controllers"]["B"]["weights_sha256"] is None
    assert all(r["aborted"] and r["abort_reason"] == "max_frames" for r in rows)      # the cap


def test_a_busy_controller_is_a_harness_error_not_a_quiet_result(tmp_path):
    class Slow:
        kind, name = "policy", "slow"

        def decide(self, observation, legal):
            time.sleep(0.25)
            return "WAIT"

    scenarios = tiny_scenarios(60)
    [trial] = [t for t in suite.plan_trials(scenarios, ["D1"], ["MvS"], 1, 0,
                                            policy_factory=Slow) if t.start_id == "D1-a"]
    row = suite.run_trial(trial, tmp_path, seed_key=suite.DRY_RUN_KEY, key_id="k", run_id="r",
                          git={"commit": "0" * 40, "dirty": False}, dry_run=True,
                          limits=VersusLimits(timeout_s=0.05))
    assert row["seats"]["A"]["busy"] > 0
    assert row["harness_error"] is True and row["aborted"] is True
    assert row["abort_reason"] == "harness_error:busy"


def test_an_exception_in_a_trial_is_a_reported_aborted_row(tmp_path):
    class Boom:
        kind, name = "policy", "boom"

        def __init__(self):
            raise RuntimeError("cannot build")

    scenarios = tiny_scenarios(60)
    [trial] = [t for t in suite.plan_trials(scenarios, ["D1"], ["MvS"], 1, 0,
                                            policy_factory=Boom) if t.start_id == "D1-a"]
    row = suite.run_trial(trial, tmp_path, seed_key=suite.DRY_RUN_KEY, key_id="k", run_id="r",
                          git={"commit": "0" * 40, "dirty": False}, dry_run=True)
    assert row["aborted"] is True and "cannot build" in row["error"]
    assert row["abort_reason"] == "exception" and row["success"] is None


# --- the secret seed key ----------------------------------------------------------------------------
def test_make_seed_key_writes_32_random_bytes_privately_and_never_overwrites(tmp_path):
    path = tmp_path / "seed.key"
    assert cli.main(["--make-seed-key", str(path)]) == 0
    text = path.read_text().strip()
    assert len(bytes.fromhex(text)) == 32
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
    assert cli.main(["--make-seed-key", str(path)]) == 2
    other = tmp_path / "second.key"
    cli.main(["--make-seed-key", str(other)])
    assert other.read_text() != path.read_text()


def test_a_real_run_needs_a_seed_key_and_a_weak_key_is_refused(tmp_path):
    assert cli.main(["--scenarios", "D1", "--configs", "SvS", "--out", str(tmp_path / "o")]) == 2
    weak = tmp_path / "weak.key"
    weak.write_text("abcd\n")
    assert cli.main(["--scenarios", "D1", "--configs", "SvS", "--seed-key-file", str(weak),
                     "--out", str(tmp_path / "o")]) == 2


def test_the_seed_key_never_reaches_a_result_or_a_trace(tmp_path):
    key_path = tmp_path / "seed.key"
    cli.main(["--make-seed-key", str(key_path)])
    key_hex = key_path.read_text().strip()
    out = tmp_path / "run"
    assert cli.main(["--scenarios", "D1", "--configs", "SvS", "--trials", "1",
                     "--max-frames", "60", "--seed-key-file", str(key_path),
                     "--out", str(out)]) == 0
    data = json.loads((out / "results.json").read_text())
    assert data["run"]["dry_run"] is False
    assert data["run"]["seed_key_id"] != suite.DRY_RUN_KEY_ID and len(data["run"]["seed_key_id"]) == 8
    for path in out.rglob("*"):
        if path.is_file():
            assert key_hex not in path.read_text() and key_hex[:20] not in path.read_text()


# --- the held-out split from the CLI -----------------------------------------------------------------
def test_heldout_dry_run_uses_wait_seats_checks_the_hash_and_claims_nothing(tmp_path, monkeypatch):
    ledger = tmp_path / "ledger.jsonl"
    monkeypatch.setattr(manifest, "LEDGER_PATH", ledger)
    out = tmp_path / "h"
    assert cli.main(["--dry-run", "--split", "heldout", "--trials", "1", "--max-frames", "90",
                     "--out", str(out)]) == 0
    data = json.loads((out / "results.json").read_text())
    assert data["run"]["held_out_dry_run_wait_seats"] is True
    assert data["run"]["scenario_file_sha256"]["heldout"] == manifest.HELDOUT_SHA256
    assert [r["start_id"] for r in data["rows"]] == ["H6-1", "H6-2", "H6-3", "H6-4"]
    for r in data["rows"]:
        assert ROW_KEYS <= set(r) and r["split"] == "heldout"
        assert r["controllers"]["A"]["kind"] == "fallback" == r["controllers"]["B"]["kind"]
        assert r["success"] is None and r["success_reason"] == "outcome_only"
    assert not ledger.exists()


def test_a_heldout_dry_run_refuses_a_policy_seat(tmp_path):
    assert cli.main(["--dry-run", "--split", "heldout", "--configs", "MvS",
                     "--out", str(tmp_path)]) == 2


def test_the_cli_refuses_a_heldout_file_whose_hash_changed(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(manifest, "HELDOUT_SHA256", "0" * 64)
    assert cli.main(["--dry-run", "--split", "heldout", "--out", str(tmp_path)]) == 2
    assert "hash" in capsys.readouterr().err
    assert not (tmp_path / "results.json").exists()


def test_a_real_heldout_run_is_claimed_once_per_frozen_policy(tmp_path, monkeypatch):
    ledger = tmp_path / "ledger.jsonl"
    monkeypatch.setattr(manifest, "LEDGER_PATH", ledger)
    key = tmp_path / "seed.key"
    cli.main(["--make-seed-key", str(key)])
    args = ["--split", "heldout", "--configs", "SvS", "--trials", "1", "--max-frames", "30",
            "--seed-key-file", str(key)]
    assert cli.main([*args, "--out", str(tmp_path / "r1")]) == 0
    assert len(manifest.read_ledger(ledger)) == 1
    assert cli.main([*args, "--out", str(tmp_path / "r2")]) == 2             # same frozen policy
    assert len(manifest.read_ledger(ledger)) == 1
    assert not (tmp_path / "r2" / "results.json").exists()


def test_list_prints_the_splits_scenarios(capsys):
    assert cli.main(["--list"]) == 0
    assert "D1" in capsys.readouterr().out
    assert cli.main(["--list", "--split", "heldout"]) == 0
    assert "H6" in capsys.readouterr().out
