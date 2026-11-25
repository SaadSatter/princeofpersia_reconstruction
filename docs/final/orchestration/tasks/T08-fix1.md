# T08-fix1: decisions #64, #65, #74–#77 and the T08 gate findings

Handoff id: HO-T08-fix1-orchestrator. Assigned: tech-lead; then qa (Gate 1), evaluation-specialist (Gate 2), Gate 3. Corrective attempt 1 of 2 for T08.
Read first: `tasks/T08.md`@0bba440 (with its amendment); `reports/T08-tech-lead.md`@deb8718; `reports/T08-qa.md`@cf43ba1 (F-1 to F-4); `reports/T08-evaluation-specialist.md`@059aea5 (E-1 to E-6 and its proposed fix list); decisions #58–#61, #64–#66, #74–#77 in `DECISIONS-2026-11-24.md` on `main`.
Base: `gate/T08-eval` 059aea5 (T08 + QA probes + Eval test). `git switch -c task/T08-fix1 059aea5`. Paste the base's suite line.

## Fix list (failing test first for each)

1. **#64 run-once key**: the ledger key is (weights SHA-256, engine commit). A second held-out run for the same pair is refused. A real held-out run is refused on an unknown commit or a dirty tree, counting untracked files under `evaluation/` and `tools/eval/`. Every run (claimed or refused) is recorded.
2. **QA F-1** (before item 3): D1 credits a guard only if the agent struck it, or was in the guard's room when it went down.
3. **#65 seat-B starts**: mirrored starts for D1, B2, I3 and F5-a/b with the subject in seat B, tuning split only, and per-seat analysis.
4. **QA F-2**: `duel_results` tolerates `controllers: {}` and lists those rows as aborted (#24). **QA F-4**: `--replay` reads `split` from the trace's `meta.json`.
5. **#76 B2**: success also requires the subject still disguised at the end. Keep the threshold 50 a named parameter and `success_active` reported, not scored (#66).
6. **#74 H6 to 8 starts**: first commit a written selection rule (in `docs/final/evaluation/PROTOCOL.md` or `evaluation/heldout/README.md`), then add H6-5 to H6-8 by that rule: rival start cells disjoint from the 8 `TUNING_STARTS`, every tuning scenario, `arena.STARTS` and the existing H6 starts, and no H6 configuration (both starts plus guard layout) equal to a training or tuning configuration. Never consult policy or baseline results on the new starts. Re-freeze `H6.json` and record the new SHA-256 in all three places. Do not run any policy on H6; for schema tests, WAIT seats or scripted seats with a small frame cap and a temp ledger only.
7. **Docs (#75, #77, E-6)**: PROTOCOL.md section 3 and the H6 README say start cells and guard post tuples are disjoint and patrol ranges are not, and the claim is "unseen start pairs and guard layouts". The pre-registered T09 bar: at least 14 of 16 held-out duels won and no aborted duel; below that, "not supported", with the full numbers. Under H-b: the PPO rival was trained for duels only, so the skill scenarios are a result, not a defect. Wilson intervals for the new sizes.
8. Optional (Eval item 6): an evaluator-side script that generates the F-3 exposure table.

## Tests you may change

- `tests/test_qa_T08_probes.py`: remove the strict `xfail` marks of F-1, F-2 and F-4 once they pass. Change nothing else in it.
- `tests/test_eval_T08_gate2.py` pins the F-3 exposure numbers and the Wilson table for the 4-start H6. **Do not edit it.** If item 6 breaks it, say which assertions and why in your report; its author updates it at Gate 2 (as in T16 and T17).
- No other existing test.

## Limits

Permitted writes: `evaluation/**`, `tools/eval/**`, new tests `tests/test_eval_t08fix1_*.py`, the two test files above as stated, `docs/final/evaluation/**`, `docs/agent-sessions/` (one new file), `docs/final/orchestration/reports/T08-fix1-tech-lead.md`. Not `pop/`, `agents/`, `tools/rl/`, `play.py`, `render/`, `web/`, `server/` (T19 is changing the engine and front ends in another session). No training, no `--live`, no PPO run on H6, no write to the real ledger.

Gates: QA (`gate/T08-fix1-qa`), Eval (`gate/T08-fix1-eval`: the new H6 starts and rule, the ledger, the bar), Gate 3. T09 runs only after T08-fix1 and T19 close.

## Amended 2026-11-25 (#78)

Saad allowed the six tests broken by #74 and #65 to be updated by their authors, pinned values only (old and new listed in each report). Tech Lead now: the three tests in `tests/test_eval_registry.py` and `tests/test_eval_suite.py` named in #78. QA at Gate 1: its hash probe. Evaluation Specialist at Gate 2: its two tests in `tests/test_eval_T08_gate2.py`. No other existing-test edit.
