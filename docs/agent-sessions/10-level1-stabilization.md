# Session 10 — Level 1 post-review stabilization (before P5)

| Field | Value |
| --- | --- |
| Agent | Claude Code (CLI), model Claude Opus 5.5 (`claude-opus-5-5`) |
| Role | Implementation agent (instructions: `CLAUDE.md`) |
| Session ID | `d4e6718b-405e-4e8f-9665-d314679d5fa9` (same CLI session as 08, continued) |
| Date | 2026-10-26 |
| Branch | `level1-reconstruction`, **local commits only**: nothing pushed, merged or synced to PR #57 |
| Transcript | Local only, not committed |

## Student instructions

The independent `rules-reviewer` reviewed session 08's work. The student
relayed its findings and approved fixing them before P5: (1) a blocking
loose-floor movement bug, reproducible in S3, which also invalidated the
87-action Level 1 route; (2) keep the frozen suite unchanged and strengthen
trace replay to the complete state, stopping on any divergence; (3) find a
new legitimate route; (4) exit activation by any plate, the loose-floor
required bit, an always-true test assertion, R-C29 and potion provenance,
checklist and session log, and a review of committed layout facts (flag,
don't delete). Out of scope: repository visibility, artwork permissions,
new art, P5. The reviewer's own report is not in this repository; this
session worked from the student's summary.

## 1. Movement bug

**Root cause.** Run, careful step, standing and running jump, and climb up
each planned a destination, ran their frames, then placed the kid there.
`_tick` could meanwhile drop the loose floor under him and start his fall;
the macro then placed the still-"falling" kid at the planned cell. He was
left falling on solid ground (S3: `RUN_JUMP_RIGHT WAIT RIGHT JUMP_RIGHT
RUN_JUMP_RIGHT JUMP_RIGHT`) or fell on into a wall (S3: `... LEFT
STEP_LEFT`; S1: `RIGHT RUN_JUMP_RIGHT RUN_JUMP_RIGHT WAIT STEP_RIGHT`, the
step lands the kid in the wall at room 2 (2,3)). A search over legal
actions with the session-08 engine reached it in **S1, S3, H1, H3** (S2 and
H2 have no loose floors). Session 08's P0 had patched only the two climbing
cases.

**Fix (R-D33).** `Game._phase`, one resolver used by every move and timed
action. The kid keeps his footing until a departure frame (run 2/4, step
4/8, standing jump 6/12, running jump at once, climb up 4/12; hangs and
actions on the spot throughout). A floor falling before departure
interrupts the move and he falls from where he stands; after departure he
is in motion (`_airborne`), the floor he left no longer affects him, and
`_enter` checks support on arrival. Walls are never entered: destinations
are checked against walls before the move, and an interrupted kid is
never placed.

## 2. Frozen suite

- Nothing in the suite's definitions, seeds, limits, prompts, results or
  traces changed (`git diff 0e5df5f -- traces EVALUATION.md agents evaluate.py`
  empty). `docs/EVALUATION_SUITE.md` gained one change-log row.
- `tests/test_trace_replay.py` now also checks the complete authoritative
  state after reset and every step (kid incl. fall progress and sword,
  frames, terminal, all tiles, gates, exits, plates, spikes, loose floors,
  episode counters) against golden fingerprints made by replaying each trace
  **with the engine at its recording commit** (temporary worktrees at
  `3c4c210`, `06ff044`, `b2a6e2a`, `c23ebf7`; `8bd8cb1` for the dev trace).
  Mutation check: `GATE_HOLD` 50 → 49 is caught at state 11 of an S2 trace.
- **No divergence**: 16 of 16 traces, 292 states, identical. The correction
  therefore changes only behavior no recorded episode reached.

## 3. Level 1 route

- The session-08 route was invalid: its 5th action (`JUMP_RIGHT` off the
  loose floor at room 1 (2,6)) left the kid "falling" on solid floor at
  (2,8) on the old engine; on the fixed engine the route breaks by action 23.
- New route (`tools/solve_level1.py`, fixed engine), pinned in
  `tests/test_level1_original.py`: start → sword in room 15 → exit in
  room 9; **won, 87 actions, 0 invalid, 790 frames, sword taken in room 15,
  1 HP left**; no inconsistent state at any frame.
- Frontend: `play.py L1 --keys <route>` (headless, original art) ends
  "ESCAPED! (actions 87, invalid 0)".
- Solver fix: its search key ignored the exit's position, so waiting for an
  opening exit was pruned. With the fix, the shortest win without the guard
  is 20 actions (rooms 1, 2, 3, 9); session 08's "28" was measured on the
  buggy engine.

## 4. Other review findings

| Finding | Resolution |
| --- | --- |
| Exit opened only by raise plates | `openexit` (`Source/MOVER.S:562-569`) has no plate-type test: any plate opens a linked exit. Engine and R-C09 corrected; `test_rules.py::test_any_plate_kind_opens_a_linked_exit`. No suite scenario links a drop plate to an exit. |
| Loose-floor required bit ignored | Read in one place in all 29 source files: `BREAKLOOSE` (`Source/MOVER.S:394-397`), so a required loose floor never breaks. No Level 1 loose floor has it; the reader refuses one rather than simulate it as breakable (R-C35). |
| Trace replay coverage | Complete-state fingerprints (section 2). |
| Always-true assertion (`tests/test_level1.py`) | Now compares L1's legal actions with a suite scenario in the same posture. |
| R-C29 provenance | Substantiated from the Apple II source: `GETINITOBJ` (`Source/FRAMEADV.S:2217-2234`, "1=gate up, 2=gate down", table `initsettings` at lines 22-23), run at level start by `SETINITIALS` (`Source/SUBS.S:1441-1466`, called at `Source/TOPCTRL.S:274`). Specs other than 1 and 2 are refused. |
| Potion rule (R-A03) classification | Same routine shifts the stored potion value left 5 at load (`Source/FRAMEADV.S:2239-2245`); drinking reads `>> 5` (`Source/CTRL.S:2146-2151`). Promoted `assumed` → `code` with these locators. |
| Checklist, session log | `docs/REQUIREMENTS_CHECKLIST.md` (new Level 1 section, regression list), this log, `docs/LEVEL1.md`, `docs/IMPLEMENTATION_PLAN.md`, change summary `docs/reviews/CHANGE-SUMMARY-session10.md`. |

## Layout-data review (for the student's decision; nothing removed)

A scan of every tracked file found **no original room row and no room-link
tuple** (matches are only coincidences in the authored suite, which
predates this work). Committed original facts, all descriptive:

| What | Where |
| --- | --- |
| Single coordinates: start (room 1 block 0), the entry plate (room 5 (0,2) / screen 5 block 2), the slammed gate (room 5 (0,9)), guards (room 3 block 17, room 21 block 6), two cells in the audit (room 14 (0,3), room 7 (2,3)), the loose floor at room 1 (2,6) | `docs/RULE_SOURCE_MAP.md`, `docs/GAME_SPEC.md`, `docs/LEVEL1.md`, audit report, `tests/test_level1_original.py` |
| Room numbers of the sword (15), exit (9), guards (3, 21) | same |
| Partial connectivity: rooms 13 and 18 link only to each other, room 24 unlinked, 21 reachable; the route's room sequence 1 → 2 → 6 → 8 → 7 → 20 → 12 → 15 → … → 3 → 9 | `docs/RULE_SOURCE_MAP.md` R-C34, `docs/LEVEL1.md`, `tools/solve_level1.py` `DEFAULT_VIA` |
| Aggregate tile counts | `tests/test_level1_original.py` |
| The 87-action route (actions only; replaying it needs the local file) | `tests/test_level1_original.py` |

Assessment: none of this is a complete or reconstructible layout; the
room sequence and link facts are the most revealing (part of the room
graph). Options: keep as is; or move the route and room sequence out of
committed files (e.g. compute the route at test time). The student decides.

## Verification

| Check | Result |
| --- | --- |
| `uv run pytest -q` | 281 passed, 1 skipped |
| `tests/test_regressions.py` | 25 passed (14 loose-floor movement); 9 of the 10 new movement cases fail on the session-08 engine (the standing-jump-after-departure case happened to end consistent there) |
| `tests/test_trace_replay.py` | 33 passed (16 traces, field and complete-state checks) |
| Frozen baseline suite, fresh run vs `traces/eval/` | 12/12 won, 0 differences |
| Impossible-state and crash search, six suite scenarios | none |
| L1 route, engine and frontend | won, 87 actions, 0 invalid, sword, 1 HP |
| Fresh clone, `UV_OFFLINE=1`, no level file | 272 passed, 10 skipped (6 original-file tests by design) |

## Commits (branch `level1-reconstruction`)

| Commit | Content | Files |
| --- | --- | --- |
| `b061194` | Movement resolution `_phase` (R-D33), regression tests, new L1 route | `pop/engine.py`, `pop/physics.py`, `tests/consistency.py`, `tests/test_level1_original.py`, `tests/test_regressions.py` |
| `e999181` | Complete-state trace replay with golden fingerprints | `tests/data/trace_states.json`, `tests/test_trace_replay.py`, `tests/trace_state.py` |
| `a2b49ae` | Exit by any plate, gate spec 1/2, required loose floor, assertion fix | `pop/levels.py`, `pop/mechanics.py`, `tests/test_level1.py`, `tests/test_levelfile.py`, `tests/test_rules.py` |
| `04cf17f` | Documentation; solver search-key fix | `docs/EVALUATION_SUITE.md` (change-log row only), `docs/GAME_SPEC.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/LEVEL1.md`, `docs/REQUIREMENTS_CHECKLIST.md`, `docs/RULE_SOURCE_MAP.md`, `docs/agent-sessions/10-level1-stabilization.md`, `docs/reviews/CHANGE-SUMMARY-session10.md`, `tools/solve_level1.py` |
| (handoff commit) | This log and the change summary completed for the handoff (documentation only) | `docs/agent-sessions/10-level1-stabilization.md`, `docs/reviews/CHANGE-SUMMARY-session10.md` |

Not committed, by design: original level files (`vendor/levels/`, git-ignored),
reference sources (`vendor/ref-levels/`), bundled art (`assets/original/*/`,
course branch only), scratch scripts and screenshots (session scratchpad,
outside the repository), local transcripts, API keys (none used).

## Remaining fidelity limitations (Level 1)

From `docs/LEVEL1.md` (approximated / missing tables, each with its rule row):

- **Guards and combat** (rooms 3 and 21) are not implemented (P5). Until then
  the sword is not needed: the shortest win is 20 actions through rooms
  1, 2, 3, 9.
- Whole-block movement with fixed jump landings (3 / 5 blocks, R-D01); no
  ledge grab mid-jump or mid-fall; no running momentum or skids.
- Fall damage by rows fallen (R-D03), constant fall speed (R-D16), hang
  drop one row less (R-D17).
- A loose floor lands instantly on the first support below (R-D14); landing
  wiggles not shown (R-D30); the move departure frames are our choice
  (R-D33).
- Spike trigger range (R-D19), drop-plate slam speed, gate bar height
  (R-A04 `assumed`), sword pickup 12 frames instead of 22 (R-D28), entry
  played inside `reset` (R-D29).
- A gate closing on a kid inside its cell is not modeled.
- Sword and skeleton drawn as code shapes until the art milestone (D4).
- No observed play of an original build: nothing is labeled `observed`.

## Independent review report

The `rules-reviewer` report on session 08's work, whose findings this
session resolves, is **not in this repository**: none under `docs/reviews/`
or elsewhere in the project, and none found in nearby folders. This session
worked from the student's summary of it. To make check 3d inspectable, the
student should save that report as `docs/reviews/REVIEW-session08-level1.md`
(the agent did not reconstruct or paraphrase it into a review file).

## Not done

- P5 (combat), new art, any push or PR #57 sync: not started, by instruction.
- No `/game-rules-audit` run: `interface.py`, `observation.py` and
  `runner.py` were not changed this session.
- No observed play of an original build; the SDLPoP checklist in
  `docs/LEVEL1.md` now includes the departure frames.
