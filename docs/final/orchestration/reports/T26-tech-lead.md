---
handoff_id: HO-T26-tech-lead
task_id: T26
date: 2026-11-26
from: tech-lead
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T26.md@2d59733
source_branch: task/T26
source_commit: dfe2d90e5b12486510a150dd4ba30fdd96e2528f
reviewed_commit: n/a
verdict: n/a
---

# T26: tech-lead report (how far does one left/right tap move a rival?)

Status: done (investigation only; no code, test or doc changed)

## Work completed
Measured left/right taps and holds through the real `VersusEpisode` with the exact key-to-action mapping of `web/bridge.py` (`seat_input`, `running_dir`, the per-tick loop of `WebGame.tick`), at base dfe2d90 and again on the T23 code (0c7d73a, extracted to a scratch directory). Read the original `SEQTABLE.S` and our rule rows. Proposed four options. Scratch scripts are outside the repository: `/private/tmp/claude-501/-Users-saadsatter-Classes-AI-Pract-Building-Games-princeofpersia-reconstruction/8e40f288-673a-4e35-9ce3-4719a7f7c80a/scratchpad/t26.py` and `t26_t23.py`.

## Paths
Only this report.

## Short answer
- One accepted tap always moves **one whole block** (14 original units, 32 px of a 320 px room, one full body width) in 4 ticks (R-D01, R-C26). That is by design, not a bug.
- At the base, a human tap of only **2 ticks (167 ms, an ordinary quick tap) moves 2 blocks**, and a hold of 4 ticks (one run's length) also moves 2. The extra block is the input still queued from the last held tick (R-V00: the held key is resent every tick, the newest input waits as the one pending input and starts when the move ends). This is what T23 (#93) removes.
- After T23 a tap of 1 to 4 ticks moves exactly one block, and a hold moves one block per 4 ticks held. What remains is the size of that block: smaller steps are impossible under R-D01.

## How a tap is turned into moves (all front ends share it)
1. Each 12 Hz tick the front end reads which keys are held and sends the one matching action (`seat_input`, `web/bridge.py`; `versus_input`, `play.py`, kept equal by a test). A held key is resent every tick; there is no key-down edge.
2. `Duel.submit` stores it as the single pending input (a newer one replaces an older one, R-V00).
3. `Duel._advance`: while a move runs (RUN = 4 frames, STEP = 8, TURN = 4), nothing starts; when it ends, the pending input starts at once (same tick). The kid is moved to the next block only at the end of the move (`Game._phase`, `_enter`).
4. Hence blocks moved = the first move + every later tick boundary (ticks 5, 9, 13...) at which the pending input is still there, including one that was sent from a key already released. Release does not cancel it at the base.

## Table 1: measured at the base (dfe2d90), no change
Method: seat A in the arena (room 2, row 0, clear floor, start col 4), key held for N ticks then released, counted until the kid is idle. Moves started at ticks given. "Block" = 14 units. Sheathed and drawn gave identical numbers (checked on a separate row, hold 1, 2, 4, 12, both facings; see below), so one table is given.

| Facing vs key | Shift | Hold 1 tick | Hold 2 | Hold 3-5 | Hold 6-9 | Hold 10-13 | Moves start at ticks |
| --- | --- | --- | --- | --- | --- | --- | --- |
| same way | no (run, 4 frames) | 1 block | 2 | 2 | 3 | 4 | 1, 5, 9, 13 |
| same way | yes (careful step, 8 frames) | 1 | 2 | 2 | 2 | 3 | 1, 9, 17 |
| opposite | no | 0 (turn only, 4 frames) | 1 (turn, then 1 block) | 1 | 2 | 3 | turn at 1, then 5, 9, 13 |
| opposite | yes | 0 (turn only) | 1 | 1 | 2 | 2 | turn at 1, then 5, 13 |

Exact sweeps (blocks moved, same way, no Shift): hold 1 = 1; 2 to 5 = 2; 6 to 9 = 3; 10 to 13 = 4. With Shift: 1 = 1; 2 to 9 = 2; 10 to 13 = 3. Opposite way: one block fewer (the first move is the turn); with Shift it tops out at 2 for holds of 6 to 13.
Units: a run covers 14 units in 4 ticks (0.33 s); a 12-tick (1 s) hold covers 56 units (4 blocks, 128 px of the 320 px screen); a careful step covers 14 units in 8 ticks.
Drawn sword: identical block counts and ticks (rows in the first scratch run: hold 1, 2, 4, 12, both facings, Shift and not). Stance moves are separate (UP/DOWN change stance while drawn).
Queued or graced second move: yes, the pending input adds the second move for every hold of 2 ticks or more. R-V35 (grace) does not add a move: it only converts a direction plus a jump (UP or JUMP pressed within 2 ticks) into a standing flip; it was not measured here and applies only when a jump input is also sent. Not measured: tap plus UP combinations.

## Table 2: same measurement with T23 applied (0c7d73a: `VersusEpisode.release`)
Applied in `WebGame.tick` as T23 does: when no key maps to an action, the seat's pending input is cleared.

| Facing vs key | Shift | Hold 1-4 | 5-8 | 9-12 | 13 |
| --- | --- | --- | --- | --- | --- |
| same way | no | 1 | 2 | 3 | 4 |
| same way | yes | 1 (holds 1-8) | 2 (holds 9-13) | | |
| opposite | no | 0 (turn only) | 1 | 2 | 3 |

So after T23 one block per 4 ticks held, and a 2-tick tap is 1 block, not 2. The gain is exactly one block on every short press; long holds are one block shorter than at the base.

## Per front end
| Front end | How input is sampled | Same table? |
| --- | --- | --- |
| Hosted page, local two-player and vs AI (`web/main.js`, `web/bridge.py`) | held keys read once per 12 Hz tick (`stepClock`) | yes (this is the code measured) |
| `play.py --versus` | `pygame.key.get_pressed()` once per frame at 12 FPS, then `versus_input` | yes by code reading (`versus_input` equals `seat_input`; not run here, it needs a display) |
| Online server (`server/match.py`) | the page sends the held set on each key event; the server uses the latest set at each of its 12 Hz ticks | same table; a tap whose down and up both arrive between two server ticks is never seen (unmeasured, from code reading) |

A real finger tap lasts about 80 to 150 ms, i.e. 1 or 2 samples at 83 ms per tick. At the base about half of such taps therefore move 2 blocks (64 px, two body widths), which fits Saad's report.

## Comparison with the original
(`vendor/ref-levels/src/SEQTABLE.S`, read to compare numbers only.)
- A tap or hold on the direction the kid already faces starts `startrun`, 6 frames moving 8+3+3 = 14 units (`runstt4-6`, lines 159-166), then the `runcyc` loop at 26 units per 8 frames (lines 168-175, R-C26). The 14 units of `startrun` equal our one block. Releasing the key then ends in `runstop` (`stand`, lines 891-898), which adds 2+7+2-2 = 9 further units. So a quick tap in the original covers about 23 units, more than our 14. The original is not shorter than ours.
- A careful step (`fullstep`/`step14`, lines 1069+) moves exactly 14 units, our STEP (same distance, 8 frames, R-C07 block pitch 14).
- Opposite direction: `turn` (lines 541-557), no movement, then run; ours is the same (TURN 4 frames, R-D20).
- Where we differ: the original has sub-block positions (the kid stops anywhere, `chx` per frame). R-D01 deliberately rejected sub-block positions: we always land on a whole block. The original also has no queued second move: the next step needs the key held at the check frames.

Rule rows involved: R-D01 (whole blocks), R-C26 (run speed), R-C07 (14-unit pitch), R-D20 (turn on reverse), R-D07 (humans use the same macros as agents), R-V00 (pending input), R-V35 (grace), R-V22 (hop turn, flip).

## Does T23 (#93) explain part of it?
Yes, about half in everyday play. T23 is not in the base dfe2d90 (it is in task/T23, to be merged into T23-fix1 per #105). At the base a 2-tick tap moves 2 blocks; with T23 it moves 1. T23 does not change distance per move or how many moves one held second makes (3 runs in 12 ticks, 4 blocks at the base, 3 with T23).

## Options (Saad chooses)
Common facts: block pitch and positions are in `pop/physics.py` (`COLS = 10`), the observation, the arena layouts, the macro vocabulary, the PPO encoder (`agents/rl/encoder.py`, weights `agents/rl/weights/ppo-run-1.json`) and about 55 of 158 test files mention columns, spans or run actions (counted by grep, a rough size).

| # | Option | Rows it changes | Tests it breaks | PPO and baseline | Rough size |
| --- | --- | --- | --- | --- | --- |
| 1 | No change beyond the scheduled T23-fix1. Tell playtesters that one tap is one block and that a tap of 1 to 4 ticks equals one block after T23. | none | none | none; PPO keeps its weights; AI never releases keys so T23 does not touch it | none |
| 2 | Half-block steps: the engine's column grid is doubled (20 columns of 7 units, 16 px); run, step, turn and jump distances are rescaled in half-blocks so speed in units per second is unchanged; one tap = one half-block (about 16 px). Rooms and arena layouts are redrawn at 20 columns. | R-D01 (whole block becomes half block), R-C07 / R-C26 / R-C27 (spans), R-D26, R-D33 plus every jump-span row, `docs/final/CONFIGURATION.md` grid numbers | the 55 column-dependent test files in part, `tests/test_arena.py`, flip and grace tests, render tests | observation shape and legal-action meaning change (CQ-1); the PPO encoder input and the macro-to-frame plans change, so retrain; the baseline's pathfinding is rewritten for the finer grid | large: several days of engine work, arena redraw, art repositioning, a full retraining and a new Gate 2 |
| 3 | Add one short human step (a nudge, half a block, 3 frames) used when a direction key is tapped from standing and released within 2 ticks; hold still runs whole blocks. The rival also gets it as a legal action. | R-D01 (a second landing granularity), R-D20, R-V35 interplay | grace and hop-turn tests that count positions; many cell-based tests | new action name, so the macro vocabulary and observation `legal_actions` change (CQ-1, #23 reopened); PPO retrain; baseline needs the half block in its pathfinder | medium-large; also breaks "always on a whole block" for every later rule (traps, claims, gates, `Duel.claims`) |
| 4 | Wait for the continuous side-scroller study (T27). Pixel-level movement is natural there (a view window scrolling over a long level); R-D01 would be replaced in that design instead of patched here. | decided in T27 | decided in T27 | decided in T27 | none now; blocks on #107 |

Not offered, and why: making an unshifted tap a careful step (it moves the same 14 units, 8 frames instead of 4, so it is slower, not shorter); per-front-end key repeat delays (the same input rule would have to be copied three times; the R-V35 note already rejected that pattern).

## Recommendation (not a choice)
Option 1 now, then re-test with T23 merged: it removes the one avoidable extra block, at no cost, and Saad's complaint may be mostly that. If a tap of one block is still too large after T23, the real fix is a different position resolution (Option 2, or Option 4 if the side-scroller is chosen); both are too large to do twice, so decide them together with #107. I would not add Option 3: it changes the vocabulary and gives two granularities for little gain.

## Acceptance criteria to evidence
| # | Criterion (from the brief) | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Table: tap and hold 2, 4, 12 ticks; facing both ways; sheathed and drawn; queued or graced input | yes, with limits | Tables 1 and 2 above, sweep 1 to 13 ticks. play.py and the server were read, not run |
| 2 | Compare with the original and our rows | yes | Section "Comparison with the original" |
| 3 | Does T23 explain part of it | yes | T23 section |
| 4 | 2 to 4 options with rows, tests, PPO and baseline effects, size; include no change; recommend without choosing | yes | Options table |

## Tests run
No suite run: the brief permits no change to code, tests or docs and this branch changes only this file. Measurements are scripts in the scratchpad (plain `python3`, no network, no model calls).

## Findings
- [minor, unverified] A tap shorter than one server tick may be lost online (see Per front end). I did not measure it.
- [minor, unverified] Tap plus UP interplay with R-V35 was read, not measured.

## Known limitations
- Measured on the clear floor of arena room 2 row 0. Edge, wall and body cases (bump, edge refusal, claims) were not part of the question.
- `play.py` was not run (needs pygame and a display).
- Distances in "units" use the original 14-unit pitch (32 px on a 320 px screen).

## Unresolved findings
None.

## Requested next action
Orchestrator: read this report at the commit holding it on `task/T26`, take Gate 3, and put the options to Saad. No QA or Evaluation gate (no code change).
Commit to review: n/a (report only)
What changed: nothing in the product
How to check it: run the scripts above from a checkout of dfe2d90 (`t26.py`) and of 0c7d73a (`t26_t23.py` points at an extract of it)
What I am unsure about: only the two unverified items under Findings
Touches the knowledge boundary or AI seat: no (Gate 2 does not apply)

## Student decision required
Which option (1 to 4) for tap and hold size, ideally decided together with #107 (continuous side-scroller).
