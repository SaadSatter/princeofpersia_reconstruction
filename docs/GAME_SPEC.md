# Game Specification — Prince of Persia (1989), Level 1 Reconstruction

Status: **approved scope, Phase 3** (student decisions of 2026-10-26).
Evidence for each rule: `docs/RULE_SOURCE_MAP.md` (ids `R-xx`).
Evaluation scenarios: `docs/EVALUATION_SUITE.md` (frozen).

## 1. Scope statement

A bounded reconstruction of the **dungeon gameplay of Level 1** of the
Apple II *Prince of Persia* (1989): side-view rooms of 10×3 tiles, running,
careful steps, standing and running jumps, climbing, falling damage, loose
floors, spikes, pressure plates, timed gates, and an exit door opened by a
plate.

**This is not the complete original Level 1.** The original Level 1 has 23
rooms (decoded locally from `Levels/LEVEL1`), a sword, two guards, and four
potions. Our playable rooms are **independently authored layouts** informed
by the verified mechanics and by the original Level 1's room sequence
(start by dropping into the dungeon; loose floors and pits; spikes; a plate
that opens a gate; an exit opened by a plate on an upper-left ledge, as in
original room 9). The exact rooms are listed in `docs/EVALUATION_SUITE.md`.
A larger reconstruction toward all 23 rooms is a stretch goal, only after
the interface, baseline, model player, and CI work.

### Included
Movement (run, turn, careful step, standing jump, running jump, climb up,
climb down/hang, drop, crouch), gravity and fall damage, walls and room
edges, multi-room navigation, loose floors, spikes, raise plates, drop
plates, gates with the original timing, exit door, heal potion, 60-minute
game clock, restart.

### Excluded (with reasons)

| Excluded | Reason |
| --- | --- |
| Levels 2–14 | Student scope decision: Level 1 only. |
| The original 23-room Level 1 layout | Publication rights unclear; authored layouts instead (R-D13). |
| Sword pickup, guards, combat | Deferred until platforming and exit work (student decision). Actions `STRIKE`, `BLOCK`, `ADVANCE`, `RETREAT` are not implemented. |
| Ledge grab after a short jump or while falling | Needs the original's continuous motion; jumps land on fixed blocks (R-D01). |
| Jumping up to knock down a loose floor above | Not needed for the authored rooms; noted as an omission. |
| Loose-floor shaking when landing nearby | Simplified; only stepping on a loose floor triggers it (R-D14). |
| Original animation frames, art, sound | Not ported; placeholder shapes (R-D02). |
| Potions other than heal | Level 1 potions all have the same spec value (R-A03). |

## 2. World model

- A level is a set of rooms; each room is **10 columns × 3 rows** (R-C01),
  with links left/right/up/down (R-C02). A missing link is a wall at the
  side edges, solid rock above, and a bottomless drop below (R-D15).
- Row 0 is the top row. A tile at (row, col) is a cell; "standing on
  (r, c)" means standing on that cell's floor.
- Tiles (our map notation; ids follow `BGDATA.S` names, R-C03):

| Sym | Tile | Floor? | Blocks walking? |
| --- | --- | --- | --- |
| `.` | space | no | no |
| `_` | floor | yes | no |
| `#` | wall | — (solid) | yes |
| `^` | spikes | yes | no |
| `L` | loose floor | yes, until it falls | no |
| `G` | gate | yes | yes, while below the pass height |
| `u` | raise plate | yes | no |
| `p` | drop plate | yes | no |
| `E` `e` | exit (left/right half) | yes | no |
| `f` | potion (heal) | yes | no |
| `r` | rubble | yes | no |
| `P` `t` | pillar / torch (decoration) | yes | no |

- A cell is **supported** if its tile has a floor, or the cell directly
  below is a wall (R-D04).
- Plates link to gates or exits through a link table that players never see.

## 3. Time and kinematics

- **Frame:** the engine's fixed step. 12 frames = 1 second of game time
  (R-A01).
- **Position:** room, row, column, facing. Between actions the kid is always
  on a whole block (R-D01). Timers (gates, spikes, loose floors, plates)
  advance every frame, including during moves.
- **Move durations** (frames): run one block 4 (R-C26), careful step 8,
  turn 4, standing jump 12, running jump 12, climb up 12, climb down to hang
  6, climb up from hang 8, crouch 4, drink 8, exit stairs 12, wait 6.
- **Falling:** 4 frames per row (R-D16). Rows fallen = landing row − start
  row (across rooms). Landing: 1 row = no damage, 2 rows = −1 HP, 3+ rows =
  death (R-C10 via R-D03). Dropping from a hang counts one row fewer (R-D17).
  Falling off a room with no room below = death (`died:fall`).

## 4. Actions — exact semantics

Each action is a **macro** that runs at most 12 frames (one exception: a
fall started by the action continues up to 12 frames total; if still in
the air, posture becomes `falling` and the next action must be `WAIT`).
"Ahead" means column + facing. **Any directional action while facing the
other way only turns** (4 frames) — matches the original, where pressing
back turns the prince around.

| Action | Prerequisite (else effect) | Duration | Result |
| --- | --- | --- | --- |
| `WAIT` | — | 6 | Nothing; timers advance. While falling: continue falling. |
| `LEFT` / `RIGHT` | Facing that way; ahead not wall/barring gate/edge (else `bumped`, 2 frames) | 4 | Move one block ahead. If the new block is unsupported, fall. Entering sprung-or-springing spikes this way kills (`died:spikes`). |
| `STEP_LEFT` / `STEP_RIGHT` | Facing that way; ahead supported and not blocked (else `edge` / `bumped`, 2 frames) | 8 | Careful step one block. Never walks off an edge. Never impaled (R-C13). |
| `JUMP_LEFT` / `JUMP_RIGHT` | Facing that way | 12 | Standing jump: move up to 3 blocks ahead (R-C27). Stops before the first wall/barring gate in the path. Then land: unsupported → fall; spikes → `died:spikes`. |
| `RUN_JUMP_LEFT` / `RUN_JUMP_RIGHT` | Facing that way; block 1 ahead supported and not blocked (else behaves as `LEFT`/`RIGHT`) | 12 | Run up one block, then jump to 5 blocks ahead of the start (clears gaps of up to 3) (R-C27). Same blocking and landing rules as a jump. |
| `UP` | — | 12 or 8 | In order: (1) standing on an open exit tile → climb stairs → **win**; (2) hanging → climb back up; (3) cell above is open (no floor, not wall) and the cell above-ahead is supported → climb onto it (R-C12); (4) otherwise jump in place (`none`, 8 frames). |
| `DOWN` | — | 4–8 | In order: (1) hanging → let go and fall; (2) on a potion → drink (heal 1, up to max) (R-C16); (3) ahead is open with no floor → climb down and hang from this ledge; (4) otherwise crouch (`none`). |

Legal actions (R-D06) depend **only on posture**:

| Posture | Legal actions |
| --- | --- |
| `standing` | `WAIT LEFT RIGHT STEP_LEFT STEP_RIGHT JUMP_LEFT JUMP_RIGHT RUN_JUMP_LEFT RUN_JUMP_RIGHT UP DOWN` |
| `hanging` | `WAIT UP DOWN` |
| `falling` | `WAIT` |
| terminal (won, dead, limit) | none |

**Validation:** an action that is not a string, not in the vocabulary, or
not legal for the posture is **invalid**: rejected, counted, no state
change, no frames pass (R-D12). Five consecutive invalid actions end the
episode (`invalid_limit`). A legal action that does nothing reports
`effect: "none"` (or `bumped` / `edge`) and still costs its frames.

## 5. Mechanics

| Mechanic | Behavior | Rules |
| --- | --- | --- |
| Raise plate `u` | Pressed while the kid stands on it. Each frame pressed: linked gates rise / linked exits open, and the gate's hold timer restarts. Pops up 5 frames after the kid leaves. | R-C05, R-C09 |
| Drop plate `p` | Pressed: linked gates drop fast. | R-C09, R-C08 |
| Gate `G` | Position 0 (closed) to 188 (open). Rises 4/frame; at the top holds 50 frames; then lowers 1/frame. Drops fast when a drop plate is pressed. Bars the kid while `position/4 + 6 < 40`, i.e. below 136 (R-C28). | R-C08, R-C28 |
| Exit `E e` | Opens 4/frame up to 188 once triggered; never closes. Open (usable) at 188. | R-C09, R-C17 |
| Loose floor `L` | Kid stepping onto it starts it; 10 frames later it falls: the tile becomes space; the floor lands on the first supported cell below in the same column as rubble `r`; a kid there loses 1 HP (`died:crushed` at 0). A kid on it when it falls starts falling. | R-C14, R-D14 |
| Spikes `^` | Spring when the kid is on the same row within one block; stay sprung while he is near, then retract 15 frames later. Running or jumping onto them, or falling onto them, kills; careful steps never kill; standing among sprung spikes is safe. | R-C13, R-C15, R-D19 |
| Potion `f` | `DOWN` on it: heal 1 HP up to max; the potion is gone. | R-C16 |
| Clock | 60 minutes (43,200 frames). At 0 → `time_up`. | R-C24 |
| HP | Start 3 of 3. | R-C19 |

## 6. Authoritative state (engine only)

Situation id; rooms (tile grids, mutable); link table; gate positions and
hold timers; plate timers; exit positions; spike timers; loose-floor
timers; kid (room, row, col, facing, posture, hp, max_hp, hang flag);
frame counter; RNG (seeded, unused until combat); terminal flag and reason.

## 7. Episodes, outcomes, limits

- `reset(seed)` loads a situation from `docs/EVALUATION_SUITE.md`. The seed
  is recorded; **no current mechanic uses randomness**, so repeated trials
  of a situation differ only by player behavior.
- **Win:** `UP` on an open exit tile. Score 1. Otherwise score 0.
- **Terminal reasons:** `won`, `died:spikes`, `died:fall`, `died:crushed`,
  `time_up`, `step_limit`, `call_limit`, `invalid_limit`.
- **Runner limits:** max actions and max model calls per situation (suite
  file), per-call timeout 20 s, 5 consecutive invalid actions. Failed or
  timed-out calls count as calls and produce a `WAIT` labeled
  `source: "fallback"`.
- **Restart:** `reset(seed)` (runner); `R` key (human).

## 8. Observation (what a human sees on screen)

Current room only: its 3 rows as symbol strings (table above), dynamic
state (gate open %, whether each gate bars, spikes sprung, loose floors
shaking, plates pressed, exit open %), which edges lead on, an opaque room
label; the kid's row, column, facing, posture, HP/max; minutes left;
actions and calls left; the last action's result; the task text.

Never visible: other rooms, plate→gate links, internal timer counts, the
level data, solution routes, and the evaluator's records. Plate kinds
(raise vs drop) **are** shown (R-D18).

## 9. Human frontend

`play.py` (Pygame, placeholder shapes) maps keys to the same actions:
←/→ run or turn, Shift+←/→ careful step, ↑ up, ↓ down, ↑+←/→ standing
jump, Shift+↑+←/→ running jump, Space wait, R restart, Esc quit. Each key
press runs the same engine macro, shown at 12 frames/s.

## 10. Adaptations

Every simplification above is a `design` row in `docs/RULE_SOURCE_MAP.md`
(R-D01–R-D21) with its rationale and the alternative it beat.
