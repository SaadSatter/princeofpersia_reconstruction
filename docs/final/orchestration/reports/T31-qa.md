---
handoff_id: HO-T31-qa
task_id: T31
date: 2026-11-27
from: qa
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T31-tech-lead.md@bd918de
source_branch: gate/T31-qa
source_commit: c1a1abdce207623f6572b04dfe55146aca63a20a
reviewed_commit: d9078593f989da3b55074803175e7e5da2731432 (official g23-migration; 92705af is the CI/README commit)
verdict: ACCEPT WITH NOTES
---

# T31: qa report

Status: done

## Work completed
Cloned the official repository read-only (no push, comment or merge), diffed f306dbc..d907859, compared SCOPE_LOCK.md with this repository's 5c80341, and ran the exact "Your tests" subset from `game/` on a deleted `.venv`. No tests were added (CI/docs-only change, nothing to break beyond the run itself).

## Paths
Reviewed official: `.github/workflows/final.yml`, `README.md`, `game/docs/final/SCOPE_LOCK.md`. `git diff --stat f306dbc d907859` lists exactly these three files. This repository: this report.

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | final.yml changes only the "Your tests" pytest line; `timeout-minutes: 10`, `permissions: contents: read`, no secrets, runner expression unchanged | Met | `git diff f306dbc 92705af -- .github` shows one removed pytest line, one added comment and the file list. Lines 6-7 (permissions), 14 (runner expression) and 15 (`timeout-minutes: 10`) untouched. No `secrets.` in the file. |
| 2 | Subset includes engine-headless test | Met | `tests/test_architecture.py` |
| 3 | Subset includes hidden-info / interface tests | Met | `test_interface`, `test_leakage`, `test_seats`, `test_traps_leaks`, `test_disguise`, `test_gate_t01/t04_eval_boundary`, `test_eval_*boundary` |
| 4 | Subset includes online server-to-client boundary tests | Met | `test_online_boundary`, `test_server_match`, `test_server_ws`, `test_server_fix1_online`, `test_t22_server`, `test_gate_t13_qa_online`, `test_gate_t14_*`, `test_web_bridge`, `test_online_rooms` |
| 5 | Subset includes midterm regression suite | Met | `test_regressions`, `test_rules`, `test_level1*`, `test_levelfile`, `test_frozen_suite`, `test_situations`, `test_guards`, `test_traps`, `test_swordplay` |
| 6 | Every listed file exists | Met | script checked all 38 matches of `tests/test_*.py` in the step: none missing |
| 7 | README: one explanatory paragraph pointing to full suite | Met | `git diff f306dbc 92705af -- README.md`: +2 lines (blank + paragraph) |
| 8 | SCOPE_LOCK.md at d907859 equals 5c80341 here | Met | `shasum` of `git show 5c80341:docs/final/SCOPE_LOCK.md` and of the official `game/docs/final/SCOPE_LOCK.md` are both `6d5e0f9e52e82005278bb1dd84e5957cad211a40` (cmp on identical bytes). Note the file already existed at f306dbc, so d907859 modifies it (+33/-20), not creates it. |
| 9 | Subset passes on a fresh venv, under 4 min | Met | below: 1:51 pytest, 114 s wall including `uv sync` (warm uv cache) |
| 10 | Official CI run state | Queued | see below |

## Tests run
```
cd game; rm -rf .venv; uv sync --frozen --extra train --extra online
uv run --frozen --extra train --extra online pytest -q <files from the step>
574 passed, 8 skipped, 1 xfailed in 111.93s (0:01:51)      wall 114s incl. uv sync
```
Matches the Tech Lead's 574/8/1. Skips are the pygame-dependent tests (no `play` extra); I did not list them individually.

Official CI (`gh run list`, checked 2026-11-27 18:16 UTC): run 46047660306 on head d907859 is `queued` (created 18:12:10Z, about 4 minutes before my check; I did not wait the full 10). Earlier runs 46046347788, 46044541653, 46043723314 and 46041463704 are `cancelled` (superseded by new pushes; they ran 6 to 17 minutes before cancel, so none shows a real result). No official run has completed on the subset yet.

## Findings
No blocker or major findings.

- [minor, unverified] The 10-minute timeout is unproven on the course runner. Earlier official runs lasted 14 to 17 minutes before being cancelled (full suite), and no run of the subset has started. Local 114 s leaves headroom, but checkout (`fetch-depth: 0`), the team steps and a cold uv cache are not in that figure.
- [cosmetic] The Tech Lead report says "36 files"; the step lists 38 (`grep -o` count). Count only.
- [cosmetic] `test_ci_workflow.py` and `test_determinism.py` and `test_runner.py` are in the subset beyond the brief's four categories; harmless, they pass.
- Carried from T03: the setup-uv step needs Saad's knowing acceptance (unchanged by T31).

## Known limitations
Wall time measured on a local Mac, warm uv cache. I did not run the full 2,299-test suite (not part of this change).

## Not checked
Real CI completion on the course runner (queued). Whether the subset is the coverage Saad wants (his call).

## Unresolved findings
Official CI result.

## Student decision required
none

## Requested next action
Orchestrator: Gate 3. Re-check `gh run list -R columbia-university-ai-games/final-saadsatter` once run 46047660306 starts; if it times out, shrink the subset.
