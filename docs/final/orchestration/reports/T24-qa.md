---
handoff_id: HO-T24-qa
task_id: T24
date: 2026-11-25
from: qa
to: evaluation-specialist
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent
consumed: docs/final/orchestration/reports/T24-tech-lead.md@6f0975c
source_branch: gate/T24-qa
source_commit: see git log (head of gate/T24-qa)
reviewed_commit: 6f0975c
verdict: ACCEPT WITH NOTES
---

# T24 QA (Gate 1)

Verdict: **ACCEPT WITH NOTES**. No blocker or major finding. Two minors and two
notes for Gate 2 and the orchestrator.

## Suite
```
uv run --frozen --extra play --extra train --extra online pytest -q   (clean committed tree, 6f0975c + my probe commit c4ce987)
1983 passed, 11 skipped, 5 xfailed, 2 warnings in 564.70s (0:09:24)
```
My probes alone: `20 passed`. Against the base `pop/versus.py` (1a515ca swapped in, then
restored) the Tech Lead's file plus mine give `18 failed, 13 passed`: the positive
behaviour tests fail on the base, the unchanged-behaviour tests pass on both, as they should.

## Acceptance criteria to evidence
| # | Criterion | Met | Evidence |
| --- | --- | --- | --- |
| 1 | DOWN over / beside-facing: disguised after 12 frames, uniform gone, sheathed | met | TL `test_down_takes_the_uniform_in_12_frames[over|beside]` (fail on base); web, server and pygame probes below |
| 2 | Sword on cell first, uniform stays, then uniform | met, with a wording gap (F2) | probes `test_sword_on_cell_armed_vs_unarmed`: unarmed -> `took_sword`, armed -> `took_uniform`; TL sequence test |
| 3 | DOWN with nothing unchanged | met | `test_beside_but_facing_away...`, `test_a_guard_that_is_not_downed...`, `test_potion_cell_without_a_body_still_drinks` (`drank`), stripped body, already disguised |
| 4 | TAKE unchanged; other seat identical | met | `test_whole_world_identical_for_down_and_take_including_suspicion` (both seats' full observations, suspicion meter, both legal lists, end-state digest, every frame, over and beside); TL `test_take_is_unchanged` |
| 5 | Legal actions unchanged | met | `legal_actions` untouched in the diff; `test_legal_actions_unchanged_by_the_feature`; equal lists in the trace test |
| 6 | Existing tests asserting DOWN does not take | none found | scope diff shows no existing test edited; full suite green |
| 7 | Macros, baseline, PPO | partly (F1) | see F1 |
| 8 | Suite green, line pasted | met | above |

Scope: `git diff --name-only 1a515ca..6f0975c` lists `pop/versus.py`,
`docs/RULE_SOURCE_MAP.md`, `docs/final/VERSUS_SPEC.md`, `tests/test_t24_kneel_takes_uniform.py`,
`docs/agent-sessions/T24-kneel-takes-uniform.md` and the tech-lead report. All permitted; no existing test, no
`agents/ web/ server/ play.py`. R-V17 cites "Saad, decision #94, 2026-11-25". CI files untouched.

## Edge cases (all in `tests/test_qa_T24_probes.py`, all pass)
- Beside but facing away: nothing taken, DOWN is a plain crouch.
- Guard not downed: not stripped.
- Downed but not stripped: taken. Stripped body: DOWN is the old crouch, no `no_uniform` (R-V26 stays TAKE-only).
- Already disguised: DOWN takes nothing; a second DOWN after a take never retakes.
- Potion on the cell with a body: the uniform wins, potion stays on the floor, effect `took_uniform`. Before (base, `pop/engine.py:442-450` `_down`): DOWN on a potion cell always drank it (`drank`, +1 hp if hurt). Without a body it still drinks (probe).
- Sword on cell: unarmed picks up (`took_sword`, uniform stays), rival with a sheathed sword takes the uniform, as the TL said.
- Hanging over a body: TL test (posture guard). Mid-move DOWN: accepted and queued as on the base, no disguise during the move, deterministic.
- Other rival on the same cell, a rig on the cell: take still works, other rival not disguised.
- Two downed guards in reach: DOWN and TAKE give the same result (see F3).
- Determinism: same seed and inputs, same `digest(snapshot)`.

## Front ends (headless, the S key over a body)
- `web.bridge.WebGame`, `human_vs_ai` and `local_two_players`: disguised.
- `server.match.Match`, two humans, and human vs baseline (staged body in the real arena): disguised.
- `play.versus_input({"down"})` returns `DOWN`, legal, and the engine takes the uniform. (play.py's pygame loop itself not run.)
- Held-key repeat: after the take DOWN no longer matches (disguised), so no repeated take.

## Findings
- **F1 (minor, unverified by run, for Gate 2): the macro claim is incomplete.** The TL says macros issue DOWN only for the ledge let-go. `agents/macros.py:101` `ALL_ACTIONS` also contains `DOWN`, offered to the path planner (`_actions`, line 419; planned at 188 and 298 as the hang-down move). A hang-down needs an unsupported cell ahead, so a body must share the rival's cell at a ledge edge for DOWN to turn into a take. That is rare but possible (a guard dropped by a falling floor at an edge), and it would silently disguise the baseline/PPO rival. Not reproduced. Gate 2 should measure the baseline and the shipped PPO on the tuning starts (the TL's "cannot change" is by reading only).
- **F2 (minor, docs): wording.** Brief item 2, `docs/final/VERSUS_SPEC.md` R-V17 ("then the uniform on the next `DOWN` or `TAKE`") say a second DOWN takes the uniform. After the pickup the sword is drawn, where DOWN is a stance change and not legal as a kneel (`legal_actions`, `pop/versus.py:646`), so the player must SHEATHE or press TAKE. The TL noted it in the report but the spec sentence still says "next DOWN". Suggest "the next `TAKE`, or `DOWN` after sheathing".
- **F3 (note, pre-existing): `downed_guard_ahead` picks the own-cell body first.** With a stripped body on the own cell and a uniformed one ahead, TAKE and DOWN both do nothing (equal, so no T24 regression). Not new.
- **F4 (note): the TL's hanging test calls the private `_kneel_target()`, so it fails on the base with `AttributeError`, not with a behavioural failure.** It still guards the posture check on the new code. The behaviour is not tested end to end through `step`.
- Choices (a)-(e) in the TL report all confirmed by probe; they are design calls for Saad.
- Not a finding but a reminder: `web/keys.js` hint still lacks "S kneel: sword or uniform" (T25).

## Not checked
- The pygame event loop and a real browser (no Playwright run; the bridge was driven headless).
- Measured effect on baseline and PPO (Gate 2).
- A potion cell on the drawn-sword path (DOWN is not legal there).

## Requested next action
Evaluation Specialist Gate 2: baseline and shipped PPO on the tuning starts before and after, with attention to F1 (DOWN issued by the path planner next to a ledge).

## Student decision required
none
