# T05-fix1: macro reachability and baseline fixes (gate findings)
Assigned agent: `agents/tech-lead.md`. Setup: `_EXEC_COMMON.md`. Base: `int/wave2-t05` at `6692771` (int/wave2 + T05), which already includes T01-fix1/fix2 (TAKE always legal) and T04-fix2: `git clone -q /home/claude/sm/wt/INT /home/claude/sm/wt/T05-fix1 && cd ... && git checkout -q -b task/T05-fix1 6692771`.
Findings: `/home/claude/sm/orch/reports/GATE-T05-eval.md` and the QA gate report, if present (`/home/claude/sm/orch/reports/GATE-T05-qa.md`). Decision #23 (vocabulary approved: BLEND, DISGUISE, WAIT, FOLLOW, STRIKE, FLEE, CLIMB, SEARCH). Do not add macro names.
Fix:
1. **CLIMB goes both ways.** It climbs up an edge, and it also climbs down or drops safely where the engine allows a survivable descent (hang and drop, or an existing ledge). The orchestrator's reading is that G1's "climb" covers both directions. State this in MACROS.md as pending Saad's confirmation.
2. **Planning across floors.** RoomView/plan_path treat survivable drops as moves, not as death. Use the engine's real fall rules from the observation's tiles and edges only.
3. **SEARCH** explores every reachable room, including lower floors, using only the seat's own memory of visited rooms.
4. **FLEE** may also leave vertically.
5. **Baseline rule 5.** Do not engage a lone armed guard unless the matchup favours it (for example hp ≥ 3 and the guard knocked down or unarmed, or a sweep opening). Otherwise blend or avoid. Make DISGUISE reachable: the baseline must be able to get a uniform from the default start.
6. **DISGUISE with R-V26.** TAKE is now always legal. Use the `last_result` effect `no_uniform` (acting seat only) instead of the legal-list probe.
7. **Disclose the baseline's memory** in MACROS.md: what it keeps and for how long.
Gate tests: copy `tests/test_gate_t05_eval_baseline.py` from `git -C /home/claude/sm/wt/GATE-T05-eval show gate/T05-eval:tests/test_gate_t05_eval_baseline.py`, plus the QA gate file if it exists (`gate/T05-qa` in /home/claude/sm/wt/GATE-T05-qa). Remove the xfail marks only for the findings you fix.
Acceptance (failing tests first):
- From the default arena start, the baseline reaches rooms 4 and 5 and obtains a uniform in most seeds (report the numbers).
- It finds a WAIT rival in rooms 4–6.
- It does not die to a lone guard 8/8.
- Every input is still legal; determinism holds.
- Re-run the competence table on tuning starts and on new held-out starts that include lower rooms. Fix the held-out list in the failing-tests commit before implementing.
- Full suite green; Handoff to QA block.
Permitted writes: `agents/macros.py`, `agents/versus_baseline.py`, `tests/test_macros.py`, `tests/test_versus_baseline.py`, the copied gate files, `docs/final/MACROS.md`, `docs/agent-sessions/`.
