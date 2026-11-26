---
task: T27
from: tech-lead
to: qa
consumed: docs/final/orchestration/tasks/T27.md @ 2d59733; decision #107
base: dfe2d90 (orch/reviewed)
status: done (feasibility study only; no code, tests or design docs changed)
---

# T27 feasibility: one continuous side-scrolling arena

Study only. Evidence is read from the code at dfe2d90. Nothing was run
beyond reading and grep, so no suite result applies (no code changed).
Effort and schedule figures are my estimates, not measurements.

## 1. What the arena is now

- `pop/arena.py` (OQ-4, GDD 5.2): six rooms, each 3 rows x 10 columns,
  in a 3x2 grid. `LINKS` gives (left, right, up, down) per room. Rooms
  1-2-3 are the top row, 4-6-5 the bottom row. Room 1 drops to 4, room 2
  to 6 (the shaft), room 3 to 5; left/right links join 1-2-3 and 4-6-5.
  Together these form a loop. Starts (`STARTS`, rooms 1 and 3), guard
  posts (`GUARD_POSTS`, rooms 4 and 5), `PLATE_LINKS` and `GATES_OPEN`
  (rooms 2 and 6) are all (room, row, col) cells.
- The whole engine addresses cells as `(room, row, col)` (`pop/engine.py`
  `Kid.cell`, `pop/guards.py`, `pop/versus.py` `Geometry`). A "doorway" is
  a step off column 0 or 9 into `LINKS[room]` left/right.
- One connected level would replace the room graph, the up/down links,
  the shaft and the loop, and would move starts, guard posts and plate
  links to level-wide columns.

## 2. Hidden information

- Today a seat sees only its own room: `pop/observation.py` filters
  everything by `cell[0] == room`; `pop/versus.py` seat observation
  (lines ~1147-1205) drops rivals, guards, swords, rigs and guard
  meters not in `room`. Up/down links are deliberately hidden (`edges`
  has left/right only; `floor_below_in_room`, line 466). Disguise
  (R-V25 masking), R-V23 settle and trap ownership all lean on "not in
  my room, so not seen".
- Replacement: a window of N columns (and optionally rows) around the
  seat's own rival, e.g. 10 columns so the screen matches today. The
  rule "visible iff in the window" replaces "visible iff same room". The
  window must depend only on the seat's own position, and the same
  predicate must be used by the observation, `legal_actions`,
  `_motion_view`, the baseline and the renderer, or a leak appears at
  the window edge.
- New leak surface: with a sliding window two rivals are mutually
  visible whenever within N columns, not only in the same room. R-V25
  masking, guard suspicion range, `_motion_view` (`to: None` for ends out
  of view), rigged-tile masking and `_settles_in` must be restated
  against the window. Tests encoding the room rule include
  tests/test_disguise.py, test_traps_leaks.py, test_online_boundary.py
  and the gate/T18/T22/T24/T25 boundary tests (79 of 157 test files
  mention "room"; I did not audit how many assert the room rule).
- Server: no new category of data, but message shape changes (a tile
  window and its offset, not a room). It must still send only that
  seat's window, never the level width or full layout.
- Needs Saad's approval first: window shape and size (observation
  schema, CQ-1).

## 3. Engine

- Display-only is possible only for a camera over rooms that already
  exist. For (b) and (c) the room-based code is an engine change: room
  transitions in `pop/engine.py` (`k.room` via `LINKS`), `Geometry`
  (grid keyed by room), `pop/guards.py` (patrol and sight by room and
  row), `Duel._settle_arrivals` and `_settle` (R-V23: defined by
  arriving in an occupied room), the `_view`/claim logic (line ~708),
  swords and flying weapons keyed by room, and `situations`/`levelfile`
  (the frozen midterm suite and original Level 1 share `Geometry`, so
  room addressing cannot be removed; a level-wide layer would have to
  wrap it).
- Cheapest engine route for (b): keep `(room, row, col)` internally and
  derive `gx = x_offset(room) + col` for rooms placed on a line, then
  define visibility over `gx`. That works only for rooms in a line; the
  current arena is a 3x2 loop with vertical shafts, so (b) first needs a
  layout decision (section 5).

## 4. AI

- `agents/rl/encoder.py` uses room tiles, `edges`, `rooms_seen`,
  `in_room` and `ROOM_CAP`. A different window changes the input size,
  so trained PPO weights become invalid: retrain (the full run needs
  Saad's approval) and re-evaluate.
- `agents/macros.py` (`FieldView`, `_note_room`, `up_good`,
  `BLIND_DOWN_COST`/`BLIND_UP_COST`) and `agents/versus_baseline.py`
  rely on `obs["room"]` labels and room exits (FLEE the room, SEARCH
  avoiding a fled room). They need re-deriving for a window.
- `evaluation/` scenarios, the held-out set H6 and its ledger are keyed
  to the six-room arena and recorded results. A new level invalidates
  the T19/T24 comparisons and the held-out ledger: rerun and re-seal.
  The frozen midterm suite is unaffected if left on the old geometry.

## 5. Options

### (a) Display-only camera smoothing, rooms unchanged
- Rows: none (render and web only; no engine, observation or rule rows).
- Tests: frontend tests (`tests/test_frontend.py`, web UI tests), plus a
  check that the camera uses only the seat's own observation.
- Hidden information: unchanged, provided the camera never shows the
  neighbouring room before the seat has entered it (scroll after the
  transition, not before).
- AI and evaluation: untouched. No retrain.
- Schedule risk: low. About 1 to 2 days for pygame (`render/draw.py`)
  and web (`web/draw.js`) (estimate).
- Lost: not a truly continuous world; rooms still read as separate
  screens with a softened cut. May not give the feel requested.

### (b) Scrolling view over the same rooms joined end to end
- Needs a layout change first: the loop and shafts do not line up in a
  row. Either flatten to a six-room strip (loses the loop and vertical
  shafts; mirror starts and reachability change) or scroll in two axes.
  Either way the arena rows change (RULE_SOURCE_MAP design row, GDD 5.2
  and the "own screen: current room" line in section 6), and Saad must
  approve the changed arena (OQ-4) and the window (CQ-1).
- Rows and tests: observation schema (window); every "same room" rule
  restated as "in window" (R-V23, R-V25, guard sight, motion view); new
  leak tests at the window edge; reachability (`tools/check_arena.py`,
  `tests/test_arena.py`).
- AI: new encoder shape, full PPO retrain, rerun scenarios and the
  held-out set (new seal), re-baseline the scripted rival.
- Schedule risk: high. Gold build recording is Sat 5 Dec and G4 is Mon
  7 Dec (PROJECT_PLAN); today is 26 Nov, so about 9 days. Engine and
  boundary re-verification through all gates plus a retrain would likely
  consume most of that and leave little margin (estimate).
- Lost: room-keyed evidence (T19/T24 comparisons, H6 ledger), the
  trained policy, current reachability and QA coverage.

### (c) New continuous level
- All of (b), plus new layout design (art, traps, guard routes, mirror
  fairness), a width and scroll model in `Geometry`, guards and gates,
  and a new level data format.
- Schedule risk: very high; not credible before 5 Dec with the required
  gates.
- Lost: everything in (b) plus the six-room design decided in OQ-4.

## Recommendation

Choose (a). It adds no rule rows, keeps the knowledge boundary, the PPO
policy and the held-out evidence valid, and fits the schedule. If Saad
wants true continuity, treat (b) as a post-gold task with its own brief,
a CQ-1/OQ-4 decision (window shape and size) and a retrain budget; I
would not start it before the 5 Dec recording. (c) is not feasible in
the time left. Saad decides.

Caution for (a): the camera must not reveal the neighbouring room early,
or it creates the same leak a window would.

## Requested next action

Commit to review: see the tip of task/T27 (report only)
What changed: one report file; no behaviour change.
How to check it: read the cited locators in `pop/arena.py`,
`pop/observation.py`, `pop/versus.py` (lines ~149-168, 466, 708-715,
852-960, 1132-1205), `agents/rl/encoder.py`, `agents/macros.py`.
What I am unsure about: effort figures are estimates; how many tests
assert the room rule (79 of 157 files merely mention "room"); I did not
prototype a camera, so (a)'s 1 to 2 days is a judgement.
Touches the knowledge boundary or AI seat: no (study only). Gate 2 does
not apply to this report; it would for any build of (b) or (c).
