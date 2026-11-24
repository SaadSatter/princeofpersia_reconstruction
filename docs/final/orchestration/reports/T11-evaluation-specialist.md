# T11 report (Evaluation Specialist), 2026-11-23 — condensed by the orchestrator

Status: done. Branch `task/T11` commit e47c996 (base 721b3e6). Only `docs/final/playtest/` (5 files, 574 lines): CONSENT, PROTOCOL, QUESTIONNAIRE, OBSERVATION_TEMPLATE, LOG (marked as CQ-6 proposal). All templates; no session, player or result filled. Tests: 419 passed, 12 skipped (base unchanged).
Orchestrator check: diff touches only `docs/final/playtest/` (verified with `git diff --name-only`).

Session A (required G2/G3): A1 human vs scripted baseline with only the human's panel (needs T12) preferred; A2 two-panel human vs human fallback, identification not scored. Session B (comparative, blind X/Y codes, counterbalanced XY/YX, starting room alternated, seeds never from H6, blindness check) recommended for G4 at the earliest. Definitions: identification opportunity (with-decoy / solo), correct identification (strike or name the rival), false identification (strike or name a real guard and R3 says they thought it was the rival), missed rival, no encounter.

Findings passed on: (1) 5-minute limit not in code at 721b3e6 (T01 covers it). (2) Human vs AI not built (T05, T12). (3) Seat colours (A indigo, B crimson, play.py:151) give the rival away on seat swap: T12 must keep the human's colour fixed.

Open choices for Saad: approve kit; accept/edit hypotheses H1–H3, M1–M3; adopt LOG.md as CQ-6; Session A mode and physical divider; public notes; recording; age 18+; who seals X/Y; seed list; four-round sessions; 2-second identification window; with-decoy/solo split; whether Session B runs before G4.
Gate 1 (QA fact-check): pending.
