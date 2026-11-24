# GATE-T01 Evaluation Specialist report (Gate 2), 2026-11-23 — condensed by the orchestrator

**ACCEPT WITH NOTES** on 83127cf. Branch gate/T01-eval 865f597, tests/test_gate_t01_eval_boundary.py; full 518 passed, 12 skipped, 2 xfailed.
Verified: F1 closed frame for frame (STEP, turn, WAIT, DOWN identical to a patrolling guard; crouch shows standing/motion null); minutes_left from duel limit; AC4 counters gameplay-neutral.
Leaks (both pre-existing, not introduced by T01):
- **L1 [major]** `legal_actions` shows TAKE only if a downed guard's uniform is still there (pop/versus.py:199 uniform_ahead), but the observation and renderer show a downed guard the same either way: an AI seat can probe a body to learn the rival disguised; a human cannot. xfail strict test_legal_actions_reveal_nothing_the_observation_does_not.
- **L2 [minor]** figures sort ties rival-first in a shared cell. xfail strict test_figure_order_does_not_tell_a_disguised_rival_from_a_guard.
Design tells ranked (visible to humans too): (1) position — real guards never leave their room/row (room 4 row 2, room 5 row 2); (2) guard reaction — a real guard draws next frame on an undisguised rival in front within 5 cells; (3) stillness >13 frames or off patrol ends; (4) moves no guard makes (falling, hanging, dead, leaving room, hop, jump, climb, unarmed run); R-V25 exempts by move type, not actual cost; (5) one-frame gap between moves unless the macro layer queues ahead; (6) meterless "guard" when both rivals are disguised.
I3 "Identify" is near-trivial in the default arena (position) and via the reaction test. Options: guard posts that defeat (1), fix L1, give the baseline the tell-2 rule, report which cue each identification used.
Confounds: minutes_left out of distribution between ≤60 s tuning and 5-min H6 (drop from features or randomise limits); outcome() is cross-seat (reporting/terminal reward only, never features); replaced_inputs inflated by re-sending the same input; inputs pending at the end not counted; seeds barely matter.
Decisions for Saad: L1 fix and how; R-V25 wording "by move type"; I3 redesign; minutes_left in PPO features; replaced semantics; keep AC4.
