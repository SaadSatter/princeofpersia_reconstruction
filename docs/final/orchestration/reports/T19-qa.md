---
handoff_id: HO-T19-qa
task_id: T19
date: 2026-11-25 ET
from: qa
to: evaluation-specialist
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T19-tech-lead.md@d32bbcb (implementation 7bbab99); docs/final/orchestration/tasks/T19.md@ef2756f; DECISIONS-2026-11-24.md rows #53-#55, #71-#73 @ef2756f
source_branch: gate/T19-qa
source_commit: see the commit that adds this file (recorded by the orchestrator under consumed)
reviewed_commit: d32bbcb608c9cb5a422ae4fed00d8d4136b6dc0d
verdict: ACCEPT WITH NOTES
---

# T19: qa report

Status: done

## Work completed
Checked out `d32bbcb` on `gate/T19-qa`. Lowered the volume floor of my own T05 probe (decision #71),
wrote `tests/test_gate_t19_qa_probes.py` (76 adversarial tests), ran the full suite and the Node test.
No blocker or major finding. Three minor notes. Production code and existing tests were not touched.

## Paths
- `tests/test_gate_t05_qa_probes.py` (my own T05 probe, one assertion): `decisions > 5000` became `decisions > 4000`.
- `tests/test_gate_t19_qa_probes.py` (new).
- This report.

### Decision #71: the floor I set
`decisions > 5000` is now `decisions > 4000`. Measured by the Tech Lead: 4735 decisions in the 36 seeded games (5357 on the
base). I set 4000, about 15% under the new volume, so that the probe still fails if the duels become much shorter or
the baseline stops deciding (it still proves coverage of the six rooms and 36 games) without tracking this
decision-rate change exactly. The zero-fallback assertion (`st["fallbacks"] == 0` for every scripted, non-random
seat) is unchanged and passes. I did not recompute the decision count myself beyond the pass at the new floor.

## Acceptance criteria -> evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Both key sets drive seat A in human vs AI and online; local 2P still splits | Met | `tests/test_t19_controls.py` (22 tests, in the suite, green); `web/keys.test.js` 9 passed; mine: `test_held_keys_through_the_bridge_give_a_flip_not_a_run` (WASD and arrow sets, held through `WebGame`), `test_opposing_directions_from_both_sets_do_not_crash_and_replay_identically` (a + right held together, w and up flickering) |
| 2 | left-up and up-left at 0, 1, 2 ticks give one flip; 3 ticks is two inputs; a press in a move's last frames is buffered; lone-direction latency stated | Met, with the caveat in Finding 3 | Mine: `test_direction_then_jump_ends_exactly_where_the_plain_jump_does_in_every_cell` and `test_jump_then_direction_ends_where_the_plain_jump_does_in_every_cell` (both directions, gaps 0-2, every bottom-row floor cell of rooms 1-6 and both facings: the end state equals the plain jump's, so no distance, landing, bump or fall changes); `test_three_ticks_apart_direction_then_jump_runs_first`; `test_the_window_is_not_sticky...`; Tech Lead's `test_t19_grace.py` (buffered press, 0-tick latency). The mutation `GRACE_TICKS = 0` makes my matrix test fail, so the tests do need the feature |
| 3 | Kneel for `took_sword`, TAKE, `no_uniform`; other seat's view of a disguised rival unchanged | Met | `tests/test_t19_kneel.py` (green); mine: `test_the_other_seat_never_draws_a_crouch_for_a_disguised_rivals_take` (a disguised B's take is a standing guard figure with no `took_uniform` effect and no crouch strip for A) |
| 4 | Standing jump flips, today's distances; climb and hop unchanged; rule row updated | Met | `tests/test_t19_flip.py`; my cell matrix (flip lands where the plain jump lands); `test_up_under_a_ledge_still_climbs_whatever_direction_came_first[0,1,2]`; `test_held_up_then_a_direction_under_the_start_ledge_still_climbs`; R-V22 amended and R-V35 added in `docs/RULE_SOURCE_MAP.md` (lines 156, 169) |
| 5 | Determinism | Met | `test_random_two_seat_inputs_never_crash_and_replay_identically` (12 seeds, 300 ticks, both seats random actions, full observations compared twice); Tech Lead's determinism tests |
| 6 | Suite green, real line | Met | below. No browser or pygame window was run by hand, by me or (per the handoff) by the Tech Lead |

Grace window probes asked for in the dispatch:
- 0 to 3 ticks, both orders: matrix tests above (3 ticks: direction-then-jump is two inputs; see Finding 3 for jump-then-direction).
- During a run: `test_continuing_a_run_keeps_the_running_jump` (Tech Lead, green) and the held-key bridge tests.
- Wall or ledge: `test_into_a_wall_the_window_ends_where_the_plain_jump_does[0,1,2]` (room 1 col 0 and room 3 col 9, never ends in the wall column), `test_a_jump_at_a_gap_edge_lands_the_same_with_and_without_the_window`, the climb tests.
- Disguised: `test_a_disguised_grace_flip_raises_suspicion_like_a_plain_jump[0,1,2]` (R-V19 flip price equal over the first 10 flip frames, with a guard in sight; the probe asserts it is non-zero), `test_a_disguised_hop_turned_into_a_flip_raises_suspicion`, `test_a_disguised_rival_in_the_window_shows_the_other_seat_nothing_a_plain_jump_would_not` (6 scripts; figure stays kind `guard`, same key set, no effect name beyond the plain jump's, the hop's and the guard motions).
- Both seats together: `test_both_seats_in_the_window_at_once_do_not_disturb_each_other` (4 x 4 gap pairs, each seat's trace equals its solo trace), `test_two_seats_flipping_toward_the_same_cell_never_end_sharing_it`, `test_seat_b_gets_the_same_window_mirrored`.

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q
1522 passed, 12 skipped, 4 xfailed, 2 warnings in 385.25s (0:06:25)
node web/keys.test.js
keys.test.js: 9 passed
uv run --frozen --extra play --extra train --extra online pytest -q tests/test_gate_t19_qa_probes.py
76 passed in 3.69s
```
Skips and xfails are the same classes as the base (12 skipped, 4 xfailed, as at `fc02687`). The two T19 failures the
Tech Lead reported are gone: the T05 probe by my floor change, the `test_server_ws.py` one by the amendment in `d32bbcb`.

Scope check: `git diff --name-only fc02687..7bbab99` lists only permitted paths (`pop/versus.py`, `pop/engine.py`, `web/bridge.py`,
`web/keys.js`, `web/keys.test.js`, `web/online.js`, `server/match.py`, `render/versus_view.py`, `play.py`, docs, new `tests/test_t19_*.py`
and the four allowed existing tests). `d32bbcb` adds the report and the one `test_server_ws.py` assertion (decision #72). No `agents/`, `agents/rl/`,
`tools/rl/`, `web/draw.js`, `web/main.js` or CI change. CI files unchanged.

## Findings
No blocker, no major. Reproduced:
1. [minor] `pop/versus.py` `Duel._grace_jump` / `_suspect`: a disguised rival in a guard's sight pays R-V19 run suspicion
   (+4 a frame) for the 1 to 2 run frames the grace window then discards. Repro: disguised A at room 2 col 2, guard at col 6
   in sight, `RIGHT` then `JUMP_RIGHT` 2 ticks later: suspicion 4, 8, then 14 (the flip's +6) against 6 for the plain jump
   on tick 0. The kid never moves during those frames. It is a small, consistent tell (4 or 8 points) that the rule map does
   not state; it is not a hidden-information leak. Expected: either accepted and noted in R-V35, or the discarded run frames not counted.
2. [minor] `web/bridge.py` human vs AI with a held `up` and `right` at the start cell (under a ledge): `up` alone climbs, both
   together is `JUMP_RIGHT` (a flip), `up` then `right` one tick later still climbs. This follows R-V22 and existing
   `seat_input`; I record it because players may see the same keys give a climb or a flip depending on press order.
3. [minor, restates the Tech Lead's Finding 4, not re-run by me] "3 ticks apart behaves as two inputs" holds for direction-then-jump
   (`test_three_ticks_apart_direction_then_jump_runs_first`). For jump-then-direction the hop turn applies for any of the 8 hop frames,
   so a direction up to 7 ticks after `UP` is one flip. The brief asked to keep "a direction during a hop still turns it into a flip",
   so the acceptance sentence for criterion 2 is met for the order it can be met for.

Unverified concerns (for Gate 2, not reproduced here): the macro planner (`agents/macros.py` `plan_path`) still prices
`JUMP_*` against the facing as a 4-frame turn plus the jump and its predictor models a reversal as a turn only, while the
engine now faces and jumps at once (decision #71). The PPO rival `ppo-run-1.json` was trained on the old dynamics.
The mean decision count per duel fell about 12% (5357 to 4735 in the same 36 games), so the dynamics change is visible in play.

## Not checked
- No browser or pygame window was run by hand; Playwright smoke (`.github/workflows/web-smoke.yml`) was not run.
- The kneel art itself was not looked at (decision #73 accepts the crouch strip); only the strip name per effect and frame count are tested.
- Stalled-tick catch-up on the hosted page (up to 3 ticks per frame) shortening the window in wall time: not exercised.
- `server/app.py` and the T18-fix1 files: not touched (parallel QA).
- Gate 2 matters (planner pricing, shipped PPO rival, baseline strength): left to the Evaluation Specialist.

## Known limitations
My disguise probes place the guard by hand at col 6 and read the engine's own suspicion meter; they do not replay a full guard patrol.

## Unresolved findings
Findings 1 to 3 (all minor, none block).

## Requested next action
Evaluation Specialist: read `docs/final/orchestration/reports/T19-qa.md` on `gate/T19-qa`. Check the planner's turn pricing, the baseline, R-V25 masking and `ppo-run-1.json` against the new dynamics, and recommend re-evaluation or retraining to Saad.

## Student decision required
None for QA. Finding 1 (count discarded run frames or not) is a small rule choice; Saad may want to decide it.
