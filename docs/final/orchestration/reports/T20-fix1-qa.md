---
handoff_id: HO-T20-fix1-qa
task_id: T20-fix1
date: 2026-11-25
from: qa
to: evaluation-specialist
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T20-fix1-tech-lead.md@abbe5ec (work 000f86c on task/T20-fix1); brief docs/final/orchestration/tasks/T20-fix1.md@68c57eb
source_branch: gate/T20-fix1-qa
source_commit: the parent of this report's commit on gate/T20-fix1-qa (holds tests/test_t20_qa_probes.py); the receiver records the report commit
reviewed_commit: abbe5ec3408c51c8a6469815847abc53bfa47a6b
verdict: ACCEPT WITH NOTES
---

# T20-fix1: QA report (Gate 1)

Status: done

## Work completed
Checked out abbe5ec. Under decision #85 I changed only my own `tests/test_t20_qa_probes.py` (list below), verified F1, F2 and F3 are fixed, and probed the grace and repeat markers with 9 new tests. I did not touch `tests/test_eval_t20_probes.py` or any production file. No defect found.

## Paths
`tests/test_t20_qa_probes.py` (changed), this report.

## Test changes (old -> new)
1. `test_one_held_jump_is_one_flip_not_one_per_tick`: strict `xfail` (QA-T20-F1) -> mark removed; asserts `flip == 1` for a 10-tick hold. Passes.
2. `test_real_scripted_duel_summarizes_deterministically`: refused lunges held 5 ticks -> 14 ticks (over the #83 `REFUSED_RUN_MIN = 12`). Passes; summaries still byte-identical.
3. `test_a_direction_cancelled_by_a_jump_within_grace_logs_as_the_jump_only`: strict xfail expecting only `RUN_JUMP_RIGHT` accepted -> marker form (#82): the `RIGHT` row is written without `grace`; the `RUN_JUMP_RIGHT` action row and the `JUMP_RIGHT` move row carry `grace: true`; the summary has `moves == {"JUMP_RIGHT": 1}` and `flip == 1`. Passes.

New tests (mine): `test_no_grace_marker_when_the_direction_is_old_or_on_the_other_side`, `test_grace_drops_only_the_nearest_direction_not_an_older_unrelated_one`, `test_two_grace_jumps_drop_two_directions`, `test_the_repeat_marker_marks_the_second_engine_flip_of_one_held_key`, `test_a_very_long_hold_is_still_one_use`, `test_a_release_and_a_new_press_is_a_new_use_even_if_the_engine_queue_ran_on`, `test_two_taps_a_flip_apart_are_two_uses`, `test_an_input_held_after_a_different_move_is_not_a_repeat`, `test_f3_a_pause_that_ends_by_forfeit_is_closed`. The file has 15 passing tests.

## Acceptance criteria -> evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | A held flip gives `flip: 1`; a jump then 3 LEFT ticks gives one flip | yes | F1 test (10-tick hold); `test_a_very_long_hold_is_still_one_use` (40 ticks, 3 or more engine starts, flip 1). Probe: jump then LEFT x3 gives one flip and a `LEFT` move with `effect: turned` at t13 |
| 2 | Grace: jump row `grace: true`, summary drops the direction | yes | rewritten F2 test; two-grace and nearest-direction tests |
| 3 | Kick over a jump and hop turned into a flip log as the started move | yes, by the Tech Lead's tests only | `tests/test_t20fix1_*` pass in the full suite; I added no kick or hop probe |
| 4 | Determinism with and without `--playtest` | yes | the Tech Lead's `test_trace_hash_and_messages_equal_with_and_without_logging` and the Eval 8-combination test pass; my scripted-duel summaries are byte-identical |
| 5 | Leak tests pass | yes | all T20 leak tests pass. The accessor is on `VersusEpisode`, which seats never receive, and no observation field was added |
| 6 | Suite green except the expected item | yes | result line below |
| F3 | `pause` end on forfeit | yes | `test_f3_a_pause_that_ends_by_forfeit_is_closed`: the last pause phase is `end` and starts equal ends |

## Probe results (repeat and grace markers)
- A 10-tick hold of `d`+`w`: the engine starts two flips (t1 and t13). The second is `repeat: true` and the summary counts one use. A 40-tick hold also counts one.
- A tap, one empty tick, a tap: two uses, no repeat flag. Two taps 20 ticks apart: two uses.
- A grace jump drops only the nearest earlier same-side direction. An older RIGHT 30 ticks earlier stays. A direction 6 ticks before a jump, or on the other side, gets no marker.
- I could not make either marker wrong in these cases. Concern, not reproduced: the summarizer drops the grace direction by backward search, so a log with a grace jump but no earlier same-side direction row would drop an older unrelated one. The engine only cancels a direction it started, so I could not produce that from play.

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q tests/test_t20_qa_probes.py
15 passed in 0.92s

uv run --frozen --extra play --extra train --extra online pytest -q
FAILED tests/test_eval_t20_probes.py::test_a_queued_direction_is_not_credited_with_the_running_flip
1 failed, 1625 passed, 12 skipped, 4 xfailed, 2 warnings in 287.49s (0:04:47)
```
The one failure is Eval's E1 strict XPASS (Eval removes the mark at Gate 2). The 4 xfails are other tasks' marks; the 12 skips were there before. I ran no suite while production files changed.

## Findings
No blocker or major. Notes:
1. [minor, scope] The Tech Lead edited two existing tests (`tests/test_t20_summarize.py::test_stalls`, `tests/test_t20_telemetry.py::test_connection_events_and_forfeit`), though the brief said not to edit existing tests. The edits are the exact assertions that #83 and F3 change, and the handoff reports them. Gate 3 should rule on it.
2. [minor, scope] `pop/versus.py` holds more than the accessor: a private `_rewrite` dict, a `rewrite` argument on `Duel._start`, and a `StartedMove` str subclass. I read the diff. No rule reads `_rewrite`, the argument is passed at three call sites, and trace and hash equality tests pass. Gate 3 judges "the accessor only".
3. [minor, design] `repeat` is inferred from the key stream, so two deliberate same-key taps on consecutive ticks read as one hold (the handoff says so). A 10-tick hold gives `moves` of 2 flips but `mechanics.flip` of 1; TELEMETRY.md must keep explaining that.
4. [minor, unverified] The backward-search grace drop (see probes).

## Not checked
Real WebSocket clients and `play.py --versus --playtest` under a display (same as the Tech Lead). Kick-over-jump and hop-turn were checked only through the Tech Lead's tests. CI: the diff `a039283..abbe5ec` touches no `.github/` or `ci/` file. Scope is otherwise inside the brief's permitted paths, apart from notes 1 and 2.

## Requested next action
Gate 2 (Eval): remove E1's mark, let the `ast` source test allow `started_move`, and re-check the recorder's knowledge boundary.

## Student decision required
None.
