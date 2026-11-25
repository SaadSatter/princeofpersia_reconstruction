# GATE-T04 reports (QA Gate 1, Evaluation Specialist Gate 2), 2026-11-23 — condensed by the orchestrator

Both: **ACCEPT WITH NOTES** on af76c30. Neither saw the other's report.
- QA: branch gate/T04-qa ea165f3, tests/test_gate_t04_qa_adversarial.py (11 passed, 5 xfailed strict). Full: 468 passed, 12 skipped, 5 xfailed. Real won duel through the runner now tested (plain won:A slot A; swapped won:B, winner_slot A; both replay).
- Eval: branch gate/T04-eval eab92a5, tests/test_gate_t04_eval_boundary.py (8 passed, 4 xfailed strict). Full: 465 passed, 12 skipped, 4 xfailed.

Findings routed to the Tech Lead (T04-fix1):
- QA-1 [major] str subclass with permissive __eq__ passes validation; step refuses; runner raises RuntimeError, both seats stop (versus_runner.py:96-97,165-167). Fix: type(value) is str / normalise.
- QA-3 [major] answer whose __repr__ raises crashes the run (versus_runner.py:72-74,104).
- QA-2 [minor] str subclass overriding strip: trace records one input, engine plays another; JSONL replay diverges.
- QA-4 / eval-3 [minor] controller.reset() unbounded on the runner thread.
- eval-2 [medium] after a real timeout the abandoned thread keeps running and decide() is called again concurrently; fix: seat busy -> fallback until the earlier call returns.
- eval-4 / QA cosmetic: BaseException (SystemExit) labelled malformed, not error; VersusLimits(timeout_s=None) unvalidated.
- eval-1 [low] controller_seed is an unkeyed hash, reversible for small seeds (impact small); key it or fix the design-note sentence.
- Both: in-process isolation is by convention (gc.get_objects / sys._current_frames reach the episode): document in VERSUS_RUNNER.md; untrusted controllers need a separate process.
- Orchestrator integration trial: test_controller_gets_only_plain_copies_of_its_own_seat fails on T01 merge (minutes_left 0 vs 5: comparison episode built with another duel limit).
- Eval recommendations: per-frame observer hook for scenario metrics (never fed to controllers); trusted fast path for training (deepcopy ~40%, thread start ~25–30% of runner time); measured ~2,500 decisions/s at cadence 6.
Decision for Saad: QA-5 one controller instance in both seats (recommend refuse with ValueError); cadence 6 / timeout 5 s; aborted vs forfeit (both reviewers recommend aborted, always reported); exact-name validation (keep).
