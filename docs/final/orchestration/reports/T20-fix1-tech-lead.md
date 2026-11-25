---
handoff_id: HO-T20-fix1-tech-lead
task_id: T20-fix1
date: 2026-11-25
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T20-fix1.md@6ba2ad4; reports/T20-qa.md and reports/T20-evaluation-specialist.md @a039283 (gate/T20-eval); DECISIONS-2026-11-24.md@1f7fa10 (rows #85, #86)
source_branch: task/T20-fix1
source_commit: 000f86c9dd7952b843a0c9cdf85b28abd21d3f9f
reviewed_commit: n/a
verdict: n/a
---

# T20-fix1: tech-lead report

Status: done (3 failures remain, all in QA- and Eval-owned tests, decision #85)

## Work completed
Added the read-only accessor `VersusEpisode.started_move(seat)` (decision #81) with a failing test first (commits before the implementation). The recorder now logs a `move` row once per engine start and counts uses only from those rows. Grace gets a marker (#82), the refused-run threshold is 12 (#83), `pause` end is logged on forfeit (F3), and TELEMETRY.md carries the Gate 2 doc fixes. Schema is now 2. Old (schema 1) logs still summarize the old way.

## Paths
`pop/versus.py` (accessor, `StartedMove`, a reporting-only `_rewrite` dict), `server/telemetry.py`, `tools/telemetry/summarize.py`, `docs/final/playtest/TELEMETRY.md`, new `tests/test_t20fix1_accessor.py`, `tests/test_t20fix1_recorder.py`, `tests/data/t20_telemetry/v2/2026-11-25-V2V2-001-A.jsonl` (a subdirectory, so the schema 1 fixture tests do not read it), `docs/agent-sessions/T20-fix1-telemetry-uses.md`. No change to `server/match.py` or `server/app.py` (the pause end is closed inside the recorder).

## Acceptance criteria -> evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | One held flip gives `flip: 1`; a jump then 3 LEFT ticks gives one flip | yes | `test_one_held_flip_is_one_flip` (held 1, 4, 10, 11 ticks), `test_a_jump_then_three_left_ticks_is_one_flip`, `test_two_separate_taps_are_two_flips`. QA's F1 and Eval's E1 strict xfails now XPASS |
| 2 | Grace cancel: jump row `grace: true`; the summary does not count the direction | yes | `test_grace_jump_row_is_marked_and_the_summary_drops_the_direction`; differential fuzz `test_recorder_grace_agrees_with_the_engines_own_cancel` (3 seeds, marker set equals the engine's own `_grace_jump` hits, at least one hit) |
| 3 | Kick over a jump, hop turned into a flip, log as the started move | yes | `test_a_kick_that_replaced_a_jump_logs_as_a_kick`, `test_a_hop_that_turned_into_a_flip_logs_as_the_flip`, `test_the_started_move_says_which_engine_rewrite_started_it` |
| 4 | Determinism with and without `--playtest` | yes | `test_trace_hash_and_messages_equal_with_and_without_logging` (2 seeds x two humans / baseline AI: trace, state hash, every client message equal); the Eval 8-combination test and the T20 tests still pass |
| 5 | Leak tests pass | yes | all T20 leak and non-interference tests pass; the accessor adds nothing to an observation (`test_reading_it_changes_nothing_and_is_not_in_an_observation`) |
| 6 | Suite green except expected items | partly | see below |
| F3 | `pause` end on forfeit | yes | `test_a_paused_duel_that_ends_by_forfeit_logs_the_pause_end` |
| Docs | the six TELEMETRY.md items | yes | seed warning, per-seat host counts, idle = no input, stuck = stayed, accepted is not executed, AI duels summarize the human only |

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q
5 failed, 1611 passed, 12 skipped, 5 xfailed, 2 warnings in 285.71s (0:04:45)
```
Amendment after decisions #85 and #86 (commit on top of 394ca4f): the suite now reads
```
uv run --frozen --extra play --extra train --extra online pytest -q
3 failed, 1613 passed, 12 skipped, 5 xfailed, 2 warnings in 276.95s (0:04:36)
```
The 3 failures are the QA- and Eval-owned items, updated by their authors at their gates (#85):
1. `tests/test_eval_t20_probes.py::test_a_queued_direction_is_not_credited_with_the_running_flip`: E1 strict xfail now XPASS. Eval removes the mark.
2. `tests/test_t20_qa_probes.py::test_one_held_jump_is_one_flip_not_one_per_tick`: F1 strict xfail now XPASS. QA removes the mark.
3. `tests/test_t20_qa_probes.py::test_real_scripted_duel_summarizes_deterministically`: asserts a refused run from 5 refused ticks; #83 needs 12. QA updates it.
Changed by me (own T20 tests, only these assertions):
- `tests/test_t20_summarize.py::test_stalls`: `a["refused_runs"] == [{"action": "LUNGE", "start_t": 5, "end_t": 8, "length": 4}]` -> `a["refused_runs"] == []` (the fixture's 4-tick run is under `REFUSED_RUN_MIN = 12`).
- `tests/test_t20_telemetry.py::test_connection_events_and_forfeit`: pause phases `["start", "end", "start"]` -> `["start", "end", "start", "end"]` (F3: the forfeit closes the pause).
The `_rewrite` label stays (#86). The earlier line before the amendment (5 failed, 1611 passed) is superseded.

Still xfail, form to change by QA (decision #82): `test_a_direction_cancelled_by_a_jump_within_grace_logs_as_the_jump_only` (expects the log to hold only the jump; the log is append-only by decision, both rows exist, the jump row has `grace`).

## Findings
None new. Decisions that went past the letter of the brief, for Gate 3 to judge:

- **`pop/versus.py` is more than the accessor.** Grace cannot be told from the move name. I first inferred it from the seat's own started-move history (a same-side direction within 2 ticks); the differential fuzz found a false positive (seed 1: RIGHT bumped, ended, and a queued JUMP_RIGHT began the next tick: not a cancel). So `Duel._start` now takes a `rewrite` label ("kick", "grace", "hop_turn", else None), stored in a new dict `_rewrite` that no rule reads, and `started_move` returns a `str` subclass `StartedMove` with `.rewrite`. Still one public method; two private additions, no rule change. If Gate 3 wants the strict reading ("the accessor only"), the alternative is the history inference with its known false positive.
- **A held key counts once, by the key, not by the engine.** The engine does start a second flip when a key is held longer than a flip (the input queued while it runs). QA's repro (held 10 ticks, expected 1) therefore gives 2 engine starts. The recorder marks the second `repeat: true` (same held key as the last start of that move; refused ticks count as held), and the summary skips it for the mechanics counts. `moves` still counts every engine start. If Saad prefers raw engine starts, drop the `repeat` skip in `mechanics_used`.
- **`action` rows lose `effect`** (schema 2). It described the running move, not the input. The started move's own `effect` is on the `move` row.
- **`_HOP_FLIP_<DIR>`** is the engine's internal name for a hop turned into a flip; it appears in `move` rows of the seat's own log. It names no other seat's fact.

## Known limitations
- The `hit`/`heart_lost` cause is still a guess from the seat's own view (as before).
- `repeat` is inferred from the key stream: two deliberate taps of the same key on consecutive ticks during one move read as one held key.
- Real WebSocket clients and `play.py --versus --playtest` under a display were not run (the code path uses the same recorder; `test_t20_play.py` passes).

## Unresolved findings
None of mine. The 5 failures above wait for their authors' gates.

## Requested next action
QA (Gate 1) reads `task/T20-fix1` at 000f86c, updates the F1, F2 (and Eval the E1) tests, and the two existing T20 tests that the brief's thresholds and F3 change; then Gate 2 re-checks the recorder.

Commit to review: 000f86c9dd7952b843a0c9cdf85b28abd21d3f9f on task/T20-fix1
What changed: uses are counted from `move` rows, once per engine start (a held key once); the log marks grace and the summary drops the cancelled direction; kick swaps and hop turns log as the started move; refused runs need 12 ticks; the pause closes on forfeit; the docs say what the numbers mean.
How to check it: `uv run --frozen --extra play --extra train --extra online pytest -q tests/test_t20fix1_accessor.py tests/test_t20fix1_recorder.py` (32 pass); `... pytest -q tests/test_t20_qa_probes.py tests/test_eval_t20_probes.py --runxfail` shows F1 and E1 now pass and the F2 old form still fails by design.
What I am unsure about: the `_rewrite` addition in `pop/versus.py` beyond "the accessor only"; counting a held key once (`repeat`) versus raw engine starts; Gate 2 needs its `ast` source test to allow `started_move` (and still forbid `step`, `tick`, `_duel`, `_move_action`).
Touches the knowledge boundary or AI seat: yes (the recorder reads one new engine fact about the seat's own input; Gate 2 applies)

## Student decision required
None.
