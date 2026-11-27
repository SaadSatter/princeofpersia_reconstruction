---
handoff_id: HO-T25-qa
task_id: T25
date: 2026-11-26
from: qa
to: evaluation-specialist
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T25-tech-lead.md@a399510 (brief docs/final/orchestration/tasks/T25.md@773b955)
source_branch: gate/T25-qa
source_commit: ecfb5a9
reviewed_commit: a399510
verdict: ACCEPT WITH NOTES
---

# T25: qa report

Status: done

## Work completed
Reviewed a399510 on `task/T25` (tests f37d1a8, work b25e8b2 and 2de419a) against decisions #95 to #98. Read the diff of
`server/app.py`, `web/keys.js`, `web/online.html`, `web/online.js`. Wrote 37 probe cases
(`tests/test_qa_T25_probes.py`) against real localhost sockets, and ran a real `python -m server`
with a scripted client. No blocker or major finding. No production or existing test edited.

## Paths
`tests/test_qa_T25_probes.py` (new), this report. Scratch client (not committed): scratchpad `qa25.py`.

## Acceptance criteria → evidence
| # | Criterion (from the brief) | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | #95 AI / Baseline start at once, no Create/Join, no code shown | Met (by pure rule and source; not run in a DOM or browser) | `lobbyView` probes (13 inputs); `online.js` click handler calls `begin({type:"join",create:true,mode})` for `startsAtOnce`; `enterRoom` hides `#room` unless `lobbyView(roomMode).showCode` |
| 1b | Server makes a private room, not joinable | Met | probe `test_second_client_cannot_enter_a_private_room_by_any_route` (ai and baseline): by code, lower case, padded, forged `mode:"human"`, forged `seat:"B"`, guessed / empty / null / near-miss token all get `full` or `bad_token`, no token or code in the reply, seat B never seated. A `create` carrying the owner's token makes a separate room. Real server run: same results |
| 1c | Create / Join with a code stay for Human vs Human, shown only then | Met | `#human-lobby` is `display:none` until `showCreateJoin`; `createBtn` ignores clicks unless `chosenMode === "human"`; probe `test_human_room_still_gives_code_and_a_second_seat` |
| 1d | Owner reconnect by token; room reaped on leave; rematch one press | Met | probes `owner_reconnects_by_token...`, `room_is_reaped_after_the_player_leaves...` (kept in the 15 s grace, gone after it, then `no_room`), `rematch_in_a_private_room_is_one_press`; real server owner reconnect returned `hello` seat A for both modes |
| 2 | #96 loading screen centred, also on resize | Met for CSS (look not seen) | `position: fixed; inset: 0; display:flex; align-items/justify-content: center`, viewport-relative so no script on resize. Probe: the only `position: fixed` rule in the page is `#status[data-state="loading"]` |
| 3 | #97 handshake noise quiet, real errors kept | Met | Empty and half-request connections: no ERROR. Malformed request line, 20 kB header, 500 headers, bad Sec-WebSocket-Key, and an exception raised in `_http`: all still ERROR with a traceback. Unit test of the filter: only EOFError / ConnectionError / TimeoutError / InvalidMessage chains rewritten, a chain with a ValueError cause or a RuntimeError is untouched. Real server log after an empty socket and a `junk` socket: the junk one printed the full ERROR traceback, the empty one printed nothing |
| 4 | #98 kneel hint | Met | probes: seat A shows "S kneel", seat B "Down kneel", each only its own, for modes `human_vs_ai`, `online`, `None`; `local_two_players` names each exactly once; all contain the sheathe nuance |
| - | Boundary: no code, token or other-seat data beyond the seat's own | Met | joiner replies carry no token or code; owner stream (`state`, `status`) contains no `seed`, `token`, `code`, `ppo`, `fallback`, `weights`; hello keys exactly `type, seat, token, rival, code`. Existing boundary tests pass in the full suite |
| - | Scope: no change to `pop/`, `agents/rl/**`, `evaluation/**`; no existing test edit | Met | `git diff --name-only 083546e..a399510`: GAME_MODES.md, ONLINE_PLAY.md, T25-tech-lead.md, server/app.py, tests/test_t25_online_polish.py (new), web/keys.js, web/online.html, web/online.js |
| - | Failing tests first | Not re-run | the handoff states f37d1a8 had 9 failed, 3 passed; I did not check out f37d1a8 |

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q tests/test_qa_T25_probes.py
37 passed in 5.02s

uv run --frozen --extra play --extra train --extra online pytest -q     (clean committed tree, ecfb5a9)
2240 passed, 11 skipped, 5 xfailed, 2 warnings in 423.38s (0:07:03)
```

## Findings
Reproduced:
- **[minor] `web/online.html` loading rule, `web/online.js:245`** (Concern 2). `setStatus("Reconnecting", "loading")`
  uses the same state as "Connecting", so the opaque full-window overlay (`#0d0e12`, z-index 10) hides the game
  during a mid-duel reconnect. Repro: read `online.js:245` and the CSS rule. Expected: the game stays visible
  while paused/reconnecting (the paused state already exists); actual: the page goes blank with one line of text.
  Not a boundary issue. Saad's call, or a `data-state="reconnecting"` without the overlay.
- **[minor, informational] `server/app.py` `QuietUnusedConnections`.** A handshake that times out
  (`TimeoutError`) is also demoted to INFO. That is a slow or stalled client, not only an unused browser socket,
  so a slowloris-style probe leaves no ERROR. Matches the brief ("unused connections"), and is a one-word change
  if Saad wants it loud. Not reproduced with a live stalled socket; reasoned from `BENIGN`.
- **[cosmetic] bad Origin.** The brief asked to show a bad Origin still logs at ERROR. It does not, and never did:
  `_http` answers 403 and the library logs no handshake failure. Probe `test_bad_origin_is_refused_403` pins
  the 403. Not a regression.

Concern 1 (judgement): the AI room's `hello` carries its room code to its own seat only (confirmed on the wire,
and the joiner's `full`/`bad_token` replies carry none). The owner already holds the token, which is stronger than
the code, so the code gives the owner nothing new and gives nobody else anything. The one residual is that
`full` versus `no_room` tells a code-guesser that a code names a live room (true for human rooms too, and the
join rate limit of 10 failures a minute per connection applies). Not a leak of hidden state. Accept.

Unverified: the page was not run in a browser or DOM by me (no Playwright run): the click flow, hidden code box,
overlay look, and the sessionStorage restore of `roomMode` on refresh are checked from source only. Tech Lead
also notes the AI buttons stay clickable after Human vs Human is chosen (a click starts an AI match); harmless.

## Known limitations
No browser. No screenshot. `f37d1a8` red-first claim taken from the handoff.

## Not checked
Real-browser layout and resize behaviour; Playwright smoke; CI workflow files (not in the diff); `--playtest`
telemetry in AI rooms (not touched by this change).

## Requested next action
Evaluation Specialist (Gate 2): boundary of the private-match path. Then Gate 3. Decide on the Reconnecting overlay.

## Student decision required
None.
