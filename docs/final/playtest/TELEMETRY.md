# Playtest telemetry

Status: built in T20 (decisions #67 and #68). Off unless you ask for it. Nothing here
changes a rule, a number or what a player sees.

## Turn it on

```sh
uv run --extra online python -m server --playtest [--telemetry-dir traces/playtest]
uv run --extra play   python play.py ARENA --versus --playtest [--telemetry-dir traces/playtest]
```

The server prints one line saying telemetry is on. Without `--playtest` no file is
written and no code path reads a seat. `traces/playtest/` is git-ignored: the logs stay
on the host machine. Nothing is sent to a client, and no client message changes with the
flag on (tests/test_t20_telemetry.py compares every message).

Read the logs with:

```sh
python3 tools/telemetry/summarize.py traces/playtest [--out DIR]
```

It writes `summary.json` and `summary.md`: stalls (idle spells, runs of refused
actions, time stuck in one room), quits (disconnect, forfeit, no rematch, a duel
abandoned) and mechanics never used or used once (TAKE, RIG, flip, block, draw,
sheathe, sword pickup; strikes and the disguise are listed for context). The output is
byte-identical for the same input. Thresholds (decision #83, named constants):
`IDLE_THRESHOLD_S` 3 s, `REFUSED_RUN_MIN` 12 ticks (1 s), `STUCK_ROOM_S` 60 s.

What the summary numbers mean (read this before using them):

- **A use is counted once, when the engine starts the move.** A key held down is one use.
  The engine runs an input queued while a move is running when that move ends, and that
  start is marked `repeat` and not counted (same held key as the last start of the
  same move). A key pressed while a flip runs is the move it starts later, never the flip.
  A jump that follows a direction within the R-V35 grace window cancels that direction:
  the jump row has `grace`, and the summary drops the direction from `moves`.
- **Flip.** One per started `JUMP_*`, `RUN_JUMP_*` or `_HOP_FLIP_*` move (every directional
  jump is a flip, R-V22 as amended by #53). A running jump's `move` row reads `moved`
  because it begins as a 4-frame run and turns into the flip inside the same move, so the
  name decides, not the row's effect. A standing jump that bumped a wall (effect `bumped`)
  is not a flip. A running jump that bumps after its run-up cannot be told from a flip at
  its start and counts as one (known limit). A kick that replaced a jump is `KICK`.
- **A held draw key** toggles DRAW and SHEATHE. It is one use (the first toggle); the later
  toggles carry `repeat`.
- **`moves` and `repeats`.** `moves` is every engine start, per move name. `repeats` (and
  `repeats_by_move`) is how many of them were a held key running on. So `moves - repeats`
  is new uses. It equals a mechanic's uses where one move is one mechanic (TAKE, RIG,
  lunge, throw, kick, sweep, draw plus sheathe). It does not for `flip` (JUMP_*, RUN_JUMP_*
  and `_HOP_FLIP_*` all map to it, and a bumped jump maps to none), `block` (STANCE_UP and
  STANCE_DOWN), `sword_pickup` and `disguise` (events, not moves).
- **"Accepted" is not "executed".** The engine drops a few accepted inputs unstarted
  (about 2.6 percent in scripted play). `action` rows are inputs asked for; only `move`
  rows say what ran.
- **Idle means no input.** It is "no accepted action for 3 s". A player walking into a
  wall, or holding a key that does nothing, is not idle.
- **Stuck means stayed in the room.** 60 s in one room, not "could not leave". A long
  fight or ambush in one of the six rooms is normal.
- **Refused runs** need 12 ticks in a row (decision #83). Shorter refusals are the
  engine's fixed 3-tick window, not a stall.
- **AI duels summarize the human seat only.** The baseline seat has no log; its inputs
  and fallbacks are in the duel trace (`traces/online`). "Never used", quits and
  `no_rematch` in such a duel describe the human.
- **Counts are from the seat's own view.** `heart_lost` causes are a guess from that
  view (a rival's trap with a guard in the room reads as `strike`).

## Files

One JSON Lines file per room, duel and seat, plus one host summary per duel:

```
traces/playtest/<date>-<room>-<duel n>-<seat>.jsonl      A and B (the AI seat has none)
traces/playtest/<date>-<room>-<duel n>-host.json          counts and the engine's own reason
```

`<date>` is the host's date, `<room>` the room code (`HOME` for the code-less room,
`LOCAL` for `play.py`), `<duel n>` counts duels in the room from 001 (a rematch is the
next number; a restarted server never appends to an old file).

Line 1 is a header, not an event:

```json
{"type":"header","schema":2,"build":"3f9a1c2e","commit":"abc123def456","versions":{...},
 "seed":0,"rival":"human","room":"HOME","duel":1,"duel_frames":3600,
 "ticks_per_second":12,"idle_threshold_s":3.0,"seat":"A"}
```

`build` and `versions` are the web build's id and pinned versions, `commit` the git commit
of the server, `rival` is `human` or `baseline` (the AI seat). The seed is in the header
because the file stays on the host. There is no name, address, user agent or token.

Every other line is an event: `{"t": tick, "s": seconds, "seat": "A", "type": ..., ...}`.
`t` is the duel's frame count after the tick that produced it (12 per second; 0 at the
start). `s` is wall-clock seconds since the duel started, read from the server's clock
outside the engine, so it includes pauses. Lines are in tick order.

| type | extra fields |
|---|---|
| `duel_start` | `room` (opaque label), `hearts`, `armed`, `traps_left` |
| `action` | an input the seat asked for, one row per tick a key is held: `action`; `accepted`; for an accepted one `started` (the move the engine started this tick, or null: a held or queued input starts nothing) and `grace`; or `error` for a refused input (one that was not legal now). There is no `effect` here: before schema 2 it described the move already running, not this input |
| `move` | a move the engine started, once per start: `move` (the engine's name after its own rewrites: R-V10 kick swap, R-V22 hop turn named `_HOP_FLIP_<DIR>`, R-V35 grace), `effect` (that move's own planned effect, for example `flipped`), `grace` (true when this jump cancelled a direction, R-V35), `repeat` (true when the same held key started it again) |
| `room` | `room`: the opaque label of the room entered |
| `disguise_on`, `disguise_broken` | `cause` on broken: `action:<name>`, `heart_lost` or `suspicion` |
| `sword_drop`, `sword_pickup` | `cause` on drop: `thrown` or `knocked_away` (not logged for DRAW, SHEATHE or TAKE) |
| `trap_rigged`, `trap_sprung` | `row`, `col`; `whose: "mine"` (own traps only, in the owner's log only) |
| `hit` | a heart lost to a strike (someone or a flying sword in the room, no fall), `hearts` left |
| `heart_lost` | `lost`, `hearts`, `cause`: `fall`, `strike` or `hazard` |
| `idle` | `phase` `start` (`since_t`, `threshold_s`) and `end` (`seconds`): no accepted action for `IDLE_THRESHOLD_S` (3 s, a proposal for Saad), counted in duel ticks so a pause never counts |
| `pause` | `phase` `start` or `end`: the duel paused because a seat dropped (#38); both seats' logs. A paused duel that ends by forfeit (or is abandoned) logs `end` just before `forfeit` or `duel_end` |
| `disconnect`, `reconnect` | the seat's own |
| `forfeit` | `by`: `me` or `rival` (the grace ran out) |
| `duel_end` | `result` (`won`, `lost`, `draw`, null), `reason` (as the client is shown it; `abandoned` or `room_failed` when the room closed first), `frames` |
| `rematch` | `pressed`: true when pressed; false once, when the room closed with no press |

## What is recorded, and what is not

Each seat's log holds only what that seat's own observation could show, and its own
inputs. It never holds the other rival's identity when disguised (a disguised rival is a
guard to the other seat, so nothing is written), nor the other seat's traps or hearts
(only its own `heart_lost`), nor other rooms, guard scripts, the engine state or a token.
A trap that hurts the seat appears only as `heart_lost` with the cause its own view
shows. The host summary (`...-host.json`) may read both seats and the engine's reason.
It holds the engine's reason, the seed, who forfeited and per-seat event counts, so it
does show, by count, which seat rigged a trap or disguised (`trap_rigged`,
`disguise_on`). It is host-only and is never read by the summarizer.

**Never hand a seat's file back to its player, to the other player or to a participant
who asks for "their log".** Each file's header carries the duel's seed, and the seed
determines the arena's hidden facts (guard scripts, spawns). The files stay on the host.

Not recorded: names, addresses, user agents, tokens, key logs outside the game actions,
video, audio. Two seats of one duel never see each other's file.

The recorder only reads (`observe`, `legal_actions`, `outcome`, and since T20-fix1
`started_move`, the move the engine started for that seat on the last tick; it is
read-only and in no observation). It never steps the engine or touches the RNG, and a failure while writing stops the log, never the duel.

## Draft for CONSENT.md

The draft sentence is in `docs/final/playtest/CONSENT.md`, under "Draft addition for
option (b)". Draft for Saad's approval; the read-aloud text is unchanged.
