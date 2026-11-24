"""Summaries of a results file: success rates, win/draw/loss, every round.

Rules (docs/final/evaluation/PROTOCOL.md):
  * the denominator is every row: an aborted round counts as "not a success"
    and "not a win", and is also counted and listed on its own;
  * intervals are 95 % Wilson intervals; with fewer than 3 trials per
    condition they are printed but flagged "n<3";
  * dry-run rows are labelled and are not evidence of anything but the plumbing.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .stats import wilson

MIN_TRIALS = 3


def load_rows(paths: list[str | Path]) -> tuple[list[dict], list[dict]]:
    rows, headers = [], []
    for p in paths:
        data = json.loads(Path(p).read_text())
        headers.append(data["run"])
        rows.extend(data["rows"])
    return rows, headers


def label(ctrl: dict) -> str:
    return {"policy": "M", "scripted": "S"}.get(ctrl.get("kind"), ctrl.get("name", "?"))


def rate(k: int, n: int) -> dict:
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "rate": (k / n) if n else None, "lo": lo, "hi": hi,
            "flag": "n<%d" % MIN_TRIALS if n < MIN_TRIALS else ""}


def success_by_scenario(rows: list[dict]) -> list[dict]:
    """Per scenario, start, configuration: successes over all rounds."""
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        if r.get("success") is None and not r["aborted"]:
            continue                               # outcome-only scenarios (H6)
        groups[(r["scenario"], r["config"])].append(r)
    out = []
    for (scn, cfg), rs in sorted(groups.items()):
        out.append({"scenario": scn, "config": cfg,
                    "subject": "/".join(sorted({label(r["controllers"]["A"]) for r in rs
                                                if r.get("controllers")})),
                    "aborted": sum(r["aborted"] for r in rs),
                    **rate(sum(1 for r in rs if r.get("success") is True), len(rs))})
    return out


def duel_results(rows: list[dict]) -> list[dict]:
    """Win/draw/loss per controller label, per scenario, over both seats."""
    tally: dict[tuple, dict] = defaultdict(lambda: {"win": 0, "draw": 0, "loss": 0,
                                                    "aborted": 0, "n": 0})
    for r in rows:
        if r["scenario_kind"] not in ("duel",) and r["scenario"] != "F5":
            continue
        if r["scenario"] == "F5" and r["start_id"] != "F5-c":
            continue                              # F5-c is the rival-vs-rival start
        for seat in ("A", "B"):
            ctrl = r.get("controllers", {}).get(seat)
            if ctrl is None:
                continue
            t = tally[(r["scenario"], f"{label(ctrl)} in seat {seat}", r["config"])]
            t["n"] += 1
            if r["aborted"]:
                t["aborted"] += 1
                continue
            t[r["outcome"][f"result_{seat}"]] += 1
    out = []
    for (scn, who, cfg), t in sorted(tally.items()):
        out.append({"scenario": scn, "controller": who, "config": cfg, **t,
                    "win": rate(t["win"], t["n"]), "loss": rate(t["loss"], t["n"])})
    return out


def render(rows: list[dict], headers: list[dict], every_round: bool = True) -> str:
    lines = ["# Versus evaluation summary", ""]
    if any(r["dry_run"] for r in rows):
        lines += ["**DRY RUN rows present: plumbing check only, not evidence of play strength.**", ""]
    for h in headers:
        lines.append(f"- run `{h['run_id']}` split `{h['split']}` commit `{h['commit'][:12]}` "
                     f"dry_run={h['dry_run']} seed_key_id={h['seed_key_id']}")
    aborted = [r for r in rows if r["aborted"]]
    lines += ["", f"Rows: {len(rows)}; aborted: {len(aborted)} (counted as not a success, "
              "not a win, and listed below).", ""]
    lines += ["## Scenario success (every round in the denominator)", "",
              "| scenario | config | seat-A controller | k/n | rate | 95% Wilson | aborted | flag |",
              "|---|---|---|---|---|---|---|---|"]
    for s in success_by_scenario(rows):
        r = "n/a" if s["rate"] is None else f"{s['rate']:.2f}"
        lines.append(f"| {s['scenario']} | {s['config']} | {s['subject']} | {s['k']}/{s['n']} | "
                     f"{r} | {s['lo']:.2f}-{s['hi']:.2f} | {s['aborted']} | {s['flag']} |")
    lines += ["", "## Duels: win / draw / loss", "",
              "| scenario | controller | config | W | D | L | aborted | win 95% | loss 95% |",
              "|---|---|---|---|---|---|---|---|---|"]
    for d in duel_results(rows):
        lines.append(f"| {d['scenario']} | {d['controller']} | {d['config']} | {d['win']['k']} | "
                     f"{d['draw']} | {d['loss']['k']} | {d['aborted']} | "
                     f"{d['win']['lo']:.2f}-{d['win']['hi']:.2f} | "
                     f"{d['loss']['lo']:.2f}-{d['loss']['hi']:.2f} |")
    if aborted:
        lines += ["", "## Aborted rounds", ""]
        lines += [f"- `{r['row_id']}`: {r['abort_reason']} {r.get('error') or ''}" for r in aborted]
    if every_round:
        lines += ["", "## Every round", "", "| row | termination | success | reason |", "|---|---|---|---|"]
        for r in rows:
            lines.append(f"| {r['row_id']} | {r.get('termination', 'ERROR')} | "
                         f"{r.get('success')} | {r.get('success_reason')} |")
    return "\n".join(lines) + "\n"
