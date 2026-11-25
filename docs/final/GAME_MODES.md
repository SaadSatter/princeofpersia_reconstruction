# Game modes (task T22)

Decisions: #91 and #92 (T22-fix1), #87 (all three front ends offer the same three modes), #88 (honest names),
#89 (against an AI the human plays seat A with WASD or the arrows), #90 (built from
`orch/reviewed` 74975e1, merged after T20), #3 (the PPO policy is the in-game AI), #43
(the AI rival does not rig traps), #45 (0.04 s online answer budget), #49 (online
fallbacks are logged, never shown), #41 and #46 (rematch), #55 (control sets).

There are three modes, listed once in `agents/modes.py`. Every front end reads that list.

| Mode id | Name on the menu, HUD and end screen | Other seat |
| --- | --- | --- |
| `ai` | AI Model (trained) | the shipped PPO policy (`agents/rl/weights/ppo-run-1.json`, SHA-256 checked at load) |
| `baseline` | Baseline (scripted) | `agents/versus_baseline.make_baseline()` |
| `human` | Human vs Human | a second person |

`--neutral` (server) and `&label=neutral` (page) still show only "Rival", for blind tests.

## pygame (`play.py`)

```sh
uv run --extra play python play.py                        # the start menu: Up/Down, Enter, Esc
uv run --extra play python play.py --menu                 # the same, explicitly
uv run --extra play python play.py --classic              # the old single-prince level (S3)
uv run --extra play python play.py S2                     # a named situation, as before
uv run --extra play python play.py --mode ai              # straight into AI Model (trained)
uv run --extra play python play.py --mode baseline
uv run --extra play python play.py --mode human           # one keyboard: A = WASD, B = arrows
uv run --extra play python play.py ARENA --versus         # the same as --mode human
```

A bare `play.py` opens the menu (#92). Naming a situation, or `--classic`, `--versus`,
`--watch`, `--replay` (or scripted `--keys`/`--screenshot` without menu keys), keeps the
single-player behaviour. The mode flags play the arena (`ARENA`); they cannot be combined with `--watch` or
`--replay`. Against an AI (`ai`, `baseline`) you are seat A on **either** WASD/F/G/T/left
Shift **or** the arrows, `.`, `/`, `'`, right Shift, and see only your own panel. R restarts
(one press). In `human` the keyboard is split as before and both panels show.
A wrong or missing weights file stops `--mode ai` with an error (exit 2).

## Hosted page (`web/index.html`)

Open the page: it opens on a chooser with buttons for the three modes (`?play=ai`,
`?play=baseline`, `?play=human`) and starts nothing until one is picked (#92). An address that
already names a game (`play=`, `mode=` or `rival=`) skips the chooser. `human` is the local two-player page (one
keyboard, both panels); the link to online play is for two people on separate machines.
Details: `docs/final/WEB_BUILD.md`.

## Online server

```sh
uv run --extra online python -m server               # rooms; the creator picks the mode
uv run --extra online python -m server --rival ai    # the default (code-less) room is vs AI
```

On the page, pick the mode, then **Create room**. AI rooms start at once with the rival on
seat B; a Human vs Human room waits for the second player's code join. Details:
`docs/final/ONLINE_PLAY.md`.

## What the AI seat is, and what it is not

- **Timing.** The pygame and hosted-page AI seats are called synchronously, once per tick,
  with no time budget (measured per decision on the Mac: median 0.04 ms, p99 1.2 ms; not
  measured in Pyodide). Only the online server has the 0.04 s limit (#45), with a labelled
  `"source": "fallback"` when an answer is late (#49).
- **WAIT.** A decision tick that answers WAIT submits `"WAIT"`, as the evaluation runner does,
  and the ticks between decisions submit nothing. The game and the runner then play the
  shipped rival identically (T22-fix1, EVAL-T22-1). A failed or illegal answer is no input and a
  labelled fallback.
- **The name is a label, not a claim.** "AI Model (trained)" says what the rival is. The
  policy was trained against scripted rivals, and nothing here shows how it fares against
  people (the T09 comparison was not supported). No win rate or strength figure appears in
  the menu, the HUD or the end screen (EVAL-T22-5).
- **Fallbacks.** The hosted page writes the AI seat's labelled fallbacks to the browser
  console only; pygame prints one line at exit; the server keeps them in its trace and log.
  They never reach the other seat's screen.
- **Weights.** Loaded and hash-checked once per process and shared (the network is
  immutable); each game gets its own controller state.
