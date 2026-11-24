# GATE-T01 QA report (Gate 1) on T01 83127cf, plus T11 fact-check on e47c996 — condensed by the orchestrator

T01 verdict: **ACCEPT WITH NOTES**. Branch gate/T01-qa 68f58dc, tests/test_gate_t01_qa_disguise.py (exhaustive probe: every standable cell × facing × seat × guard placement × legal input; 21,528 cases, ~690k frames). 83127cf + QA tests: 520 passed, 12 skipped, 3 xfailed. Tests-first order verified commit by commit. AC4 gameplay-neutral: 60-seed fuzz hash 4c236c36daf885f4 identical before and after.
T02 cross-check: merging task/T02 onto 83127cf -> all 5 T02 strict xfails XPASS with real assertions. T02-F1 closed; T02-F2 closed (R-V24); T02-F2b closed by masking (R-V25, Saad to confirm).
R-V24 measured: +6 on each of the hop's 8 frames = 48 per hop; three hops in sight break the disguise.
Findings: QA1 [minor] disguised STEP into the next room shows motion.to null for 8 frames (pop/versus.py:952-956), xfail; QA2 [minor/design] hanging/falling/dead postures as a "guard", xfail; QA3 [minor/design, pre-existing] repeated WAIT beside a guard resets the stillness counter, lingering never applies (idle 96 vs WAIT 0 in 120 frames), xfail; replaced_inputs counts identical repeats (18,260 in fuzz); cosmetic: session record number, VERSUS_SPEC §2.2 outcome keys.

T11 verdict: **ACCEPT WITH NOTES**. Major: CONSENT.md promises a round log (keys, positions) but play.py --versus writes none (only in-memory VersusEpisode.log). Minor: PROTOCOL §4 item 6 outdated after T01 (5-minute default); no session slot for the [R] revised-encounter test between G2/G3 and G4; "observed exactly as a guard" overstated (QA1–QA3); trap event codes assume traps (fine as planning).

Decisions for Saad: R-V25 masking vs suspicion; R-V24 amount (48/hop); QA1–QA3; AC4 and identical repeats; approve removing T02's 5 xfails at integration; trace writer vs consent change.
