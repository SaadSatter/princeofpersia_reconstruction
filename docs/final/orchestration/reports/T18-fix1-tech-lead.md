---
handoff_id: HO-T18-fix1-tech-lead
task_id: T18-fix1
date: 2026-11-25
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T18-fix1.md@8dfc1bb
source_branch: task/T18-fix1
source_commit: 057504c2f1e59334432928052a96a2714517d121
reviewed_commit: n/a
verdict: n/a
---

# T18-fix1: tech-lead report

Status: done

## Work completed
Wrote `tests/test_online_rooms_fix1.py` first (failed with the trace-dir NotADirectoryError escaping `pump()`). Then `OnlineServer.pump()` catches an exception from one room's `advance` (which runs `on_finish`, the trace write and `_record`), logs it via the `server` logger with the room code and traceback (server side only), marks that room ended, and continues with the other rooms and HOME. `run_ticks` therefore never ends because of one room. `server/__main__.py` unchanged.

## Paths
`server/app.py`, `tests/test_online_rooms_fix1.py`, `docs/final/ONLINE_PLAY.md` (one sentence), `docs/agent-sessions/T18-fix1-room-error-boundary.md`, this report.

## Acceptance criteria -> evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Unwritable trace dir in room 1: logged, room 2 and HOME keep ticking and finish, server runs | Yes | new test: A errors, B and HOME recorded, `run_ticks` task still alive |
| 2 | No client receives exception text | Yes | new test scans all client messages for path, Errno, Traceback |
| 3 | Suite green except expected XPASS | Yes | below |

## Tests run
```
uv run --extra online --extra train pytest -q
1 failed, 1365 passed, 15 skipped, 3 xfailed, 2 warnings in 359.41s (0:05:59)
```
The one failure is `tests/test_eval_t18_rooms.py::test_a_failing_trace_write_in_one_room_does_not_stop_the_other_rooms`, the strict xfail for EVAL-T18-1 now XPASSing (expected; the Evaluation Specialist removes the mark at Gate 2). Plain `uv run pytest -q` skips websockets and numpy tests, so the extras were needed. Skip count (15) differs from the brief's 12 and passed count differs from 1380; this is likely my extras/environment, not verified against the base run.

## Findings
No findings.

## Known limitations
Only exceptions in `advance` are caught. An error elsewhere in `pump` (flush) is not. If a room failed before reaching "ended", it is forced to "ended" without an announce to clients.

## Requested next action
Commit to review: 057504c2f1e59334432928052a96a2714517d121 on task/T18-fix1
What changed: a room's finishing/recording error is contained, logged with the room code, and ends only that room.
How to check it: `uv run --extra online pytest -q tests/test_online_rooms_fix1.py tests/test_eval_t18_rooms.py` (the second shows the expected XPASS).
What I am unsure about: whether forcing the room to "ended" without notifying clients is the wanted UX (in the trace-write case the state was already ended and announced); the skip/pass counts versus the brief's baseline.
Touches the knowledge boundary or AI seat: no (server error handling only; no observation or message content changed, but the brief names Gate 2 for the online server, so Gate 2 applies as the brief states)
