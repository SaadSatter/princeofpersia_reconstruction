# Change summary for the independent reviewer — session 07 (original art in the course submission)

For `.claude/agents/rules-reviewer.md`. Written by the implementation agent;
not a review.

**Trigger.** Student decisions (2026-10-26): include the original artwork in
the course submission, after the student confirmed permission; then,
"course-PR-only": the 207 images go only into the private course branch
(`saadsatter/midterm`, PR #57); the public development repository keeps only
the manifest. Cite Mechner's repository; do not call its README or SDLPoP's
GPL a license for the DOS artwork.

**Not changed.** `pop/`, `agents/`, `evaluate.py`, the evaluation suite,
results and traces, prompts, the baseline.

**Change.**
1. `render/assets.py`: default image folder is `assets/original/`; unused
   entries removed (window 326, hit splat 619) so 207 images are required.
2. `tools/fetch_assets.py` → `tools/bundle_assets.py`: maintainer tool;
   fetches SDLPoP at the pinned commit into git-ignored `vendor/`, copies
   only required images to `assets/original/`, writes `MANIFEST.tsv`
   (source, size, SHA-256); `--check` verifies offline.
3. `.gitignore`: ignores `assets/original/*/` (keeps `MANIFEST.tsv`) and
   local transcript files. The course branch force-adds the images.
4. Tests (`tests/test_frontend.py`): `test_no_original_images_are_tracked`
   (the session 06 rule) replaced by `test_tracked_images_are_the_bundle_or_nothing`;
   added `test_bundled_images_match_the_manifest` (runs where the images
   exist, so in course CI), `test_manifest_lists_exactly_the_images_the_game_draws`,
   `test_bundled_art_is_the_default`, `test_every_bundled_piece_is_drawn`,
   `test_window_draws_with_the_bundled_original_art` (pygame + images).
5. Docs: new `docs/ASSET_PROVENANCE.md`; `docs/ASSETS.md`, `CLAUDE.md`,
   R-D02, `GAME_SPEC.md`, plan.

**Things to check.**
- The provenance doc separates the student's (unverified) permission
  confirmation from independently verified written evidence (source
  READMEs only), quotes Mechner's README exactly, and does not present it
  or SDLPoP's GPL as a license for the artwork.
- The public repository never tracks a PNG; the course branch tracks exactly
  the manifest's 207 (`test_tracked_images_are_the_bundle_or_nothing`).
- The course folder's copied `.gitignore` ignores the PNGs; they are
  force-added there. A later sync that forgets `git add -f` would drop them
  (the test only allows all or none, so it would not catch a full drop).
