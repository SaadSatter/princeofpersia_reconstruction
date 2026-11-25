"""QA probes for T07-run1: independent of the Tech Lead's tests."""
import hashlib
import json
import math
from pathlib import Path

from agents.rl import policy as pol

ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / "tools" / "rl" / "runs" / "run-1"


def _flat(x):
    if isinstance(x, list):
        for y in x:
            yield from _flat(y)
    else:
        yield x


def test_weights_all_finite_numbers():
    data = json.loads(Path(pol.SHIPPED_WEIGHTS).read_text())
    n = 0
    for layer in data["layers"]:
        for key in ("w", "W", "b"):
            if key in layer:
                for v in _flat(layer[key]):
                    assert isinstance(v, (int, float)) and math.isfinite(v)
                    n += 1
    assert n > 10000


def test_log_is_monotone_and_config_commit_matches_summary():
    rows = [json.loads(x) for x in (RUN / "log.jsonl").read_text().splitlines() if x.strip()]
    steps = [r["steps"] for r in rows]
    assert steps == sorted(steps) and len(set(steps)) == len(steps)
    summary = json.loads((RUN / "summary.json").read_text())
    assert summary["commit"] in (RUN / "run-1.meta").read_text()
    assert summary["wall_seconds"] >= 4800 and summary["stopped"] == "time_cap"


def test_constant_is_hash_of_bytes_and_no_stray_weights_files():
    assert hashlib.sha256(Path(pol.SHIPPED_WEIGHTS).read_bytes()).hexdigest() == pol.SHIPPED_SHA256
    assert not (RUN / "weights.json").exists()  # one shipped copy only
    assert (RUN / "run-1.stdout").stat().st_size > 0
