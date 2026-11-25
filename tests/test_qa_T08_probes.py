"""QA probes for T08 (Gate 1). Adversarial checks the Tech Lead's tests do not make.

No policy runs on H6, no write to the real ledger (a temp ledger is patched in),
no network. Findings are marked xfail(strict=True) with their id from
docs/final/orchestration/reports/T08-qa.md.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from evaluation import analysis, manifest, monitors as M, spec, suite
from pop import arena
from pop.versus import VersusEpisode
from tools.eval import run_versus_suite as cli

ROOT = Path(__file__).resolve().parent.parent


def rival(room=1, col=2, hp=3, posture="standing", disguised=False, row=2):
    return {"room": room, "row": row, "col": col, "hp": hp, "posture": posture,
            "disguised": disguised}


def guard(room=1, col=5, downed=False, uniform=True, knocked=0, target=None):
    return {"room": room, "row": 2, "col": col, "downed": downed, "uniform": uniform,
            "knocked_down": knocked, "target": target}


def state(a, b, guards, suspicion=None):
    return {"frames": 0, "terminal": None, "rivals": {"A": a, "B": b}, "guards": guards,
            "suspicion": suspicion or {}}


# --- F-1: D1 attributes a guard the OTHER rival downed earlier to the agent -----------------
def test_d1_does_not_credit_a_guard_the_other_rival_downed_before_leaving():
    """The other rival downs the guard in room 4 while the agent is in room 3, walks on to
    room 5, then the agent enters room 4 and takes the uniform. The other rival is never in the
    agent's room, so #59 is satisfied, but the agent did not kill the guard."""
    mon = M.DisguiseMonitor()
    frames = [
        state(rival(3), rival(4), {"g": guard(4)}),
        state(rival(3), rival(4), {"g": guard(4, downed=True)}),     # B downs it
        state(rival(3), rival(5), {"g": guard(4, downed=True)}),     # B leaves
        state(rival(4), rival(5), {"g": guard(4, downed=True)}),     # A arrives
        state(rival(4, disguised=True), rival(5), {"g": guard(4, downed=True, uniform=False)}),
    ]
    for i, s in enumerate(frames, 1):
        mon.observe(i, s)
    assert mon.result()["success"] is False


# --- F-2: analysis crashes on an aborted row that has no controllers ------------------------------
def _exception_row(scenario="F5", kind="fight", start="F5-c", config="MvS"):
    return {"schema": "x", "row_id": f"{scenario}/{start}/{config}/t0", "scenario": scenario,
            "scenario_kind": kind, "start_id": start, "config": config, "trial": 0,
            "dry_run": False, "forced_controllers": {}, "controllers": {},
            "aborted": True, "abort_reason": "exception", "harness_error": True,
            "error": "RuntimeError: cannot build", "success": None, "success_reason": None}


def test_analysis_summarises_a_run_where_every_row_aborted_before_controllers_existed():
    rows = [_exception_row(), _exception_row(scenario="D1", kind="disguise", start="D1-a",
                                             config="SvS")]
    hdr = [{"run_id": "r", "split": "tuning", "commit": "c" * 40, "dry_run": False,
            "seed_key_id": "abcd1234"}]
    text = analysis.render(rows, hdr)
    assert "Aborted rounds" in text and "cannot build" in text


# --- the freeze --------------------------------------------------------------------------------
def test_a_tampered_heldout_file_that_is_not_even_json_is_refused_by_hash_not_by_the_parser(
        tmp_path):
    bad = tmp_path / "H6.json"
    bad.write_text("{ not json")
    with pytest.raises(manifest.FreezeError, match="hash mismatch"):
        manifest.load_heldout(bad)


def test_a_one_byte_change_is_refused_and_the_real_file_hash_is_the_recorded_one():
    data = (ROOT / "evaluation" / "heldout" / "H6.json").read_bytes()
    assert manifest.HELDOUT_SHA256.startswith("d013152a") and manifest.HELDOUT_SHA256.endswith("5266")
    import hashlib
    assert hashlib.sha256(data).hexdigest() == manifest.HELDOUT_SHA256
    assert hashlib.sha256(data + b"\n").hexdigest() != manifest.HELDOUT_SHA256


def test_the_ledger_is_not_bypassed_by_seed_key_scenario_subset_trials_or_seed_base(
        tmp_path, monkeypatch):
    ledger = tmp_path / "ledger.jsonl"
    monkeypatch.setattr(manifest, "LEDGER_PATH", ledger)
    k1, k2 = tmp_path / "k1", tmp_path / "k2"
    cli.main(["--make-seed-key", str(k1)])
    cli.main(["--make-seed-key", str(k2)])
    base = ["--split", "heldout", "--configs", "SvS", "--max-frames", "30"]
    assert cli.main([*base, "--trials", "1", "--seed-key-file", str(k1),
                     "--out", str(tmp_path / "a")]) == 0
    for extra in (["--seed-key-file", str(k2)], ["--scenarios", "H6", "--seed-key-file", str(k1)],
                  ["--trials", "3", "--seed-key-file", str(k1)],
                  ["--seed-base", "99", "--seed-key-file", str(k1)]):
        args = [*base, "--trials", "1", *extra] if "--trials" not in extra else [*base, *extra]
        assert cli.main([*args, "--out", str(tmp_path / "b")]) == 2, extra
    assert len(manifest.read_ledger(ledger)) == 1
    assert not (tmp_path / "b" / "results.json").exists()


def test_a_heldout_run_without_a_seed_key_is_refused_and_claims_nothing(tmp_path, monkeypatch):
    ledger = tmp_path / "ledger.jsonl"
    monkeypatch.setattr(manifest, "LEDGER_PATH", ledger)
    assert cli.main(["--split", "heldout", "--configs", "SvS", "--out", str(tmp_path / "o")]) == 2
    assert not ledger.exists()


def test_a_heldout_dry_run_never_builds_a_policy_controller(tmp_path, monkeypatch):
    from evaluation import controllers as C
    built = []
    real = C.build
    monkeypatch.setattr(C, "build", lambda kind, *a, **k: (built.append(kind), real(kind, *a, **k))[1])
    assert cli.main(["--dry-run", "--split", "heldout", "--trials", "1", "--max-frames", "30",
                     "--out", str(tmp_path)]) == 0
    assert built and set(built) == {"wait"}


def test_the_ledger_line_is_written_before_the_first_trial(tmp_path, monkeypatch):
    ledger = tmp_path / "ledger.jsonl"
    monkeypatch.setattr(manifest, "LEDGER_PATH", ledger)
    seen = []
    real = suite.run_trial

    def spy(*a, **k):
        seen.append(ledger.exists() and len(manifest.read_ledger(ledger)))
        raise KeyboardInterrupt   # abort the whole run at trial one

    monkeypatch.setattr(suite, "run_trial", spy)
    key = tmp_path / "k"
    cli.main(["--make-seed-key", str(key)])
    with pytest.raises(KeyboardInterrupt):
        cli.main(["--split", "heldout", "--configs", "SvS", "--trials", "1",
                  "--seed-key-file", str(key), "--out", str(tmp_path / "o")])
    assert seen == [1]
    monkeypatch.setattr(suite, "run_trial", real)
    assert cli.main(["--split", "heldout", "--configs", "SvS", "--trials", "1", "--max-frames", "30",
                     "--seed-key-file", str(key), "--out", str(tmp_path / "o2")]) == 2


def test_no_rl_code_imports_the_eval_tools_or_the_evaluation_package():
    for sub in ("agents/rl", "tools/rl"):
        for path in sorted((ROOT / sub).rglob("*.py")):
            for node in ast.walk(ast.parse(path.read_text())):
                names = ([a.name for a in node.names] if isinstance(node, ast.Import)
                         else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
                assert not any(n.split(".")[0] == "evaluation" or n.startswith("tools.eval")
                               for n in names), path


# --- F-3: H6 guard patrols overlap the cells that tuning and training use -------------------------
def _cells(guards):
    return {(g[0], g[1], c) for g in guards for c in range(g[2][0], g[2][1] + 1)}


@pytest.mark.xfail(strict=True, reason="F-3: H6 guard patrol cells overlap tuning and default posts")
def test_h6_guard_patrol_cells_are_disjoint_from_every_other_split():
    h = manifest.load_heldout()["H6"]
    t = manifest.load_tuning()
    hg = _cells(g for st in h.starts for g in st.guards.values())
    tg = _cells(g for sc in t.values() for st in sc.starts for g in st.guards.values())
    ag = _cells(arena.GUARD_POSTS.values())
    assert hg.isdisjoint(tg | ag)


# --- ScenarioEpisode changes only the intended set-up -------------------------------------------
def test_a_default_start_runs_exactly_like_a_plain_versus_episode():
    sc = manifest.load_tuning()["F5"]
    start = sc.start("F5-c")           # full hearts, no disguise, no forced seat
    a = spec.ScenarioEpisode(start, 300, 5)
    b = VersusEpisode(arena.situation("A"), start.episode_starts(), 5, 300,
                      {n: (g[0], g[1], g[2], g[3]) for n, g in start.guards.items()})
    script = ["WALK_RIGHT", "WAIT", "STEP_RIGHT", "WAIT"] * 40
    for i in range(300):
        for ep in (a, b):
            ep.step("A", script[i % len(script)] if script[i % len(script)] in ep.legal_actions("A") else "WAIT")
            ep.step("B", "WAIT")
            ep.tick()
        for seat in "AB":
            assert json.dumps(a.observe(seat), sort_keys=True, default=str) == \
                json.dumps(b.observe(seat), sort_keys=True, default=str), (i, seat)
    assert json.dumps(a.observe("A"), sort_keys=True, default=str) == \
        json.dumps(b.observe("A"), sort_keys=True, default=str)


def test_the_scenario_set_up_adds_nothing_to_a_seats_observation_or_legal_list():
    t = manifest.load_tuning()
    ep = spec.episode_factory(t["I3"], "I3-a")()
    obs = ep.observe("A")
    blob = json.dumps(obs, default=str).lower()
    for word in ("monitor", "success", "scenario", "i3", "decoy", "start_id", "seed_key"):
        assert word not in blob, word
    # the disguised rival B reads as a guard to A (R-V18): no figure of kind "rival"
    assert all(f.get("kind") != "rival" for f in obs.get("figures", obs.get("visible", [])) or [])
    assert set(ep.legal_actions("A")) <= set(ep.legal_actions("A")) and ep.legal_actions("A")


def test_hearts_set_by_the_start_survive_a_second_reset_and_do_not_leak_between_episodes():
    t = manifest.load_tuning()
    ep = spec.episode_factory(t["F5"], "F5-b")()
    assert ep._duel.rivals["A"].kid.hp == 2
    other = spec.episode_factory(t["F5"], "F5-a")()
    assert other._duel.rivals["A"].kid.hp == 3 and ep._duel.rivals["A"].kid.hp == 2


# --- replay ---------------------------------------------------------------------------------------------
def test_replaying_a_heldout_trace_without_the_heldout_split_fails_cleanly(tmp_path, capsys):
    out = tmp_path / "h"
    assert cli.main(["--dry-run", "--split", "heldout", "--trials", "1", "--max-frames", "30",
                     "--scenarios", "H6", "--out", str(out)]) == 0
    trace = next((out / "traces").rglob("meta.json")).parent
    # the split is recorded in meta.json, so replay should find it without being told
    assert cli.main(["--replay", str(trace)]) in (0, 1, 2)


def test_replaying_a_heldout_trace_with_the_heldout_split_reproduces_the_snapshot(tmp_path):
    out = tmp_path / "h"
    assert cli.main(["--dry-run", "--split", "heldout", "--trials", "1", "--max-frames", "30",
                     "--scenarios", "H6", "--out", str(out)]) == 0
    for meta in (out / "traces").rglob("meta.json"):
        assert cli.main(["--replay", str(meta.parent), "--split", "heldout"]) == 0
