# T23-fix1: finish the release rule across the server trace and pygame (#93, #99, #100)

Handoff id: HO-T23-fix1-orchestrator. Assigned: tech-lead (the same agent if available); then qa, evaluation-specialist (Gate 2 applies: engine input rule, server trace and replay), Gate 3.
**Starts only after T22 closes** (#100). Base (decision #105, 2026-11-26): `orch/reviewed` dfe2d90 with `task/T23` 0c7d73a merged in: `git switch -c task/T23-fix1 dfe2d90 && git merge --no-edit 0c7d73a`.

1. `server/match.py` and `server/trace.py`: record each human release in the input trace, so replay gives the same outcome and state hash. `tests/test_server_match.py` passes unchanged.
2. `play.py`: call `ep.release(seat)` in its own input loop, so pygame and `--playtest` have the fix.
3. #99: the Tech Lead updates its one T20 assertion. QA updates its four at Gate 1. List each change old → new.
4. Confirm that AI seats never call `release`, and that the T19 compare set gives identical traces.
5. Suite green on a committed, clean tree, with the real line pasted.

Permitted writes: those of `tasks/T23.md`, plus `server/match.py`, `server/trace.py`, `play.py` (the one input hook), `tests/test_t20fix1_recorder.py` (the one assertion), new `tests/test_t23fix1_*.py`, and `docs/final/orchestration/reports/T23-fix1-tech-lead.md`.
