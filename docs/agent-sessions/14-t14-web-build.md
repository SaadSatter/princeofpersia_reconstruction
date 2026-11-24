# Session 14 — T14 hosted web build (Pyodide + Phaser)

| Field | Value |
| --- | --- |
| Tool / role | Claude Code, Tech Lead subagent (instructions: `docs/final/orchestration/agents/tech-lead.md`, `CLAUDE.md`, `AGENTS.md`), started by the orchestrator |
| Session | `https://claude.ai/code/session_01DktSfuWQ416LWvPbT3AoAS` (from the commit trailer the orchestrator supplied). The transcript id was not extracted: `tools/evidence/extract_sessions.py` was not run in this sandbox |
| Model | `claude-opus-5-5` |
| Date | 2026-11-23 |
| Branch | `task/T14` from `83127cf` (task/T01), in a sandbox clone; not pushed |
| Independence | Builder session. Not a review |
| Brief | `docs/final/orchestration/tasks/T14.md` |

## Saad's instructions in force (quoted from `docs/final/orchestration/DECISIONS-2026-11-23.md`)

- #12: "Pyodide + Phaser (Recommended)"
- #13: "G2/G3, Sat Nov 28"
- #1: "Online play demo it locally, and defer it." (online human vs human stays deferred)

## What was done

- `web/bridge.py` (`WebGame`, `press`, `tick`, `tick_json`, `rematch`;
  modes `human_vs_ai` and `local_two_players`; rival hook with labelled
  placeholders `IdleRival` and `RandomRival`).
- `render/draw_list.py` (one seat's observation -> draws) and
  `render/webart.py` (standard-library PNG reader/writer, art measurements,
  crimson recolour, spike pixels).
- `web/index.html`, `web/main.js`, `web/keys.js` (+ `web/keys.test.js`),
  `web/versions.json`; `tools/web/build.py`, `tools/web/smoke.cjs`;
  `.github/workflows/pages.yml`, `.github/workflows/web-smoke.yml`;
  `docs/final/WEB_BUILD.md`.
- No rule changed, so no rule-map row.

## Commits

| Commit | Message |
| --- | --- |
| `aa66b60` | test(T14): failing tests for the web bridge, draw list, build and page JS |
| `444cb92` | feat(T14): hosted web build: Pyodide bridge, draw list, Phaser page, build and CI |
| (this record's commit) | docs(T14): web build guide and session record |

## Tests

`python3 -m pytest -q -p no:cacheprovider` (sandbox, Python 3.13, pygame
absent): `560 passed, 12 skipped in 6.27s` after the feature commit plus the docs.
Before the feature commit the new tests failed (collection error for
`web.bridge`; 8 failed and 7 errors in the build and JS tests).

## Not verified

The page never ran in a browser: the sandbox cannot fetch Pyodide or Phaser.
Headless Chrome on the built page showed `error: ReferenceError: loadPyodide
is not defined`, as expected. The CI workflows have not run.
