# T24-fix1 session (tech-lead worker)

Base `d187e1c`, branch `task/T24-fix1`. Brief `tasks/T24-fix1.md@773b955`, decisions #98 and #101.

Failing tests first, then `Rival._would_hang_down` (the `engine._down` hang test) gating the uniform
branch of `Rival._kneel_target` in `pop/versus.py`. R-V17 updated in the rule map and `VERSUS_SPEC.md`
(#98 wording, #101 ledge rule). One existing test edited as authorised. No macro, baseline or PPO code
changed. No paid calls, no training, no H6 run.
