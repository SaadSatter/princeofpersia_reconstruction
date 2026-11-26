"""Summarise versus-suite results (docs/final/evaluation/PROTOCOL.md).

    python3 tools/eval/analyze_results.py evaluation/runs/<run>/results.json [more.json]
    python3 tools/eval/analyze_results.py results.json --json summary.json --no-rounds

Prints Markdown: distinct outcomes per condition, per-scenario success rates
and win/draw/loss with Wilson intervals, aborted rounds, and every round.
Never drops a row.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from evaluation import analysis  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("results", nargs="+")
    p.add_argument("--json", help="also write the tables as JSON")
    p.add_argument("--no-rounds", action="store_true", help="omit the every-round table")
    args = p.parse_args(argv)
    rows, headers = analysis.load_rows(args.results)
    print(analysis.render(rows, headers, every_round=not args.no_rounds), end="")
    if args.json:
        Path(args.json).write_text(json.dumps({
            "success": analysis.success_by_scenario(rows),
            "duels": analysis.duel_results(rows),
            "conditions": analysis.condition_table(rows), "rows": len(rows),
            "aborted": sum(r["aborted"] for r in rows)}, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
