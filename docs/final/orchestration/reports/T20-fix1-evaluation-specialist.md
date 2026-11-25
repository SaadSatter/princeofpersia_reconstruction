---
handoff_id: HO-T20-fix1-evaluation-specialist
task_id: T20-fix1
date: 2026-11-25
from: evaluation-specialist
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T20-fix1-qa.md@47ebfea (reviewed abbe5ec, work 000f86c); tasks/T20-fix1.md@73d5206; decisions #81-#83, #85, #86
source_branch: gate/T20-fix1-eval
source_commit: 47ebfea (base; the probe-test changes and this report are committed on top)
reviewed_commit: abbe5ec3408c51c8a6469815847abc53bfa47a6b (as carried by 47ebfea)
verdict: REJECT
---

# T20-fix1: evaluation specialist report (Gate 2)

Status: done

## Work completed
Under #85 I removed the strict xfail from E1 and changed my `ast` source test to require exactly one new read (`started_move`) and still forbid `step`, `tick`, `reset`, `rematch`, `press`, `_duel*`, `rivals`, `_move_action`, `_rewrite`, `_started`. I proved the `_rewrite` label and `StartedMove` are reporting-only (#86), re-ran the 8-combination determinism test and the leak probes on schema 2, and measured what the summarizer's `moves` and `mechanics` give a T21 analyst. Everything about the knowledge boundary is clean. The summarizer, however, reports `flip: 0` for a running jump (E2, below), so the verdict is REJECT on measurement validity, not on a leak.

## Paths
`tests/test_eval_t20_probes.py` (changed: E1 mark removed, ast test updated, 7 new tests, 2 new strict xfails); this report.

## Acceptance criteria -> evidence (Gate 2 scope)
| # | Scope item | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | E1 mark removed, ast test allows one `started_move` | yes | `test_a_queued_direction_is_not_credited_with_the_running_flip` passes unmarked; `test_recorder_source_only_reads` asserts `started_move` is called and `_move_action`, `_rewrite`, `_started`, `_duel*`, `rivals` are not touched |
| 2 | #86: no rule reads `_rewrite`/`StartedMove` | yes | ast scan of `pop/`, `agents/`, `server/`: `_rewrite` appears exactly in `Duel.__init__` (the init), `Duel._start` (the write) and `VersusEpisode.started_move` (the only read). `snapshot()` (the state hash input) holds no "rewrite". `StartedMove` is used only in `started_move`. `test_rewrite_label_is_written_in_start_and_read_only_by_started_move` |
| 3 | The label changes no trace, state hash, observation | yes | `test_rewrite_label_changes_no_trace_hash_observation_or_message`: 3 seeds x human/baseline AI, 700 ticks. The same duel runs with the label and with `Duel._start` patched to drop it. Trace, state hash, every client message and every `observe`+`legal_actions` JSON are identical. A guard test shows labelled starts occur (`test_labelled_run_actually_exercises_labels`) and the blind run has none |
| 4 | No seat can see it | yes | `test_no_seat_surface_names_a_rewrite`: no "rewrite", "grace", "hop_turn", "_HOP_FLIP", "started_move", "StartedMove" in any observation, legal-action list or client message (2 seeds). `VersusEpisode` is never given to a seat, and `started_move` is on it, not in any observation |
| 5 | 8-combination determinism, leak probes on schema 2 | yes | `test_a_log_is_identical_whatever_b_hides` (A's log byte-identical whatever B hides, on schema 2 logs), `test_trace_hash_and_messages_equal_with_and_without_logging` (4 seeds x 2 rivals = 8), and the Tech Lead's own copy, all pass |
| 6 | moves/mechanics split measures what T21 needs | no | E2 (major), E3 (minor), see Findings |
| 7 | Earlier items 2-5 | yes | below |

Earlier items:
- Item 2 (one place for the resolved action): the recorder takes the resolved action only from `started_move`. Kick over a jump (R-V10), hop turned into a flip (R-V22), grace (R-V35) and stale drops all come from the engine's own `_start`, tested by `test_r_v10_...`, `test_r_v22_...`, `test_r_v35_...`, `test_starts_never_exceed_accepted_inputs_and_stale_drops_start_nothing` and a differential fuzz of grace against the engine's own `_grace_jump` hits. `action` rows no longer carry `effect`.
- Item 3 (recorder contract): the module docstring, the class contract in `server/telemetry.py` and TELEMETRY.md all name `started_move` as the one read beyond the frontend's.
- Item 4 (determinism after the change): re-run, passes; the accessor does not cache.
- Item 5 (TELEMETRY.md): seed warning, host per-seat counts, idle = no input, stuck = stayed, accepted is not executed, AI duels summarize the human only, refused-run 12 ticks: all present in the diff.

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q tests/test_eval_t20_probes.py
22 passed, 2 xfailed in 12.54s
uv run --frozen --extra play --extra train --extra online pytest -q tests/test_eval_t20_probes.py --runxfail
2 failed, 22 passed in 12.80s   (the two new E2 and E3 probes fail as intended)
uv run --frozen --extra play --extra train --extra online pytest -q
1635 passed, 12 skipped, 6 xfailed, 2 warnings in 298.52s (0:04:58)
```
With my two new strict xfails removed, the suite would show 2 failures (E2, E3). With E1's mark removed and nothing else added it is green.

## Findings
**E2 [major, reproduced] A running jump is never counted as a `flip`.** A running jump begins as a 4-frame run (`effect: moved`) and becomes the 8-frame flip inside the same move, with no second engine start. The `move` row therefore says `RUN_JUMP_RIGHT`, `effect: moved`, and `mechanics_used` gives `flip: 0`. R-V22 as amended (`pop/versus.py:171`) says every directional jump is a flip, so the summary would tell T21 that a player who only ran and jumped never used the flip.
Repro: `d` held 8 ticks, then `d`+`w` for one tick, then no keys for 14 ticks. Observation: t9 `started_move` is `RUN_JUMP_RIGHT` with `effect: moved` frames 1-4, then t13 `effect: flipped` frames 1-8 with `started_move` None. Result: `moves == {RIGHT: 2, RUN_JUMP_RIGHT: 1}`, `flip == 0`; expected 1. Strict xfail: `tests/test_eval_t20_probes.py::test_a_running_jump_is_counted_as_a_flip`.
Fix (for the Tech Lead, not me): count a `flip` for a started move named `JUMP_*`, `RUN_JUMP_*` or `_HOP_FLIP_*` (or when the effect turns `flipped` within a started move), and update the docstring that already claims "a running jump" counts. Same defect class as E1, one use at the start.

**E3 [minor, reproduced] A held `g` counts several draws and sheathes.** The key resolves to DRAW and SHEATHE in turn, so the `repeat` marker (same move name) never fires. A 30-tick hold gives `draw: 4, sheathe: 4`. It cannot turn "never used" into "used" wrongly, but it inflates "used once" and use counts. Strict xfail `test_a_held_draw_key_is_one_use`. Acceptable as a documented limit if Saad prefers; otherwise treat a hold id as the repeat key for toggles.

**Notes (not blocking)**
1. `moves` counts every engine start, including `repeat` ones: a 40-tick hold of `d` gives `RIGHT: 9`, a 30-tick `w`+`d` hold gives `JUMP_RIGHT: 3` against `flip: 1`. This is documented in TELEMETRY.md, but the summary does not show how many starts were repeats. For T21, a `moves_repeats` count (or excluding repeats from `moves`) would make the two columns reconcilable.
2. Two deliberate same-key taps on consecutive ticks during one move read as one hold (already a Tech Lead limitation).
3. Grace drop searches backward for the nearest same-side direction (QA's unreproduced concern). I could not produce a grace jump without an earlier direction either.
4. `_rewrite`, `rewrite` argument and `StartedMove` go beyond "the accessor only". I find them harmless (rows 2-4); Gate 3 rules on scope.
5. `RIG` under a 30-tick `t` hold gave no `move` and no mechanic in my probe seat position; this is a legality fact (refused, so not a use), not a recorder fault.

## Leak findings
None found. Probed: A's log byte-identical across B's hidden disguise, rig and wandering; no disguise or trap words in A's log; no client message, observation or legal-action list carries rewrite, grace, started or hop names; trace, state hash and all messages equal with and without `--playtest` and with the label dropped; recorder source forbids `step`, `tick`, `_duel`, `_move_action`, `_rewrite`. `_HOP_FLIP_<DIR>` appears only in the seat's own log.

## Baseline fairness
Not in scope. The telemetry change touches no baseline, observation or action.
## Reward and training method
Not in scope.
## Checkpoint reproducibility
Not in scope.
## Train / held-out separation
Not touched. I read no held-out file and tuned nothing.
## Evaluation validity and confounds
Not a comparative evaluation. Measurement validity of playtest telemetry: see E2 and E3. T21 should read `moves` as raw engine starts and `mechanics` as uses.
## Local inference performance
Not measured; no inference path changed. `started_move` is a few dict reads per tick (not timed).
## Replay and fallback
No trace format change. A replay of a duel is identical with and without the label. Baseline AI duels run with the recorder unchanged; the AI seat still has no log.
## Training-run readiness
Not applicable to this task.

## Known limitations
No real WebSocket clients or `play.py --versus --playtest` under a display. Probes use the server `Match` directly.

## Unresolved findings
E2 (major), E3 (minor).

## Requested next action
Tech Lead (T20-fix2, the last attempt before escalation): fix E2 so a started `JUMP_*`, `RUN_JUMP_*` or `_HOP_FLIP_*` counts one flip, decide E3, and optionally expose repeat counts. Remove my two strict xfails' marks as part of the fix (they are in my file; I or the Tech Lead under a #85-style note). Then Gate 2 re-check of `tests/test_eval_t20_probes.py` at the new sha.

## Student decision required
None.
