# T22-fix2: merge T22 with the T20/T21 line, and the last small T22 notes

Handoff id: HO-T22-fix2-orchestrator. Assigned: tech-lead; then qa (Gate 1), evaluation-specialist (Gate 2), Gate 3. Corrective attempt 2 of 2 for T22 (the last before escalation to Saad).
Read first: `tasks/T22.md`@9305b3e, `tasks/T22-fix1.md`@7bf5bef; `reports/T22-fix1-qa.md`@5ebf909 (QA-T22fix1-1, -2); `reports/T22-fix1-evaluation-specialist.md`@967db26 (ACCEPT; optional fix2 list); `tasks/T20.md` and the T20 reports on `orch/reviewed` (playtest telemetry, which changed `play.py` and `server/` in parallel, decision #90).

## Why

The Gate 3 integration trial of `gate/T22-fix1-eval` 967db26 onto `orch/reviewed` 1a515ca (T20 + T21 closed) conflicts in `play.py`, `server/__main__.py`, `server/match.py` and `docs/final/ONLINE_PLAY.md`. Resolving code conflicts is implementation work.

## Do

1. `git switch -c task/T22-fix2 967db26`, then `git merge origin/orch/reviewed` (1a515ca) and resolve the conflicts so that **both** features work in full: the T22 modes (menu by default #92, `--mode`, `--classic`, AI rooms, honest labels #88/#91, WAIT forwarding, the weights cache) and T20 telemetry (`--playtest` in `play.py` and the server, per-seat logs, nothing about the other seat, telemetry never touching the engine). Where they meet (for example `--playtest` with `--mode ai`, an AI room with telemetry on), pick the behaviour both briefs imply and test it; telemetry must log only the human seat's own facts in an AI room and never the AI's observation or fallbacks beyond what T20 allows. Describe every conflict and how you resolved it in the report.
2. **QA-T22fix1-2:** the `?mode=ai` row in `docs/final/WEB_BUILD.md` says "Baseline (scripted)".
3. **QA-T22fix1-1:** `agents/modes.py` `_shared_net`: hash the file bytes on every call and key the cache on the SHA-256 digest (Eval: about 0.3 ms per call).
4. The wrong `# WAIT` comment next to the late-answer path in `server/rival.py` says what it does (returns no input, labelled fallback).
5. Remove only the strict `xfail` markers of QA's two QA-T22fix1 probes in `tests/test_qa_T22fix1_probes.py` once they pass (authorised; list them).

If a T20 or T21 test and a T22 test contradict each other, stop and report which; do not edit either beyond item 5.

Permitted writes: as in `tasks/T22-fix1.md`, plus the merge resolution in `play.py`, `server/**`, `docs/final/ONLINE_PLAY.md`, and new tests `tests/test_t22fix2_*.py`. Not `pop/`, `agents/rl/**`, `agents/versus_baseline.py`, `tools/rl/**`, `evaluation/**`, `tools/telemetry/**` (except what a conflict forces; say so). No training, no `--live`, no H6 run, no new dependency.

Suite on a clean committed tree: `uv run --frozen --extra play --extra train --extra online pytest -q`; paste the real line. Also run the T20 manual check the T20 report describes, with `--mode ai`, if feasible.
Gates: QA (`gate/T22-fix2-qa`: both features, the overlap, scope), Eval (`gate/T22-fix2-eval`: AI seat and telemetry boundary in AI rooms, parity still holds), Gate 3 (merge is then a fast-forward of `orch/reviewed`).
