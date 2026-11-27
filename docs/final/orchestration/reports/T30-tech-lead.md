---
handoff_id: HO-T30-tech-lead
task_id: T30
date: 2026-11-27 ET
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T30.md@a293773
source_branch: task/T30
source_commit: 400819e5e1b9daa4d57e01806db30471ff65c3eb (first commit; one later commit fixes freeze wording and adds this report, see git log of task/T30)
reviewed_commit: n/a
verdict: n/a
---

# T30: tech-lead report

Status: done

## Work completed
Refreshed `docs/final/SCOPE_LOCK.md` per decision #123 (nine rules). Still a draft, blank approval line kept. No PR, no copy to official PR #2.

## Paths
`docs/final/SCOPE_LOCK.md` (only); this report.

## Acceptance criteria → evidence
| # | Rule | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Stale lines updated with evidence; "only if gates close by Friday" removed | yes | In-scope rows for T23/T23-fix1 (41550f9, PR #12 4e20b83), CI (4e20b83; run 46038977033 on 271d1ee, from REVIEW_LOG), three-mode menu/kneel/online polish, Pages run 46040177615 with DNS pending. Limitations rows "CI red until PR #12" and "not on main" removed; Freeze section rewritten |
| 2 | External playtest pending until Saad conducts it | yes | Limitations table |
| 3 | LAN suffices; public server not required | yes | In-scope LAN row; Out-of-scope row says "not excluded forever" |
| 4 | PPO retrain, AI RIG_TRAP, movement/scroll, other gameplay moved to "Deferred" section with the required title; #118 freeze kept | yes | New section after Out of scope |
| 5 | Telemetry/BI agent listed as possible third G4 role | yes | New section "Possible third production role for G4" |
| 6 | T09 result kept verbatim | yes | 13 W, 2 D, 1 L of 16, bar 14, NOT SUPPORTED; added "threshold not changed" |
| 7 | Hosted frontend distinct from LAN server | yes | Both in-scope rows and the devtools limitation |
| 8 | Baseline header line | yes | "Scope baseline (decision #123)" paragraph under the draft line |
| 9 | Draft and blank approval line kept; nothing in Saad's voice | yes | Header unchanged; #123 only cited |

## Tests run
```
uv run pytest -q   (no extras)
13 errors during collection (numpy missing; CI installs --extra train --extra online)
uv run --frozen --extra train --extra online pytest -q
3 failed, 2296 passed, 48 skipped, 5 xfailed, 2 warnings in 505.98s (0:08:25)
```
The change is one markdown file. The 3 failures are in `tests/test_qa_T08_probes.py` (on rerun: the ledger-bypass test, `cli.main` returned 2 where 0 was expected; the ledger-line test, "DID NOT RAISE KeyboardInterrupt"). I did not diagnose them or run them on the base commit. I assume they are environmental (untracked held-out or ledger files in a fresh worktree), but that is unverified.

## Findings
Scope check: `git diff --name-only a293773..HEAD` = `docs/final/SCOPE_LOCK.md` plus this report.
Sources: 271d1ee, 4e20b83, 41550f9 are in `main` history; run ids 46040177615 and 46038977033 come from REVIEW_LOG lines 270-271 and were not re-queried on GitHub.

## Known limitations
The brief names "CI green on main (PR #12 merge 4e20b83, T29)"; the only run id in the records is 46038977033 on 271d1ee, so I cited that.

## Unresolved findings
The 3 test failures above (unrelated to a docs-only change, not diagnosed).

## Requested next action
Commit to review: HEAD of task/T30 (see git log; the first work commit is 400819e)
What changed: scope lock text only, no code.
How to check it: read `docs/final/SCOPE_LOCK.md`; verify each cited sha, run id and decision number; compare with #123 in `DECISIONS-2026-11-26.md` (lines 80-95).
What I am unsure about: the 3 test failures; whether run ids taken from REVIEW_LOG without a live query suffice; the wording "T23-fix1 landed before the freeze".
Touches the knowledge boundary or AI seat: no (Gate 2 does not apply)

## Student decision required
Approval of the refreshed scope lock is Saad's, after QA and Gate 3. Not answered here.

## Update after QA
QA N1 fixed: `SCOPE_LOCK.md` now cites push run 46040129893 (success on `main` 271d1ee), not 46038977033 (a workflow_dispatch on `orch/pr13-merge`), and says the last completed push runs on `main` succeeded (N2). No other change. The mentions of 46038977033 above are the original, superseded evidence. I did not re-query GitHub; the run id is from QA's note.
