# GATE-T14: independent review of the hosted web build (Pyodide + Phaser)
Gate 1: `agents/qa.md`. Gate 2: `agents/evaluation-specialist.md`. These are separate subagents.
Commit: `e6c274d` on task/T14: `git clone -q /home/claude/sm/wt/T14 /home/claude/sm/wt/<gate-id> && cd ... && git checkout -q e6c274d`.
Inputs:
- `/home/claude/sm/orch/tasks/T14.md` (brief);
- `/home/claude/sm/orch/reports/T05-T06a-T14-T02close.md` (implementer report, T14 section);
- `/home/claude/sm/orch/PLAN-2026-11-23-v3-delta.md`;
- DECISIONS #12–14.

The sandbox cannot load Pyodide or Phaser (CDN blocked). Do not try to bypass it. Review the JS against the libraries' documented APIs as best you can, and say plainly what is unverified.
Permitted writes: new tests `tests/test_gate_t14_<qa|eval>_*.py` on `gate/T14-<qa|eval>` (failing ones xfail strict).

QA focus:
- **Bridge correctness.** Key map parity with `play.py --versus`; in local mode the two players' keys do not interfere.
- **Determinism; build reproducibility.** Does the archive contain everything the page imports?
- **JS–Python contract.** Every field main.js reads exists in the payload. Write a Node test that feeds a recorded payload JSON into the pure parts of main.js, if they can be isolated.
- **Workflows.** Valid YAML; least-privilege permissions; no secrets. Does the smoke test assert something meaningful?
- **Docs.** WEB_BUILD.md run instructions are correct.
- **Merges.** Scratch merges with task/T01-fix1 and with task/T05: does the bridge still work, and can VersusBaseline plug into the rival hook?

Evaluation Specialist focus:
- **Payload leak boundary.** Walk every key; check `outcome.reason` revealing an unseen death (decide whether it is acceptable; recommend). The draw list must not depend on anything outside `observe(human_seat)`.
- **The rival hook.** It gets only its own view. Can the PPO policy (pure-Python inference) run under Pyodide within 1/12 s per tick?
- **The static-page limitation.** Devtools can read state. Is it documented accurately in WEB_BUILD.md, and does it affect the planned blind playtest (a player opening devtools)?
- **Playtest kit.** Is the build suitable for T11 Session A/B? It has no trace file yet: consent option (a).

Return the verdict block from your role file. Be concise.
