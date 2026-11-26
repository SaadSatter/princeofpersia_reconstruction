---
handoff_id: HO-T21-dryrun-telemetry-analyst
task_id: T21-dryrun
date: 2026-11-25
from: telemetry-analyst
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T21.md@60f4805 (item 4, dry run)
source_branch: task/T21
source_commit: 72066f176f316294fb750b147d0c0b5af4d028a5 (base; fixture logs read at this commit)
reviewed_commit: n/a
verdict: n/a
---

# T21-dryrun: telemetry analyst report (format demonstration)

Status: done

**This is a dry run, written by the Tech Lead following the analyst procedure
(`agents/telemetry-analyst.md`) to show the format.** It is not a real
analyst's work and not a playtest result. The input is the T20 fixture,
`tests/data/t20_telemetry/`, which is hand-built test data: no real player, no
real session. Every number below is **counted from logs** (the fixture files)
with `python3 tools/telemetry/summarize.py tests/data/t20_telemetry --out <scratchpad>`,
run twice; the two `summary.json` files were byte-identical.

## The sample (counted from logs)

- 5 seat logs, 3 duels (ABCD duel 1: A and B; ABCD duel 2: A and B; EFGH duel 1: A only).
- Schema groups: all 5 logs are **schema 1** (`build: "fixture"`). Schema 1 logs
  are read per accepted action and undercount `block`, `flip`, `draw` and
  `sheathe` (T20-fix2). No schema 2 log is in this sample, so nothing is pooled.
  (`tests/data/t20_telemetry/v2/` holds one schema 2 file; it is a separate group
  and is not used below.)
- Rival: all headers say `"rival":"human"`, so every seat is a human seat.
- Unusable logs: none. `*-host.json`: none present, none read.

## Findings: stall (counts from logs)

| # | what | where | how many | evidence | confidence |
|---|---|---|---|---|---|
| S1 | One idle spell of 7.167 s (no accepted action for 3 s, then none until a TAKE) | room-aaa, ticks 14 to 100 (`idle` start `since_t` 14, end at `t` 100) | 1 of 5 seat logs, 1 of 3 duels | `2026-11-25-ABCD-001-A.jsonl:9-11` | low: one seat, a small sample; idle means no accepted input, not "stuck" |
| S2 | Stayed in one room for the whole duel: 83.333 s (seat A), 83.333 s (seat B), 66.667 s (seat B) | room-aaa (ABCD-002-A), room-ccc (ABCD-002-B and ABCD-001-B) | 3 of 5 seat logs, 2 of 3 duels (over the 60 s threshold) | `ABCD-002-A.jsonl:2-5`, `ABCD-002-B.jsonl:2-5`, `ABCD-001-B.jsonl:2-9` | low: "stuck" means stayed in the room, not "could not leave"; ABCD-002 ended by a forfeit at tick 1000 after a disconnect, and ABCD-001-B was disconnected from tick 400 to 430; paused or disconnected time counts toward the room time |

Refused-action runs of 12 ticks or more: none in the 5 seat logs.

## Findings: quit (counts from logs)

| # | what | where | how many | evidence | confidence |
|---|---|---|---|---|---|
| Q1 | Disconnect without reconnect, ending in a forfeit (seat B forfeits, seat A wins by `rival_disconnected`) | ABCD duel 2, tick 500 (B disconnect) to tick 1000 (forfeit) | 1 duel of 3 (both seat logs agree) | `ABCD-002-B.jsonl:3-5`, `ABCD-002-A.jsonl:4-5` | medium: both seats' logs show it; one duel only |
| Q2 | Disconnect then no rematch pressed | ABCD duel 1, B: disconnect at tick 400, `rematch` pressed false at tick 800 | 1 seat log; seat A pressed rematch in the same duel (`ABCD-001-A.jsonl:17`) | `ABCD-001-B.jsonl:5-10` | low: one seat; B reconnected at tick 430 (line 7) and then did not press |
| Q3 | Duel abandoned (room closed with no result) at tick 100 | EFGH duel 1, seat A | 1 of 3 duels | `EFGH-001-A.jsonl:3` | low: one seat log; a one-seat file cannot tell a closed browser tab from a host stop |

## Findings: ignored mechanic (counts from logs, schema 1 group)

Totals over the 5 seat logs. "Seat logs using it" is the count of seat logs
with at least one use.

| # | mechanic | uses | seat logs using it | evidence | confidence |
|---|---|---|---|---|---|
| M1 | sheathe, sword pickup, throw, kick, sweep never used | 0 | 0 of 5 | summary, "Never used"; no matching rows in any file | low: 5 seat logs, 3 duels, fixture data; sheathe is also weak evidence when draw is 1 (a zero-gap draw then sheathe reads as one hold) |
| M2 | TAKE, RIG, flip, block, draw each used once in total | 1 each | 1 of 5 each | `ABCD-001-A.jsonl:10` (TAKE), `ABCD-002-A.jsonl:3` (RIG) | low: schema 1 undercounts flip and block; "flip" would count jump starts, not key presses, in schema 2 |
| M3 | A seat that used no listed mechanic at all | 0 | 2 of 5 seat logs (ABCD-002-B, EFGH-001-A) | summary, "Mechanics used: none" | low: EFGH-001-A is an 8.333 s abandoned duel |

## Not shown by logs

Why a player idled, left, disconnected or did not press rematch; whether a
mechanic was understood; whether a disconnect was the player's or the
network's; who the players were (headers carry a room code and a duel number
only); anything the other seat saw; anything about an AI seat (none in this
sample). The logs show only what each seat's own view and own inputs held.

## Commands run

```
python3 tools/telemetry/summarize.py tests/data/t20_telemetry --out <scratchpad>/sum   (twice; byte-identical)
grep -n '"idle"\|forfeit\|disconnect\|duel_end\|rematch\|"RIG"\|"TAKE"\|"room"' tests/data/t20_telemetry/*.jsonl
```

## Requested next action
Orchestrator: nothing to relay. Format check only (QA, Gate 1).

## Student decision required
None.
