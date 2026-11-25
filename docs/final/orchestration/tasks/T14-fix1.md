# T14-fix1: web build corrections and AI-rival plug-in
Assigned agent: `agents/tech-lead.md`. Setup: `_EXEC_COMMON.md`. Base: `int/wave2-web` (int/wave2-t05 + task/T14): `git clone -q /home/claude/sm/wt/INT /home/claude/sm/wt/T14-fix1 && cd ... && git checkout -q -b task/T14-fix1 int/wave2-web`.
Inputs: `/home/claude/sm/orch/reports/GATE-T14-qa.md`, `/home/claude/sm/orch/reports/GATE-T14-eval.md`; DECISIONS #12–14, #24, #25 (keep the end screen saying how the duel ended; rematch keeps the seed).
Gate tests: copy `tests/test_gate_t14_*` from `gate/T14-qa` (/home/claude/sm/wt/GATE-T14-qa) and `gate/T14-eval` (/home/claude/sm/wt/GATE-T14-eval). Remove the xfail marks only for what you fix. Keep the eval outcome-reason xfail, because decision #25 keeps the raw reason. Change it to a passing test asserting the decided behaviour and cite #25.
Fix:
1. `SeatControllerRival(controller, every=6)` in `web/bridge.py`. It calls `decide(obs, tuple(legal))` every `every` ticks, maps WAIT to None, gives one controller per game (QA-5 policy) and labels the fallback. Make `?rival=baseline` the default AI rival on the page (VersusBaseline from `agents/versus_baseline.py`), keeping idle and random as labelled options. Ship `agents/` in game.zip, stdlib only.
2. The smoke test must prove input reaches the engine. Expose a test-only readout (for example `window.__smLast = {frame, me:{room,row,col}}`), assert the position changes after holding a key, and compare screenshots before and after.
3. Key hints for the human's actual seat.
4. A neutral rival label option (`?label=neutral` → "Rival") for blind Session B; and a short build hash from manifest.json shown on the page for the playtest log.
5. WEB_BUILD.md:
   - the adapter;
   - game.zip is public (engine, baseline, later the weights);
   - the query string is editable;
   - devtools must stay closed in playtests and the facilitator watches the screen;
   - rematch keeps the seed (decision #25; a learning confound, noted for the protocol);
   - "not verified in a browser" stays until CI runs.
Permitted writes: `web/**`, `tools/web/**`, `tests/test_web_*.py`, the copied gate files, `.github/workflows/web-smoke.yml`, `.github/workflows/pages.yml`, `docs/final/WEB_BUILD.md`, `docs/agent-sessions/`.
Acceptance:
- failing tests first;
- `WebGame(rival=SeatControllerRival(make_baseline()))` plays 600 ticks with 0 invalid inputs;
- the Node contract test still passes;
- full suite green;
- Handoff to QA block.
