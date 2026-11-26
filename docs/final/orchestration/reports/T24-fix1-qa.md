---
handoff_id: HO-T24-fix1-qa
task_id: T24-fix1
date: 2026-11-26
from: qa
to: evaluation-specialist
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T24-fix1-tech-lead.md@673f09f; tasks/T24-fix1.md@773b955; reports/T24-qa.md@48176a5; reports/T24-evaluation-specialist.md@d187e1c
source_branch: gate/T24-fix1-qa
reviewed_commit: 673f09f (code a3bf3fd, tests 07e622f, base d187e1c)
verdict: ACCEPT
---

# T24-fix1: QA report (Gate 1)

Verdict: **ACCEPT**. No findings.

## Suite (clean committed tree at 673f09f)
```
uv run --frozen --extra play --extra train --extra online pytest -q
1989 passed, 11 skipped, 5 xfailed, 2 warnings in 370.40s (0:06:10)
```
My probes (added after that run): `tests/test_qa_T24fix1_edges.py` 55 tests pass; with `test_qa_T24_probes.py` 75 passed in 0.14s.

## Acceptance
| # | Criterion | Met | Evidence |
| --- | --- | --- | --- |
| 1 | `_would_hang_down` is the `engine._down` test | yes | `pop/versus.py:295-300`: `ahead()` is a tuple, `not self.blocks(target)`, `not geom.supported(target)`; `engine.py:451-453` is the same three terms, same `self.blocks` (the Rival override) and `self.ahead()`. The own-cell sword and potion branches precede it in the engine, and the sword branch of `_kneel_target` is unchanged and first. |
| 2 | Edge cases, both facings | yes | 40 differential cases (ahead tile: space, floor, wall, closed gate, open gate, loose, drop plate, sword, rubble, spikes; body on own cell or on the cell ahead; facing +1 and -1): DOWN hangs exactly when the same DOWN with no body hangs, never disguises when it hangs, and disguises when it does not hang. Sanity test confirms space hangs and floor, wall, closed gate take. A dropped sword on the own cell at an edge (both facings): target is `sword`, never the uniform. |
| 3 | TAKE still takes at an edge | yes | `test_take_still_takes_at_every_edge_case` (space, floor, wall, closed gate, loose; both facings). |
| 4 | Other seat's view unchanged for DOWN-take vs TAKE-take away from edges | yes | per-tick JSON equality of seat B's observation, two starts (over, beside and facing). |
| 5 | My T24 probes unchanged and passing | yes | `tests/test_qa_T24_probes.py` untouched (not in the diff), passes. |
| 6 | Authorised test edit exactly as listed | yes | `git diff d187e1c..673f09f -- tests/test_eval_T24_f1.py`: only the third test, renamed `..._still_hangs`; asserts `_kneel_target() is None`, posture `hanging`, not disguised, effect `hanging`. Matches the old/new in the handoff. No other existing test changed. |
| 7 | Rule map and spec cite #98, #101 | yes | R-V17 row and VERSUS_SPEC R-V17 name decision 98 (SHEATHE then DOWN, or TAKE) and 101 (hang wins at an edge, TAKE takes). |
| 8 | Scope | yes | `git diff --name-only d187e1c..673f09f`: `pop/versus.py`, `docs/RULE_SOURCE_MAP.md`, `docs/final/VERSUS_SPEC.md`, `tests/test_eval_T24_f1.py`, `tests/test_t24fix1_hang_wins.py`, `docs/agent-sessions/T24-fix1-hang-wins.md`, the TL report. All permitted. |

## Mutation check
Removing `and not self._would_hang_down()` from `_kneel_target` makes 5 of my edge tests fail (restored; production untouched).

## Notes (not findings)
- The Tech Lead's report says "not tested: a body lying over an unsupported cell". My `body=ahead, tile=space` case forces a downed guard onto a hole cell: DOWN still hangs, as without a body.
- The Tech Lead's report quotes its suite run at a3bf3fd (311 s); I re-ran at 673f09f (370 s); same counts.
- Not run: A/B macro or PPO measurement, pygame, browser (Gate 2 re-runs the A/B; expected zero change).

## Requested next action
Evaluation Specialist re-runs the T24 before/after A/B (zero change expected).
