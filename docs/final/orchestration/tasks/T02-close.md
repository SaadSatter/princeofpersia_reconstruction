# T02-close: close the QA→Tech handoff loop on the integrated branch
Assigned agent: `agents/qa.md`
Base: `int/wave1` at `03856b9`: `git clone -q /home/claude/sm/wt/INT /home/claude/sm/wt/T02-close && cd ... && git checkout -q -b task/T02-close 03856b9`. The branch integrates task/T01, task/T04-fix1, task/T11-fix1 and task/T02.
Decision: DECISIONS #20, "Yes, remove them (Recommended)". QA removes the 5 T02 xfail marks once T01 is integrated.
Do:
1. Verify each of the 5 XPASS tests passes for the right reason: read the assertion and the observed values.
2. Remove exactly those 5 `xfail` marks in `tests/test_qa_t02_disguise_tells.py`. Change nothing else.
3. Update `docs/final/orchestration/handoff-drafts/2026-11-24-qa-to-tech.md`: add a closing "Evidence" entry. It lists the T01 commits that fixed F1, F2 and F2b, the merge commit 03856b9, the test names now passing, and the full-suite result line. **Leave "Student decision" empty for Saad.**
Permitted writes: those two files only.
Acceptance: full suite shows no failures and no XPASS; report the result line.
