"""The held-out freeze (docs/final/evaluation/PROTOCOL.md; decision #9).

`evaluation/heldout/H6.json` is OFF LIMITS to training, tuning and prompt or
reward design. Only `tools/eval/run_versus_suite.py --split heldout` reads it,
and only through `load_heldout`, which first checks the file's SHA-256 against
the constant below. The hash is recorded here, in the protocol and in the
commit that added the file; changing the file means a new hash, a new commit
and a note in the protocol, and invalidates any held-out result already
reported.

Run-once rule: `evaluation/heldout/ledger.jsonl` is append-only. A held-out
run writes its ledger line *before* the first trial (so an aborted run still
counts) and a second run for the same frozen policy key is refused.
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
HELDOUT_SHA256 = "33b777a2e71cb335d58ce5aca50e4c13605cb279ca274c0e5ca596ef0cc4188a"


class FreezeError(RuntimeError):
    pass


def verify_heldout(path: Path = HELDOUT_PATH, expected: str = HELDOUT_SHA256) -> str:
    actual = file_sha256(path)
    if actual != expected:
        raise FreezeError(f"held-out file hash mismatch: expected {expected}, found {actual}. "
                          "The frozen set was edited; do not run it.")
    return actual


def load_heldout(path: Path = HELDOUT_PATH, expected: str = HELDOUT_SHA256):
    verify_heldout(path, expected)
    return load_scenario_file(path, "heldout")


def load_tuning():
    return load_scenario_file(TUNING_PATH, "tuning")


def read_ledger(path: Path = LEDGER_PATH) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def claim_heldout_run(policy_key: str, info: dict, path: Path = LEDGER_PATH) -> dict:
    """Record a held-out run for this frozen policy, or refuse a second one."""
    if not policy_key:
        raise FreezeError("a held-out run needs a frozen policy key")
    for row in read_ledger(path):
        if row.get("policy_key") == policy_key:
            raise FreezeError(f"held-out set already run for policy key {policy_key[:16]}... "
                              f"(run {row.get('run_id')}); one run per frozen policy")
    row = {"policy_key": policy_key, "heldout_sha256": HELDOUT_SHA256,
           "claimed_at_unix": int(time.time()), **info}
    with path.open("a") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")
    return row
