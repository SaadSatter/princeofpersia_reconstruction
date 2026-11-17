# Shadow Masque versus spec: two seats, swordplay, guards, disguise

Status: **approved as written by Saad, 2026-11-17**, including every number
marked *proposed*, the observation fields (Section 6) and the key map
proposal (Section 2.3, OQ-7). The decisions in Section 1 are Saad's; the
numbers were drafted by the agent. Implementation follows Section 9. Each rule gets an `R-V`
id; it becomes a `design` row in `docs/RULE_SOURCE_MAP.md` when it is
implemented, with its failing test written first.

## 1. Decisions in force

| Decision (Saad) | Value |
| --- | --- |
| Damage (2026-11-17) | **Keep 3 hearts** (OQ-1 stands). Swordplay follows *Nidhogg*'s stances, matched-height blocks and disarms, but a clean hit costs 1 heart instead of killing |
| Moves in the first playable (2026-11-17) | Three stances (high, mid, low), block by matching height, disarm, **lunge, sword throw, dive kick, low kick / sweep** |
| Two-seat timing, CQ-1 (2026-11-17) | **Real-time ticks**: the server advances one shared game 12 frames per second and both rivals' moves overlap frame by frame |
| Disguise and guards, OQ-2 and OQ-5 (2026-11-17) | A guard is downed by one clean hit or a trap and stays down. DOWN beside a downed guard takes its uniform. Running, jumping, climbing, a drawn sword or striking near a guard raise that guard's suspicion of you; walking lowers it; full suspicion breaks the disguise and the guard attacks. A guard's meter is shown only to the rival it suspects |

The suspicion meter is therefore **in** scope (the GDD listed it as a cut
candidate). Swordplay is our own rules in the genre of *Nidhogg* (Messhof):
mechanics only, no names, art or code from it.

## 2. Two seats in one game (CQ-1)

### 2.1 Ticks

- `pop/versus.py` holds one `Duel` with one geometry, one `Mechanics`, two
  `Rival`s (seats `A`, `B`) and the arena's guards. Every random choice uses
  the duel's `random.Random(seed)`.
- Today's moves are already per-frame generators (`Game._run`, `_jump`,
  `_up` … yield once per frame). The duel keeps that: each rival has at
  most one move in progress; `tick()` runs **one world frame**
  (`Mechanics.tick`, falls, traps) and then advances each rival's move one
  frame, A then B, then guards, then resolves contacts (Section 3). Order
  inside a frame never decides a hit: contacts are resolved on the frame's
  end state, symmetrically.
- A seat's input starts a move only when that rival is *free* (no move in
  progress). Stance changes and blocks are the exception (R-V03). A seat
  holds at most one pending input: a newer input replaces an older one
  (the keyboard's latest press wins); the AI seat's macro-action is just an
  input.
- 12 ticks per second, as the midterm's display (R-D26). The server runs
  ticks on a clock; tests and replays call `tick()` directly, so they stay
  deterministic and need no clock.

### 2.2 The five operations, per seat

| Operation | Two-seat form |
| --- | --- |
| `reset(seed)` | New duel; returns nothing secret (each seat calls `observe`) |
| `observe(seat)` | That seat's view only (Section 6) |
| `legal_actions(seat)` | The inputs that seat may submit now |
| `step(seat, action)` | Validates and queues the seat's input; refused input changes nothing and is counted, as in the midterm |
| `outcome()` | `ongoing`, or terminal with reason: `won:A`, `won:B`, `draw:both_died`, `draw:time_up` (GDD 5.3) |
| runner and server only: `tick()` | Advances one frame; never exposed to a seat |

### 2.3 Inputs (action vocabulary)

The midterm's 11 movement actions stay. New inputs:

| Input | Keyboard (proposal, OQ-7) | Legal when |
| --- | --- | --- |
| `STANCE_UP`, `STANCE_DOWN` | Up / Down while standing with the sword drawn | Standing, armed |
| `LUNGE` | F | Standing, armed |
| `THROW` | Up + F | Standing, armed |
| `KICK` | F while airborne (dive kick) | During the airborne frames of a jump |
| `SWEEP` | Down + F | Standing or crouching |
| `TAKE` | Down beside a downed, uniformed guard | Standing next to one, facing it |

Up and Down keep their midterm meanings (climb, crouch, hang, drink) when
the sword is sheathed or nothing else applies. *Proposed:* while armed and
standing on open floor, Up/Down change stance; to climb or crouch, a rival
first sheathes with `SHEATHE` (S). This keeps one key map for both. This
needs Saad's approval (OQ-7, key map).

## 3. Swordplay rules (R-V01 to R-V12)

Frames are engine frames (12 per second). All numbers *proposed*.

| Id | Rule | Proposed numbers |
| --- | --- | --- |
| R-V01 | Hearts: each rival starts with 3; a stab, a thrown-sword hit, a guard's stab, a sprung trap or a damaging fall costs 1; 0 is death | (decided, OQ-1) |
| R-V02 | Stances: high, mid, low. A drawn sword is always in one; a new rival starts sheathed, then draws to mid | Draw 3 frames |
| R-V03 | Changing stance takes effect after a short delay and is allowed even during the opponent's attack (that is how disarms happen) | 2 frames |
| R-V04 | Lunge: windup, active, recovery. Hits a rival or guard in the cell ahead, same row, facing, during active frames | 2 + 2 + 4 = 8 frames, reach 1 cell |
| R-V05 | Block: a lunge is blocked if the defender is armed, facing the attacker and in the **same stance** at the active frame: no hit, and the attacker is pushed back | 1 cell, if the cell behind is free |
| R-V06 | Hit: a lunge that is not blocked costs the defender 1 heart, pushes them back 1 cell and gives them invulnerability so one exchange cannot take two hearts | 12 frames invulnerable |
| R-V07 | Disarm: if the defender's stance change lands **into** the attacker's height during the attacker's windup, the attacker's sword is knocked away and lands 1–2 cells behind them | Window = the 2 windup frames |
| R-V08 | Sword throw: the sword flies along the thrower's row and hits the first rival or guard (1 heart); a defender in the thrower's stance deflects it; it lands where it stops. The thrower is unarmed | 2 cells per frame; stops at walls, closed gates and room edges |
| R-V09 | Unarmed: cannot lunge, throw or block; can kick and sweep; picks a sword up with DOWN on its cell | Pickup 6 frames |
| R-V10 | Dive kick: during a jump's airborne frames, `KICK` drops diagonally forward. Blocked by a high stance; a hit disarms the target and knocks them down (no heart lost) | Lands 1 cell ahead; knockdown 10 frames |
| R-V11 | Sweep: hits the cell ahead from a crouch. Avoided by a low stance or by being airborne; a hit knocks down (no heart) | 6 frames; knockdown 10 frames |
| R-V12 | Knocked down: cannot act; a lunge on a knocked-down rival always hits | — |

Rivals cannot walk or run through each other or through a standing guard;
they can jump over a knocked-down one, and a jump to the side can flip over
a standing one (R-V22). Every running jump is a flip, so it can also clear
holes and spikes as a flip, and so is a hop straight up turned by pointing a
direction mid-hop.

| Id | Rule | Numbers |
| --- | --- | --- |
| R-V22 | Flip (Saad, 2026-11-17; confirmed after playtest the same day: guards can be flipped over, and flips are automatic, with no separate key): **every running jump is a flip** (over holes and spikes too, as far as a running jump already goes), and a standing jump flips when it passes over someone; a standing jump over nobody stays a plain jump. **Hop then point** (Saad, 2026-11-17): a direction input (with or without Up held) during a hop straight up (`UP` on open floor, not a climb to a ledge) ends the hop and starts a standing jump that way, always a flip, facing the pointed way without a separate turn. A direction after the hop has landed is an ordinary move. A standing or running jump may fly over the other rival or a standing guard **in the jumper's own room**, and never lands on anyone. Walls and closed gates still stop it; a body in another room still blocks, as before, so a jump never reveals someone out of sight. A flip is one forward 360° somersault, shown to every seat in the room as motion effect `flipped`. Otherwise it is a jump: dive kick allowed, suspicion as a leap, sweeps miss while airborne. The flipper keeps its cell until it lands (as every jump), so a lunge into that cell still hits it; its landing cell is claimed for the flight so a guard cannot step into it | Same span and frames as the jump (3 cells standing, 4 after a running jump's run-up); the arc rises 22 px higher on screen *(proposed)* | Swords dropped in a room stay there; they are
visible to whoever is in that room.

## 4. Guards (R-V13 to R-V16)

Scripted, not AI (GDD). Hostile to both rivals equally.

| Id | Rule | Proposed numbers |
| --- | --- | --- |
| R-V13 | Patrol: each guard walks its post's cells (arena `GUARD_POSTS`) back and forth at step speed, turning at the ends | Pause 12 frames at each end |
| R-V14 | Sight: a guard sees a rival in its room, same row, in front of it, within range, with no wall or closed gate between | 5 cells |
| R-V15 | Attack: on seeing an undisguised rival (or one whose disguise broke) a guard draws, advances and lunges when adjacent. It copies the rival's stance after a reaction delay, so a quick stance change can beat it | Reaction 6 frames; lunge at most every 16 frames |
| R-V16 | Downed: one clean hit (lunge, thrown sword) or a trap downs a guard for the rest of the duel. A downed guard keeps its uniform until a rival takes it (once) | — |

## 5. Disguise and suspicion (R-V17 to R-V21)

| Id | Rule | Proposed numbers |
| --- | --- | --- |
| R-V17 | `TAKE` beside a downed, uniformed guard: the rival kneels, takes the uniform and is disguised; its sword is sheathed under it | 12 frames |
| R-V18 | A disguised rival is drawn, and observed by the other seat, **exactly** as a guard (Section 6). Guards ignore a disguised rival whose suspicion is not full | — |
| R-V19 | Suspicion: each guard has a meter 0–100 **per rival**. It rises only while that guard sees the disguised rival (R-V14 sight) | Running +4/frame; jumping or climbing +6/frame; standing still within 1 cell for over 2 s +1/frame |
| R-V20 | It falls when the rival walks (`STEP`), stands still out of reach, or is out of sight | −2/frame |
| R-V21 | The disguise breaks at once on: drawing, any attack, or any guard's meter reaching 100 (decided); *proposed additions:* a stance change (it draws the sword anyway) and losing a heart. Then it is gone for the rest of the duel (one uniform per downed guard) | — |

## 6. What each seat sees (leak rules)

Each seat's observation is today's (room tiles, gates, plates, loose floors,
its own rival) plus:

- `figures`: everyone else **in the same room**, each as
  `{kind: "rival"|"guard", row, col, facing, posture, stance, armed}`,
  sorted by position. A disguised rival appears with `kind: "guard"`, a
  guard's posture set and no extra field. There are no ids, seats or
  names in `figures`.
- `motion` (added in implementation, 2026-11-17, **for Saad's review**): on `me`
  and on each figure, the move in progress as it looks on screen: effect,
  frames done, length, and its planned end cell only if that cell is in the
  same room (`to` is `null` otherwise, so up/down links stay hidden). A
  client needs it to animate a move while it runs; it shows nothing a player
  watching the screen would not see. Not a seat's pending input.
- `swords`: dropped swords in the room, as cells.
- `me`: the seat's own rival, adding `stance`, `armed`, `disguised`,
  `knocked_down_frames`.
- `suspicion`: a list of `{row, col, level}` for guards **in view** whose
  meter concerns **this** rival only.

Never in a seat's observation: the other seat's suspicion meters, which
figure is the disguised rival, guard scripts or posts, trap ownership, other
rooms, the seed, or the other seat's inputs.

Leak tests, failing first: (1) seat B's observation with a disguised A is
identical, field for field, to the observation where that figure is a real
guard in the same pose; (2) seat B never receives A's suspicion; (3) the
server's outgoing message to B equals `observe("B")` and nothing more.

## 7. AI seat and runner

The AI seat submits the same inputs (Section 2.3) from its own observation,
about one every 4 s (decided). It will fence poorly against a human at that
cadence; whether that is playable is OQ-9 and is measured at the first
playtest, not assumed. The runner counts every input and call per seat and
applies per-seat timeouts; a timed-out seat's labelled fallback is `WAIT`.

## 8. Art (ready or in progress)

PixelLab animations, side view, for both the rival and the guard: three
stances, three lunges, sword throw, dive kick, sweep, taking a uniform; plus
the existing walk, strike, hit and downed clips. A disguised rival is drawn
with the guard's own frames. Suspicion is drawn in code above the guard, for
the suspected seat only.

## 9. Order of work after approval

1. Rule-map rows R-V01 to R-V21 (`design`) and the leak tests, failing.
2. `pop/versus.py`: two rivals and ticks, movement only, through the five
   operations; per-seat observation; determinism test (same seed and the
   same per-tick inputs give an identical trace).
3. Swordplay R-V01 to R-V12, one test per rule.
4. Guards R-V13 to R-V16, then disguise and suspicion R-V17 to R-V21.
5. Renderer for two rivals, guards, swords and the suspicion meter; then the
   server and browser client (OQ-11).

Each step ends with `uv run pytest -q` and an independent review
(`rules-reviewer` or `game-rules-audit`) before the next starts.

## 10. Implementation notes (2026-11-17, for Saad's confirmation)

Built on branch `final/versus-engine` in stages 1-4 (`pop/versus.py`,
`pop/guards.py`; tests `tests/test_versus.py`, `test_swordplay.py`,
`test_guards.py`, `test_disguise.py`). Where this spec was silent the
implementation chose the values below; each is a constant and can change.

| Where | Choice |
| --- | --- |
| R-V00 timing | A move's arrival is applied at the start of the next frame (the inherited macros place the kid after their last frame); same for both rivals and guards |
| Sheathe | 3 frames, like drawing |
| Throw | 8 frames; the blade leaves on frame 3; a sword and a body swapping cells meet |
| Dive kick | 4 frames, active on the last 2; lands 1 cell ahead of where the jump is |
| Sweep | Active on frames 3-4 of 6 |
| Guards | Chase at run pace (4 frames per cell); cannot be disarmed; a kick or sweep knocks a guard down for 10 frames instead of downing it; patrol starts at the end its post faces from |
| Disguise | TAKE works from the downed guard's own cell (standing over it, either facing) or from the cell ahead, facing it; the own cell was added after Saad's playtest (2026-11-17), where T over the body did nothing. A disguised rival is observed with the guard's sheathed look (stance null, armed false) |
| Observation | Two additions: `motion` (Section 6) and flying swords in `swords` (`flying: true`); `motion.effect` gains the value `flipped` (R-V22) |
| Flip (R-V22) | The inherited jump asks `_can_vault(cell)` for each cell it would fly over; single-player answers no, so midterm traces are unchanged. A running jump still needs a free run-up cell, so it cannot flip over someone directly in front; a standing jump can. A running jump plans its flight after the run-up; `motion.frame` counts the flight from take-off (1-8), not from the start of the run (it used to report 5-12 of 8, so the picture began mid-flight; `test_regression_running_jump_flight_counts_its_own_frames`) |
| Local test keys | `play.py ARENA --versus`: A uses WASD, F attack, G draw/sheathe, T take; B uses arrows, `.` attack, `/` draw/sheathe, `'` take. One keyboard, two panels, each drawn from its own seat's observation; not the online key map (OQ-7). Up + direction while running in that direction is a running jump (a flip, R-V22), as in the original game; from a standstill it is a standing jump unless Shift is held. Before Saad's playtest of 2026-11-17 it needed Shift even mid-run, so a run never turned into a flip |

Not done yet: the independent review after each stage (Section 9 asks for
one before the next stage; it must run in a separate session to be
independent), the game server and browser client, the AI seat in versus
play, traps set by rivals, and the duel time limit (OQ-3: the limit is a
parameter, default the inherited 60-minute clock).
