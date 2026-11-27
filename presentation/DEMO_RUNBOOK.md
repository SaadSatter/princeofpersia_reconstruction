# Live demo runbook (slide 2, 60 seconds)

You play the demo yourself. Nothing here changes a rule; it uses the existing `--mode ai`.
The rival is the shipped PPO policy (loaded by SHA-256) and answers whatever you do, so its moves
are not scripted and not repeatable by hand. Say so if you describe them.

## Before you start (30 seconds, off camera)

From the repository root, on the commit you want to show:

```sh
uv sync --extra play                       # once
uv run --extra play python play.py ARENA --mode ai --seed 0 --scale 3
```

It opens one window (the rival's view is hidden, as in play). Close it with Esc. Seed 0 is the seed
of the external playtest, so the start positions match: you start in the West Cells (room 1), the
rival in the East Tower (room 3). No API key, no network.

Controls: arrows or WASD move, F lunge, G draw or sheathe the sword, T take a downed guard's uniform,
Up while armed changes stance. Hold Shift for a careful step. R restarts.

## Route and beats (about 60 s)

Checked against the engine with a scripted bot (the rival not in the way): the route below works.

1. **Movement.** Hold Right along the bottom floor for about 2 seconds. You drop through the shaft
   at the end of the West Cells into the **Barracks** (this happened at tick 24, 2.0 s, in the check).
2. **Scripted guard.** A guard patrols the Barracks floor. Press G to draw, walk up, press F to lunge until
   the guard goes down (about 3 to 6 s of fighting in the check; a real hand can take longer).
3. **Take the uniform.** Stand next to the downed guard and press T. You are now drawn as a guard.
4. **Disguise and suspicion.** Walk calmly past the other guard. Hopping (Up) near a guard adds
   suspicion (+6 per frame, 48 per hop); three hops in sight break the disguise.
5. **The rival.** Go looking for it (the Undercroft and Pit Hall are the way east). In the external playtest (replay engine state, tick 68) the
   rival was in the Pit Hall from tick 68 (read from the replay engine state). When it appears, fight, run, or use a loose floor: say what you
   decided because of what it just did. Do not claim it was scripted; do not claim it was planned.

If the rival has not appeared by about 0:50 of the slot, stop and cut to slide 3 (it is fine to say
"the rival is somewhere in the other half of the palace").

## Fallbacks, in order

1. **Window will not open or crashes.** Run `uv run --extra play python play.py ARENA --mode baseline --seed 0 --scale 3`
   (scripted baseline, same game). Say it is the baseline, not the learned rival.
2. **pygame is missing.** `uv sync --extra play` (needs the network once). If you cannot, use the video
   on slide 4 as the gameplay, labelled "reconstructed from telemetry", and the stills on slide 2.
3. **Nothing runs.** Use the stills on slide 2 (labelled as a scripted rehearsal) and the 22 s clip on slide 4.
   Say plainly that the live demo was not available.
4. **Clip will not play inside the slide.** Play `presentation/out/xgjt-001-segment.mp4` from Finder.

## What is real and what is not

- Slide 2 stills: a scripted rehearsal bot drove seat A for the first 89 ticks; seat B was the real PPO
  policy. They show the route, not the rival (it was out of sight). Label them as a rehearsal.
- Slide 4 clip: not a new match. A replay of the logged inputs of room XGJT, duel 1, checked against its
  recorded state hash.
