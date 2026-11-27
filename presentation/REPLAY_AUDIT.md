# Replay feasibility audit: external Human vs AI playtest (T33 stage 2a)

**Verdict: FULL reconstruction of the engine state, inputs and events. Not every item in the observer
notes is supported by the replay (see "Observer notes versus replay").**

## Which duel

`docs/final/playtest/LOG.md` section 3: session 2026-11-27 XGJT, A1 Human vs AI (trained PPO rival),
player P01, external yes, consent option (b) (decision #130), notes publishable yes, 1 duel (XGJT-001).
Room XUKM (6 duels) is Human vs Human (`telemetry/2026-11-27/README.md`) and is not this playtest.

Inputs: `docs/final/playtest/telemetry/2026-11-27/online/duel-XGJT-001-seed0.json`
(seed 0, `rival: ai`, 465 ticks of resolved inputs, 465 release lists, 0 fallbacks, outcome `won:B`,
state hash recorded) and `playtest/2026-11-27-XGJT-001-A.jsonl` (the human seat's event log).

## Does the telemetry contain enough

| Needed | Present | Where |
| --- | --- | --- |
| Initial state | yes | seed 0, `arena_episode(seed)` (fixed arena, fixed starts and guard posts) |
| Every input of both seats, with timing | yes | `ticks` (per tick `[seat, action]`), `releases` (decision #93) |
| AI actions | yes | seat B's inputs are in `ticks` (78 inputs); the AI seat has no event log of its own |
| Seed, tick rate, duel limit | yes | header: seed 0, 12 ticks/s, 3600 frames |
| Game version | yes | header `commit 6eaced529faf`; LOG.md names `main` cca7002. `git diff` of `pop server agents render web play.py` between each and `ab395fc` is empty, so the current engine is the playtest engine |
| Outcome and state hash | yes | `won:B`, 465 frames, `5dadb78e1da67d1fb312711bd48dbc60a2a4f71f5000fb00b14ec1463572a910` |

## Replay result

`server.trace.replay(trace)` (the repository's own function) returns outcome `won:B`, 465 frames, and state
hash `5dadb78e...a910`: equal to the recorded hash, outcome dict identical (inputs A 115, B 78; replaced A 63, B 7;
stale A 1). Reproduce: `uv run --extra play --with imageio-ffmpeg --with numpy python presentation/render_replay.py --verify-only`.

## Events: replay versus telemetry (human seat log)

| Event | Telemetry (A log) | Replay (engine state, per tick) | Agree |
| --- | --- | --- | --- |
| Room changes of A | t 67, 153, 246 | A changes room at 67, 153, 246 | yes |
| A hearts 3 to 2 | t 417 `hit` | 417 | yes |
| A hearts 2 to 1 | t 441 `hit` | 441 | yes |
| A hearts 1 to 0, duel end | t 465 `hit`, `duel_end` lost `won:B` | 465 | yes |
| sword_drop | t 465, cause `thrown` | A's sword `drawn` until 464, `none` at 465; A's own input at tick 463 is `THROW`; no other sword drop in the duel | yes; the drop is the human's own throw |
| Idle spell | t 240 to 372 (about 11 s) | A sends no input 240 to 372 | yes |
| B hearts 3 to 2 | not logged (AI seat) | tick 456 (after A's LUNGE inputs at 454, 456) | replay only |
| Guard `pit_hall` downed | no event in the log | engine `downed` becomes true at tick 327; B was in the room and lunged at 325; A sent no input from 240 to 372. Attacker is not recorded | replay only, unattributed |
| B sweep then lunge | not logged | B SWEEP at 409, 433; LUNGE at 415, 439; A is knocked down (10 frames) from 411 and 435 | replay only |

## Observer notes versus replay

Saad's notes are quoted verbatim on slide 4 as his. Replay support, per item:

| Observer note | Supported by the replay or telemetry? |
| --- | --- |
| The human player was able to identify the AI rival | not measurable (no identification event) |
| The AI was also able to locate the human player | consistent (both in room 5 from tick 246) but not shown who found whom |
| Strong combat, consecutive attacks | consistent: three hits on the human in 48 ticks (417, 441, 465), two sweep-then-lunge sequences |
| Disarming opponents | **not supported**: the only sword drop is the human's own THROW (input 463, drop 465) |
| Effective at defeating scripted guards | **partly**: a guard goes down at 327 with only B acting nearby; attacker not recorded |
| The human struggled to counter or interrupt the AI | consistent (0 of 3 hearts against 1 lost by the AI; 63 of the human's 115 inputs were replaced); a struggle is an observer judgement |

Decision #135 (Saad): quote the notes verbatim as observer notes, and show a separate "Replay shows" box with
verified facts only. Done on slide 4. LOG.md is unchanged.

## Limits of the video

- It is seat A's view only (as the player saw it), drawn by the pygame renderer with the generated art. The
  hosted client was a Phaser page that draws from the same engine state; the picture is not byte-identical to
  what the player saw.
- The video covers ticks 216 to 465 (20.8 s) plus a 2 s hold on the last frame. Frames before 216 are not shown.
- The caption strips state only facts in the table above, with the tick number.
