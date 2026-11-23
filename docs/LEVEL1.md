# L1 — the original Level 1 (reconstruction status)

Status on 2026-10-26: phases P0–P4 done (session 08); post-review
stabilization done (session 10: movement resolution fix R-D33, review
findings, new verified route). All on the local branch
`level1-reconstruction`. **P5 (guards and combat) not started**, waiting for
the student's approval. Nothing from this work has been synced to course
PR #57.

## Student decisions (2026-10-26)

| # | Decision |
| --- | --- |
| D1 | The original level data stays outside Git. A maintainer fetches it from a pinned source, checked by SHA-256; the game reads it at run time. Not committed to either repository. |
| D2 | Simplified combat (sword pickup and the original guard encounter) as a separate final phase, P5. Keep the original's legitimate ways to avoid the guard where feasible. |
| D3 | Fix the S3 loose-floor climb crash first, with a regression test, and show that every committed trace replays identically. |
| D4 | Placeholders while building; before completion, bundle the needed original sword, guard and animation images in the private course PR only, with the manifest and provenance updated. |

## Setup and play

Working directory: the project folder.

```
uv run python tools/fetch_level1.py          # once: fetch + SHA-256 check into vendor/levels/ (git-ignored)
uv run python tools/fetch_level1.py --check  # verify, no network
uv sync --extra play
uv run python play.py L1                     # keyboard play; --placeholder for shapes
uv run python tools/solve_level1.py          # maintainers: find a route with the real engine
```

Without the file, `play.py L1` stops with these instructions, and every
other scenario works as before.

Sources (pinned in `pop/levels.py`):
- Apple II `LEVEL1`, historicalsource/princeofpersia `2b4ddb5`, 2304 bytes,
  SHA-256 `600205ef…cd316`. This is the file the game reads.
- DOS level 1, NagyD/SDLPoP `3c5add5` `data/LEVELS/res2001.bin`, 2305 bytes,
  SHA-256 `ae8dd778…dc06c`. Used only as a cross-check: its tiles, specs,
  links, start and guards are identical to the Apple II file (R-C32).

The historicalsource README grants no rights in Prince of Persia; this is
why the data is never committed (R-D13).

## What L1 is, and how it stays separate

- Built by `pop/levels.py:to_situation` from the file: 24 room slots, of
  which 21 are reachable (rooms 13 and 18 link only to each other; room 24
  is unlinked, R-C34). The exit is in room 9, the sword in room 15, and
  guards are recorded in rooms 3 and 21 (not placed yet).
- **Not in the evaluation suite.** `L1` is not in `pop.situations.SITUATIONS`,
  `evaluate.py` refuses it, and its runs never enter `EVALUATION.md` (R-D27).
- Level 1's extra rules are switched on per scenario (`Situation.rules`,
  R-D31), so S1–S3/H1–H3 behave exactly as when their results were recorded.
  Guard tests: `tests/test_frozen_suite.py` pins each frozen definition, its
  first observation and the model's system prompt (hashes from before any
  Level 1 code); `tests/test_trace_replay.py` replays all 16 committed traces
  step by step.
- **What players see.** Only `pop/observation.py`: the current room, as for
  every scenario. `tests/test_level1.py::test_observation_shows_only_the_current_room`
  checks this, and the audit (`docs/audits/AUDIT-2026-10-26-session08-level1.md`)
  confirmed that no other room's rows appear. One leak was found and fixed:
  hopping under a loose floor in the room above named the effect (audit
  finding 1).
- `tests/test_level1.py::test_no_original_level_file_is_tracked_by_git`
  fails if either pinned file is ever committed.

## Original Level 1 mechanics: implemented, approximated, missing

**Implemented as in the original** (evidence `code`; tests named in `docs/RULE_SOURCE_MAP.md`)

| Mechanic | Rule |
| --- | --- |
| Room layout, tile types, room links (including one-way links) | R-C01–R-C05, R-C32, R-C34 |
| Start in room 1, block 0, facing right; drop-in entry; the gate behind him slams shut | R-C06, R-C30 |
| A gate open at load (room 5) stays open until a plate acts on it | R-C29 |
| Raise and drop plates, including plates with two targets and plates acting on another room; any plate kind opens a linked exit (corrected in session 10) | R-C05, R-C09 |
| Gate timing (rise 4, hold 50, lower 1), exit opening 4 per cycle and never closing | R-C08, R-C09 |
| Exit in room 9, opened by the plate on the upper-left ledge; `UP` on the open exit wins | R-C17 |
| Loose floors break when stood on, landed on or hung from, and when hit from below by a hop | R-C14, R-C31 |
| Spikes in pits; landing or running onto sprung spikes kills | R-C13, R-C15 |
| Four potions, all heal +1 (stored type, shifted at load) | R-C16, R-A03 |
| Gate and loose-floor state set at load (gate spec 1 up, 2 down; loose floors reset) | R-C29 |
| "Required" loose floors never break (none in Level 1; the reader refuses one) | R-C35 |
| Sword pickup (`DOWN` on it) | R-C21 |
| 3 HP, 60-minute clock | R-C19, R-C24 |

**Approximated** (each a `design` row with its reason)

| Original | Ours | Row |
| --- | --- | --- |
| Continuous positions; jumps cover about 2.9 / 4.8 blocks | Whole blocks; jumps land exactly 3 / 5 blocks ahead | R-D01 |
| Landing speed decides damage | Rows fallen: 1 safe, 2 = −1 HP, 3+ death | R-D03 |
| Accelerating fall | 4 frames per row | R-D16 |
| A hanging drop starts lower | Counts one row less | R-D17 |
| A loose floor falls as an object | Lands instantly on the first support below, 10 frames after it is triggered | R-D14 |
| The floor under the feet is tested every frame of a move | Each move has a departure frame: a floor falling before it interrupts the move (he falls from where he stands); after it, he is in motion (run 2/4, step 4/8, standing jump 6/12, running jump at once, climb 4/12) | R-D33 |
| Landings wiggle nearby loose floors (cosmetic) | Not shown | R-D30 |
| Spike proximity trigger | Same row, within one block | R-D19 |
| Drop-plate gate slam (accelerating) | 63 per frame | R-C08 note |
| Gate bars below an image height of about 40 | Bars below position 136 | R-A04 (`assumed`) |
| Sword pickup takes 22 frames | 12 (macro cap) | R-D28 |
| The player watches the entry drop | It runs inside `reset`; the first `last_result` reports it | R-D29 |
| Sword and skeleton images | Drawn as shapes in code; pickup shows the crouch clip | D4 (images at the art milestone) |

**Missing**

| Mechanic | Why / when |
| --- | --- |
| Guards in rooms 3 and 21; sword fighting | Phase P5, after review (D2). **Until then, room 3 is unguarded, so the sword is not needed to win.** |
| Grabbing a ledge mid-jump or mid-fall (Shift) | R-D01 (fixed jump landings). Not needed for any route found so far; the original allows recoveries this cannot. |
| Running momentum, skids, turning while running | R-D01 |
| A gate closing on a kid who stands in its cell | Not modeled; the original's behavior was not verified |
| Rubble jamming a plate | Does not arise in Level 1: none of its 12 loose floors lands on a plate (checked with the engine, session 08) |
| Sound, title, cutscenes, going on to Level 2 | Out of scope; leaving through the exit ends the episode as a win |
| A model player on L1 | Its prompt legend lacks `S` and `k`; `play.py` refuses it (audit note 3) |

## Verification (session 10, 2026-10-26, after the stabilization)

| Check | Result |
| --- | --- |
| Data: pinned SHA-256 and size; Apple II vs DOS layouts | match; identical (`tools/fetch_level1.py --check`) |
| `uv run pytest -q` (with the local file) | 281 passed, 1 skipped |
| Loose-floor movement regression tests (`tests/test_regressions.py`) | 25 passed (14 of them on loose-floor movement); 9 of the 10 new movement cases fail on the session-08 engine |
| Fresh clone of the branch, `UV_OFFLINE=1`, no level file, no pygame | 272 passed, 10 skipped (6 original-file tests skip by design); `play.py L1` prints the setup instructions |
| Committed traces (`tests/test_trace_replay.py`) | 16 of 16 identical, including the **complete state** after reset and every step (292 states) against the engines that recorded them |
| Fresh baseline run of the final suite vs `traces/eval/` | 12 of 12 wins; traces identical (timing fields aside) |
| Frozen definitions, first observations, model prompt | hashes unchanged (`tests/test_frozen_suite.py`) |
| Search over all six suite scenarios for impossible states (in wall, falling while supported, standing on air, hanging from nothing) and crashes | none (before the fix: S1, S3, H1, H3) |
| L1 sword route, engine (`test_level1_original.py::test_sword_route_completes_level1_consistently_at_every_frame`) | won; 87 actions, 0 invalid, 790 frames; sword taken in room 15; 1 HP left; consistent at every frame |
| L1 sword route, frontend: `play.py L1 --keys <route>` headless, original art | "ESCAPED! (actions 87, invalid 0)" |
| Session-08 route on the fixed engine | invalid: its 5th action jumped off the loose floor at room 1 (2,6) and depended on the kid being left "falling" on solid floor; by action 23 he is falling and `LEFT` is refused |
| Shortest win without the guard (rooms 1, 2, 3, 9 only) | 20 actions, 2 HP: what the missing guard allows until P5 |
| Baseline on L1 (exhibition, seeds 100 and 101, not committed) | `step_limit` at 600 actions, never leaves room 1 (unchanged by the fix). It was written for the authored suite and is not tuned for L1. |
| Rules audit (session 08) | `docs/audits/AUDIT-2026-10-26-session08-level1.md` |
| Independent rules review (of session 08's work) | findings received from the student; resolutions in `docs/agent-sessions/10-level1-stabilization.md` |

## Comparison with the original game

What has been compared, and how:

1. **Layout:** decoded from two independent original releases (Apple II
   source and DOS data), which agree byte for byte on everything the game
   uses.
2. **Rules:** each mechanic is read from the 6502 source, with SDLPoP's C
   reimplementation as a second reading where the Apple II source was
   unclear (gate state at load, potion values, start facing). Locators are
   in `docs/RULE_SOURCE_MAP.md`.
3. **Completability:** with our movement rules, the real layout is
   completable along a room sequence we chose: down from room 1, through
   the gated rooms 6 → 8 → 7 → 20 → 12 to the sword in room 15, then back
   through room 3 to the exit in room 9. The route passes three closed
   gates, so it necessarily uses their original plates. Whether this matches
   how the original is usually played has not been checked against a
   walkthrough or play.

**Not done:** no one has played an original build for this comparison, so
no rule here is labeled `observed`. Owner: the student. Suggested checks in
SDLPoP (or another original build), with notes of build, room and date:

- [ ] Room 1: after the entry, is the slammed gate at room 5 (0,9) closed before control returns?
- [ ] Departure frames (R-D33): standing on a loose floor that is about to fall, how late can a run, step, jump or climb start and still get away?
- [ ] Each jump on the 87-action route (`tests/test_level1_original.py` `SWORD_ROUTE`): does the original allow it from the same block, and land on the same block?
- [ ] Rooms 6/12/14 (row 0): when you hop under the loose floor of the room above, does it visibly shake on screen? (This decides audit finding 1.)
- [ ] Fall damage at each drop on the route: is the HP loss the same?
- [ ] Gate timing: can you reach each gate in time from its plate, as our route does?
- [ ] Room 3: can you get past the guard without the sword? This is the reference for P5's "legitimate ways to avoid the guard".

## Art (decision D4)

Until the art milestone, the sword and skeleton are drawn as code shapes in
both art modes, and the pickup reuses the crouch clip. Before completion, a
separate, student-approved step adds the images the frontend then draws:
the sword and skeleton floor pieces, the kid's `pickupsword` and
`resheathe` frames (`Source/SEQTABLE.S:1255-1275`, frames 229–240), and in
P5 the guard sprites and the kid's sword frames. These go into
`assets/original/` with `MANIFEST.tsv` and `docs/ASSET_PROVENANCE.md`
updated, committed **only on the course branch** (PR #57), never in the
public repository; `.gitignore` already excludes `assets/original/*/`. The
exact image numbers are chosen from contact sheets at that step.

## P5 (not started; needs the student's go-ahead)

- Place the two guards (R-C33) with program 0 (R-C23) and base strength
  (R-C22), decisions from the engine's seeded RNG.
- Add a `sword` posture and `STRIKE`, `BLOCK`, `ADVANCE`, `RETREAT` for `L1`
  only, with `/game-rules-audit` (legal actions change for `L1`).
- First read `Source/AUTO.S` and `Source/CTRL.S` for what a guard does to a
  kid without a sword and whether he can be passed. That sets which ways
  around the guard stay legitimate (D2).
- Replace the 87-action route test with one that defeats or avoids the
  guard, and keep the frozen-suite checks green.
