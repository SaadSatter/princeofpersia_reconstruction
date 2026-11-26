---
handoff_id: HO-T23-qa
task_id: T23 (T23, T23-fix1, T23-fix2)
date: 2026-11-26
from: qa
to: evaluation-specialist
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T23-fix2-tech-lead.md@444bd39
source_branch: gate/T23-qa
source_commit: see the final message (this report is committed on top of the test commit 435ab28)
reviewed_commit: 444bd39
verdict: ACCEPT
---

# T23: QA report (Gate 1)

Status: done

## Work completed
Checked out 444bd39 on `gate/T23-qa`. Verified 9c53235 (only the two approved edits, #113 and #114) and the
scope against `dfe2d90..444bd39`. Updated my four T20 assertions (#99). Added probes for Saad's sequence on
the server, in `play.py --playtest` and for replay and AI seats, and checked that they fail with
`VersusEpisode.release` made a no-op.

## Paths
- `tests/test_t20_qa_probes.py` (3 assertions), `tests/test_t20_qa_refused_mirror.py` (1 threshold)
- `tests/test_t23_qa_release.py` (new, 12 cases)

## #99 updates, old → new
| Test | Old | New | Why |
| --- | --- | --- | --- |
| `test_t20_qa_probes.py::test_the_repeat_marker_marks_the_second_engine_flip_of_one_held_key` (`d,w` x10, then released) | two `JUMP_RIGHT` starts, the second with `repeat` | one `JUMP_RIGHT`, no `repeat` | the queued flip lapses at the release |
| `::test_a_release_and_a_new_press_is_a_new_use_even_if_the_engine_queue_ran_on` | `flip == 2` | `flip == 1` | the second press is released in flight, so it never starts (the `not any(repeat)` line is kept) |
| `::test_an_input_held_after_a_different_move_is_not_a_repeat` | `flip >= 2` | `flip >= 1` | both later presses are released in flight |
| `test_t20_qa_refused_mirror.py::test_refused_mirror_agrees_with_real_resolution[3-None]` | `asked > 300 and refused > 20` | `asked > 200 and refused > 20` | fuzz seed 3 asks 251 now (106 refused) because released keys drop queued input; the mirror check `mism == []` is unchanged and holds. Other seeds: 2337, 1985, 381, 639 asked |

The held-through repeat marker is still covered by `test_a_very_long_hold_is_still_one_use` and my new test.

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| T23-1 | Saad's sequence: no move after landing, no logged move | Yes | hosted page/bridge: `tests/test_t23_release.py`; server: `test_server_saads_sequence_logs_only_the_flip[3,4,5,6,8]` (only `JUMP_RIGHT` logged, final column equals the never-pressed run); `play.py --playtest`: `test_play_playtest_saads_sequence_and_hold_through` (scripted `pygame.key.get_pressed`, one move logged) |
| T23-2 | Holding through the landing still runs on | Yes | `test_server_holding_through_the_landing_still_runs_on` (>= 3 starts), the play.py case (>= 3), `test_holding_through_the_landing_still_runs_on` |
| T23-3 | Grace (R-V35), hop turn (R-V22), kick (R-V10) unchanged | Yes | their existing tests pass in the full suite; the grace tests in `test_t20_qa_probes.py` pass unedited |
| T23-4 | AI seats identical | Yes | `test_ai_seat_never_releases_on_the_server` (spy: only `A` released against baseline); `web/bridge.py` and `play.py` call `release` only on human seats (`modes.step_ai_seat` path has no release); T19 compare set was run by the Tech Lead (T23-fix1 report), not repeated by me |
| fix1-1 | Release recorded in the server trace, replay gives the same outcome and hash | Yes | `test_server_replay_reproduces_outcome_and_hash[3,5,8]`; `test_replay_depends_on_the_recorded_releases` (a trace stripped of releases gives a different hash, so the test is not satisfied by ignoring them) |
| fix1-2 | `play.py` releases | Yes | the `--playtest` case above |
| fix2-1 | Clean branch, only T23 files | Yes | `git diff --name-only dfe2d90..444bd39`: `docs/RULE_SOURCE_MAP.md`, agent-session note, three reports, `play.py`, `pop/versus.py`, `server/match.py`, `server/trace.py`, `web/bridge.py`, `tests/test_server_match.py`, `test_t20fix1_recorder.py`, `test_t22fix2_overlap.py`, `test_t23_release.py`, `test_t23fix1_release.py`. No `.github/` or `ci/` change |
| fix2-2/3 | #113 and #114 edits only | Yes | `git show 9c53235`: the replay test now calls `server.trace.replay(tr)` and compares outcome and hash; the overlap test accepts `rematch` rows after `duel_end`. Both match the handoff table |
| 5 | Suite on a committed clean tree | Yes | below |

Sensitivity: with `VersusEpisode.release` made a no-op (a pytest plugin, no production edit), 7 of my 12
new cases fail (all five server cases, the replay-dependence case, the play.py case).

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q   (gate/T23-qa at 435ab28, tests committed; only this report untracked)
2360 passed, 11 skipped, 5 xfailed, 2 warnings in 766.95s (0:12:46)
```
The four T20 QA tests that failed at 444bd39 now pass; the new file adds 12 passing cases.

## Findings
None at blocker, major or minor level.
- Note (cosmetic, from the brief's reading of #93): `release` also fires on a tick where a key is held but its
  action is not in the legal list. That is the intended "keys ask for nothing legal" rule (R-V36), and no test
  shows a held, legal key losing its input.

## Not checked
- The browser page itself (Playwright, a real tab): I covered `WebGame.tick`, which the page runs, through
  the server `Match` and the existing bridge tests, not a live browser.
- The T19 compare set (identical AI traces): relied on the Tech Lead's run in `T23-fix1-tech-lead.md`.
- Gate 2 areas (AI quality, telemetry privacy) are left to the Evaluation Specialist.

## Unresolved findings
none

## Requested next action
Evaluation Specialist, Gate 2 (engine input rule, server trace and replay), then Gate 3.

## Student decision required
none
