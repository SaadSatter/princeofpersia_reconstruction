# GATE-T04-fix1: re-review of the T04 corrections
Gate 1: `agents/qa.md`. Gate 2: `agents/evaluation-specialist.md`. These are separate subagents.
Commit: `616ba8d` on task/T04-fix1: `git clone -q /home/claude/sm/wt/T04-fix1 /home/claude/sm/wt/<gate-id> && git -C ... checkout -q 616ba8d`.
Inputs: `/home/claude/sm/orch/reports/GATE-T04.md` (the findings), `/home/claude/sm/orch/reports/T04-fix1-tech-lead.md` (the fix report), `/home/claude/sm/orch/tasks/T04-fix1.md` (brief).
Scope:
1. Each finding is really closed. Your original gate tests now pass unchanged; probe around them (variants of each attack).
2. No regression: full suite, and a scratch merge with task/T01 (`/home/claude/sm/wt/T01`) plus task/T01-fix1 if it exists (`/home/claude/sm/wt/T01-fix1`).
3. The new surface:
   - `on_frame` / `EpisodeView`: can anything from it reach a controller?
   - The fast path (`copy_mode="json"`, `threaded=False`): does it weaken isolation, or change results versus the default on the same seed?
   - `seed_key`: is the key ever written out?
   - `busy` semantics: counting, recovery, and determinism under real timeouts.
4. Evaluation Specialist only: suitability of on_frame for scenario metrics (D1 "no other player on screen", B2 suspicion threshold) and of the fast path for PPO rollouts.
Permitted writes: new tests `tests/test_gate_t04fix1_<qa|eval>_*.py` on `gate/T04-fix1-<qa|eval>` in your clone.
Return the verdict block from your role file. Keep it concise.
