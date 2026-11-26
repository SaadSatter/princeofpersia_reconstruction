---
handoff_id: HO-T16-evaluation-specialist
task_id: T16
date: 2026-11-24
from: evaluation-specialist
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id)
consumed: docs/final/orchestration/reports/T16-qa.md@37cf95c (which consumed T16-tech-lead.md@7519820); brief docs/final/orchestration/tasks/T16.md@e5ecff5
source_branch: gate/T16-eval
reviewed_commit: 9024ef8 (code), 37cf95c (QA)
verdict: ACCEPT WITH NOTES
---

# T16: Gate 2 evaluation report

Status: done

## Verdict
**ACCEPT WITH NOTES.** E1-fix1 and E2-fix1 are fixed and now covered by behaviour tests, including with a 2-worker pool. No leak, no held-out reachability, no failed criterion. T07 + T07-fix1 + T16 are **ready for Saad's go/no-go** on the full run, with one question for him (F1) and the checklist below.

## Work completed
- Inverted the two stale probes in `tests/test_eval_T07fix1.py`, as the orchestrator asked. Renamed:
  - `test_final_check_does_not_read_rival_error_counts` -> `test_final_check_counts_an_exported_policy_error_and_fails` (injects `Net.act` failure, 2 combos; asserts `policy_errors > 0` and `failed is True`).
  - `test_in_loop_eval_errors_are_not_summed` -> `test_in_loop_eval_error_is_counted_logged_and_stops_the_run` (injects an error into greedy episodes only; asserts `TrainingError`, `summary.stopped == "policy_error"`, no weights sha, `eval_policy_errors > 0` in the last `log.jsonl` row).
  - Nothing else in that file changed. (The now-unused `import inspect` line was left in place so as to change nothing else.)
- New `tests/test_eval_T16.py` (2 tests, multi-worker, cheap):
  - `workers=2`, error in greedy eval episodes: counted, logged, run stops, no `weights.json`, `summary.policy_errors` equals the logged eval count.
  - `workers=2` training, then `final_check` error: `stopped == "final_check_policy_error"`, `failed True`. Note `final_check` always runs in the parent process on the exported file, never in the pool, so "multi-worker final_check" reduces to this.
- Read `train.py` at 9024ef8 end to end, the QA report and my T07-fix1 report. No training run, no paid call.

## Tests run
```
uv run --frozen --extra play --extra train pytest -q tests/test_eval_T07fix1.py tests/test_eval_T16.py
6 passed in 6.01s
```
Full suite: `1187 passed, 12 skipped, 2 xfailed, 2 warnings in 183.86s` (pytest's own line, run on this branch).

## Earlier findings: resolved?
| Finding | State |
| --- | --- |
| E1-fix1 final_check ignores shipped-path errors | Resolved. `final_check` sums `rival.policy_errors()` per duel (fresh rival per duel, so no double count) and returns `policy_errors`, `failed`; `train` sets `stopped = "final_check_policy_error"`, adds to the total; CLI exits 2. |
| E2-fix1 in-loop eval errors uncounted | Resolved. `_error_total(evs)` goes into the row (`eval_policy_errors`), the total, and stops under #47. Verified with 1 and 2 workers. |
| E3-fix1 docs | Resolved per QA (RL_POLICY.md:123-133, 156, 196). |
| M1 empty batch | Resolved (`_batch` returns None; update skipped). |

## Findings
- **F1 (answer to the orchestrator's question): should weights be withheld after a `final_check` error?** My recommendation is yes, withhold or rename, but it is Saad's call because it reads #47 ("stop on first error"). Facts: today the exported weights stay on disk with their sha and only `summary.stopped` and exit status 2 signal the failure. A script or a human that picks up `weights.json` alone ships a policy that fell back to WAIT. The in-training path already withholds weights on error, so the two paths are inconsistent. Cost of the fix is about 3 lines in `train.py` (write to `weights.failed.json`, or delete, when `final["failed"]`), but a failed final check after 85 minutes then costs the run's weights. Middle option, no code: keep as is and make T07-train's brief say "a run counts only if exit 0 and `stopped == "max_iters"` or `"time_cap"`; otherwise the weights file is not to be used". I recommend the code change, because the run is expensive and the failure mode (silent WAIT policy shipped) is exactly what #47 exists to prevent. Not a blocker for the go/no-go; it is a question to put to Saad with it.
- **F2 (minor, reading of #47):** an eval-only error stops the run after that update's PPO step; no weights exported. Acceptable and consistent with #47. Say so in the T07-train brief.
- **F3 (minor):** the single `weights.json` is exported only at the end. A time-cap stop is `stopped == "time_cap"`, the normal finish when `max_iters` is None. QA's F4 applies: a consumer must accept `time_cap` and `max_iters` as success values.
- **F4 (minor, throughput):** the in-loop curve is a 2-start-pair curve (documented). The final check is 128 pure-Python duels run serially in the parent after training, at roughly 0.3 to 0.5 s each (estimate from the earlier 0.34 s untrained duel figure; not measured here), so plan on about 1 to 2 minutes on top of the 85-minute budget. The course cap is 90 minutes, so the margin is small. Suggest `--seconds 4800` or leave 5100 and accept about 87 to 88 minutes total; Saad's choice.

## Leak findings
None found. T16 touches only `tools/rl/train.py`, a comment in `env.py`, docs and tests; `agents/rl/**`, the encoder, observation and action mask are untouched (QA diff). The error count is a training-side integer, never returned to a seat or an observation.

## Baseline fairness
Unchanged since T07-fix1 (same affordances; nearest-figure targeting named as a confound). Not re-examined beyond the diff.

## Reward and training method
Unchanged. Last weights exported, `checkpoint_chosen_by_score: False`. Empty-batch skip only applies with fail-fast off, which the CLI never sets.

## Checkpoint reproducibility
Unchanged; `load_net` still checks the sha; the multi-worker identity test is in the existing suite and passed for QA.

## Train / held-out separation
Unchanged. `tools/rl/` reads only `TUNING_STARTS` (8 starts, 32 combos). Known N1 overlap with H6-4's B cell still blocks T08's freeze, not this run.

## Evaluation validity and confounds
No comparative evaluation was run or claimed. Confounds as before: tuning starts only, nearest-figure targeting, a 2-start-pair monitoring curve, one baseline opponent plus snapshots.

## Local inference performance
Not re-measured in this gate (no code on the inference path changed). No new number claimed.

## Replay and fallback
Fallback is counted and, from #47, treated as a failure in training and in `final_check`. Replay not touched.

## Training-run readiness
**Ready for Saad's approval**, wall time about 85 min training plus about 1 to 2 min final check (estimate). Still between this commit and the run:
1. Saad's explicit go-ahead on the full run (decision for him, quoted in the T07-train brief).
2. F1: Saad decides whether a failed `final_check` withholds weights (recommended: yes).
3. Merge path: T07, T07-fix1 and T16 live on gate/task branches and `int/reviewed-T07`; the run must start from a named commit with a clean tree (`summary.json` records `commit`). The orchestrator names that commit.
4. `numpy` from the `train` extra installed (`uv run --frozen --extra train`); run command and `--out` directory fixed in the brief; machine must not sleep for 85 minutes.
5. Decide the `--seconds` value given F4 and the 90-minute course cap.
6. After the run, read `summary.json` and exit status before trusting `weights.json` (`stopped` in {`time_cap`, `max_iters`}, `policy_errors == 0`).
7. Not part of the run but pending: N1 overlap (T08 freeze), held-out H6 run once per frozen policy.

## Student decision required
None.

## Requested next action
Orchestrator: Gate 3; put F1 and the `--seconds` choice to Saad with the go/no-go; write T07-train.
Touches the knowledge boundary or AI seat: yes (AI rival training and error accounting; no observation, action or hidden-information change).
