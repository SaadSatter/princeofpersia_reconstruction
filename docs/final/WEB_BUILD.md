# Shadow Masque hosted web build (T14)

Status: built and tested in CPython on branches `task/T14` and `task/T14-fix1`; **not yet run in a
browser** (see [What has not been verified](#what-has-not-been-verified)).
Decisions in force: DECISIONS-2026-11-23 #12 "Pyodide + Phaser
(Recommended)" and #13 "G2/G3, Sat Nov 28"; #1 keeps online human vs human
deferred.

## How it works

```
browser                                         Python (Pyodide, in the page)
-------                                         -----------------------------
keys.js   KeyboardEvent.code -> key name   ->   web/bridge.py WebGame.press(keys)
main.js   12 ticks per second              ->   WebGame.tick_json()
                                                  human seat: play.py --versus key map
                                                  AI seat: rival(observe(seat), legal_actions(seat))
                                                  VersusEpisode.tick()
          Phaser blits the draw list       <-   {"seat_view": observe(human seat),
          DOM shows hud.text and outcome         "draw": [...], "hud": {...}, "outcome": {...}}
```

* `web/bridge.py` runs the arena duel (`pop/versus.py arena_episode`). It
  takes the physical keys held, turns them into each human seat's input with
  the same table and rules as `play.py --versus` (`KEY_MAP`, `seat_input`,
  the in-air LUNGE -> KICK swap, inputs filtered by `legal_actions`), asks
  the rival hook for the AI seat, ticks, and returns one payload.
* The AI seat is `SeatControllerRival(controller, every=6)` (`web/bridge.py`),
  an adapter from a T04/T05 `SeatController` to the per-tick hook: it calls
  `controller.decide(obs, tuple(legal))` on ticks 0, 6, 12, ... (the runner's
  0.5 s cadence), maps `WAIT` to no input, submits nothing on the ticks
  between, and replaces an illegal answer or an exception with no input,
  counting it in `fallbacks` and saying so in the page label. `make_game()`
  builds one fresh controller per game. The web build **bypasses the T04
  runner**: no step limits, timeouts or traces apply in the browser.
* `render/draw_list.py` turns one seat's observation into draws (sprite
  sheet, source rectangle, position, size, flip, tint, rotation; plus
  rectangles and lines) using the same pose and animation helpers as the
  pygame frontend (`render/versus_view.py`, `render/anim.py`,
  `render/genart.py`). Phaser only blits them. `render/webart.py` measures
  the art pack and recolours the second rival with standard-library code.
* `web/main.js` loads Pyodide and Phaser, unpacks `game.zip`, runs the clock
  and draws. It holds no game logic (`tests/test_web_js.py` checks it names
  no game action or hidden field).

## Modes

| URL | Mode | Notes |
| --- | --- | --- |
| `index.html`, `?play=ai`, `?play=baseline`, `?play=human` | The three modes (T22, #87, #88): buttons from the mode list in `manifest.json` (`modes`, written by the build from `agents/modes.py`). `?play=ai` is **AI Model (trained)**: the shipped PPO policy, loaded from `agents/rl/weights/ppo-run-1.json` inside `game.zip` through the same SHA-256 check as everywhere else (`manifest.json` `weights_sha256`). `?play=baseline` is **Baseline (scripted)**. The bare page opens on the mode chooser and starts nothing until a mode is picked (T22-fix1, #92). `?play=human` is the local two-player page below. A link to `online.html` is for two people on separate machines | 
| `?mode=ai` | Human vs AI, human on seat A (`&seat=B` for B) | The AI seat is the **scripted baseline** (`agents/versus_baseline.py`, `?rival=baseline`, the default), labelled "AI rival: versus-baseline (scripted)". `&rival=idle` (stands still) and `&rival=random` (random legal inputs) stay as labelled placeholders. The trained rival (T07) plugs into the same adapter |
| `&label=neutral` | Neutral rival label | The page says only "Rival" for every kind of rival. Use it for blind playtest sessions. It changes no play |
| `?mode=local` | Local two-player test | Both seats on one keyboard, two panels, like `play.py ARENA --versus`. **Both players see both panels**; the page says so. A test mode, not the online game |
| `&seed=N` | Seed | Default 0 |

The key hints under the game are for the seat actually played. The page shows
a short **build hash** (`build`, from `manifest.json`: 8 hex digits over every
file's SHA-256) so a playtest log can name the exact build.

Keys are `play.py --versus`'s: seat A WASD, F attack, G draw/sheathe,
T take, left Shift; seat B arrows, `.`, `/`, `'`, right Shift
(VERSUS_SPEC 2.3, OQ-7).

Labels on the page, the HUD line and the end screen are the honest names, "AI Model
(trained)" and "Baseline (scripted)" (#88); `&label=neutral` still shows only "Rival". A
wrong or missing weights file stops the page's AI mode with an error, not a silent baseline.
The bundle grows by the weights file (about 430 KB, before compression).

## Build and run locally

```sh
python3 tools/web/build.py              # writes web/dist/ and prints every file's SHA-256
cd web/dist && python3 -m http.server 8000
# open http://localhost:8000/  (needs internet for the pinned CDN files)
```

`web/dist/` is gitignored. The build is reproducible (fixed file order, fixed
zip timestamps and permissions, fixed PNG encoding): two builds from the
same inputs are byte-identical (`tests/test_web_build.py`). Output:
`index.html`, `main.js`, `keys.js`, `game.zip` (all of `pop/`, the
pygame-free `render/` modules, `agents/` (the scripted baseline and what it
imports, standard library only), `web/bridge.py`, `web/art.json`), `art/`
(the generated pack, the crimson rival strips, the spike states) and
`manifest.json` (hashes, versions, sheets).

## Pinned versions (one place: `web/versions.json`)

| What | Version | Loaded from |
| --- | --- | --- |
| Pyodide | 0.27.7 | `https://cdn.jsdelivr.net/pyodide/v0.27.7/full/` |
| Phaser | 3.88.2 | `https://cdn.jsdelivr.net/npm/phaser@3.88.2/dist/phaser.min.js` |
| Playwright (CI smoke only) | 1.49.1 | npm, installed in the workflow |

`web/index.html` holds placeholders; the build fills them from
`versions.json` and refuses a URL that does not name its pinned version.
These versions were chosen from memory and **could not be fetched from this
sandbox** (CDN blocked). The first CI smoke run confirms they resolve; no
Subresource Integrity hashes are set yet, because they could not be computed
here (recommended follow-up once the files are reachable).

## Deploy

* `.github/workflows/pages.yml`: on push to `main`, build and deploy
  `web/dist` to GitHub Pages. Needs Saad to enable Pages (Settings -> Pages
  -> Source: GitHub Actions). The build job has `contents: read` only; the
  deploy job needs `pages: write` and `id-token: write`, which GitHub's
  Pages deployment requires. No secrets.
* `.github/workflows/web-smoke.yml`: on pull requests, build, check the JS
  (`node --check`, `node web/keys.test.js`), serve `web/dist`, and run
  `tools/web/smoke.cjs` in Playwright Chromium: wait for `ready`, hold D for
  2 s, require the frame counter to advance, the console to have no errors,
  the human seat's position to change (the page's test-only readout
  `window.__smLast = {frame, me: {room, row, col}}`) and the canvas pixels to
  differ before and after, so a dead key handler fails; upload a screenshot
  artifact. Read-only token, no secrets.

## Knowledge boundary (limitation)

The payload the page draws is derived from the human seat's observation
only: no other-seat observation, no seed, no `Duel`, no disguise flag of
another figure, no trap owner, no input counts of the other seat
(`tests/test_web_bridge.py`). A disguised rival is drawn with exactly a
guard's draw entries.

**But on a static page the whole engine runs in the browser.** A player
with the browser's developer tools can read the full game state (the
other rival's position and disguise, the guards' scripts, the arena layout).
`AGENTS.md` forbids sending a client the full state *for online play*; a
static page cannot meet that. It is acceptable for:

* human vs AI: reading state only cheats against your own opponent, and the
  AI seat still receives only its own observation through the rival hook;
* the local test mode, where both panels are visible anyway.

It is **not** acceptable for online human vs human on two machines. That
uses the authoritative server (`server/`, built in T13, decision #35), which
holds the only `GameState` and sends each client only its own seat's payload,
in the shape of the bridge's. See [`ONLINE_PLAY.md`](ONLINE_PLAY.md) for how
to run it, what each player receives and how the boundary is tested. The
hosted page on this document is for human vs AI and local play only.

## Playtest notes (read before a session)

* **`game.zip` is public.** Anyone can download it: the engine, the scripted
  baseline and, later, the trained rival's weights. Do not put anything in it
  that a participant must not read.
* **The query string is editable.** A participant can change `rival`, `seed`,
  `seat` or `label` in the address bar. Give them the URL without a bar, or
  watch the screen.
* **Developer tools stay closed** in playtests, and the facilitator watches the
  screen (see Knowledge boundary: with devtools open a player can read the
  whole state).
* **Rematch keeps the seed** (DECISIONS #25): the Rematch button (or R / Enter, once the duel has ended) replays the same arena and the
  same scripted guards, and resets the rival. The baseline is deterministic, so
  a second round against it can be learned. This is a learning confound across
  rounds; the protocol should say so and, if needed, change `seed` between
  rounds.
* The end screen states how the duel ended (the raw reason, as decided in #25).
* For a blind session use `?label=neutral`; write the build hash on the log.

## What has not been verified

* The page has never run in a browser: the sandbox cannot reach the CDN.
  Loaded in the sandbox's headless Chrome, the built page reports
  `error: ReferenceError: loadPyodide is not defined`, as expected without
  the CDN. Pyodide's `unpackArchive`, the Phaser frame, tint, rotation and
  flip calls, and the 12 ticks per second clock are written against the
  libraries' documented APIs and untested.
* The CI workflows have not run (no push from the sandbox). **Not verified in
  a browser** stays true until the smoke workflow passes in CI, including the
  new position and pixel checks, which have never run. The adapter plays 600
  ticks with 0 invalid inputs in CPython only; its timing under Pyodide is
  unmeasured.
* Drawing fidelity: the room is drawn with the same tiles and layout rules as
  `render/dungeon.py`, but loose tiles, plates and gates are simplified to
  lines and rectangles. Checked by eye only on PIL renderings of the draw
  list, not against the pygame window.
