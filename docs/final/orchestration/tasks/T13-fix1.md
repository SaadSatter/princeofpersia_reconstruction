# T13-fix1: online server corrections (Gate 1 REJECT, Gate 2 notes)

Handoff id: HO-T13-fix1-orchestrator. Assigned: tech-lead (the same procedure); then qa, then evaluation-specialist.
**Corrective attempt 1 of 2.** A second rejection escalates to Saad.
Findings:
- `docs/final/orchestration/reports/T13-qa.md` @ 52ce850 (`gate/T13-qa`);
- `docs/final/orchestration/reports/T13-evaluation-specialist.md` @ 9a3feac (`gate/T13-eval`, which contains QA's branch).

Original brief: `tasks/T13.md`. Decisions: #35–#39, #41, #45, #46 (both players press rematch), #48 "Detect in ~6 s (Recommended)", #49 "Log only, document (Recommended)".
Setup: `tasks/_EXEC_COMMON.md`.

## Base

`gate/T13-eval` at `9a3feac`: `git switch -c task/T13-fix1 9a3feac`. It holds T13 plus QA's 25 probes and Eval's 5. Run with `uv run --frozen --extra play --extra train --extra online pytest -q`. Known: the T07 parity fixture fails on this line; that test is fixed on `orch/reviewed` and is not yours to touch.

## Fix (each with a test; the strict xfails named become passing)

| # | Finding | Severity | What |
|---|---|---|---|
| 1 | QA-1 | major | A client that stops reading must never block the tick loop or the other seat. Send per seat with a timeout, or through per-seat queues that drop stale frames. On timeout, close only that socket. That counts as a disconnect under #38. Remove the strict xfail `-k stops_reading` in `tests/test_gate_t13_qa_online.py` (the mark only) |
| 2 | QA-2 | major | If `_join`'s hello send or `old.close()` raises, release the seat with `connection_lost`. Never leave a seat "connected" on a dead socket. Remove the strict xfail `-k died_during` (the mark only) |
| 3 | EVAL-2 | major | A token reconnect gets its `hello` at once. Close the old socket in a background task; never wait on it before answering |
| 4 | EVAL-3, #48 | major | Explicit keepalive: `ping_interval=3`, `ping_timeout=3`. When a seat is detected dead, clear its held keys at once, then start the 15 s grace (#38) |
| 5 | EVAL-1 | minor | On rematch, reset `_seen_fallbacks` and clear `_fallbacks` in `_restart`. Each duel's trace logs exactly its own fallbacks. Remove the strict xfail in `tests/test_eval_t13_online.py` (the mark only) |
| 6 | EVAL-4 | minor | `TimeLimitedRival.reset` must take effect even while the worker is busy, by queueing the reset or replacing the worker |
| 7 | — | minor | `TimeLimitedRival` gets a `close()` (a sentinel), called on lobby reset. No daemon-thread leak |
| 8 | — | minor | `web/online.js`: no auto-reconnect after the server's "replaced" close. Show "This seat was opened in another tab" |
| 9 | — | minor | Reject a WebSocket whose `Origin` host differs from the `Host` header (LAN-only server) |
| 10 | EVAL-5, #49 | minor | `docs/final/ONLINE_PLAY.md`: online play logs AI fallbacks (`"source": "fallback"`) and never aborts a live duel |
| 11 | EVAL-6 | minor | Add `traces/online/` to `.gitignore` |

Also update `ONLINE_PLAY.md` for items 4 and 8.

## Permitted write paths

`server/**`, `web/online.js`, `web/online.html`, `web/ui.js`, `docs/final/ONLINE_PLAY.md`, `.gitignore` (the one line), new tests `tests/test_server_fix1_*.py`, the xfail-mark removals named above (the mark lines only), `docs/agent-sessions/` (a new file), `docs/final/orchestration/reports/T13-fix1-tech-lead.md`. Not `pop/`, `agents/`, `render/`, `web/bridge.py`, `web/main.js`, or other existing tests.

## Acceptance

1. Every row above is fixed, with a test that fails without the fix.
2. All three strict xfails pass unmarked.
3. A reconnect `hello` arrives in under 1 s even with a half-open old socket.
4. A silent drop is detected in about 6 s, tested with short fake timeouts.
5. The suite result line is pasted; the only failure allowed is the known T07 fixture.
6. No server left running.

## Gates

QA (`gate/T13-fix1-qa`), Eval (`gate/T13-fix1-eval`), then Gate 3, integrating into `orch/preview` and then `orch/reviewed`. Saad playtests on two machines after Gate 3.
