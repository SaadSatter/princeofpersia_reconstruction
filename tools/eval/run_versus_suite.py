"""Run the versus evaluation suite (docs/final/evaluation/PROTOCOL.md, task T08).

    python3 tools/eval/run_versus_suite.py --dry-run                  # baseline vs baseline, tuning split
    python3 tools/eval/run_versus_suite.py --dry-run --split heldout  # WAIT seats only, no ledger entry
    python3 tools/eval/run_versus_suite.py --make-seed-key evaluation/runs/seed.key
    python3 tools/eval/run_versus_suite.py --split tuning --configs MvS,SvM \
        --seed-key-file evaluation/runs/seed.key
    python3 tools/eval/run_versus_suite.py --replay evaluation/runs/<run>/traces/D1/D1-a/SvS-t0

PPO and scripted controllers only: there is no provider, token or cost path
and no network call. Configurations name the seat A and seat B controllers:
S = scripted baseline, M = the PPO rival from the shipped weights
(`agents/rl/policy.py` SHIPPED_WEIGHTS, hash checked at load, recorded in
every row). SvS, MvS, SvM and MvM (test only; refused on the held-out split).
MvS against SvM is the seat swap. The held-out file is hash-checked before it
is read and is run once per (weights SHA-256, engine commit) pair (decision #64,
evaluation/manifest.py). A real held-out run is refused on an unknown commit or
a dirty tree, and every refusal is recorded beside the ledger. A dry run on the
held-out set uses WAIT seats only and never a policy. `--replay` takes the split
from the trace's meta.json.
"""

from __future__ import annotations

import argparse
import json
import secrets
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from evaluation import controllers as C, manifest, suite  # noqa: E402
from evaluation.spec import SpecError, file_sha256  # noqa: E402
from pop.versus_runner import VersusLimits  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--split", choices=("tuning", "heldout"), default="tuning")
    p.add_argument("--scenarios", help="comma-separated ids (default: every scenario in the split)")
    p.add_argument("--configs", help=f"comma-separated, from {suite.CONFIGS}")
    p.add_argument("--trials", type=int, default=3,
                   help="per start and configuration (3+ for a comparison; see PROTOCOL.md)")
    p.add_argument("--seed-base", type=int, default=0)
    p.add_argument("--seed-key-file", help="file holding the secret seed key (not a dry run)")
    p.add_argument("--make-seed-key", metavar="PATH", help="write a new random seed key and exit")
    p.add_argument("--dry-run", action="store_true",
                   help="public seed key, results marked dry_run; default configuration SvS")
    p.add_argument("--out", help="output directory (default evaluation/runs/<run id>)")
    p.add_argument("--decision-every", type=int, default=suite.DEFAULT_DECISION_EVERY)
    p.add_argument("--timeout", type=float, default=5.0)
    p.add_argument("--max-fallbacks", type=int, default=None)
    p.add_argument("--max-frames", type=int, default=None,
                   help="safety cap; a capped run is an aborted row (for smoke tests)")
    p.add_argument("--replay", metavar="TRACE_DIR", help="re-feed a two-seat trace; exit 1 on mismatch")
    p.add_argument("--list", action="store_true", help="list the split's scenarios and exit")
    return p


def make_seed_key(path: Path) -> int:
    if path.exists():
        print(f"refusing to overwrite {path}", file=sys.stderr)
        return 2
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(secrets.token_bytes(suite.MIN_KEY_BYTES).hex() + "\n")
    print(f"wrote {path} (keep it out of git and away from controllers)")
    return 0


def replay(trace_dir: Path, default_split: str) -> int:
    """Re-feed a two-seat trace. The split comes from the trace's own `meta.json` (QA F-4),
    so a held-out trace replays without `--split heldout`; `--split` is only the fallback
    for a meta file that predates the field."""
    try:
        split = json.loads((trace_dir / "meta.json").read_text()).get("split", default_split)
    except (OSError, ValueError) as exc:
        print(f"error: cannot read {trace_dir / 'meta.json'}: {exc}", file=sys.stderr)
        return 2
    try:
        if split == "heldout":
            scenarios = manifest.load_heldout()
        elif split == "tuning":
            scenarios = manifest.load_tuning()
        else:
            print(f"error: the trace's split is {split!r}; expected tuning or heldout",
                  file=sys.stderr)
            return 2
    except (manifest.FreezeError, SpecError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    report = suite.replay_dir(trace_dir, scenarios)
    print(json.dumps(report))
    return 0 if report["ok"] else 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.make_seed_key:
        return make_seed_key(Path(args.make_seed_key))

    if args.replay:
        return replay(Path(args.replay), args.split)

    try:
        scenarios = manifest.load_heldout() if args.split == "heldout" else manifest.load_tuning()
    except (manifest.FreezeError, SpecError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.list:
        for sc in scenarios.values():
            print(f"{sc.id} [{sc.kind}] {sc.duration_frames} frames: " +
                  ", ".join(s.id for s in sc.starts))
        return 0

    ids = args.scenarios.split(",") if args.scenarios else list(scenarios)
    unknown = [i for i in ids if i not in scenarios]
    if unknown:
        print(f"error: not in the {args.split} split: {unknown}", file=sys.stderr)
        return 2
    heldout = args.split == "heldout"
    configs = (args.configs or ("SvS" if args.dry_run else "MvS,SvM")).split(",")
    for c in configs:
        if c not in suite.CONFIGS:
            print(f"error: unknown configuration {c}", file=sys.stderr)
            return 2
    if heldout and any(c in suite.TEST_ONLY_CONFIGS for c in configs):
        print("error: MvM is test only and never runs on the held-out split", file=sys.stderr)
        return 2
    needs_policy = any("M" in c for c in configs)
    if heldout and args.dry_run and needs_policy:
        print("error: a held-out dry run uses WAIT seats only; it never shows the set to a policy",
              file=sys.stderr)
        return 2
    if args.trials < 1:
        print("error: --trials must be at least 1", file=sys.stderr)
        return 2

    if args.dry_run:
        key, key_id = suite.DRY_RUN_KEY, suite.DRY_RUN_KEY_ID
    else:
        if not args.seed_key_file:
            print("error: a real run needs --seed-key-file (see --make-seed-key)", file=sys.stderr)
            return 2
        try:
            key = suite.load_seed_key(args.seed_key_file)
        except (OSError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        key_id = suite.seed_key_id(key)

    git = suite.git_state()
    run_id = suite.new_run_id() + ("-dry" if args.dry_run else "")
    out = Path(args.out) if args.out else ROOT / "evaluation" / "runs" / run_id
    force_wait = heldout and args.dry_run

    ledger_row = None
    if heldout and not args.dry_run:
        # The frozen policy: the shipped weights if any seat is M, else the scripted sources.
        policy_key = (C.make_shipped_policy().weights_sha256 if needs_policy
                      else "scripted:" + C.source_sha256())
        info = {"run_id": run_id, "commit": git["commit"], "dirty": git["dirty"],
                "configs": configs}
        try:
            manifest.verify_heldout()
            manifest.require_known_clean_tree(git)
            ledger_row = manifest.claim_heldout_run(policy_key, info)
        except manifest.FreezeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            manifest.record_refusal(policy_key, info, str(exc))     # decision #64
            return 2

    limits = VersusLimits(timeout_s=args.timeout, max_fallbacks=args.max_fallbacks,
                          max_frames=args.max_frames)
    trials = suite.plan_trials(scenarios, ids, configs, args.trials, args.seed_base,
                               force_wait=force_wait)
    rows = []
    for t in trials:
        row = suite.run_trial(t, out, seed_key=key, key_id=key_id, run_id=run_id, git=git,
                              dry_run=args.dry_run, decision_every=args.decision_every,
                              limits=limits)
        rows.append(row)
        print(f"{row['row_id']:<28} {row.get('termination', 'ERROR'):<22} "
              f"success={row.get('success')} aborted={row['aborted']}")

    header = {"run_id": run_id, "split": args.split, "dry_run": args.dry_run,
              "held_out_dry_run_wait_seats": force_wait, "configs": configs,
              "scenarios": ids, "trials": args.trials, "seed_base": args.seed_base,
              "commit": git["commit"], "dirty": git["dirty"], "seed_key_id": key_id,
              "decision_every": args.decision_every, "timeout_s": args.timeout,
              "max_frames": args.max_frames,
              "decisions_in_force": suite.DECISIONS_IN_FORCE,
              "scenario_file_sha256": {
                  "tuning": file_sha256(manifest.TUNING_PATH),
                  "heldout": manifest.HELDOUT_SHA256 if heldout else None},
              "ledger": ledger_row,
              "provider_fields": "N/A (scripted and PPO controllers make no provider call)"}
    path = suite.write_results(out, header, rows)
    bad = [r for r in rows if r["aborted"]]
    print(f"wrote {path}: {len(rows)} rows, {len(bad)} aborted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
