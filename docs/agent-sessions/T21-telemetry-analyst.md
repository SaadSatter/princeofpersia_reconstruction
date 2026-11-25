# T21 session (tech-lead worker)

Base `72066f1` (`orch/reviewed`), branch `task/T21`. Brief `tasks/T21.md@60f4805`, decision #69.

Added the `telemetry-analyst` worker: native definition (`.claude/agents/telemetry-analyst.md`,
`claude-sonnet-5-5`, tools Read, Grep, Glob, Bash, Write, no Agent tool) and procedure
(`docs/final/orchestration/agents/telemetry-analyst.md`). Its only write path is its own report.
The procedure carries the T20-fix2 Gate 2 reading notes (flip counts jump starts; a zero-gap
DRAW then SHEATHE reads as one hold; never pool pre-fix2 logs; AI duels summarize the human
seat only).

Role tables edited on `main`'s current text (checked out from `main` for the five files that
differ between `main` and `orch/reviewed`, then edited): `CLAUDE.md`, orchestration `README.md`,
`agents/orchestrator.md`, `.claude/agents/orchestrator.md`, `COURSE_ROLE_MAP.md`. No code change.
Dry run on `tests/data/t20_telemetry/`: `reports/T21-dryrun-telemetry-analyst.md`.

No paid calls, no training, no server run.
