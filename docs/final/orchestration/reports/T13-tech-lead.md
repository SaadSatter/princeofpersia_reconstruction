---
handoff_id: HO-T13-tech-lead
task_id: T13
date: 2026-11-24 ET
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T13.md@f2c25e8
source_branch: task/T13
source_commit: 160135c4932e8ee2da9377e4780b28841d3e5be7
reviewed_commit: n/a
verdict: n/a
---

# T13: tech-lead report

Status: done

## Work completed
Built `server/` (one authoritative `Match`, WebSocket and HTTP layer, trace replay, a
time-limited AI seat), an online page (`web/online.html`, `online.js`, `draw.js`, `ui.js`) with
the game-styled Rematch button, the `online` extra, `docs/final/ONLINE_PLAY.md`, rule row R-S01.
Tests were committed first (7119f91, failing), then the implementation. The orchestrator's
mid-task items (inherited findings, E1, E3) are handled and listed below.

## Paths
New: `server/{__init__,__main__,app,match,rival,trace}.py`, `web/{online.html,online.js,draw.js,ui.js,ui.test.js}`,
`docs/final/ONLINE_PLAY.md`, `docs/agent-sessions/T13-online-play.md`,
`tests/test_server_match.py`, `tests/test_server_ws.py`, `tests/test_online_boundary.py`, `tests/test_online_web.py`.
Changed: `pyproject.toml` (one line), `uv.lock` (websockets 15.0.1 only), `tools/web/build.py`
(ships online page and scripts), `web/main.js` (guarded Rematch button), `web/index.html` (ui.js tag),
`web/keys.js` (hint text), `docs/final/WEB_BUILD.md`, `docs/RULE_SOURCE_MAP.md` (R-S01), `tests/test_web_js.py` (addition).
`web/bridge.py`, `pop/`, `agents/`, `render/` untouched.

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Two clients, one duel, third "full" | yes | `tests/test_server_ws.py` (real sockets, fake clock) |
| 2 | Boundary: allow-list, B's rig/disguise change nothing, guard vs disguised byte-identical, statuses equal | yes | `tests/test_online_boundary.py` |
| 3 | Junk, oversize, other-seat ignored; legal filter | yes | `test_server_match.py` (parametrised junk, `invalid_inputs == 0`) |
| 4 | Trace replays to outcome and state hash | yes | `test_the_input_trace_replays_...`, `server/trace.py` |
| 5 | Disconnect pause, resume, forfeit, bad token | yes | `test_server_match.py`, `test_server_ws.py`; row R-S01 |
| 6 | Rematch button after end only; both presses; same seed; one press in single-human modes; styling | yes (code) | `test_online_web.py`, `ui.test.js`, `test_server_match.py`. Visual look NOT checked |
| 7 | No websockets import outside `server/app.py`; `uv lock --check` | yes | `test_no_module_outside_server_imports_websockets`; lock diff adds only websockets |
| 8 | Suite | yes | below |
| 9 | Manual run | partial | scripted run, below |

## Tests run
```
uv run --extra online --extra train pytest -q
1 failed, 1172 passed, 14 skipped, 2 xfailed in 128.76s (0:02:08)
FAILED tests/test_rl_policy.py::test_pure_python_logits_equal_the_numpy_forward_pass_on_200_observations
```
The one failure is the pre-existing T07 fixture test named in the brief (145 < 200 observations); I did not touch it.
`uv lock --check`: passes. Manual run: `python -m server --port 8799 --host 127.0.0.1`, then a scripted client script (not committed) opened three WebSockets: seats A and B, the third got `error: full`; A held `d` and got 37 `state` messages in 3 s, col 2 to 9; `GET /` returned 200. Not run: a browser, two machines, the firewall prompt, `--rival baseline` over a socket (tested in-process only).

## Findings
No defects found by me. Design choices QA should attack:
* The key `{"type":"keys"}` message is physical key names; the page filters to its seat's names and the server filters again.
* Pacing: at most 3 catch-up ticks, then the backlog is dropped.
* Both seats down: the earlier deadline decides who forfeits. A drop in "ended" frees the seat once nobody is connected.
* A frame over 1 MiB closes that socket (library limit); that counts as a drop for the sender.

## Inherited findings
1. `exposeForTests` / `window.__smLast`: the online page publishes nothing (`test_online_page_publishes_no_test_hook`). I did not change `main.js`'s hook on the hosted page (not in scope; it still always publishes there). Flag for the orchestrator.
2. `SeatControllerRival` with no time limit: `server/rival.py` `TimeLimitedRival` runs the hook on a daemon thread, waits at most 0.04 s (under one 1/12 s tick), else WAIT for that tick; the late answer is dropped, no new question is asked while one is pending (`test_a_slow_ai_rival_never_stalls_the_tick_loop_and_is_labelled`: 30 ticks against a 0.6 s controller take under 0.5 s). This is not the runner's 5 s policy (#24): a 5 s wait would stall the human's loop, so the budget is short; flag for Saad if he wants a different number.
3. Labels: human vs human sends no rival kind; the page shows "Rival". `--rival baseline` keeps the web build's "AI rival: name (kind)" label; `--neutral` shows "Rival". No new rule invented; whether the baseline label should default to neutral online is for Saad.
E1. The server alone picks the rival (`--rival`); the page reads no query string and never fetches `game.zip`, `agents/` or engine code. The HTTP allow-list serves only `online.html`, its four scripts, `art/*` and `manifest.json`; `/game.zip`, `/index.html`, `/main.js` return 404 (tested). This also means the hosted Pyodide page is not served by this server.
E3. The AI seat's fallbacks (slow answer replaced by WAIT, controller failure) are written to the server-side trace as `{"frame","seat":"B","source":"fallback","reason"}`, summarised in the server log, and never sent to the client. The rival label sent to the human is static (no fallback counts, unlike the web build's label, which counts them). A test checks nothing "fallback" reaches the human.

## Known limitations
* `web/draw.js` is a copy of `main.js`'s drawer, not a shared module: the existing `tests/test_gate_t14_qa_main_contract.py` loads `main.js` alone (and I may not edit existing tests), so sharing would have broken it. Duplication is for the orchestrator to resolve with approval. For the same reason `main.js`'s button is optional (`typeof SMUi`), and R still rematches at any time on the hosted page.
* The Rematch button's look, the page, Phaser and keys were never run in a browser.
* The Rematch default trace dir `traces/online/` is untracked and not gitignored.
* Pre-existing: the T07 fixture test fails.

## Unresolved findings
None of mine.

## Requested next action
Commit to review: 160135c4932e8ee2da9377e4780b28841d3e5be7 on task/T13
What changed: `python -m server` hosts one duel: first browser seat A, second seat B, third refused; the server steps 12 Hz from held keys, sends each client only its own seat's payload and fixed status text, pauses 15 s on a drop then forfeits, restarts on both Rematch presses with the same seed, and records an input trace that replays exactly. The AI seat (`--rival baseline`) is time-limited and its fallbacks stay on the server.
How to check it: `uv run --extra online --extra train pytest -q tests/test_server_match.py tests/test_server_ws.py tests/test_online_boundary.py tests/test_online_web.py`; manual: `uv run --extra online python -m server`, open the printed URL in two browser tabs (sessionStorage keeps one seat per tab); try closing a tab and reopening within 15 s. Attack: junk and oversize frames, token replay, double connections with one token, reconnect races at 15 s.
What I am unsure about: the 0.04 s AI budget; behaviour when both seats drop; real-browser behaviour of `online.js` and the button; Phaser `setSize` on pooled rectangles is unchanged from T14.
Touches the knowledge boundary or AI seat: yes (Gate 2 applies)

## Student decision required
Saad: (1) confirm the "both players press" reading of #41; (2) whether `--rival baseline` should label neutral by default; (3) accept the short AI budget in place of the 5 s runner timeout for the live server.
