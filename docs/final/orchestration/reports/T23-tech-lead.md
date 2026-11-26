---
handoff_id: HO-T23-tech-lead
task_id: T23
date: 2026-11-25
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T23.md@5f783d5
source_branch: task/T23
source_commit: 455dfb0a2bf66327afe6d482e01dd7b9a8964300
reviewed_commit: n/a
verdict: n/a
---

# T23: tech-lead report

Status: blocked (the fix works, but it breaks 6 existing tests and needs paths the brief does not permit; stopping as the brief says)

## Work completed
Reproduced Saad's sequence through `WebGame` and `VersusEpisode`: left, flip left (`w`+`a` for 2 ticks), hold `a`, release at tick 6. The queued LEFT starts on the landing tick (tick 12) and is logged, so the rival runs on. Failing test first (commit `task/T23` first commit), then the fix: `VersusEpisode.release(seat)` clears that seat's pending input (no log row, no counter), and `WebGame.tick` calls it when a human seat's keys yield no legal input. The hosted page and the server both go through `WebGame.tick`, so they share it. Rule row R-V36 added. The engine core (`Duel`, grace, hop turn, kick) is untouched, and AI seats never call `release`.

## Paths
`pop/versus.py` (one method), `web/bridge.py` (one `else`), `docs/RULE_SOURCE_MAP.md` (R-V36), `tests/test_t23_release.py` (new), `docs/agent-sessions/T23-release-after-landing.md` (new), this report.

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | No movement after landing, no logged move | Yes, through `WebGame` (hosted and server) | `tests/test_t23_release.py::test_released_direction_does_not_run_after_landing` |
| 1b | Same through `play.py --playtest` | No | `play.py` has its own input loop; it needs `else: ep.release(seat)` after its `if act and act in legal` branch. Not edited (T22-fix2 owns it) |
| 2 | Holding through the landing still runs on | Yes | `test_holding_through_the_landing_still_runs_on` |
| 3 | Grace, hop-turn, kick tests pass | Yes | `tests/test_t19_grace.py` and the hop/kick tests pass in the full run |
| 4 | Baseline and PPO seats identical | By construction, not run | AI seats never call `release`; `pop/` rules unchanged. The T19 compare set was not re-run |
| 5 | Suite green | No | see below |

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q   (at the dirty tree, before committing)
9 failed, 1962 passed, 11 skipped, 5 xfailed, 2 warnings in 774.33s (0:12:54)
```
Three of the 9 were an artifact of the uncommitted tree (`tests/test_eval_suite.py` heldout ledger, two in `tests/test_qa_T08_probes.py`). They pass on the committed branch and on base `a93d36a` (re-run: `tests/test_eval_suite.py tests/test_qa_T08_probes.py tests/test_server_match.py` gave 1 failed, 86 passed, 1 xfailed). I did not re-run the whole suite after committing. Six real failures remain:
- `tests/test_t20_qa_probes.py::test_the_repeat_marker_marks_the_second_engine_flip_of_one_held_key`
- `tests/test_t20_qa_probes.py::test_a_release_and_a_new_press_is_a_new_use_even_if_the_engine_queue_ran_on`
- `tests/test_t20_qa_probes.py::test_an_input_held_after_a_different_move_is_not_a_repeat`
- `tests/test_t20_qa_refused_mirror.py::test_refused_mirror_agrees_with_real_resolution[3-None]`
- `tests/test_t20fix1_recorder.py::test_a_jump_then_three_left_ticks_is_one_flip`
- `tests/test_server_match.py::test_the_input_trace_replays_to_the_same_outcome_and_state_hash`

## Findings
[major] server replay: `server/trace.py` and `Match.trace()` record only accepted inputs per tick. A release changes the engine state but is not in the trace, so a replay no longer reproduces the outcome (`stale_inputs` differs: 10/11 live against 9/9 replayed, and the state hash is expected to differ). Determinism of the server trace therefore needs the release recorded (for example a `[seat, null]` entry per tick) in `server/match.py` and `server/trace.py`, and the replay and `Match.trace()` readers updated. I cannot infer a release from the trace alone: AI seats legitimately hold a pending input across 6+ ticks, so any age-based engine expiry would change AI behaviour.

[major] five T20 tests assert the old behaviour. They hold a key for a few ticks, release it, and expect the engine queue to run on into a second move or flip (for example "a jump then three left ticks is one flip" now logs no flip). Under #93 that second move is exactly what must not happen, so these tests encode the bug. The brief forbids editing existing tests, so they need Saad's or the orchestrator's approval to update.

## Known limitations
`play.py --versus` and `--playtest` still have the bug until its one-line call is added. The telemetry recorder reads `ep.log` and `started_move`, so it follows once `release` is called.

## Unresolved findings
The two majors above.

## Requested next action
Orchestrator: decide, then re-brief a T23-fix1 that permits `server/match.py`, `server/trace.py`, `play.py` (after T22-fix2) and updating the five T20 tests and the server replay test. Do not send `task/T23` at `455dfb0` to QA as is.

Commit to review: 455dfb0a2bf66327afe6d482e01dd7b9a8964300 on task/T23
What changed: a human seat's queued input is dropped on any tick its keys ask for nothing legal (hosted page and server path only).
How to check it: `uv run pytest -q tests/test_t23_release.py`; seed 0, `A` at (2,0,8,-1), keys `w`+`a` for 2 ticks, `a` until tick 6, then none.
What I am unsure about: whether a release should also drop an input refused as illegal-now (I do, for any non-accepted key set); the trace format change; the T19 compare set was not re-run.
Touches the knowledge boundary or AI seat: no (AI seats never call `release`; no observation, legal-action or hidden-fact change). Gate 2 only matters if the server trace change touches the seat input path.

## Student decision required
none
