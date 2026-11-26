# T09-fix1: wording and status fixes to the T09 results (docs only, decision #84)

Handoff id: HO-T09-fix1-orchestrator. Assigned: **evaluation-specialist** (the author of RESULTS-T09.md); then `qa` (Gate 1), then Gate 3. Corrective attempt 1 of 2 for T09.
Read first: `reports/T09-qa.md`@25df2ca (N1 to N6); `reports/T09-rules-reviewer.md` on `main` (findings 1 to 8); decisions #77, #80, #84.
Base: `gate/T09-qa` 25df2ca. `git switch -c eval/T09-fix1 25df2ca`.

**No run of any kind on H6, not even a replay with a policy; the ledger, results, traces and analysis files are not edited.** No code or test edits.

Edit `docs/final/evaluation/RESULTS-T09.md` (and the matching lines of your report) so that:
1. (#84, reviewer 1) "0 errors" is stated as runner-level only: "PPO inference errors (caught inside the controller and answered with WAIT) were not recorded in the held-out rows; T08-fix2 adds them for future runs."
2. (reviewer 2, QA N1) one sentence: PROTOCOL H-c ("0 stale for both seats") is not met as written on H6 (PPO 21, baseline 18); #80 relaxed it for the step-1 health check only, and on H6 the counts are reported.
3. (reviewer 3, QA N2) the fall mechanism for stale inputs is "shown for the baseline on the tuning split; not verified for the PPO seat".
4. (reviewer 4) replace "13 wins is below 14 either way" by: none of the three non-wins (H6-1 MvS, H6-2 SvM, H6-8 SvM) has a stale input on either seat, so stale inputs do not explain the shortfall; the claim stays "not shown", not "would have reached 14".
5. (reviewer 5, QA N3) label the fall counts "not independently reproduced" (no committed script), and note H6-8 SvM had 3 falls each.
6. (reviewer 6) state that H-a ("wins more than it loses") is not the pre-registered criterion, that no strength claim is made, that the Wilson interval is optimistic (effective n near 8) and that the baseline line is its complement, not independent evidence.
7. (reviewer 8) the two draws: "stalemate; cause not analysed".
8. (QA N4) one clear sentence on the seat/position confound (the 7 vs 6 split is not evidence of a seat effect).
9. `docs/final/evaluation/PROTOCOL.md`: **status lines only**: lines 5-6 ("No held-out result exists. T09 runs H6 once") and §4.6 tense, pointing to RESULTS-T09.md, and one line under H-c citing #80. No rule, bar or definition changes.
10. (QA N5) a session record in `docs/agent-sessions/` (one new file).

Permitted writes: `docs/final/evaluation/RESULTS-T09.md`, `docs/final/evaluation/PROTOCOL.md` (status lines only, as above), `docs/agent-sessions/` (one new file), `docs/final/orchestration/reports/T09-fix1-evaluation-specialist.md`. Commit, push (no force), `to: qa`.
Gates: QA (`gate/T09-fix1-qa`: every item addressed, nothing else changed, `git diff --name-only 25df2ca..HEAD` within paths, evidence files byte-identical), Gate 3.
