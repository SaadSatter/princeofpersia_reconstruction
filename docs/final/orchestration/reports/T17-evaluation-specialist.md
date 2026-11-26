---
handoff_id: HO-T17-evaluation-specialist
task_id: T17
date: 2026-11-24
from: evaluation-specialist
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T17-qa.md@3943732 (itself consuming T17-tech-lead.md@bb773ea); brief docs/final/orchestration/tasks/T17.md@efc2657
source_branch: gate/T17-eval
source_commit: 3943732
reviewed_commit: 54308c0e4c84f19f00ad4d28eeff663c71ca2c0f
verdict: ACCEPT WITH NOTES
---

# T17: evaluation-specialist report (Gate 2)

Status: done

## Work completed
Read the diff 2835928..54308c0 (5 lines in `tools/rl/train.py`, one paragraph in RL_POLICY.md, 2 TL tests), the QA report and `train()` / `main()` end to end. Re-ran the suite and ran a real (small) `train()` smoke on the branch. Judged T17 on its own, then the go/no-go for decision #51. No evaluation files or tests added; no training run started.

## Paths
This report only.

## Acceptance criteria -> evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Injected final_check error: no weights.json, weights.failed.json, summary names it with its sha, labelled failed, exit 2 | Met | TL tests, QA probes, code read: `replace()` runs only inside `if final and final["failed"]`; `weights_sha256` is taken before the rename and the content is unchanged; `stopped` and `main()` exit 2 untouched |
| 2 | Clean run still writes weights.json, exit 0 | Met | measured smoke (below): `weights_file=weights.json`, `weights_failed=False`, dir has config/log/summary/weights.json only |
| 3 | Suite green | Met | measured |

## Tests run
```
uv run --frozen --extra play --extra train pytest -q
1197 passed, 12 skipped, 2 xfailed, 2 warnings in 185.07s (0:03:05)
```
Smoke (measured, scratchpad out dir, not evidence of strength): `train(TrainConfig(max_iters=1, episodes_per_iter=4, eval_episodes=2, workers=2, max_frames=600, final_eval_seeds=4))` gave stopped=max_iters, wall 44.1 s, final check 128 full 3,600-frame pure-Python duels with 0 policy errors, weights.json written. So the final check costs well under 1 minute.

## Findings
- [none blocking]
- [minor, does not matter for #51] the in-training `policy_error` summary lacks `weights_file` and `weights_failed`. That path has `stopped="policy_error"`, `weights_sha256=null`, no weights, and `main()` exits 2 via TrainingError. The #51 acceptance rule (exit 0 and stopped in {time_cap, max_iters}) already rejects it, and nobody reads `weights_failed` for that case. Adding the keys is tidy but not needed before the run. If the orchestrator wants it, it is a one-line TL change plus a QA probe update; I would not delay the run for it.
- [minor] A crash (not a counted policy error) inside `final_check` after export leaves `weights.json` and no `summary.json`, with a traceback and a non-zero exit. Fails the #51 rule (no exit 0), so it cannot be mistaken for a good run, but the unsummarised `weights.json` must not be shipped. Not caused by T17.
- [cosmetic] Re-using an `--out` directory can leave a stale `weights.failed.json` or old `weights.json` from an earlier run (QA probes). Use a fresh directory.
- [cosmetic] `tools/rl/logs/` is not in `.gitignore`; run output will show as untracked. Do not `git add -A` afterwards.

Leak findings: none found. T17 touches no encoder, observation, action mask or runner code; the final check path still builds the policy through `make_rl_rival(path, sha)` with the recorded sha, which is why the rename is done after it.
Baseline fairness: not touched by T17 (unchanged since T07/T16 gates).
Reward and training method: unchanged. `checkpoint_chosen_by_score` stays False; last weights are exported; withholding is decided by the shipped-path error count, not by score, so it is not a score-based checkpoint choice.
Checkpoint reproducibility: rename preserves content, so `weights_sha256` matches the file named by `weights_file` (QA probe and code read). The sha-checked `load_net` is unaffected. A consumer wanting the failed file must opt in by its new name; nothing else in the repo reads the out-dir `weights.json` (grep of non-test py/yml).
Train / held-out separation: `grep heldout tools/rl agents/rl` finds nothing; `evaluation/` does not exist on this base. Unchanged by T17.
Evaluation validity and confounds: no comparative evaluation in T17. Note for the run's later reading: the final check is 32 combos x 4 seeds vs the baseline on tuning starts only, so it is a smoke of the shipped path, not a strength claim.
Local inference performance: not measured by T17. Measured incidentally: 128 pure-Python duels finish in under 44 s total.
Replay and fallback: unchanged. A policy error is not silently a WAIT in training (#47); T17 only decides the filename after the error count.
Training-run readiness: ready for Saad's approval (already given by #51). Estimated wall time: 4,800 s of training plus at most one update of overshoot (the cap is checked at the top of each loop), plus the final check (under 1 minute measured), roughly 81 to 85 minutes, inside the 90-minute course cap. The overshoot is an estimate; one update with full 5-minute duels was not timed.

## Go / no-go for decision #51
GO, from T17's integrated commit, once Gate 3 closes T17 and `orch/reviewed` contains 54308c0. Preconditions: the commit is checked out clean (the summary records `git rev-parse HEAD`), the Mac stays awake, and the out directory does not exist yet.

Command (from the repository root, on the integrated commit):
```
git rev-parse HEAD   # note this sha; it must equal summary.json "commit"
caffeinate -i uv run --frozen --extra play --extra train python -m tools.rl.train --out tools/rl/logs/run-1 --seed 0 --seconds 4800 --workers 2 > tools/rl/logs/run-1.stdout 2> tools/rl/logs/run-1.stderr; echo "exit=$?"
```
(`mkdir -p tools/rl/logs` first. Output directory: `tools/rl/logs/run-1/`, which must not exist beforehand. Any other fresh name is fine; the default `run-0` is also fine if absent.)

After it ends, check, in this order:
1. Exit status is exactly 0. Exit 2 means TrainingError or final-check failure; any traceback means no summary.
2. `summary.json` exists and `stopped` is `time_cap` or `max_iters` (expected `time_cap`). Anything else, including `policy_error` and `final_check_policy_error`, does not count.
3. `weights_failed` is false and `weights_file` is `weights.json`; `weights.json` exists, `weights.failed.json` does not. (On the `policy_error` summary these keys are absent; that is already failure by item 2.)
4. `policy_errors` is 0 and `final_check_vs_baseline_tuning_pure_python.failed` is false with `policy_errors` 0 and `episodes` 128.
5. `shasum -a 256 weights.json` equals `weights_sha256`; `commit` equals the sha noted before the run; `seed` is 0; `checkpoint_chosen_by_score` is false.
6. `wall_seconds` at or below about 5,400 (course cap 90 min); `updates` and `steps` are plausible against `log.jsonl` (last row `elapsed_s`).
7. Report the final check win rate as it is, including a poor one. It is a tuning-start smoke, not a strength claim.

## Known limitations
No full-length update was timed, so the overshoot beyond 4,800 s is estimated. Gate 2 did not run the held-out set (none exists on this base).

## Unresolved findings
None blocking.

## Requested next action
Orchestrator: Gate 3 on T17 (QA at 3943732, this report on gate/T17-eval). Then start the #51 run with the command above. The `policy_error` summary keys are optional; I recommend not delaying for them.

## Student decision required
none
