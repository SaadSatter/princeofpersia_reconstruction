# T22-fix1: decisions #91, #92 and the T22 gate findings

Handoff id: HO-T22-fix1-orchestrator. Assigned: tech-lead; then qa (Gate 1), evaluation-specialist (Gate 2), Gate 3. Corrective attempt 1 of 2 for T22.
Read first: `tasks/T22.md`@9305b3e; `reports/T22-tech-lead.md`@73e6531; `reports/T22-qa.md`@2477843 (QA-T22-1, QA-T22-2); `reports/T22-evaluation-specialist.md`@0ff9d4a (EVAL-T22-1 to -5 and its fix list); decisions #88, #91, #92 in `DECISIONS-2026-11-24.md` on `main`.
Base: `gate/T22-eval` 0ff9d4a. `git switch -c task/T22-fix1 0ff9d4a`. Paste the base's suite line.

## Fix list (failing test first for each)

1. **EVAL-T22-1 (major, required):** on a decision tick, when the controller answers WAIT, `ModeRival` submits `"WAIT"` exactly as `pop/versus_runner.py` does, and `None` between decisions; failed or illegal answers stay a labelled fallback (`"source": "fallback"`). No change to `agents/rl/`, `pop/` or the baseline. Add a replay test: a server trace containing WAIT inputs replays to the same snapshot. The game path must equal the runner path for the shipped rival (Eval's parity test).
2. **#91 / QA-T22-2:** delete the `legacy` label path in `server/__main__.py` `make_match`, so `--rival baseline` with no creator-chosen mode shows "Baseline (scripted)".
3. **#92:** a bare `python play.py` shows the three-mode menu, and the old single-player level stays reachable with a flag (keep its situation argument working). The hosted page opens on a mode chooser. Update the web smoke test (`tools/web/smoke.cjs` and, if needed, `.github/workflows/web-smoke.yml`) to pick a mode. If any other existing test breaks, stop and report.
4. **QA-T22-1:** build the `--mode` help text from `agents/modes.py`.
5. **EVAL-T22-3:** load and hash-check the immutable network once per process (cache), not per room.
6. **EVAL-T22-2:** `ModeRival.reset` clears `fallback_log`; the hosted page writes fallback entries to the browser console (labelled), never to the other seat.
7. **Docs (`docs/final/GAME_MODES.md`):** the pygame and hosted-page AI seats are called synchronously with no time budget, and only the server has the 0.04 s limit (#45); "AI Model (trained)" is a label, not a strength claim, and no win rate appears in the menu, HUD or end screen (EVAL-T22-5; T09 was not supported).

## Existing tests you may change (the orchestrator authorises exactly these)

- `tests/test_gate_t13_qa_online.py::test_cli_process_two_scripted_clients_real_clock_and_trace_dir[baseline]`: only the label assertion, to "Baseline (scripted)" (Saad #91).
- The web smoke test, to pick a mode (Saad #92).
- `tests/test_qa_T22_probes.py`: remove only the strict `xfail` marker of the QA-T22-1 case once it passes.
- `tests/test_eval_T22_parity.py`: remove only the strict `xfail` markers of the EVAL-T22-1 cases once they pass.
List each with old and new in your report. No other existing-test edit.

Permitted writes: as in `tasks/T22.md` (`agents/modes.py`, `play.py`, `render/` menu, `web/**`, `tools/web/**`, `server/**`, `docs/final/GAME_MODES.md`, the named doc paragraphs), plus `.github/workflows/web-smoke.yml` only if the smoke change needs it, the test edits above, new tests `tests/test_t22fix1_*.py`, `docs/agent-sessions/` (one new file), `docs/final/orchestration/reports/T22-fix1-tech-lead.md`. **Not** `pop/`, `agents/rl/**`, `agents/versus_baseline.py`, `tools/rl/**`, `evaluation/**`. No training, no `--live`, no H6 run, no new dependency. The other session's T20 is still changing `play.py` and `server/`: keep hooks thin.

Suite on a clean committed tree: `uv run --frozen --extra play --extra train --extra online pytest -q`; paste the real line.
Gates: QA (`gate/T22-fix1-qa`), Eval (`gate/T22-fix1-eval`), Gate 3 after T20 closes.
