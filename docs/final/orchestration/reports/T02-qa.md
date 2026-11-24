# T02 report (QA), 2026-11-23 — condensed by the orchestrator

Status: done. Branch `task/T02` (/home/claude/sm/wt/T02), base 721b3e6 (code tree = 13c7488): 90cb251 tests, f8583d6 review + handoff draft.
Files: tests/test_qa_t02_r_v23.py (18 tests; pass on 13c7488; 8 fail on pre-fix 7b38b65); tests/test_qa_t02_disguise_tells.py (15 tests; 10 pass, 5 xfail strict T02-F1/F2/F2b); docs/reviews/INDEPENDENT-REVIEW-r-v23-and-f1-2026-11-24.md; docs/final/orchestration/handoff-drafts/2026-11-24-qa-to-tech.md (Student decision empty).
Tests: 447 passed, 12 skipped, 5 xfailed. test_flip_review.py on 7b38b65: 12 failed, 14 passed (matches the fix commit's claim).
Verdict: ACCEPT WITH NOTES for the R-V23 fixes (all 2026-11-18 blocking/should-fix findings closed; notes kept by Saad; one partial until T05). F1 and F2 routed to T01.
Findings: F1 major (disguised WAIT motion); F2 major (R-V24 not built at 13c7488); F2b minor/design (DOWN none/4, no decision); F3 minor (settle can send the mover back to came_from: full row, or both rivals' settle cells equal; docstring says never — small unlisted leak, pop/versus.py:645-654); F4 minor (_replan cancels a run-jump into an out-of-sight body instead of re-planning, last_result None, pop/versus.py:661-670); F5 minor/design (rivals out of sight swap through each other across a doorway); F6 minor/design (settle can carry the mover across holes, spikes, bodies); F9 minor (stale/replaced inputs, = AUDIT-B F3); F7, F8 cosmetic (spec wording, stale docstrings).
Decisions for Saad: Student decision on the handoff; DOWN while disguised; R-V24 amount; F3–F6 acceptable?; F9; removing xfail marks once fixes land.

Orchestrator integration trial (T01 83127cf + T02 + T04 + T11): the 5 T02 strict xfails now XPASS, i.e. QA's own tests confirm T01 closes F1, F2 (R-V24) and F2b (crouch masked by R-V25). Follow-up: QA removes the xfail marks after Gate 1 on T01.
