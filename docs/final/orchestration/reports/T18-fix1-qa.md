---
handoff_id: HO-T18-fix1-qa
task_id: T18-fix1
date: 2026-11-25
from: qa
to: evaluation-specialist
configured_model: claude-sonnet-5-5
consumed: docs/final/orchestration/reports/T18-fix1-tech-lead.md@f49b9dd
reviewed_commit: 057504c2f1e59334432928052a96a2714517d121 (checked out at f49b9dd, report-only delta)
source_branch: gate/T18-fix1-qa
source_commit: see git log of gate/T18-fix1-qa (head commit)
verdict: ACCEPT WITH NOTES
---

# T18-fix1: QA report

## Acceptance criteria -> evidence
| # | Criterion | Met | Evidence |
| --- | --- | --- | --- |
| 1 | Unwritable trace dir in room 1: logged with room code, room 2 and HOME keep ticking/finish, server runs | Met | `tests/test_online_rooms_fix1.py` passes; with `server/app.py` reverted to fc02687 it fails (NotADirectoryError escapes pump), so it tests the fix. My `tests/test_online_rooms_fix1_qa.py` (error from `_tick`, not only on_finish) also passes and fails on base. |
| 2 | No client receives exception text | Met | both tests scan all client messages for path, Errno, Traceback, RuntimeError, secret string: none. Log message carries code "AAAA" only server side. |
| 3 | Suite green except expected XPASS | Met | `uv run --frozen --extra play --extra train --extra online pytest -q`: `1 failed, 1381 passed, 12 skipped, 3 xfailed, 2 warnings in 381.21s`. The one failure is `tests/test_eval_t18_rooms.py::test_a_failing_trace_write_in_one_room_does_not_stop_the_other_rooms` (strict XPASS of EVAL-T18-1, expected). Base was 1380 passed, 12 skipped, 4 xfailed: 1381 = +1 new test; 3 xfailed = the XPASS. |

Scope: `git diff --name-only fc02687..057504c` = server/app.py, tests/test_online_rooms_fix1.py, docs/final/ONLINE_PLAY.md, docs/agent-sessions/T18-fix1-room-error-boundary.md. All within permitted paths. No CI changes.

## Findings
No blocker or major.
- minor (unverified as a UX concern, behaviour confirmed): `server/app.py` `_room_failed` forces `state="ended"` without announcing to clients when the error comes from the tick itself (not on_finish). Clients in that room get no "ended" message; they see frames stop. In the on_finish case the room was already announced. Reproduced with my test (room goes "ended", no message). Expected vs actual: ideally clients are told the match ended (without error text).
- note: the error is logged once per room (not per tick), confirmed.
- note: only `advance` is guarded; an error in `_flush_room`/`_reap` still escapes `pump` (tech-lead's stated limitation; not reproduced, out of brief scope).

## Not checked
No Playwright/browser run (server change only). Tech-lead's skip-count worry resolved: with all extras skips are 12, as at base. Process note: while the full suite ran in the background I briefly swapped `server/app.py` to the base version for a mutation check and restored it (git diff clean afterwards). The suite imports modules at collection, before the swap, so I judge the run unaffected, but it was not rerun.
