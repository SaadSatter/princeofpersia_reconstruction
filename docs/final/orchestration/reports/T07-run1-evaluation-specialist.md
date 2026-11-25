---
handoff_id: HO-T07-run1-evaluation-specialist
task_id: T07-run1
date: 2026-11-24 ET
from: evaluation-specialist
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent
consumed: docs/final/orchestration/reports/T07-run1-qa.md@b3d1361
source_branch: gate/T07-run1-eval
reviewed_commit: 8c1a3af (QA probes b3d1361)
verdict: ACCEPT WITH NOTES
---

# T07-run1: Evaluation Specialist report (Gate 2)

Verdict: **ACCEPT WITH NOTES**. Commit reviewed: 8c1a3af (base f08c1a8), with QA's b3d1361.

## 1. Rerun of the final check (tuning starts, not held-out, not a strength claim)
`tools.rl.train.final_check(SHIPPED_WEIGHTS, SHIPPED_SHA256, 4)`: pure-Python path, committed
`agents/rl/weights/ppo-run-1.json` through the constants, all 32 tuning combos x 4 seeds = 128 duels,
seat-swapped, 11 s.

| | Wins | Draws | Losses | Policy errors |
| --- | --- | --- | --- | --- |
| Rerun, total | 120 | 8 | 0 | 0 |
| Rerun, rival in seat A | 60 | 4 | 0 | |
| Rerun, rival in seat B | 60 | 4 | 0 | |
| `summary.json` | 120 | 8 | 0 | 0 |

Identical to the summary. Every win was a duel win (`won:A`/`won:B`); no fallback or swallowed
inference error (`rival.policy_errors()` = 0 over all 128).

The 8 draws: all `draw:time_up` at 3,600 frames, all in two combos, 9 and 11 (tuning start pair
index 2, `((1,2,8,-1),(4,2,4,1))`, rival on the second start, once as seat A, once as seat B), 4 of 4
seeds each. So it is one scenario, not eight: the rival and baseline never settle it. Both seats issued about
470 inputs, so it is a stalemate or mutual avoidance, not a crash or idle policy. I did not trace
it further. Note also that the 4 seeds of a combo gave the same result here, so 128 duels are
fewer independent trials than 128; this matters for any later claim.

New eval test: `tests/test_eval_T07run1_rerun.py` (2 tests, 11 s): the rerun equals the summary
counts; encoder scan (below).

## 2. Dependence on `jumped` / `flipped`, and T19 (#53, #54)
- `agents/rl/encoder.py` names the effects once, in `LEAPS = ("jumped","flipped","climbed","hanging","dropped")`.
  Used for (a) "my own motion is a leap" and (b) a per-figure "leap" track flag. A jumped to flipped
  rename or swap changes no feature. The scan test pins "exactly two literals".
- `agents/versus_baseline.py` has the same tuple, so the baseline is also insensitive.
- `agents/macros.py` does not name either effect. Macros (`JUMP`, `RUN_JUMP`) are expanded to inputs;
  the encoder reads no `last_result` effect names.
- So the **encoder and baseline code need no change**. The risk is not the names but the dynamics: after T19 the
  same macro gives a different move (flip distance and pose, `last_result` effect, and the 2-tick grace
  window changes how the held-key sequences of `JUMP`/`RUN_JUMP` expand and when a move starts).
  The weights were trained against the old dynamics (standing jump flips only over someone), so
  behaviour can shift, and the baseline opponent shifts with it.

**Recommendation for Saad: re-check only after T19, no retraining now.** Re-check =
1. Re-run this same 128-duel tuning check on T19's tip with the committed weights (unchanged SHA). Pass = 0 policy
   errors, 0 fallbacks, and no loss spike versus 120/8/0 (any loss, or more than a handful of new draws, is a trigger).
2. Rerun the parity test and the encoder leak/invariance tests.
3. Only if (1) fails, retrain (a new, approved 80-minute run). Retraining is not justified by
   the rename alone.
The held-out run (T09) must use the post-T19 engine, so its baseline and policy are both on the
final rules. Do not run H6 before T19 lands. If Saad wants strength claims, T09 on post-T19 rules is the
check that counts; this rerun cannot support one.

## 3. Other concerns
- (low) Final entropy 0.104 (ent coefficient 0.01, `clip_frac` 0.008, `policy_loss` ~0): the policy is close to deterministic.
  Fine for shipping (greedy at inference), but it means little exploration left; a shifted engine
  (T19) can leave it stuck rather than adapting. Another reason to re-check.
- (low) Opponent mix: last update 6 baseline / 10 snapshot (`snapshot_prob` 0.5, pool 6). Training win rate vs
  baseline only 0.83 at the end versus 1.0 in the tuning eval: tuning-start eval is on trained-on starts, so 120/8/0 is
  an in-distribution number. Self-play could drift from the baseline's style; the baseline-only eval each update
  guards that, and it held.
- (low) Seeds make no difference to the final check (4 identical results per combo seen in the draws), so the duels are
  near-deterministic; report 32 distinct scenarios, not 128, in any prose.
- (note, from QA N1/N2) `RL_POLICY.md` command line shows `run-0`/5100 s; stderr (empty) not committed. Cosmetic.
- Checkpoint: last weights exported, `checkpoint_chosen_by_score` false, hash chain (file = constant = summary) verified by QA and
  by my load through `SHIPPED_SHA256`. No held-out file read (I ran no H6; `tools/rl` scan unchanged and not edited).

## Gate 2 headings
Leak findings: none found. Probed: the encoder's effect-name use and what it reads; no code changed in `agents/rl/encoder.py`, `pop/`, or `tools/rl/`
in this diff (QA scope check), so the earlier T17/T07 boundary checks stand.
Baseline fairness: unchanged by this task; baseline and encoder both treat `jumped`/`flipped` alike. T19 changes both opponents' dynamics together.
Runtime bounds: 128 duels in 11 s pure-Python (about 86 ms per 3,600-frame duel at 1 decision per about 7.6 frames), so inference is cheap locally; no latency concern.
Evaluation validity / confounds: tuning starts, trained-on, 32 effective scenarios, no held-out, no strength claim; draws are one scenario; the held-out T09 must wait for T19.
Live-run readiness: not applicable (no `--live`; the local PPO rival makes no paid calls). Cost 0.
Replay fidelity and labelled fallback: no fallbacks occurred (0 of 128); the swallowed-error counter is 0 and a fallback is labelled by the existing path; not re-probed here.

## Findings
| ID | Severity | Finding |
| --- | --- | --- |
| E1 | note | Re-check after T19 (above); no retraining now. |
| E2 | note | 8 draws are one stalemate scenario (combos 9 and 11, time_up). |
| E3 | note | 4 seeds per combo are identical, so 32 distinct duels. |
| E4 | low | Low final entropy; retrain only if the T19 re-check fails. |

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q
SUITE_LINE
```
Not run: H6, training, `--live`, browser or pygame window.

## Requested next action
Orchestrator Gate 3. Then T19 Gate 2 repeats the section 2 re-check.

## Student decision required
None.
