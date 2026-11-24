# T04-fix3: last runner items (Saad's decision #24, wave-2 gate notes)
Assigned agent: `agents/tech-lead.md`. Base: `int/wave2` at cd5c4aa (`git clone -q /home/claude/sm/wt/INT /home/claude/sm/wt/T04-fix3 && cd ... && git checkout -q -b task/T04-fix3 cd5c4aa`).
1. **QA-5, decision #24 ("Accept all").** `VersusRunner` refuses the same controller object in both seats with ValueError. Remove the QA-5 xfail in `tests/test_gate_t04_qa_adversarial.py`.
2. **Eval-1, decision #24.** Keep `seed_key` opt-in in the runner. Document in VERSUS_RUNNER.md that evaluation runs must pass one (the T08 harness does). Change the eval-1 gate test from xfail into a passing test that asserts the keyed seed cannot be recovered, and leave the unkeyed one documented. Explain what you changed.
3. **GATE-w2 race.** Mark a controller in flight at call start, under the registry lock, so that concurrently started runners never call it at the same time. A runner that finds it in flight gives a `busy` fallback. Remove the xfails GATE-w2-QA-1 (`gate/w2-qa`, /home/claude/sm/wt/GATE-w2-qa) and GATE-w2-eval-1 (`gate/w2-eval`, /home/claude/sm/wt/GATE-w2-eval) after copying those gate files in unchanged.
4. Fix the session note wording to "R-V26, QA3 and L2" in `docs/agent-sessions/13-t01-engine-fixes.md`.
Permitted writes: `pop/versus_runner.py`, `pop/seats.py`, `tests/test_versus_runner.py`, the gate test files named above, `docs/final/VERSUS_RUNNER.md`, `docs/agent-sessions/13-T04-versus-runner.md`, `docs/agent-sessions/13-t01-engine-fixes.md`.
Acceptance: failing tests first; full suite green; Handoff to QA block.

---

## Resumed 2026-11-24 (native agents)

The sandbox run of this brief was cut off by the usage limit at about 02:00 ET on 2026-11-24. This note replaces every `/home/claude/sm/...` path above. Setup, commits and tests follow `tasks/_EXEC_COMMON.md`.

**Base.** Branch from `7fe2e9c`, the earlier Tech Lead's tests-first commit on top of `cd5c4aa`: `git switch -c task/T04-fix3 7fe2e9c`. It already holds the gate files copied from the lost branches (`tests/test_gate_w2_qa_probes.py`, `tests/test_gate_w2_eval_probes.py`), the QA-5 xfail removal in `tests/test_gate_t04_qa_adversarial.py`, and the eval-1 change in `tests/test_gate_t04_eval_boundary.py`. Before implementing:
1. Check `git diff --name-only cd5c4aa 7fe2e9c`.
2. Check that each test change matches items 1–3 of this brief.
3. Run the suite, and record which tests fail and why.
The findings behind items 1–3 are condensed in `docs/final/orchestration/reports/wave2-batch.md` ("GATE-w2") and `reports/GATE-T04.md` on `main`.

**WIP snapshot.** `orch/wip-T04-fix3` at `76de25c` holds interrupted, **untested and unreviewed** edits to `pop/versus_runner.py`. You may read it (`git show 76de25c:pop/versus_runner.py`). Do not cherry-pick it blindly.

**Since then.** T05 + T05-fix1 were closed into `orch/reviewed` (2180fea). They change none of your paths, so stay on the `7fe2e9c` base; the orchestrator integrates.

**Permitted write paths:** as above, plus the gate files already in `7fe2e9c` (`tests/test_gate_t04_qa_adversarial.py`, `tests/test_gate_t04_eval_boundary.py`, `tests/test_gate_w2_qa_probes.py`, `tests/test_gate_w2_eval_probes.py`) and your report `docs/final/orchestration/reports/T04-fix3-tech-lead.md`. You may edit these gate files only to remove the xfail marks for findings you fixed, or as item 2 requires. Explain each such edit in the report.

**Thread safety.** Item 3 is a concurrency fix. Its test must fail before the fix, and it must not be flaky: use a barrier or event to force the overlap, not sleeps. Run it at least 50 times and report the count.

**Gates:** Gate 1 `qa` (`gate/T04-fix3-qa`) and Gate 2 `evaluation-specialist` (`gate/T04-fix3-eval`), because it changes the runner. Then Gate 3.
