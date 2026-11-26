# Macro layer and scripted versus baseline (task T05)

Status: implemented on `task/T05`, awaiting QA (Gate 1) and the Evaluation
Specialist (Gate 2). Everything marked *proposed* needs Saad's approval; the
macro vocabulary is a CQ-1 item.

Code: `agents/macros.py` (executor, controller), `agents/versus_baseline.py`
(policy). Tests: `tests/test_macros.py`, `tests/test_versus_baseline.py`.

## Vocabulary (*proposed*)

| Macro | What the executor does | Done when / fails when |
| --- | --- | --- |
| `BLEND` | Careful steps along the floor, pause two waits (about 12 frames) at the end of the stretch, turn (4 frames). Matches a guard's patrol shape (step 8, pause 12, turn 4) | done after one leg; fails on timeout |
| `DISGUISE` | Walk to the nearest figure whose posture is `downed` (own cell or the cell ahead), `TAKE` (always legal, R-V26; a `last_result.effect` of `no_uniform`, acting seat only, means the body was already stripped) | done when `me.disguised`; fails `no_target`, `unreachable`, `no_uniform` (cell remembered, not retried) |
| `WAIT` | `WAIT` | done at once |
| `FOLLOW` | Approach the nearest suspected figure to 3 cells, same row, face it | done `in_range`; fails `no_target`, `unreachable` |
| `STRIKE` | Draw when within 5 cells (3 if disguised), approach, face, then: `LUNGE` if the target is unarmed, knocked down or facing away; `SWEEP` if it is armed and facing me (a sweep is not blocked by a blocker, and a lunge on a knocked-down body always hits, R-V12); a different stance if its stance is low | done when the target is gone after an attack; fails `no_target`, `unreachable` |
| `FLEE` | Leave the room by the edge away from the nearest armed figure or rival, else the other edge, else a pit in the bottom row, else a shaft up that is known to work (T05-fix1) | done on a new room or no threat; fails `cornered` |
| `CLIMB` | Change floor, both ways (**confirmed by Saad, decision #31**). Parameter `direction`: `up` plans to a pose from which `UP` climbs to a higher row, or tries `UP` in the top row to leave by a shaft (one column and facing at a time, remembered); `down` walks off a ledge for a fall of one row, or hangs from the ledge (`DOWN`) and lets go (`DOWN`) so that a two-row fall costs no heart (R-D17), or leaves through a pit in the bottom row. No direction: the nearest of either, up first | done when the row changed (`climbed`, `dropped`) or the room changed (`new_room`); fails `no_climb` |
| `SEARCH` (*addition*) | Leave the room by the exit toward the room seen least recently (never-seen first): a side edge, a pit down, or a shaft up. Rooms this seat fled from are tried last. Careful steps when disguised, leaps only if walking cannot reach the exit. `prefer: down` (the baseline asks for it) puts the pit first among unseen rooms, so the lower floor is seen early | done on a new room; fails `no_edge` |
| `RIG_TRAP` | Reserved; reported `failed: reserved`, never played | |

`SEARCH` is not in the G1 list. Without it nothing moves a seat between rooms
(the rival starts in another room), so the PPO rival would need it too.

## Executor rules

- Deterministic; plans only from the observation and legal tuple. A target is
  chosen from observed attributes (position, posture, motion, armed). The
  figure `kind` is read only for the label `"rival"` (visible: an undisguised
  rival is shown as a rival); a disguised rival is found by tells, not by id.
- **Queue-ahead.** Each decision plans from `me.motion.to` (where the current
  move ends), so the returned input starts the frame the move finishes. A step
  (8 frames) always chains without a gap at the 6-tick cadence; a run (4)
  leaves 2 idle frames per decision, so blending walks.
- **Re-validation.** Every returned input is checked against the current legal
  list; an input legal only later (for example `TAKE` before arriving) is
  replaced by `WAIT` and asked again (counted in `executor.substituted`).
- **Reporting.** `executor.events` has `macro_done` / `macro_failed` with a
  reason; `MacroController.log` has one row per decision. A failed macro is not
  re-run for 5 decisions, and a stuck pose (5 decisions, no motion) or more
  than a per-macro decision cap fails it (`stuck`, `timeout`).
- **Moves that end out of sight.** While a move is in progress and the observation masks where it ends (`motion.to` is null: a climb up a shaft, a flip over the edge), the executor sends `WAIT`. An input queued then would run in a room not yet seen, and a direction pressed during a hop turns it into a flip (R-V22). A finished wait keeps the `to` of the move before it, so the planned pose ignores `to` for a wait.
- **Vertical planning (T05-fix1).** `FieldView` adds the engine's fall rules to the room model, from this room's tiles only: a fall of one row is safe, two rows cost a heart, three kill, and a fall from a hang counts one row less (R-D17). A pit in the bottom row is planned as leaving the room downwards, assuming a floor at the top of the room below (a pit looks the same whether or not a room lies below, so the view cannot know). A climb up needs the cell above open and the cell ahead of it floor, so the top-row climb is tried per column and facing. Cells in front of a standing guard-looking figure cost extra when this seat is not disguised.
- The room model is `agents/baseline.py` `RoomView` (the midterm baseline's
  published-rules model), extended so that standing figures stop a walk but a
  jump flies over them (R-V22).

## Baseline heuristics (`VersusBaseline`, `kind: scripted`)

First match wins: (0) a knocked-down figure within 3 cells in the row, not
disguised: `STRIKE` (a lunge always hits, R-V12); (1) one heart and an armed or
suspected figure within 4 cells in the row: `FLEE` (an unarmed rival cannot cost
a heart, so it is not fled from); (2) a rival, or a guard with a tell: `STRIKE` (`WAIT` if currently
unreachable); (3) a guard with a weak tell: `FOLLOW`; (4) not disguised and a
downed guard in view: `DISGUISE`; (5) not disguised, exactly one standing
guard in view (T05-fix1; an armed guard wins too often to fight at will):
`STRIKE` only when the matchup favours it, that is full hearts and the guard
knocked down, or unarmed with its back to me; if it is armed or sees me (its row,
in front, within 5, no wall) within 3 cells, `FLEE` the room when it is more
than 2 cells away and `STRIKE` when closer (running from an engaged guard costs
more hearts than the fight); if it is unarmed and cannot see me, `WAIT` up to 40
decisions for its patrol to turn its back; if it is on a lower row and I have full
hearts, `CLIMB` down to its row; otherwise go on to (6); (6) disguised and suspicion
over 50, or one heart: `BLEND`; (7) `SEARCH` (`prefer: down`).

Tells (all visible to a human): a "guard" that jumps, climbs or flips; one
that runs unarmed (real guards run only chasing, sword drawn); one motionless
over 24 frames while unarmed (a patrol pause is 12); one facing me in its
5-cell sight line that has not drawn within 12 frames while I am not
disguised (a real guard draws within 3). Weak tell: motionless 12 frames or
in sight and unreacting. The sight range 5 is a published rule (R-V14), not
hidden state. The baseline never receives the other seat's observation, the
episode or the seed.

Known limits: no trap rigging; stance play is one-step (a sweep, then a lunge
inside the 10 knocked-down frames); a lone-guard fight can still cost a heart
or two when the guard is adjacent at the start; the shaft-up search is blind (it
tries one column and facing at a time and remembers what worked); a mirror
match is decided by seat order (seat A resolves first), see Results.

## What the baseline remembers (disclosed; Gate 2 asked for this)

All of it is this seat's own observations, in plain counters. `reset(seed)`
clears all of it.

| Keeps | Lives | Used for |
| --- | --- | --- |
| Figure tracks in the current room: per standing guard-looking figure, frames motionless, frames in sight without drawing, whether it ever leapt or ran unarmed | until the room changes | tells (rules 2, 3) |
| Rooms visited, by opaque label: visit count, the decision it was last seen, which neighbour each exit led to | whole duel | `SEARCH` order (never-seen first, then least recently seen) |
| Rooms fled from: the decision and the hearts it fled at | 120 decisions (about 12 s), or the whole duel if it fled on its last heart | `SEARCH` tries them last |
| Top-row (column, facing) pairs that climbed out of a room, and pairs tried that did nothing | whole duel | blind shaft search, `CLIMB up` |
| Downed bodies whose uniform was already taken | whole duel | `DISGUISE` does not retry them |
| Macros that failed recently | 8 decisions | no immediate retry |
| Guard-wait counter | until no figure is in view | the 40-decision wait in rule 5 |

The PPO rival (T07) keeps no such memory unless its encoder is given it; read
the comparison with that in mind.

## Results (this sandbox, Python 3.13)

Fixed starts, seats swapped, 2 seeds each, 5-minute duels, win = baseline wins.
Tuning starts (used while fixing bugs; two starts x 2 seats x 2 seeds):
vs WAIT 8/8, vs Random 8/8. Held-out starts (four starts, first run after the
fixes; no thresholds were changed after looking at them): vs WAIT 16/16, vs
Random 16/16. The start lists are in `tests/test_versus_baseline.py`. Caveat:
the baseline was debugged on the default arena start, which is also tuning
start 1; both opponents are passive, so these numbers show competence against
passive seats only, not against the PPO rival.

### T05-fix1 (this worktree, Python 3.13.5 via `uv run`)

- Default arena start, vs WAIT, 4 seeds x 2 seats: rooms 4 and 5 both reached
  8/8, uniform obtained 8/8 (`test_from_the_default_start...`). Before the fix:
  rooms 4 and 5 not reached from the lower floor, no uniform (Gate 2, Gap 1).
- Lone guard from a guard-room start (rooms 4 and 5, 2 seeds x 2 seats): 0
  deaths in 8/8 (before: 8/8 lost).
- Lower-floor tuning starts (two, seats swapped, 2 seeds): vs WAIT 8/8, vs Random 8/8.
  New held-out lower-floor starts (seven, frozen before the fix): vs WAIT 28/28, vs Random 27/28.
  Older top-row held-out starts: 16/16 and 16/16.
- Random starts in every room (40 duels, sampler seed 99, seats alternating, 3,600
  frames, vs WAIT): 39 wins, 0 losses, 1 timeout (QA's earlier sweep: 22 W, 8 L, 10 T).
  Vs Random (sampler seed 7): 37 W, 3 L, 0 T.
- Baseline vs baseline, default starts, 12 swapped duels: 0 draws, all won by seat B
  (the same trace every time, as the baseline is deterministic; seat A resolves
  first). Random starts (24 duels): 10 W, 7 L, 7 T from one side's view.

Throughput (baseline vs Random, 5 seeds x 2,000 frames, cadence 6, decisions
counted for both seats): default runner about 2,100 per second; fast path
(`copy_mode="json"`, `threaded=False`) about 3,000 per second.
