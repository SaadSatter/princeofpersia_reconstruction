# T01 report (Tech Lead), 2026-11-23 — condensed by the orchestrator

Status: done, awaiting gates. Branch `task/T01` (/home/claude/sm/wt/T01), base 721b3e6:
a1100f6 failing tests AC1–3 (27 failed, 61 passed) -> 558ef6d F1 masking + R-V24 + rule rows -> 6160501 5-minute duel + minutes_left -> 1a838c1 failing tests AC4 (4 failed, 1 passed) -> 7027536 fix own test key -> 64d0c0e AC4 stale/replaced counts (droppable with 1a838c1, 7027536) -> 83127cf session record.
Files: pop/versus.py; docs/RULE_SOURCE_MAP.md (R-V24, R-V25); docs/final/VERSUS_SPEC.md (R-V24 row, §10 time limit); tests/test_t01_disguise_tells.py, test_t01_duel_limit.py, test_t01_input_counts.py; docs/agent-sessions/13-t01-engine-fixes.md (number collides; renumber at integration). No existing test edited.
Tests: 512 passed, 12 skipped (base 419/12; +93). Frozen suite/situations/trace replay: 136 passed, 3 skipped.
F1: more tells found (bumped/2, edge/2, blocked jump bumped/8, crouch none/4, hop none/8). Fix (R-V25, new design rule — needs Saad): a disguised figure shows a motion to the other seat only if a guard can show it (GUARD_MOTIONS) or the move raises suspicion by rule; otherwise motion null (paused-guard look). Own `me.motion` unchanged. Rejected: giving guards a "waited" motion.
R-V24: disguised UP hop in a guard's sight +6 per frame (proposal; reuses R-V19 step); Duel.suspicious_rise single source.
Duel: DUEL_FRAMES = 3600 default for Duel, VersusEpisode, arena_episode; minutes_left from duel limit; single-player clock unchanged.
AC4: outcome() per-seat stale_inputs, replaced_inputs (report only).
Residual tells (design): postures falling/hanging/dead never shown by guards (loose-floor fall raises no suspicion); disguised WAIT counts neither for lingering nor for the -2 fall; disguised figure can leave its room, guards never do. Docs outside paths: VERSUS_SPEC §2.2 outcome keys, agent-sessions README, EVIDENCE_INDEX.
Decisions for Saad: R-V24 +6/frame; R-V25 masking vs making those moves suspicious; keep/drop AC4; residual tells.
