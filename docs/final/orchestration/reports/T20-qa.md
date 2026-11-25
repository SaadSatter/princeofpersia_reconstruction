---
handoff_id: HO-T20-qa
task_id: T20
date: 2026-11-25
from: qa
to: evaluation-specialist
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T20-tech-lead.md@fd5366a
source_branch: gate/T20-qa
source_commit: see the commit that holds this file (git log gate/T20-qa)
reviewed_commit: fd5366a
verdict: REJECT
---

# T20: QA report

Status: done

## Work completed
Checked out fd5366a (implementation c1be053) on `gate/T20-qa`. Ran the brief's suite command. Wrote a differential fuzz of the refused-input mirror against the real key resolution, and probes for flag-off, failed room, lifecycle events, privacy, and the summarizer on a real scripted duel. The mirror, flag-off, ordering, failed-room and privacy checks hold. Two findings reproduced (both major), so the verdict is REJECT.

## Paths
`tests/test_t20_qa_refused_mirror.py` (5 pass), `tests/test_t20_qa_probes.py` (4 pass, 2 xfail strict for F1 and F2). No production or existing test file touched.

## Acceptance criteria -> evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Off by default, no file without the flag | yes | `test_flag_off_writes_no_file_anywhere` (join, play, pause, reconnect, forfeit, rematch, close: cwd stays empty); tech-lead's `test_off_by_default_*`; `--playtest` is `store_true` |
| 2 | Scripted two-client duel, both logs, #68 types, tick order | yes | tech-lead tests; `test_lifecycle_events_and_privacy_of_every_file` (disconnect < forfeit < duel_end; pause start/end, reconnect on B); ordering sorted in `test_room_failed_after_..._once` |
| 3 | Leak test | yes | tech-lead tests; no token, IPv4, "user-agent", "origin", "name" key in any of the 3 files of a full lifecycle |
| 4 | Trace and state hash identical | yes (not re-run beyond the suite) | tech-lead's two tests pass in the full suite |
| 5 | No client message changes | yes (same) | same tests |
| 6 | summarize fixture; byte-identical | partly | fixture tests pass; byte-identical on a real scripted duel in two `--out` dirs. But mechanic counts are per tick, not per use: F1 |
| 7 | Suite green | yes | below |
| (dispatch note) | R-V35 grace: a direction cancelled by a jump within 2 ticks logs as the jump only, plus a `grace` marker | NO | F2 |

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q      (before my files were added)
1561 passed, 12 skipped, 4 xfailed, 2 warnings in 402.84s (0:06:42)
uv run --frozen --extra play --extra train --extra online pytest -q tests/test_t20_qa_refused_mirror.py tests/test_t20_qa_probes.py
9 passed, 2 xfailed   (5 + 4 passed in separate runs: 5 passed in 4.33s; 4 passed, 2 xfailed in 0.50s)
```
The tech-lead's 1568 passed / 11 skipped used `--all-extras`; the skip count differs by one extra-gated test. No failure either way.

## Findings

Reproduced:

1. [major] F1 `tools/telemetry/summarize.py` `mechanics_used` (and `server/telemetry.py` `after_tick`, which logs every tick an input is held) counts one mechanic use per tick the key is held, not per use. A single held jump (keys `d`+`w` for 10 ticks, one flip) gives `flip: 10`; the same holds for TAKE, RIG, STANCE_UP/DOWN ("block"), lunge, because the engine accepts the same input every tick while the move runs. So "used once" (brief item 5) almost never triggers and totals are inflated, which is the number the T21 analyst reads. "Never used" stays correct. Repro: `uv run ... pytest tests/test_t20_qa_probes.py::test_one_held_jump_is_one_flip_not_one_per_tick --runxfail` (expected 1, actual 10; the handoff names the per-tick logging as a known limitation but not its effect on counts). Fix direction (for the Tech Lead): count a use at the rising edge of an action, or when the previous tick's accepted action differs.

2. [major] F2 R-V35 grace not reflected. The T20 dispatch note says a direction cancelled by a jump within 2 ticks "should log as the jump only, plus a `grace` marker". With `d` for one tick then `d`+`w`, the log holds `RIGHT accepted effect moved` then `RUN_JUMP_RIGHT accepted effect flipped`; the engine log is the same two inputs, and `Duel._grace_jump` drops the RIGHT. No `grace` text exists in `server/telemetry.py`. Repro: `pytest tests/test_t20_qa_probes.py::test_a_direction_cancelled_by_a_jump_within_grace_logs_as_the_jump_only --runxfail` (expected accepted == ["RUN_JUMP_RIGHT"], actual ["RIGHT", "RUN_JUMP_RIGHT"]). Telemetry reading only `step` results cannot see the drop without reading the engine's state; the orchestrator may decide the marker needs a `pop/` read or that the brief wording is relaxed.

3. [minor] No `pause end` is logged when a paused duel ends by forfeit, so a log can show `pause start` with no end. Not tested as a failing test.

Not reproduced (tried and held):
- Refused-input mirror vs `WebGame.tick` (`Match._note_refused`): 5 seeds x 1500 ticks, random key sets from both sets (#55), shift, both seats, two-seat and AI modes, in-air LUNGE to KICK and legal filtering. Every held input the real tick did not step was logged refused exactly once; none stepped was logged refused; none silent. Zero divergences, 300+ asks and 20+ refusals per seed. Reason it holds: `ep.step` only queues, so seat A's step never changes seat B's `legal_actions` within a tick.
- Grace window and refused logic: the mirror does not depend on R-V35 (it acts on what the bridge submits), so no wrong "refused" arises from it.
- Failed room: a trace writer that raises (forfeit then `_record`), then `_room_failed` twice: each seat log has one `duel_end`, one `forfeit`, tick-ordered rows, and the host JSON exists.
- Flag off, privacy, event order: see criteria 1 to 3.

Unverified concerns: a real browser or WebSocket pair was not run; `play.py --versus --playtest` was not run interactively; the `hit`/`heart_lost` cause heuristic and the 3 thresholds are proposals (Saad).

## Known limitations
Probes drive `Match` directly, as the tech-lead's tests do.

## Not checked
Real WebSocket clients, hosted page, Playwright (no browser change in this task), `play.py --versus --playtest` under a real display, CI files (not in the diff).

## Requested next action
Orchestrator to send F1 and F2 back to the Tech Lead (or decide to relax them), then re-run Gate 1; Gate 2 reads the knowledge-boundary points above.

Commit to review: the gate/T20-qa head (this report and the two test files).
What changed: tests and this report only.
How to check it: `uv run --frozen --extra play --extra train --extra online pytest -q tests/test_t20_qa_refused_mirror.py tests/test_t20_qa_probes.py`.
What I am unsure about: whether F2's "grace marker" was a requirement or a hint.
Touches the knowledge boundary or AI seat: yes (Gate 2 applies)

## Student decision required
None.
