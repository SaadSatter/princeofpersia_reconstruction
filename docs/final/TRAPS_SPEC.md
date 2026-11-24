# Shadow Masque traps spec: the RIG action (addendum to VERSUS_SPEC)

Status: **PROPOSAL for Saad's approval (T06a).** Nothing here is implemented or
decided. Every number and choice below is a *proposal*; where the choice is a
real design call, two options are given and one is recommended. Decisions in
force it builds on: GDD 2026-11-15 (two trap types, loose floor and gate plate,
4 traps per rival, traps hurt everyone including the owner), DECISIONS #2
(traps are a G2 target; loose floor first, gate plate second), G1 knowledge
boundary ("a rigged tile looks normal unless you rigged it"). Rule ids start at
R-V27 (R-V26 is the TAKE rule). OQ-6 is answered in Section 4.

## 1. The RIG action

`RIG` is a new move in the VERSUS_SPEC Section 2.3 vocabulary, submitted as
the macro `RIG_TRAP` (Section 7). The rival kneels for a short time, then the
target cell is rigged.

| Question | Proposal |
| --- | --- |
| Target cell | **Option A (recommended):** the floor cell directly ahead (facing), same row. The owner never stands on its own trap while rigging. **Option B:** the cell under the rival's feet; it must step off first |
| Legal on | A cell whose tile is plain `FLOOR` (`_`) with support, in the rival's current room. Not on `L`, plates, gates, spikes, holes, rubble, doorway/edge cells, a cell holding a body or a claimed landing cell. Loose rig also needs a floor below that the fall can reach (the existing `_drop_loose` landing); plate rig needs a gate in the same room (Section 3) |
| Legal when | Standing, free (no move in progress), not knocked down, not hanging, `traps_left > 0`, and the cell is not already rigged **by this seat**. Sword drawn or sheathed: either; it stays as it was |
| Duration | 12 frames kneeling, as TAKE (R-V17). A hit or knockdown during the kneel cancels the rig and **still spends the trap** *(proposal; stops free cancel-probing)* |
| Disguise | Does **not** break it. **Option 1 (recommended):** while a guard sees the disguised rival, the kneel counts as suspicious: +3 suspicion per frame *(proposal, between standing-still and running)*. **Option 2:** `RIG_TRAP` is not legal while any guard sees you (simplest, but legality then depends on guard positions the seat can see anyway, so no leak) |
| Visible to others | A rival in the same room sees a kneeling figure (a crouch pose, same as TAKE and a sweep start). It does not see which cell, or whether a trap resulted |

Legality may depend only on the seat's own state and what it can see. It must
never depend on the other seat's traps (Section 6, "double rig").

## 2. Double rig (needed for the knowledge boundary)

If `RIG_TRAP` were refused on a cell the rival had rigged, the refusal would
tell the seat "that is rigged". So: a cell may carry **one rig per seat**. If
both seats rig the same cell, both succeed, both spend a trap, each sees its
own marker, and the first body to spring it consumes both. Nothing the other
seat does changes what this seat is told.

## 3. The two trap types

| Type | Rig on | When sprung | Effect | Harm |
| --- | --- | --- | --- | --- |
| Loose floor | A `FLOOR` cell | A body **steps onto** the cell (arrives, or lands on it). Standing on it while it is rigged does not trigger | After the existing `LOOSE_DELAY` (10 frames) of shaking, the tile falls as an environmental loose floor does (`Mechanics.touch_loose`, `_drop_loose`); the body falls with it | The existing damaging-fall rule (R-V01, 1 heart); a guard that falls is downed (R-V16) |
| Gate plate | A `FLOOR` cell in a room that has a gate | A body steps onto the cell | The room's gate slams (the existing drop-plate slam, `GATE_FAST`) | **Option A (recommended):** the slam costs **1 heart** to a body in the gate's cell (a guard there is downed), otherwise it only blocks. **Option B:** the slam only blocks and splits the room; the harm comes from the rival being cut off and hit by guards (weaker; then G1's "trap costs 1 heart" holds for loose floor only) |

Only two rooms have a gate (Gatehouse, Undercroft), each with one gate, so
plate rigs are limited to those rooms. A rig of either type is invisible
until sprung; the shaking tile, falling tile and moving gate that follow are
existing, room-wide visible events.

**Who springs it.** Any body: either rival, or a guard walking its patrol
(R-V13). A guard on a loose rig is downed; a guard on a plate rig slams the
gate. The rival that rigged it gets no immunity and no warning (G1: traps
"can harm either rival, including the trap owner").

**Counts.** 4 per rival, **shared across both types** *(recommended; one
`traps_left` number, simplest to display and test)*. Alternative: 2 of each
type. A sprung or consumed rig frees nothing back (Section 4).

## 4. One-shot or re-arm (OQ-6)

| Option | Behaviour |
| --- | --- |
| **A. One-shot (recommended; the DECISIONS #2 proposal)** | A rig is consumed when sprung. The 4 per rival are a lifetime budget; `traps_left` only goes down. A fallen loose floor is already permanent (the tile is gone), so one-shot is also the existing physics |
| B. Re-arm | A sprung gate plate re-arms after 120 frames (10 s) *(number proposed)*. Loose floor cannot re-arm without inventing a rebuilt tile. Costs a second rule and a timer in the observation |

## 5. What each seat observes

Today's `tiles`, `state.loose_shaking`, `state.plates_pressed` and `state.gates`
stay as they are and stay the same for both seats.

- `tiles` shows a rigged cell as a plain `_` to **every** seat, owner included.
  No new tile glyph is ever introduced.
- New field on `me`, present for both seats: `traps_left` (int, own budget).
- New top-level field, present for both seats: `my_traps`, a list of
  `{row, col, kind}` for **this seat's own** unsprung rigs **in the current
  room**, sorted. The other seat's observation has the same key with its own
  list; it never contains a cell the seat did not rig itself.
- `legal_actions` lists `RIG_TRAP` by the legality in Section 1 only. Same
  list shape for both seats.
- When a rig is sprung the cell leaves `my_traps`. A spring in the room is
  visible to everyone there (shaking, falling, gate), but nothing says who
  rigged it. A seat in another room sees nothing (existing room rule).
- `figures`, `motion` and `suspicion` are unchanged. No ownership, count of
  the other seat's traps, or trap positions outside the owner's own list.

## 6. Leak tests required (written failing first)

1. **Normal tile, field for field.** Seat A rigs cell X. Seat B's
   `observe("B")` equals the observation from a duel where X was never rigged,
   except for B's own `my_traps` and `traps_left` (which are B's, not A's).
   Check `tiles`, `state`, `figures`, `motion`, `edges`.
2. **Owner sees only its own.** A's `my_traps` has X; B's has no entry for X;
   after B rigs a different cell Y, A's still has only X.
3. **Legal actions identical.** B's `legal_actions` before and after A rigs
   X (B in the room, B not on X) are equal; and equal to a duel with no rig.
4. **Double rig.** With A's rig on X, B's `RIG_TRAP` toward X is listed and
   accepted exactly as on an unrigged cell; B's `traps_left` drops by one;
   no field B sees differs from the unrigged case.
5. **Spring does not name the owner.** After B steps on A's rig (and after a
   guard does), B's observation and `last_result` contain no seat id, owner
   or "trap" word; only the existing shaking/fall/gate motion.
6. **Server message.** The outgoing message for a seat equals `observe(seat)`
   (VERSUS_SPEC Section 6, leak test 3); a rig adds nothing to the other
   seat's message. The AI seat's prompt contains only its own `my_traps`.
7. **Owner can be hurt.** A rigs X, A later steps on X: A loses 1 heart (a
   no-immunity test, not a leak test, kept beside the others).
8. Baseline vs AI seat see the same `RIG_TRAP` interface (CLAUDE.md duty 5).

Plus behaviour tests per rule row below, and a determinism check (same seed
and inputs, same trace).

## 7. The macro `RIG_TRAP`

One macro, no parameters: the engine rigs the cell ahead (Option A). *Proposal:*
to keep CQ-1's vocabulary small, G2 ships `RIG_TRAP` as loose floor only; the
plate type arrives later either as an argument to `RIG_TRAP` or as a second
macro `RIG_GATE`, decided with CQ-1. The macro expands to the `RIG` input, which
holds for 12 frames. It is legal exactly as in Section 1 and nothing else.
The scripted rival uses the same macro, labelled as a baseline.

## 8. Rule rows to add (`design` label, failing test first)

| Id | Rule |
| --- | --- |
| R-V27 | `RIG`: legality, target cell, 12-frame kneel, cancel by hit, trap spent at start |
| R-V28 | Loose-floor rig: invisible, springs on a body stepping onto it, then the existing loose-floor fall |
| R-V29 | Gate-plate rig: invisible, springs on a body stepping onto it, slams the room's gate; slam harm per Section 3 |
| R-V30 | Anyone springs a rig: rival (owner included), guard; guard downed by a loose rig (R-V16) |
| R-V31 | Budget: 4 per rival, shared across types; a double rig on one cell is allowed (Section 2) |
| R-V32 | One-shot: a rig is consumed when sprung (OQ-6, Option A) |
| R-V33 | Rigging while disguised raises suspicion (Option 1) |
| R-V34 | Observation: `my_traps`, `traps_left`, tiles unchanged (Section 5); this row is the leak-test row |

## 9. Minimum for G2 versus later

| G2 (proposal) | Later (G3 or cut) |
| --- | --- |
| `RIG_TRAP` for **loose floor** only, cell ahead, one-shot, 4 per rival | Gate plate rig (second, per DECISIONS #2; GDD scope cut 3 allows one trap type) |
| Owner and guards springable, owner can be hurt | Plate slam harm option, re-arm (Option B of OQ-6) |
| `my_traps`, `traps_left`, leak tests 1 to 8 | HUD marker art for the owner's rigs |
| Scripted rival rigs one trap, same macro as the AI seat | Smarter rigging in the scripted rival |
| Disguise suspicion while kneeling (Option 1) | Tuning from playtest |

Unsure about: the plate type's room limit (only two gated rooms); the
`RIG_TRAP` macro shape for two types; whether a gate slam should hurt;
whether the kneel makes a rig-ing rival too easy to read.

## 10. Decisions Saad must make

1. **OQ-6:** one-shot (recommended) or re-arm after 120 frames?
2. Target cell: ahead (recommended) or under the feet?
3. Trap budget: 4 shared across types (recommended) or 2 + 2?
4. Disguised rigging: suspicion +3/frame (recommended) or illegal in a guard's sight?
5. Gate slam harm: 1 heart to a body in the gate cell (recommended) or block only?
6. Double rig allowed so the knowledge boundary holds (recommended; the alternative leaks)?
7. Kneel 12 frames and cancel-spends-the-trap (proposed numbers)?
8. Macro shape: one `RIG_TRAP` (loose first) now; second type via argument or `RIG_GATE` with CQ-1?
9. G2 minimum: loose floor only, gate plate in G3?
