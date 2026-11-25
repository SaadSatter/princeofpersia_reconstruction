---
task: T09-fix1
from: qa
to: orchestrator
consumed: docs/final/orchestration/reports/T09-fix1-evaluation-specialist.md@fbce328 (HO-T09-fix1-evaluation-specialist)
reviewed_commit: fbce328 (origin/eval/T09-fix1, base 25df2ca)
verdict: ACCEPT
---

# T09-fix1 QA (Gate 1)

**Verdict: ACCEPT.** No blocker, major or minor finding. No H6 run of any kind, no ledger or evidence write.

Suite, clean tree at fbce328: `uv run --frozen --extra play --extra train --extra online pytest -q` gives
**1778 passed, 11 skipped, 5 xfailed, 2 warnings in 293.44s (0:04:53)**. (1767 at 25df2ca plus 11 from the earlier QA probe test, which that base already carries.)

## Criteria

| item | met | evidence |
| --- | --- | --- |
| 1 "0 errors" runner-level only | yes | RESULTS "odd rows" last bullet: PPO inference errors caught and answered with WAIT were not recorded; T08-fix2 adds them (#84) |
| 2 H-c not met as written | yes | one sentence, PPO 21 / baseline 18, #80 step-1 only. Recomputed from results.json: 21 and 18 |
| 3 mechanism baseline only | yes | "shown for the baseline on the tuning split; not verified for the PPO seat", four cells named. I mapped seats (A is the baseline in SvM): the PPO cells with stale are exactly H6-2 MvS, H6-5 MvS, H6-6 SvM, H6-7 SvM |
| 4 non-wins have no stale | yes, true | results.json stale_inputs for H6-1 MvS, H6-2 SvM, H6-8 SvM are 0/0 on both seats (also H6-1 SvM, H6-8 MvS). Sentence keeps "not shown", not "would have reached 14". Per-cell table matches the data cell by cell |
| 5 falls not reproduced, H6-8 SvM 3 each | yes | wording added; 3/3 matches the unchanged fall list |
| 6 H-a, interval, baseline complement | yes | new section; lower bound 0.57, effective n near 8, baseline 1W 2D 13L is the complement |
| 7 draws | yes | "Stalemate; cause not analysed." on both |
| 8 seat/position confound | yes | 7W 1D 0L vs 6W 1D 1L, 8 each, not evidence of a seat effect |
| 9 PROTOCOL status only | yes | line-by-line diff: three hunks only: header status text (lines 5-9), one "Status note" under the H-c table citing #80, section 4.6 item 6 tense ("ran ... result is in RESULTS-T09.md"). The H-c, H-a, bar and definition lines are untouched. The text "the rules below are unchanged" is accurate |
| 10 session record | yes | `docs/agent-sessions/T09-fix1-wording.md` added, one file |
| Paths | yes | `git diff --name-only 25df2ca..fbce328`: the agent-sessions file, PROTOCOL.md, RESULTS-T09.md, the evaluation-specialist report. Nothing else |
| Evidence byte-identical | yes | `git diff --stat 25df2ca fbce328 -- evaluation tools pop agents tests` is empty (results, traces, analysis, ledger, code, tests) |
| Nothing else changed in meaning | yes | the RESULTS diff has only the listed edits; verdict line, counts and tables are untouched |

## Question: the earlier report line 29 ("0 errors")

`T09-evaluation-specialist.md` still says "0 errors", left unedited by design. RESULTS-T09.md carries the correction, and RESULTS is the document readers cite, so this is enough. Optional for Gate 3: a one-line pointer in the REVIEW_LOG that the earlier report's "0 errors" is superseded by RESULTS-T09.md and decision #84. I do not require it.

## Not checked

Falls (25 vs 37) remain not re-derived (now labelled as such). PPO inference errors are not in the rows, so cannot be checked from the files.
