# Game modes (task T22)

Decisions: #87 (all three front ends offer the same three modes), #88 (honest names),
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
uv run --extra play python play.py --menu                 # the start menu: Up/Down, Enter, Esc
uv run --extra play python play.py --mode ai              # straight into AI Model (trained)
uv run --extra play python play.py --mode baseline
uv run --extra play python play.py --mode human           # one keyboard: A = WASD, B = arrows
uv run --extra play python play.py ARENA --versus         # the same as --mode human
```

The mode flags play the arena (`ARENA`); they cannot be combined with `--watch` or
`--replay`. Against an AI (`ai`, `baseline`) you are seat A on **either** WASD/F/G/T/left
Shift **or** the arrows, `.`, `/`, `'`, right Shift, and see only your own panel. R restarts
(one press). In `human` the keyboard is split as before and both panels show.
A wrong or missing weights file stops `--mode ai` with an error (exit 2).

## Hosted page (`web/index.html`)

Open the page: buttons for the three modes (`?play=ai`, `?play=baseline`, `?play=human`).
The bare page is Baseline (scripted), as before. `human` is the local two-player page (one
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
