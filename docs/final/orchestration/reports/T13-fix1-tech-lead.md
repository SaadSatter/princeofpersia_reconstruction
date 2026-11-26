---
handoff_id: HO-T13-fix1-tech-lead
task_id: T13-fix1
date: 2026-11-24 ET
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T13-fix1.md@63ff5ea; reports/T13-qa.md@52ce850; reports/T13-evaluation-specialist.md@9a3feac
source_branch: task/T13-fix1
source_commit: 385b3bfc05284f571b636ca527f583a9217d3e83
reviewed_commit: n/a
verdict: n/a
---

# T13-fix1: tech-lead report

Status: done

## Work completed
All 11 rows fixed, each with a test that fails on the base (I reverted `server/`, `web/online.js` and `.gitignore` to
`9a3feac` and ran `tests/test_server_fix1_online.py`: 10 of 10 failed; restored afterwards). The three strict xfail marks
(`-k stops_reading`, `-k died_during`, EVAL-1) are removed and those tests pass.

## Paths
`server/app.py`, `server/match.py`, `server/rival.py`, `web/online.js`, `docs/final/ONLINE_PLAY.md`, `.gitignore`,
new `tests/test_server_fix1_online.py`, mark-only removals in `tests/test_gate_t13_qa_online.py` (2 lines) and
`tests/test_eval_t13_online.py` (1 line), `docs/agent-sessions/T13-fix1-online-server.md`, this report.

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Every row fixed with a test failing without the fix | yes | rows 1,3,4,6,7,8,9,11: `tests/test_server_fix1_online.py`; rows 2,5: the unmarked QA and Eval tests; row 10 is docs |
| 2 | Three strict xfails pass unmarked | yes | `test_a_client_that_stops_reading...`, `test_a_seat_whose_socket_died_during_join...`, `test_fallbacks_of_a_second_duel...` pass |
| 3 | Reconnect hello under 1 s over a half-open old socket | yes | `test_a_reconnect_hello_arrives_in_under_a_second...` |
| 4 | Silent drop detected in about 6 s, short fake timeouts | yes | production constants 3 s ping, 3 s timeout (tested), close timeout 1 s; test uses 0.2 s each and detects in under 2 s, keys cleared, seat paused with a deadline |
| 5 | Suite line pasted, only the known failure | see note | below |
| 6 | No server left running | yes | `pgrep -fl "python -m server"` printed nothing; tests close their servers |

## What changed (behaviour)
- Each seat has its own outgoing queue and writer task (`SeatLink`). The tick loop only appends (stale `state` frames
  dropped past 48 queued); a send over 2 s aborts only that socket, which ends its handler, i.e. a disconnect (#38).
- `_join`: the old socket is closed in a background task (then aborted); `hello` is sent at once. If the hello send fails
  the seat is released with `connection_lost`.
- Keepalive `ping_interval=3`, `ping_timeout=3`, `close_timeout=1` (the library's 10 s would add delay; about 6 to 7 s
  total). `connection_lost` already clears held keys before starting the 15 s grace.
- WebSocket upgrade refused with 403 when `Origin` host differs from `Host`. No `Origin` is allowed (scripts, tests).
- `TimeLimitedRival.reset` is queued behind a running question; `close()` sends a sentinel; `Match._reset_lobby` and
  `Match.close()` call it. `python -m server` does not call `Match.close()` on exit (process exit ends daemon threads).
- `web/online.js`: close code 1000 with reason "replaced" stops reconnecting and shows "This seat was opened in another tab".

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q
1 failed, 1228 passed, 11 skipped, 2 xfailed in 160.34s (0:02:40)
FAILED tests/test_rl_policy.py::test_pure_python_logits_equal_the_numpy_forward_pass_on_200_observations
```
The one failure (`assert 145 >= 200`, baseline run too short) is in `test_rl_policy.py`, which does not touch `server/`.
I take it to be the known T07 parity fixture failure; I did not rerun it on the base to confirm, and the first full run
before my edits to the xfail marks showed the same failure.

## Findings / deviations
- **Brief deviation (EVAL-1).** The brief says "clear `_fallbacks` in `_restart`". The Eval test (which I may only unmark)
  computes `len(m._fallbacks) - first == 10` after the rematch, which only holds if `_fallbacks` is NOT cleared (clearing
  gives -10). So `_fallbacks` stays cumulative, `_restart` records `_duel_fallbacks_from` and resets `_seen_fallbacks`
  to the rival's current counters, and `trace()["fallbacks"]` returns only the current duel's. Each trace logs exactly its
  own fallbacks; both the test and the intent hold. Past traces keep their own copy.
- `TimeLimitedRival.reset` when idle still runs inline; a reset queued just before the worker goes idle, followed at once by
  a second inline reset, could overlap in two threads. Not reached by the rematch flow (one reset per rematch).

## Known limitations
No real browser or two-machine check (the JS change is verified by a source-order test only). Silent-drop timing in
production (about 7 s) was tested only with scaled-down values.

## Unresolved findings
None of QA-1, QA-2, EVAL-1 to EVAL-6 remain open to my knowledge.

## Requested next action
Commit to review: 385b3bfc05284f571b636ca527f583a9217d3e83 on task/T13-fix1 (the report commit follows it)
What changed: see "What changed".
How to check it: `uv run --frozen --extra play --extra train --extra online pytest -q tests/test_server_fix1_online.py tests/test_gate_t13_qa_online.py tests/test_eval_t13_online.py`
What I am unsure about: the EVAL-1 deviation above; the 1 s `close_timeout` choice; whether 2 s `SEND_TIMEOUT_S` is right on slow Wi-Fi (it only applies to one message, but a slow link would drop a seat).
Touches the knowledge boundary or AI seat: yes (server-to-client message path and the AI seat's fallback log and worker). Gate 2 applies.

## Student decision required
None.
