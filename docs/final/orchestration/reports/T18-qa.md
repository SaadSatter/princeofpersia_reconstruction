---
handoff_id: HO-T18-qa
task_id: T18
date: 2026-11-24
from: qa
to: evaluation-specialist
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T18-tech-lead.md@a3e96b4 (brief tasks/T18.md@4c541a8)
source_branch: gate/T18-qa
source_commit: see the branch head (tests + this report)
reviewed_commit: a3e96b4 (code 6bb906a)
verdict: ACCEPT WITH NOTES
---

# T18: QA report

Status: done.

## Work completed
Read the diff `f08c1a8..6bb906a`, the amended brief and the Tech Lead's report. Ran the full suite and attacked the room logic with 10 independent tests (malformed payloads, cross-room and default-room tokens, cap, rate-limit window, expiry notice, hello contents, code collision). One minor finding.

## Paths
- Added: `tests/test_gate_t18_qa_rooms.py` (9 pass, 1 `xfail(strict, QA-T18-1)`).
- Scope check: `git diff --name-only f08c1a8..a3e96b4` touches only `server/**`, `web/online.html`, `web/online.js`, `docs/final/ONLINE_PLAY.md`, `tests/test_online_rooms.py`, `docs/agent-sessions/`, the TL report. All permitted. No existing test edited, no `pop/`, `web/keys.js`, `web/bridge.py`, `pyproject.toml`. CI files untouched.

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | create → code; join any case; duel starts | yes | TL `test_create_then_join_with_any_case...`; my `test_hello_carries_only_...` |
| 2 | two rooms independent; stall does not slow other | yes | TL stalled-client test passes; per-room `_flush_room` never awaits a socket (code read) |
| 3 | unknown / full / expired refused, no leak | yes | my malformed-payload test (9 junk code shapes all give "No room with that code"); expired code reads as unknown; hello holds only seat, token, rival, own code |
| 4 | token cannot cross rooms; refresh-rejoin works | yes | my `test_a_coded_token_in_the_default_room_and_back...` (both directions `bad_token`, legit refresh still seat A) |
| 5 | expiry, injectable clock | yes | TL tests; my expiry-notice test (client receives `expired`, then code unknown) and cap-frees-on-expiry test |
| 6 | alphabet, length, not the duel RNG, seed-0 trace unchanged | yes | TL tests; my constants test (24 letters, no I/O, 600 s, 15 s) |
| 7 | rate limit | yes | my test: 10 failed then `rate_limited`; creates do not count; a new connection has its own allowance; window slides after 60 s; guesses against an existing full room are counted too |
| 8 | T13/T13-fix1 online tests pass unchanged | yes | in the full run; `tests/test_gate_t13_qa_online.py` not modified |
| 9 | suite green, real line | yes | below |
| #56 default room | yes | TL's three tests plus mine (coded token into default and back refused) |
| trace name carries code | partly | helper `trace_name` tested; the file write itself is not exercised by a unit test (CLI test passes with `HOME`) |

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q          (at a3e96b4)
1350 passed, 12 skipped, 2 xfailed, 2 warnings in 316.70s (0:05:16)

uv run --frozen --extra online pytest -q tests/test_gate_t18_qa_rooms.py
9 passed, 1 xfailed
```
The full run was started before my test file was written, so its count is the Tech Lead's 1350. My file adds 9 passes and 1 xfail. `node --check web/online.js`: ok.

## Findings
Reproduced:
- [minor] QA-T18-1 `server/rooms.py:normalize_code` — `str.upper()` widens some Unicode characters, so `normalize_code("ﬀAB")` returns `"FFAB"` (three typed characters, valid code). Repro: `uv run python -c "from server.rooms import normalize_code; print(normalize_code('ﬀAB'))"`. Expected `None`; actual `FFAB`. Harmless (the same code, no new room reachable) and the page caps input at 4 characters, but the spelling is not strict. Test: `test_ligature_input_is_not_a_second_spelling_of_a_code` (xfail strict).

Observed, by design, not defects:
- A code-guess reveals "full" versus "No room", so room existence of a guessed code is learnable; limited by 10 failed joins a minute per connection (a reconnect resets it, as the TL notes; 24^4 codes, at most 50 rooms).
- If the creator drops before the second player joins, the next joiner gets seat A (T13 `connection_lost` behaviour, TL's known limitation).

Unverified: no browser run (landing state, code display, refresh flow); no two-machine run; trace-file write by the CLI for coded rooms.

## Not checked
Browser behaviour and the Playwright smoke test (not run; not in the brief). Paid or live calls (none made). Real-clock expiry (only the injected clock).

## Known limitations
As listed by the Tech Lead; the rate limit is per connection.

## Unresolved findings
QA-T18-1 (minor).

## Requested next action
Evaluation Specialist: Gate 2 on the server-to-client boundary at `a3e96b4` (tests on `gate/T18-qa`). Orchestrator may route QA-T18-1 to the Tech Lead or accept it.

## Student decision required
none.
