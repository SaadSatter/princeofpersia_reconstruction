---
handoff_id: HO-T13-fix1-evaluation-specialist
task_id: T13-fix1
date: 2026-11-24 ET
from: evaluation-specialist
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T13-fix1-qa.md@38b0f45 (gate/T13-fix1-qa), which consumed T13-fix1-tech-lead.md@b75695f; brief tasks/T13-fix1.md@261037e; earlier findings T13-evaluation-specialist.md@9a3feac
source_branch: gate/T13-fix1-eval
reviewed_commit: 385b3bfc05284f571b636ca527f583a9217d3e83
verdict: ACCEPT WITH NOTES
---

# T13-fix1: evaluation specialist (Gate 2)

**Verdict: ACCEPT WITH NOTES.** No leak found; EVAL-1 to EVAL-6 resolved as decided. No code or tests added by me; this report only.
No server left running (none started by me; the tests close their own).

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q tests/test_online_boundary.py tests/test_server_ws.py \
  tests/test_gate_t13_qa_online.py tests/test_eval_t13_online.py tests/test_server_fix1_online.py tests/test_gate_t13fix1_qa_online.py
67 passed in 56.87s
```
I did not rerun the full suite; QA's line on b75695f is `1 failed, 1228 passed, 11 skipped, 2 xfailed` (the known T07 parity fixture). The reviewed code is unchanged since.

## EVAL-1 to EVAL-6
| Finding | Status | Evidence |
| --- | --- | --- |
| EVAL-1 per-duel fallbacks | Resolved | `_restart` sets `_duel_fallbacks_from` and re-reads `_seen_fallbacks`; `trace()` slices from it. My strict xfail now passes unmarked. QA's four-duel probe: each trace holds only its own entries, replay hash intact. Residual (QA-5): a slow question finishing after a rematch can log at most one stray entry; log-only, no play effect |
| EVAL-2 reconnect waits 10 s | Resolved | `_join` closes the old socket in `_background` and sends `hello` first; QA real-process run: hello in 0.003 s with the old socket half open |
| EVAL-3 half-open seat keeps keys, 40 s notice | Resolved per #48 | `ping_interval=3`, `ping_timeout=3`, `close_timeout=1`; a dead seat goes through `connection_lost` (clears held keys) then the 15 s grace. QA measured the pause at 7.0 s in real time (3+3+1), against "about 6 s". Accept |
| EVAL-4 reset while busy | Resolved | `reset` queues a job behind the running question; `close()` sentinel; 15 lobby resets leave no worker threads (QA) |
| EVAL-5 no abort limit | Resolved per #49 | `ONLINE_PLAY.md` states online play logs `"source": "fallback"` and never aborts a live duel |
| EVAL-6 `traces/online/` | Resolved | `.gitignore` lines present |
Also checked: `online.js` closes with code 1000 and reason `replaced` set `stopped` and show the message (read only, no browser).

## Server-to-client boundary after the new parts
Leak findings: none found. Probed by reading `server/app.py`, `match.py`, `rival.py`, `online.js` and running the boundary suites above:
- **Per-seat queues and drops.** Each `SeatLink` is fed only by `match.drain(seat)` for its own seat, so a seat's queue holds only that seat's messages. Drops remove the oldest `state` frame of the same queue and never a status. Whether a frame is dropped depends on that client's own read speed, not on the other seat or on hidden state. One seat's stall or timeout aborts only its socket (QA probes: the other seat keeps receiving). The one cross-seat effect is the pause the other player sees when a seat is dropped; that is the public connection state of decision #38 and the text is fixed.
- **Timing.** The tick loop no longer awaits any socket, so one client's behaviour cannot be observed by the other as timing. Per-tick server work is unchanged from my earlier measure (0.65 ms ordinary, about 2 ms on the public 6-tick decision cadence).
- **403.** Decided before the handshake from `Origin` and `Host` headers only; the body is the constant `forbidden`. It depends on no game state, and runs before any seat is touched. QA checked same-host variants (127.0.0.1, localhost, LAN IP) are accepted and other-site, `null`, mixed names, userinfo and wrong port are refused; a duplicated header or a missing `Host` does not crash the server.
- **`replaced`.** Sent only to the previous socket of the same token (a token holder already knows the seat) and says nothing about the other seat or game. A wrong token never reaches it: `match.join` rejects first with the fixed `bad_token` text.
- **Keepalive.** Protocol-level ping/pong frames with no payload from the game; no state-dependent content.
- **Hello.** Still `rival, seat, token, type` to the joiner only; the new early send does not widen it. The AI seat's inputs and trace handling are unchanged (my AI-input test passes).

## Judgement on QA's notes (must any be fixed before the two-machine playtest?)
| Note | Judgement |
| --- | --- |
| `MAX_QUEUED = 48` (about 4 s of lag at 12 Hz) | **Can wait; cheap to lower.** It matters only for a link that is slower than the stream but alive. Nothing in the boundary or correctness depends on it. If Saad sees lagging views on Wi-Fi, set it to about 12 to 24 (1 to 2 s); a one-line follow-up with a test, not a gate item |
| About 19 KB per state message, about 226 KB/s per seat (1.8 Mbit/s) | **Can wait.** Fine for a LAN or ordinary Wi-Fi (measured by QA, not by me). It is a pre-existing size; compression or deltas would be a protocol change and belong after the playtest, only if it shows lag. The playtest should note the link type |
| `SEND_TIMEOUT_S = 2.0` | **Can wait.** A seat is dropped only when one send stalls 2 s (a roam or a deep fade); the cost is a pause and a token reconnect inside the 15 s grace, not the duel. If playtest shows spurious drops, raise to 4 to 5 s (still under the 6 s keepalive). Estimated from code and QA's arithmetic; not measured on a real link |

Nothing must be fixed before the playtest. The playtest is the first real-link check (QA and I used localhost only).

## Other fields
Baseline fairness: unchanged from T13 (the same `versus-baseline` through the observation and legal list only; my AI-input test passes).
Reward and training method: not applicable (no PPO in the server path).
Checkpoint reproducibility: not applicable.
Train / held-out separation: not applicable; `server/` does not import `tools/rl/` or `evaluation/`.
Evaluation validity and confounds: not a comparative evaluation. Online duels are demo play and must not be counted as evidence.
Local inference performance: not re-measured; the T13 figure stands (measured, Apple M4, baseline decision tick 1.96 ms mean, 3.98 ms max). PPO is not served here.
Replay and fallback: traces still replay to the same hash after rematch (my test, QA's four-duel probe). Fallbacks are labelled `"source": "fallback"`, per duel, logged only (#49).
Training-run readiness: not applicable to T13-fix1.

## Not checked
No browser (the `online.js` close handler read only); no real Wi-Fi or two-machine run; no full-suite rerun by me; the Tech Lead's revert check not repeated; no `--live` calls.

## Student decision required
None.
