---
handoff_id: HO-T24-evaluation-specialist
task_id: T24
date: 2026-11-25
from: evaluation-specialist
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T24.md@b1514bc; DECISIONS-2026-11-24.md #94, #98 @a127fc2; docs/final/orchestration/reports/T24-tech-lead.md@6f0975c; docs/final/orchestration/reports/T24-qa.md@48176a5
source_branch: gate/T24-eval
source_commit: fa09273 (code), this report's own commit follows
reviewed_commit: 6f0975c (QA probes at 48176a5)
verdict: ACCEPT WITH NOTES
---

# T24: evaluation-specialist report (Gate 2)

Verdict: **ACCEPT WITH NOTES.** No leak. The scripted baseline and the shipped PPO rival behave
bit-identically before and after T24 on the tuning starts. QA F1 is real at the engine level but never
occurs in a duel (0 of 768 macro-rival episodes). Nothing is required before Gate 3; two small fixes are
recommended (F1, F2).

Not done, by instruction: no training, no `--live`, no H6 (`evaluation/heldout/` not opened). Tuning starts only.

## Paths
- `evaluation/t24_compare.py` (new): `t19_compare` plus a counter of DOWN-takes and DOWN sword pickups.
- `tests/test_eval_T24_f1.py` (new, 3 tests): the F1 reproduction.
- This report. Scratch outputs (not committed): `old_*.json`, `new_*.json` in the session scratchpad.

## Before / after, tuning starts, seat-swapped
`ppo-run-1.json` (sha unchanged) and the scripted baseline. 32 combos x 8 engine seeds (`vary`) = 256
episodes per row, every episode counted. Base engine: `git archive 1a515ca` into a scratch folder
(verified: `has_kneel_path: false` there, `true` on 6f0975c). After: this tree (6f0975c plus QA probes).

| Condition | Engine | W / D / L | Mean frames | Distinct final states | Seed-0 final hashes | Fallbacks | Aborted | DOWN-takes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PPO vs scripted baseline | 1a515ca | 240 / 16 / 0 | 859.2 | 30 | identical (32 of 32) | 0 | 0 | n/a |
| PPO vs scripted baseline | 6f0975c | 240 / 16 / 0 | 859.2 | 30 | identical | 0 | 0 | **0** |
| baseline vs baseline (control) | 1a515ca | 128 / 0 / 128 | 738.4 | 14 | identical (32 of 32) | 0 | 0 | n/a |
| baseline vs baseline (control) | 6f0975c | 128 / 0 / 128 | 738.4 | 14 | identical | 0 | 0 | **0** |
| PPO vs random-input seat (stress) | 1a515ca | 254 / 0 / 2 | 334.1 | 252 | identical (32 of 32) | 0 | 0 | n/a |
| PPO vs random-input seat (stress) | 6f0975c | 254 / 0 / 2 | 334.1 | 252 | identical | 0 | 0 | 3 (all by the random seat) |

Changed duels: **0** in every row on all compared hashes, outcomes and means. Unintended disguises by either macro rival:
**0** (DOWN-takes are 0 in both macro-only rows; the 3 in the stress row are the random seat pressing DOWN over a body, which is
the new rule working, and they did not change any outcome or seed-0 hash). Fallbacks 0. Policy errors 0
(no aborted episode). Only seed-0 hashes were compared per game; the aggregates (outcomes, means, distinct-state counts) are equal
to the decimal for all 768 episodes. Draws: 16 `time_up` in PPO vs baseline, same on both engines (the same two start pairs, as at T19).
Caveats as T19: 256 PPO-vs-baseline episodes are only 32 distinct games; tuning starts, which the policy was trained on; no strength claim.

## Checks
- **Action rule both seats share.** `_kneel_target` / `_kneel` live on `Rival`, so seat A and B go through the same code. R-V25: QA's
  `test_whole_world_identical_for_down_and_take_including_suspicion` compares both seats' full observations, the suspicion meter,
  both legal lists and the end-state digest every frame, over and beside; I re-read it and the diff and found no path where DOWN
  exposes something TAKE does not (the kneel is the same `took_uniform` plan). R-V19: DOWN-take is the TAKE generator, so it
  raises and lowers suspicion identically (same test). Knowledge boundary: `_kneel_target` reads only the rival's own cell,
  posture and the downed guard in reach, all of which TAKE already reads; no new observation key, legal action or error text.
- **Macro layer / baseline / PPO.** `agents/versus_baseline.py` and `agents/rl/` never name DOWN. Only `agents/macros.py` emits it
  (`_hang_drop`, planned from `ALL_ACTIONS`). Measured: 0 DOWN-takes in 512 macro-rival episodes.

## F1 (QA minor): real, narrower than QA thought, not reached in practice
The T24 posture guard covers a rival that is already **hanging** (the let-go DOWN). It does not cover the *first* DOWN, the standing
hang-down at an edge (`engine._down`: unsupported cell ahead, then `HANG_DOWN`). A standing rival at an edge whose own cell holds
a downed uniformed guard now takes the uniform instead of hanging. Reproduced (`tests/test_eval_T24_f1.py`, room 1 row 0 col 7,
body on the cell, hole ahead at col 8: DOWN gives `took_uniform`, disguised, still standing; with no body it still hangs).
The planner's `_hang_drop` checks `(r, c) in self.bodies` only for the target cell, not the own cell, so it can plan DOWN there. The
bodies are rare (a guard knocked out exactly on an edge cell) and 768 macro-rival episodes never hit it. Effect if it did: 12 frames
spent, an unplanned disguise (arguably useful), the next decision re-plans; no crash, no hidden-information effect.
**Recommended fix (small, `pop/versus.py`, for the Tech Lead; not edited by me):** in `_kneel_target`'s uniform branch return `None`
when this DOWN would start a hang-down, i.e. when the cell ahead is not blocked and not supported (the same test `engine._down` uses
at 470). Then a ledge-edge DOWN keeps its old meaning and `TAKE` takes the uniform there. Alternative, in the macro layer, is to
avoid planning a hang-down from a body cell; the engine fix is simpler and protects humans too. **Not required before Gate 3**
(no measured effect; rare; test documents it). If the orchestrator wants the rule closed, do it in the same follow-up as F2.

## F2 (QA minor): VERSUS_SPEC wording vs #98
Confirmed. `docs/final/VERSUS_SPEC.md` R-V17 at 6f0975c says "then the uniform on the next `DOWN` or `TAKE`". After a sword pickup
the sword is drawn, where DOWN is a stance change, so under decision #98 ("sheathe or T") the next step is `SHEATHE` then `DOWN`, or
`TAKE`. Suggested sentence: "...picked up first (R-V09); with the sword drawn, `SHEATHE` then `DOWN`, or `TAKE`, takes the uniform
(Saad, decision 98)". Docs only, same follow-up. Not required before Gate 3; fix before the key hints (T25) quote it.

## Evidence affected?
No. T08 and T09 evidence was produced on the earlier engines, and T24 changes behaviour only when `DOWN` is pressed beside or over a
downed uniformed guard, which neither macro rival does. The table above is the engine-only A/B showing no change for either rival
on the tuning starts. T19's recommendation stands: keep `ppo-run-1.json`, no retraining; the single H6 run (T09, decision #61) should
be made once on the final engine, so its report should name the engine commit. Any old trace that contains a human `DOWN` beside a body
would replay differently (that is the intended rule change); no macro-rival trace does.

## Leak findings
None found. Probed: observation key sets and legal lists (equal for DOWN-take and TAKE per QA's test and the diff); the other seat's
view of the kneel; no new error or log string; no RNG, seed or hidden-state read in the new code.

## Baseline fairness
Unchanged: same observation and macros as the PPO rival; competent (beats a random seat 239 to 244 of 256 earlier, splits the mirror
control exactly 128/128 here).

## Runtime bounds, local inference, replay and fallback
Not touched by T24. Fallbacks 0 in every row; the labelled `WAIT` fallback and replay tests are in the suite below. Latency not
re-measured (no inference change; T19 figure stands: mean 0.216 ms per decision).

## Reward, training method, checkpoint reproducibility, train / held-out separation
Unchanged and not re-read. Shipped file still loads by its SHA-256 (`tests/test_rl_run1_shipped.py` in the suite). Tuning starts only;
H6 not opened.

## Evaluation validity and confounds
Controlled engine-only A/B (same seeds, same weights). Confounds as T19: 32 distinct games vs the baseline, first start decides the mirror,
tuning starts trained on. Only seed-0 hashes compared per game; aggregates equal across all episodes.

## Live-run readiness / Training-run readiness
Not applicable to T24. None requested.

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q   (clean committed tree, fa09273)
1986 passed, 11 skipped, 5 xfailed, 2 warnings in 340.54s (0:05:40)
uptime at finish: 23:44 up 11 days, 2:05, 2 users, load averages: 9.20 11.11 11.10
```
Comparison commands: `PYTHONPATH=. python evaluation/t24_compare.py <ppo|mirror|ppo_rand> 8 vary` in this tree and in a `git archive 1a515ca` extract.
`node --test web/` not run (no web file changed).

## Findings
1. [minor, F1] ledge-edge DOWN over an own-cell body takes the uniform instead of hanging; unreached by either macro rival; fix recommended.
2. [minor, F2] VERSUS_SPEC R-V17 "next DOWN or TAKE" contradicts #98 (drawn sword: SHEATHE first).
3. [note] the random-input seat now disguises itself via DOWN over bodies (3 of 256 episodes); intended by #94, no outcome change.

## Known limitations
No human, browser or online trial; hashes compared at seed 0 only; tuning starts only.

## Unresolved findings
F1 and F2 (minor).

## Before Gate 3
**None required.** Optional follow-up task (Tech Lead): F1 engine guard plus F2 sentence, rerun `tests/test_eval_T24_f1.py` (the third test then flips to
"still hangs") and `evaluation/t24_compare.py`.

## Requested next action
Orchestrator: Gate 3 on `gate/T24-eval` with QA's report.

## Student decision required
none
