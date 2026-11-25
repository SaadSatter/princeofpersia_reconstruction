"""QA probes for T09 (read-only on the committed H6 evidence).

Never runs the held-out split and never touches the ledger. Skipped when the
committed evidence is absent (for example on a branch without T09).
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "evaluation" / "results" / "T09" / "results.json"
LEDGER = ROOT / "evaluation" / "heldout" / "ledger.jsonl"
H6 = ROOT / "evaluation" / "heldout" / "H6.json"
WEIGHTS = ROOT / "agents" / "rl" / "weights" / "ppo-run-1.json"
RESULTS_MD = ROOT / "docs" / "final" / "evaluation" / "RESULTS-T09.md"

pytestmark = pytest.mark.skipif(not RES.exists(), reason="T09 evidence not on this branch")

H6_SHA = "d013152a84aed5d6ddf189a306e1dfa66f8b178a68dde2f6d5039684e82a5266"
W_SHA = "80e4a1100fddbdbbb8a4504fc8f7a2aa1b6d8a28bb4b053519634d742b5aba4c"


def _rows():
    return json.loads(RES.read_text())["rows"]


def _ppo_seat(row):
    return "A" if row["config"] == "MvS" else "B"


def _wilson(k, n, z=1.959964):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def test_frozen_inputs_hash():
    assert hashlib.sha256(H6.read_bytes()).hexdigest() == H6_SHA
    assert hashlib.sha256(WEIGHTS.read_bytes()).hexdigest() == W_SHA


def test_ledger_exactly_one_claim_and_key():
    lines = [x for x in LEDGER.read_text().splitlines() if x.strip()]
    assert len(lines) == 1
    c = json.loads(lines[0])
    assert c["status"] == "claimed" and c["dirty"] is False
    assert c["policy_key"] == W_SHA and c["heldout_sha256"] == H6_SHA
    assert c["commit"].startswith("77bc2f7")
    assert c["configs"] == ["MvS", "SvM"]
    assert not (ROOT / "evaluation" / "heldout" / "refusals.jsonl").exists()
    # the run id of the claim is the run id of every row
    assert {r["run_id"] for r in _rows()} == {c["run_id"]}
    assert {r["commit"] for r in _rows()} == {c["commit"]}


def test_ledger_has_no_key_material():
    c = json.loads(LEDGER.read_text().splitlines()[0])
    assert not any("key" in k and k != "policy_key" for k in c)


def test_48_rows_complete_and_healthy():
    rows = _rows()
    assert len(rows) == 48
    cells = {(r["start_id"], r["config"], r["trial"]) for r in rows}
    assert cells == {
        (f"H6-{s}", c, t) for s in range(1, 9) for c in ("MvS", "SvM") for t in range(3)
    }
    for r in rows:
        assert r["split"] == "heldout" and not r["dry_run"] and not r["dirty"]
        assert not r["aborted"] and not r["harness_error"] and r["error"] is None
        assert r["invalid_inputs"] == {"A": 0, "B": 0}
        for s in "AB":
            seat = r["seats"][s]
            for k in ("fallbacks", "refused", "errors", "timeouts", "busy"):
                assert seat[k] == 0, (r["row_id"], s, k)
        assert r["controllers"][_ppo_seat(r)]["weights_sha256"] == W_SHA
        assert r["controllers"]["A" if _ppo_seat(r) == "B" else "B"]["kind"] == "scripted"


def test_trials_agree_per_cell():
    seen = defaultdict(set)
    for r in _rows():
        seen[(r["start_id"], r["config"])].add(
            (r["final_snapshot_sha256"], r["termination"], r["outcome"]["frames"])
        )
    assert all(len(v) == 1 for v in seen.values())


def _cells():
    cells = defaultdict(list)
    for r in _rows():
        p = _ppo_seat(r)
        cells[(r["start_id"], r["config"])].append(r["outcome"]["result_" + p])
    return {k: ("win" if all(x == "win" for x in v) else "loss" if "loss" in v else "draw")
            for k, v in cells.items()}


def test_counts_verdict_per_decision_77():
    cells = _cells()
    assert len(cells) == 16
    res = list(cells.values())
    assert (res.count("win"), res.count("draw"), res.count("loss")) == (13, 2, 1)
    supported = res.count("win") >= 14 and not any(r["aborted"] for r in _rows())
    assert supported is False
    a = [v for (s, c), v in cells.items() if c == "MvS"]
    b = [v for (s, c), v in cells.items() if c == "SvM"]
    assert (a.count("win"), a.count("draw"), a.count("loss")) == (7, 1, 0)
    assert (b.count("win"), b.count("draw"), b.count("loss")) == (6, 1, 1)
    sweeps = sorted(s for s in {k[0] for k in cells}
                    if cells[(s, "MvS")] == "win" and cells[(s, "SvM")] == "win")
    assert sweeps == ["H6-3", "H6-4", "H6-5", "H6-6", "H6-7"]
    assert cells[("H6-8", "SvM")] == "loss"
    assert cells[("H6-1", "MvS")] == "draw" and cells[("H6-2", "SvM")] == "draw"
    # robustness line without H6-1
    rest = [v for (s, c), v in cells.items() if s != "H6-1"]
    assert (rest.count("win"), rest.count("draw"), rest.count("loss")) == (12, 1, 1)


def test_wilson_numbers_in_report():
    lo, hi = _wilson(13, 16)
    assert (round(lo, 2), round(hi, 2)) == (0.57, 0.93)
    lo, hi = _wilson(12, 14)
    assert (round(lo, 2), round(hi, 2)) == (0.60, 0.96)
    text = RESULTS_MD.read_text()
    assert "0.57 to 0.93" in text and "0.60 to 0.96" in text


def test_stale_numbers_per_controller():
    ppo = base = 0
    per_cell = {}
    for r in _rows():
        p = _ppo_seat(r)
        b = "B" if p == "A" else "A"
        ppo += r["stale_inputs"][p]
        base += r["stale_inputs"][b]
        per_cell[(r["start_id"], r["config"])] = (r["stale_inputs"][p], r["stale_inputs"][b])
    assert (ppo, base) == (21, 18)
    expected = {
        ("H6-2", "MvS"): (1, 0), ("H6-4", "MvS"): (0, 1), ("H6-4", "SvM"): (0, 1),
        ("H6-5", "MvS"): (1, 0), ("H6-5", "SvM"): (0, 1), ("H6-6", "MvS"): (0, 1),
        ("H6-6", "SvM"): (3, 0), ("H6-7", "MvS"): (0, 2), ("H6-7", "SvM"): (2, 0),
    }
    for k, v in per_cell.items():
        assert v == expected.get(k, (0, 0)), k


def test_latency_numbers():
    n = tot = 0
    mx = 0.0
    for r in _rows():
        lat = r["latency"][_ppo_seat(r)]
        n += lat["n"]
        tot += lat["n"] * lat["mean_ms"]
        mx = max(mx, lat["max_ms"])
    assert n == 7500 and round(tot / n, 2) == 0.27 and mx == 10.8


def test_honest_wording():
    text = RESULTS_MD.read_text()
    first = text.splitlines()[0]
    assert "NOT SUPPORTED" in first
    assert "not mean the rival is worse" in text or "does not mean the rival is worse" in text
    for needle in ("nearest figure", "seat order is confounded with position",
                   "stale", "G-3", "optimistic", "hazard"):
        assert needle in text, needle
    low = text.lower()
    assert "outperform" not in low and "stronger than" not in low and "is better than" not in low


def test_no_seed_key_in_committed_evidence():
    # a key file is 64 hex chars made outside the repo; the only 64-hex strings
    # allowed in committed evidence are known digests (snapshots, weights, H6,
    # baseline source hash is 16 hex and so cannot match)
    allowed = {W_SHA, H6_SHA}
    allowed |= {r["final_snapshot_sha256"] for r in _rows()}
    allowed |= set(json.loads(RES.read_text())["run"]["scenario_file_sha256"].values())
    pat = re.compile(r"\b[0-9a-f]{64}\b")
    for p in [LEDGER, RES, RESULTS_MD, *RES.parent.glob("analysis.*")]:
        for m in pat.findall(p.read_text()):
            assert m in allowed, (p.name, m)
    for meta in (RES.parent / "traces").rglob("meta.json"):
        for m in pat.findall(meta.read_text()):
            assert m in allowed, (meta, m)
    assert not list((ROOT / "evaluation").glob("**/seed*key*"))
