---
handoff_id: HO-T20-fix2-evaluation-specialist
task_id: T20-fix2
date: 2026-11-25
from: evaluation-specialist
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T20-fix2-qa.md@0f5983c (reviewed ed64a01, work 5ab77c3); tasks/T20-fix2.md@9a3717c; reports/T20-fix2-tech-lead.md
source_branch: gate/T20-fix2-eval
source_commit: 0f5983c (base; the mark removal and this report are committed on top)
reviewed_commit: ed64a01d589632424372d798f0e669f7b260b9e6
verdict: ACCEPT WITH NOTES
---

# T20-fix2: evaluation specialist report (Gate 2)

Verdict: ACCEPT WITH NOTES. E2 and E3 are fixed. No leak, no determinism change.

Status: done

## Work completed
Removed the strict xfail marks from `test_a_running_jump_is_counted_as_a_flip` (E2) and `test_a_held_draw_key_is_one_use` (E3) in `tests/test_eval_t20_probes.py`; both pass. Probed QA's three noted cases through the real `Match` and `summarize.mechanics_used`. Reviewed the item-4 table and the repeats reconciliation. Re-ran the full suite.

## Paths
`tests/test_eval_t20_probes.py` (two marks removed, nothing else); this report.

## Acceptance criteria -> evidence (Gate 2 scope)
| # | Scope item | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Marks removed, tests pass | yes | full run below, 0 failed, 4 xfailed (the other four, not mine to this task) |
| 2 | Each counted mechanic is one deliberate use | yes, with notes | probes and table below |
| 3 | Determinism, leak probes, client-message identity | yes | same tests as fix1 (8-combination determinism, `test_a_log_is_identical_whatever_b_hides`, `test_no_seat_surface_names_a_rewrite`, label-changes-nothing test) all pass in the full run; no `pop/` change in `git diff --name-only 5700c42..ed64a01` |
| 4 | Flip rule duplicates no engine logic beyond `started_move` names | yes | `is_flip` (`tools/telemetry/summarize.py:120`) reads only the `move` row's name prefix (`JUMP_`, `RUN_JUMP_`, `_HOP_FLIP_`) and the `effect` string, both already emitted from `started_move`. It re-implements no rewrite, grace or hop rule. My ast test `test_recorder_source_only_reads` still passes, so the recorder still calls only `started_move` beyond the frontend's reads |

## Measurement validity probes (mine, run through `Match`; script in my scratchpad, not committed)
| Realistic play | Result |
| --- | --- |
| run 8 ticks, jump (d+w) once | flip 1 (`RUN_JUMP_RIGHT`), no other jump |
| run, then tap d+w every other tick, 6 taps | flip 1: the engine starts one jump; later taps start nothing |
| run, tap d+w every third tick, 5 taps | flip 2 (`RUN_JUMP_RIGHT`, then `JUMP_RIGHT`): the engine itself started a second jump after the first ended, so this is two real jumps |
| two separate run-up jumps | flip 2 |
| `g` held 30 ticks | draw 1, sheathe 0; the 7 later toggles carry `repeat` |
| `g` tap, `g` tap with no gap tick | draw 1 only (see note 1) |
| `g`, 3 ticks gap, `g` | draw 1, sheathe 1 |
| run 40 ticks into a wall | no move rows beyond RIGHT, counts nothing |

Item-4 table (Tech Lead): I checked each row against `tests/test_t20fix2_counts.py` and QA's probes. TAKE, RIG, sweep, lunge, throw, kick, sword_pickup, disguise each have a press case and a held-20 case counting once. Flip and block are covered above and by QA. The table is accurate. The `block` find (read 0 in schema 2, counted now from accepted stance rows) is a real fix1 regression caught by item 4 and is correct; I confirmed `repeat` is skipped.

Repeats reconciliation: `moves - repeats` equals uses for TAKE, RIG, lunge, throw, kick, sweep and draw+sheathe together. It does not for flip, block, sword_pickup, disguise, and the report says so with reasons. That is honest and enough for T21 provided T21 reads `mechanics` for uses and `moves` only as raw starts.

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q
1683 passed, 12 skipped, 4 xfailed, 2 warnings in 434.09s (0:07:14)
```
Green. 1681 passed at QA plus my two unmarked tests = 1683; the 2 failures QA saw are gone.

## Findings
No blocker, major or minor reproduced. Notes (measurement limits, not defects):
1. DRAW then SHEATHE on separate presses with zero gap ticks reads as one hold (draw 1, sheathe 0). Real keyboard play rarely has a zero-tick gap (a tick is one 6-frame step), so I judge the undercount small. T21 should state it.
2. Jump taps spaced so that the engine starts a new jump count as separate flips; taps while a jump is in flight count once. This follows the engine and the F1 held-key principle. A T21 analyst should read "flip" as "jump starts", not "key presses".
3. A running jump that bumps after its run-up counts 1 flip (known, undetectable at start; QA could not produce it in these rooms).
4. Old schema-2 logs from fix1 undercount `block` (0 or each accepted row once). Recorded logs from before this fix should not be pooled with new ones for `block` and `flip` and `draw`/`sheathe`.

## Leak findings
None found. Probed: no seat surface (observation, legal actions, client messages, two seeds) names rewrite, grace, hop_turn, _HOP_FLIP, started_move; trace, state hash, messages and observations are identical with logging on and off (4 seeds x 2 rivals) and with the rewrite label dropped; A's log is byte-identical whatever B hides. This attempt changed only the telemetry summarizer and recorder hold detection, no `pop/`.

## Not in scope this gate (AI rival checks)
Baseline fairness, reward and training method, checkpoint reproducibility, train/held-out separation, local inference latency, replay and fallback: not touched by T20-fix2 and not re-assessed here. Evaluation validity and confounds: for T21, the flip/draw notes above. Training-run readiness: not applicable to this task.

## Known limitations
As the notes. No browser run (no browser change).

## Unresolved findings
None.

## Requested next action
Orchestrator: Gate 3 on `gate/T20-fix2-eval`. Record notes 1 to 4 for T21's analysis text.

## Student decision required
None.
