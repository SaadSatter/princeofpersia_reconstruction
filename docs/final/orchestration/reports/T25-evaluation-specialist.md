---
handoff_id: HO-T25-evaluation-specialist
task_id: T25
date: 2026-11-26
from: evaluation-specialist
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T25-qa.md@efd8049 (and T25-tech-lead.md@a399510, brief tasks/T25.md@773b955)
source_branch: gate/T25-eval
source_commit: e056a98
reviewed_commit: a399510 (with QA probes at efd8049)
verdict: ACCEPT WITH NOTES
---

# T25: evaluation-specialist report (Gate 2)

Status: done. No training, no `--live`, no H6 run, no browser.

## Verdict: ACCEPT WITH NOTES

No blocker or major finding. Nothing under `pop/`, `agents/rl/**`, `evaluation/**` changed.

## Findings

1. **Leaks: none new (informational).** The AI room's `hello` carries the room code and token to
   its own seat only. Test `test_code_and_token_only_in_owner_hello_never_in_stream` (ai and
   baseline, 25 ticks): every later message is `state` or `status`, and neither the code nor
   the token appears in any of them. The code gives the owner nothing the token does not
   already give, and the page hides it. Removing it from the wire would break refresh-rejoin;
   not worth it.
2. **`full` vs `no_room`: existence only.** A joiner gets `full` for a live private room and
   `no_room` for an unknown code; neither reply carries code, token or mode. Both count as failed
   joins, so the limit (10 per minute per connection) fires on a mix of the two
   (`test_full_vs_no_room_...`). Residual (pre-existing, T13 design, not T25): the counter is per
   connection, so a client that reconnects gets a fresh budget; a guesser can therefore probe
   codes, learning only "a live room exists" (and it cannot be entered). Informational.
3. **Logging filter: safe for its stated scope.** I read `QuietUnusedConnections`: it rewrites only
   "opening handshake failed" whose exception (and cause) are EOF, connection, timeout or
   InvalidMessage; anything else, including a ValueError cause, stays ERROR with its traceback
   (QA probed malformed line, 20 kB header, 500 headers, bad key, a bug in `_http`). Handler errors
   and other server.ws lines are untouched.
4. **QA finding 2 (stalled client): checked, and the filter is not the cause.** A client that sends
   half a request and stalls is closed by the server after the library's 10 s open timeout (test
   `test_a_stalled_handshake_is_closed_by_the_server...`). By hand I ran the same stall with and
   without the filter: in both runs the log at INFO and above is empty, so the library logs no
   handshake failure for that timeout and the filter hides nothing. Residual, minor: stalled
   clients leave no log line at INFO, before or after T25; the socket is reclaimed. Optional
   follow-up: log at WARNING if Saad wants slowloris visibility. Not required.
5. **Bad Origin (QA cosmetic): agree.** The 403 is returned by `_http` and never produced a
   handshake-failure log; unchanged by T25.
6. **AI seat unchanged.** `test_ai_room_seat_is_the_shipped_rival_with_the_recorded_hash`: the
   shipped weights file hashes to `policy.SHIPPED_SHA256`, and a private AI match has a rival.
   The T22 parity tests (`test_eval_T22_parity.py`, seeds 0 and 3, runner vs game hook, same
   inputs and final snapshot) pass at this tree. T25 touched no `pop/`, `agents/`.
7. **QA finding 1 ("Reconnecting" hides the game):** a design call for Saad, not a boundary
   matter. The overlay shows the same text only; no hidden state is revealed or concealed by it.

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q tests/test_eval_T25_boundary.py tests/test_eval_T22_parity.py
8 passed (then the boundary file alone: 5 passed, 11.6 s)

uv run --frozen --extra play --extra train --extra online pytest -q     (clean committed tree, e056a98)
2245 passed, 11 skipped, 5 xfailed, 2 warnings in 340.99s (0:05:40)
uptime: 0:26  up 11 days, 2:46, 2 users, load averages: 3.66 3.81 4.75
```

## Gate 3
Nothing must happen first. Saad's call: the "Reconnecting" overlay (finding 7) and, optionally, WARNING
for stalled handshakes. Look, centring and the one-click flow remain unchecked in a browser (his next playtest).

## Known limitations
No browser or DOM run; red-first claim (f37d1a8) not re-checked; the stall check used the installed
websockets version only.

## Student decision required
None.
