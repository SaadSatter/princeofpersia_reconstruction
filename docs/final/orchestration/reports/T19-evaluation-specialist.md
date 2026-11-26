---
handoff_id: HO-T19-evaluation-specialist
task_id: T19
date: 2026-11-25 ET
from: evaluation-specialist
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T19-qa.md@48915d4 (reviewed d32bbcb, implementation 7bbab99); docs/final/orchestration/tasks/T19.md@eaa0fc9; DECISIONS-2026-11-24.md #53-#55, #61, #71-#73 @eaa0fc9
source_branch: gate/T19-eval
source_commit: base 48915d4 (this report's own commit is recorded by the orchestrator)
reviewed_commit: d32bbcb608c9cb5a422ae4fed00d8d4136b6dc0d
verdict: ACCEPT WITH NOTES
---

# T19: evaluation-specialist report (Gate 2)

Status: done

## Work completed
Read the QA handoff, decisions #53 to #55, #61, #71 to #73 and the T19 diff (`fc02687..7bbab99`, `pop/versus.py`).
Checked the macro planner, the scripted baseline, R-V25 masking and suspicion, the PPO encoder's dependence
on `jumped`/`flipped`, and ran the shipped rival `ppo-run-1.json` on the pre-T19 engine (`fc02687`, extracted with
`git archive` into a scratch folder) and the post-T19 engine, seat-swapped, on the **tuning starts only**.
The H6 held-out set was not read or run (decision #61). No training, no `--live`. `agents/rl/**`, `tools/rl/**`,
`server/app.py` and `tests/test_eval_t18_rooms.py` were not touched.

Verdict: **ACCEPT WITH NOTES.** No leak, no new hidden-information path. Two minor notes (planner pricing, suspicion
surcharge) and one recommendation for Saad: **no retraining and no re-evaluation of the shipped weights is needed
for the T19 dynamics change**; the single H6 run (T09) should still be made on the post-T19 engine, as planned.

## Paths
- `evaluation/t19_compare.py` (new): seat-swapped tuning-start comparison, runnable on either tree.
- `tests/test_eval_t19.py` (new, 10 tests).
- This report. Scratch outputs (not committed): `old_*.json`, `new_*.json`, `oldv_*.json`, `newv_*.json` in the session scratchpad.

## Acceptance criteria -> evidence
| # | Gate 2 scope item (brief) | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Planner prices `JUMP_*` against the facing as a 4-frame turn; engine now faces and jumps at once (#71) | Confirmed, minor, behaviour-neutral | `test_planner_still_models_jump_against_facing_as_a_turn_but_the_engine_jumps_at_once`; `test_no_macro_ever_emits_a_jump_against_the_facing_...` |
| 2 | Scripted baseline | No change in behaviour or fairness | same tests; mirror control below; `test_baseline_tracker_counts_flipped_like_jumped_as_a_leap` |
| 3 | R-V25 masking and suspicion; QA minor 1 as a tell | Not a hidden-information tell; surcharge is real and bounded | `test_grace_flip_pays_...`, `test_surcharge_is_invisible_to_the_other_seat_...` |
| 4 | Hidden information under R-V35 | None found | see Leak findings |
| 5 | PPO encoder on "jumped" vs "flipped" | No dependence | `test_encoder_features_are_identical_when_jumped_and_flipped_are_swapped`, `test_duel_never_reports_jumped_any_more_...` |
| 6 | Re-evaluate or retrain `ppo-run-1.json`? | Recommendation below | comparison tables |

### 1. Planner pricing (decision #71)
`agents/baseline.py` `RoomView.predict` turns any `JUMP_x`/`RUN_JUMP_x` against the facing into a turn with no
displacement (`F_TURN`, no move); `agents/macros.py` `plan_path` prices it `FRAMES["turn"]=4`. The engine now flies
three cells at once (reproduced: facing right at room 2 col 4, `JUMP_LEFT` ends at col 1, the model says col 4).
Effect: **efficiency only.** Such a step is tied in cost and resulting pose with `LEFT`/`RIGHT`, which come first in
`ALL_ACTIONS` and win the strict `<` in `plan_path`, so a jump against the facing is never emitted. Measured over all
32 tuning combos, both rivals (PPO and baseline), `with` the facing: 216 + 308 (baseline) and 406 + 114 (PPO)
`JUMP_*`/`RUN_JUMP_*` inputs; `against` the facing: **0**. The planner misses a cheaper route (a turn is padded to one
6-frame decision, then the jump) but cannot plan into an unexpected position. `RUN_JUMP_x` against the facing still
turns first in the engine, so the model is right for it. Recommendation to the Tech Lead (not edited, outside my
paths): model `JUMP_x` against the facing as a jump in `RoomView.predict` and price it without the turn; this also
changes every plan, so it is a behaviour change for the rival and needs its own task, a rerun of the tuning
comparison and Saad's say.

### 2. Baseline fairness
Unchanged: same observation and macro affordances as the PPO rival; `versus_baseline.LEAPS` already contains both
effect names. Competence control (baseline vs baseline, 32 combos, seat/start swapped): 128 W / 0 D / 128 L over 256
episodes on both engines, identical final-state hashes for all 32 distinct games. The first seat start decides
the game, not the seat, which is the start-position confound already known (two tuning start pairs dominate; see
validity).

### 3. R-V25 masking and suspicion (QA minor 1)
Reproduced (QA's finding, my own aligned measurement): a disguised rival in a guard's sight that presses a direction
and then `JUMP_<same>` `gap` ticks later pays exactly **`SUSPICION_RUN x gap` = 4 or 8 extra points** on every aligned
flip frame, against a plain `JUMP_<same>` (`test_grace_flip_pays_...`). The kid never moves in those frames.
Assessment as a tell:
- The meter is never in the other seat's observation. B sees a figure of kind `guard`, with motion effects drawn only
  from the set a plain disguised jump or run already shows (`moved` at run frames, `flipped`); position does not
  creep during the discarded run frames.
- A disguised flip is already a non-guard motion that R-V25 lets through because it raises suspicion; the window adds
  no new effect name. So it is not a hidden-information leak and it does not make a disguised rival easier to spot.
- It is a small, consistent rule inconsistency: the same final move costs 4 to 8 of 100 more depending on the
  inputs that preceded it. A disguised AI never emits direction-then-jump pairs (macros send one input per decision of
  6 frames), so the rival is not affected; only human seats are. **Accept, and name it in R-V35**, or have the Tech Lead
  not charge frames the window discards. Saad's choice (rule number), not mine.

### 4. PPO encoder, "jumped" versus "flipped"
`agents/rl/encoder.py` mentions the two names only inside `LEAPS` (`me_leaping`, track `leap`); the existing
source-scan test (`test_eval_T07run1_rerun.py`) still holds, and my test renames `flipped` to `jumped` on a live
observation (own move and the other rival's) and shows the whole 251-feature vector is bit-identical. Post-T19 a duel
never reports `jumped` at all (every directional jump, standing or running, is `flipped`); the policy never saw a
difference between the two names in training, so the change of name cannot move its output.

### 5. Does the shipped rival need re-evaluation or retraining? (recommendation for Saad)
Evidence: the shipped weights on the tuning starts, seat-swapped, pre-T19 engine (`fc02687`, extracted in a scratch
folder, verified by `pop.versus.__file__` and no `GRACE_TICKS`) versus post-T19 (`48915d4`). `evaluation/t19_compare.py`,
32 combos x 8 seeds. All rounds counted, 0 aborted, 0 fallbacks in every row.

| Condition (A and B swapped) | Engine | W / D / L | Win rate, Wilson 95% | Mean frames | Final-state hashes |
| --- | --- | --- | --- | --- | --- |
| PPO vs scripted baseline | pre-T19 | 240 / 16 / 0 of 256 | 0.938 (30 of 32 distinct games) [0.80, 0.98] | 859.2 | identical to post-T19 |
| PPO vs scripted baseline | post-T19 | 240 / 16 / 0 of 256 | same | 859.2 | 30 distinct, identical set |
| baseline vs baseline (control) | pre / post | 128 / 0 / 128 of 256 | 0.5 | 738.4 | identical, 14 distinct |
| PPO vs random-input seat | pre-T19 | 255 / 0 / 1 of 256 | 0.996 [0.978, 0.999] | 335.6 | 253 distinct |
| PPO vs random-input seat | post-T19 | 254 / 0 / 2 of 256 | 0.992 [0.972, 0.998] | 334.1 | 252 distinct |
| baseline vs random-input seat | pre-T19 | 244 / 0 / 12 of 256 | 0.953 [0.920, 0.973] | 321.5 | 232 distinct |
| baseline vs random-input seat | post-T19 | 239 / 0 / 17 of 256 | 0.934 [0.896, 0.958] | 318.6 | 232 distinct |

Reading, honestly:
- Against the macro baseline the games are **bit-identical** before and after T19: both macro layers emit one input per
  6-frame decision, never a jump against the facing and never a direction and a jump within 2 ticks, and a standing jump
  lands where it did. The only change, the effect name, is invisible to the encoder (item 4). So there is nothing to
  re-learn on this opponent.
- The random-input seat is the stress test: it does exercise `JUMP_*` against the facing and the grace window. Every
  difference there is inside noise (PPO 255 to 254 wins; baseline 244 to 239, Wilson intervals overlap, no test would
  call it significant), and nothing aborted or fell back. These are not strength claims.
- Caveats. Those 256 PPO-vs-baseline episodes are only **32 distinct games** (engine seed barely varies them; 30 distinct
  final states), so the n for the Wilson interval is 32, not 256. Tuning starts only (8 pairs, 32 combos); nearest-figure
  targeting; the policy was trained on exactly these starts, so none of this says anything about unseen scenarios.
  Humans produce the new inputs (direction-then-jump, jump against the facing) that the baseline never does; no human
  trial was run here.

**Recommendation to Saad: do not retrain, and do not hold T09.** Keep `ppo-run-1.json` (sha unchanged:
`80e4a110...5aba4c`). The H6 run (decision #61) should be made once on the post-T19 engine as already planned; it needs
no extra pre-run, and the post-T19 tuning result above is its sanity check. Retrain only if Saad later changes the
macro layer (for example the planner fix in item 1) or the reward; a new run would then train on the new dynamics
anyway. This recommendation is on tuning scenarios only and is not evidence of strength.

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q tests/test_eval_t19.py
10 passed in 9.47s
uv run --frozen --extra play --extra train --extra online pytest -q
1532 passed, 12 skipped, 4 xfailed, 2 warnings in 394.48s (0:06:34)
```
`node --test web/` not run by me (no web file changed in this gate); QA reported `keys.test.js: 9 passed`.
Comparison commands (reproducible): `PYTHONPATH=. uv run --frozen --extra train python evaluation/t19_compare.py <ppo|mirror|ppo_rand|base_rand> 8 vary`, run in the post-T19 tree and in a `git archive fc02687` extract.

## Findings
Reproduced:
1. [minor] `agents/baseline.py` `RoomView.predict` / `agents/macros.py` `plan_path`: `JUMP_*` against the facing is
   still modelled as a 4-frame turn (decision #71 keeps the instant turn). Behaviour-neutral (never emitted, 0 in 64
   duels); a missed shortcut only. Owner: Tech Lead, a separate task.
2. [minor] `pop/versus.py` `Duel._grace_jump`/`_suspect`: discarded run frames pay suspicion (4 per frame, 4 or 8 total).
   Not a leak (meter never observed; no new effect name); a rule-statement or rule-choice item (QA minor 1, confirmed).

Unverified, not claimed: browser and pygame behaviour; the hosted-page tick catch-up shortening the window; human play
against the rival with the new inputs.

## Leak findings
None found. Probed: the grace rule reads only the seat's own pending input, move frame and last move (no other-seat
data); R-V25 `GUARD_MOTIONS` filter and `suspicious_rise` unchanged, and a disguised A in the window shows B only
`kind: guard` figures with effects already visible for a plain jump or run; the `jumped`/`flipped` rename cannot reach
a feature; observation key sets are unchanged (QA's six scripts plus mine).

## Baseline fairness
Unchanged by T19 (same observation, same macros, same planner; `LEAPS` includes both names). Competent: it beats a
random-input seat 239 to 244 of 256 post/pre and splits the mirror control exactly. See item 2.

## Reward and training method
Not changed by T19 and not re-read beyond what the brief asks. The shipped run's recorded facts stand (`summary.json`:
final weights, `checkpoint_chosen_by_score: false`, seed 0, 1,487,955 steps, 4812.6 s, commit `f08c1a8`). The weights
were trained on the pre-T19 engine; see item 5 for why that does not matter against the baseline.

## Checkpoint reproducibility
Unchanged. The shipped file still loads only with its SHA-256 (`80e4a110...`): `tests/test_rl_run1_shipped.py` is in
the suite below. No retrain, so no new same-seed check.

## Train / held-out separation
Unchanged and respected: I read and ran only `env.TUNING_STARTS`; `evaluation/heldout/` does not exist in this tree
and was not opened; H6 is reserved for T09 on the post-T19 engine (decision #61).

## Evaluation validity and confounds
Seat-swapped, 32 combos, fresh controllers per episode, every episode counted, 0 aborted, 0 fallbacks. Confounds: tuning
starts only and policy-trained on them; effectively 32 distinct games against the macro baseline; the first start
decides the mirror control; nearest-figure targeting; no secret `seed_key` (tuning, not a comparative claim); same
engine seed 0 as training in the first four rows. Pre/post identical hashes show a controlled A/B of the engine alone.

## Local inference performance
Measured, Apple arm64 laptop, pure-Python path (`make_rl_rival`), one duel from the default starts: 155 decisions,
mean 0.216 ms, p50 0.101 ms, p99 1.34 ms, max 1.47 ms per decision. Far inside the 6-frame cadence. Browser build
not measured here.

## Replay and fallback
Not re-tested beyond the suite: determinism and replay tests (`test_trace_replay.py`, QA's replay probe) pass in the
suite below. Fallback count was 0 in every comparison row; the labelled `WAIT` fallback path is unchanged and its tests
are in the suite.

## Training-run readiness
Not applicable. No training was run and this gate recommends none for T19.

## Known limitations
See item 5 caveats; no human, browser or online trials; no held-out run by design.

## Unresolved findings
Findings 1 and 2 (minor).

## Requested next action
Orchestrator: Gate 3 on `gate/T19-eval` (my commit) with QA's. Tech Lead (separate task, if Saad wants it): planner model of
`JUMP_*` against the facing; R-V35 sentence or change for the discarded run frames. T09 may run H6 on the post-T19 engine.

## Student decision required
Saad's decisions, not mine: (a) accept the 4 to 8 suspicion surcharge (state it in R-V35) or stop charging discarded
run frames; (b) agree that `ppo-run-1.json` is kept and not retrained for T19.
