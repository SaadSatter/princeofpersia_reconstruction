# Session 05 — Course submission draft PR and course CI

| Field | Value |
| --- | --- |
| Agent | Claude Code (CLI), model Claude Opus 5.5 (`claude-opus-5-5`) |
| Role | Implementation agent (instructions: `CLAUDE.md`) |
| Session ID | `6bd3c5dd-7710-4a07-85aa-1d556de600c0` |
| Date | 2026-10-26 |
| Repositories | personal `SaadSatter/princeofpersia_reconstruction` (`main`); course `columbia-university-ai-games/game-dev-f26` |
| Transcript | Local only, not committed |

## Student instructions

Inspect the course repository and its contribution instructions; place the
project under `midterms/saadsatter/`; install the course workflow at
`.github/workflows/midterm-saadsatter.yml`, scoped to the folder and with no
secrets; check that no keys, transcripts, unrelated files or original assets
are included; open a **draft** PR on a separate branch; verify the course CI
run; record the result here. Do not change mechanics, evaluation cases,
baseline or prompts. Do not merge or mark the PR ready without approval.

## What the course repository requires

- Course repo default branch: `main`. The account `SaadSatter` has Write
  permission, so the branch was pushed to the course repo directly (no fork).
- No midterm-specific contribution guide or PR template exists in the course
  repo (only `.github/PULL_REQUEST_TEMPLATE/minigame.md`, for the Get Out lab).
  The hand-in steps in `docs/MIDTERM_GUIDELINES.md` ("Hand-in" section) were
  followed: branch `<login>/midterm`, only `midterms/<login>/` plus
  `.github/workflows/midterm-<login>.yml`, PR targeting `main`.
- The course root `pyproject.toml` defines no uv workspace, and the course's
  own workflows run only root-level tests, so the project folder installs and
  tests on its own lockfile.

## What was transferred

- Source: `git archive e2e806e` of the personal repo, extracted into
  `midterms/saadsatter/` unchanged (81 tracked files). Untracked files were
  not copied: the three local conversation transcripts, `.venv/`, caches,
  `vendor/`, `data/levels/`, and `tools/decode_levels.py` (never committed).
- Workflow: `ci/midterm-saadsatter.yml` copied byte-for-byte to
  `.github/workflows/midterm-saadsatter.yml`. Triggers only on paths
  `midterms/saadsatter/**` and the workflow file (plus manual dispatch);
  `working-directory: midterms/saadsatter`; `permissions: contents: read`;
  `persist-credentials: false`; no `secrets.*`; runs `uv sync --frozen` and
  `uv run --frozen pytest -q` on Python 3.11 and 3.12.
- PR diff: 82 files, all under `midterms/saadsatter/` except the one workflow.

## Pre-push checks

| Check | Result |
| --- | --- |
| Secret patterns (`sk-ant-…`, `sk-…`, `AIza…`, `gh*_…`, private keys) in tracked files | Only fake test values (`sk-ant-FAKE-…`, `test-key-not-real`) in `tests/` |
| Absolute local paths, email addresses | None |
| Binaries / images / sound / fonts / original level files / files > 200 KB | None |
| 6502 assembly lines in tracked files | None |
| Workflow commands rehearsed in the course layout, no API keys in the environment | 118 passed, 1 skipped (the skip needs the `model` extra) |

## Branch, commit and PR

- Branch: `saadsatter/midterm` in `columbia-university-ai-games/game-dev-f26`
- Commit: `b78c7767b57ca7e13178ab4868a917b9736dfc56` (on base `66f051b`)
- Draft PR: https://github.com/columbia-university-ai-games/game-dev-f26/pull/57
  (draft; not marked ready; not merged)

## Course CI result for `b78c776`

| Workflow / job | Event | Result | Run |
| --- | --- | --- | --- |
| `midterm-saadsatter`, Python 3.11 and 3.12 | pull_request | **pass**, 118 passed, 1 skipped (each) | https://github.com/columbia-university-ai-games/game-dev-f26/actions/runs/40387697770 |
| `midterm-saadsatter`, Python 3.11 and 3.12 | push | **pass** | https://github.com/columbia-university-ai-games/game-dev-f26/actions/runs/40387642148 |
| Course `Setup and deterministic checks` (starter tests) | push, pull_request | pass | runs 40387642071, 40387697766 |
| Course `Minigame lab` | push, pull_request | pass | runs 40387641851, 40387697849 |
| Course `Minigame submission boundaries` | pull_request_target | **fail** | https://github.com/columbia-university-ai-games/game-dev-f26/actions/runs/40387697882 |

The boundaries failure message: "A student variation PR may change only its
author's game folder. Instructor-owned files need an instructor PR. Outside
scope: .github/workflows/midterm-saadsatter.yml". This guard was written for
the Get Out lab and rejects the one workflow file the midterm hand-in
requires. The other midterm draft PR (#55) fails the same check for the same
reason. Shared course tooling was not changed or bypassed; a course
maintainer needs to resolve it.

## Not done in this session

- No game mechanics, evaluation suite, baseline, prompt or test was changed.
- The personal repo's `REQUIREMENTS_CHECKLIST.md` and `EVALUATION.md` "CI
  evidence" section were not updated with these run links.
- No README exists yet; the PR description says so instead of linking one.
