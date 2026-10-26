# Original artwork: provenance and permission basis

The frontend draws **207 original Prince of Persia (DOS) images** from
`assets/original/` (60,241 bytes). Everything else in this project (code,
room layouts, placeholder art, documentation) is our own work.

**Where the images are (student decision 2026-10-26, session 07):**

| Repository | Visibility | Images | What a clone shows |
| --- | --- | --- | --- |
| Course submission: `columbia-university-ai-games/game-dev-f26`, branch `saadsatter/midterm`, PR #57, folder `midterms/saadsatter/` | private | **all 207 included** | original art by default, offline |
| Development: `SaadSatter/princeofpersia_reconstruction` | public | **none** (only `MANIFEST.tsv`; the PNGs are git-ignored) | placeholder art, unless a maintainer rebuilds the images locally with `tools/bundle_assets.py` |

## What is bundled

| Folder | Files | Bytes | Content |
| --- | --- | --- | --- |
| `assets/original/KID/` | 150 | 47,540 | The Prince: 148 animation frames (run, step, turn, jumps, hang, climb, fall, crouch, drink, exit stairs, deaths) and 2 health triangles |
| `assets/original/VDUNGEON/` | 40 | 9,598 | Dungeon pieces: floors and floor edges, front edges, wall blocks, loose floor (still and shaking), rubble, pillar, gate frame and bars, pressure plates, spike floor and spikes, exit door frame, lintels, panel and stairs, torch bracket, brick decoration |
| `assets/original/PRINCE/` | 17 | 3,103 | Torch flames (9), potion (1), potion bubbles (7) |

`assets/original/MANIFEST.tsv` lists every file with its source path, size
and SHA-256. `tools/bundle_assets.py --check` and
`tests/test_frontend.py::test_bundled_images_match_the_manifest` verify the
folder against it (on the course branch, so course CI checks the bundle);
`test_tracked_images_are_the_bundle_or_nothing` fails if any other image is
committed, or if only some of the 207 are.

Only images the game draws are included (`render/assets.py`
`required_files`; `test_every_bundled_piece_is_drawn`). Not included: the
other 69 kid images, 92 dungeon pieces, 40 other `PRINCE` images (sword and others), guards, palace tiles, fonts,
palettes (`.pal`), sounds, music, level files, `.DAT` archives, and any
SDLPoP code.

## Source

| Item | Value |
| --- | --- |
| Repository | https://github.com/NagyD/SDLPoP (SDLPoP, an open-source port of the DOS game; GitHub owner `NagyD` and contributors) |
| Commit | `3c5add5fb7f83d4ceb542823ab66d00146c4271b` (2025-12-24) |
| Paths | `data/KID/`, `data/VDUNGEON/`, `data/PRINCE/` (PNG files, copied byte for byte; 0 of 207 differ from an independent clone, checked 2026-10-26) |
| Original work | *Prince of Persia* (1989), designed by Jordan Mechner; DOS version published by Broderbund. The franchise is owned by Ubisoft. |
| Original author's repository | Jordan Mechner, *Prince of Persia Apple II*: https://github.com/jmechner/Prince-of-Persia-Apple-II (README read 2026-10-26; latest commit `25243550b6e1d035d7b51b5d7e5114a83ebcb5c0`, 2024-09-27; GitHub license field: "Other", `NOASSERTION`) |
| Frame numbers (not images) | The same Apple II source as mirrored at https://github.com/historicalsource/princeofpersia, commit `2b4ddb5377f905840bf64f32e2f543a79f434222`, `01 POP Source/Source/SEQTABLE.S` |
| Frame → image mapping (a fact, not copied code) | read from SDLPoP `src/seg006.c` `frame_table_kid`; stored as 11 range shifts in `render/assets.py` |

## Stated terms of the sources (quoted; nothing added)

**Jordan Mechner, README of https://github.com/jmechner/Prince-of-Persia-Apple-II
(updated September 2024):**

> We extracted and posted the 6502 code because it was a piece of computer
> history that could be of interest to others, and because if we hadn't, it
> might have been lost for all time. We did this for fun, not profit. As the
> author and copyright holder of this source code, I personally have no
> problem with anyone studying it, modifying it, attempting to run it, etc.
> Please understand that this does NOT constitute a grant of rights of any
> kind in Prince of Persia, which is an ongoing Ubisoft game franchise.
> Ubisoft alone has the right to make and distribute Prince of Persia games.

What this does and does not say:

- It welcomes studying, modifying and attempting to run **the Apple II
  source code**. It does not mention education; "educational" describes
  our use, not his terms.
- It expressly grants **no rights of any kind in Prince of Persia**, and
  says Ubisoft alone may make and distribute Prince of Persia games.
- It is **not a license for the DOS artwork** bundled here (the images come
  from the DOS version via SDLPoP, not from this repository), and we do not
  treat it as one.

**SDLPoP** (https://github.com/NagyD/SDLPoP): its README says the program is
open source under the GNU General Public License v3 (`COPYING`). That
license covers SDLPoP's program code. It states no terms for the game data
in `data/`, and **SDLPoP's code license does not cover the original
artwork**. We do not include or copy SDLPoP's code.

**historicalsource/princeofpersia**: a mirror of the same Apple II source;
its README likewise grants no rights in Prince of Persia.

No source we found grants a license to redistribute the DOS artwork. The
artwork remains the property of its rights holders.

## Permission basis for including the artwork

Two different things, kept separate:

1. **The student's permission confirmation** (not independently verified):
   on 2026-10-26 (session 07) the student stated: "We have confirmed that
   permissions for including the original Prince of Persia artwork in our
   educational reconstruction's GitHub submission are satisfactory," and
   directed that the 207 images be included in the private course
   submission only, with attribution and the manifest, and kept out of the
   public development repository.
2. **Independently verified written evidence:** only the source READMEs
   quoted above (checked by the implementation agent on 2026-10-26). They
   welcome study of the Apple II source and expressly grant no Prince of
   Persia rights. **They do not establish a right to redistribute the DOS
   artwork.**

**Our use:** noncommercial and educational: a course submission
(Columbia COMS E6998, Fall 2026) in a private course repository. No claim of
ownership; full attribution above.

The assignment's reuse rule (`docs/MIDTERM_GUIDELINES.md`): "Public
availability does not establish an open license. Link source materials and
check their terms before copying code, prose or assets into a public
repository. … The instructor resolves unclear publication rights before
release, and decides check 1c for any submission whose reuse terms a TA
flags as doubtful."

## Removing the artwork

If the permission is withdrawn or does not cover a use: delete the images
from the course branch in a new commit (no history rewrite without the
instructor's agreement; the course forbids force-pushes after the
deadline). The game still runs; with the images missing it draws
placeholder shapes (`play.py --placeholder` forces this mode).

## Rebuilding the bundle (maintainers)

From the project folder, with network access:

```
uv run python tools/bundle_assets.py          # fetches SDLPoP at the pinned commit into vendor/, copies only required images
uv run python tools/bundle_assets.py --check  # no network: verify against MANIFEST.tsv
```

The game itself never downloads anything.

## Syncing the course branch (maintainers)

The course folder is the development tree plus the 207 images. Because the
folder's `.gitignore` (copied unchanged) ignores the PNGs, they are
force-added on the course branch only. From a clone of `game-dev-f26` on
branch `saadsatter/midterm`:

```
# 1. replace the folder with the development commit (no images)
git rm -rq midterms/saadsatter && mkdir -p midterms/saadsatter
git -C <dev-repo> archive <commit> | tar -x -C midterms/saadsatter
# 2. add the verified images
cp -R <dev-repo>/assets/original/KID <dev-repo>/assets/original/VDUNGEON \
      <dev-repo>/assets/original/PRINCE midterms/saadsatter/assets/original/
(cd midterms/saadsatter && uv run python tools/bundle_assets.py --check)
git add midterms/saadsatter && git add -f midterms/saadsatter/assets/original
```
