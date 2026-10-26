# Change summary for the independent reviewer — session 08 (original Level 1 as `L1`)

For `.claude/agents/rules-reviewer.md`. Written by the implementation agent;
not a review. Branch `level1-reconstruction` (local; not synced to PR #57).

**Trigger.** Student decisions D1–D4 of 2026-10-26 (`docs/LEVEL1.md`):
reconstruct the original Level 1 as a separate scenario, keep the original
data out of Git, fix the S3 crash first, placeholders until the art milestone,
stop before combat (P5).

**Not changed.** The frozen suite (S1–S3, H1–H3: rooms, links, limits,
seeds), `agents/`, `evaluate.py`, `traces/`, `EVALUATION.md`,
`docs/EVALUATION_SUITE.md`, the model prompt.

**Change.**
1. `pop/engine.py` P0 (`f9c2c14`): when a loose ledge falls during `UP`
   from hanging or `DOWN` to hang, the kid falls (`_up` crashed with
   `TypeError`; `_down` left him hanging on air). Both reachable in S3.
2. `pop/levelfile.py` (new): pure reader of the original format (EQ.S /
   MOVER.S facts). `pop/levels.py` (new): pinned sources, `L1` built from
   `vendor/levels/LEVEL1` at run time, `get()` resolving suite ids and `L1`.
3. `pop/situations.py`: `Situation` gains `gates_open`, `start_falling`,
   `start_presses`, `rules` (defaults = old behavior). `pop/mechanics.py`:
   gates may start open; `press_once`. `pop/engine.py`: `_intro` (entry
   drop + plate press), sword pickup and loose-from-below behind
   `Situation.rules`; `bumped_ceiling` named only if the floor is in view
   (audit F1, `83892fc`).
4. `pop/interface.py`: `Episode` accepts a suite id, `L1`, or a `Situation`;
   first `last_result` = the entry (None for the suite).
   `pop/observation.py`: `kid.sword` only when rule `sword` is on.
5. `play.py`, `render/`: `L1` choice, entry clip, sword/skeleton shapes;
   screenshot mode's frame budget grows with scripted keys.
6. Tools: `tools/fetch_level1.py`, `tools/solve_level1.py` (maintainers).

**Tests.** `test_frozen_suite.py` (pinned hashes from before the change),
`test_trace_replay.py` (16 traces), `test_level1.py` and `test_levelfile.py`
(our own level files, `level_fixture.py`), `test_level1_frontend.py`,
`test_level1_original.py` (local only; skips in CI), three new
`test_regression_*`.

**Please check in particular.**
- Can any S1–S3/H1–H3 behavior differ from before (rules gating,
  `Situation` defaults, `Episode` lookup)? Are the pinned hashes a sufficient guard?
- Does anything original reach a player beyond the current room
  (observation, effects, errors, `last_result`, room labels)?
- Is any decoded original layout committed in any form (tests, docs, rule map)?
- Are the deviation rows (R-D27–R-D32) and the "missing" list in
  `docs/LEVEL1.md` complete and honest; is anything silently simplified?
- Rule map rows R-C06 (corrected facing), R-C29–R-C34: do locators support them?
