---
from: qa
to: tech
column: prototype
date: 2026-11-24
---

# Handoff: QA (+ Evaluation) → Tech. T18 room codes: one room's error stops every room

Draft. The orchestration repository holds it until `agent-team/` exists in the
official repository. T03 then copies it to
`agent-team/handoffs/2026-11-24-qa-eval-to-tech-T18.md`.
**Student decision** is Saad's to write. No agent fills it (Saad, 2026-11-26, option A).

## Route

Tech Lead (T18, report `reports/T18-tech-lead.md`@a3e96b4)
→ QA, Gate 1 (`reports/T18-qa.md`@7f3525e on `gate/T18-qa`, ACCEPT WITH NOTES)
→ Evaluation Specialist, Gate 2 (`reports/T18-evaluation-specialist.md`@f4dc475 on `gate/T18-eval`, ACCEPT WITH NOTES)
→ Saad (decisions #62, #63, `DECISIONS-2026-11-24.md`)
→ Tech Lead (T18-fix1, brief `tasks/T18-fix1.md`).

## Findings handed over

- **EVAL-T18-1 (minor, strict xfail):** an exception in one room's `on_finish` (for example an unwritable `--trace-dir`) escapes `pump()` and stops every room on the server.
- **QA-T18-1 (minor, strict xfail):** `normalize_code` reads the ligature "ﬀ" as "FF".
- Observations: room cap 50 against a measured safe level of about 40 rooms on the M4; room creates are not rate-limited; "full" versus "No room" tells a guesser that a code exists.

## Acceptance criteria for the follow-up (T18-fix1)

An error in one room's finish or trace write is logged and contained to that room; every other room keeps ticking; EVAL-T18-1's strict xfail passes and its author removes the mark at Gate 2.

## Follow-up evidence

T18-fix1: QA Gate 1 3124e13, Evaluation Gate 2 2062af4 (ACCEPT WITH NOTES), integrated at Gate 3 as `orch/reviewed` b2203c3; on `main` since PR #11 (a93d36a). Session record `docs/agent-sessions/T18-fix1-room-error-boundary.md`.

Saad's recorded answers at the time (AskUserQuestion, verbatim): #62 "Its fine the way it is"; #63 "let's add the server crash fix".

## Student decision

<!-- Saad writes this section in his own words. Agents leave it empty. -->
