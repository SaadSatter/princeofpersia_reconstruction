"""Run the versus evaluation suite (docs/final/evaluation/PROTOCOL.md, task T08).

    python3 tools/eval/run_versus_suite.py --dry-run                # baseline vs baseline, tuning split
    python3 tools/eval/run_versus_suite.py --dry-run --split heldout    # WAIT seats only, no ledger entry
    python3 tools/eval/run_versus_suite.py --make-seed-key evaluation/runs/seed.key
    python3 tools/eval/run_versus_suite.py --split tuning --configs MvS,SvM \
        --policy-factory agents.ppo:make_policy --seed-key-file evaluation/runs/seed.key
    python3 tools/eval/run_versus_suite.py --replay evaluation/runs/<run>/traces/D1/D1-a/SvS-t0

PPO and scripted controllers only: there is no provider, token or cost path
and no network call. Configurations: S = scripted baseline, M = policy (PPO);
SvS, MvS, SvM, and MvM (test only; refused on the held-out split). The seat
swap is MvS versus SvM. The held-out file is hash-checked before it is read
and is run once per frozen policy (evaluation/manifest.py).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from evaluation import controllers as C, manifest, suite  # noqa: E402
from evaluation.spec import SpecError  # noqa: E402
from pop.versus_runner import VersusLimits  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--split", choices=("tuning", "heldout"), default="tuning")
    p.add_argument("--scenarios", help="comma-separated ids (default: every scenario in the split)")
    p.add_argument("--configs", help=f"comma-separated, from {suite.CONFIGS}")
    p.add_argument("--trials", type=int, default=3, help="per start and configuration (>= 3 for a comparison)")
    p.add_argument("--seed-base", type=int, default=0)
    p.add_argument("--policy-factory", help="module:callable building a fresh M controller")
    p.add_argument("--seed-key-file", help="file holding the secret seed key (not a dry run)")
    p.add_argument("--make-seed-key", metavar="PATH", help="write a new random seed key and exit")
    p.add_argument("--dry-run", action="store_true", help="no policy, public key, results marked dry_run")
    p.add_argument("--out", help="output directory (default evaluation/runs/<run id>)")
    p.add_argument("--decision-every", type=int, default=suite.DEFAULT_DECISION_EVERY)
    p.add_argument("--timeout", type=float, default=5.0)
    p.add_argument("--max-fallbacks", type=int, default=None)
    p.add_argument("--d1-scope", choices=("any_frame", "until_success"), default="any_frame")
    p.add_argument("--replay", metavar="TRACE_DIR", help="re-feed a two-seat trace; exit 1 on mismatch")
    p.add_argument("--list", action="store_true", help="list the split's scenarios and exit")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.make_seed_key:
        path = Path(args.make_seed_key)
        if path.exists():
            print(f"refusing to overwrite {path}", file=sys.stderr)
            return 2
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(os.urandom(32).hex() + "\n")
        print(f"wrote {path} (keep it out of git and away from controllers)")
        return 0

    try:
        scenarios = manifest.load_heldout() if (args.split == "heldout") else manifest.load_tuning()
    except (manifest.FreezeError, SpecError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.list:
        for sc in scenarios.values():
            print(f"{sc.id} [{sc.kind}] {sc.duration_frames} frames: " +
                  ", ".join(s.id for s in sc.starts))
        return 0

    if args.replay:
        report = suite.replay_dir(args.replay, scenarios)
        print(json.dumps(report))
        return 0 if report["ok"] else 1

    ids = args.scenarios.split(",") if args.scenarios else list(scenarios)
    unknown = [i for i in ids if i not in scenarios]
    if unknown:
        print(f"error: not in the {args.split} split: {unknown}", file=sys.stderr)
        return 2
    heldout = args.split == "heldout"
    default_cfg = "SvS" if args.dry_run else "MvS,SvM"
    configs = (args.configs or default_cfg).split(",")
    for c in configs:
        if c not in suite.CONFIGS:
            print(f"error: unknown configuration {c}", file=sys.stderr)
            return 2
    if heldout and any(c in suite.TEST_ONLY_CONFIGS for c in configs):
        print("error: MvM is test only and never runs on the held-out split", file=sys.stderr)
        return 2
    if args.trials < 1:
        print("error: --trials must be at least 1", file=sys.stderr)
        return 2

    factory = C.load_factory(args.policy_factory) if args.policy_factory else None
    needs_policy = any("M" in c for c in configs)
    if args.dry_run and needs_policy and factory is None:
        print("error: a dry run has no policy; use SvS or pass --policy-factory", file=sys.stderr)
        return 2
    if needs_policy and factory is None:
        print("error: M seats need --policy-factory", file=sys.stderr)
        return 2

    if args.dry_run:
        key, key_id = suite.DRY_RUN_KEY, suite.DRY_RUN_KEY_ID
    else:
        if not args.seed_key_file:
            print("error: a real run needs --seed-key-file (see --make-seed-key)", file=sys.stderr)
            return 2
        key = suite.load_seed_key(args.seed_key_file)
        key_id = suite.seed_key_id(key)

    git = suite.git_state()
    run_id = suite.new_run_id() + ("-dry" if args.dry_run else "")
    out = Path(args.out) if args.out else ROOT / "evaluation" / "runs" / run_id
    force_wait = heldout and args.dry_run         # a held-out dry run never shows a policy the set

    ledger_row = None
    if heldout and not args.dry_run:
        probe = [C.describe(C.build("policy", factory)) for _ in range(1)] if needs_policy else []
        key_src = probe[0]["weights_sha256"] if probe else ("scripted:" + C.source_sha256())
        try:
            manifest.verify_heldout()
            ledger_row = manifest.claim_heldout_run(
                key_src, {"run_id": run_id, "commit": git["commit"], "configs": configs})
        except manifest.FreezeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    limits = VersusLimits(timeout_s=args.timeout, max_fallbacks=args.max_fallbacks)
    trials = suite.plan_trials(scenarios, ids, configs, args.trials, args.seed_base,
                               policy_factory=factory, force_wait=force_wait)
    rows = []
    for t in trials:
        row = suite.run_trial(t, out, seed_key=key, key_id=key_id, run_id=run_id, git=git,
                              dry_run=args.dry_run, decision_every=args.decision_every,
                              limits=limits, scope=args.d1_scope)
        rows.append(row)
        print(f"{row['row_id']:<28} {row.get('termination', 'ERROR'):<22} "
              f"success={row.get('success')} aborted={row['aborted']}")

    header = {"run_id": run_id, "split": args.split, "dry_run": args.dry_run,
              "held_out_dry_run_wait_seats": force_wait, "configs": configs,
              "scenarios": ids, "trials": args.trials, "seed_base": args.seed_base,
              "commit": git["commit"], "dirty": git["dirty"], "seed_key_id": key_id,
              "decision_every": args.decision_every, "timeout_s": args.timeout,
              "parameters_pending_saad": suite.PENDING_SAAD,
              "scenario_file_sha256": {
                  "tuning": manifest.file_sha256(manifest.TUNING_PATH),
                  "heldout": manifest.HELDOUT_SHA256 if heldout else None},
              "ledger": ledger_row,
              "provider_fields": "N/A (scripted and PPO controllers make no provider call)"}
    path = suite.write_results(out, header, rows)
    bad = [r for r in rows if r["aborted"]]
    print(f"wrote {path}: {len(rows)} rows, {len(bad)} aborted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
