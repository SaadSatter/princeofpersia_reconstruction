# Final project requirements checklist

Gate deliverables for *Shadow Masque*, with status and the decisions in force.
Evidence locations are in [`EVIDENCE_INDEX.md`](EVIDENCE_INDEX.md).

**Source of the deliverables:** the gate dates and deliverable names in
[`PROJECT_PLAN.md`](PROJECT_PLAN.md), taken from the course syllabus. The
official final-project guidelines and the course reader are **not in this
repository**. Saad: add them as `docs/final/FINAL_GUIDELINES.md` (unedited)
so agents can check against the rubric, not a summary of it.

Status values: **done** (evidence exists and is linked), **in progress**,
**not started**, **blocked** (waiting on a decision, named).

Updated 2026-11-16.

## Gates

| Gate | Date | Deliverable | Status | Notes |
| --- | --- | --- | --- | --- |
| G1 | Sun 15 Nov | Pitch recording | done | Linked from [`README.md`](README.md) |
| G1 | Sun 15 Nov | Pitch deck | done | Linked from [`README.md`](README.md) |
| G1 | Sun 15 Nov | Initial GDD | done | [`GDD.md`](GDD.md) |
| G1 | Sun 15 Nov | Initial Configuration Document, role coverage | done | [`CONFIGURATION.md`](CONFIGURATION.md) |
| G1 | Sun 15 Nov | Initial Project Plan and Risk Register | done | [`PROJECT_PLAN.md`](PROJECT_PLAN.md) |
| Week 9 | after G1 post | Silent-playtester notes on three midterm recordings | in progress | Saad writes them |
| — | Tue 17 Nov | G1 decision (Approve or Hold) | not started | Instructor |
| — | Thu 19 Nov | Braintrust: two replies in the G1 discussion | not started | Saad |
| Checkpoint | Mon 23 Nov | Deployed model call through the runner | not started | Needs a live call; Saad approves |
| Checkpoint | Mon 23 Nov | Isolated session state per seat | not started | Fake-provider test in CI |
| Checkpoint | Mon 23 Nov | Forced-timeout fallback | in progress | Single-seat fallback exists from the midterm; per-seat test needed |
| G2+G3 | Sat 28 Nov | First playable recording | not started | |
| G2+G3 | Mon 30 Nov | First playable build | not started | |
| G2+G3 | Mon 30 Nov | Initial Playtest Log | blocked | Format is CQ-6 |
| G2+G3 | Mon 30 Nov | Scope-lock plan | not started | Cut order: GDD Section 8 |
| G2+G3 | Mon 30 Nov | Update GDD and Configuration Document | not started | |
| G2+G3 | Mon 30 Nov | Updated Risk Register; Braintrust notes | not started | |
| G4 | Sat 5 Dec | Gold build recording | not started | |
| G4 | Mon 7 Dec | Final GDD and Configuration; Harness; Gold build; Playtest Log update | not started | |
| G5 | Mon 14 Dec | Final game and AAR; Playtest Log; optional System Card Response | not started | |
| Capstone | 17–23 Dec | Engineering & Design Retrospective, walkthrough, live presentation | not started | |

## Engineering requirements carried from the midterm

These still hold for every PR (`AGENTS.md`, midterm checks 2c, 3b, 3c):

| Requirement | Status for versus play |
| --- | --- |
| Engine headless, no `pygame` in `pop/` | done (test exists) |
| Deterministic reset and traces | done for one seat; two seats not started |
| Legal and illegal actions validated, refused action changes no state | done for one seat; two seats not started |
| Step, model-call and timeout limits with terminal reasons | done for one seat; per-seat limits not started |
| Hidden-information tests: current room only | done for one seat |
| Hidden-information tests: disguise identity, trap ownership | not started |
| A `test_regression_<issue>` test per observed bug | ongoing |

## Decisions in force (Saad, 2026-11-15)

From [`GDD.md`](GDD.md), "Decisions confirmed by Saad":

- Working title *Shadow Masque*.
- Two trap types: loose floor and gate plate; 4 traps per rival.
- 3 hearts per rival; 1 heart per stab, trap or damaging fall.
- One AI macro-action about every 4 s per AI seat (playability open: OQ-9).

Pending: engine choice recommendation in
[`ENGINE_DECISION.md`](ENGINE_DECISION.md) (stay on Python/Pygame).

## Open decisions blocking work

| ID | Blocks | Needed by |
| --- | --- | --- |
| OQ-2 | Disguise rules and their leak tests | Wed 18 Nov |
| OQ-5 | Taking a uniform from a downed guard | Wed 18 Nov |
| OQ-7 | Split-screen key map | Sun 22 Nov |
| CQ-1 | Macro-action vocabulary for the AI rival | Thu 26 Nov |
| CQ-6 | Playtest log format | Fri 27 Nov |
