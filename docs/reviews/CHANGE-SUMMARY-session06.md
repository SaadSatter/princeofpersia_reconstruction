# Change summary for the independent reviewer — session 06 (frontend, R-D02, R-D26)

For `.claude/agents/rules-reviewer.md`. Written by the implementation agent;
not a review.

**Trigger.** Student request (2026-10-26): a graphical Pygame frontend using
the original sprites and tiles, keyboard play, and modes that show an agent
playing (for the required recording). The student approved changing R-D02
(art), the source-use rule in `CLAUDE.md`, and adding `--watch`/`--replay`.

**Not changed.** `pop/` (engine, interface, observation, runner), `agents/`,
`evaluate.py`, the evaluation suite, prompts, the baseline, and all existing
tests. No trace was added or edited.

**Change.**
1. Rule text: `CLAUDE.md` source-use restrictions and layout; R-D02 revised,
   R-D26 added (`docs/RULE_SOURCE_MAP.md`); `docs/GAME_SPEC.md` §1 exclusions
   and §9; new `docs/ASSETS.md`.
2. `tools/fetch_assets.py`: sparse-fetches three SDLPoP image folders at a
   pinned commit into git-ignored `vendor/SDLPoP/`. Local only.
3. `render/anim.py` (pure): one accepted step → a clip of exactly the
   step's engine frames, built from the before/after observation, the
   step's effect, frames and `fell_rows`, and the outcome reason.
4. `render/assets.py` (pure): asset folder lookup, piece numbers,
   frame→image range shifts (read from SDLPoP's table; see ASSETS.md).
5. `render/draw.py` (pygame): draws from observation dicts and poses only.
6. `play.py`: human keys (via `Episode`), `--watch` (wraps the player and
   runs the real `run_episode`; the runner's `commit` hook reports each
   submitted action and its source), `--replay` (re-runs a trace through
   `Episode` and compares every step with the recorded kid and room).
7. `render/layout.py` (pure): which piece goes where, each in its own
   cell's column except the floor surface's perspective overhang. Added
   after the student's playtest found a wall side face hiding a pit
   (`test_regression_wall_side_face_hid_a_one_cell_pit`, which fails with
   the old placement).
8. `tests/test_frontend.py`: 49 tests (no pygame or images needed except
   one skipped smoke test).

**Things to check.**
- Information boundary: `render/` imports no engine module
  (`test_render_reads_observations_only`). `play.py` holds an `Episode`,
  like `play_text.py`. Watch mode's `WatchedPlayer` forwards `decide`
  unchanged; it sees only what the runner gives the player.
- Fallback labels: watch mode shows the runner's `source`; a fallback is
  shown as `[fallback] WAIT` (`test_watch_labels_fallback_moves_as_fallback`).
- Held-out cases: `--watch model-*` requires `--live` and refuses H1–H3
  (`test_play_refuses_unsafe_watch_options`); the baseline may be watched
  anywhere (it was already run on H1–H3).
- Watch mode keeps a second display `Episode` that replays the submitted
  actions. Determinism makes it identical (checked against the runner's
  trace in `test_watch_reports_each_submitted_step_with_its_source`); if it
  ever differed, the window could show a different state from the runner's.
- Human mode auto-submits `WAIT` while falling (the only legal action), so
  a fall plays through without key presses.
- Asset rights: no original image is tracked
  (`test_no_original_images_are_tracked`).
- Known approximations: tile offsets and sprite anchoring are ours, not
  pixel-exact; clips are resampled to the engine's block-based timing.

**Evidence.** `uv run pytest -q`: 168 passed, 1 skipped (local, pygame
installed). Clean copy without the `play` extra or images: 167 passed,
2 skipped. Visual checks were filmstrips rendered headless during the
session (not committed).
