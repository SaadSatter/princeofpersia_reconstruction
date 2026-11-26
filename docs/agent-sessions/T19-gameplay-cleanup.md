# T19 session (tech-lead worker)

Base `fc02687` (`orch/reviewed`), branch `task/T19`. Gameplay clean-up from Saad's request of 2026-11-24:
flip is the default directional jump (#53, R-V22 amended), a 2-tick direction + jump grace window (#54, new
R-V35, in the engine so every seat and front end gets it), either control set for the player's own seat outside
local two-player (#55), and a kneel for sword pickups and uniform takes (item 3, `crouch` strip).
Tests written first (commit `4eb0da4`, 45 Python tests failing plus the new Node cases), then the engine and the
front ends. No paid calls, no training, no server left running, no browser or pygame window run by hand.
Result line, changed tests, and the two existing tests that pin the old rules are in
`docs/final/orchestration/reports/T19-tech-lead.md`.
