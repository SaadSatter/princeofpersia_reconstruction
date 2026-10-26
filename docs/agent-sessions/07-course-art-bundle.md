# Session 07 — Original artwork in the course submission only

| Field | Value |
| --- | --- |
| Agent | Claude Code (CLI), model Claude Opus 5.5 (`claude-opus-5-5`) |
| Role | Implementation agent (instructions: `CLAUDE.md`) |
| Session ID | `6bd3c5dd-7710-4a07-85aa-1d556de600c0` (same CLI session as 05–06, continued) |
| Date | 2026-10-26 |
| Repositories | development `SaadSatter/princeofpersia_reconstruction` (public); course `columbia-university-ai-games/game-dev-f26` (private), branch `saadsatter/midterm`, PR #57 |
| Transcript | Local only, not committed |

## Student instructions and decisions

1. Student asked to include the original artwork in the course
   submission, bundle only the required art, document provenance without inventing terms or evidence, and show
   the inventory, size and concerns before committing.
2. After review, the student approved the 207-image bundle, manifest,
   loader, tests and provenance documentation, and chose **course PR only**:
   the images go into the private course branch and PR #57; the public
   development repository stays free of them. Cite
   https://github.com/jmechner/Prince-of-Persia-Apple-II; do not treat its
   README as a license for the DOS artwork. No force-push, no history
   rewrite, no merge.

## Checks before committing

| Check | Result |
| --- | --- |
| Bundle | 207 PNGs, 60,241 bytes (KID 150 / 47,540; VDUNGEON 40 / 9,598; PRINCE 17 / 3,103); 0 content duplicates; 0 of 207 differ from an independent SDLPoP clone at `3c5add5` |
| Packed size increase if bundled | about +75 KiB (225 → 300 KiB), measured with `git gc --aggressive` on a clone |
| Mechner README | read via the GitHub API on 2026-10-26 (repository HEAD `25243550b6e1d035d7b51b5d7e5114a83ebcb5c0`); quoted exactly in `docs/ASSET_PROVENANCE.md` |
| `uv run pytest -q` (working copy; images present locally, untracked) | 173 passed, 1 skipped |
| Fresh clone of the development tree (0 PNGs tracked), `UV_OFFLINE=1` | without pygame 170 passed, 4 skipped; with pygame 171 passed, 3 skipped; `play.py S3` shows placeholder art ("bundled images missing") |
| Fresh clone of the course folder (207 PNGs tracked), `UV_OFFLINE=1` | without pygame 171 passed, 3 skipped; with pygame 173 passed, 1 skipped; `play.py S3` shows original art |
| Engine, agents, suite, results, traces | unchanged (`git diff` empty for `pop/ agents/ evaluate.py traces/ EVALUATION.md docs/EVALUATION_SUITE.md`) |

Commit and CI evidence: see the section below (added after the pushes).

## Commits, PR update and CI

| Item | Value |
| --- | --- |
| Development commit | `3dbed8d` on `main` (public): manifest, loader, tool, tests, docs; **0 PNG files tracked** |
| Dev CI for `3dbed8d` | success, 170 passed and 4 skipped on Python 3.11 and 3.12 (no images, no pygame): https://github.com/SaadSatter/princeofpersia_reconstruction/actions/runs/40407256391 |
| Course branch commit | `24e083b` on `saadsatter/midterm` (normal push, no force): folder = `3dbed8d` + 207 PNGs force-added; `bundle_assets.py --check` passed before commit; only `midterms/saadsatter/**` changed; workflow file unchanged |
| Course workflow `midterm-saadsatter` for `24e083b` | success on pull_request (run 40407336405) and push (run 40407328373), 171 passed and 3 skipped on each Python version; one skip fewer than dev CI because `test_bundled_images_match_the_manifest` runs where the images exist: https://github.com/columbia-university-ai-games/game-dev-f26/actions/runs/40407336405 |
| Course `Minigame submission boundaries` | still fails, same cause as sessions 05–06 (rejects the required workflow file; run 40407332804) |
| PR #57 | https://github.com/columbia-university-ai-games/game-dev-f26/pull/57: still an open draft, not merged; description updated (bundled art, attribution, written terms, provenance link, commands) |

## Follow-up

Student instructions (2026-10-26): the provenance documentation keeps only
the written terms (the source READMEs). Updated `docs/ASSET_PROVENANCE.md`,
R-D02, the session 07 change summary, this record and the PR #57
description.
