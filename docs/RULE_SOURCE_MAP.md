# Rule / Source Map

Every gameplay rule in this reconstruction has one evidence label and a
locator. Labels follow the assignment (`docs/MIDTERM_GUIDELINES.md`,
"Rules and evidence"):

| Label | Meaning here |
| --- | --- |
| `code` | Verified by reading the original 6502 source or decoding the original level files. Locator = file:line in the reference repo. |
| `manual` | Documented in original materials (Broderbund manual, Mechner's 1989 technical doc `popsource.pdf`). Locator = document + page. |
| `observed` | Verified by playing an original build. Locator = build, level, room, date, and recording/notes link. |
| `assumed` | An unverified inference about the original. Must name what would verify it. |
| `design` | Our intentional adaptation or new rule. Locator = `docs/GAME_SPEC.md` section + rationale. |

**Reference:** `https://github.com/historicalsource/princeofpersia` at
commit `2b4ddb5377f905840bf64f32e2f543a79f434222`. Paths below are relative
to `01 POP Source/` unless stated. Line numbers were read on 2026-10-26.

**Status of other evidence:** no `manual` source has been consulted yet;
no `observed` play of an original build has been recorded yet. Rows that
need those are marked `assumed` until the evidence exists. Do not promote a
label without adding the new locator.

**Implementation column:** `file:function` and the test that checks the
rule. Empty means not implemented (out of scope or deferred).

## Level structure and data

| ID | Rule | Label | Locator | Impl / test |
| --- | --- | --- | --- | --- |
| R-C01 | A level is 24 rooms; each room is 30 tiles = 3 rows × 10 columns. | `code` | `Source/EQ.S:258-265` (`BLUETYPE ds 24*30`); level files are 2304 bytes, consistent with the layout || `pop/physics.py` `COLS, ROWS`; `pop/situations.py` asserts 3×10 |
| R-C02 | Each room stores 4 neighbor links (left, right, up, down); 0 = none. | `code` | `Source/EQ.S:264` (`MAP ds 24*4`); decoded from `Levels/LEVEL1` || `pop/physics.py:Geometry.norm`; `test_rules.py::test_fall_damage_by_rows` |
| R-C03 | Tile ids 0–29: space, floor, spikes, posts (pillar), gate, dpressplate, pressplate, panelwif, pillarbottom, pillartop, flask, loose, panelwof, mirror, rubble, upressplate, exit, exit2, slicer, torch, block (wall), bones, sword, window, window2, archbot, archtop1–4. | `code` | `Source/BGDATA.S:6-35` || `pop/tiles.py` (our symbols for these kinds) |
| R-C04 | A tile byte's low 5 bits are the id; bit 5 marks a "required" floor piece; bits 6–7 are a variant. A second "spec" byte per tile holds object state. | `code` | `Source/EQ.S:484-486` (`secmask`, `reqmask`, `idmask`); `Source/MOVER.S:394-397` | |
| R-C05 | A plate's spec byte indexes the link table; each link entry gives a target room (5 bits across LINKLOC/LINKMAP), target block (0–29), a last-entry flag, and a 5-bit plate timer. | `code` | `Source/MOVER.S:1543-1580` (`gettimer`, `getloc`, `getlastflag`, `getscrn`) | |
| R-C06 | Kid start room, block, and facing come from the level's INFO block; guard start block/facing/program per room follow it. | `code` | `Source/EQ.S:272-284`; decoded: Level 1 start = room 1, block 0, face −1 (left) | |
| R-C07 | Block pitch is 14 screen units horizontally; 3 rows per room. | `code` | `Source/TABLES.S:143-155` (`BlockEdge`, step 14); `Source/TABLES.S:39-42` || `pop/physics.py` `RUN` (block = unit of movement) |

## Movement, gravity, landing

| ID | Rule | Label | Locator | Impl / test |
| --- | --- | --- | --- | --- |
| R-C10 | Landing speed below `OofVelocity` (22) = soft landing; below `DeathVelocity` (33) = medium landing, kid loses 1 HP; otherwise hard landing, fatal (strength −100). | `code` | `Source/CTRL.S:42-43`, `Source/CTRL.S:184-219` || `pop/engine.py:Game._land`; `test_rules.py::test_fall_damage_by_rows`, `::test_one_row_fall_is_safe` |
| R-C11 | Guards cannot survive a medium (two-story) landing; the shadow always lands softly. | `code` | `Source/CTRL.S:202-207` | |
| R-C12 | A falling or jumping kid can grab a ledge edge when vertical speed ≤ `grabspeed` (32) and within reach. | `code` | `Source/CTRL.S:45-47`, `Source/CTRL.S:245-295` || `pop/engine.py:Game._up` (climb only, no mid-air grab); `test_rules.py::test_climb_up_needs_open_space_above_and_ledge_ahead` |
| R-A01 | The original simulation runs at about 12 frames per second. | `assumed` | Not found in source yet. Verify via `popsource.pdf` or timing an original build. | |
| R-C26 | Running speed: the run cycle moves 26 units per 8 frames (≈ one 14-unit block per 4 frames). | `code` | `Source/SEQTABLE.S:168-177` (`runcyc1`–`runcyc8`, chx 5+1+2+4+5+2+3+4) || `pop/physics.py` `RUN = 4`; `test_rules.py::test_run_moves_one_block_in_four_frames` |
| R-C27 | Standing jump moves 41 units (≈ 2.9 blocks); running jump moves 67 units (≈ 4.8 blocks), of which ≈ 26 are on the ground before take-off. We round to 3 and 5 blocks (R-D01). | `code` | `Source/SEQTABLE.S:442-464` (`standjump` chx sum), `Source/SEQTABLE.S:469-482` (`runjump` chx sum) || `pop/physics.py` `JUMP_SPAN`, `RUN_JUMP_SPAN`; `test_rules.py::test_standing_jump_lands_three_blocks_ahead`, `::test_running_jump_lands_five_blocks_ahead` |
| R-C28 | A gate bars a character while `gatepos/4 + gatemargin(6) < image height`. | `code` | `Source/COLL.S:62`, `Source/COLL.S:1371-1381` (`gatebarr?`) || `pop/mechanics.py` `GATE_BARS_BELOW`; `test_rules.py::test_gate_bars_below_pass_height`, `::test_closed_gate_bars` |
| R-A04 | The kid's standing image height is about 40 units, so a gate bars him below position 136 (≈ 72 % open). | `assumed` | Height not looked up. Verify from the kid's image table (`Images/IMG.CHTAB1`) or observed play. | |

## Traps and gadgets

| ID | Rule | Label | Locator | Impl / test |
| --- | --- | --- | --- | --- |
| R-C08 | Gate position runs 0 (`gminval`) to 188 (`gmaxval`); it rises 4 per cycle, holds at the top for 50 cycles (`gatetimer` = gmaxval+50, counted down to gmaxval), then lowers 1 per cycle; a drop plate lowers it fast with the accelerating `gatevel` table. Exits open 4 per cycle (`exitinc`). | `code` | `Source/MOVER.S:56-67`, `Source/MOVER.S:89-91` (`gateinc db -1,4,4`, `exitinc = 4`), `Source/MOVER.S:845-885`; `Source/BGDATA.S:194-195` || `pop/mechanics.py:Gate`; `test_rules.py::test_gate_timing_follows_original_constants`, `::test_drop_plate_slams_gate` |
| R-C09 | Raise plate (`upressplate`, id 15) raises linked gates and opens linked exits; drop plate (`pressplate`, id 6) lowers linked gates; rubble on a plate jams a gate open; an exit only opens, never closes; plate timer `pptimer` = 5 cycles; a permanently-down plate has timer 31. | `code` | `Source/MOVER.S:425-475` (`PUSHPP`), `Source/MOVER.S:503-555` (`trigger`, `trigobj`), `Source/MOVER.S:562-615` (`openexit`, `triggate`) || `pop/mechanics.py:Mechanics._press`; `test_rules.py::test_closed_exit_does_not_win_and_open_exit_does`, `::test_exit_never_closes_once_opened` |
| R-C13 | Spikes impale a kid who runs onto them while sprung, or lands from a running/standing jump on them while lethal; standing and careful-step positions (CharPosn < 7) are not impaled. | `code` | `Source/CTRL.S:2016-2052` (`CHECKIMPALE`); landing case `Source/CTRL.S:167-182` || `pop/engine.py:Game._enter`, `_land`; `test_rules.py::test_running_onto_spikes_kills`, `::test_careful_steps_across_spikes_are_safe`, `::test_jump_landing_on_spikes_kills`, `::test_falling_onto_spikes_kills` |
| R-C14 | Loose floor: wiggles for 4 frames, detaches at frame `Ffalling` (10), falls with accel 3 to terminal velocity 29, crumbles; can crush a character (distance 30). Required floor pieces never break. | `code` | `Source/MOVER.S:69-80`, `Source/MOVER.S:389-412` (`BREAKLOOSE`); `Source/BGDATA.S:149` || `pop/mechanics.py` `LOOSE_DELAY`, `_drop_loose`; `test_rules.py::test_loose_floor_falls_ten_frames_after_stepping_on`, `::test_falling_loose_floor_hurts_kid_below` |
| R-C15 | Spikes spring, stay out `spiketimer` (15) cycles, then retract; extended at state ≥ `spikeExt` (5), retracting from `spikeRet` (9). | `code` | `Source/MOVER.S:62`, `Source/MOVER.S:365-375` (`GETSPIKES`), `Source/BGDATA.S:121-122` || `pop/mechanics.py` `SPIKE_HOLD`; `test_rules.py::test_spikes_spring_when_near_and_retract_later` |
| R-C16 | Potion effects by type: 1 recharge 1 HP, 2 boost max HP, 3 weightless for 200 cycles, 4 invert screen, 5 lose 1 HP. Type read as `spec >> 5`. | `code` | `Source/MISC.S:251-345` (`POTIONEFFECT`); `Source/CTRL.S:2146-2151` || type 1 only: `pop/engine.py:Game._down`; `test_rules.py::test_potion_heals_one_up_to_max` |
| R-A03 | Levels 1–13 store potion spec values 1–5 unshifted, while `LEVEL14` stores them shifted (32, 64, 160). We read unshifted values directly as the type. | `assumed` | Decoded from `Levels/LEVEL1`–`LEVEL14`. Verify by finding a load-time conversion in `Source/UNPACK.S`/`Source/MASTER.S`, or by observed play (Level 1 potions heal). | |
| R-C17 | Pressing up in front of an open exit climbs the stairs and ends the level. | `code` | `Source/CTRL.S:1150-1168`, `Source/CTRL.S:1247-1260` (`Stairs`) || `pop/engine.py:Game._up`; `test_situations.py::test_scripted_route_wins_within_limits` |
| R-C18 | Slicers cycle with `slicetimer` = 15 cycles between slices. | `code` | `Source/MOVER.S:65`; `Source/BGDATA.S:128-131` | |

## Kid, sword, guards, timer

Rows R-C20–R-C23 and R-C25 are research for the original game. Sword, guards, combat and level scripts are **not implemented** in this midterm (scope decision 2026-10-26); they stay here as evidence for the exclusions in `docs/GAME_SPEC.md` §1.

| ID | Rule | Label | Locator | Impl / test |
| --- | --- | --- | --- | --- |
| R-C19 | The kid starts the game with 3 hit points. | `code` | `Source/TOPCTRL.S:65` (`initmaxstr = 3`), `Source/TOPCTRL.S:161` || `pop/engine.py:Kid.hp` |
| R-C20 | Level 1 starts without the sword. | `code` | `Source/TOPCTRL.S:334` | |
| R-C21 | Crouching on the sword picks it up (`gotsword` = 1); on a potion, drinks it. | `code` | `Source/CTRL.S:2143-2160`, `Source/MISC.S:261-275` | |
| R-C22 | Guard base strength by level: 4,3,3,3,3,4,5 (levels 0–6) and 4,4,5,5,5,4,6 (levels 7–13). | `code` | `Source/AUTO.S:128-133` | |
| R-C23 | Guard behavior per program (0–11): strike, restrike, block, impaired-block, advance probabilities (×255) and refractory timer. Level 1 guards use program 0 (strike 75, block 0, advance 255). | `code` | `Source/AUTO.S:97-125`; program ids decoded from `Levels/LEVEL1` INFO | |
| R-C24 | The game has a 60-minute limit; when it reaches zero before level 13 the player loses; the timer stops on level 14 or after Jaffar dies. | `code` | `Source/SUBS.S:88-89` (`t = 60 ;game time limit`), `Source/TOPCTRL.S:577-596` || `pop/physics.py` `GAME_FRAMES`; `test_rules.py::test_clock_runs_out` |
| R-C25 | Level-specific scripts: L4 mirror, L5 thief steals potion, L6 falling off screen 1 goes to the next level, L8 mouse, L12 phantom bridge and leaving screen 23 goes to level 13, L13 Jaffar theme, L14 screen 5 wins. | `code` | `Source/AUTO.S:246-320`, `Source/AUTO.S:1128`, `Source/AUTO.S:1563-1637`; `Source/TOPCTRL.S:532-570`, `Source/TOPCTRL.S:1052`, `Source/TOPCTRL.S:1661`; `Source/CTRL.S:326` | |

## Design adaptations (our rules)

Each row names the alternative it beat (rubric 4a). Section numbers refer to
`docs/GAME_SPEC.md`.

| ID | Rule | Label | Rationale and alternative rejected |
| --- | --- | --- | --- |
| R-D01 | The kid is always on a whole block between actions; moves take a fixed number of frames; jumps land a fixed number of blocks ahead (standing 3, running 5, rounded from R-C27). | `design` | §3–4. A frame-exact port of `SEQTABLE.S`/`FRAMEDEF.S` would amount to porting the assembly and makes positions ambiguous for agents. Rejected: sub-block continuous positions. |
| R-D02 | Placeholder geometric art; no original images or sound. | `design` | §1. No publication rights for the original assets. Rejected: extracted sprites. |
| R-D03 | Fall damage by rows fallen: 1 safe, 2 = −1 HP, 3+ death. Approximates the landing-speed classes of R-C10. | `design` | §3. Same three outcome classes without a velocity model. Rejected: simulating `CharYVel`. |
| R-D04 | A cell is supported if its tile has a floor or the cell below is a wall. | `design` | §2. Original collision uses per-tile edge tables. Rejected: per-pixel floor heights. |
| R-D05 | Agents act through macro actions of at most 12 frames; the frames used are logged per step. | `design` | §4. The assignment allows a fixed-step wrapper; a model call per frame is unaffordable. Rejected: a frame-count parameter (4/8/12) on every action, which multiplies the action space. |
| R-D06 | `legal_actions` depends only on posture. | `design` | §4. A context-sensitive list (e.g., `UP` only under a ledge) would reveal geometry and hint at solutions. Rejected: listing only actions that would succeed. |
| R-D07 | Human keys map to the same macro actions and the same engine step. | `design` | §9. One rule set for both. Rejected: separate real-time human physics. |
| R-D12 | Invalid actions cost no game time; 5 in a row end the episode (`invalid_limit`). | `design` | §4, §7. Prevents unbounded loops without charging game time for one formatting error. Rejected: treating invalid as `WAIT`, which hides errors. |
| R-D13 | Playable rooms are independently authored, informed by the original Level 1's sequence (drop-in start, pits, loose floors, spikes, plate-opened gate, exit opened by a plate on an upper-left ledge as in decoded room 9). | `design` | §1. Publication rights for original level data are unclear (student decision 2026-10-26). Rejected: committing decoded `LEVEL1`. |
| R-D14 | Only stepping or landing on a loose floor starts it; no shaking from nearby landings; the falling floor lands instantly on the first supported cell below. | `design` | §5. Keeps R-C14's 10-frame delay without simulating a falling object. Rejected: a falling-object physics model. |
| R-D15 | A missing room link is a wall at the sides, rock above, and a bottomless (fatal) drop below. | `design` | §2. The original treats screen 0 as solid; a bottomless drop gives pits a clear outcome. Rejected: wrapping or blocking the bottom edge. |
| R-D16 | Falling takes 4 frames per row. | `design` | §3. Original fall speed accelerates (R-C10 velocities); a constant keeps timing predictable. Rejected: an acceleration curve. |
| R-D17 | Climbing down to hang and then dropping counts one row fewer for damage. | `design` | §3. In the original a hanging drop starts lower and lands slower. The one-row reduction is our approximation and is not verified. Rejected: no hang (removes a safe-descent decision). |
| R-D18 | Raise and drop plates are shown as different symbols; their link targets are hidden. | `design` | §8. The original draws plates as tiles a player learns to read; showing the kind but not the target matches what a human learns by playing. Rejected: hiding plate kind (forces blind trial and error). |
| R-D19 | Spikes spring when the kid is on the same row within one block and retract 15 frames after he leaves that range. | `design` | §5. Approximates R-C15's trigger without the original's proximity code. Rejected: spikes always out. |
| R-D20 | Directional actions while facing the other way only turn (4 frames). | `design` | §4. Matches the original's turn-on-reverse. Rejected: turning and moving in one action. |
| R-D21 | Episode action/call/timeout limits are separate from the 60-minute game clock. | `design` | §7. The assignment requires runner-enforced limits independent of game rules. |
