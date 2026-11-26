"""T08-fix1 item 1 (decision #64): the run-once key is (weights SHA-256, engine commit).

A second held-out run for the same pair is refused; the same weights on a new
commit are allowed, and both lines are listed. A real held-out run is refused on
an unknown commit or a dirty tree (untracked files under `evaluation/` and
`tools/eval/` count). Every run, claimed or refused, is recorded. No policy runs
on H6 here (scripted seats, a 30-frame cap) and the real ledger is never written:
every test patches in a temp ledger.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from evaluation import manifest, suite
from tools.eval import run_versus_suite as cli

CLEAN = {"commit": "a" * 40, "dirty": False}


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                   env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                        "GIT_COMMITTER_EMAIL": "t@t", "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
                        "HOME": str(cwd)})


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    (root / "evaluation" / "heldout").mkdir(parents=True)
    (root / "tools" / "eval").mkdir(parents=True)
    (root / "evaluation" / "mod.py").write_text("x = 1\n")
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "init")
    return root


# --- the key ---------------------------------------------------------------------------------------
def test_the_same_weights_on_the_same_commit_are_refused_and_both_names_the_pair(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    manifest.claim_heldout_run("w1", {"run_id": "r1", "commit": "c1"}, ledger)
    with pytest.raises(manifest.FreezeError, match="w1|already run"):
        manifest.claim_heldout_run("w1", {"run_id": "r2", "commit": "c1"}, ledger)


def test_the_same_weights_on_a_new_commit_are_allowed_and_both_runs_are_listed(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    manifest.claim_heldout_run("w1", {"run_id": "r1", "commit": "c1"}, ledger)
    manifest.claim_heldout_run("w1", {"run_id": "r2", "commit": "c2"}, ledger)
    rows = manifest.read_ledger(ledger)
    assert [(r["policy_key"], r["commit"], r["run_id"]) for r in rows] == [
        ("w1", "c1", "r1"), ("w1", "c2", "r2")]
    assert all(r["status"] == "claimed" for r in rows)


def test_new_weights_on_the_same_commit_are_allowed(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    manifest.claim_heldout_run("w1", {"run_id": "r1", "commit": "c1"}, ledger)
    manifest.claim_heldout_run("w2", {"run_id": "r2", "commit": "c1"}, ledger)
    assert len(manifest.read_ledger(ledger)) == 2


def test_a_claim_with_no_policy_key_is_still_refused(tmp_path):
    with pytest.raises(manifest.FreezeError):
        manifest.claim_heldout_run("", {"commit": "c1"}, tmp_path / "l.jsonl")


def test_a_refusal_is_recorded_beside_the_ledger_and_does_not_count_as_a_run(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    manifest.claim_heldout_run("w1", {"run_id": "r1", "commit": "c1"}, ledger)
    row = manifest.record_refusal("w1", {"run_id": "r2", "commit": "c1"}, "same pair", ledger)
    assert row["status"] == "refused" and row["reason"] == "same pair"
    refusals = manifest.read_refusals(ledger)
    assert [r["run_id"] for r in refusals] == ["r2"]
    assert [r["run_id"] for r in manifest.read_ledger(ledger)] == ["r1"]


# --- unknown commit and dirty tree --------------------------------------------------------------------
@pytest.mark.parametrize("git_info", [{"commit": "unknown", "dirty": None},
                                      {"commit": "", "dirty": False},
                                      {"commit": "a" * 40, "dirty": True},
                                      {"commit": "a" * 40, "dirty": None}])
def test_an_unknown_commit_or_a_dirty_or_unknown_tree_is_refused(git_info):
    with pytest.raises(manifest.FreezeError):
        manifest.require_known_clean_tree(git_info)


def test_a_known_commit_on_a_clean_tree_passes():
    manifest.require_known_clean_tree(CLEAN)


def test_git_state_counts_untracked_files_under_evaluation_and_tools_eval(repo):
    assert suite.git_state(repo) == {"commit": suite.git_state(repo)["commit"], "dirty": False}
    assert len(suite.git_state(repo)["commit"]) == 40
    (repo / "evaluation" / "new_monitor.py").write_text("y = 2\n")
    assert suite.git_state(repo)["dirty"] is True
    (repo / "evaluation" / "new_monitor.py").unlink()
    (repo / "tools" / "eval" / "helper.py").write_text("z = 3\n")
    assert suite.git_state(repo)["dirty"] is True


def test_git_state_still_counts_a_modified_tracked_file_and_ignores_unrelated_untracked_files(repo):
    (repo / "notes.txt").write_text("not evaluator code\n")
    assert suite.git_state(repo)["dirty"] is False
    (repo / "evaluation" / "mod.py").write_text("x = 2\n")
    assert suite.git_state(repo)["dirty"] is True


def test_the_ledger_files_themselves_do_not_make_the_tree_dirty(repo):
    (repo / "evaluation" / "heldout" / "ledger.jsonl").write_text("{}\n")
    (repo / "evaluation" / "heldout" / "refusals.jsonl").write_text("{}\n")
    assert suite.git_state(repo)["dirty"] is False


def test_outside_a_repository_the_commit_is_unknown(tmp_path):
    state = suite.git_state(tmp_path)
    assert state["commit"] == "unknown"


# --- the CLI ---------------------------------------------------------------------------------------------
@pytest.fixture
def cli_env(tmp_path, monkeypatch):
    ledger = tmp_path / "ledger.jsonl"
    monkeypatch.setattr(manifest, "LEDGER_PATH", ledger)
    key = tmp_path / "seed.key"
    cli.main(["--make-seed-key", str(key)])
    state = {"git": dict(CLEAN)}
    monkeypatch.setattr(suite, "git_state", lambda *a, **k: dict(state["git"]))

    def run(name):
        return cli.main(["--split", "heldout", "--configs", "SvS", "--trials", "1",
                         "--max-frames", "30", "--seed-key-file", str(key),
                         "--out", str(tmp_path / name)])
    return {"ledger": ledger, "state": state, "run": run, "tmp": tmp_path}


def test_cli_second_run_of_the_same_pair_is_refused_and_recorded(cli_env):
    assert cli_env["run"]("r1") == 0
    assert cli_env["run"]("r2") == 2
    ledger = manifest.read_ledger(cli_env["ledger"])
    assert len(ledger) == 1 and ledger[0]["commit"] == CLEAN["commit"]
    refusals = manifest.read_refusals(cli_env["ledger"])
    assert len(refusals) == 1 and refusals[0]["status"] == "refused"
    assert refusals[0]["commit"] == CLEAN["commit"]
    assert not (cli_env["tmp"] / "r2" / "results.json").exists()


def test_cli_the_same_policy_on_a_new_commit_runs_and_both_lines_are_listed(cli_env):
    assert cli_env["run"]("r1") == 0
    cli_env["state"]["git"] = {"commit": "b" * 40, "dirty": False}
    assert cli_env["run"]("r2") == 0
    ledger = manifest.read_ledger(cli_env["ledger"])
    assert [r["commit"] for r in ledger] == ["a" * 40, "b" * 40]
    assert ledger[0]["policy_key"] == ledger[1]["policy_key"]
    assert manifest.read_refusals(cli_env["ledger"]) == []


@pytest.mark.parametrize("bad", [{"commit": "unknown", "dirty": None},
                                 {"commit": "a" * 40, "dirty": True}])
def test_cli_refuses_a_real_heldout_run_on_an_unknown_commit_or_a_dirty_tree(cli_env, bad):
    cli_env["state"]["git"] = bad
    assert cli_env["run"]("r1") == 2
    assert manifest.read_ledger(cli_env["ledger"]) == []
    assert not (cli_env["tmp"] / "r1" / "results.json").exists()
    [refusal] = manifest.read_refusals(cli_env["ledger"])
    assert refusal["status"] == "refused" and refusal["commit"] == bad["commit"]
    # and a clean tree can still run afterwards: the refusal claimed nothing
    cli_env["state"]["git"] = dict(CLEAN)
    assert cli_env["run"]("r2") == 0


def test_cli_a_dry_run_on_a_dirty_tree_is_not_refused_and_writes_no_ledger_line(cli_env):
    cli_env["state"]["git"] = {"commit": "unknown", "dirty": True}
    assert cli.main(["--dry-run", "--split", "heldout", "--trials", "1", "--max-frames", "30",
                     "--out", str(cli_env["tmp"] / "d")]) == 0
    assert not cli_env["ledger"].exists()
    assert not cli_env["ledger"].with_name("refusals.jsonl").exists()


def test_the_header_of_a_real_run_names_the_ledger_row(cli_env):
    assert cli_env["run"]("r1") == 0
    data = json.loads((cli_env["tmp"] / "r1" / "results.json").read_text())
    assert data["run"]["ledger"]["status"] == "claimed"
    assert data["run"]["ledger"]["commit"] == CLEAN["commit"]
