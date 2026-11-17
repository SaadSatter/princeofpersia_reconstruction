# Shadow Masque art: provenance

The online build cannot serve the original DOS sprites (they exist only on
the private course branch; [`docs/ASSET_PROVENANCE.md`](../ASSET_PROVENANCE.md)).
Shadow Masque draws its own art instead.

## Decision

Saad, 2026-11-16 (OQ-8): use **our own medieval stone dungeon art made with
PixelLab**, with 32 px characters, pillars in the background and frameless
iron portcullis gates. Saad checked PixelLab's terms of service (updated
30 October 2026; <https://www.pixellab.ai/termsofservice>) and reads them as
permitting the use, modification and distribution of generated outputs,
including commercially, so the art is committed to this public repository.

Rejected the same day: a SakPix free demo sheet (style clash with our art,
front-facing gate, and no licence file establishing redistribution). It was
never committed.

## What is where

`assets/generated/` (40 files). `MANIFEST.tsv` lists every file
with its source, size and SHA-256; `tests/test_generated_art.py` checks the
folder against it, and `tests/test_frontend.py` allows no other tracked
images besides the original-art manifest.

| Files | Made with | PixelLab id |
| --- | --- | --- |
| `tiles/platform.png`, `tiles/platform.json` | PixelLab sidescroller tileset (pro), grey granite with flagstone tops; the JSON keeps only the corner table | `b723a004-aac5-4b9e-8a71-c3742a4a53a7` |
| `props/pillar.png`, `props/torch.png`, `props/door.png` | PixelLab map objects | `a6907856-…`, `b692d8c1-…`, `5e16db79-…` |
| `rival/*.png` (stand, run, step, jump, leap, crouch, death, drink, strike, block, hit) | PixelLab character (v3, 32 px, side view) and its skeleton animations, east only | character `200624a1-3d6e-4098-b4a6-781eb38a7312` |
| `rival/climb.png` | Hang, pull and press frames **hand-built** in `tools/build_generated_art.py` from the rival's standing sprite; crouch, rise and stand from the PixelLab `climb-skel` animation | as above |
| `rival/stance_*.png`, `rival/lunge_*.png`, `rival/throw.png`, `rival/dive_kick.png`, `rival/sweep.png`, `rival/take.png` (2026-11-17) | PixelLab skeleton animations for the swordplay in [`VERSUS_SPEC.md`](VERSUS_SPEC.md); stances and lunges use straight-arm poses so the blade height reads at a glance. The mid stance's blade is **hand-drawn** by the build tool (PixelLab dropped it) | as above |
| `guard/*.png` (stand, walk, stance, strike, hit, downed, and since 2026-11-17 `stance_*`, `lunge_*`) | PixelLab character and skeleton animations | character `3e3205ed-340e-4965-a0ca-71cd9d2a4f2a` |
| `sprites.json` | Frame sizes, counts and anchors, written by the build tool | — |

Drawn in code, not stored: the portcullis gate and the floor spikes
(`render/dungeon.py`), the loose-floor tiles and pressure plates (cut from
the drawn floor slab), the potion, and the HUD hearts. The second rival is
the first one recoloured from indigo to crimson at load time, so both rivals
share every frame and the same size.

Rebuild: download the PixelLab outputs listed above, then
`uv run python tools/build_generated_art.py RAW_DIR` (layout in the tool's
docstring). The game and tests never contact PixelLab.

## How it was made (rules followed)

- Prompts described our own designs in a genre style ("medieval dungeon",
  "1980s cinematic platformer"). "Prince of Persia" was never in a prompt.
- No original sprite, tile or level was uploaded to PixelLab or used as a
  reference or tracing source.
- The gate is our own drawing in the style of the genre's portcullis gates
  (two planes of iron bars sliding into the ledge above), not a copy of the
  original game's gate image.
- The art follows the engine's grid (`render/anim.py`: 32 px columns, 63 px
  rows, feet line 55 px down, hanging feet 33 px below the ledge); the grid
  was never changed for the art. One-cell gaps stay one cell wide
  (`test_a_one_cell_gap_is_drawn_one_cell_wide`).

## Cost

188 PixelLab generations of the account's 2,000 monthly plan allowance
(`get_balance`, 2026-11-17: 95 by 2026-11-16, then 93 for the swordplay
clips including two rounds of retries for readable stances); the prepaid
credit balance ($24.72) was not touched.
