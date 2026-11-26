# T23-fix2: approved test edits and a clean branch (#113, #114)

Handoff id: HO-T23-fix2-orchestrator. Assigned: tech-lead (same agent); then qa (Gate 1, with its four #99 updates), evaluation-specialist (Gate 2), Gate 3.
Input: `reports/T23-fix1-tech-lead.md`@5756e25 on `task/T23-fix1`.

1. **Clean base (orchestrator's correction).** Merging 0c7d73a into dfe2d90 brought in 126 main-line commits (`.claude/**`, `AGENTS.md`, orchestration records), which do not belong on the gameplay line. Make a new branch `task/T23-fix2` from `dfe2d90` and cherry-pick only the T23 and T23-fix1 work: 987a0ad, 455dfb0, 0c7d73a (report), then the T23-fix1 commits after 6041f6c. Confirm with `git diff --name-only dfe2d90..HEAD` that only T23 files change. Leave `task/T23-fix1` as it is.
2. #113: `tests/test_server_match.py::test_the_input_trace_replays_to_the_same_outcome_and_state_hash` replays through `server.trace.replay(tr)`.
3. #114: `tests/test_t22fix2_overlap.py::test_ai_room_logs_only_the_human_seat` accepts a `rematch` row after `duel_end`.
4. List both edits old → new. Leave the four QA T20 tests for QA (#99).
5. Suite on the committed clean tree, with the real line (only those four QA tests may fail).

Permitted writes: those of T23-fix1, plus the two tests above (only those assertions), and `reports/T23-fix2-tech-lead.md`.
