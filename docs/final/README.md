# Shadow Masque — final project, G1 Concept

Working title: *Shadow Masque*. A two-player versus game built on this repository's Prince of Persia–style engine (the midterm).

| G1 item | Link |
|---|---|
| Recording | [G1 pitch recording (Google Drive)](https://drive.google.com/file/d/1iioIm1JEEDA7lVOisP4arZPk8TZJlA5_/view?usp=sharing) |
| Deck | [G1 pitch deck (Google Slides)](https://docs.google.com/presentation/d/1uY0srRtRv9uPN3S5nRifjzna6CjPEKrSMPiYuEDhRrA/edit?usp=sharing) |
| Initial GDD | [`GDD.md`](GDD.md) |
| Initial Configuration Document, with role coverage | [`CONFIGURATION.md`](CONFIGURATION.md) |
| Initial Project Plan, with gate dates and Initial Risk Register | [`PROJECT_PLAN.md`](PROJECT_PLAN.md) |

## Working documents

| Document | Purpose |
|---|---|
| [`REQUIREMENTS_CHECKLIST.md`](REQUIREMENTS_CHECKLIST.md) | Gate deliverables, status, decisions in force |
| [`EVIDENCE_INDEX.md`](EVIDENCE_INDEX.md) | Where each deliverable's evidence lives |
| [`ENGINE_DECISION.md`](ENGINE_DECISION.md) | Python/Pygame vs Godot (recommendation, pending Saad) |
| [`ART_PROVENANCE.md`](ART_PROVENANCE.md) | Where the generated art came from and on what terms (OQ-8) |

Agent configuration: [`AGENTS.md`](../../AGENTS.md) (shared invariants, Claude and Codex), [`agent-config.json`](../../agent-config.json) (course manifest for the in-game rival and the agent team), [`orchestration/README.md`](orchestration/README.md) (the native orchestrator and named workers, file-based handoffs, review gates), `.claude/agents/rules-reviewer.md` and `.codex/agents/pop-rule-reviewer.toml` (independent reviewers), `.claude/skills/game-rules-audit/` and `.claude/skills/session-evidence/` (skills).

Open questions are marked `OQ-n` (design) and `CQ-n` (configuration) in each document.

The midterm documents in [`docs/`](../) still describe the Level 1 reconstruction. The final project's changes are recorded here: [`GDD.md`](GDD.md) and [`CONFIGURATION.md`](CONFIGURATION.md) each open with "Changes since the last gate (G1 → G2/G3, as of 2026-11-24)". The orchestration state, Saad's decisions and review log are in [`orchestration/`](orchestration/) ([`STATUS.md`](orchestration/STATUS.md), [`DECISIONS-2026-11-23.md`](orchestration/DECISIONS-2026-11-23.md), [`DECISIONS-2026-11-24.md`](orchestration/DECISIONS-2026-11-24.md)). Most rival, trap, web and evaluation work is on `orch/preview` or WIP branches, not on `main`.

Videos are never committed; the recording is linked only.
