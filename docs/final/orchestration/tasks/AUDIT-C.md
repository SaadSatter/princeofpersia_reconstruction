# AUDIT-C: AI rival seat and evaluation harness (read-only)
Assigned agent: `agents/evaluation-specialist.md` (audit mode)
Setup: `tasks/_AUDIT_COMMON.md`
Requirements: FINAL_REQUIREMENTS §1 (macro-actions, hypothesis, baseline, budgets), §3 executable agent extension + manifest [R], §5 evaluation harness [R]/[+]; orchestration brief §8.
Permitted write paths: none (scratch checkouts under /home/claude/sm/wt/AUDIT-C only). No live calls; fake providers only.

Inspect on `final/versus-engine` (and note differences on other branches):
1. Agent interfaces: does the five-operation interface exist for two seats (`reset/observe/legal_actions/step/outcome` with player_id)? What does a seat controller receive and return? Can human, scripted, model and fallback controllers be swapped per seat today?
2. Model-driven controller (`agents/model_player.py`, `agents/providers.py`): does it work for a versus seat or only the midterm single-player game? Prompt contents, history per seat, macro-action vocabulary (G1: blend, disguise, rig trap, wait, follow, strike, flee, climb), validation against current state, timeout/fallback, non-blocking behaviour, cost/token accounting, budget caps, `--live` gate.
3. Scripted opponent (`agents/baseline.py` and any versus bot): is there a competent versus baseline matching G1 (nearest uniform, shortest path, adjacent strike) on the same observation? Any privileged access?
4. Evaluation runners (`evaluate.py`, `pop/situations.py`, runner traces): which configurations exist (scripted vs scripted, model vs scripted, seat-swapped, model vs model)? Deterministic scenarios available; held-out separation; result schema (scenario, seed, commit, model id, prompt/config version, seat, outcome, termination, invalid actions, calls, latency, tokens, cost, fallbacks, trace refs).
5. Live-model evidence on record (`traces/`, `EVALUATION.md`, session 04): date, model, build (midterm vs versus), counts, cost — and whether it supports the G1 budget figures for the *current* build.
6. Replay tooling and replay fidelity for two seats.
7. Observation boundary: probe for indirect leakage (ids, ordering, counts, legal actions, error text, logs, pathfinding helpers) in versus observations; run `tests/test_disguise.py`, `tests/test_leakage.py`, `tests/test_flip_review.py`.
8. Dry-run and spending controls present or missing.
Return: reuse list, must-build list (ordered, with dependencies), a proposed scenario set (disguise/blending, rival identification, trap placement/avoidance, fight vs retreat, full duel held-out) with initial conditions, success criteria and metrics stated as *proposals for Saad's approval*, and a cost estimate for a minimal live pre-G2 suite labelled as an estimate.
