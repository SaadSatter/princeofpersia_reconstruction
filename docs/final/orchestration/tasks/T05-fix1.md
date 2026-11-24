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

---

## Resumed 2026-11-24 14:19 ET (native agents)

The sandbox run of this brief was cut off by the usage limit at about 02:00 ET on 2026-11-24. This note replaces every `/home/claude/sm/...` path above. Setup, commits and tests now follow `tasks/_EXEC_COMMON.md` (your own worktree, `--author` on every commit, no push).

**Decision in force, #31** (`DECISIONS-2026-11-24.md`): Saad chose "CLIMB both ways (Recommended)". Fix 1 is no longer pending. In `MACROS.md`, record `CLIMB` going down as **confirmed by Saad (decision #31)**, not as pending.

**Base.** Branch from `0846a16`, not from `6692771`: `git switch -c task/T05-fix1 0846a16`. That commit is the earlier Tech Lead's failing-tests commit on top of `6692771`. It holds the copied gate files `tests/test_gate_t05_eval_baseline.py` and `tests/test_gate_t05_qa_probes.py`, the new tests in `tests/test_macros.py` and `tests/test_versus_baseline.py`, and the **frozen** `LOWER_HELD_OUT_STARTS`. Before implementing:
1. Check that `git diff --name-only 6692771 0846a16` lists only those four test files.
2. Run the suite and record which tests fail or xfail, and why.
3. Do not change `LOWER_HELD_OUT_STARTS` or the tuning and held-out starts. If one is wrong (for example, unreachable by any legal play), stop and say so in your report; do not edit it.
You may add tests, and fix a test only where it contradicts the brief or a decision. Explain each such fix in your report.

**WIP snapshot.** `orch/wip-T05-fix1` at `ab78522` holds the interrupted, **untested and unreviewed** edits to `agents/macros.py`, `agents/versus_baseline.py` and `tests/test_macros.py`. You may read it (`git show ab78522:<path>`) and reuse ideas. Do not cherry-pick or merge it blindly. Everything you commit must be your own reviewed work, and it must pass the tests.

**Findings to fix (where they are now).**
- Gate 2: `docs/final/orchestration/reports/GATE-T05-eval.md` on `main` (Gap 1 no descent, Gap 2 lone guard, memory disclosure). xfails `GATE-T05-eval-1`, `-2` in `tests/test_gate_t05_eval_baseline.py`.
- Gate 1: the QA report commit `dec85c8` was lost with the sandbox. Its findings are condensed in `docs/final/orchestration/reports/wave2-batch.md` ("GATE-T05-qa"), and its probes are in `tests/test_gate_t05_qa_probes.py` at `0846a16`. Majors: QA-1 mirror-match deadlock (10/10 draws), QA-2 lone-guard rule loses to WAIT, QA-3 SEARCH stays on one row. Minor: `decide` crashes on a `None` or malformed policy tuple. xfails `GATE-T05-qa-1` to `-3`.
- Remove an xfail mark only for a finding you fixed. For a finding you did not fix, keep its mark and say why in the report.

**QA-1 (mirror deadlock).** Add this to the fixes above. Baseline vs baseline must not end 10/10 in a no-hit draw. Report the baseline-vs-baseline result over at least 12 seat-swapped duels. A fix that breaks the symmetry must use only the seat's own observation and its own seeded state. No seat may read the other's identity or seed.

**Report.** `docs/final/orchestration/reports/T05-fix1-tech-lead.md` on `task/T05-fix1`, from `reports/_TEMPLATE.md`, with `consumed: docs/final/orchestration/tasks/T05-fix1.md@<coordination sha>`. Include the competence numbers each acceptance criterion asks for, with seeds, and say whether you used `uv run pytest -q` or the fallback.

**Permitted write paths** (unchanged, plus the report): `agents/macros.py`, `agents/versus_baseline.py`, `tests/test_macros.py`, `tests/test_versus_baseline.py`, `tests/test_gate_t05_eval_baseline.py`, `tests/test_gate_t05_qa_probes.py`, `docs/final/MACROS.md`, `docs/agent-sessions/` (a new file only), `docs/final/orchestration/reports/T05-fix1-tech-lead.md`. Nothing in `pop/`. If a fix needs an engine change, stop and report `blocked`.

**Gates:** Gate 1 `qa` (branch `gate/T05-fix1-qa`), Gate 2 `evaluation-specialist` (branch `gate/T05-fix1-eval`; this changes the baseline and the macro layer), then Gate 3 by the orchestrator. Integration target: `orch/preview` (which already holds T05), via the orchestrator.
