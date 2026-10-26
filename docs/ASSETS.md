# Original art: how the frontend uses it

The frontend draws 207 original Prince of Persia (DOS) images from
`assets/original/`. They are bundled **only in the private course
submission** (PR #57); this public development repository has only their
manifest. Their source, attribution, permission basis and inventory are in
**`docs/ASSET_PROVENANCE.md`**. This file explains how the screen and the
animations are built from them.

- In the course submission, no setup and no network: `uv sync --extra play`,
  then `uv run python play.py S3` (working directory: the project folder).
- In the public development repository the same command draws placeholder
  shapes; a maintainer can rebuild the images locally (git-ignored) with
  `uv run python tools/bundle_assets.py`.
- `--placeholder` draws simple shapes instead; the same happens if any
  required image is missing (the status line says so).
- `POP_ASSETS=<dir>` points the frontend at another folder with the same
  layout (`KID/`, `VDUNGEON/`, `PRINCE/`).
- Maintainers rebuild or verify the bundle with `tools/bundle_assets.py`
  (`--check` needs no network).
- We do not copy SDLPoP's GPL code or tables. One fact was read from its
  frame table (`src/seg006.c`, `frame_table_kid`): which DOS image shows each
  original frame. We store it as 11 range shifts for the frames we use
  (`render/assets.py` `FRAME_SHIFTS`) and checked each animation by eye.
- Apple II images (historicalsource `IMG.CHTAB*`, `IMG.BGTAB*`, packed
  hi-res shape tables) are not used; SDLPoP has the same frames as PNG.

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
