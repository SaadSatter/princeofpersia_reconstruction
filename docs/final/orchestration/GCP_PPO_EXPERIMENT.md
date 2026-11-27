# GCP CPU experiment for PPO training

Status: branch created; cloud resources not provisioned and no GCP credits used.

Branch: `experiment/gcp-ppo-cpu`, based on `orch/reviewed` at the reviewed
training implementation and run evidence.

## Purpose

Measure whether a Google Compute Engine CPU VM improves PPO training
throughput or time-to-result compared with the recorded Apple M4 run. The
trainer is Python/NumPy and simulates the game; this experiment does not need
a GPU or a Google AI API. It is a new training experiment, not a replacement
for the committed `run-1` policy.

The reference run used seed 0, two workers, a 4,800-second cap, 1,487,955
steps, and 1,568 updates. Its final 128-duel tuning check was 120 wins, 8
draws, 0 losses. The held-out evaluation remains separate and must not be
used to tune or select weights.

## Bounded benchmark

Use the project `train` extra and a separate run directory. Start with a
short run and compare `steps / wall_seconds` and `steps / estimated VM cost`
with run-1. Keep all output under `tools/rl/runs/gcp-benchmark/`; do not
overwrite `agents/rl/weights/ppo-run-1.json` or the committed run-1 evidence.

Example command on a clean checkout of this branch:

```sh
uv sync --frozen --extra train
uv run --frozen --extra train python -m tools.rl.train \
  --out tools/rl/runs/gcp-benchmark \
  --seed 1 \
  --seconds 300 \
  --workers 4
```

The trainer writes `config.json`, `log.jsonl`, `summary.json`, and exported
weights to the output directory. It does not currently save resumable
checkpoints. Use a standard VM for a run that must finish; do not use Spot for
the initial benchmark. A new seed is an independent training result and must
be evaluated and reported as such. Do not run the held-out H6 evaluation
except through the approved evaluation task/protocol.

## Cloud cost boundary

The user stated a $100 budget for this experiment. This note does not create
resources, authorize a particular VM size, or spend credits. Before launching,
record the selected region, machine type, vCPU count, quoted hourly price,
disk choice, maximum runtime, and a shutdown plan. Keep estimated total VM and
disk charges below $100, with a meaningful margin. Credits are a payment
method, not a spending limit; configure a budget alert and stop the VM when
the run ends.

## Result record

For each cloud run, preserve the commit SHA, VM type/region, worker count,
seed, wall time, steps, updates, `stopped` reason, policy error count, weight
SHA-256, final tuning result, estimated cost, and steps per dollar. Compare
throughput against run-1; do not claim the cloud model is stronger based only
on tuning starts. Keep credentials out of the repository and transfer only
the intended run artifacts back to the branch.
