# GATE-T05: independent review of the macro layer and scripted baseline
Gate 1: `agents/qa.md`. Gate 2: `agents/evaluation-specialist.md`. These are separate subagents.
Commit: `19b5da2` on task/T05: `git clone -q /home/claude/sm/wt/T05 /home/claude/sm/wt/<gate-id> && cd ... && git checkout -q 19b5da2`. Leave /home/claude/sm/wt/T05 untouched.
Inputs:
- `/home/claude/sm/orch/tasks/T05.md` (brief and acceptance);
- `/home/claude/sm/orch/reports/T05-T06a-T14-T02close.md` (implementer report, T05 section);
- `docs/final/MACROS.md` in the clone.
Known noise: the 5 XPASS failures in `tests/test_qa_t02_disguise_tells.py` come from the base (closed in task/T02-close). Ignore them.
Permitted writes: new tests `tests/test_gate_t05_<qa|eval>_*.py` on `gate/T05-<qa|eval>`; failing ones marked `xfail(strict=True, reason="GATE-T05-<id>")`.

QA focus:
- every acceptance criterion;
- the executor never sends an illegal input over long randomised duels in every room;
- failure reporting and cooldown;
- determinism including the fast path;
- swap-a-guard over full trajectories, not just short sequences;
- the baseline against itself (mirror match, seats swapped) and against a RandomController;
- compatibility with TAKE always legal: merge `task/T01-fix1` from `/home/claude/sm/wt/T01-fix1` into a scratch clone and run the suite.

Evaluation Specialist focus:
- **Boundary.** Does any macro or tracker use something a human could not see: ids, ordering, counts, or the legal list as a probe after R-V26?
- **Fairness.** Is the baseline competent (G1: "nearest uniform, shortest path toward target, adjacent strike") and not deliberately weak? Are its tells the human-visible ones?
- **Suitability as the PPO comparison opponent.** Same macro vocabulary and cadence.
- **Held-out integrity.** Were thresholds tuned on held-out starts? Check MACROS.md and the commit history.
- **SEARCH.** Is it needed, and does it leak?
- **Confounds** for scenarios D1, B2, I3, F5, H6.

Return the verdict block from your role file. Be concise.
