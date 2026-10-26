# Evaluation Suite (declared before tuning)

Declared: **2026-10-26**, before any gameplay code, baseline, or prompt
existed. The commit that adds this file is the freeze point; its hash is
recorded in `EVALUATION.md`. Any later change to a situation, seed, or limit
must be listed in the change log at the bottom with a reason and date, and
results before and after a change are reported separately.

All layouts are **original, independently authored** rooms using
mechanics from `docs/GAME_SPEC.md`. They are not copies of original Prince
of Persia rooms. Map notation: `docs/GAME_SPEC.md` §2. Each room is listed
top row first. Links not listed are missing (wall at the sides, rock above,
bottomless below).

## Common settings

| Setting | Value |
| --- | --- |
| Player id | `kid` |
| Start HP | 3 / 3 |
| Per-call timeout | 20 s |
| Consecutive invalid limit | 5 |
| Tuning seeds (S1–S3 only) | 0, 1 |
| Final-trial seeds (all situations) | 100, 101 |
| Players | baseline; model `history` (last 8 steps + seen rooms); model `obs-only` (S1–S3) |
| Model | Anthropic Claude Haiku 4.5 (id configured by env var; exact id recorded per trial) |

No implemented mechanic uses randomness, so the seed does not change the
episode. Repeated trials measure the model's own variability. This is
stated in `EVALUATION.md`.

**Held-out rule:** H1–H3 are never run, shown, or described in a prompt
during prompt tuning. Tuning uses only S1–S3 with seeds 0–1.

---

## S1 — Gap Trial

Tests: running, standing jump over a 1-block pit, running jump over a
3-block pit with a loose-floor takeoff, using the exit.
Start: room 1, row 1, col 1, facing right. Exit open from the start.
Limits: 40 actions, 40 model calls.

```
room 1  (right -> 2)        room 2  (left -> 1)
##########                  ##########
_t___.____                  __L_..._Ee
#####^####                  ##.#...###
```

Pit under room 1 col 5 has spikes. Room 2's loose floor (col 2) and 3-wide pit (cols 4–6) drop into
nothing.

## S2 — Trap Trial

Tests: careful steps across spikes, a raise plate opening a timed gate in
the next room, avoiding a drop plate that slams the gate, timing.
Start: room 1, row 1, col 0, facing right. Exit open from the start.
Limits: 50 actions, 50 model calls.

```
room 1  (right -> 2)        room 2  (left -> 1)
##########                  ##########
_u__^^^___                  __p__G_Ee_
##########                  ##########
```

Links: room 1 plate (1,1) raises gate room 2 (1,5). Room 2 drop plate
(1,2) lowers that gate.

## S3 — Escape Trial (complete bounded escape episode)

Tests every implemented mechanic in sequence, modeled on the flow of the
original Level 1: drop into the dungeon, cross pits and a loose floor,
pass spikes, use a plate to open a gate, climb to a ledge plate that opens
the exit (as in original room 9), come down, and leave.
Start: room 1, row 0, col 1, facing right. Exit closed.
Limits: 80 actions, 80 model calls.

```
room 1 (right->2)   room 2 (l->1, r->3)   room 3 (l->2, r->4)   room 4 (left->3)
#__t__.###          ##########            ##########            u.....####
######_f__          __.__L.___            _u___^^_G_            ____Ee__##
##########          ##^##__###            ##########            ##########
```

Links: room 3 plate (1,1) raises gate room 3 (1,8). Room 4 plate (0,0)
opens exit room 4 (1,4)–(1,5). Potion: room 1 (1,7). Room 2's lower pocket
(row 2, cols 5–6) is a recoverable fall: climb back up.

---

## Held-out variations

### H1 — Gap variant (leftward)

Start: room 2, row 1, col 8, facing left. Exit open. Limits: 40 / 40.

```
room 1 (right -> 2)         room 2 (left -> 1)
##########                  ##########
_Ee..._L__                  ___..__t__
###...#.##                  ###^^#####
```

### H2 — Trap variant

Start: room 1, row 1, col 0, facing right. Exit open. Limits: 50 / 50.

```
room 1 (right -> 2)         room 2 (left -> 1)
##########                  ##########
__u_^^_p__                  ___G_^_Ee_
##########                  ##########
```

Links: room 1 plate (1,2) raises gate room 2 (1,3). Room 1 drop plate
(1,7) lowers it.

### H3 — Escape variant

Start: room 1, row 1, col 1, facing right. Exit closed. Limits: 80 / 80.

```
room 1 (r->2)    room 2 (l->1, r->3)   room 3 (l->2, r->4)   room 4 (left->3)
##########       ##########            ##########            #####...u#
#__f__L__.       ##########            ##.___G___            _____.____
######.#__       __._u_^^__            ___#######            #####Ee__#
```

Links: room 2 plate (2,4) raises gate room 3 (1,6). Room 4 plate (0,8)
opens exit room 4 (2,5)–(2,6). Potion: room 1 (1,3).

---

## Recorded per episode

situation, seed, player, provider, model id (as returned), game version
(git short hash), outcome and terminal reason, actions, invalid actions,
model calls, failed calls, fallbacks, frames, latency (mean, max), input and
output tokens, estimated cost (prices dated on the run day).

## Change log

| Date | Change | Reason |
| --- | --- | --- |
| 2026-10-26 | Initial declaration | — |
