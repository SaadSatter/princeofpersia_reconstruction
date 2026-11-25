---
handoff_id: HO-T18-tech-lead
task_id: T18
date: 2026-11-24
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T18.md@53e7ece
source_branch: task/T18
source_commit: e30d868286624ca52b03c459d14e23e81af34766
reviewed_commit: n/a
verdict: n/a
---

# T18: tech-lead report

Status: partial. The feature is built. Acceptance item 8 is not met: two existing tests pin the single-duel lobby (see Findings). The brief says to stop and report rather than edit them, so I did not.

## Work completed
Online play now has rooms. The page offers Create room and Join room (4-letter code). The server keeps many rooms, each with its own `Match`, seat links, sockets, tick, pause/forfeit, rematch and trace file. Codes come from `random.SystemRandom`. Rooms expire, tokens are per room, and failed joins are rate limited. Tests were committed first (24320d0, they fail on the base because `server.rooms` does not exist), then the code (e30d868).

## Paths
- New: `server/rooms.py` (alphabet, `make_code`, `normalize_code`, `Room`, `FailedJoins`, constants), `tests/test_online_rooms.py` (16 tests), `docs/agent-sessions/T18-room-codes.md`.
- Changed: `server/app.py` (rooms, lobby phase, expiry, per-room flush/pump), `server/__main__.py` (a match factory per room; `trace_name` puts the code in the trace file name), `web/online.html`, `web/online.js`, `docs/final/ONLINE_PLAY.md`.
- Not touched: `server/match.py`, `pop/**`, `web/bridge.py`, `web/keys.js`, `play.py`, `render/**`, existing tests.

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | create → code; join any case; duel starts | yes | `test_create_then_join_with_any_case_starts_the_duel` |
| 2 | two rooms independent; stall in room 1 does not slow room 2 | yes | `test_two_rooms_play_independent_duels_and_a_stalled_client_stalls_nobody` (room 1's four clients never read; room 2 keeps ticking) |
| 3 | unknown, full, expired refused; nothing leaks | yes | `test_unknown_full_and_malformed_codes...`, expiry test (expired reads "No room with that code", same as unknown), `test_nothing_from_another_room_reaches_a_client` |
| 4 | token from room X cannot rejoin room Y; refresh-rejoin works | yes | `test_a_token_from_one_room_cannot_rejoin_another_but_refresh_rejoin_works` |
| 5 | expiry with injectable clock | yes | `test_room_expires_after_ten_minutes...`, `..._both_seats_have_been_gone...`, `test_one_seat_back_in_time...`, `test_code_is_not_reused_while_its_room_lives` |
| 6 | alphabet, length; not the duel RNG; seed-0 trace unchanged | yes | `test_codes_use_the_alphabet_and_never_touch_the_duel_rng`, `test_the_seed_zero_duel_is_the_same_with_and_without_rooms` (room's own Match, same inputs, equal trace incl. state hash) |
| 7 | rate limit | yes | `test_ten_failed_joins_a_minute_then_a_refusal_per_connection` |
| 8 | T13/T13-fix1 online tests pass unchanged | **no, 2 fail** | see Findings |
| 9 | suite green, real line | no (2 failures above) | below |
| item 7 of "What to build" (`--rival baseline`) | yes | `test_baseline_room_gives_seat_b_to_the_ai_at_once_and_join_is_full` |
| trace name includes code | yes | `test_the_trace_name_carries_the_room_code` (the helper only; the file write itself was not exercised in a test) |

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q
2 failed, 1345 passed, 12 skipped, 2 xfailed, 2 warnings in 297.17s (0:04:57)
```
Failures: `tests/test_gate_t13_qa_online.py::test_cli_process_two_scripted_clients_real_clock_and_trace_dir[none]` and `[baseline]`. Base was `1330 passed, 12 skipped, 2 xfailed`; the 15 extra passes are my new tests (16, one counted differently in the base total; all new tests pass).

Manual check: `python -m server` on localhost with six scripted WebSocket clients: two rooms created, joined with a lower-case code, two independent duels (a key in room 1 moved only room 1), an unknown code and a full room refused with the exact messages. No browser was opened; the page (landing state, code display, Create/Join buttons, reconnect after refresh) is untested visually. `node --check` and the existing page tests pass.

## Findings
- [blocker for item 8] `tests/test_gate_t13_qa_online.py:697-704` (the CLI test) connects with a code-less `{"type":"join"}` to `python -m server`, expects seat A, then B, then "full" for a third. That is the single-duel lobby. With rooms, `python -m server` has no default duel. I did not edit it. I did not keep a hidden default room in the CLI either: anyone could then join it without a code, which defeats the code. Needs an orchestrator decision: authorise editing that test (its `join` helper should send `{"type":"join","create":true}` for the first client and `{"type":"join","code":<code from hello>}` for the rest; the "full" assert text is now "That room is full" and `code` is still `"full"`), or tell me to add a legacy default room to the CLI.
- [flag] `tests/test_online_web.py::test_the_page_sends_only_keys_a_join_and_a_rematch_request` pins the page's message types to `{join, keys, rematch}`. To keep it unchanged the page asks for a room with `{"type":"join","create":true}`; the server also accepts `{"type":"create"}`. The brief says "create"; if you prefer a separate type, that test needs a one-word change.
- [flag] Error text changed from "The duel is full." to "That room is full" for all full cases (no test pinned the old text).

## Known limitations
- The rate limit is per connection, as briefed. A client that reconnects gets a fresh allowance, so it slows a brute-force but does not stop it. With 24^4 = 331,776 codes and at most 50 live rooms, a guess is about 1 in 6,600. A per-IP limit is a cheap extra; not done because the brief says per connection.
- Failed joins keep the socket open (so a typo can be retried) for 60 s idle.
- If the creator refreshes before a second player joins, the seat is freed (T13 behaviour in `Match.connection_lost`), so the page returns to the landing state and the room dies after 15 s. I left `match.py` alone.
- Proposals for Saad, not decided: 10 failed joins a minute; room cap 50 ("The server is full. Try later."); the 10 minute and 15 s expiry times (the 15 s is the existing forfeit window).
- Every room uses the server's `--seed` (never sent to a client).
- No browser run; no two-machine run.

## Unresolved findings
The two CLI tests above.

## Requested next action
Commit to review: e30d868286624ca52b03c459d14e23e81af34766 on task/T18 (tests first at 24320d0)
What changed: online play has rooms. Create room returns a 4-letter code and seat A; Join room with the code (any case) takes seat B. Rooms are independent, expire (10 min with no second player; 15 s with nobody connected), keep tokens per room, and failed joins are limited to 10 a minute per connection. `--rival baseline` rooms start at once with the AI on seat B.
How to check it: `uv run --frozen --extra play --extra train --extra online pytest -q tests/test_online_rooms.py`; then the full suite; `uv run --extra online python -m server` and open the page in two browsers (not done by me).
What I am unsure about: the two pinned CLI tests (orchestrator decision); the `create` spelling; creator refresh while waiting; per-connection limit being weak; browser look and flow untested.
Touches the knowledge boundary or AI seat: yes (server-to-client boundary: each room's clients receive only their own seat's messages; the room code goes only to that room's own seats; Gate 2 applies)

## Student decision required
none. (Rate limit 10 a minute and the room cap 50 are proposals for Saad.)
