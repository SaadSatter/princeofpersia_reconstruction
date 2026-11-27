# T22 session (tech-lead worker)

Base `74975e1` (`orch/reviewed`), branch `task/T22`. The trained PPO rival in the game with three
modes (AI Model, Baseline, Human vs Human) in `play.py`, the hosted page and the online server
(decisions #87 to #90). Mode logic is in new modules (`agents/modes.py`, `render/menu.py`,
`server/modes.py`) with small hooks in `play.py`, `web/`, `server/` and `tools/web/build.py`, so the
merge with T20 stays small. Tests first (commit `a07ca95`), then the implementation, then the report
`docs/final/orchestration/reports/T22-tech-lead.md` (result line, what was run by hand, concerns).
No paid calls, no training, no H6 run, no new dependency, no browser or real window run by hand.
