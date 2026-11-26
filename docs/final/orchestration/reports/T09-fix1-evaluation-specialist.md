---
handoff_id: HO-T09-fix1-evaluation-specialist
task_id: T09-fix1
date: 2026-11-25
from: evaluation-specialist
to: qa
consumed: HO-T09-fix1-orchestrator (tasks/T09-fix1.md@c325f9e); reports/T09-qa.md@25df2ca (N1-N6); reports/T09-rules-reviewer.md (1-8); decisions #77, #80, #84
base: 25df2ca (gate/T09-qa), branch eval/T09-fix1
verdict: wording and status fixes made; no result, bar or evidence changed
---

# T09-fix1: wording and status fixes

Docs only. No run of any kind on H6 (no policy, no replay). Ledger, refusals, results, traces, code and tests not edited. No test suite run (docs only).

| item | finding | file, place | change |
| --- | --- | --- | --- |
| 1 | reviewer 1, #84 | RESULTS-T09.md, "The odd rows", last bullet | "0 errors" stated as runner-level only; PPO inference errors (WAIT) not recorded in rows; T08-fix2 adds them |
| 2 | reviewer 2, N1 | RESULTS, "Stale inputs and falls", first sentence | H-c not met as written on H6 (PPO 21, baseline 18); #80 relaxed it for step 1 only; counts reported |
| 3 | reviewer 3, N2 | RESULTS, stale-mechanism sentence | "shown for the baseline on the tuning split; not verified for the PPO seat", with the four cells named |
| 4 | reviewer 4 | RESULTS, last sentence of that section | "13 is below 14 either way" replaced: none of H6-1 MvS, H6-2 SvM, H6-8 SvM has stale on either seat; claim stays "not shown" |
| 5 | reviewer 5, N3 | RESULTS, falls sentence | labelled "not independently reproduced"; H6-8 SvM 3 falls each added |
| 6 | reviewer 6 | RESULTS, new section "Status of H-a and the intervals" | H-a is not the pre-registered criterion; no strength claim; interval optimistic (effective n near 8); baseline line is the complement |
| 7 | reviewer 8 | RESULTS, two draw bullets | "Stalemate; cause not analysed." |
| 8 | N4 | RESULTS, Confounds, position bullet | seat A 7W 1D 0L vs seat B 6W 1D 1L (8 each) is not evidence of a seat effect |
| 9 | reviewer 7 | PROTOCOL.md header (lines 5-6), section 4.6, one note under H-c | status lines only, pointing to RESULTS-T09.md; H-c note cites #80; no rule, bar or definition changed |
| 10 | N5 | docs/agent-sessions/T09-fix1-wording.md | new session record |

Not done: nothing skipped. The earlier `T09-evaluation-specialist.md` (line 29, "0 errors") was left unedited (outside the permitted paths); RESULTS-T09.md now carries the correction. N6 (`to:` label) is addressed by `to: qa` here.
