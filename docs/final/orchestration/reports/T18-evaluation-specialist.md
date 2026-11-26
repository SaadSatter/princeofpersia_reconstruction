---
handoff_id: HO-T18-evaluation-specialist
task_id: T18
date: 2026-11-24
from: evaluation-specialist
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T18-qa.md@7f3525e (brief tasks/T18.md@108fd1b, amended, decisions #52, #56, #57)
source_branch: gate/T18-eval
source_commit: 7f3525e (base; the tests and this report are the branch head)
reviewed_commit: a3e96b4 (code 6bb906a)
verdict: ACCEPT WITH NOTES
---

# T18: evaluation specialist report (Gate 2, server-to-client boundary)

Status: done.

## Work completed
Read `server/app.py`, `server/rooms.py`, `server/match.py`, `server/rival.py`, `server/__main__.py` at the reviewed code, QA's report and both existing room test files. Wrote 11 independent probes (`tests/test_eval_t18_rooms.py`): every message a client receives across four rooms, code and RNG independence, the HOME default room, one baseline AI seat per room, thread cleanup, and one room's failure against the others. Measured per-room tick cost. One reproduced finding (minor), one capacity note. No leak found.

## Paths
- Added `tests/test_eval_t18_rooms.py` (10 pass, 1 `xfail(strict, EVAL-T18-1)`).
- Added this report. No production code, existing test, trainer, encoder or held-out file touched.

## Acceptance criteria → evidence
| # | Focus item | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Nothing crosses rooms | yes | `test_every_message_a_client_gets_names_only_its_own_room_and_seat`: default room plus rooms AAAA, BBBB, CCCC, two clients each, 30 ticks. The whole received stream of each client was scanned: no other room's code, no token other than its own, no "HOME". Hello holds only `type, seat, token, rival, code` and the code is the client's own. |
| 2 | Nothing crosses seats | yes | same test (the other seat's token never appears); `test_state_messages_carry_only_the_documented_fields...` (state fields `type, seat, rival, seat_view, draw, hud, outcome`; only `state` and `status` types). |
| 3 | Codes never from the duel RNG | yes | `test_code_generation_never_touches_the_global_or_the_duel_rng`: `random.getstate()` unchanged by 200 codes; `rooms.py` uses `SystemRandom` and has no `seed` outside comments; `app.py` and `rooms.py` have no `random.Random(`, `random.seed(` or `.seed`. `test_rooms_with_the_same_duel_seed...`: two rooms at seed 0 get different codes, and the code is not in the duel trace. (The TL's seed-0 trace-identity test also passes.) |
| 4 | HOME default room isolated | yes | `test_the_default_room_is_not_a_joinable_code...`: "HOME" contains O, so `normalize_code("HOME")` is None and joining it answers `no_room`; a default-room client never sees the name or a `code` field. `test_default_room_survives_while_coded_rooms_expire...`: a coded room expiring leaves the default room and its seat untouched; the expired room's old token gets `no_room`. Separate seat pools and cross-token refusal are covered by the TL and QA tests, which pass. |
| 5 | `--rival baseline` AI seat per room | yes | `test_each_baseline_room_has_its_own_controller...`: two baseline rooms, each with its own `Match`, `WebGame` and rival object; each controller received only that room's `observe("B")` keys and legal strings, with no code, token, seed or `GameState` text. `test_a_failing_ai_in_one_room_leaves_the_other_rooms_duel_byte_identical`: AI in room B raising every decision (fallbacks counted) leaves room A's tick trace and state hash identical to a run without the failure. `test_the_baseline_seat_is_never_a_joinable_seat...`: baseline rooms (default and coded) answer a second join with `full`; the two AIs are distinct objects. `test_expired_baseline_rooms_stop_their_worker_threads`: six expired baseline rooms leave no extra thread. |
| 6 | Failure isolation | partly | EVAL-T18-1 below. |

## Tests run
```
uv run --frozen --extra online pytest -q tests/test_eval_t18_rooms.py tests/test_gate_t18_qa_rooms.py tests/test_online_rooms.py
39 passed, 2 xfailed in 103.08s (0:01:43)
```
The two xfails are QA-T18-1 (ligature) and EVAL-T18-1 (below). The full suite was not re-run (QA ran it at a3e96b4: 1350 passed). The machine was under load (load average about 13).

## Findings
Reproduced:
- [minor] EVAL-T18-1 `server/app.py` `pump` / `server/match.py` `_record`: an exception from one room's `on_finish` (in the CLI, `write_trace`, for example an unwritable `--trace-dir` or a full disk) escapes `pump()` and ends `run_ticks`, so every room stops advancing and the server process exits. One room's finish can end all rooms, which the brief's "a stall in one room never delays another" is meant to exclude. Reproduction: `uv run --frozen --extra online pytest -q tests/test_eval_t18_rooms.py --runxfail -k failing_trace` (raises `OSError: disk full` out of `pump`). Expected: that room's trace is lost and logged, other rooms keep ticking. Suggested fix for the Tech Lead: wrap each room's `advance` and flush in `pump`, and the `on_finish` call in `_record`, in try/except that logs. Not a leak. Test marked strict xfail.

Observed, not defects:
- Capacity note (measured, noisy). Per-room tick cost on one Apple M4 under load average about 13: one room about 1 to 1.5 ms; 10 rooms median 12 ms; 50 human rooms median 70 to 79 ms, p90 163 to 344 ms against the 83 ms tick, with 83 to 110 of 240 ticks over budget. 50 baseline rooms: median 35 to 37 ms, 18 to 20 of 240 over budget. All rooms share one event-loop thread, so near the 50-room cap the duels slow down together (the catch-up limit keeps them from fast-forwarding, `MAX_CATCH_UP`). Roughly 40 or fewer simultaneous rooms is safe at 12 Hz on this machine (estimate from the measurement; an idle machine would do better). The cap of 50 is the TL's proposal; Saad may lower it or accept it for a classroom of a few rooms. Label: measured, one machine, under load, single runs.
- `TimeLimitedRival.__call__` waits up to its 0.04 s budget on the event loop thread. A slow AI in one baseline room can therefore delay every room by up to 40 ms per decision tick. The baseline answers in well under a millisecond, so it is not hit in practice. Worst case with many slow AI rooms is bounded, not unbounded.
- Existence oracle: "full" versus "No room" tells a guesser a code is live (QA also noted this). The 10-failed-joins-a-minute limit is per connection and a new connection resets it, so it is a deterrent for typing mistakes, not a defence against a scripted guesser (24^4 = 331,776 codes, at most 50 live). Guessing a live code with a free seat gives the guesser the seat; the code is the only secret by design (#52). Fine for a LAN classroom. A per-IP limit would need a Saad decision.
- All rooms use the same duel seed (`--seed`), so two rooms play the identical arena and opening. Nothing crosses; it is a design property of T13.
- Rate limit counts only failed joins; Create is uncounted, so one connection can fill the 50-room cap (then `busy` for everybody for up to 15 s per abandoned room, 10 minutes if the creator stays connected and alone). Availability only.

Unverified: browser behaviour; two machines; the CLI trace write for coded rooms (only `trace_name` is unit-tested; EVAL-T18-1 depends on that path); real-clock expiry.

## Leak findings
none found. Probed: every message received by 8 clients in 4 rooms (codes, tokens, "HOME"); hello fields; state and status fields; default-room name; coded token into default room and back (QA, passing); expired room's token and code; AI controller inputs per room (own `observe("B")` keys, no code, token, seed or state text); AI failure and counters in one room against another; global and duel RNG use in code generation; AI worker threads after expiry.

## Baseline fairness
Not in scope (no baseline or encoder change in T18). Per room the baseline is a fresh `make_baseline()` with the same observation and legal list as before; the per-room test shows no extra input.

## Reward and training method
N/A: T18 changes no PPO, reward or training code.

## Checkpoint reproducibility
N/A: no weights or trainer involved.

## Train / held-out separation
N/A: `evaluation/heldout/` and `tools/rl/` were not read or run. No tuning against held-out scenarios.

## Evaluation validity and confounds
No comparative evaluation was run. Confound for the capacity numbers: one machine, loaded, single runs, simulated clock (no real sockets in the timing loop).

## Local inference performance
Measured, Apple M4, load average about 13: see the capacity note (per-room advance cost, not PPO inference). Not measured in a browser.

## Replay and fallback
Per-room AI fallbacks are counted and kept in that room's own trace (test above: 36 ticks, fallbacks logged only in the failing room, `source: fallback` labelled in the trace by `Match._note_fallbacks`). Replay of a room trace is unchanged from T13 (same `server/trace.py`); not re-run for coded rooms beyond the identical-trace comparison above.

## Training-run readiness
N/A for T18 (no training involved).

## Known limitations
As above; no paid call, no browser run, no full suite re-run by me.

## Unresolved findings
EVAL-T18-1 (minor). QA-T18-1 (minor, consumed). Capacity and per-connection rate-limit notes for Saad.

## Requested next action
Orchestrator, Gate 3: accept the boundary. Route EVAL-T18-1 (try/except in `pump` and `_record`) to the Tech Lead, or accept it for a LAN classroom; decide whether the 50-room cap should drop to about 30 given the measured capacity. Read the tests at the head of `gate/T18-eval`.

## Student decision required
none.
