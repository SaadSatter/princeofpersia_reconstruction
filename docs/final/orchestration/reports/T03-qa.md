---
handoff_id: HO-T03-qa
task_id: T03
date: 2026-11-27
from: qa
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T03.md@7c4fc1d; reports/T03-tech-lead.md@7809c5c
source_branch: gate/T03-qa
source_commit: 7c4fc1d6b805ded1710f9e24cdb486014b61682a (base; tests are in the commit that holds this report)
reviewed_commit: official final-saadsatter g23-migration a417057ea176860ad4f5c6ce26fb13b193d57e33, then f306dbcb4111b16ab0dd3262bc47ebe245c578c8 (head, PR #2)
verdict: ACCEPT WITH NOTES
---

# T03: QA report (Gate 1)

Status: done. Read-only clone of the official repo; nothing pushed, commented or merged there.

## Work completed
Cloned `g23-migration`, checked a417057 (suite, snapshot, template, handoff, links), then fetched the new head f306dbc (decisions #121/#122) and re-checked it. Added `tests/test_gate_t03_qa_snapshot.py` (skips unless `OFFICIAL_CLONE` is set).

## Paths
`tests/test_gate_t03_qa_snapshot.py`, this report.

## Acceptance criteria -> evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Only allowed files; from `assets/original` only MANIFEST.tsv | Met | `git ls-files` matching `assets/original` prints only `game/assets/original/MANIFEST.tsv`; no `.dat`, `.env`, `.pem`, `.pt`, `.zip`, vendor, `data/levels`, `*conversation*` tracked; no tracked file over 2 MB; 876 tracked files; `game/assets/` holds only `generated/` (own art) and `original/MANIFEST.tsv`. Secret regex hits only two fake test values (`game/tests/test_gate_t04_qa_adversarial.py:149`, `test_regressions.py:179`). `game/docs/agent-sessions/*.md` are the project's session records, not raw transcripts |
| 2 | Template root files preserved except README and final.yml "Your tests" step | Met with a note (N1) | Diff of template initial commit 32fa606 against head, outside `game/`, `agent-team/`, `.claude/`, `.agents/`: only `.github/workflows/final.yml` and `README.md`. AGENTS.md, CLAUDE.md, .gitignore, `team/`, `tests/` untouched. `permissions: contents: read`, no secrets, `persist-credentials: false`, runner expression unchanged |
| 3 | Handoff `agent-team/handoffs/2026-11-24-qa-to-tech.md` byte-identical to 7c4fc1d | Met | `cmp` against `git show 7c4fc1d:docs/final/orchestration/handoff-drafts/2026-11-24-qa-to-tech.md`: identical (also test `test_graded_handoff_identical_to_draft`) |
| 4 | `team validate` / render no drift | Met | f306dbc and a417057: validate prints only the G4 floor warning (`agents=2 origin_notes=0`), rc 0; `render --today from-team-json` rc 0 and `git status` shows no changes; `python3 -m unittest discover -s tests -p "test_team_*.py"`: Ran 111 tests, OK |
| 5 | README links resolve | Met | 17 relative links in README.md, all targets exist (script run on f306dbc and a417057) |
| 6 | Game suite runs from `game/` | Met | see Tests run |
| 7 | Official CI state | Reported, not waited | Run 46043723314 (a417057) is `completed / cancelled`: superseded by the f306dbc push (workflow `cancel-in-progress` for PRs). New run 46044541653 on f306dbc is `queued` (self-hosted runner pending). No pass/fail result exists yet |
| 8 | f306dbc: other-roles.md matches Saad's quoted lines (#121) | Met | Words of all six lines match the quote in `DECISIONS-2026-11-26.md@1a9b513` (producer/design/art/bi/release `student`, narrative `not needed, because ...`, same explanatory text). Layout differs slightly: each explanation sits on a continuation line beginning "— " rather than on the same line (validate accepts it). HTML placeholder comment removed |
| 9 | f306dbc: QA writes limit (#122) | Met | `agent-team/roles/qa.md` `writes: "tests and handoff notes; never production game code"` |

## Tests run
```
cd final-saadsatter/game && uv run --frozen --extra play --extra train --extra online pytest -q -p no:cacheprovider   (a417057 tree)
2373 passed, 14 skipped, 5 xfailed, 2 warnings in 540.85s (0:09:00)

OFFICIAL_CLONE=.official/final-saadsatter uv run --no-project --with pytest pytest -q tests/test_gate_t03_qa_snapshot.py
5 passed
```
f306dbc touches only `agent-team/*` (5 files, no `game/`), so the game suite was not re-run on it.

## Findings
No blocker or major. Reproduced notes:
- [minor] N1 `.github/workflows/final.yml` — the diff is more than the "Your tests" step: a new `- uses: astral-sh/setup-uv@v5` step sits just before it (needed for uv). Expected by the brief: only that step changes. Reproduce: `git diff 32fa606 HEAD -- .github/workflows/final.yml`. Saad should accept it knowingly.
- [minor] N2 CI time and extras: the job has the template's `timeout-minutes: 10`; the suite took 9:00 here (8:06 for the Tech Lead), plus `uv sync` with a cold cache and the team steps. The CI command omits `--extra play`, which the brief's check list includes (skips then differ: Tech Lead 48 skipped without play, 14 with). Risk is a timeout in the official run. Unverified (CI has not run).
- [cosmetic] N3 T03 report says the tracked `game/.github/`, `game/.claude/` and `game/CLAUDE.md` are inert at the root; confirmed they are tracked under `game/` only. Claude Code started at the root reads the template AGENTS.md, as the Tech Lead noted.
- Tech Lead's report criterion 8 ("TBD: Saad" rejected by validate) is resolved by #121.

## Known limitations
Not checked: the official CI result (queued); links inside `game/docs/**` (only README links checked); runtime model; GitHub Pages / CNAME behaviour of `game/CNAME` (inert at root); the Student decision content of the T18 handoff (empty by design, #120).

## Unresolved findings
N1, N2 above (for Saad / Gate 3).

## Requested next action
Orchestrator: Gate 3 on f306dbc; watch run 46044541653 for the timeout risk (N2). If it times out, the fix is the CI step or `timeout-minutes`, which needs Saad's approval since it is a template root file.

## Student decision required
Saad: accept the extra `setup-uv` step (N1) and the CI duration risk (N2); merge PR #2 or not.
