---
handoff_id: HO-T24-fix1-tech-lead
task_id: T24-fix1
date: 2026-11-25
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T24-fix1.md@773b955; reports/T24-qa.md@48176a5; reports/T24-evaluation-specialist.md@d187e1c
source_branch: task/T24-fix1
source_commit: a3bf3fd
reviewed_commit: n/a
verdict: n/a
---

# T24-fix1: tech-lead report

Status: done

## Work completed
- #101 (F1): new `Rival._would_hang_down` in `pop/versus.py` (cell ahead not blocked and not supported, the `engine._down` test). `_kneel_target`'s uniform branch returns None when it is true, so `DOWN` hangs as before; `TAKE` still takes the uniform. The sword branch is untouched (the engine checks the sword tile before hanging too).
- #98 (F2): `VERSUS_SPEC.md` R-V17 now says: with the sword then drawn, `SHEATHE` then `DOWN`, or `TAKE`, takes the uniform; plus the #101 ledge sentence.
- Rule-map R-V17 row updated (cites #98, #101, new test file, `_would_hang_down`).
- Commits: failing tests 07e622f, fix and docs a3bf3fd, this report after.

## Paths
`pop/versus.py`, `docs/RULE_SOURCE_MAP.md`, `docs/final/VERSUS_SPEC.md`, `tests/test_t24fix1_hang_wins.py` (new, 3 tests), `tests/test_eval_T24_f1.py` (one test edited), `docs/agent-sessions/T24-fix1-hang-wins.md`, this report.

## Authorised test edit (tests/test_eval_T24_f1.py, third test)
- Old: `test_down_at_a_ledge_edge_standing_over_a_body_takes_the_uniform_instead_of_hanging`: `_kneel_target() == "uniform"`; after DOWN + TAKE_FRAMES+2 ticks, `disguised is True`, posture `standing`, effect `took_uniform`.
- New: `test_down_at_a_ledge_edge_standing_over_a_body_still_hangs`: `_kneel_target() is None`; after DOWN + 30 ticks, posture `hanging`, `disguised is False`, effect `hanging`.
No other existing test changed.

## Acceptance criteria -> evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Failing test first | yes | 07e622f: 2 new-behaviour tests failed (3 failed on that commit incl. the edited one... see below), fix in a3bf3fd |
| 2 | DOWN hangs at an edge over a body; TAKE takes; away from edge DOWN takes | yes | `test_t24fix1_hang_wins.py` 3 tests |
| 3 | R-V17 row and spec sentence | yes | diff in a3bf3fd |
| 4 | Only the one test edited | yes | `git diff d187e1c --stat -- tests` |

Failing-first detail: at 07e622f the edited test and `test_down_at_the_edge_over_a_body_hangs_and_takes_nothing` failed; the TAKE and away-from-edge tests passed (they pin unchanged behaviour).

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q   (clean committed tree at a3bf3fd)
1989 passed, 11 skipped, 5 xfailed, 2 warnings in 311.34s (0:05:11)
```

## Findings
No findings. Beside-and-facing cases are unaffected in practice: a body ahead stands on a supported cell, so `_would_hang_down` is false there (covered by the away-from-edge test and all T24 tests passing). Not tested: a body ahead lying over an unsupported cell (not constructible with guards that stand on floor).

## Known limitations
No macro/PPO measurement run (none requested; Eval re-runs the A/B, zero change expected). No pygame or browser run.

## Unresolved findings
none

## Requested next action
QA Gate 1 on `task/T24-fix1` at the report's source_commit a3bf3fd; then Eval re-runs the T24 A/B.

## Student decision required
none
