---
handoff_id: HO-T08-evaluation-specialist
task_id: T08
date: 2026-11-24
from: evaluation-specialist
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T08-qa.md@cf43ba1 (QA ACCEPT WITH NOTES, F-1 to F-4); docs/final/orchestration/reports/T08-tech-lead.md@deb8718; docs/final/orchestration/tasks/T08.md@0bba440 (amended late night); DECISIONS-2026-11-24.md@2f199e2 (#58-#61, #64-#66)
source_branch: gate/T08-eval
source_commit: see the commit that adds this file (the final message names it)
reviewed_commit: cf43ba1 (code = deb8718 plus QA probes)
verdict: ACCEPT WITH NOTES
---

# T08: Evaluation Specialist (Gate 2) report

Status: done. Verdict: **ACCEPT WITH NOTES**. No leak was reproduced, H6 is not reachable from training, the freeze and run-once mechanics work, and the scenario predicates match Saad's #9 words and the #58/#59 readings. Nothing blocks T09 *building on* this code. Two things must change before T09 produces a held-out claim: the run-once key (#64) and an honest statement of what H6 can show (F-3, power). Both are in the T08-fix1 list. H6 itself stays frozen.

## Suite
```
uv run --frozen --extra play --extra train --extra online pytest -q
1479 passed, 11 skipped, 8 xfailed, 2 warnings in 379.84s (0:06:19)
```
Run on gate/T08-eval at cf43ba1 (includes QA's probe file: 1468 + 11 passed, 4 + 4 xfailed; collected before my test file existed). My new file alone: `5 passed in 0.11s` (`tests/test_eval_T08_gate2.py`). No PPO run on H6, the real ledger was never written, no training, no `--live`.

## What I ran (all local, tuning split)
`run_versus_suite.py --split tuning --configs SvS,MvS,SvM --trials 3` with a fresh `--make-seed-key` key: 75 rows, 0 aborted, 21 s wall. Every row records the shipped weights hash `80e4a110...ba4c` (equals `SHIPPED_SHA256`), fallbacks 0, invalid 0, stale 0, measured latency per decision about 0.2 ms mean, 0.5 ms max (this machine, `time.perf_counter`, tuning start F5-c). Plumbing evidence only, not strength.

Result of the smoke worth stating: **every condition collapsed to exactly one distinct outcome across its 3 seeds** (25 conditions, 25 distinct). Seeds add nothing for scripted-vs-policy play, as T07-run1 E3 found, and the analysis says so correctly.

## Findings

| id | severity | finding |
| --- | --- | --- |
| E-1 | **moderate** | **#64 not built.** The ledger key is the weights hash alone (`tools/eval/run_versus_suite.py:138`). Saad chose weights plus engine commit. As built, a re-run after T19 or any rule change is refused outright; with #64 it is allowed but recorded. Also add: refuse a real held-out run if `git.commit == "unknown"` or `dirty` is true (`evaluation/suite.py:56` only counts tracked changes), so the commit in the key means something |
| E-2 | moderate | **Power of H6 as a confirmatory test is low** (see "T09 and power"). 4 starts give 8 distinct duels, not 24 |
| E-3 | minor | **#65 not built** (seat-B starts for D1, B2, I3, F5-a/b), so the per-seat claim in the protocol holds only for F5-c and H6. Until then the PPO is measured as the *subject* from seat A only |
| E-4 | minor | **I3 starts: two of three have the rival and the guard equidistant** (I3-a, I3-b, both 2 cells; I3-c the guard is nearer, 2 against 5). A nearest-figure striker succeeds only by tie-break in a and b; it fails c. Good: I3-c discriminates. Note for T09: I3 evidence from 3 starts is thin and the decoy stride is uncalibrated (already a stated confound) |
| E-5 | minor | **B2's flag does not require the disguise to survive.** A seat that drops its disguise (attacks) out of every guard's sight scores B2 success; `disguise_lost_frame` is recorded but not scored. The QA note is right. Not a defect of the build (Saad's wording does not say), but it is a reading for Saad (item 3 below) alongside #66 |
| E-6 | minor | **H-b is likely to fail for D1 and B2 and that is a result, not a defect.** The PPO was trained for duels only (disguise appears only as a 0.05 shaping term). Smoke: D1 0/3 against the baseline's 1/3; B2 1/3 each; I3 1/3 against 3/3. Report as found. PROTOCOL.md H-b should say these skills were not trained for, so a loss there is expected and is not a failed rival |
| QA F-1 | minor | confirmed (D1 credits the other rival's kill). Latent only while seat B is WAIT; becomes live with #65 if mirrored starts put an active rival opposite. Fix before #65 |
| QA F-2 | minor | confirmed (`analysis.duel_results` KeyError on `controllers: {}`); matters for T09 because an M seat failing to load weights is exactly this row |
| QA F-3 | minor | **accept and document; do not change H6.** See below |
| QA F-4 | minor | confirmed (`--replay` ignores `meta.json` split); one-line fix |

No leak: the probes (QA) plus my read of `evaluation/monitors.py`, `controllers.py`, `suite.py`: monitors are fed only from `on_frame` through `view.snapshot()`; controllers receive `observe` and the legal list; the disguised rival shows as `kind: guard`; the seed key is hashed to an id and never written; `agents/rl/**` and `tools/rl/**` do not import `evaluation` or read `heldout/` (test and source scan pass).

## QA F-3: recommendation (accept and document; keep H6 frozen)

Measured on the committed files (`tests/test_eval_T08_gate2.py` pins these):

- Training used **only the default arena guards**: `tools/rl/env.py:178` builds every episode with `arena.GUARD_POSTS`, which are two guards, in rooms 4 and 5 only, patrolling cols 1 to 8. There were never guards in rooms 1, 2, 3 or 6 during training.
- Of the 8 H6 guard posts, **5 (rooms 1 and 3) are in rooms that had no guard in training at all**. 3 are in rooms 4 and 5: two lie entirely inside the default patrols (h61-g1, h61-g2) and one partly (h63-g1, cols 7 to 9; col 9 is outside). So H6-1 is the one start whose guard layout is a subset of the training arena; H6-2 and H6-4 put *both* guards in rooms never guarded in training.
- No H6 configuration (both rival starts plus guard layout) equals any training configuration. The 6 training starts QA found inside H6 patrols are cells the policy has seen as walkable floor and as starts; it never saw a guard patrolling them in those rooms (rooms 1, 3), or saw a differently placed patrol (room 4).
- The tuning-scenario overlap (15 cells) concerns evaluator scenarios, which are not training data and are not tuned against H6; only start cells and post tuples need to be distinct there.

Why accept: (1) the held-out claim a policy can support is "unseen start pairs and unseen guard layouts", not "unseen cells". Full cell-level disjointness is not reachable in ten-column rooms when the training arena patrols span cols 1 to 8 in rooms 4 and 5 and the eight training starts touch all six rooms. (2) The overlap is not a leak: nothing about H6 reached training, no checkpoint was chosen on it (the shipped weights are the last export), and H6 has never been run. (3) Changing H6 now costs only a new hash in three places and a test update, but it would not buy a different claim, only a different partial overlap.

What to do instead (T08-fix1, no change to H6.json):
1. Rewrite PROTOCOL.md section 3 and the H6 README line "appear nowhere else": say *start cells and post tuples are disjoint; patrol ranges are not*, and state the numbers above (5 of 8 posts in rooms never guarded in training; H6-1 is training-like).
2. T09 reports H6 **per start**, with H6-1 labelled as the most training-like, so a reader can see whether a result rests on it.
3. Add a small evaluator-side script or test that prints this exposure table, so the claim is generated, not hand-written (my pinned test is the minimum).

If Saad wants more power instead (next section), that is the moment to change H6, and F-3 can be folded into it for free.

## T09 and power: can 4 H6 starts give a meaningful held-out claim?

A meaningful *descriptive* claim: yes. A *confirmatory* claim: only a strong one.

- Baseline and argmax policy are deterministic; the smoke showed 1 distinct outcome per condition. Seeds do not add trials. Four starts times two seat orders (MvS, SvM) give **8 distinct duels**, and the two orders of one start share geometry, so the effective n is between 4 and 8.
- Wilson 95 % lower bound for k wins of 8 (computed, pinned in the test): 8/8 gives 0.68; 7/8 gives 0.53; 6/8 gives 0.41; 5/8 gives 0.31. So H-a ("wins more than it loses") can be called supported only with 7 or 8 wins of 8, counting draws as non-wins. Anything weaker is reported with intervals that overlap and no strength claim, as PROTOCOL.md already says.
- Recommended T09 wording, fixed before the run: pre-register "support = at least 7 of 8 wins and 0 aborted; otherwise report the counts without a claim". Report per seat and per start.
- Option for Saad (item 1): extend H6 to 8 or more starts *before* the one run. H6 has not been run, so a new hash voids nothing. With 16 outcomes, 14 of 16 gives a lower bound of about 0.64. This is a decision on a frozen set and a design number, so it is Saad's; I recommend it only if he wants a confirmatory claim rather than a descriptive one.

## Statistics, comparison plan, and the rest of the checklist

- **Wilson on distinct outcomes, aborted in the denominator, mirror = one trial, per seat**: built and tested; the smoke output behaves as stated (`n<3` flag, F5 duel table by seat, mirror table). The scenario-success table counts a start's distinct outcomes as n, so with 3 starts the best possible interval is 0.44 to 1.00; say that next to every scenario rate.
- **Comparison plan (PROTOCOL.md section 6)**: sound (SvS control, MvS and SvM seat swap, fresh controllers, secret key). Add the pre-registered threshold above and the E-6 sentence.
- **Environment, observation boundary, reward and training method, checkpoint reproducibility**: not touched by T08 (T07 gates covered them). Weights hash in every row matches `SHIPPED_SHA256`.
- **Baseline fairness**: the scripted baseline is the same controller as T05 and runs through the same runner and observation. In the D1 starts it strikes the idle seat B (D1-b, D1-c `won:A`), which makes D1 fail on #59; this is the nearest-figure targeting confound and is reported, not tuned.
- **Replay fidelity**: replay test passes; replay is never new evidence. F-4 only.
- **Fallback**: aborted and harness-error rows are written and reported; the analysis crash on empty `controllers` (F-2) must be fixed first.

## Leak findings
None found. Probed: monitor and success text in observations, key and seed in rows and traces, H6 hash refusal before parse, `agents/rl/**` and `tools/rl/**` scans, WAIT-only held-out dry run.
Baseline fairness: same observation and macros; nearest-figure targeting confound in D1 and I3 stated.
Reward and training method: not in scope; no training run.
Checkpoint reproducibility: weights hash in rows equals `SHIPPED_SHA256`.
Train / held-out separation: start pairs and post tuples disjoint; patrol ranges overlap partly (F-3, accepted with documentation); 5 of 8 posts in rooms never guarded in training; H6 never run with a policy.
Evaluation validity and confounds: one distinct outcome per condition; 3 starts per skill scenario; decoy uncalibrated; seat A subject only until #65; H-b skills untrained.
Local inference performance: measured, 0.21 ms mean and 0.5 ms max per decision, tuning start F5-c, this machine (macOS Darwin 25.5, pure-Python policy). Browser not measured.
Replay and fallback: replay reproduces; fallbacks 0 in all 75 rows.
Training-run readiness: not applicable to this task (no training); T09 readiness is below.

## Proposed T08-fix1 (one Tech Lead task, tests first)
1. **#64**: ledger key = (weights SHA-256, engine commit); keep refusing a second run for the same pair; refuse a real held-out run on an unknown commit or a dirty tree (include untracked evaluation files); record every run. Test: same weights and commit refused, same weights new commit allowed and both lines listed.
2. **F-1** before **#65**: D1 credits a guard only if the subject is in the guard's room when it goes down (or the subject struck it).
3. **#65**: mirrored seat-B starts for D1, B2, I3, F5-a/b on the tuning split only; H6 unchanged; per-seat results in the analysis.
4. **F-2**: `duel_results` tolerates `controllers: {}`; the aborted section lists those rows. **F-4**: `--replay` reads `split` from `meta.json`.
5. **Docs**: F-3 wording (PROTOCOL.md section 3, H6 README), E-6 sentence under H-b, the pre-registered T09 threshold, the "best interval with 3 starts is 0.44 to 1.00" note, #66 wording kept.
6. Do **not** edit `H6.json` (hash stays `44da40ec...0847`) unless Saad takes the larger-H6 option, in which case it is a separate, re-hashed commit before anything runs.

## Items for Saad
1. **Larger H6?** Keep 4 starts (descriptive claim, support only at 7 or 8 wins of 8) or extend to 8 or more before the one run (confirmatory power). Recommendation: extend only if the final report needs a strength claim; otherwise keep and word it as descriptive.
2. **F-3**: accept and document (recommended) or re-freeze H6 with patrols chosen away from training patrols (not recommended).
3. **B2 and the disguise**: should B2 also require the disguise to survive? Today dropping it out of sight still passes (`disguise_lost_frame` recorded, not scored). Your call; the build follows #58 and #66 as decided.
4. **Pre-registered T09 threshold** (at least 7 of 8 wins) before the run.

## Not checked
H6 with the policy (forbidden); browser latency; concurrent ledger claims; the I3 decoy's resemblance to a real patrol; reward and training method (T07 scope).

## Unresolved findings
E-1 to E-6 and QA F-1, F-2, F-4 go to T08-fix1; F-3 is a documentation and Saad decision. None is a blocker for Gate 3 on the build itself, but T09 must not run before T08-fix1 item 1.

## Requested next action
Orchestrator: Gate 3 on T08 with the fix1 list; ask Saad items 1 to 4; brief T08-fix1.
