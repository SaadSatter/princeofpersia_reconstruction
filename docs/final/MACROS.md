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
| `DISGUISE` | Walk to the nearest figure whose posture is `downed` (own cell or the cell ahead), `TAKE` | done when `me.disguised`; fails `no_target`, `unreachable`, `no_uniform` (cell remembered, not retried) |
| `WAIT` | `WAIT` | done at once |
| `FOLLOW` | Approach the nearest suspected figure to 3 cells, same row, face it | done `in_range`; fails `no_target`, `unreachable` |
| `STRIKE` | Draw when within 5 cells (3 if disguised), approach, face, then: `LUNGE` if the target is unarmed, knocked down or facing away; `SWEEP` if it is armed and facing me (a sweep is not blocked by a blocker, and a lunge on a knocked-down body always hits, R-V12); a different stance if its stance is low | done when the target is gone after an attack; fails `no_target`, `unreachable` |
| `FLEE` | Leave by the edge away from the nearest armed figure or rival | done on a new room or no threat; fails `cornered` |
| `CLIMB` | Plan to a pose from which `UP` climbs to a higher row | done when the row is higher; fails `no_climb` |
| `SEARCH` (*addition*) | Leave the room by the edge toward the room seen least recently (never-seen first); careful steps when disguised, leaps only if walking cannot reach the edge | done on a new room; fails `no_edge` |
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
- The room model is `agents/baseline.py` `RoomView` (the midterm baseline's
  published-rules model), extended so that standing figures stop a walk but a
  jump flies over them (R-V22).

## Baseline heuristics (`VersusBaseline`, `kind: scripted`)

First match wins: (1) one heart and an armed figure within 4 cells in the row:
`FLEE`; (2) a rival, or a guard with a tell: `STRIKE` (`WAIT` if currently
unreachable); (3) a guard with a weak tell: `FOLLOW`; (4) not disguised and a
downed guard in view: `DISGUISE`; (5) not disguised, exactly one standing
guard in view, two or more hearts: `STRIKE` it; (6) disguised and suspicion
over 50, or one heart: `BLEND`; (7) `SEARCH`.

Tells (all visible to a human): a "guard" that jumps, climbs or flips; one
that runs unarmed (real guards run only chasing, sword drawn); one motionless
over 24 frames while unarmed (a patrol pause is 12); one facing me in its
5-cell sight line that has not drawn within 12 frames while I am not
disguised (a real guard draws within 3). Weak tell: motionless 12 frames or
in sight and unreacting. The sight range 5 is a published rule (R-V14), not
hidden state. The baseline never receives the other seat's observation, the
episode or the seed.

Known limits: it searches by walking room to room along its current row
(never falls on purpose), so a rival that goes down a floor is not followed;
no trap rigging; stance play is one-step; a lone-guard fight can cost a heart.

## Results (this sandbox, Python 3.13)

Fixed starts, seats swapped, 2 seeds each, 5-minute duels, win = baseline wins.
Tuning starts (used while fixing bugs; two starts x 2 seats x 2 seeds):
vs WAIT 8/8, vs Random 8/8. Held-out starts (four starts, first run after the
fixes; no thresholds were changed after looking at them): vs WAIT 16/16, vs
Random 16/16. The start lists are in `tests/test_versus_baseline.py`. Caveat:
the baseline was debugged on the default arena start, which is also tuning
start 1; both opponents are passive, so these numbers show competence against
passive seats only, not against the PPO rival.

Throughput (baseline vs Random, 5 seeds x 2,000 frames, cadence 6, decisions
counted for both seats): default runner about 2,100 per second; fast path
(`copy_mode="json"`, `threaded=False`) about 3,000 per second.
