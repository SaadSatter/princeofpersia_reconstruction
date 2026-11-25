"""The held-out freeze (docs/final/evaluation/PROTOCOL.md; decisions #9 and #60).

`evaluation/heldout/H6.json` is OFF LIMITS to training, tuning and prompt or
reward design. Only `tools/eval/run_versus_suite.py --split heldout` reads it,
and only through `load_heldout`, which first checks the file's SHA-256 against
the constant below. The hash is recorded here, in the protocol, in
`evaluation/heldout/README.md` and in the commit that added the file. Changing
the file means a new hash, a new commit and a note in the protocol, and
invalidates any held-out result already reported.

Run-once rule (decision #64): `evaluation/heldout/ledger.jsonl` is append-only.
A held-out run writes its ledger line *before* the first trial (so an aborted run
still counts) and a second run for the same (weights SHA-256, engine commit) pair
is refused; the same weights on a new commit are allowed and both lines stay.
Refused attempts are written to `refusals.jsonl` beside it. A real run is also
refused on an unknown commit or a dirty tree.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from .spec import file_sha256, load_scenario_file

ROOT = Path(__file__).resolve().parent
HELDOUT_PATH = ROOT / "heldout" / "H6.json"
LEDGER_PATH = ROOT / "heldout" / "ledger.jsonl"
TUNING_PATH = ROOT / "scenarios" / "tuning.json"
# Re-frozen by T08-fix1 (decision #74): H6-5 to H6-8 added by the rule in PROTOCOL.md 3.1.
# The first freeze (four starts) was 44da40eca7a5606a9778cd3dca9756a34eb3962d3143a1304247ef2c92070847;
# it never ran, so no result is voided.
HELDOUT_SHA256 = "d013152a84aed5d6ddf189a306e1dfa66f8b178a68dde2f6d5039684e82a5266"


class FreezeError(RuntimeError):
    pass


def verify_heldout(path: Path = HELDOUT_PATH, expected: str | None = None) -> str:
    """The file's SHA-256, or FreezeError if it is missing or not the frozen one."""
    expected = HELDOUT_SHA256 if expected is None else expected
    try:
        actual = file_sha256(path)
    except OSError as exc:
        raise FreezeError(f"held-out file unreadable ({exc}); do not run without it") from exc
    if actual != expected:
        raise FreezeError(f"held-out file hash mismatch: expected {expected}, found {actual}. "
                          "The frozen set was edited; do not run it.")
    return actual


def load_heldout(path: Path = HELDOUT_PATH, expected: str | None = None):
    verify_heldout(path, expected)
    return load_scenario_file(path, "heldout")


def load_tuning():
    return load_scenario_file(TUNING_PATH, "tuning")


def read_ledger(path: Path | None = None) -> list[dict]:
    """The claimed runs (one JSON object per line, append only)."""
    return _read_lines(LEDGER_PATH if path is None else path)


def _read_lines(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def refusals_path(ledger: Path | None = None) -> Path:
    """Refused attempts live beside the ledger, not in it: only a claim uses up a run."""
    return (LEDGER_PATH if ledger is None else ledger).with_name("refusals.jsonl")


def read_refusals(ledger: Path | None = None) -> list[dict]:
    return _read_lines(refusals_path(ledger))


def require_known_clean_tree(git: dict) -> None:
    """A held-out result must name the engine it ran on (decision #64): refuse an unknown
    commit and a tree with uncommitted changes (`suite.git_state` counts untracked files
    under `evaluation/` and `tools/eval/`). `dirty` None means git could not say."""
    commit = git.get("commit")
    if not commit or commit == "unknown":
        raise FreezeError("a real held-out run needs a known engine commit (git says "
                          f"{commit!r}); run it from a git checkout")
    if git.get("dirty") is not False:
        raise FreezeError("a real held-out run needs a clean tree: commit or remove "
                          "uncommitted changes, including new files under evaluation/ and "
                          "tools/eval/ (decision #64)")


def claim_heldout_run(policy_key: str, info: dict, path: Path | None = None) -> dict:
    """Record a held-out run, or refuse a second one for the same (weights SHA-256,
    engine commit) pair (decision #64). The same weights on a new commit are allowed;
    both lines stay in the ledger. `policy_key` is the weights SHA-256, or the scripted
    source hash for scripted-only runs; the commit comes from `info["commit"]`."""
    path = LEDGER_PATH if path is None else path
    if not policy_key:
        raise FreezeError("a held-out run needs a frozen policy key")
    commit = info.get("commit")
    for row in read_ledger(path):
        if row.get("policy_key") == policy_key and row.get("commit") == commit:
            raise FreezeError(f"held-out set already run for policy key {policy_key[:16]}... "
                              f"on commit {str(commit)[:12]} (run {row.get('run_id')}); one run "
                              "per (weights, engine commit)")
    row = {"status": "claimed", "policy_key": policy_key, "heldout_sha256": HELDOUT_SHA256,
           "claimed_at_unix": int(time.time()), **info}
    with path.open("a") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")
    return row


def record_refusal(policy_key: str | None, info: dict, reason: str,
                   ledger: Path | None = None) -> dict:
    """Record a refused held-out attempt (decision #64: every run is recorded). It claims
    nothing, so a later clean run is still allowed."""
    path = refusals_path(ledger)
    row = {"status": "refused", "reason": reason, "policy_key": policy_key,
           "heldout_sha256": HELDOUT_SHA256, "refused_at_unix": int(time.time()), **info}
    with path.open("a") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")
    return row
