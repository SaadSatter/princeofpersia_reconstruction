# AUDIT-B report (QA subagent, audit mode), 2026-11-23

Condensed by the orchestrator from the subagent's final message (findings, tables and proposals kept). Orchestrator re-ran the F1 probe on 13c7488 and saw the same result (`disguised: motion {'effect': 'waited', ...}` vs `guard: motion None` -> DIFFERENT).

Status: done (read-only). Commit reviewed: 13c748875c4e61ecda7526489d31d4dfd2d5d645. Files changed: none. Side effect disclosed and undone: `team/__pycache__`, `tests/__pycache__` created in /home/claude/final-saadsatter by `unittest`, deleted; `git status --porcelain --ignored` clean.

## 1. Tests (`python3 -m pytest -q -p no:cacheprovider -rs`, Py 3.13.18, pytest 9.1.1 — not the pinned <9)
| Ref | Result |
|---|---|
| final/versus-engine 13c7488 | 419 passed, 12 skipped (twice) |
| main 0e5df5f | 170 passed, 4 skipped |
| level1-reconstruction 2b5c909 (= g1, agent-setup tests tree) | 272 passed, 10 skipped |
| origin/level1-reconstruction d5f6bda | 192 passed, 4 skipped |
| final/art-pixellab 3c0b0b4 | 278 passed, 11 skipped |
Skips on versus-engine: no pygame (test_generated_art:17, test_frontend:260,:269, test_versus:198 window), no anthropic (test_provider_sdk:13), images not bundled (test_frontend:211), original L1 not fetched (test_level1_original x6). Dev CI runs `uv sync --frozen` with no extras, so pygame/anthropic tests also skip in CI: the versus window and generated art have never run in CI.

## 2. Determinism
Committed: same-process run-twice tests in test_versus, test_swordplay, test_guards, test_disguise, test_flip_review. Probes: 400-frame two-seat script hash 195ccde61e142cf5 identical under PYTHONHASHSEED 1/2/3; fuzz replay from ep.log identical (ff96d21579193cc7); 200 random seeds: 0 crashes, all terminal (won:A 101, won:B 99), observation keys stable; seat-swap mirrored scripts seat-independent. Gaps: no committed replay-from-log or cross-process test; RNG only used for disarmed-sword landing (pop/versus.py:694), seeds 0 and 1 give identical traces.

## 3. Coverage (versus)
| Category | Status | Evidence / weakness |
|---|---|---|
| Rule/state invariants | present | test_rivals_cannot_pass_through_each_other, ..._both_stay_out, test_flip_review settle tests |
| Terminal: win | present | test_three_hits_kill_and_win_for_the_other_rival |
| Terminal: draw both died | weak | set via `_die()`, never played out |
| Terminal: time limit | present, limited | 5-frame test; default 60 min vs GDD 5 min (OQ-3) |
| Invalid/malformed rejected, no change, counted | weak | seat A only, 7/"FLY"/blank; no not-legal-now with snapshot equality, no seat B, no terminal refusal |
| Stale actions | missing | queued input that becomes illegal silently dropped, not counted (`_advance` ~560); replaced input vanishes |
| Observed regressions | present | test_regression_take_while_standing_over_the_downed_guard, ..._running_jump_flight..., test_flip_review.py |
| Combat / guards / disguise | present | R-V01–R-V21 per-rule tests |
| Rival-set traps | missing | not implemented |
| Both seats | partial | mostly A-centric |
| Isolation: rooms, inputs, seat names | present | test_a_rival_in_another_room_is_not_observed, test_observation_names_no_seat..., test_the_other_rivals_input_is_never_observed |
| Isolation: disguise identity | weak (F1) | existing test covers standing still with motion None only |
| Isolation: suspicion | present | test_suspicion_is_shown_only_to_the_suspected_seat |
| Isolation: trap ownership / server message | missing | not built |
| Deterministic replay | weak | no replay from log/trace for versus |
| Per-seat limits, timeout, fallback | missing | runner/agents/evaluate single-seat only |

## 4. Findings
- **F1 [major] pop/versus.py:911-919 (observe, _motion_view).** A disguised rival's WAIT shows the other seat `kind:"guard"` with `motion.effect:"waited", frames:6`; a paused guard has `motion: None` and guards only produce moved/drew/sheathed/turned/lunge (pop/guards.py:154-184). Field-level identity leak; contradicts R-V18, VERSUS_SPEC §6 leak test (1), checklist "disguise identity … done". Repro: VersusEpisode(arena.situation("A"), {"A": (2,0,4,-1), "B": (2,1,0,+1)}, 0, guard_posts={}), set A disguised/sheathed/stance None, step("A","WAIT"), tick(); compare observe("B")["figures"] with a paused guard at (2,0,(4,4),-1). Renderer maps waited -> WAIT clip, so probably invisible to a human (not checked by eye).
- **F2 [minor/design]** Disguised UP (hop), DOWN, JUMP_* are moves no guard performs — visible on screen; design question whether they raise suspicion/break disguise.
- **F3 [minor]** Stale/replaced queued inputs dropped with no count or feedback; matters for AI-seat illegal/stale metrics.
- Unverified: R-V23 fixes in 13c7488 written by the session that audited them; no independent re-review (sm-untracked-13.md says so). Dev CI status for 13c7488 not checked.
Earlier findings: all 2026-11-18 audit/review findings fixed in 13c7488 or kept by Saad (2026-11-23); midterm session08 F1 and session09 HIGH fixed.

## 5. CI readiness
Dev ci.yml: PR + push main, py 3.11/3.12, uv sync --frozen, pytest. ci/midterm-saadsatter.yml pinned by tests/test_ci_workflow.py (stale for final). Official final.yml: py 3.12, team unittests (ran: 111 OK), team validate (passes vacuously: "no agent-team/ yet"), render, generated-file diff; game step is a placeholder. Needed: decide game folder (QA recommends a subfolder so pytest testpaths do not collect template team tests — see reconciliation), replace placeholder with uv sync + pytest, optional pygame job with SDL_VIDEODRIVER=dummy, team init + commit render, merge .gitignore, replace test_ci_workflow.py, extend template AGENTS/CLAUDE rather than replace. Branch protection: not verifiable.

## 6. Integration risks
Re-run suite and 16 golden midterm traces after fast-forward; root layout change on move; commit uncommitted docs first; server/runner work must re-run leak tests against server messages, isolation tests first.

## Proposed tests (not written)
test_disguised_rival_waiting_is_observed_like_a_paused_guard (fails today); test_disguised_figure_motion_effects_are_guard_effects; test_refused_input_changes_nothing_for_either_seat; test_terminal_refusal_is_not_counted; test_stale_queued_input_is_reported; test_mutual_lunge_same_frame_both_lose_heart_symmetric; test_double_death_same_frame_is_draw_by_play; test_replay_from_input_log_reproduces_state; test_versus_trace_is_identical_across_processes; test_seed_changes_rng_dependent_outcomes; test_seat_swap_mirror_gives_mirror_outcome; test_per_seat_step_call_limits_and_timeout_fallback_is_WAIT; test_seat_model_sessions_share_no_history; test_server_message_equals_observe; test_trap_owner_not_in_other_seat_observation_or_legal_actions; test_trap_harms_its_owner; test_final_workflow_runs_game_tests_and_team_checks.

Decisions for Saad: F2 tells; stale-input counting; OQ-3; official game folder (CQ-5); pygame CI job; branch protection.

Verdict: ACCEPT WITH NOTES (engine stages 1–4 + flip as tested); not gate-ready. Findings: F1 major, F2 minor/design, F3 minor. Not checked: GitHub PR/CI/branch protection; rendering; pinned pytest; live paths (none for versus).
