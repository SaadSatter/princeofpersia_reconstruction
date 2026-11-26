# Shadow Masque — final project (G1 Concept; G2/G3 updates dated 2026-11-26)

Working title: *Shadow Masque*. A two-player versus game built on this repository's Prince of Persia–style engine (the midterm).

| G1 item | Link |
|---|---|
| Recording | [G1 pitch recording (Google Drive)](https://drive.google.com/file/d/1iioIm1JEEDA7lVOisP4arZPk8TZJlA5_/view?usp=sharing) |
| Deck | [G1 pitch deck (Google Slides)](https://docs.google.com/presentation/d/1uY0srRtRv9uPN3S5nRifjzna6CjPEKrSMPiYuEDhRrA/edit?usp=sharing) |
| Initial GDD | [`GDD.md`](GDD.md) |
| Initial Configuration Document, with role coverage | [`CONFIGURATION.md`](CONFIGURATION.md) |
| Initial Project Plan, with gate dates and Initial Risk Register | [`PROJECT_PLAN.md`](PROJECT_PLAN.md) |

## G2/G3 (due Sat 28 Nov 2026, 11:59 p.m.)

| G2/G3 item | Link |
| --- | --- |
| Updated GDD and Configuration, dated "Changes since the last gate" (2026-11-26) | [`GDD.md`](GDD.md), [`CONFIGURATION.md`](CONFIGURATION.md) |
| Task tracker (tasks T01 to T29, gates, evidence) | [`TRACKER.md`](TRACKER.md) |
| Scope lock (draft, not approved by Saad) | [`SCOPE_LOCK.md`](SCOPE_LOCK.md) |
| Playtest kit and log (no external session yet) | [`playtest/LOG.md`](playtest/LOG.md), [`playtest/PROTOCOL.md`](playtest/PROTOCOL.md) |
| Evaluation of the AI rival | [`evaluation/RESULTS-T09.md`](evaluation/RESULTS-T09.md), [`RL_POLICY.md`](RL_POLICY.md) |
| Modes, online play, hosted build, versus runner | [`GAME_MODES.md`](GAME_MODES.md), [`ONLINE_PLAY.md`](ONLINE_PLAY.md), [`WEB_BUILD.md`](WEB_BUILD.md), [`VERSUS_RUNNER.md`](VERSUS_RUNNER.md) |
| First playable recording | Saad's, not yet linked |

## Working documents

| Document | Purpose |
|---|---|
| [`REQUIREMENTS_CHECKLIST.md`](REQUIREMENTS_CHECKLIST.md) | Gate deliverables, status, decisions in force |
| [`EVIDENCE_INDEX.md`](EVIDENCE_INDEX.md) | Where each deliverable's evidence lives |
| [`ENGINE_DECISION.md`](ENGINE_DECISION.md) | Python/Pygame vs Godot (recommendation, pending Saad) |
| [`ART_PROVENANCE.md`](ART_PROVENANCE.md) | Where the generated art came from and on what terms (OQ-8) |

Agent configuration: [`AGENTS.md`](../../AGENTS.md) (shared invariants, Claude and Codex), [`agent-config.json`](../../agent-config.json) (course manifest for the in-game rival and the agent team), [`orchestration/README.md`](orchestration/README.md) (the native orchestrator and named workers, file-based handoffs, review gates), `.claude/agents/rules-reviewer.md` and `.codex/agents/pop-rule-reviewer.toml` (independent reviewers), `.claude/skills/game-rules-audit/` and `.claude/skills/session-evidence/` (skills).

Open questions are marked `OQ-n` (design) and `CQ-n` (configuration) in each document.

The midterm documents in [`docs/`](../) still describe the Level 1 reconstruction. The final project's changes are recorded here: [`GDD.md`](GDD.md) and [`CONFIGURATION.md`](CONFIGURATION.md) each open with "Changes since the last gate (G1 → G2/G3, as of 2026-11-26)", which supersedes the 2026-11-24 entry kept below it. The orchestration state, Saad's decisions and review log are in [`orchestration/`](orchestration/) ([`STATUS.md`](orchestration/STATUS.md), [`DECISIONS-2026-11-23.md`](orchestration/DECISIONS-2026-11-23.md), [`DECISIONS-2026-11-24.md`](orchestration/DECISIONS-2026-11-24.md), which also holds the entries of 2026-11-25 and 2026-11-26 up to #102, and [`DECISIONS-2026-11-26.md`](orchestration/DECISIONS-2026-11-26.md)). The rival, traps, web build, online server and evaluation are on `main` (PR #11); the three-mode menu, kneel-takes-uniform and online polish are on `orch/reviewed` (PR #12, open).

Videos are never committed; the recording is linked only.
