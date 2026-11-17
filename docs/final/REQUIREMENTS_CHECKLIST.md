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
| Server sends each client only its own seat's observation | not started |
| A `test_regression_<issue>` test per observed bug | ongoing |

## Decisions in force (Saad, 2026-11-15)

From [`GDD.md`](GDD.md), "Decisions confirmed by Saad":

- Working title *Shadow Masque*.
- Two trap types: loose floor and gate plate; 4 traps per rival.
- 3 hearts per rival; 1 heart per stab, trap or damaging fall.
- One AI macro-action about every 4 s per AI seat (playability open: OQ-9).

Saad, 2026-11-16:

- Online play, each rival on their own screen, instead of local split screen
  (a shared screen lets each player see the other's view).
- OQ-8: our own medieval stone dungeon art made with PixelLab plus
  hand-drawn frames (32 px rivals and guards, background pillars, iron
  portcullis gates), committed in `assets/generated/`. PixelLab's terms of
  30 Oct 2026 permit publishing outputs (Saad's reading).
  [`ART_PROVENANCE.md`](ART_PROVENANCE.md). SakPix demo art rejected (style
  clash; redistribution unclear).
- OQ-4: a six-room arena, `pop/arena.py`.

Saad, 2026-11-17 ([`VERSUS_SPEC.md`](VERSUS_SPEC.md), draft awaiting approval
of its numbers):

- Swordplay in the style of *Nidhogg* (stances, matched-height blocks,
  disarms); lunge, sword throw, dive kick and sweep in the first playable;
  3 hearts kept.
- CQ-1 timing: real-time ticks, 12 frames per second, both seats overlap.
- OQ-2 and OQ-5: guards downed for good by one clean hit or a trap; DOWN
  takes the uniform; suspicion meter kept, shown only to the suspected rival.

Pending: engine choice recommendation in
[`ENGINE_DECISION.md`](ENGINE_DECISION.md) (stay on Python/Pygame).

## Open decisions blocking work

| ID | Blocks | Needed by |
| --- | --- | --- |
| VERSUS_SPEC | Approval of the proposed numbers, observation fields and key map in `VERSUS_SPEC.md` | Wed 18 Nov |
| OQ-11 | Browser client technology | Sun 22 Nov |
| OQ-7 | Key map | Sun 22 Nov |
| OQ-10 | Hosting | Thu 26 Nov |
| CQ-1 | Macro-action vocabulary for the AI rival | Thu 26 Nov |
| CQ-6 | Playtest log format | Fri 27 Nov |
