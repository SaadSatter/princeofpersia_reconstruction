---
handoff_id: HO-T20-fix2-tech-lead
task_id: T20-fix2
date: 2026-11-25
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T20-fix2.md@332e039; docs/final/orchestration/reports/T20-fix1-evaluation-specialist.md@5700c42
source_branch: task/T20-fix2
source_commit: 5ab77c38ec8ecc927c5605a4d1c784bdd36134ab
reviewed_commit: n/a
verdict: n/a
---

# T20-fix2: tech-lead report

Status: done

## Work completed
Fixed E2 (a running jump counts one flip), E3 (a held draw key is one use), added a per-seat
`repeats` count, and re-checked every mechanic through the real engine and recorder (item 4). That
re-check found one more bug of the same class: `block` read 0 in schema 2. No `pop/` change, no
existing test edited.

## Paths
`server/telemetry.py`, `tools/telemetry/summarize.py`, `docs/final/playtest/TELEMETRY.md`,
`tests/test_t20fix2_counts.py` (new, 33 tests), `docs/agent-sessions/T20-fix2-telemetry-flip-hold.md`,
this report.

## Acceptance criteria -> evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Running jump, standing jump, hop turned flip: `flip == 1` | yes | `test_a_running_jump_is_one_flip` (d x8 then d+w: `{RIGHT: 2, RUN_JUMP_RIGHT: 1}`, flip 1), `test_a_standing_jump_is_one_flip`, `test_a_hop_turned_into_a_flip_is_one_flip`, held jumps of 1, 5, 30 ticks, shift running jump, two jumps = 2 |
| 2 | `g` held 30 ticks: one use, rest `repeat` | yes | `test_a_held_draw_key_is_one_use`: draw 1, sheathe 0, first row no `repeat`, every later toggle `repeat`. Separate presses still count: `test_separate_draw_then_sheathe_presses_are_two_uses`, `test_a_new_press_of_the_draw_key_is_a_new_use` |
| 3 | `moves - repeats` reconciles; report says where not | yes | `test_moves_minus_repeats_reconciles_...` (lunge, draw+sheathe), `test_flip_does_not_reconcile_by_name_alone`; table below and TELEMETRY.md |
| 4 | Item 4 table with a test per mechanic | yes | table below |
| 5 | Determinism, leak, client-message identity pass | yes | full suite below: only the two expected Eval XPASS fail |
| 6 | Suite green except Eval XPASS, real line | yes | below |

## What changed
- Flip rule (`tools/telemetry/summarize.py` `is_flip`): one per non-repeat `move` row whose name
  starts `JUMP_`, `RUN_JUMP_` or `_HOP_FLIP_` (the engine's own `started_move` name, so a kick that
  replaced a jump is KICK and a hop turned flip is `_HOP_FLIP_*`), or whose effect is `flipped`. A
  standing jump whose effect is `bumped` is not a flip. There is no second copy of the engine rule:
  only the names the engine already reports.
- Held keys (`server/telemetry.py`): the draw key (DRAW/SHEATHE) and a held up+direction (JUMP_x
  then RUN_JUMP_x once running) are each one key for hold detection, so later starts from the same
  hold carry `repeat`.
- `repeats` (int) and `repeats_by_move` per seat in `summary.json`; a sentence in `summary.md`.
- `block`: a stance change starts no engine move (R-V03), so no `move` row exists and `block` was 0
  in schema 2 (a fix1 regression, found by item 4). It is counted from the accepted `STANCE_*`
  `action` row, and the recorder marks `repeat` on that row while the key stays held.

## Mechanic table (item 4)
All tests are in `tests/test_t20fix2_counts.py`; "held" means the action asked on 20 consecutive ticks.
| Mechanic | Counted from | Single use counts once | Test |
| --- | --- | --- | --- |
| TAKE | `move` TAKE | yes, press and held; `disguise` also 1 | `test_take_counts_once_and_the_disguise_once[1,20]` |
| RIG | `move` RIG | yes; one `trap_rigged` | `test_rig_counts_once[1,20]` |
| flip | `move` name JUMP/RUN_JUMP/_HOP_FLIP | yes: standing, running, shift, held 1/5/30, hop, kick-over-jump (1 flip + 1 kick) | the flip tests above and `test_a_kick_over_a_jump_...` |
| block | accepted `STANCE_*` `action` row, `repeat` skipped | yes (was 0 before this fix); two presses = 2 | `test_block_stance_counts_once[1,20]`, `test_two_separate_stance_presses_are_two_blocks`, `test_a_held_stance_key_marks_its_later_ticks_repeat` |
| draw, sheathe | `move` DRAW, SHEATHE | yes (E3) | held-key and press tests above |
| sword_pickup | `sword_pickup` event | yes; held DOWN does not repeat it | `test_sword_pickup_counts_once[1,20]` |
| lunge | `move` LUNGE | yes | `test_armed_attacks_count_once` |
| throw | `move` THROW | yes | same |
| kick | `move` KICK | yes | kick test |
| sweep | `move` SWEEP | yes | `test_sweep_counts_once[1,20]` |
| disguise | `disguise_on` event | yes | in the TAKE test |

## Where `moves - repeats` does and does not equal uses
- Equals uses: TAKE, RIG, lunge, throw, kick, sweep, and draw plus sheathe together.
- Does not: `flip` (JUMP_*, RUN_JUMP_*, `_HOP_FLIP_*` all map to it, and a bumped jump to none);
  `block` (stance changes are in `action` rows, not `moves`); `sword_pickup` and `disguise` (events;
  DOWN is a move that is not always a pickup). A grace-cancelled direction is dropped from `moves`
  before repeats are counted, so the two stay consistent.

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q tests/test_t20fix2_counts.py
33 passed in 0.37s
uv run --frozen --extra play --extra train --extra online pytest -q
2 failed, 1668 passed, 12 skipped, 4 xfailed, 2 warnings in 294.29s (0:04:54)
```
The 2 failures are Eval's strict xfails XPASSing as the brief expected:
`tests/test_eval_t20_probes.py::test_a_running_jump_is_counted_as_a_flip` and
`::test_a_held_draw_key_is_one_use`. Their author removes the marks at Gate 2. Base was
`1635 passed, 12 skipped, 6 xfailed`; 33 new tests and the two XPASS account for the difference.

Scope: `git diff --name-only 5700c42..HEAD` is the five paths under "Paths" (plus this report), all permitted.

## Findings
None new open. Fixed along the way: `block` read 0 (above).

## Known limitations
- A running jump that bumps after its run-up cannot be told from a flip at its start and counts as
  one flip. A standing jump that bumped counts none (effect known at start).
- A held up+direction held through landing is one use even though the rival jumps again (consistent
  with the F1 principle); the later jumps carry `repeat`.
- A held stance key is one use by hold detection; a stance key tapped on consecutive ticks reads as
  one hold (same limit as before for other keys).
- Old schema 2 logs from fix1 (no stance `repeat`) count each accepted stance row as one use.
- Mixed-hold edge: DRAW then immediately SHEATHE on separate presses with no gap tick of silence
  between them would read as one hold.

## Unresolved findings
None.

## Requested next action
Commit to review: 5ab77c38ec8ecc927c5605a4d1c784bdd36134ab on task/T20-fix2
What changed: flip counted for every JUMP/RUN_JUMP/hop-flip start; held draw and held jump keys are
one use; `repeats` per seat; `block` counted from stance action rows (was 0).
How to check it: `uv run --frozen --extra play --extra train --extra online pytest -q tests/test_t20fix2_counts.py`;
Eval repro: d x8, then d+w x1, then 14 empty ticks gives flip 1; `g` x30 gives draw 1.
What I am unsure about: the stance fix goes slightly past the brief's list (item 4 required it);
bumped running jumps count as flips; the recorder's `action` rows for stances now can carry `repeat`.
Touches the knowledge boundary or AI seat: no (the log is the seat's own; no observation, action or
legal-action change; the AI seat has no log). Gate 2 applies anyway as the brief assigns it
(measurement validity); Eval removes the two xfail marks.

QA (`gate/T20-fix2-qa`) then Eval (`gate/T20-fix2-eval`), then Gate 3. Last attempt before escalation.

## Student decision required
None.
