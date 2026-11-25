# T07-run1: commit the weights and evidence of the full PPO run (decision #51)

Handoff id: HO-T07-run1-orchestrator. Assigned: tech-lead; then qa, then evaluation-specialist, then Gate 3.
Decision: #51, Saad: "Go, 4,800 s cap (Recommended)". The run was made by the orchestrator with the exact command in `reports/T17-evaluation-specialist.md`@55873a6, from `orch/reviewed` f08c1a8, on Saad's Mac, 2026-11-24 20:40:05 to 22:00:26 EST.

## The run (orchestrator's after-run check, all 8 items of the T17 Eval checklist pass)

Source folder (read-only, do not edit or delete): `/Users/saadsatter/Classes/AI_Pract_Building_Games/princeofpersia_reconstruction/.claude/worktrees/train/tools/rl/logs/` with `run-1.meta`, `run-1.stdout`, `run-1.stderr` (empty) and `run-1/{config.json, summary.json, log.jsonl, weights.json}`.

- `exit=0`; `stopped: time_cap`; `wall_seconds` 4812.6; 1568 updates, 25,088 episodes, 1,487,955 steps (equal to the last `log.jsonl` row; 1568 rows).
- `weights_failed: false`, `weights_file: weights.json`, no `weights.failed.json`; `policy_errors` 0.
- `weights_sha256` 80e4a1100fddbdbbb8a4504fc8f7a2aa1b6d8a28bb4b053519634d742b5aba4c = `shasum -a 256 weights.json`; `commit` f08c1a8…; `seed` 0; `checkpoint_chosen_by_score: false`.
- `final_check_vs_baseline_tuning_pure_python`: 128 episodes, 120 wins, 8 draws, 0 losses (0.9375), 0 policy errors, `failed: false`. This is a tuning-start smoke check, **not** a strength claim and not the held-out result.

## Base and setup

`git switch -c task/T07-run1 f08c1a8` (`orch/reviewed`). Suite: `uv run --frozen --extra play --extra train --extra online pytest -q` (on f08c1a8: `1330 passed, 12 skipped, 2 xfailed, 2 warnings`). Paste the real line.

## What to do

1. Copy, byte for byte, `run-1/weights.json` to `agents/rl/weights/ppo-run-1.json`, and the evidence (`config.json`, `summary.json`, `log.jsonl`, `run-1.meta`, `run-1.stdout`) to `tools/rl/runs/run-1/`. Check the SHA-256 of every copy against the source.
2. In `agents/rl/policy.py` add two constants naming the shipped file and its SHA-256 (for example `SHIPPED_WEIGHTS`, `SHIPPED_SHA256`), and nothing else. Wiring the rival into `play.py`, the web build or the server is **not** in this task (T18 and T19, owned by another session, are changing those files; it follows T19).
3. `docs/final/RL_POLICY.md`: status line, the weights table row (file, SHA-256, commit, steps, wall time), and a Results paragraph that quotes the summary numbers above with the label "tuning starts, 128 duels, seat-swapped; not held-out". Also the T07-fix1 QA N2 correction (`final_check` covers all 32 combos), if it is still wrong.
4. Tests, failing first (`tests/test_rl_run1_*.py`): the shipped file's SHA-256 equals the constant; `load_net` loads it; it is plain JSON in the `sm-ppo-mlp-1` format with the trained sizes; `summary.json` and the file agree on the hash; a short pure-Python duel with `make_rl_rival` is deterministic and has 0 fallbacks. Keep the new tests under 30 s in total.

## Not allowed

No training, no `--live` call, no held-out (H6) evaluation: H6 is frozen in T08 and run once in T09. No change to `agents/rl/encoder.py`, `tools/rl/**` code, or any existing test.

Permitted writes: `agents/rl/weights/ppo-run-1.json` (new), `agents/rl/policy.py` (the two constants), `tools/rl/runs/run-1/**` (new), `docs/final/RL_POLICY.md`, new tests `tests/test_rl_run1_*.py`, `docs/agent-sessions/` (a new file), `docs/final/orchestration/reports/T07-run1-tech-lead.md`.

## Gates

- QA (`gate/T07-run1-qa`): byte equality with the source folder, the hash chain, the tests fail without the files.
- Eval (`gate/T07-run1-eval`): rerun the pure-Python final check (all 32 tuning combos, 128 duels) on the committed file and compare it with the summary; label the result honestly (tuning, not held-out); check the encoder for any dependence on the `jumped` / `flipped` effect names, because T19 (#53) makes every directional jump a flip, and say whether the shipped weights need a re-check or retraining after T19, as a recommendation for Saad. No H6 run.
- Gate 3 (orchestrator).
