---
handoff_id: HO-T18-fix1-evaluation-specialist
task_id: T18-fix1
date: 2026-11-25
from: evaluation-specialist
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T18-fix1.md@0ba8762 ; docs/final/orchestration/reports/T18-fix1-qa.md@3124e13
source_branch: gate/T18-fix1-eval
source_commit: f41227a (tests); this report is committed on top of it
reviewed_commit: 057504c2f1e59334432928052a96a2714517d121 (server/app.py change; QA report-only delta at 3124e13)
verdict: ACCEPT WITH NOTES
---

# T18-fix1: evaluation specialist report (Gate 2, online server)

Status: done

## Work completed
- Removed the strict xfail mark from `tests/test_eval_t18_rooms.py::test_a_failing_trace_write_in_one_room_does_not_stop_the_other_rooms` (EVAL-T18-1). It now passes as a normal test.
- Checked the boundary in `server/app.py` (`pump` + `_room_failed`) and added `tests/test_eval_t18_fix1_boundary.py` (below).
- Assessed QA's minor finding (recommendation below). No production code touched. T19 paths untouched.
- Re-ran the full suite myself on a clean, committed tree (line below).

## Paths
- `tests/test_eval_t18_rooms.py` (xfail mark removed, one docstring line)
- `tests/test_eval_t18_fix1_boundary.py` (new)
- this report

## Acceptance criteria -> evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | EVAL-T18-1 xfail removed, test passes | Met | passes in the full run and in the targeted run (12 passed with the two fix1 files) |
| 2 | Exception text, path, traceback reach no client | Met | `_room_failed` calls only `log.exception(...)` (server-side logger "server"); it sends nothing. My test raises `OSError("[Errno 2] /secret/trace/dir-EVAL-9731")` from room AAAA's tick and scans every message received by all four clients for the secret path, `Errno`, `Traceback`, `OSError`, `File "`: none found. The log record does carry room code AAAA. |
| 3 | Failed room never touches another room's state | Met | Same test runs a control scenario (AAAA never fails). Room BBBB's full trace (`Match.trace()`) and every message its clients received are equal between the two runs. Mechanically: the handler mutates only `room.match.state` and `_finished` of the failing room; rooms hold their own `Match`, links and conns; `_flush_room` and `_reap` are per room. |
| 4 | Full suite, real line | see Tests run | |

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q tests/test_eval_t18_fix1_boundary.py tests/test_eval_t18_rooms.py tests/test_online_rooms_fix1.py
1 failed, 12 passed, 1 xfailed in 66.47s   (first run: my own test asserted on state after the seats had left; fixed in the test, not in production)
uv run --frozen --extra play --extra train --extra online pytest -q tests/test_eval_t18_fix1_boundary.py
1 passed, 1 xfailed in 2.09s
```
Full suite on the clean committed tree (f41227a, `git status` empty before the run):
```
uv run --frozen --extra play --extra train --extra online pytest -q
1384 passed, 12 skipped, 4 xfailed, 2 warnings in 387.30s (0:06:27)
```
Arithmetic from base fc02687 (1380 passed, 4 xfailed): +1 tech-lead test, +1 QA test, EVAL-T18-1 xfail becomes a pass, +1 my boundary test = 1384 passed; xfailed 4 - 1 + 1 (my EVAL-T18-2) = 4. The suite was not running anything else against the tree (nothing swapped during the run). One test (tests/test_online_rooms_fix1_qa.py) comes from the QA branch I started on.

## Findings
- minor, reproduced (EVAL-T18-2, confirms QA's finding): when the error comes from the tick (`room.match.advance`), `_room_failed` forces `state = "ended"` and `_finished = True` but queues no message, so that room's clients see frames stop and nothing else. Reproduced by `test_a_room_that_fails_mid_tick_tells_its_clients_it_ended`, a strict xfail (reproduces the finding; whoever fixes it removes the mark). On the `on_finish` path the "ended" status was already announced before `_record` ran, so those clients are told.
- note, reproduced: after a mid-tick failure the room stays in `rooms` and `pump` calls `advance` on it every tick. With a real error that stays raised, the traceback is logged on every tick (my fault-injection raises every call: 12 log records in 12 ticks). QA saw one record because the `on_finish` failure is not repeated once `_finished` is set. A persistent tick fault would flood the log at 60 Hz until the room expires. Unverified for real faults (an engine error is probably also persistent).
- note, not reproduced (as QA): an error in `_flush_room` or `_reap` still escapes `pump`. Out of the brief.
- note: the exception is caught as `Exception`, so `CancelledError`/`KeyboardInterrupt` are not swallowed (correct).

## Recommendation on the QA minor (room fails mid-tick, clients not told)
Fix it, small and safe, in a follow-up (T18-fix2 or folded into the next server change), not now:
1. In `_room_failed`, when the room was not already ended, call `match._announce()` (or a public `Match.abort()` wrapping `state="ended"`, `_finished=True`, `_announce()`). `_announce` queues `status(seat)`, a fixed-shape message with no exception content. That ends the client UI cleanly instead of freezing it.
2. In the same change, skip `advance` for rooms already marked failed (or log once per room), so a persistent fault logs once.
Severity is minor: it needs an engine or tick fault that today's suite cannot trigger by a normal path, and the safety goal of #63 (other rooms keep running, no leak) is met. Saad decides whether to spend a task on it; I do not recommend blocking the gate. A test for it already exists as the strict xfail above.

## Known limitations
- Fault injection replaces `Match.advance` on one instance; real faults (disk full, engine bug) take the same `except Exception` path but were exercised for `on_finish` only through QA's and the tech lead's tests.
- No browser or Playwright run; server change only. Not in my scope: AI rival, PPO, baseline (this task changes none).
- Wall-clock: the full suite takes about 6 to 7 minutes on this machine.

## Unresolved findings
EVAL-T18-2 (minor, above). EVAL-T18-1 is closed.

## Requested next action
Orchestrator: Gate 3 on `gate/T18-fix1-eval` (head = this report's commit). Decide whether to queue the small follow-up for EVAL-T18-2.

## Student decision required
None.
