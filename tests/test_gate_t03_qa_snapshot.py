"""T03 QA (Gate 1): checks on the official-repository snapshot.

Set OFFICIAL_CLONE to a checkout of final-saadsatter at branch g23-migration;
without it these tests skip (CI never touches the network or that clone).
"""
import os
import subprocess
from pathlib import Path

import pytest

CLONE = os.environ.get("OFFICIAL_CLONE")
pytestmark = pytest.mark.skipif(not CLONE, reason="OFFICIAL_CLONE not set")


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=True).stdout


def _tracked():
    out = _git(CLONE, "ls-files", "-z")
    return [p for p in out.decode().split("\0") if p]


def test_only_manifest_from_assets_original():
    assert [p for p in _tracked() if "assets/original" in p] == ["game/assets/original/MANIFEST.tsv"]


def test_no_level_data_or_raw_transcripts():
    bad = [p for p in _tracked() if p.lower().endswith((".dat", ".pem", ".env"))
           or "conversation" in p.lower() or "/vendor/" in p or "data/levels" in p]
    assert bad == []


def test_no_large_files():
    big = [p for p in _tracked() if (Path(CLONE) / p).stat().st_size > 5_000_000]
    assert big == []


def test_template_root_files_preserved():
    # 32fa606 is the template's initial commit
    changed = _git(CLONE, "diff", "--name-only", "32fa606", "HEAD", "--",
                   ".", ":!game", ":!agent-team", ":!.claude", ":!.agents").decode().split()
    assert sorted(changed) == [".github/workflows/final.yml", "README.md"]


def test_graded_handoff_identical_to_draft():
    repo = Path(__file__).resolve().parents[1]
    ref = _git(repo, "show", "7c4fc1d:docs/final/orchestration/handoff-drafts/2026-11-24-qa-to-tech.md")
    assert (Path(CLONE) / "agent-team/handoffs/2026-11-24-qa-to-tech.md").read_bytes() == ref
