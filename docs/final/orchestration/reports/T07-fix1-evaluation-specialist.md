---
handoff_id: HO-T07-fix1-evaluation-specialist
task_id: T07-fix1
date: 2026-11-24
from: evaluation-specialist
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T07-fix1-qa.md@9f7d310 (which consumed T07-fix1-tech-lead.md@2c9915f); brief docs/final/orchestration/tasks/T07-fix1.md@55a7240; earlier findings GATE-wave3-evaluation-specialist.md@f02314b
source_branch: gate/T07-fix1-eval
reviewed_commit: fa0c840 (code), 2c9915f (tech-lead report), 9f7d310 (QA)
verdict: ACCEPT WITH NOTES
---

# T07-fix1: Gate 2 evaluation report

Status: done

## Verdict
**ACCEPT WITH NOTES.** E4, E1 and E3 are resolved as decided. No leak, no held-out reachability, no failed criterion. Decision #47 is treated as decided. Three small items and one overlap (N1) are listed with their cost. None of them blocks the full run on technical grounds. What remains before a go/no-go is listed under "Training-run readiness".

## Work completed
Read the diff `ae90c8c..fa0c840` for `agents/rl/policy.py`, `tools/rl/env.py`, `tools/rl/train.py`; read the QA report and RL_POLICY.md; read candidate H6 with `git show 25e4587:evaluation/heldout/H6.json` (not copied). Added `tests/test_eval_T07fix1.py` (4 tests). Ran the full suite. No training run was started and no paid call was made.

## Tests run
```
uv run --frozen --extra play --extra train pytest -q tests/test_eval_T07fix1.py -s
4 passed in 4.03s
uv run --frozen --extra play --extra train pytest -q
1131 passed, 11 skipped, 3 xfailed in 166.73s (0:02:46)
```
(3 xfailed: the 2 from the base and QA's strict M1.)

## Earlier findings: resolved?
| Finding | Decided | State at fa0c840 |
| --- | --- | --- |
| T07-E4 errors invisible | counted and visible; #47 stop on first error | **Resolved.** `TrainPolicy.choose` counts exceptions, answers WAIT, `play_episode` returns `policy_errors` (learner plus snapshot opponent). `log.jsonl`, `summary.json` carry it. `train()` raises `TrainingError`, writes no weights, CLI exits 2. QA ran a real subprocess; I ran the **2-worker fork pool** (QA's open point): the injected error is counted in the returned episode dict, the run stops, `summary.json` has `stopped: policy_error`, no `weights.json`. |
| T07-E1 (#43) train without traps | `RIG_TRAP` reserved and masked | **Resolved.** `agents/macros.py` untouched; RL_POLICY.md lines 54-57 state it plainly (PPO rival does not set traps in G2/G3, traps human-only, #43). |
| T07-E3 (#44) more starts | about 6 more, disjoint from held-out | **Resolved, one overlap (N1).** 8 starts, six new in rooms 1-6, rows 2, columns 0-9; QA verified disjoint from `HELD_OUT_STARTS`, `LOWER_HELD_OUT_STARTS` and all four candidate H6 cells. The overlap is only in the old midterm start. |

## Findings (new)
- **E1-fix1 (minor, reproduced by source inspection and test)** `tools/rl/train.py:final_check` never reads `rival.policy_errors()`. `final_check` runs the **exported pure-Python path**, which is the one that ships. An inference error there would show as a weak win rate, not as an error. Parity test and the training-side count make this unlikely, but the one place that checks the shipped weights is the one place not counted. Fix: assert `rival.policy_errors() == 0` per duel and add the total to `summary.json`. Test: `test_final_check_does_not_read_rival_error_counts` (asserts the gap; invert it when fixed).
- **E2-fix1 (minor)** The per-update greedy evaluation episodes (`evs`) are not summed into `policy_errors`. They run the same `TrainPolicy` code on starts 0 and 1, which the rollouts also reach, so a real error would be caught there anyway. Test: `test_in_loop_eval_errors_are_not_summed`.
- **E3-fix1 (minor, documentation)** RL_POLICY.md still calls the stop-on-error rule "Proposed, for Saad" (lines 153, 185). It is decided (#47). The doc also says the per-update evaluation and `final_check` cover only the two midterm starts. In-loop is true; `final_check` runs all 32 combinations (QA N2), i.e. 128 pure-Python duels. Also says the shared cell is H6-4's "A start"; it is H6-4's B slot.
- **N1 overlap**, see below.

## Answers to QA's notes
**Start balance (8 tuning starts).** Measured: scripted baseline vs itself, one seed (7), both placements, 16 duels, 3,600-frame limit. Every duel is decisive (no draws, no limit-outs). The winner follows the **start position, not the seat**: swapping the placement flips the winning seat in all 8 pairs. The second start of the pair wins in pairs 0, 1, 5, 6, 7; the first wins in pairs 2, 3, 4. So the set has no all-one-sided bias that a learner could exploit by position, and the 32 combinations (both seats, both orders) cover each side. Lengths: pairs 0 and 1 end at 1,749 frames, 5-7 at 333-813, pair 2 at 387, **pair 3 at 115 and pair 4 at 74 frames**. Those two give very short episodes (little signal, many resets per update, and a possible quick guard or fall win); they are still valid, and with 4 of the 8 pairs shorter than 400 frames the first updates will be fast. Not a blocker; if a later run shows no learning, look here. One seed only: this is a balance probe, not a strength result.

**In-loop evaluation covers 2 of 8 start pairs.** Confirmed (`_combo(k)` for `k < 8` gives pairs 0 and 1). Not a must-fix. Reason: the end-of-run `final_check` covers all 32 combinations, and the training batch itself covers all 8. The cost of the blind spot is monitoring only: a lower-room regression would not appear in the curve. Fixing it by `eval_episodes=32` roughly quadruples the evaluation cost per update (about 0.34 s per untrained duel on an M4, estimate) and cuts the number of updates in the fixed 85-minute budget. Recommendation: leave the number, fix the sentence in the doc, and disclose that the curve is a 2-start curve. If Saad prefers the lower rooms visible, rotate the evaluation combinations per update at the same cost (a trainer change, Tech Lead, not mine).

**Multi-worker error propagation.** Tested here, passes (above). Exceptions raised inside a worker outside `choose` would raise out of `pool.map` and also stop the run loudly.

**Must anything be fixed before the full run?** No fix is *required*. Recommended in one small tech-lead commit before the run (about 10 lines plus text): E1-fix1 and E3-fix1. They protect the only evidence about the shipped weights and the accuracy of the record; the run's integrity does not depend on them. If the orchestrator wants to count that as fix 2 of 2, it can instead log E1-fix1 as a known limitation and read `summary.json` by hand after the run.

## N1: tuning start `(1,2,3,+1)` equals H6-4's B cell (candidate H6 @ 25e4587)
Facts: the cell (room 1, row 2, col 3, facing +1) is the tuning pair `((1,2,3,+1),(3,2,6,-1))`'s first start. In H6-4 it is B's start, paired with A at `(3,2,5,-1)`. The tuning partner is `(3,2,6,-1)`, so the **pair differs**, and tuning uses the default guard posts while H6 brings its own. H6 is an unfrozen, unreviewed WIP; nothing is frozen and no held-out result exists.

- **Does it block training?** No. Training reads only `TUNING_STARTS`; the candidate H6 is not on this line and not read by `tools/rl/` (source scan: the only mention of "held-out" in `tools/rl` and `agents/rl` is a docstring). The rule at stake is "no tuning against held-out", which concerns scenarios that will be frozen. The risk is one H6 start sharing a cell with 2 of the 32 training combinations, with a different partner and guards: weaker than a full overlap, but the criterion "starts that appear nowhere else" in H6's own definition would be false for H6-4.
- **It blocks T08's freeze,** not this run, until one of the two is done.
- **Option A: T08 changes H6-4 (move B's cell).** Cost: one edit in an unreviewed candidate, no retraining, no change to the midterm-two starts or to any existing test. T08 should also re-run the disjointness check against the 8 starts. Recommended. Pick the replacement from the cell set, not from policy performance.
- **Option B: remove the midterm start from `TUNING_STARTS`.** Cost: a code change in `tools/rl/env.py` and edits to `tests/test_rl_train.py` and `tests/test_rl_fix1_starts.py` (fix attempt 2 of 2 for T07-fix1, so the escalation rule applies to the next failure), the documented MACROS.md starts no longer lead the list, the recorded smoke numbers change, and the training set drops to 7 starts. It protects nothing A does not.
- The doc sentence "A start of H6-4" should read "B start".

## Leak findings
none found. Probed: the diff touches no encoder, observation, mask or `macros.py` code; the only new fields (`policy_macro`, `policy_errors`) hang off the controller on the runner side and are not part of `observe(seat)`. The error path returns the literal `"WAIT"`, and error text is never fed back to the policy. The earlier T07 leak review (GATE-wave3) stands for the unchanged encoder.

## Baseline fairness
Unchanged (`versus_baseline.py` and `macros.py` untouched). The baseline-vs-baseline run above also shows it plays decisive, position-driven duels on all 8 starts (it wins or loses by start, not by passivity).

## Reward and training method
Unchanged apart from monitoring: reward, shaping, opponent mix and `TrainConfig` hyperparameters not edited (the only new field is `fail_on_policy_error`, default true). Last weights exported; `checkpoint_chosen_by_score: false` remains. Stop-on-error is a stop, not a model choice. Disclosures still due in T08: argmax at inference versus sampling in training (T07-E6), "heart dealt" shaping for any opponent heart loss (T07-E7).

## Checkpoint reproducibility
`load_net` still demands the SHA-256 (not touched). Smoke determinism test passes in the suite. A run that stops on error now writes `weights_sha256: null` and no weights, so a failed run cannot be mistaken for a checkpoint. Parity test now uses at least 200 observations from six seeds with a fresh `Encoder` per duel and the 1e-9 tolerance (QA confirmed it is not weakened).

## Train / held-out separation
`evaluation/heldout/` does not exist on this line; T08 has not frozen H6 (so no file hash and no run-once check yet). `tools/rl` and `agents/rl` never read it. Disjointness of the 8 starts from the base lists and from the candidate cells holds except N1. T08 must re-check against the H6 it actually freezes (QA N4).

## Evaluation validity and confounds
No comparative run in this task. Confounds to carry to T08: 8 starts only (over-fitting expected), in-loop curve covers 2 of the 8 (E3-fix1), nearest-figure targeting (I3/F5), fixed training and eval seeds that are not T08's secret `seed_key`, and one start-order bias in the baseline-vs-baseline probe (seed 7 only).

## Local inference performance
Not re-measured. Training speed is the doc's estimate: about 0.34 s per untrained, early-ending duel on an Apple M4 (8 duels in 2.7 s, measured by Gate 2 earlier; labelled estimate in the doc for the full run). This task's tests (4 tests including a 2-update 2-worker run) took 4.03 s.

## Replay and fallback
Not changed. The labelled fallback for runner-level failures is untouched. Inference errors are now counted per episode in training and per controller (`policy_errors()`) in play, and fatal in training. Gap: `final_check` does not read the count (E1-fix1). The in-play counter still has to be written into game results by whoever runs the seat (T08/T13).

## Training-run readiness
**Ready for Saad's approval, with two doc/count items recommended first.** Remaining between this commit and a go/no-go, in order:
1. Gate 3 and integration of fa0c840 (and the QA and eval test files) into the line the run will start from, so `summary.json`'s commit is the reviewed one and the working tree is clean.
2. A small tech-lead commit (recommended, not blocking): E1-fix1 (count errors in `final_check`), E3-fix1 (mark #47 decided, correct the `final_check` coverage sentence, the "A start" wording, and `env.py:46` comment). M1 (QA, non-default switch) can wait.
3. Saad's explicit go for the run, quoted in the brief, naming the time cap (default 5,100 s, cap 90 min), 2 workers and the output directory. Also confirm he accepts the in-loop curve covering 2 of 8 starts.
4. T08 (parallel, not blocking the run): resolve N1 by Option A before freezing H6.
Expected cost: about 85 minutes wall time on the M4, estimate, 2 worker processes. Then a `final_check` of 128 pure-Python duels (a few minutes, estimate, not timed). If a policy or encoder error occurs the run stops with exit 2 and no weights; that is a diagnosis, not a retry in the same run.

## Student decision required
None.

## Requested next action
Commit to review: this branch tip (report and `tests/test_eval_T07fix1.py`). Orchestrator: Gate 3; decide whether to ask the tech lead for the E1-fix1/E3-fix1 commit; take N1 to T08; then ask Saad for the run.
Touches the knowledge boundary or AI seat: yes (AI seat training and its error accounting); this is the Gate 2 review.
