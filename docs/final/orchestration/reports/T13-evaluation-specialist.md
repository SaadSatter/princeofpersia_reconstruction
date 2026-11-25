---
handoff_id: HO-T13-evaluation-specialist
task_id: T13
date: 2026-11-24 ET
from: evaluation-specialist
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T13-qa.md@52ce850 (gate/T13-qa), which consumed docs/final/orchestration/reports/T13-tech-lead.md@dc28e18; brief docs/final/orchestration/tasks/T13.md@43436d4
source_branch: gate/T13-eval
source_commit: 52ce850
reviewed_commit: 160135c4932e8ee2da9377e4780b28841d3e5be7
verdict: ACCEPT WITH NOTES
---

# T13: evaluation specialist (Gate 2) report

Status: done. Branch `gate/T13-eval` from `52ce850`. No training run, no paid call, no server left running (`pgrep` empty).

**Verdict: ACCEPT WITH NOTES on the knowledge boundary.** I found no leak of hidden state to a client in messages,
HTTP routes, status and error text, or timing. QA's REJECT (QA-1, QA-2) still stands and T13-fix1 is required.
My own findings that belong in T13-fix1 are T13-EVAL-2 (major: a reconnect over a half-open socket waits 10 s)
and T13-EVAL-3 (a half-open seat keeps its last held keys for up to 40 s), plus the minors in the fix list below.

## Work completed
Read the server (`server/app.py`, `match.py`, `rival.py`, `trace.py`, `__main__.py`), `web/online.js`, `web/bridge.py`
(`_seat_payload`, `SeatControllerRival`, `rematch`), the Tech Lead's boundary tests and QA's report. Wrote 5 tests
(`tests/test_eval_t13_online.py`; 4 pass, 1 strict xfail). Ran a real localhost server (injected clock, port 0,
`python -I` scripts in the scratchpad, not committed) to probe HTTP routes and headers, the handshake, a
half-open-socket reconnect, and the baseline's per-tick latency.

## Paths
New: `tests/test_eval_t13_online.py`, this report. Nothing else touched. Scratch scripts are outside the repo.

## Acceptance criteria → evidence
| # | Check (my focus) | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Each client gets its own seat's payload only | Met | `_state_message` copies only `rival, seat_view, draw, hud, outcome` from the seat's payload (`match.py` `STATE_FIELDS`); `hello` has `rival, seat, token, type` and goes to the joiner only. Tech Lead's allow-list test passes (`test_online_boundary.py`) |
| 2 | Disguised rival vs real guard, same bytes | Met | Tech Lead's `test_a_disguised_rival_and_a_real_guard_give_a_the_same_bytes`; my `test_pause_messages_to_the_watching_seat_are_the_same_for_every_hidden_state` (B disguised and rigged vs idle: A's pause messages byte-equal) |
| 3 | Status and error text independent of hidden state | Met | `Match.status` chooses text from connection and rematch state only; `ERROR_TEXT` is two fixed strings; 404 body is the constant `not found` |
| 4 | HTTP routes | Met | Served over a real socket: `/`, `/manifest.json`, `/online.js` (200), `/art/tiles.png` (200); `/game.zip` and `/ws` without upgrade return 404 `not found`. The route table is an exact-match dict built from the manifest, so there is no path traversal surface. No engine, `agents/` or arena data is served (`game.zip`, `main.js`, `index.html` excluded) |
| 5 | AI seat sees only its own observation and legal list | Met | `test_ai_seat_receives_only_its_own_observation_and_legal_list`: the controller gets a dict with the keys of `observe("B")` and a tuple of action strings; no seed, token or state object in what it received |
| 6 | AI seat fallbacks logged and labelled | Partly met | Logged as `"source": "fallback"` with seat, frame and reason, and never sent to the client (QA also checked). Defects: T13-EVAL-1; no abort over a limit (T13-EVAL-5) |
| 7 | Replay and determinism | Met | `test_a_trace_after_a_rematch_replays_to_the_same_outcome_and_hash` (human vs human and human vs AI, second duel after a rematch): same outcome and `state_hash`. QA covered forfeit, drop, junk and late-AI traces |
| 8 | Timing side channel | Met, with a note | The server sends one `state` per seat per tick and the seats are served in fixed order; message count and types per tick do not depend on hidden state (the byte-equality tests cover this). Measured on an M4 Mac, `--rival baseline`, 700 ticks: pump takes mean 0.65 ms on ordinary ticks and mean 1.96 ms (max 3.98 ms) on the 117 ticks where the AI decides (one in six, public cadence). 0 slow answers, 0 fallbacks. The one outlier (24.9 ms) is on a non-decision tick. A 1 to 2 ms difference that follows the public 6-tick cadence says nothing about the human's hidden state and is far below LAN jitter |

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q tests/test_eval_t13_online.py --runxfail
1 failed, 4 passed in 0.58s            (the one failure is the strict-xfail finding T13-EVAL-1 shown running)

uv run --frozen --extra play --extra train --extra online pytest -q
1 failed, 1215 passed, 11 skipped, 5 xfailed in 178.32s (0:02:58)
FAILED tests/test_rl_policy.py::test_pure_python_logits_equal_the_numpy_forward_pass_on_200_observations
```
The 5 xfails are QA's 4 (including its 2 strict) and my 1. The one failure is the known T07 fixture test.

## Findings

### Reproduced
- **[major] T13-EVAL-2: a reconnect over a half-open old socket waits 10 s for its `hello`.**
  `server/app.py` `_join`: `await old.close(1000, "replaced")` runs before the new socket's `hello` is sent, and
  `close()` waits for the peer's close frame (websockets default `close_timeout=10`). Repro (`/private/tmp/claude-501/scratch/probe.py`,
  not committed): A and B join; A's socket stops reading (`transport.pause_reading()`); a new socket joins with A's token.
  Measured: first message `hello` after **10.00 s**. This is the real Wi-Fi-drop case (the old socket is half open and the server
  has not noticed). The player sees "Connecting" for 10 s of a 15 s grace, and the same await is the T13-QA-2 window.
  Fix: send the `hello` first and close the old socket in a background task (`asyncio.create_task(old.close(...))`), or `old.close_timeout`
  shortened; either way never await a dead peer before answering the live one.
- **[major, same cause as QA-1] T13-EVAL-3: a half-open seat keeps its last held keys.** While the server has not yet noticed the
  drop, `Match.held[seat]` still holds the last key set, so the absent player's figure keeps running or attacking for up to the keepalive
  window (about 40 s with the library defaults `ping_interval=20, ping_timeout=20`, `server/app.py:66` region) before the 15 s grace starts.
  Brief item 4 says "a seat with no message holds nothing", and #38 says the duel pauses when a seat's socket drops.
  Fix: set explicit short keepalives (for example `ping_interval=3, ping_timeout=3`, so a silent drop is noticed in at most 6 s), and
  have `Match.receive`/`advance` stamp the last message time per seat and clear `held[seat]` after a short silence (for example 1 s; the client
  resends on change only, so also make the client resend its key set every 0.5 s, or clear only when the socket is closed and rely on the
  keepalive). Saad should say whether the 15 s grace is to start at the actual drop (the keepalive choice implements that approximately);
  see Student decision.
- **[minor] T13-EVAL-1: AI fallback accounting after a rematch** (`server/match.py` `_note_fallbacks`, `_restart`). `strict` xfail
  `test_fallbacks_of_a_second_duel_are_logged_and_not_mixed_with_the_first`. `game.rematch()` resets the inner controller's `fallbacks`
  to 0, but `_seen_fallbacks` keeps the old high-water mark, so the first failed decision of duel 2 is not logged (9 of 10 in the test);
  and `_fallbacks` is never cleared, so duel 2's trace (and the "fallback(s) this duel" console line) carries duel 1's entries (29 vs 9). A duel's
  fallbacks must be counted per duel. Fix: in `_restart`, clear `_fallbacks` and set `_seen_fallbacks = (slow, 0)` from the live values
  (and note `TimeLimitedRival.reset` skips the reset when the worker is busy, see T13-EVAL-4). Replay is unaffected; the trace stays exact.
- **[minor] T13-EVAL-4: rematch can leave the AI seat unreset.** `server/rival.py` `reset` does nothing while `_busy` is set, so a rematch
  during an in-flight late answer keeps the previous duel's `_tick` phase and fallback count. The baseline is stateless enough that the replay is
  unaffected, but "same seed gives the same duel" is not guaranteed for the AI seat. Fix: wait for the worker (it is bounded by the controller's
  own time) or rebuild the rival in `_restart`.
- **[minor] T13-EVAL-5: no abort over a fallback limit.** Inherited T14-E3 asked the server to log fallbacks per seat and abort over the
  limit, as the runner does. Logging is done; the limit is not (a seat that always falls back plays as a WAIT bot, and the human is never
  told). For a human duel an abort may be the wrong behaviour, so this is a decision: either add a limit that ends the duel as `aborted` with fixed
  text, or document that online play only logs. I recommend documenting it in `ONLINE_PLAY.md` and printing the count at the end of each duel (already done) because the AI seat is the baseline here.
- **[minor] T13-EVAL-6: `traces/online/` is not gitignored** (`git check-ignore -v traces/online/x.json` prints nothing). Each trace holds the seed and
  both seats' per-tick inputs. It is never sent or served (404 checked) but can be committed by accident. Request for the owner of `.gitignore`.

### Reproduced facts, not defects
- The HTTP and WebSocket handshake responses carry `Server: Python/3.13 websockets/15.0.1`. It tells a LAN scanner the library version, not game state. Optional to strip.
- `manifest.json` is public and lists art file hashes and the build id (no engine files). Intended (the page needs it).
- Cross-origin join: confirmed `origin="http://evil.example"` is accepted (QA's claim).

### My judgement on QA's unverified concerns
| Concern | My judgement |
| --- | --- |
| keepalive 20 s + 20 s before the 15 s grace | **Real, fix it** (T13-EVAL-3). It also leaves the dropped seat's keys held. Read from the installed defaults; I did not wait 40 s |
| `online.js` reconnecting after the server's "replaced" close | **Real by code reading** (`web/online.js` `close` handler ignores the code, `stopped` is only set by `full`). Two tabs sharing a token (a duplicated tab copies `sessionStorage`) would take the seat from each other every second. Not run in a browser. Fix: on code 1000 with reason `replaced`, set `stopped = true` and show "This seat is open in another tab" |
| no Origin check | **Low risk, cheap fix.** The page can be opened by a hostile site in a player's browser, and the worst it does is take a free seat or occupy the lobby before the rival joins; it cannot read the other seat or the token (not accessible cross-origin). Reject an Origin whose host differs from the `Host` header (allow no Origin) |
| daemon thread leaked per lobby reset | **Real, trivial.** Every `_reset_lobby` with `--rival baseline` starts a thread that blocks forever on its queue. Fix: a `close()` that queues a sentinel, called before building the next game. Not a boundary matter |
| 0.04 s AI wait blocks the event loop | **Acceptable.** Measured baseline decisions take 2 to 4 ms, so the wait is not used in practice; the stall is capped at 40 ms per tick (under half a tick). It matters only for a slower controller, and then the cost shows in the trace, not on the client. If PPO is ever served here, run it in an executor instead of blocking |

## T13-fix1: what must be fixed
| # | Item | Severity | Owner file |
| --- | --- | --- | --- |
| QA-1 | one non-reading client freezes the tick loop: `flush` sends under one lock; send per seat with a timeout and close that socket on timeout | major | `server/app.py` |
| QA-2 | a seat left connected when `_join`'s `old.close` or `hello` send raises: release it with `connection_lost` | major | `server/app.py` |
| EVAL-2 | reconnect over a half-open socket takes 10 s; send `hello` before closing the old socket, in a background task (same lines as QA-2) | major | `server/app.py` |
| EVAL-3 | explicit short keepalive and clear a dead seat's held keys; decide with Saad when the 15 s starts | major (tied to #38) | `server/app.py`, `match.py` |
| EVAL-1 | per-duel fallback accounting after a rematch (flip my strict xfail) | minor | `server/match.py` |
| EVAL-4 | reset the AI seat reliably on rematch | minor | `server/rival.py` |
| online.js | do not reconnect after a `replaced` close | minor | `web/online.js` |
| Origin | reject a cross-origin join | minor | `server/app.py` |
| thread | close the rival's worker on lobby reset | minor | `server/rival.py` |
| EVAL-5, EVAL-6 | document no abort limit; `.gitignore` `traces/online/` (not a permitted path for the Tech Lead; orchestrator) | minor | docs, `.gitignore` |
When these land, remove the `xfail` mark in my test and in QA's two, then rerun the boundary suite (`tests/test_online_boundary.py`, `tests/test_server_ws.py`,
`tests/test_gate_t13_qa_online.py`, `tests/test_eval_t13_online.py`). Any change to `flush` must keep each seat's message order and must not
send one seat's messages through the other's connection.

## Leak findings
None found. Probed: every key of `hello`, `state`, `status` and `error` messages (allow-list plus forbidden-key walk by the Tech Lead's tests, re-read);
A's byte stream with B idle vs B disguised and rigging; pause and resume text for A across hidden states; the AI seat's inputs; HTTP routes and 404 text;
the handshake headers; token and seat bookkeeping; the order and number of messages per tick; per-tick server time; `online.js` for published test hooks
(none; `__smLast` is only in the hosted `main.js`, which the online server does not serve); the trace (server-only, replay exact).

## Baseline fairness
The server-run AI seat is the same `versus-baseline` as the web build, called through `WebGame`'s hook with `observe("B")` and `legal_actions("B")`
only (my test). The 0.04 s wrapper replaces a late answer by WAIT, as the web build's runner policy does at another scale; with the shipped baseline there were 0 slow answers in 700 ticks on this Mac. Not a strength comparison and not part of the PPO evaluation.

## Reward and training method
Not applicable to T13 (no PPO in the server path, `--rival baseline` or `none` only).

## Checkpoint reproducibility
Not applicable to T13.

## Train / held-out separation
Not applicable to T13; `server/` does not import `tools/rl/` or `evaluation/`.

## Evaluation validity and confounds
T13 is not a comparative evaluation. Online duels are demo play; do not count them as evidence. Confounds if used: the AI seat's answers depend on wall-clock budget on the laptop, so a slow machine would change the AI's play (logged as fallbacks, replayable).

## Local inference performance
Measured on an Apple M4 Mac, Python 3.13.5: baseline decision tick 1.96 ms mean, 3.98 ms max; ordinary tick 0.65 ms mean (700 ticks, 117 decisions). The PPO stdlib inference was not part of this server and is not measured here.

## Replay and fallback
Replay exact after a rematch in both modes (my tests) and after drops, junk and late AI answers (QA). Fallbacks are labelled `source: fallback` with the seat, frame and reason, kept in the trace and console, never sent to a client. Defects T13-EVAL-1, -4, -5 above.

## Training-run readiness
Not applicable to T13.

## Inherited findings
| Finding | Status |
| --- | --- |
| T14-E1 client-chosen rival / ship no `agents/` | Closed: no query option, `game.zip` and `agents/` not served (404 checked; QA checked traversal forms) |
| T14-E2 `window.__smLast` | Closed on the online page; still in the hosted `main.js` (not served here) |
| T14-E3 log AI fallbacks per seat, abort over limit | Logging met; per-duel count wrong after a rematch (EVAL-1); no abort limit (EVAL-5) |
| T14-E4 AI seat uses a time limit | Met, deliberately 0.04 s per tick (not the runner's 5 s); judged acceptable above |
| T14 label neutral by default | Not default; `--neutral` flag, documented |

## Known limitations
No real browser or two machines (the same as QA). I did not wait for the 40 s keepalive, and did not run `online.js` for the replaced-close loop.

## Unresolved findings
T13-QA-1, T13-QA-2 (QA), T13-EVAL-2, T13-EVAL-3 (major); T13-EVAL-1, -4, -5, -6 and the minors above.

## Requested next action
Orchestrator: fold QA's two majors and the table above into T13-fix1 (attempt 1 of 2), then re-run Gate 1 and Gate 2 on the fix. Read this file on `gate/T13-eval`.

## Student decision required
Saad, facts only. (1) Should the 15 s forfeit grace start at the actual network drop (needs a short keepalive, about 6 s detection) or may it start after up to 40 s of silence plus 15 s? (2) Should a failed AI seat on a human duel only log fallbacks (current) or abort the duel past a limit?
