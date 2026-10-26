# Original art: sources, local setup, restrictions

Student decision 2026-10-26 (rule R-D02, `CLAUDE.md` "Source-use
restrictions"): the frontend may draw the original Prince of Persia sprites
and dungeon tiles **from a local copy only**. Nothing in this repository is
original art; the game runs without it (placeholder mode).

## Restrictions

- The images are the original DOS game's graphics (© Jordan Mechner /
  Broderbund; the franchise is Ubisoft's). Nobody has granted us rights to
  redistribute them.
- SDLPoP is GPLv3, but that license covers its **program code**. Its README
  states no terms for the game data in `data/`.
- historicalsource/princeofpersia: Mechner permits study and modification of
  the source but grants **no rights in Prince of Persia** (its README).
- Therefore: never commit, copy into the course repository, attach, or
  otherwise redistribute any original image, sound or font. `vendor/` is
  git-ignored, and `tests/test_frontend.py::test_no_original_images_are_tracked`
  fails if a `.png`/`.pal`/`.dat`/`.bmp` file or anything under `vendor/` is tracked.
- **Recordings:** showing original art in a shared recording is a form of
  publication. Ask the instructor first, or record with `--placeholder`.
- We do not copy SDLPoP's GPL code or tables. One fact was read from its
  frame table (`src/seg006.c`, `frame_table_kid`): which DOS image shows each
  original frame. We store it as 11 range shifts for the frames we use
  (`render/assets.py` `FRAME_SHIFTS`) and checked each animation by eye.

## Where the assets are

| Asset | Source | Format | Used |
| --- | --- | --- | --- |
| Kid: all poses (219 images) | SDLPoP `data/KID/res401–619.png` | PNG, palette, transparent | yes |
| Hearts (full / empty) | SDLPoP `data/KID/res617.png`, `res618.png` | PNG | yes |
| Dungeon pieces (floors, edges, gate, spikes, plates, loose floor, rubble, pillars, exit door, stairs, torch bracket, brick decor) | SDLPoP `data/VDUNGEON/res214–351.png` | PNG pieces | yes |
| Dungeon wall blocks | SDLPoP `data/VDUNGEON/res360–377.png` | PNG pieces | yes |
| Torch flames, potion, bubbles | SDLPoP `data/PRINCE/res151–172.png` | PNG | yes |
| Guards, sword, palace tiles, other levels | SDLPoP `data/GUARD*`, `VPALACE`, … | PNG | no (out of scope) |
| Sound, music | SDLPoP `*.DAT`, `data/music` | DAT / OGG | no |
| Apple II images | historicalsource `01 POP Source/Images/IMG.CHTAB*`, `IMG.BGTAB*` | packed hi-res shape tables; would need a custom decoder | no (SDLPoP has the same frames as PNG) |
| Animation sequences (which frames, in which order) | historicalsource `01 POP Source/Source/SEQTABLE.S` | 6502 data tables | read for frame numbers; cited in `render/anim.py` |

Nothing needs extraction or conversion: SDLPoP ships the DOS images as PNG.

## Local setup

From the project folder:

```
uv sync --extra play
uv run python tools/fetch_assets.py
uv run python play.py S3
```

`tools/fetch_assets.py` sparse-fetches `data/KID`, `data/VDUNGEON` and
`data/PRINCE` from https://github.com/NagyD/SDLPoP at commit
`3c5add5fb7f83d4ceb542823ab66d00146c4271b` (2025-12-24) into
`vendor/SDLPoP/data/` and deletes the git metadata. `POP_ASSETS=<dir>`
points the frontend at another copy with the same layout. If any image the
frontend uses is missing, it falls back to placeholder shapes and says so in
the status line. `--placeholder` forces placeholder mode.

## How the screen is built (our choices)

- Original geometry: 320×200 screen, rooms of 10 × 3 tiles, 32 px wide,
  63 px tall, 8 px status line; the window scales it (`--scale`, default 3).
- Every piece is drawn inside its own cell's column (`render/layout.py`),
  so walls, holes, gates and spikes line up with the engine's cells. The
  one exception is a floor surface's right-hand part: in the original's
  perspective the top surface leans right, so its back edge reaches into
  the next cell (a floor ending at a gap shows its dark edge). Its front
  edge, where the kid stands and falls, ends on the cell boundary.
- Walls are drawn without the original's shaded side face: drawn into the
  next cell, it hid most of a one-cell pit (student playtest, session 06;
  `tests/test_regressions.py::test_regression_wall_side_face_hid_a_one_cell_pit`).
  For the same reason a gate's back post and the raised spikes' right half
  are not drawn into the next cell.
- Piece numbers are in `render/assets.py` `DUNGEON`, chosen by eye from
  contact sheets; offsets are ours, so the picture is close to, not
  pixel-identical with, the original.
- Wall faces and the brick decoration on empty cells vary per cell from a
  hash of the room label, so they don't flicker.
- Gate bars and the exit door panel are clipped to the observed `open_pct`;
  the exit shows the starry sky and stairs behind it.
- Kid sprites are mirrored when facing right (the images face left) and
  placed by the bottom centre of the image on the feet point that
  `render/anim.py` computes.

## Animation (R-D26)

The engine moves whole blocks (R-D01), so each accepted step is shown as one
clip of exactly the step's engine frames at 12 frames/s, using the
original sequence for that move resampled to that length:

| Engine step | Original frames (SEQTABLE.S label) |
| --- | --- |
| Run one block | 1–6 starting, then 7–14 cycling (`startrun`, `runcyc1`) |
| Careful step | 121–132 (`fullstep`) |
| Turn | 45–52 (`turn`) |
| Standing jump | 16–33 (`standjump`) |
| Running jump | run-up, then 34–44 (`runjump`) |
| Jump with no room / UP with nothing to climb | 67–78 (`jumpup`) |
| Climb up | jump up 67–74, then 135–148 (`climbup`) |
| Climb down to hang | 148→136 (`climbdown`), then hang 91 (`hang`) |
| Drop from hanging | 81–85 (`hangdrop`), then falling |
| Fall | 102–106 (`stepfall`/`freefall`), landing 107–109 (`softland`) |
| Crouch | 107–109 (`stoop`) |
| Drink | 191–205 (`drinkpotion`) |
| Exit stairs | 217–228 (`climbstairs`) |
| Death on spikes | 177 (`impale`) |
| Death from a fall or crush | 179–185 (`dropdead`) |

Hurt and death add a short red flash. A fall into a bottomless pit leaves
the screen.
