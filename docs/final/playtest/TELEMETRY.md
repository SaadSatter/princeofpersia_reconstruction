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
byte-identical for the same input. Two thresholds in it are proposals for Saad:
`REFUSED_RUN_MIN` (3) and `STUCK_ROOM_S` (60 s).

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
{"type":"header","schema":1,"build":"3f9a1c2e","commit":"abc123def456","versions":{...},
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
| `action` | `action`; `accepted`; `effect` (the move's effect as the seat sees it) or `error` for a refused input (one the seat asked for that was not legal now) |
| `room` | `room`: the opaque label of the room entered |
| `disguise_on`, `disguise_broken` | `cause` on broken: `action:<name>`, `heart_lost` or `suspicion` |
| `sword_drop`, `sword_pickup` | `cause` on drop: `thrown` or `knocked_away` (not logged for DRAW, SHEATHE or TAKE) |
| `trap_rigged`, `trap_sprung` | `row`, `col`; `whose: "mine"` (own traps only, in the owner's log only) |
| `hit` | a heart lost to a strike (someone or a flying sword in the room, no fall), `hearts` left |
| `heart_lost` | `lost`, `hearts`, `cause`: `fall`, `strike` or `hazard` |
| `idle` | `phase` `start` (`since_t`, `threshold_s`) and `end` (`seconds`): no accepted action for `IDLE_THRESHOLD_S` (3 s, a proposal for Saad), counted in duel ticks so a pause never counts |
| `pause` | `phase` `start` or `end`: the duel paused because a seat dropped (#38); both seats' logs |
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
shows. The host summary may read both seats and the engine's reason; it holds counts
only, no ownership.

Not recorded: names, addresses, user agents, tokens, key logs outside the game actions,
video, audio. Two seats of one duel never see each other's file.

The recorder only reads (`observe`, `legal_actions`, `outcome`). It never steps the
engine or touches the RNG, and a failure while writing stops the log, never the duel.

## Draft for CONSENT.md

The draft sentence is in `docs/final/playtest/CONSENT.md`, under "Draft addition for
option (b)". Draft for Saad's approval; the read-aloud text is unchanged.
