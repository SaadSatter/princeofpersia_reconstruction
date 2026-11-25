---
handoff_id: HO-T20-tech-lead
task_id: T20
date: 2026-11-25
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T20.md@b582d58
source_branch: task/T20
source_commit: c1be053
reviewed_commit: n/a
verdict: n/a
---

# T20: tech-lead report

Status: done

## Work completed
Playtest telemetry per decisions #67 and #68. `server/telemetry.py` is a pure reader (observe, legal_actions, outcome) hooked into `Match` (join, reconnect, disconnect, pause, tick, end, forfeit, rematch, close) and `play.py --versus`. Off unless `--playtest`. `tools/telemetry/summarize.py`, `docs/final/playtest/TELEMETRY.md`, one draft CONSENT paragraph and the ONLINE_PLAY flag line are added. No change to `pop/`. The failing tests were committed first (`bd8109a`, importing the then-missing `server.telemetry`; I did not run that commit separately).

## Paths
`server/telemetry.py` (new), `server/match.py`, `server/app.py` (`_room_failed` closes logs), `server/__main__.py`, `play.py`, `.gitignore`, `tools/telemetry/summarize.py`, `tests/test_t20_{telemetry,summarize,play}.py`, `tests/data/t20_telemetry/*.jsonl` (fixture; not named in the brief, a data file for the permitted tests), `docs/final/playtest/TELEMETRY.md`, `docs/final/playtest/CONSENT.md` (new section only), `docs/final/ONLINE_PLAY.md`, `docs/agent-sessions/T20-playtest-telemetry.md`.

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Off by default | yes | `test_off_by_default_writes_nothing`, `test_the_server_flag_is_store_true_and_off_by_default`, `test_no_flag_no_files` |
| 2 | Scripted two-client duel writes both logs, #68 types, tick order | yes | `test_both_seats_logged_in_tick_order_with_known_types` and the idle, connection, forfeit, rematch, sword, abandon tests |
| 3 | Leak test | yes | `test_other_seats_disguise_and_traps_never_appear_in_a_log`, `test_own_trap_is_logged_for_the_owner_only`, header test |
| 4 | Trace and state hash identical | yes | `test_trace_hash_and_every_client_message_are_the_same_with_telemetry` (human) and `test_same_with_the_ai_seat` |
| 5 | No client message changes | yes | same two tests compare every drained message |
| 6 | summarize fixture, byte-identical | yes | `tests/test_t20_summarize.py` |
| 7 | Suite green | yes | below |

## Tests run
```
uv run --all-extras pytest -q
1568 passed, 11 skipped, 4 xfailed, 2 warnings in 394.16s (0:06:34)
```
(plain `uv run pytest -q` fails to collect here: numpy missing without extras. `uv run --extra online pytest -q tests/test_t20_telemetry.py` 17 passed; `--extra play` tests/test_t20_play.py 3 passed.) Scope check `git diff --name-only bdc3c76..HEAD`: only the paths above.

## Findings
None blocking. Not checked: a real browser or two live WebSocket clients (tests drive `Match` directly; app.py change is only `_room_failed`, tested directly). play.py ran only under the dummy video driver with `--keys`.

## Known limitations
- Event meanings are what a seat's own view can show: `block` in the summarizer is an accepted STANCE_UP/STANCE_DOWN (a block that stopped a blow is not visible to a seat); `flip` is an accepted action whose `effect` is "flipped" (only checked on ticks with an input); `hit` is a heart lost with someone or a flying sword in the room and no fall; `sword_drop` cause is `thrown` or `knocked_away`.
- `action` events log every tick an input is held (no collapsing); a 5-minute duel can reach a few thousand lines per seat.
- Refused inputs are read by mirroring `WebGame.tick`'s key resolution before the tick (`Match._note_refused`); the bridge itself never submits an illegal action.
- The AI seat gets no log (header `rival` says baseline). The host summary holds counts and the engine reason only.
- `s` is wall-clock including pauses; idle is counted in ticks.

## Unresolved findings
None.

## Requested next action
QA (Gate 1) then Evaluation (Gate 2) on `task/T20`.

Commit to review: c1be053 on task/T20 (this report is committed after it)
What changed: with `--playtest`, the server and `play.py --versus` write per-seat JSONL logs and a host summary; `summarize.py` turns a directory into JSON and Markdown.
How to check it: `uv run --all-extras pytest -q tests/test_t20_*.py`; `uv run --extra online python -m server --playtest --rival baseline`, play, then `python3 tools/telemetry/summarize.py traces/playtest`.
What I am unsure about: thresholds (`IDLE_THRESHOLD_S` 3, `REFUSED_RUN_MIN` 3, `STUCK_ROOM_S` 60) are proposals; the `hit`/`heart_lost` cause heuristic; the fixture path outside the brief's list; the header carries the seed and `commit` per the brief (host-only files); whether the CONSENT draft wording suffices.
Touches the knowledge boundary or AI seat: yes (reads each seat's observation and writes per-seat files; Gate 2 applies)

## Student decision required
CONSENT.md draft addition and the three thresholds need Saad's approval.
