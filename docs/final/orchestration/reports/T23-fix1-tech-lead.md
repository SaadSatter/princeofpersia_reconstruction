---
handoff_id: HO-T23-fix1-tech-lead
task_id: T23-fix1
date: 2026-11-26
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T23-fix1.md@2d59733
source_branch: task/T23-fix1
source_commit: 4cad17f (work; this report is committed on top)
reviewed_commit: n/a
verdict: n/a
---

# T23-fix1: tech-lead report

Status: partial. The work is done, but the suite is not green: 7 failures remain, and two of them are outside what the brief let me change (items 1 and 2 in "Findings"). I did not edit those tests.

## Work completed
Base `dfe2d90` with `task/T23` `0c7d73a` merged (6041f6c). Failing tests first (b882931), then the work (4cad17f).
- Server trace: `WebGame.tick` records the human seats it released in `self.released`. `Match._tick` appends that per tick to `Match._releases`, and `Match.trace()` carries it as `"releases"` (one list of seats per tick). `"ticks"` is unchanged in shape. Both are reset on lobby reset and rematch.
- `server/trace.py` `replay` applies each tick's inputs, then its releases, then `tick()`. A trace with no `releases` key (older traces) still replays.
- `play.py`: a human seat with no legal key held calls `ep.release(seat)`, the same method as the hosted page. The refused-input telemetry row is kept.
- AI seats: the only three `.release(` call sites are `web/bridge.py` (human seats only), `play.py` (`shown_seats`, so the human only against an AI) and `server/trace.py`. `VersusRunner`, baseline and PPO never call it.

## Paths
`server/match.py`, `server/trace.py`, `web/bridge.py` (the `released` list), `play.py` (the one input hook), `tests/test_t23fix1_release.py` (new, 6 tests), `tests/test_t20fix1_recorder.py` (the one assertion), this report.

## #99 assertion changes (old → new)
| Test | Old | New |
| --- | --- | --- |
| `tests/test_t20fix1_recorder.py::test_a_jump_then_three_left_ticks_is_one_flip` | `assert left and all(r["effect"] != "flipped" for r in left)` | `assert not left` (the left is released before landing, so it never starts, #93). The `flip == 1` assertion is unchanged |

QA's four at Gate 1 (still failing, for QA to update): `test_t20_qa_probes.py` (three: repeat marker, release then new press, input held after a different move) and `test_t20_qa_refused_mirror.py::test_refused_mirror_agrees_with_real_resolution[3-None]`.

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Server trace records releases; replay gives the same outcome and hash; `test_server_match.py` passes unchanged | Partly | New `test_a_server_trace_with_releases_replays_to_the_same_outcome_and_hash` passes. The unchanged `test_the_input_trace_replays_to_the_same_outcome_and_state_hash` still fails (finding 1) |
| 2 | `play.py` calls `ep.release(seat)` | Yes | `test_play_py_releases_both_human_seats`, `test_play_py_against_an_ai_releases_only_the_human_seat` |
| 3 | #99 T20 assertion updated | Yes | table above |
| 4 | AI seats never release; T19 compare set identical | Yes | `test_an_ai_seat_is_never_released`; `evaluation/t19_compare.py ppo 1` on `dfe2d90` (extracted) and on this branch give byte-identical output except `wall_s` (32 episodes, 30 distinct final states, same `sha_first_seed` list) |
| 5 | Suite green on a clean tree | No | below |

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q   (committed clean tree at 4cad17f)
7 failed, 2357 passed, 11 skipped, 5 xfailed, 2 warnings in 342.00s (0:05:42)
```
Failures: `test_server_match.py::test_the_input_trace_replays_to_the_same_outcome_and_state_hash`; the four QA T20 tests above; `test_t22fix2_overlap.py::test_ai_room_logs_only_the_human_seat[ai]` and `[baseline]`. Base `dfe2d90` passes the overlap file (14 passed, run on an extracted copy).

## Findings
1. [major] `tests/test_server_match.py::test_the_input_trace_replays_to_the_same_outcome_and_state_hash` cannot pass unchanged. It replays `tr["ticks"]` with its own loop (`ep.step` then `ep.tick`) and never releases. A release is engine state, not an accepted input, so the loop reaches `stale_inputs` A 10 / B 11 against the live 9 / 9. (Only the stale counters differ in this scenario.) Any trace that records releases needs a replay that applies them; `server.trace.replay` does and matches the hash. Options for the orchestrator: (a) approve a 4-line update of that test to call `server.trace.replay(tr)` (my recommendation); (b) make a release that drops a queued input count as a stale input, which would pass the old loop here but changes a counter's meaning and would still not reproduce Saad's sequence (the old loop would start the left). I did not choose either.
2. [major] `tests/test_t22fix2_overlap.py::test_ai_room_logs_only_the_human_seat[ai|baseline]` (T22-fix2, existing test, not in my permitted writes). It drives seat A with seeded random key sets for 300 ticks and expects the log to end with `duel_end`. With the release rule the human's moves differ, A loses at frame 95, and the log ends `duel_end`, `rematch` (an ended room logs the rematch row on close). The engine and logging are right; the test assumes the duel is still running. Suggested update: accept `rematch` after `duel_end`, or end the check at the last `duel_end`. Needs an approved edit.
3. [minor] A release is recorded whenever it is called, including when nothing was queued. Replay is the same either way (`release` on an empty queue is a no-op).

## Known limitations
The hosted JS page needs no change (it goes through `WebGame.tick`). Telemetry rows are unchanged: a release logs nothing. Replay applies releases after the tick's inputs; a seat is either stepped or released in a tick, so the order across seats does not matter.

## Unresolved findings
1 and 2 above.

## Requested next action
Orchestrator: approve edits to the two tests in findings 1 and 2 (or choose option (b)), then QA at Gate 1 (the four T20 tests). Gate 2 applies: it touches the input rule, the server trace and replay.

Commit to review: 4cad17f on task/T23-fix1 (the report commit follows it)
What changed: the release rule from T23 now also reaches pygame (`play.py`) and the server trace, so replay reproduces a duel that had releases.
How to check it: `uv run --frozen --extra play --extra train --extra online pytest -q tests/test_t23fix1_release.py tests/test_t23_release.py tests/test_trace_replay.py`; the T19 compare check is `PYTHONPATH=. python evaluation/t19_compare.py ppo 1` run on `dfe2d90` and on the branch, diffing the output.
What I am unsure about: whether to choose option (a) or (b) in finding 1; the exact shape of the `releases` key (a list of seat lists per tick, kept apart from `ticks` so older readers do not break).
Touches the knowledge boundary or AI seat: no for observations and legal actions (AI seats never release); Gate 2 applies for the input rule and the server trace.

## Student decision required
none
