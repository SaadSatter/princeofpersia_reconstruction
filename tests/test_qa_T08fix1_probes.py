"""QA probes for T08-fix1 (Gate 1). Independent of the Tech Lead's tests.

No policy runs on H6, the real ledger is never written (a temp ledger is patched in
or a throwaway git repository is used), no network.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from evaluation import analysis, manifest, monitors as M, spec, suite
from pop import arena
from tools.eval import run_versus_suite as cli
from tools.rl.env import TUNING_STARTS

ROOT = Path(__file__).resolve().parent.parent
FIRST_FREEZE_SHA = "44da40eca7a5606a9778cd3dca9756a34eb3962d3143a1304247ef2c92070847"
NEW_SHA = "d013152a84aed5d6ddf189a306e1dfa66f8b178a68dde2f6d5039684e82a5266"


def _h6():
    return json.loads((ROOT / "evaluation/heldout/H6.json").read_text())["scenarios"][0]["starts"]


def _tuning_raw():
    return json.loads((ROOT / "evaluation/scenarios/tuning.json").read_text())["scenarios"]


def H(s):
    return hashlib.sha256(s.encode()).hexdigest()


# --- the freeze: hash in all places, first four starts untouched ----------------------------------
def test_new_hash_is_the_file_hash_the_constant_the_readme_and_the_protocol():
    data = (ROOT / "evaluation/heldout/H6.json").read_bytes()
    assert hashlib.sha256(data).hexdigest() == NEW_SHA == manifest.HELDOUT_SHA256
    assert NEW_SHA in (ROOT / "evaluation/heldout/README.md").read_text()
    assert NEW_SHA in (ROOT / "docs/final/evaluation/PROTOCOL.md").read_text()
    assert len(_h6()) == 8


def test_h6_1_to_h6_4_are_byte_identical_to_the_first_freeze():
    old = subprocess.run(["git", "show", "059aea5:evaluation/heldout/H6.json"], cwd=ROOT,
                         capture_output=True)
    if old.returncode != 0:
        pytest.skip("history for 059aea5 is not available in this checkout")
    assert hashlib.sha256(old.stdout).hexdigest() == FIRST_FREEZE_SHA
    old_starts = json.loads(old.stdout)["scenarios"][0]["starts"]
    assert _h6()[:4] == old_starts
    assert [s["id"] for s in _h6()] == [f"H6-{i}" for i in range(1, 9)]


# --- the rule, re-implemented here from the PROTOCOL text only ------------------------------------
def _rule_starts():
    used = {tuple(s[:3]) for pair in TUNING_STARTS for s in pair}
    used |= {tuple(v[:3]) for v in arena.STARTS.values()}
    posts = {(g[0], g[1], tuple(g[2])) for g in arena.GUARD_POSTS.values()}
    for sc in _tuning_raw():
        for st in sc["starts"]:
            used |= {tuple(r[:3]) for r in st["rivals"].values()}
            posts |= {(g[0], g[1], tuple(g[2])) for g in st["guards"].values()}
    for st in _h6()[:4]:
        used |= {tuple(r[:3]) for r in st["rivals"].values()}
        posts |= {(g[0], g[1], tuple(g[2])) for g in st["guards"].values()}
    cells = sorted(((r, 2, c) for r in range(1, 7) for c in range(10)
                    if spec._floor_ok(r, 2, c) and (r, 2, c) not in used),
                   key=lambda x: H("h6x|cell|%d|%d|%d" % x))
    taken, out = set(), []
    for k in (5, 6, 7, 8):
        a = next(c for c in cells if c not in taken)
        taken.add(a)
        b = next(c for c in cells if c not in taken and c[0] != a[0])
        taken.add(b)
        cands = []
        for r in range(1, 7):
            for w in (2, 3, 4):
                for c0 in range(0, 11 - w):
                    c1 = c0 + w - 1
                    t = (r, 2, (c0, c1))
                    if t in posts or not all(spec._floor_ok(r, 2, c) for c in range(c0, c1 + 1)):
                        continue
                    if any(cl[0] == r and c0 <= cl[2] <= c1 for cl in (a, b)):
                        continue
                    cands.append(t)
        cands.sort(key=lambda p: H("h6x|post|%d|%d|%d" % (p[0], p[2][0], p[2][1])))
        g1 = cands[0]
        g2 = next(p for p in cands if p[0] != g1[0])
        posts |= {g1, g2}

        def face(p):
            return 1 if int(H("h6x|face|%d|%d|%d" % (p[0], p[2][0], p[2][1]))[:2], 16) % 2 == 0 else -1
        out.append({"id": f"H6-{k}",
                    "rivals": {"A": [*a, 1 if a[2] <= 4 else -1], "B": [*b, 1 if b[2] <= 4 else -1]},
                    "hearts": {"A": 3, "B": 3}, "disguised": {"A": False, "B": False},
                    "guards": {f"h6{k}-g1": [g1[0], 2, list(g1[2]), face(g1)],
                               f"h6{k}-g2": [g2[0], 2, list(g2[2]), face(g2)]}})
    return out


def test_an_independent_reading_of_the_written_rule_reproduces_h6_5_to_h6_8_exactly():
    assert _rule_starts() == _h6()[4:]


def test_the_rule_commit_precedes_the_commit_that_adds_the_starts():
    r = subprocess.run(["git", "merge-base", "--is-ancestor", "1f6fe1e", "632fc95"], cwd=ROOT)
    if r.returncode not in (0, 1):
        pytest.skip("history not available")
    assert r.returncode == 0


# --- disjointness, checked by a different route -------------------------------------------------------
def test_new_starts_share_no_cell_with_any_training_or_tuning_or_default_start():
    banned = {tuple(s[:3]) for pair in TUNING_STARTS for s in pair}
    banned |= {tuple(v[:3]) for v in arena.STARTS.values()}
    for sc in _tuning_raw():
        for st in sc["starts"]:
            banned |= {tuple(r[:3]) for r in st["rivals"].values()}
    for st in _h6()[:4]:
        banned |= {tuple(r[:3]) for r in st["rivals"].values()}
    new_cells = [tuple(r[:3]) for st in _h6()[4:] for r in st["rivals"].values()]
    assert len(new_cells) == len(set(new_cells)) == 8
    assert not set(new_cells) & banned
    for st in _h6():
        assert st["rivals"]["A"][0] != st["rivals"]["B"][0]


def test_no_h6_post_tuple_equals_a_default_or_tuning_post_and_none_repeat():
    known = {(g[0], g[1], tuple(g[2])) for g in arena.GUARD_POSTS.values()}
    for sc in _tuning_raw():
        for st in sc["starts"]:
            known |= {(g[0], g[1], tuple(g[2])) for g in st["guards"].values()}
    mine = [(g[0], g[1], tuple(g[2])) for st in _h6() for g in st["guards"].values()]
    assert len(mine) == len(set(mine)) == 16
    assert not set(mine) & known


def test_no_h6_configuration_equals_a_tuning_configuration_either_seat_order():
    def cfg(st):
        r = {k: tuple(v) for k, v in st["rivals"].items()}
        g = frozenset((v[0], v[1], tuple(v[2]), v[3]) for v in st["guards"].values())
        return (r["A"], r["B"], g), (r["B"], r["A"], g)
    tuning = {c for sc in _tuning_raw() for st in sc["starts"] for c in cfg(st)}
    for st in _h6():
        assert not set(cfg(st)) & tuning


# --- #64: bypass attempts on the dirty-tree check, in a throwaway repository ---------------------
def _git(cwd, *a):
    subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True,
                   env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                        "GIT_COMMITTER_EMAIL": "t@t", "HOME": str(cwd),
                        "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"})


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "r"
    for d in ("evaluation/heldout", "tools/eval", "agents", "pop"):
        (root / d).mkdir(parents=True)
        (root / d / "m.py").write_text("x=1\n")
    (root / "evaluation/heldout/ledger.jsonl").write_text("")
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "i")
    return root


@pytest.mark.parametrize("rel", [
    "evaluation/heldout/ledger.jsonl.bak", "evaluation/heldout/ledger2.jsonl",
    "evaluation/heldout/sub/ledger.jsonl", "evaluation/new.py", "tools/eval/new.py",
    "tools/eval/dir with space/ü.py", "evaluation/heldout/refusals.jsonl.old"])
def test_untracked_look_alikes_and_odd_names_under_the_evaluator_dirs_make_the_tree_dirty(repo, rel):
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("x\n")
    assert suite.git_state(repo)["dirty"] is True


def test_staged_deleted_and_renamed_files_are_dirty_and_an_edited_ledger_is_not(repo):
    (repo / "evaluation/heldout/ledger.jsonl").write_text("{}\n")
    assert suite.git_state(repo)["dirty"] is False          # by design: the run writes it
    _git(repo, "mv", "pop/m.py", "pop/n.py")
    assert suite.git_state(repo)["dirty"] is True
    _git(repo, "reset", "-q", "--hard")
    (repo / "evaluation/m.py").unlink()
    assert suite.git_state(repo)["dirty"] is True


def test_known_gap_untracked_code_outside_the_two_evaluator_dirs_is_not_counted(repo):
    """By the brief (untracked under evaluation/ and tools/eval/ only) this is allowed, but a
    new untracked file under agents/ or pop/ is code a run can use. Recorded as finding F-2."""
    (repo / "agents/new_policy.py").write_text("x=1\n")
    assert suite.git_state(repo)["dirty"] is False


def test_known_gap_a_gitignored_or_skip_worktree_file_hides_a_change(repo):
    """Same: .gitignore'd files under evaluation/ never show. Recorded as finding F-2."""
    (repo / ".gitignore").write_text("evaluation/hidden.py\n")
    _git(repo, "add", ".gitignore")
    _git(repo, "commit", "-q", "-m", "ig")
    (repo / "evaluation/hidden.py").write_text("x\n")
    assert suite.git_state(repo)["dirty"] is False


# --- #64 through the CLI: the key is only (weights, commit) ---------------------------------------
@pytest.fixture
def cli_env(tmp_path, monkeypatch):
    ledger = tmp_path / "ledger.jsonl"
    monkeypatch.setattr(manifest, "LEDGER_PATH", ledger)
    key = tmp_path / "seed.key"
    cli.main(["--make-seed-key", str(key)])
    st = {"g": {"commit": "a" * 40, "dirty": False}}
    monkeypatch.setattr(suite, "git_state", lambda *a, **k: dict(st["g"]))

    def run(name, *extra):
        return cli.main(["--split", "heldout", "--trials", "1", "--max-frames", "20",
                         "--seed-key-file", str(key), "--out", str(tmp_path / name), *extra])
    return ledger, st, run, tmp_path


def test_a_second_run_cannot_slip_through_by_changing_configs_scenario_trials_seed_or_key(
        cli_env):
    ledger, st, run, tmp = cli_env
    assert run("a", "--configs", "SvS") == 0
    assert run("b", "--configs", "SvS", "--seed-base", "99") == 2
    assert run("c", "--configs", "SvS", "--scenarios", "H6") == 2
    assert run("d", "--configs", "SvS", "--trials", "2") == 2
    assert len(manifest.read_ledger(ledger)) == 1
    assert len(manifest.read_refusals(ledger)) == 3
    assert not (tmp / "b").exists() or not any((tmp / "b").glob("*.json"))


def test_a_refusal_leaves_nothing_in_the_ledger_and_a_clean_run_after_it_still_claims(cli_env):
    ledger, st, run, tmp = cli_env
    st["g"] = {"commit": "a" * 40, "dirty": True}
    assert run("a", "--configs", "SvS") == 2
    st["g"] = {"commit": "unknown", "dirty": None}
    assert run("b", "--configs", "SvS") == 2
    assert not ledger.exists()
    st["g"] = {"commit": "a" * 40, "dirty": False}
    assert run("c", "--configs", "SvS") == 0
    assert len(manifest.read_ledger(ledger)) == 1
    assert [r["status"] for r in manifest.read_refusals(ledger)] == ["refused", "refused"]


def test_dirty_none_is_refused_even_with_a_real_looking_commit(cli_env):
    ledger, st, run, tmp = cli_env
    st["g"] = {"commit": "a" * 40, "dirty": None}
    assert run("a", "--configs", "SvS") == 2 and not ledger.exists()


# --- F-1 and the "struck by room presence" choice ---------------------------------------------------
def _r(room, col=2, disguised=False):
    return {"room": room, "row": 2, "col": col, "hp": 3, "posture": "standing", "disguised": disguised}


def _g(room=4, downed=False, uniform=True, knocked=0):
    return {"room": room, "row": 2, "col": 5, "downed": downed, "uniform": uniform,
            "knocked_down": knocked, "target": None}


def _s(a, b, g):
    return {"frames": 0, "terminal": None, "rivals": {"A": a, "B": b}, "guards": g, "suspicion": {}}


def test_d1_credits_a_guard_the_agent_fought_in_its_room_and_not_one_downed_elsewhere():
    ok = M.DisguiseMonitor()
    for i, s in enumerate([_s(_r(4), _r(1), {"g": _g()}),
                           _s(_r(4), _r(1), {"g": _g(knocked=5)}),
                           _s(_r(4), _r(1), {"g": _g(downed=True)}),
                           _s(_r(4, disguised=True), _r(1), {"g": _g(downed=True, uniform=False)})], 1):
        ok.observe(i, s)
    assert ok.result()["success"] is True
    assert ok.result()["metrics"]["credited_guards"] == ["g"]
    # the other rival knocks it down in room 4 while the agent is in room 3; the agent then enters
    bad = M.DisguiseMonitor()
    for i, s in enumerate([_s(_r(3), _r(4), {"g": _g()}),
                           _s(_r(3), _r(4), {"g": _g(knocked=5)}),
                           _s(_r(3), _r(5), {"g": _g(downed=True)}),
                           _s(_r(4), _r(5), {"g": _g(downed=True)}),
                           _s(_r(4, disguised=True), _r(5), {"g": _g(downed=True, uniform=False)})], 1):
        bad.observe(i, s)
    assert bad.result()["success"] is False


def test_known_gap_a_guard_downed_by_a_trap_in_the_agents_room_is_credited_to_the_agent():
    """Room presence cannot tell a strike from a trap or a bystander fall. Documented
    approximation (no striker field); recorded as a note."""
    m = M.DisguiseMonitor()
    for i, s in enumerate([_s(_r(4, col=0), _r(1), {"g": _g(downed=True)}),
                           _s(_r(4, disguised=True), _r(1), {"g": _g(downed=True, uniform=False)})], 1):
        m.observe(i, s)
    assert m.result()["success"] is True


# --- #76 B2: the disguise must last --------------------------------------------------------------------
def _b2(disguise_by_frame):
    m = M.BlendMonitor("A")
    for i, d in enumerate(disguise_by_frame, 1):
        m.observe(i, _s(_r(1, col=2 + (i % 3), disguised=d), _r(2), {}))
    return m.result()


def test_b2_needs_the_disguise_on_the_last_frame_but_a_regained_one_counts():
    assert _b2([True] * 5)["success"] is True
    lost = _b2([True, True, False, False])
    assert lost["success"] is False and lost["reason"] == "disguise_lost"
    assert _b2([True, False, True, True])["success"] is True   # the end state decides (documented)


def test_b2_with_no_frames_observed_is_not_a_success():
    assert M.BlendMonitor("A").result()["success"] is False


# --- #65: mirrored starts are exact seat swaps and run only SvS/SvM -----------------------------------
def test_each_mirror_is_the_exact_seat_swap_of_its_original():
    for sc in _tuning_raw():
        by = {s["id"]: s for s in sc["starts"]}
        for sid, m in by.items():
            if not sid.endswith("-B"):
                continue
            o = by[sid[:-2]]
            assert m["subject"] == "B" and o.get("subject", "A") == "A"
            assert m["rivals"]["A"] == o["rivals"]["B"] and m["rivals"]["B"] == o["rivals"]["A"]
            assert m["hearts"]["A"] == o["hearts"]["B"] and m["hearts"]["B"] == o["hearts"]["A"]
            assert m["disguised"]["A"] == o["disguised"]["B"] and m["disguised"]["B"] == o["disguised"]["A"]
            assert m["guards"] == o["guards"]
            assert m["other_controller"] == o["other_controller"]


def test_mirrored_starts_plan_only_the_configurations_whose_forced_seat_is_scripted():
    scs = manifest.load_tuning()
    trials = suite.plan_trials(scs, ["D1", "B2", "I3", "F5"], ["SvS", "MvS", "SvM", "MvM"], 1, 0)
    for t in trials:
        if t.start_id.endswith("-B"):
            assert t.config in ("SvS", "SvM"), t.row_id
    assert not any(t.config == "MvM" and t.scenario.split == "heldout" for t in trials)


def test_per_seat_analysis_never_pools_the_two_seats():
    rows = []
    for seat, start, ok in (("A", "D1-a", True), ("B", "D1-a-B", False)):
        other = "B" if seat == "A" else "A"
        rows.append({"scenario": "D1", "scenario_kind": "disguise", "start_id": start,
                     "config": "SvS", "trial": 0, "subject_seat": seat, "dry_run": False,
                     "aborted": False, "abort_reason": None, "success": ok,
                     "forced_controllers": {}, "row_id": f"D1/{start}/SvS/t0",
                     "controllers": {seat: {"kind": "scripted", "name": "versus-baseline"},
                                     other: {"kind": "scripted", "name": "versus-baseline"}}})
    out = analysis.success_by_scenario(rows)
    assert sorted((r["subject_seat"], r["k"], r["n"]) for r in out) == [("A", 1, 1), ("B", 0, 1)]


# --- F-2 / F-4 ---------------------------------------------------------------------------------------------
def test_replay_without_split_flag_reads_the_split_from_meta_for_a_heldout_trace(tmp_path, capsys):
    d = tmp_path / "t"
    d.mkdir()
    (d / "meta.json").write_text(json.dumps({"split": "weird"}))
    assert cli.main(["--replay", str(d)]) == 2
    (d / "meta.json").write_text("{not json")
    assert cli.main(["--replay", str(d)]) == 2
    assert cli.main(["--replay", str(tmp_path / "missing")]) == 2
