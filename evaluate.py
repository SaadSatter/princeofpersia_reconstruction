"""Run the frozen evaluation suite (docs/EVALUATION_SUITE.md) and write traces.

Working directory: the project folder.

    # baseline, final seeds, all six situations (no network)
    uv run python evaluate.py --suite final --players baseline

    # live model trials (needs ANTHROPIC_API_KEY; costs money)
    uv sync --extra model
    uv run python evaluate.py --suite final --players model-history --live

Suites:
    tuning  S1-S3, seeds 0, 1     (the only cases allowed while tuning prompts)
    final   S1-S3 and held-out H1-H3, seeds 100, 101
Players: baseline, model-history, model-obs-only (obs-only runs on S1-S3 only).

Outputs, under --out (default traces/eval): one JSONL trace per episode,
results.json (all episode headers), and table.md (the comparison table).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from pop import GAME_VERSION
from pop.runner import Limits, run_episode, save_trace

SUITES = {
    "tuning": (["S1", "S2", "S3"], [0, 1]),
    "final": (["S1", "S2", "S3", "H1", "H2", "H3"], [100, 101]),
}
OBS_ONLY_SITUATIONS = {"S1", "S2", "S3"}
PLAYERS = ("baseline", "model-history", "model-obs-only")


def game_version() -> str:
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                             text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--", "pop", "agents"],
                               capture_output=True, text=True, check=True).stdout.strip()
        return f"{GAME_VERSION}+{sha}{'-dirty' if dirty else ''}"
    except (OSError, subprocess.CalledProcessError):
        return f"{GAME_VERSION}+unknown"


def make_player(kind: str, provider_name: str, model: str | None):
    if kind == "baseline":
        from agents.baseline import BaselinePlayer
        return BaselinePlayer()
    from agents.model_player import ModelPlayer
    from agents.providers import make_provider
    return ModelPlayer(make_provider(provider_name, model), variant=kind.removeprefix("model-"))


def _sum_cost(costs: list[float | None]) -> float | None:
    """Unknown (None) if any episode's cost is unknown; never shown as $0 (audit F-2)."""
    if any(c is None for c in costs):
        return None
    return round(sum(costs), 4)


def summarize(episodes: list[dict]) -> list[dict]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for e in episodes:
        groups[(e["player"], e["situation"])].append(e)
    rows = []
    for (player, sid), eps in sorted(groups.items()):
        n = len(eps)
        reasons = defaultdict(int)
        for e in eps:
            reasons[e["outcome"]["reason"]] += 1
        rows.append({
            "player": player, "situation": sid, "trials": n,
            "seeds": [e["seed"] for e in eps],
            "wins": sum(e["outcome"]["score"] for e in eps),
            "reasons": dict(sorted(reasons.items())),
            "mean_actions": round(sum(e["outcome"]["actions"] for e in eps) / n, 1),
            "invalid": sum(e["outcome"]["invalid_actions"] for e in eps),
            "calls": sum(e["model_calls"] for e in eps),
            "failed_calls": sum(e["failed_calls"] for e in eps),
            "fallbacks": sum(e["fallbacks"] for e in eps),
            "latency_mean_ms": round(sum(e["latency_ms"]["mean"] for e in eps) / n, 1),
            "latency_max_ms": max(e["latency_ms"]["max"] for e in eps),
            "tokens_in": sum(e["usage"]["tokens_in"] for e in eps),
            "tokens_out": sum(e["usage"]["tokens_out"] for e in eps),
            "cost_usd": _sum_cost([e["usage"]["cost_usd"] for e in eps]),
        })
    return rows


def table_md(rows: list[dict]) -> str:
    head = ("| Player | Situation | Trials (seeds) | Wins | Terminal reasons | Mean actions | "
            "Invalid | Calls | Failed calls | Fallbacks | Latency mean / max (ms) | "
            "Tokens in / out | Est. cost (USD) |")
    lines = [head, "|" + " --- |" * 13]
    for r in rows:
        reasons = ", ".join(f"{k} {v}" for k, v in r["reasons"].items())
        lines.append(
            f"| {r['player']} | {r['situation']} | {r['trials']} ({', '.join(map(str, r['seeds']))}) | "
            f"{r['wins']}/{r['trials']} | {reasons} | {r['mean_actions']} | {r['invalid']} | "
            f"{r['calls']} | {r['failed_calls']} | {r['fallbacks']} | "
            f"{r['latency_mean_ms']} / {r['latency_max_ms']} | "
            f"{r['tokens_in']} / {r['tokens_out']} | "
            f"{'unknown' if r['cost_usd'] is None else format(r['cost_usd'], '.4f')} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--suite", choices=sorted(SUITES), required=True)
    ap.add_argument("--players", default="baseline",
                    help="comma-separated: " + ", ".join(PLAYERS))
    ap.add_argument("--situations", help="comma-separated subset of the suite's situations")
    ap.add_argument("--seeds", help="comma-separated subset of the suite's seeds")
    ap.add_argument("--live", action="store_true", help="allow real model calls (costs money)")
    ap.add_argument("--provider", default="anthropic", choices=["anthropic", "vertex"])
    ap.add_argument("--model", help="model id (default: $POP_MODEL or claude-haiku-4-5)")
    ap.add_argument("--out", default="traces/eval")
    args = ap.parse_args(argv)

    situations, seeds = SUITES[args.suite]
    if args.situations:
        chosen = args.situations.split(",")
        bad = set(chosen) - set(situations)
        if bad:
            ap.error(f"{sorted(bad)} not in the {args.suite} suite (held-out cases need --suite final)")
        situations = chosen
    if args.seeds:
        chosen = [int(s) for s in args.seeds.split(",")]
        if set(chosen) - set(seeds):
            ap.error(f"seeds must be from {seeds} for the {args.suite} suite")
        seeds = chosen
    players = args.players.split(",")
    for p in players:
        if p not in PLAYERS:
            ap.error(f"unknown player {p!r}")
        if p.startswith("model") and not args.live:
            ap.error("model players make paid API calls; pass --live to run them")

    if any(p.startswith("model") for p in players):
        # Before any episode: a missing key must stop the run, not become
        # 40 counted failed calls (first live attempt, 2026-10-26; R-D25).
        from agents.providers import ProviderConfigError, check_credentials
        try:
            check_credentials(args.provider)
        except ProviderConfigError as exc:
            ap.exit(2, f"evaluate.py: error: {exc} No episode was run.\n")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    version = game_version()
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    episodes = []
    for kind in players:
        for sid in situations:
            if kind == "model-obs-only" and sid not in OBS_ONLY_SITUATIONS:
                continue
            for seed in seeds:
                player = make_player(kind, args.provider, args.model)
                res = run_episode(player, sid, seed, Limits())
                res["game_version"] = version
                res["suite"] = args.suite
                res["run_utc"] = stamp
                if kind.startswith("model"):
                    from agents.providers import PRICE_DATE, PRICE_SOURCE
                    res["provider"] = args.provider
                    res["price_date"] = PRICE_DATE
                    res["price_source"] = PRICE_SOURCE
                    models = {r["meta"].get("model") for r in res["trace"] if r["meta"].get("model")}
                    res["model_ids_returned"] = sorted(models)
                path = out / f"{stamp}-{kind}-{sid}-{seed}.jsonl"
                save_trace(res, path)
                header = {k: v for k, v in res.items() if k != "trace"}
                header["trace_file"] = str(path)
                episodes.append(header)
                o = res["outcome"]
                print(f"{kind:15} {sid} seed {seed}: {o['reason']:14} actions {o['actions']:3} "
                      f"invalid {o['invalid_actions']} calls {res['model_calls']} "
                      f"fallbacks {res['fallbacks']}  -> {path}")
                if res["failed_call_kinds"]:
                    kinds = ", ".join(f"{k} {n}" for k, n in res["failed_call_kinds"].items())
                    print(f"    failed calls by kind: {kinds}")
                    if res["model_calls"] and res["failed_calls"] == res["model_calls"]:
                        print("    WARNING: every model call failed; this episode is not "
                              "evidence of model gameplay.")

    rows = summarize(episodes)
    (out / f"{stamp}-results.json").write_text(json.dumps(
        {"run_utc": stamp, "suite": args.suite, "game_version": version,
         "players": players, "episodes": episodes, "summary": rows}, indent=2) + "\n")
    (out / f"{stamp}-table.md").write_text(table_md(rows))
    print()
    print(table_md(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
