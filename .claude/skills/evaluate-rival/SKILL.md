---
name: evaluate-rival
description: Reproducible evaluation of Shadow Masque's AI rival (the locally trained PPO policy) against the scripted baseline. Validates a checkpoint's SHA-256 and pure-Python inference, runs seat-swapped scripted comparisons on tuning scenarios, runs the frozen held-out set (H6) once per frozen policy, replays two-seat traces, and writes results and an evidence note. Use for Gate 2 reviews, before a gate, or when asked how strong the rival is. Never starts a full training run or a paid model call.
argument-hint: "<check | compare | heldout | replay | smoke> [weights path] [weights sha256]"
allowed-tools: Read, Grep, Glob, Bash(git show:*), Bash(git log:*), Bash(git rev-parse:*), Bash(git branch:*), Bash(shasum:*), Bash(uv run pytest:*), Bash(python3 -m pytest:*), Bash(uv run python tools/eval/*), Bash(python3 tools/eval/*), Bash(uv run python -c:*), Bash(python3 -c:*), Write(docs/final/evaluation/**), Write(docs/final/orchestration/reports/**), Edit(docs/final/evaluation/**)
---

# evaluate-rival

Mode and arguments: **$ARGUMENTS**

You evaluate the PPO rival. You do not train it, tune it or change it. The
rival does not need to win. Report what happened, including failures,
aborted runs and weak results.

## Hard rules

1. **No training.** `python -m tools.rl.train` (about 85 minutes) and any
   run longer than 10 minutes need Saad's explicit go-ahead in this session,
   or quoted in the brief. Without it, stop and say what you would run.
2. **No paid calls.** The PPO rival has no provider, tokens or cost; record
   those fields as `N/A` (as PR #64 does). A `--live` LLM call is out of
   scope for this skill.
3. **Held-out discipline.** The held-out set (`evaluation/heldout/H6.json`)
   runs **once per frozen policy**, through the CLI, which checks its
   SHA-256 and writes a ledger row. Never read it to tune anything, never edit
   it, and never run it on a policy that is still changing.
4. **Every round is reported**, including `aborted` runs (over the fallback
   limit) and fallbacks (`"source": "fallback"`). A replay is never new
   evidence. A dry run is labelled `dry_run`.
5. **Success criteria are Saad's** (decision #9). B2's "low" threshold and
   D1's "on screen" are pending his confirmation; name them as pending in
   every result.

## Step 0: know what exists on your branch

Most evaluation code is not on `main` yet (2026-11-24):

| Piece | Where | State |
| --- | --- | --- |
| Encoder, stdlib policy, `load_net`, `make_rl_rival` | `agents/rl/` | `orch/preview` (T07), awaiting Gates 1 and 2 |
| Trainer | `tools/rl/` | `orch/preview` (T07). **Training not run; no weights** |
| Macro layer and scripted baseline | `agents/macros.py`, `agents/versus_baseline.py` | `orch/preview` (T05). Fix T05-fix1 is WIP (`orch/wip-T05-fix1`) |
| Scenario suite, held-out set, CLI, analysis | `evaluation/`, `tools/eval/` | `orch/wip-T08`: **untested, unreviewed WIP** |

```sh
git rev-parse --abbrev-ref HEAD && git rev-parse HEAD
ls agents/rl tools/rl tools/eval evaluation 2>&1
```

If a piece is missing on your branch, say so and stop that step. Do not copy
code across from a WIP branch.

## Mode `check`: validate a checkpoint

```sh
shasum -a 256 <weights.json>
python3 -c "from agents.rl.policy import load_net; n = load_net('<weights.json>', '<sha256>'); print(n)"
uv run pytest -q tests/test_rl_policy.py tests/test_rl_encoder.py
```

Pass when the hash matches the value recorded in `docs/final/RL_POLICY.md`
(weights table) and in `summary.json`, the load refuses a wrong hash, and the
parity test (pure Python against numpy, 1e-9) passes. Record the commit,
seed, steps and wall time from `summary.json`.

## Mode `compare`: policy against the scripted baseline (tuning split)

```sh
python3 tools/eval/run_versus_suite.py --list --split tuning
python3 tools/eval/run_versus_suite.py --split tuning --dry-run              # plumbing only
python3 tools/eval/run_versus_suite.py --make-seed-key <outside-the-repo>/seed.key
python3 tools/eval/run_versus_suite.py --split tuning --configs SvS,MvS,SvM --trials 3 \
    --policy-factory <module:callable> --seed-key-file <outside-the-repo>/seed.key
python3 tools/eval/analyze_results.py <results.json> --json <out>.json
```

Configurations: `SvS` (scripted vs scripted), `MvS` / `SvM` (policy in seat
A / seat B: seats swapped), `MvM` test only. Three or more trials per start
and configuration. Fresh controllers per trial. Report win, draw and loss
with Wilson intervals, per-scenario success, and fallback, invalid, stale and
busy counts.

## Mode `heldout`: the frozen H6 run

Only when the brief says the policy is frozen and Saad approved the run.

```sh
python3 tools/eval/run_versus_suite.py --split heldout --dry-run             # WAIT seats only
python3 tools/eval/run_versus_suite.py --split heldout --configs MvS,SvM --trials 3 \
    --policy-factory <module:callable> --seed-key-file <outside-the-repo>/seed.key
```

The CLI refuses a changed held-out file and writes a ledger row. Record the
ledger row in the evidence note.

## Mode `replay`

```sh
python3 tools/eval/run_versus_suite.py --replay <trace-dir>     # exit 1 on mismatch
```

## Mode `smoke`: deterministic tests only

```sh
uv run pytest -q tests/test_rl_encoder.py tests/test_rl_policy.py tests/test_rl_train.py
uv run pytest -q tests/test_eval_monitors.py    # where T08 exists
```

`test_rl_train.py` runs a training *smoke* (under 60 s, 900-frame duels). It
checks the loop, not strength.

## Evidence note

Write `docs/final/evaluation/<YYYY-MM-DD>-<mode>.md` (or, inside a gate
review, put the same content in your report):

```
Date / commit / branch:
Policy: weights path, SHA-256, training commit, seed, steps   (or "none: untrained")
Baseline: agents/versus_baseline.py @ <sha>, MACROS.md memory disclosure
Split and scenarios: tuning | heldout; ids; scenario file SHA-256
Configs and trials: SvS/MvS/SvM, n per start
Results: table with Wilson intervals; every round; aborted runs
Fallbacks / invalid / stale / busy: per seat
Latency: measured (machine) | estimated
Pending Saad: B2 threshold, D1 "on screen", others
Commands run: exact, with result lines
Not run and why:
```

## Manifest

This skill is the project's executable agent extension for evaluation.
`agent-config.json` (repository root) records it with the course's manifest
fields.
