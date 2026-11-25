"""Summaries of a results file: success rates, win/draw/loss, every round.

Rules (docs/final/evaluation/PROTOCOL.md):
  * every row is in the denominator: an aborted round counts as "not a
    success" and "not a win", and is also counted and listed on its own;
  * seeds are not independent trials. Rows of one condition (scenario, start,
    configuration) with the same final snapshot are one trial (T07-run1
    Evaluation E3: duels of one start pair gave identical results across
    seeds). `n_rows` is what ran, `n` is the distinct outcomes the interval
    uses; an aborted row is always its own trial;
  * a mirror match (the same kind of controller in both seats) is one trial,
    reported by seat, never as two controllers;
  * intervals are 95 % Wilson; with fewer than 3 distinct outcomes they are
    printed but flagged "n<3";
  * dry-run rows are labelled and are evidence of the plumbing only.
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
            "flag": ("n<%d" % MIN_TRIALS) if n < MIN_TRIALS else ""}


def _distinct(rows: list[dict]) -> list[dict]:
    """One row per distinct outcome of a condition. The first row of each final
    snapshot stands for its repeats; aborted rows each stand for themselves."""
    seen: set = set()
    out = []
    for r in rows:
        key = None if r["aborted"] else r.get("final_snapshot_sha256")
        if key is not None:
            if key in seen:
                continue
            seen.add(key)
        out.append(r)
    return out


def _by_condition(rows: list[dict]) -> dict[tuple, list[dict]]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        groups[(r["scenario"], r["start_id"], r["config"])].append(r)
    return groups


def condition_table(rows: list[dict]) -> list[dict]:
    """Rows run and distinct outcomes for every (scenario, start, configuration)."""
    out = []
    for (scn, start, cfg), rs in sorted(_by_condition(rows).items()):
        out.append({"scenario": scn, "start_id": start, "config": cfg, "n_rows": len(rs),
                    "n_distinct": len(_distinct(rs)),
                    "aborted": sum(1 for r in rs if r["aborted"])})
    return out


def success_by_scenario(rows: list[dict]) -> list[dict]:
    """Per scenario and configuration: successes over the distinct outcomes of
    every start. Outcome-only scenarios (no success flag) are not listed."""
    scored = [r for r in rows if r["scenario_kind"] != "duel"]
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in scored:
        groups[(r["scenario"], r["config"])].append(r)
    out = []
    for (scn, cfg), rs in sorted(groups.items()):
        picked = []
        for conds in _by_condition(rs).values():
            picked.extend(_distinct(conds))
        out.append({"scenario": scn, "config": cfg,
                    "subject": "/".join(sorted({label(r["controllers"]["A"]) for r in rs
                                                if r.get("controllers")})),
                    "n_rows": len(rs), "distinct": len(picked),
                    "aborted": sum(1 for r in rs if r["aborted"]),
                    **rate(sum(1 for r in picked if r.get("success") is True), len(picked))})
    return out


def is_duel(r: dict) -> bool:
    """A rival-against-rival row: no seat was forced to a stand-in."""
    return not r.get("forced_controllers") and r["scenario_kind"] in ("duel", "fight")


def duel_results(rows: list[dict]) -> list[dict]:
    """Win/draw/loss. Mixed configurations (MvS, SvM): per controller label over
    both seats, with the per-seat split. A mirror (SvS, MvM): one trial, by seat."""
    duels = [r for r in rows if is_duel(r)]
    out: list[dict] = []
    mirror: dict[tuple, list[dict]] = defaultdict(list)
    mixed: dict[tuple, list[dict]] = defaultdict(list)
    for r in duels:
        a, b = label(r["controllers"]["A"]), label(r["controllers"]["B"])
        (mirror if a == b else mixed)[(r["scenario"], r["config"])].append(r)
    for (scn, cfg), rs in sorted(mirror.items()):
        picked = [x for conds in _by_condition(rs).values() for x in _distinct(conds)]
        done = [x for x in picked if not x["aborted"]]
        out.append({"scenario": scn, "controller": label(rs[0]["controllers"]["A"]),
                    "config": cfg, "mirror": True, "n_rows": len(rs), "n": len(picked),
                    "aborted": len(picked) - len(done),
                    "a_wins": sum(x["outcome"]["result_A"] == "win" for x in done),
                    "b_wins": sum(x["outcome"]["result_B"] == "win" for x in done),
                    "draws": sum(x["outcome"]["result_A"] == "draw" for x in done)})
    by_ctrl: dict[tuple, dict] = {}
    for (scn, cfg), rs in sorted(mixed.items()):
        picked = [x for conds in _by_condition(rs).values() for x in _distinct(conds)]
        for x in picked:
            for seat in ("A", "B"):
                name = label(x["controllers"][seat])
                d = by_ctrl.setdefault((scn, name), {
                    "scenario": scn, "controller": name, "mirror": False,
                    "configs": set(), "n_rows": 0, "n": 0, "aborted": 0,
                    "win": 0, "draw": 0, "loss": 0,
                    "by_seat": {s: {"win": 0, "draw": 0, "loss": 0, "n": 0} for s in "AB"}})
                d["configs"].add(cfg)
                d["n"] += 1
                d["by_seat"][seat]["n"] += 1
                if x["aborted"]:
                    d["aborted"] += 1
                else:
                    res = x["outcome"][f"result_{seat}"]
                    if res in ("win", "draw", "loss"):
                        d[res] += 1
                        d["by_seat"][seat][res] += 1
        for x in rs:
            for seat in ("A", "B"):
                by_ctrl[(scn, label(x["controllers"][seat]))]["n_rows"] += 1
    for (scn, name), d in sorted(by_ctrl.items()):
        d["config"] = "+".join(sorted(d.pop("configs")))
        d["win_ci"] = wilson(d["win"], d["n"])
        d["loss_ci"] = wilson(d["loss"], d["n"])
        d["flag"] = ("n<%d" % MIN_TRIALS) if d["n"] < MIN_TRIALS else ""
        out.append(d)
    return out


def render(rows: list[dict], headers: list[dict], every_round: bool = True) -> str:
    lines = ["# Versus evaluation summary", ""]
    if any(r.get("dry_run") for r in rows) or any(h.get("dry_run") for h in headers):
        lines += ["**DRY RUN rows present: plumbing check only, not evidence of play strength.**",
                  ""]
    for h in headers:
        lines.append(f"- run `{h['run_id']}` split `{h['split']}` commit `{h['commit'][:12]}` "
                     f"dry_run={h['dry_run']} seed_key_id={h['seed_key_id']}")
    aborted = [r for r in rows if r["aborted"]]
    lines += ["", f"Rows: {len(rows)}; aborted: {len(aborted)} (counted as not a success, "
              "not a win, and listed below).", ""]
    lines += ["## Distinct outcomes per condition", "",
              "Seeds are not independent trials: rows of one condition with the same final "
              "state are one trial.", "",
              "| scenario | start | config | rows | distinct | aborted |", "|---|---|---|---|---|---|"]
    for c in condition_table(rows):
        lines.append(f"| {c['scenario']} | {c['start_id']} | {c['config']} | {c['n_rows']} | "
                     f"{c['n_distinct']} | {c['aborted']} |")
    lines += ["", "## Scenario success (distinct outcomes; aborted rounds count as failures)", "",
              "| scenario | config | seat-A controller | k/n | rate | 95% Wilson | rows | aborted | flag |",
              "|---|---|---|---|---|---|---|---|---|"]
    for s in success_by_scenario(rows):
        r = "n/a" if s["rate"] is None else f"{s['rate']:.2f}"
        lines.append(f"| {s['scenario']} | {s['config']} | {s['subject']} | {s['k']}/{s['n']} | "
                     f"{r} | {s['lo']:.2f}-{s['hi']:.2f} | {s['n_rows']} | {s['aborted']} | "
                     f"{s['flag']} |")
    duels = duel_results(rows)
    lines += ["", "## Duels: win / draw / loss", ""]
    mixed = [d for d in duels if not d["mirror"]]
    mirror = [d for d in duels if d["mirror"]]
    if mixed:
        lines += ["| scenario | controller | configs | W | D | L | n | aborted | win 95% | by seat A | by seat B | flag |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    elif not mirror:
        lines += ["No rival-against-rival rows."]
    for d in mixed:
        sa, sb = d["by_seat"]["A"], d["by_seat"]["B"]
        lines.append(f"| {d['scenario']} | {d['controller']} | {d['config']} | {d['win']} | "
                     f"{d['draw']} | {d['loss']} | {d['n']} | {d['aborted']} | "
                     f"{d['win_ci'][0]:.2f}-{d['win_ci'][1]:.2f} | "
                     f"{sa['win']}W {sa['draw']}D {sa['loss']}L | "
                     f"{sb['win']}W {sb['draw']}D {sb['loss']}L | {d['flag']} |")
    if mirror:
        lines += ["", "Mirror matches (the same kind of controller in both seats): one trial each, "
                  "by seat.", "",
                  "| scenario | controller | config | trials | seat A wins | seat B wins | draws | aborted |",
                  "|---|---|---|---|---|---|---|---|"]
        for d in mirror:
            lines.append(f"| {d['scenario']} | {d['controller']} | {d['config']} | {d['n']} | "
                         f"{d['a_wins']} | {d['b_wins']} | {d['draws']} | {d['aborted']} |")
    if aborted:
        lines += ["", "## Aborted rounds", ""]
        lines += [f"- `{r['row_id']}`: {r['abort_reason']} {r.get('error') or ''}" for r in aborted]
    if every_round:
        lines += ["", "## Every round", "", "| row | termination | success | reason |",
                  "|---|---|---|---|"]
        for r in rows:
            lines.append(f"| {r['row_id']} | {r.get('termination', 'ERROR')} | "
                         f"{r.get('success')} | {r.get('success_reason')} |")
    return "\n".join(lines) + "\n"
