# Agent session evidence


- [Session 11 — Free dungeon art download](11-free-dungeon-art-download.md): download and fit review; external assets remain outside Git.
- [Session 12 — PixelLab art and arena](12-pixellab-art-and-arena.md): generated dungeon art (OQ-8), six-room arena (OQ-4), macOS black-box fix; PR #1.
- [Session 20 — Orchestrator: gameplay clean-up, room codes, playtest telemetry, telemetry analyst](20-orchestrator-gameplay-telemetry.md): tasks T18–T21 through the gates; decisions #52–#86 (this session's rows); PR #11 refresh.

## Index of all committed session records (2026-11-26, task T10b)

**Numbering clash, recorded rather than renamed.** Two records start `13-`
(`13-t01-engine-fixes.md`, `13-T04-versus-runner.md`), three start `14-`, and
`15-T05-fix1-macros-baseline.md` shares 15 with Saad's own
`15-native-orchestration.md` (his file, not committed here; his
`13-flip-audit-review-fixes.md` would be a third `13-`). Numbers 16 to 19 are
single. Later records carry the task id instead of a number. A `git mv` was not
done because the current names are linked from committed handoff reports and
review findings that T10b may not edit (`orchestration/reports/T04-*`,
`T05-fix1-tech-lead.md`, `orchestration/tasks/T04-fix*.md`, `docs/reviews/`).
Use the task id as the key. Proposed renames are in the T10b report.

| File | Heading |
| --- | --- |
| [`01-engine-implementation.md`](01-engine-implementation.md) | Session 01 — Prince of Persia: Configuration, Engine and Interface |
| [`02-agent-evaluation.md`](02-agent-evaluation.md) | Session 02 — Baseline, Model Player, Evaluation Infrastructure, CI |
| [`03-audit-fixes-live-prep.md`](03-audit-fixes-live-prep.md) | Session 03 — Audit fixes, live-evaluation preparation |
| [`04-live-attempt-diagnosis.md`](04-live-attempt-diagnosis.md) | Session 04 — Failed live attempt: diagnosis and fix (R-D25) |
| [`05-course-pr.md`](05-course-pr.md) | Session 05 — Course submission draft PR and course CI |
| [`06-pygame-frontend.md`](06-pygame-frontend.md) | Session 06 — Pygame frontend with original art (local only) |
| [`07-course-art-bundle.md`](07-course-art-bundle.md) | Session 07 — Original artwork in the course submission only |
| [`08-level1-reconstruction.md`](08-level1-reconstruction.md) | Session 08 — Original Level 1 as a separate scenario (P0–P4) |
| [`09-week7-pair-audit.md`](09-week7-pair-audit.md) | Week 7 pair audit preparation — October 26, 2026 |
| [`10-level1-stabilization.md`](10-level1-stabilization.md) | Session 10 — Level 1 post-review stabilization (before P5) |
| [`11-free-dungeon-art-download.md`](11-free-dungeon-art-download.md) | Session 11 — Free dungeon art candidate download |
| [`12-pixellab-art-and-arena.md`](12-pixellab-art-and-arena.md) | Session 12 — PixelLab dungeon art, six-room arena, macOS black-box fix |
| [`13-T04-versus-runner.md`](13-T04-versus-runner.md) | Session 13 (T04) — Seat-controller protocol and versus runner |
| [`13-t01-engine-fixes.md`](13-t01-engine-fixes.md) | Session 13 — T01 engine fixes: disguise tells, R-V24 hop, 5-minute duel, input counts |
| [`14-T05-macros-baseline.md`](14-T05-macros-baseline.md) | Session 14 (T05) — Macro layer and scripted versus baseline |
| [`14-t06b-traps.md`](14-t06b-traps.md) | Session 14 — T06b: rival-rigged traps, loose floor |
| [`14-t14-web-build.md`](14-t14-web-build.md) | Session 14 — T14 hosted web build (Pyodide + Phaser) |
| [`15-T05-fix1-macros-baseline.md`](15-T05-fix1-macros-baseline.md) | Session 15: T05-fix1 (macro reachability and baseline fixes) |
| [`16-t07-ppo-rival.md`](16-t07-ppo-rival.md) | Session 16: T07 (renumbered from 11 in T07-fix1; 11 was taken by the art download record) PPO rival (orchestrated Tech Lead subagent) |
| [`17-T07-fix1-ppo-corrections.md`](17-T07-fix1-ppo-corrections.md) | Session 17: T07-fix1 PPO stack corrections (orchestrated Tech Lead subagent) |
| [`18-T16-ppo-pretraining-polish.md`](18-T16-ppo-pretraining-polish.md) | Session 18: T16 PPO pre-training polish (orchestrated Tech Lead subagent) |
| [`19-T17-withhold-failed-weights.md`](19-T17-withhold-failed-weights.md) | Session 19: T17 withhold weights after a failed final check (orchestrated Tech Lead subagent) |
| [`T07-run1.md`](T07-run1.md) | T07-run1 session: commit the run-1 weights and evidence (tech-lead worker, claude-sonnet-5-5) |
| [`T08-fix1-evaluation-corrections.md`](T08-fix1-evaluation-corrections.md) | T08-fix1 session (tech-lead worker) |
| [`T08-fix2-fix1-not-recorded.md`](T08-fix2-fix1-not-recorded.md) | T08-fix2-fix1 session (tech-lead worker) |
| [`T08-fix2-policy-errors.md`](T08-fix2-policy-errors.md) | T08-fix2 session (tech-lead worker) |
| [`T08-versus-evaluation-suite.md`](T08-versus-evaluation-suite.md) | T08 session (tech-lead worker) |
| [`T09-fix1-wording.md`](T09-fix1-wording.md) | T09-fix1 session (evaluation-specialist worker) |
| [`T13-fix1-online-server.md`](T13-fix1-online-server.md) | T13-fix1 session (tech-lead worker) |
| [`T13-online-play.md`](T13-online-play.md) | T13 session: online play (tech-lead worker, claude-sonnet-5-5) |
| [`T18-fix1-room-error-boundary.md`](T18-fix1-room-error-boundary.md) | Session: T18-fix1, one room's error never stops the server |
| [`T18-room-codes.md`](T18-room-codes.md) | T18 session (tech-lead worker) |
| [`T19-gameplay-cleanup.md`](T19-gameplay-cleanup.md) | T19 session (tech-lead worker) |
| [`T20-fix1-telemetry-uses.md`](T20-fix1-telemetry-uses.md) | T20-fix1 session (tech-lead worker) |
| [`T20-fix2-telemetry-flip-hold.md`](T20-fix2-telemetry-flip-hold.md) | T20-fix2 session (tech-lead worker) |
| [`T20-playtest-telemetry.md`](T20-playtest-telemetry.md) | T20 session (tech-lead worker) |
| [`T21-telemetry-analyst.md`](T21-telemetry-analyst.md) | T21 session (tech-lead worker) |
| [`T22-fix1.md`](T22-fix1.md) | T22-fix1 session (tech-lead worker) |
| [`T22-game-modes.md`](T22-game-modes.md) | T22 session (tech-lead worker) |
| [`T24-fix1-hang-wins.md`](T24-fix1-hang-wins.md) | T24-fix1 session (tech-lead worker) |
| [`T24-kneel-takes-uniform.md`](T24-kneel-takes-uniform.md) | T24 session (tech-lead worker) |
