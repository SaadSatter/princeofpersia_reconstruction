---
handoff_id: HO-T13-fix1-qa
task_id: T13-fix1
date: 2026-11-24 ET
from: qa
to: evaluation-specialist
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T13-fix1-tech-lead.md@b75695f (task/T13-fix1); docs/final/orchestration/tasks/T13-fix1.md@286f380
source_branch: gate/T13-fix1-qa
source_commit: see the commit that adds this file (tests and report are committed together)
reviewed_commit: 385b3bfc05284f571b636ca527f583a9217d3e83 (checked out at b75695f, which adds only the report and session note)
verdict: ACCEPT WITH NOTES
---

# T13-fix1: QA report (Gate 1)

Status: done. Verdict: **ACCEPT WITH NOTES**. No blocker or major finding reproduced.

## Results
Full suite on `b75695f`, before my tests were added:
```
uv run --frozen --extra play --extra train --extra online pytest -q
1 failed, 1228 passed, 11 skipped, 2 xfailed in 182.18s (0:03:02)
FAILED tests/test_rl_policy.py::test_pure_python_logits_equal_the_numpy_forward_pass_on_200_observations
```
The one failure is the known T07 parity fixture (`assert 145 >= 200`), outside `server/`. The 2 xfails are not T13 ones
(the three T13 strict xfails are gone).
My new file alone: `tests/test_gate_t13fix1_qa_online.py`: `14 passed in 11.66s`. I did not re-run the whole suite with it
added; it only adds tests, and I ran the T13 files and my file together in the earlier targeted run (95 passed).
Scope: `git diff --name-only 9a3feac..b75695f` is inside the permitted paths; the three test edits remove only the mark
lines. No `.github/` or `ci/` change.

## Acceptance criteria to evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Every row fixed, with a test that fails without the fix | Met | Tech Lead reverted `server/`, `web/online.js`, `.gitignore` and saw 10 of 10 new tests fail (not re-done by me). I read each fix in the diff; row 10 is docs (checked in `ONLINE_PLAY.md`); row 8 (JS) is checked by source order only, see Not checked |
| 2 | Three strict xfails pass unmarked | Met | `-k stops_reading`, `-k died_during` and the EVAL-1 test pass in the full run; diff shows only the mark lines removed |
| 3 | Reconnect hello under 1 s with a half-open old socket | Met | Their test, plus my real-process run: hello in 0.003 s after A had stopped reading for 10 s (see "Manual run") |
| 4 | Silent drop detected in about 6 s | Met | Their scaled test, plus mine with the production 3 s + 3 s constants in real time (`test_a_silent_drop_is_noticed_in_about_six_seconds...`): detected between 2.5 and 9 s, keys cleared. Manual run: seat paused at 7.0 s (ping 3 s + timeout 3 s + 1 s close) |
| 5 | Suite line pasted, only T07 fixture fails | Met | above |
| 6 | No server left running | Met | `pgrep -fl "python -m server"` printed nothing after my real-process run; every server in my tests is closed in `finally` or by `Rig.__aexit__` |

## Regression hunt (the fix's new moving parts)
All of these pass unless listed under Findings.
| Area | Probe (in `tests/test_gate_t13fix1_qa_online.py`) | Result |
| --- | --- | --- |
| Queue ordering and lost status | stalled `SeatLink`, 300 state frames and the statuses `paused`, `playing`, `ended` | Every status delivered, in order; state frames stay ordered; newest frame kept; the last message is the `ended` status, so no stale frame after the end screen |
| Queue bound | slow but alive link (20 ms per send) with a 120 frame burst | Queue held at <= 49, socket not aborted |
| One seat's stall | two `SeatLink`s, one never completes | Only that socket aborted; the other keeps receiving |
| Reconnect racing the background close | six reconnects with one token in a row | Each hello fast, total < 3 s; exactly one link per seat, no grace started by an old socket's close, last socket's keys reach the match and frames come back |
| New socket dies right after hello while the old one is closing | abort at once, then reconnect inside the grace | Paused with deadline, then resumes on the third socket |
| Old close vs new held keys | keys on the new socket while the old closes | Held keys and writer task survive |
| Origin vs same-host browsers | raw upgrade requests: `127.0.0.1`, `localhost`, `LOCALHOST` (case), https origin with the same host, the machine's LAN IP on a `0.0.0.0` server | All 101. Refused 403: other site, `null`, `localhost` page to `127.0.0.1` host (mixed names), userinfo in origin, wrong port. No Origin: 101 |
| Origin edge cases | two `Origin` headers; `Origin` with no `Host` | Not accepted, server still serves the next client (no crash) |
| EVAL-1 per-duel fallbacks | four duels with a failing controller, then a late-answer controller with a queued reset, same seed | Each duel's trace has only its own entries (first entry at its own frame 0 to 2, sizes strictly increasing, past traces unchanged afterwards, `sum(sizes) == len(_fallbacks)`); the trace still replays to the same hash |
| Worker thread leak | 15 lobby resets | No worker threads left |
| Two rival resets overlapping | 400 rounds of question then reset against a 2 ms `reset` | Not reproduced (no overlap) |
| Original 25 probes and the cli real-process test | `tests/test_gate_t13_qa_online.py` unchanged | All pass (the 2 formerly xfail now pass) |

### Manual run (real process, real clock, localhost, production constants)
`python -m server --rival none`, two raw clients. A sent join and then stopped reading (`pause_reading`) for 10 s.
- B received 61 messages in the first 5 s (about 12 per second) and the loop was never blocked by A.
- A was detected silent at 7.0 s (B got `paused`); this is the 3 + 3 + 1 s chain, a little over the "about 6 s" in #48.
- A's token reconnect got `hello` in 0.003 s; B got `playing` again at 10.0 s. Process terminated, none left.

## Findings
No blocker, no major.

1. **minor (derived, not reproduced on a real slow link).** `server/app.py:34-35`, `SeatLink.put`: `MAX_QUEUED = 48` frames
   at 12 Hz means a link slower than the stream can lag by up to about 4 s before frames are dropped. Reproduction: the
   slow-link unit probe (queue held at 49 for a 120 frame burst). Expected: a real-time duel should keep a lag nearer 0.5
   s; actual: up to 4 s of stale view for a slow but alive client. Suggest a depth near 6.
2. **minor (measured fact, pre-existing).** One `state` message is about 19 KB (about 226 KB/s per seat, 1.8 Mbit/s;
   measured with `Match` and two joined seats at 12 Hz). The websockets write buffer is 32 KiB, so each send waits to drain
   whenever the link is under that rate. This is what makes the queue and the 2 s timeout matter on Wi-Fi.
3. **minor (open point 2, assessed).** `SEND_TIMEOUT_S = 2.0` (`server/app.py:35`). A single send waits only until the
   32 KiB buffer drains to its low mark, so a link at 100 KB/s waits about 0.25 s per send and a link at 30 KB/s about 0.8
   s. The seat is dropped only when one send is stuck for 2 s: a Wi-Fi stall or roam of 2 s or more, or a sustained rate
   under about 12 KB/s. The drop then costs a pause and a token reconnect (15 s grace), not the duel. Acceptable; a 4 to 5
   s timeout would still be well under the 6 s keepalive. The playtest on two machines is the real check.
4. **minor (open point 1, assessed).** Two resets overlapping in two threads needs two `reset` calls inside one worker
   cycle. The rematch flow calls it once per duel, so it is unreachable today; my 400-round hammer did not overlap.
5. **minor (concern, not reproduced).** After a rematch whose rival `reset` is still queued behind a slow question, that old
   question can finish and bump `inner.fallbacks` once before the reset runs, and that entry is then logged to the new
   duel. At most one stray entry per rematch, and only with a slow controller. Logging only (#49), no effect on play.
6. **cosmetic.** `server/app.py:63` `SeatLink.put(text, stale_ok)` never uses `stale_ok`; the state test is a string
   prefix check on `'{"type":"state"'`, which relies on key order from `json.dumps`. It holds today (my ordering test
   exercises it through the real message shape only indirectly).

## Not checked
- No browser: `web/online.js` close handler ("replaced", no auto reconnect) read only. By reading, the same-tab race I
  worried about cannot occur, because `connect()` runs only from a close event, so an old socket's "replaced" close cannot
  arrive after the new one is up. Still unverified in a real browser.
- Real Wi-Fi: slow-link behaviour (findings 1 to 3) is inferred from the code and the 19 KB message size, not measured.
- Not re-run: the Tech Lead's revert check (10 of 10 failing on the base).
- No Playwright, no two-machine run, no `--live` model calls, nothing outside localhost.

## Requested next action
To the Evaluation Specialist (Gate 2): the knowledge-boundary path changed (per-seat queue, `hello`, fallback log). Nothing new
reaches the client in my probes beyond the existing message types. Then the orchestrator for Gate 3.

## Student decision required
None.
