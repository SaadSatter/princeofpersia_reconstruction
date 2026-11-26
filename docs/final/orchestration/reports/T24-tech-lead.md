---
handoff_id: HO-T24-tech-lead
task_id: T24
date: 2026-11-25
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T24.md@b1514bc
source_branch: task/T24
source_commit: 2323635
reviewed_commit: n/a
verdict: n/a
---

# T24: tech-lead report

Status: done

## Work completed
`DOWN` (standing, not already disguised) over, or beside and facing, a downed uniformed guard now runs the `TAKE` move: 12 frames, effect `took_uniform`, disguised, sword sheathed, stance cleared. A dropped sword on the cell is still picked up first (R-V09, unchanged). `_versus_macro` routes `DOWN` through a new `Rival._kneel_target()` / `_kneel()`; `_take` and `_pickup` are untouched. Failing tests were committed first (3de572f).

## Paths
- `pop/versus.py` (`_versus_macro` dispatch, `_kneel_target`, `_kneel`)
- `tests/test_t24_kneel_takes_uniform.py` (new, 11 tests)
- `docs/RULE_SOURCE_MAP.md` (R-V17), `docs/final/VERSUS_SPEC.md` (R-V17 row)
- `docs/agent-sessions/T24-kneel-takes-uniform.md`, this report
- Commits: 3de572f tests, e21ddc1 engine, 8e9ac82 docs, 2323635 posture guard, then session note and report.

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | DOWN over / beside-facing takes uniform, 12 frames, sheathed | yes | `test_down_takes_the_uniform_in_12_frames[over|beside]` |
| 2 | Sword on cell first, uniform stays, then second kneel takes it | yes | `test_a_dropped_sword_on_the_cell_...`. Note: after the pickup the sword is drawn and DOWN is then a stance change, not legal, so the second step needs SHEATHE (or TAKE) first |
| 3 | DOWN with nothing unchanged | yes | `test_down_with_nothing_to_take_is_unchanged`, stripped body, already-disguised, hanging tests |
| 4 | TAKE unchanged; other seat's observation identical | yes | `test_take_is_unchanged`, `test_the_other_seat_sees_the_same_for_down_take_and_take` (full B observation, JSON equal, every frame) |
| 5 | No new action, DOWN legal where it was | yes | `test_no_new_action_and_down_stays_legal_where_it_was`; `legal_actions` not edited |
| 6 | Existing tests asserting DOWN does not take a uniform | none found | full suite green with no existing test edited. Grepped tests for DOWN with uniform/TAKE |
| 7 | Macro / baseline / PPO | see Findings | |
| 8 | Suite green | yes | below |

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q   (clean committed tree at 2323635)
1963 passed, 11 skipped, 5 xfailed, 2 warnings in 770.76s (0:12:50)
```
(Same run at e21ddc1+docs, before the posture guard and one extra test: 1962 passed, 11 skipped, 5 xfailed. The base 1a515ca suite line was not re-run by me.)

## Findings
- Macro layer: the only `DOWN` the macros ever issue is the ledge let-go (`agents/macros.py:371`, `_hang_drop`, planned at 188 and 298). `DISGUISE` issues `TAKE`. No macro, the baseline (`agents/versus_baseline.py` has no DOWN) or `agents/rl/` issues `DOWN` from standing over a body. `play.py` (62, 132) maps the human key to `DOWN`, which is the intended change.
- I added a `posture == "standing"` guard to the uniform branch so a hanging let-go in a cell shared with a body can never turn into a take (test included). The sword branch keeps R-V09's old condition.
- Shipped PPO rival: it acts only through macros, so its behaviour should not change. This is by reading, not measured; Gate 2 measures it.
- Other seat: `took_uniform` is already the motion effect TAKE exposes (R-V25/T19 handling is unchanged), so DOWN-take is indistinguishable by construction and by test.
- Choices the brief left open, flagged for QA/Saad: (a) DOWN while already disguised does not take (mirrors TAKE not being legal when disguised); (b) a body with a stripped uniform makes DOWN do the old crouch/potion, not `no_uniform` (R-V26 stays TAKE-only); (c) over a body on a potion cell, the uniform wins over drinking; (d) an armed rival (sword "sheathed") on a sword cell cannot pick up, so DOWN takes the uniform; (e) a rival with a drawn sword cannot DOWN at all (stance change), so it uses TAKE.
- `web/keys.js` hint text not edited (not permitted). List for T25: "S kneel: sword or uniform".

## Known limitations
No playtest done; headless tests only.

## Unresolved findings
None.

## Requested next action
QA Gate 1 on `task/T24` at the commit holding this report; Evaluation Specialist Gate 2 (shipped rival and baseline on the tuning starts, before and after, as T19).

## Student decision required
none
