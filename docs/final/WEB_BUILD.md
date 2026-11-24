# Shadow Masque hosted web build (T14)

Status: built and tested in CPython on branch `task/T14`; **not yet run in a
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
| `index.html` or `?mode=ai` | Human vs AI, human on seat A (`&seat=B` for B) | The AI seat is the **placeholder** `IdleRival` (stands still), labelled on the page. `&rival=random` uses `RandomRival` (random legal inputs). The trained rival (T05/T07) plugs into `WebGame(rival=...)`: any callable `(observation, legal_actions) -> action or None`, which receives only its own seat's view |
| `?mode=local` | Local two-player test | Both seats on one keyboard, two panels, like `play.py ARENA --versus`. **Both players see both panels**; the page says so. A test mode, not the online game |
| `&seed=N` | Seed | Default 0. R restarts the duel from the same seed |

Keys are `play.py --versus`'s: seat A WASD, F attack, G draw/sheathe,
T take, left Shift; seat B arrows, `.`, `/`, `'`, right Shift
(VERSUS_SPEC 2.3, OQ-7).

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
pygame-free `render/` modules, `web/bridge.py`, `web/art.json`), `art/`
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
  2 s, require the frame counter to advance and the console to have no
  errors, and upload a screenshot artifact. Read-only token, no secrets.

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
still needs the authoritative server (`server/`, deferred by decision #1),
which sends each client only its own seat's payload. The bridge's payload is
already the shape a server would send.

## What has not been verified

* The page has never run in a browser: the sandbox cannot reach the CDN.
  Loaded in the sandbox's headless Chrome, the built page reports
  `error: ReferenceError: loadPyodide is not defined`, as expected without
  the CDN. Pyodide's `unpackArchive`, the Phaser frame, tint, rotation and
  flip calls, and the 12 ticks per second clock are written against the
  libraries' documented APIs and untested.
* The CI workflows have not run (no push from the sandbox).
* Drawing fidelity: the room is drawn with the same tiles and layout rules as
  `render/dungeon.py`, but loose tiles, plates and gates are simplified to
  lines and rectangles. Checked by eye only on PIL renderings of the draw
  list, not against the pygame window.
