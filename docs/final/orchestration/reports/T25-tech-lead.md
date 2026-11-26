---
handoff_id: HO-T25-tech-lead
task_id: T25
date: 2026-11-26
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T25.md@773b955
source_branch: task/T25
source_commit: 2de419a
reviewed_commit: n/a
verdict: n/a
---

# T25: tech-lead report

Status: done

## Work completed
Online page polish from Saad's playtest (decisions #95, #96, #97) plus the key hint (#98).
Base `orch/reviewed` 083546e. Failing tests first (f37d1a8), then the work (b25e8b2), then a
one-line comment fix (2de419a).

1. #95: on the online page a click on AI Model or Baseline starts a private match at once
   (`{"type":"join","create":true,"mode":...}`). Create / Join / code box sit in a block
   (`#human-lobby`) shown only after Human vs Human is chosen. The room code is not shown for
   AI rooms. The pure rule is `SMKeys.lobbyView(modeId)` in `web/keys.js` (so it is testable
   in node). The server is unchanged for this: the AI room is the existing T22 room; its
   `hello` still carries the room's code to its own seat only (the page needs it to rejoin
   after a refresh, and now hides it); a join with that code gets `full`.
2. #96: `#status[data-state="loading"]` is a fixed, full-viewport flex overlay centring its text
   (CSS only, so a resize recentres it). It covers the page while connecting or reconnecting.
3. #97: `server/app.py` `QuietUnusedConnections` filter on logger `server.ws` (passed to
   `serve(logger=...)`). A handshake failure caused by an empty or closed connection
   (EOFError, ConnectionError, timeout, InvalidMessage) is rewritten to one short INFO line
   with no traceback; any other handshake failure keeps ERROR and its traceback.
4. #98: key hints now say "S kneel: sword or uniform (sheathe first if your sword is drawn)."
   (seat B and the arrow set: "Down kneel: ..."), in all three hint forms.

Docs updated: `docs/final/ONLINE_PLAY.md` step 5, `docs/final/GAME_MODES.md` online section.

## Paths
`web/keys.js`, `web/online.html`, `web/online.js`, `server/app.py`, `tests/test_t25_online_polish.py` (new),
`docs/final/ONLINE_PLAY.md`, `docs/final/GAME_MODES.md`, this report. Nothing under `pop/`,
`agents/rl/**`, `tools/rl/**`, `evaluation/**`. No existing test edited.

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | AI / Baseline: one click, no Create/Join, no code | Yes, by test and by source; not in a browser | `lobbyView` tests; page-structure test; scripted client below |
| 1b | Create / Join only for Human vs Human, shown only then | Yes (same caveat) | `#human-lobby` hidden until human chosen; `createBtn` ignores clicks otherwise |
| 2 | Loading screen centred, also on resize | CSS rule tested; look unverified | `test_loading_status_is_a_centred_full_window_overlay_in_css` |
| 3 | Handshake noise quiet, real errors kept | Yes | two tests with real sockets; real server log empty after three spare connections |
| 4 | Key hint with #98 nuance | Yes | three node tests |
| - | Failing tests first | Yes | f37d1a8: 9 failed, 3 passed (the 3 are regression guards) |
| - | AI-room boundary holds | Yes | joiner of an AI room gets `full` only, no token or code; existing boundary tests pass |
| - | No change to `pop/`, `agents/rl/**`, `evaluation/**` | Yes | `git diff --name-only 083546e..HEAD` |

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q      (clean committed tree, 2de419a)
2203 passed, 11 skipped, 5 xfailed, 2 warnings in 414.54s (0:06:54)
```
A first full run (before 2de419a) had 4 failures: T22 probes
(`test_qa_T22_probes.py` x3, `test_t22_modes.py` x1) that forbid the mode label text in
`online.js`; my own comment spelled "Human vs Human". I reworded the comment; no test was
edited. `node web/keys.test.js`: 9 passed.

Scripted client against a real server (`python -m server --port 18765 --host 127.0.0.1`,
real shipped AI weights, no `--live`): fetched `/` and `/keys.js` (page has `human-lobby`,
keys.js has the new hint); opened three TCP sockets and closed them without a request (server
log showed only the three startup lines, no handshake error); for `mode=ai` and `mode=baseline`
sent `{"type":"join","create":true,"mode":...}`, got `hello` (seat A, keys: code, rival, seat,
token, type), received 37 `state` messages (all seat A) and a `status: playing`, rival label
"AI Model (trained)" / "Baseline (scripted)"; a second client joining with the room's code got
`error full` and no code or token. Script: scratchpad `client.py` (not committed).

## Findings
No findings by me. Not done: a real browser. I did not see the buttons, the centring, the
overlay colour or the hidden code box render, and I did not run the JS in a DOM (no jsdom
harness): the click flow in `online.js` is covered by source-level tests plus the pure
`lobbyView`, not executed end to end.

## Known limitations
- The `hello` for an AI room still includes the room code (to its own seat). The page stores
  it and never shows it. If QA or Gate 2 wants it removed from the wire, the page's
  refresh-rejoin (token plus code) needs another route.
- The loading overlay also covers the page during "Reconnecting" mid-duel (same state name).
  Intended by me as a "connecting screen", but Saad may want the game visible then.
- Overlay colours, font size (20px monospace) are my choice, not from a decision.
- Handshake filter matches by exception type, not by text, so a non-benign cause stays loud.
- After choosing Human vs Human, the AI buttons stay clickable (a click starts an AI match);
  a refresh in an AI room restores `roomMode` from sessionStorage.

## Unresolved findings
None.

## Requested next action
QA (Gate 1) then Evaluation Specialist (Gate 2, boundary of the private-match path). Read
`task/T25` at 2de419a.

Commit to review: 2de419a on task/T25
What changed: online page lobby (one-click private AI, Create/Join human-only), centred loading
overlay, quiet unused-connection log line, kneel key hint with sheathe nuance (#95 to #98).
How to check it: `uv run --frozen --extra play --extra train --extra online pytest -q tests/test_t25_online_polish.py`;
`node web/keys.test.js`; run `python -m server`, open the page in a browser and click each mode,
resize during "Connecting", reload inside an AI match (no code shown, the seat comes back).
What I am unsure about: the look (no browser); the overlay during Reconnecting; the code in
the AI room's `hello`.
Touches the knowledge boundary or AI seat: yes (the private AI-room path; no server rule
changed, only its page and logging)

## Student decision required
None.
