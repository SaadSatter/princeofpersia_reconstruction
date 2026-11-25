# GATE-wave3: reviews of T06b (traps), T07 (PPO stack, before full training), T14-fix1 (web corrections)
Each subagent reviews only the parts assigned in its prompt, as Gate 1 (`agents/qa.md`) or Gate 2 (`agents/evaluation-specialist.md`).
Commits:
- T06b `4e9121b` (code 9af96a9) on task/T06b in /home/claude/sm/wt/T06b, base cd5c4aa;
- T07 `1e34cf2` on task/T07 in /home/claude/sm/wt/T07, base 6692771 (int/wave2-t05);
- T14-fix1 `ca3667b` on task/T14-fix1 in /home/claude/sm/wt/T14-fix1, base 4bbabec (int/wave2-web).
Clone each into your own worktree (`git clone -q <task worktree> /home/claude/sm/wt/<gate-id>-<task>`). Never edit the task worktrees.
Inputs: the briefs (`/home/claude/sm/orch/tasks/T06b.md`, `T07.md`, `T14-fix1.md`), the implementer reports (`/home/claude/sm/orch/reports/wave2-batch.md`), the spec `docs/final/TRAPS_SPEC.md` (in the T06b clone), DECISIONS #12–25.
Permitted writes: new tests `tests/test_gate_w3_<qa|eval>_<task>_*.py` on `gate/w3-<qa|eval>-<task>` in your clones (failing ones xfail strict).
Focus:
- **T06b (QA).**
  - Every spec rule and the decision #22 choices.
  - Adversarial rig placement (edges, doorways, bodies, landing cells, both seats, disguised).
  - Spring timing; double rig; one-shot; the 1-heart rule.
  - Determinism; frozen suite.
  - A scratch merge with T05 and T07 (int/wave2-t05 + T06b) to check that nothing breaks.
- **T06b (Eval).**
  - The ownership leak boundary: tiles, `my_traps`, legal actions (does RIG legality reveal another seat's rig? the spec says the same rig is allowed per seat), outcome, last_result, guards' reactions, suspicion side channels, and the kneel masking.
  - Whether a PPO encoder could learn the other seat's rigs from anything it observes.
- **T07 (QA).**
  - Encoder, mask, PPO math (GAE, clipping, advantage normalisation), parity, hash checks, determinism with 1 and 2 workers, and the smoke run.
  - `tools/rl/env.py` uses `on_frame` true state only for reward and never for features.
- **T07 (Eval).**
  - Feature boundary.
  - The nearest-target rule and its effect on I3.
  - Shaping terms and how they could teach exploits.
  - The 2 tuning starts: overfitting and the H6 separation. T07 must not read evaluation/heldout; check that its code paths cannot.
  - Readiness for the full training run after T05-fix1.
- **T14-fix1 (QA).**
  - The adapter: cadence, WAIT→None, fallbacks, a fresh controller per game.
  - The page default is the baseline; neutral label; build hash.
  - The three existing web tests it edited: justified, and only within permitted paths?
  - The smoke script logic; the Node contract test.
- **T14-fix1 (Eval).** The adapter gives the AI seat only its own view; the neutral label is really neutral (no other field differs); the build hash reveals nothing.
Return one verdict block per task you reviewed. Be concise.
