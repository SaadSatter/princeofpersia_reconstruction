# Audit — session 08, Level 1 reconstruction (P0–P3)

| Field | Value |
| --- | --- |
| Date | 2026-10-26 |
| Commit | `78422ee` (branch `level1-reconstruction`, local) |
| Auditor | `/game-rules-audit` skill, run by the implementation agent in the session that wrote the change (so this is **not** the independent review; see `docs/reviews/CHANGE-SUMMARY-session08.md`) |
| Scope | `f9c2c14` (P0 loose-ledge fix), `f23efa9` (L1 reader, registry, Level 1 rules), `78422ee` (frontend) |
| Files read | `docs/MIDTERM_GUIDELINES.md` (interface, compare players, rubric 2b/2c/3b/3c/5a), `docs/GAME_SPEC.md` §4/§7/§8, `docs/RULE_SOURCE_MAP.md`, `docs/REQUIREMENTS_CHECKLIST.md`, `pop/interface.py`, `pop/observation.py`, `pop/runner.py`, `pop/engine.py`, `pop/levels.py`, `pop/levelfile.py`, `play.py`, `agents/`, `evaluate.py`, `tests/` |

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| A1 five operations | PASS | `pop/interface.py:44,57,63,70,92` |
| A2 unknown player rejected | PASS | `pop/interface.py:122-124` (`_check_player`), unchanged |
| A3 outcome fields | PASS | `pop/interface.py:92-101` status, reason, score, actions, invalid_actions, frames; calls are in the runner's episode header (`pop/runner.py:216`) |
| B1 observation keys | PASS with note | L1 reset observation keys, recursive: `actions_left, edges.{left,right}, kid.{col,facing,hp,max_hp,posture,row,sword}, last_result.{effect,fell_rows,frames,hp_change}, minutes_left, room, state.{exits,gates,loose_shaking,plates_pressed,spikes_sprung}, task, tiles`. All are in GAME_SPEC §8 except `kid.sword` and the new effects `took_sword`, `bumped_ceiling`, which GAME_SPEC does not list yet (finding 2). Frozen suite: `tests/test_frozen_suite.py` pins the reset observation of S1–S3/H1–H3 (unchanged). |
| B2 no other rooms / links / timers / level data | PASS with one finding | Script: every row of every other L1 room that is not also a row of room 1 is absent from the reset observation JSON (`[]`). `tests/test_level1.py::test_observation_shows_only_the_current_room` (no `link`, `plate_links`, `gates_open`, `guard`, `sha256`, `LEVEL1`). Guards are read from the file but not placed. Exception: finding 1. |
| B3 legal actions by posture only | PASS | `pop/interface.py:63-68` → `Game.legal_actions` → `LEGAL_BY_POSTURE` (unchanged); L1 standing list is the same 11 actions |
| B4 step results reveal nothing hidden | **FAIL** | finding 1 |
| B5 model prompt from observations only | PASS | `grep -rn "pop.engine\|pop.levels\|pop.levelfile\|GameState\|open(\|vendor\|LEVEL1" agents/` → no matches; `tests/test_architecture.py` now also forbids `pop.levels`, `pop.levelfile`, `level_fixture`; system prompt hash pinned (`tests/test_frozen_suite.py::test_model_system_prompt_unchanged`) |
| B6 baseline same inputs | PASS | `agents/baseline.py` unchanged; same forbidden-import test |
| C1 out-of-vocabulary rejected, no state change | PASS | `pop/interface.py:76-81`, `tests/test_interface.py` (snapshot before/after), unchanged |
| C2 non-string actions | PASS | `pop/interface.py:76-77` |
| C3 actions after terminal refused | PASS | `pop/interface.py:73-74` |
| C4 consecutive-invalid limit | PASS | `pop/interface.py:113-115`; tests in `tests/test_interface.py` |
| D1 step limit | PASS | `pop/interface.py:85-87`; L1 uses `max_actions` 600 (`pop/levels.py` `LEVEL1_LIMITS`); exhibition baseline runs on L1 ended `step_limit` at 600 |
| D2 call limit, failed calls count | PASS | `pop/runner.py:128-139`, `max_calls` from the situation (600 for L1); unchanged code |
| D3 per-call timeout, fallback label | PASS | `pop/runner.py:69-92`, unchanged; `tests/test_runner.py` |
| D4 trace fields | PASS | `pop/runner.py:170-186` unchanged; `tests/test_trace_replay.py` replays all 16 committed traces |
| D5 runner owns the Episode | PASS | `pop/runner.py:121-130` |
| E1 one engine step for human and agent | PASS | `play.py` `Driver.apply` → `Episode.step`; the entry clip (`Driver.intro`) only displays the first observation's `last_result` |
| E2 no pygame in `pop/` | PASS | `grep -rn "import pygame\|from pygame" pop/` → none |
| E3 macro frames ≤ 12 | PASS with note | new `PICKUP_SWORD = 12` (`pop/physics.py`), bump-ceiling uses `JUMP_IN_PLACE` 8; `perform` asserts ≤ `MAX_FRAMES`. The L1 entry (4 frames) runs in `reset`, not as a macro (R-D29). GAME_SPEC §4 does not list the pickup yet (finding 2). |
| E4 determinism | PASS | `uv run pytest -q -k "leak or legal or limit or determin or level1 or frozen or replay"` → 96 passed, 1 skipped; `tests/test_level1.py::test_reset_is_deterministic` |
| F1 rule map agrees with engine and tests | PASS | R-C14 (P0 fix), R-C21, R-C29, R-C30, R-C31, R-C32, R-C34, R-D27–R-D32 each name the code and a test that exists and passes |
| F2 no unjustified promotion | PASS | R-A03 stays `assumed` (DOS loader evidence added as support only); R-C06 corrected with new locators, label unchanged |

## Findings (most severe first)

1. `[should fix] pop/engine.py:Game._up (rule ceiling_loose) — the effect "bumped_ceiling" reveals that an unseen tile in the room above is a loose floor — standing at room 14 (0,3) and pressing UP returns effect "bumped_ceiling" while the observation shows no change (loose_shaking [], room 14 row 0 unchanged); the knocked tile is room 7 (2,3), not in view. Same for rooms 6 (0,5) and 12 (0,8). Options for the student: report "none" when the knocked tile is outside the current room, or keep it if the original visibly shows the floor above shaking (not verified).`
2. `[should fix] docs/GAME_SPEC.md §4, §5, §8 — L1's additions are not in the spec: kid.sword key, effects took_sword and bumped_ceiling, sword pickup action semantics (DOWN on S, 12 frames), the entry in last_result — GAME_SPEC is the inspectable rule specification (rubric 1a/1b).`
3. `[note] pop/runner.py — a model player can still be run on L1 programmatically (run_episode(model, "L1", seed)); its prompt legend has no entry for S and k. play.py refuses model watch on L1 and evaluate.py refuses L1, so no path a user would take does this.`
4. `[note] tests/test_level1_original.py — the original-file tests (counts, start, 87-action route) skip in CI by design (D1); their only evidence is local runs recorded in the session log.`

## Not checked

- Live model behavior on L1: not run (no live trials in this session; model on L1 is refused by `play.py`).
- Whether the original game visibly shows a floor shaking in the room above (decides finding 1): needs observed play.
- Course CI (`ci/midterm-saadsatter.yml`) on these commits: nothing synced to PR #57 (student instruction).

## Follow-up (after the audit, same session)

- Finding 1: changed in a separate commit after this report. The effect is
  now `none` when the knocked floor is not in the current room; the floor
  still falls. Regression test
  `tests/test_regressions.py::test_regression_bumped_ceiling_revealed_a_loose_floor_in_the_unseen_room_above`
  failed before the change (`'bumped_ceiling' == 'none'`) and passes after.
  The student decides whether this matches the original (not verified by
  observed play).
- Finding 2: addressed by the P4 documentation commit (GAME_SPEC §4, §5, §8).
- Findings 3–4: unchanged; recorded in `docs/LEVEL1.md`.
