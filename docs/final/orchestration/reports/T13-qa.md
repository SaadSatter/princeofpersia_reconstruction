---
handoff_id: HO-T13-qa
task_id: T13
date: 2026-11-24 ET
from: qa
to: evaluation-specialist
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T13-tech-lead.md@dc28e18 (task/T13); docs/final/orchestration/tasks/T13.md@f2c25e8
source_branch: gate/T13-qa
source_commit: see the commit that adds this file (tests and report are committed together)
reviewed_commit: 160135c4932e8ee2da9377e4780b28841d3e5be7 (tests-first 7119f91, online extra 198e731)
verdict: REJECT
---

# T13: QA (Gate 1) report

Status: done. Branch `gate/T13-qa` from `160135c` (`git rev-parse HEAD` confirmed).
Run with `uv run --frozen --extra play --extra train --extra online pytest -q`.

**Verdict: REJECT.** Two major defects reproduced with real localhost sockets (T13-QA-1, T13-QA-2).
Every acceptance criterion in the brief is met in the cases the Tech Lead tested, and I found no leak of
hidden state, no crash on hostile frames and no authority hole. The rejections are about robustness of the
shared tick loop and seat bookkeeping, which the brief's "adversarial clients, reconnect races" gate exists to find.

## Paths
New (mine): `tests/test_gate_t13_qa_online.py` (25 tests: 23 pass, 2 `xfail(strict=True)` that reproduce the two majors).
No production code, no existing test, no workflow was edited.

## Scope
`git diff --name-only ae90c8c..160135c`: `server/**`, `web/{online.html,online.js,draw.js,ui.js,ui.test.js,main.js,index.html,keys.js}`,
`tools/web/build.py`, `tests/test_{server_match,server_ws,online_boundary,online_web,web_js}.py`, `pyproject.toml`, `uv.lock`,
`docs/{RULE_SOURCE_MAP.md,agent-sessions/T13-online-play.md,final/ONLINE_PLAY.md,final/WEB_BUILD.md}`.
All permitted. `pop/`, `agents/`, `render/`, `play.py`, `web/bridge.py`, `.github/workflows/`, `ci/` untouched. `tests/test_web_js.py` is additions only.
`web/main.js` was edited (guarded Rematch button); the brief allows `web/**` but this file is the hosted page the T14 contract test loads.
`grep -rn websockets pop agents render play.py web/bridge.py`: no match. `uv lock --check`: "Resolved 27 packages". The lock diff adds only `websockets 15.0.1` and the `online` extra.

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Two clients, one duel, third "full" | Met | Tech Lead's `test_server_ws.py`; mine: idle sockets that never join take no seat, first frame must be `join`, a second `join` (even with the other seat's token) is ignored, a third client during a pause gets `full` and cannot take the paused seat; CLI process with real clock: A, B, third `full` |
| 2 | Boundary | Met | Mine: B names A's seat, sends A's keys, `input`/`outcome`/`state` messages, nested/odd key lists: A never moves, duel never ends, no invalid input. Messages to a client over a duel with a drop, reconnect and 70 ticks never contain B's token, the seed, any IP, "token", "owner", "trap_owner", "rng", "script". Pause and resume status messages to B are byte-equal across four different hidden/held-key setups for A. The only `disguised` text is a client's own `me` block (its own seat) |
| 3 | Authority | Met | Mine (real sockets): 22 junk frames (binary, empty, `{`, `null`, `[]`, 5000-digit ints, nested arrays, wrong types, over-512 chars, wrong `seat`), 4000-message keys flood plus rematch/join spam in about 1 s, a 2 MiB frame. None crashed the server; held keys stayed inside the sender's own key map; rematch during play is a no-op. The 2 MiB frame closes only its sender with code 1009; that counts as a drop (pause, then resume on token) |
| 4 | Determinism | Met | Mine: trace of a duel with a drop, a reconnect, junk and key changes replays to the same outcome and `state_hash`; trace of a server-run AI seat with every answer late (budget 0, 103 fallbacks) replays exactly |
| 5 | Disconnect (#38) | Met | Mine: second-tab reconnect at 12 s resumes on the same frame and the old deadline never fires; reconnect at 14.5 s resumes, a second drop starts a fresh 15 s; forfeit at 15 s; late return after the forfeit gets the end screen ("You disconnected" / "Rival disconnected") and both can rematch with the same seed; token A cannot take seat B; forged, truncated, upper-cased and 300 or 5000 character tokens are refused; both seats down, the earlier deadline decides |
| 6 | Rematch (#41) | Met in code; look not checked | Mine: closing during a rematch clears that press; one press shows "waiting", then "Rival wants a rematch" to the other, restart only when both are connected and have pressed, same seed, frame 0; both leave after the end resets the lobby and keeps the seed. `node web/ui.test.js`: ok. No browser here, so the button's appearance, pixel edges and focus ring are unchecked |
| 7 | No websockets import; lock | Met | see Scope |
| 8 | Suite | Met | below |
| 9 | Manual run | Met (scripted, real process) | Mine: `python -m server --port <free> --rival none` and `--rival baseline` as subprocesses, real clock, 2 s of play: about 12 state messages per second, A moves, label present, no "fallback" or "seed" text, process terminated and reaped by the test |

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q      (160135c, before my tests)
1 failed, 1188 passed, 11 skipped, 2 xfailed in 146.99s (0:02:26)
FAILED tests/test_rl_policy.py::test_pure_python_logits_equal_the_numpy_forward_pass_on_200_observations

uv run --frozen --extra play --extra train --extra online pytest -q      (with my 25 tests)
1 failed, 1211 passed, 11 skipped, 4 xfailed in 168.90s (0:02:48)
FAILED tests/test_rl_policy.py::test_pure_python_logits_equal_the_numpy_forward_pass_on_200_observations

pytest -v tests/test_gate_t13_qa_online.py   ->   23 passed, 2 xfailed in 28.39s
node web/ui.test.js -> ui.test.js ok;  node web/keys.test.js -> keys.test.js: 6 passed
uv lock --check -> Resolved 27 packages
```
The one failure is the known pre-existing T07 fixture test (T07-fix1). 11 skips (the Tech Lead saw 14: they ran without `play`).
After the suite: `traces/` holds only `dev eval live`. **No `traces/online/` was created** by the suite or by my tests (the CLI test passes `--trace-dir <tmp>`; the default directory is written only when a duel ends in a real run, and is still not gitignored). No server process was left running (`pgrep` empty).

## Findings

### Reproduced
- **[major] T13-QA-1: one client that stops reading freezes the tick loop for the other seat.**
  `server/app.py:128-135` (`flush`) awaits `ws.send` for each seat inside one `_flush_lock`, and `pump` (`:137-140`) and every `handler` call it, so one slow or half-open socket blocks the pump for both players.
  Repro: `uv run --frozen --extra online pytest -q tests/test_gate_t13_qa_online.py -k stops_reading --runxfail` (or a scripted client that stops calling `recv`/`pause_reading()` after joining, with the other client reading). With seat A paused, `pump()` stopped completing at tick 392 (about 33 s of play at 12 Hz, 3 s of real time with the fake clock) and seat B received nothing more. Separately, one of my own scripted clients that did not read for about 70 ticks hung the server and my test until the test timeout.
  Expected: the other seat keeps ticking, or the slow seat is treated as dropped. Actual: both seats freeze with no status message until the library's keepalive closes the dead socket. The test is `xfail(strict=True, reason="T13-QA-1")`.
- **[major, low likelihood] T13-QA-2: a seat can be left "connected" with a dead socket, so there is no pause and no forfeit.**
  `server/app.py:103-126` (`_join`): `match.join` marks the seat connected and `conns[seat]` is set before `await old.close(...)` and `await ws.send(hello)`. If either raises (the new socket died), `handler` still has `seat = None`, so its `finally` never calls `connection_lost`.
  Repro (`-k died_during --runxfail`): A and B join; A's socket stops answering (`pause_reading`); a second socket joins with A's token; it closes while the server awaits `old.close`; then the old socket closes. Result: `match.state == "playing"`, `connected == {A: True, B: True}`, `conns["A"].state == CLOSED`; 480 more ticks (40 s) later still `playing`, `deadline == {}`. B plays on against a ghost with no pause and no forfeit, and the only way out is the owner's token returning, or B leaving.
  Expected: the seat is released or paused when its hello cannot be sent. The first-join path has the same shape (join sent, socket closed before the hello); I could not hit that window in 40 tries.
  `xfail(strict=True, reason="T13-QA-2")`.

### Reproduced facts that are not defects
- Both defects above go away once the tests' `Client` reads continuously, so a real browser (which always reads) only meets T13-QA-1 on a half-open Wi-Fi link.

### Unverified concerns (read from code or library defaults, not run to completion)
- **[minor] Detection of a silent drop is slow.** `serve(...)` in `server/app.py:66` uses the library defaults `ping_interval=20, ping_timeout=20` (read from the installed signature). A Wi-Fi drop with no close frame is noticed after up to about 40 s, and only then does the 15 s grace start. In that window the duel keeps ticking and the dropped player's seat holds no keys while the rival can attack. The brief's "pause 15 s" reads as starting at the drop. I did not wait 40 s to measure it. For Saad, as it bears on #38.
- **[minor] Duplicate-tab fight.** The server closes a replaced socket with code 1000 "replaced" (verified). `web/online.js:150-157` (`close` handler) reconnects after 1 s on any close unless `stopped`, and never reads the code or reason. A tab duplicated from a seated tab copies `sessionStorage` (same token), so the two tabs would take the seat from each other about once a second. Not run (no browser).
- **[minor] No Origin check, no join secret.** `serve(...)` is called with `origins=None`, and a tokenless join takes any free seat. I verified a cross-origin `Origin: http://evil.example` join returns `hello`. Any page open in a player's browser, or anyone on the Wi-Fi, can take the free seat. Within the stated LAN model; it leaks nothing.
- **[minor] A daemon thread per lobby reset.** `TimeLimitedRival.__init__` starts a thread and `_reset_lobby` builds a new game, so a long session with `--rival baseline` leaks one idle thread per reset. Harmless at demo scale.
- **[minor] Reload while waiting.** In `waiting`, a drop frees the seat and deletes its token, so a refreshed first player gets `bad_token` then a tokenless join. `online.js` handles it (clears the token and reconnects). Fine, but the player may get the other seat if B joined in between.
- **[note] The slow-AI path blocks the event loop.** `TimeLimitedRival.__call__` calls `done.wait(budget)` on the loop thread, so a slow controller can stall every socket for up to 0.04 s per question (the Tech Lead's choice, deliberately under one tick).

## Facts bearing on the three choices the Tech Lead flagged (not decided here)
1. **AI-seat budget 0.04 s.** With the shipped baseline, 3 idle-human duels (771 ticks each) gave 0 fallbacks and a worst tick of 25 to 28 ms, so the baseline answers inside the budget on this Mac. With `rival_budget_s=0` every answer is replaced by WAIT (103 fallbacks in a 150-tick duel), the duel still replays exactly, and no fallback text reaches the client. A slower controller (the PPO net, a loaded laptop) would show up only in the server trace, not the player's screen.
2. **Label default.** With `--rival baseline` and no `--neutral`, every `state` message to the human carries `"rival": "AI rival: versus-baseline (scripted)"` (checked in `test_ai_seat_with_every_answer_late...`). Human vs human sends no rival kind. The label is static (no fallback counts).
3. **"Both press" reading of #41.** Verified: one press shows "Waiting for rival…" to the presser and "Rival wants a rematch" to the other; the restart needs both connected and both pressed; a press from a seat that then disconnects is cleared; with `--rival baseline` one press restarts (single human seat).

## Inherited findings (GATE-wave3)
| Finding | Status |
| --- | --- |
| `window.__smLast` on the page | Online page publishes nothing (`test_online_page_publishes_no_test_hook`; I also found no `__smLast` in `web/online.js`). The hosted `main.js` still publishes it, and the online server does not serve `main.js` (404, checked over HTTP). Inherited item not fixed in `main.js`, as the Tech Lead said |
| AI-seat time limit | Done differently from the 5 s runner policy (0.04 s per tick, `server/rival.py`); the 5 s figure would stall the human's loop. Held under a 0.6 s controller. Facts above |
| Neutral label default | Not default. Facts above |
| E1: no client-chosen rival, no engine code | Met. `/game.zip`, `/main.js`, `/index.html`, `/server/app.py`, `/pop/versus.py`, `/web/bridge.py`, `/../pyproject.toml`, `/%2e%2e/...`, `/art/`, `/.git/config`, `/traces/online/` all return 404/400 with no source text; POST, a 70 kB header and garbage bytes do not crash the server and it keeps serving; the page reads no query string |
| E3: fallbacks logged server-side | Met. Fallbacks go to the trace and the console summary; none of `fallback`, `slow_answer`, `controller_failed`, `budget` appears in anything sent to the human |

## Not checked
- A real browser, Phaser, `online.js`, the Rematch button's look (pixel edges, `background-image` crop of `art/tiles.png`, focus ring, the 4 px shadow stepping), key handling, sessionStorage reconnect, and two real machines. Playwright and a browser are not installed here. The button's code was read and `node web/ui.test.js` passes; its appearance is for Saad or a browser run.
- The macOS firewall prompt and the LAN URL on a real network (only `127.0.0.1`).
- A real 40 s keepalive timeout (not waited for).
- Gate 2 matters (hidden-state equivalence of guard versus disguised rival over the server is covered by the Tech Lead's `test_online_boundary.py`, which I read and ran, not re-derived).

## Known limitations
Two reproduced majors are left as strict xfails. `web/draw.js` duplicates the drawer in `main.js` (the Tech Lead's disclosed limitation, for the orchestrator).

## Unresolved findings
T13-QA-1 (major), T13-QA-2 (major). The minors above.

## Requested next action
Orchestrator: send T13-QA-1 and T13-QA-2 to the Tech Lead (T13-fix1). Suggested minimal shape, not binding:
(1) in `flush`, send per seat with a short timeout or `asyncio.gather` so a slow seat cannot hold the lock, and close that seat's socket on timeout so the normal drop rule applies;
(2) in `_join`, wrap the hello/replace steps so that a failure calls `match.connection_lost(seat, now)` (or set `seat` before the awaits).
Also consider an explicit `ping_interval`/`ping_timeout` that matches the 15 s rule, and not reconnecting on a "replaced" close in `online.js`.
When those are fixed, flip my two `xfail` tests (they are strict, so they will fail loudly until the `xfail` marks are removed by whoever owns that edit) and send to Gate 2.
Evaluation Specialist (Gate 2, after the fix): the boundary tests pass here; please re-check the label and the AI fallback path once `flush` changes.
Read `docs/final/orchestration/reports/T13-qa.md` on `gate/T13-qa`.

## Student decision required
Saad, facts only (decisions are his): the three the Tech Lead listed (AI budget, the `--rival baseline` default label, "both press"), plus whether a silent Wi-Fi drop should start the 15 s grace at once instead of after the library's roughly 40 s keepalive.
