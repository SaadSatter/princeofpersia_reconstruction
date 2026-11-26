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

Updated 2026-11-16; decisions and notes brought up to 2026-11-24 (task T10a) and again to 2026-11-26 (task T10b). Where a row says "on `orch/reviewed`", it is in PR #12 (open) and not yet on `main`. The G2/G3 date is **Sat 28 Nov 2026, 11:59 p.m.** (`orchestration/inputs/FINAL_REQUIREMENTS.md` section 6), not Mon 30 Nov. Task state: [`TRACKER.md`](TRACKER.md); branch state: [`orchestration/STATUS.md`](orchestration/STATUS.md).

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
| Checkpoint | Mon 23 Nov | Deployed model call through the runner | not started | Needs a live call; Saad approves. Since 2026-11-23 the AI rival is a PPO policy (#3), which makes no provider call; live spending is capped under $1, smoke only (#8). How the checkpoint applies is Saad's call |
| Checkpoint | Mon 23 Nov | Isolated session state per seat | done | Seat-controller protocol and versus runner closed at Gate 3 (T04, T04-fix3), on `main` (each seat has its own observation, history and controller) |
| Checkpoint | Mon 23 Nov | Forced-timeout fallback | done | Per-seat labelled `WAIT` fallback, 5 s timeout, abort over the limit (#24), on `main`; online live AI seat 0.04 s budget, log-only fallbacks (#45, #49) |
| G2+G3 | Sat 28 Nov | First playable recording | not started | Saad records it. The build exists (pygame menu on `orch/reviewed`, online server and hosted page on `main`); no hosted URL (Pages deploy returned 404 on 2026-11-26) |
| G2+G3 | Sat 28 Nov | First playable build | in progress | Duel, disguise, scripted guards, trained rival, online play: built. Needs PR #12 merged, CI green (T29) and the official-repository copy (T03) |
| G2+G3 | Sat 28 Nov | Initial Playtest Log | blocked | No external playtest has been run. [`playtest/LOG.md`](playtest/LOG.md) is an empty template; the protocol, hypotheses and consent sentence are drafts that Saad has not approved |
| G2+G3 | Sat 28 Nov | Scope-lock plan | in progress | Draft [`SCOPE_LOCK.md`](SCOPE_LOCK.md), not approved by Saad. Cut order: GDD Section 8 |
| G2+G3 | Sat 28 Nov | Update GDD and Configuration Document | in progress | Dated "Changes since the last gate" entries of 2026-11-26 cover decisions #31 to #118 (T10b, pending QA and Saad's merge); the 2026-11-24 entries are kept as history |
| G2+G3 | Sat 28 Nov | Updated Risk Register | not started | Dated risk notes of 2026-11-26 are in [`PROJECT_PLAN.md`](PROJECT_PLAN.md); Saad owns the re-scoring |
| G2+G3 | Mon 30 Nov | Three Braintrust replies | not started | Saad. Due Mon 30 Nov, 11:59 p.m. |
| G4 | Sat 5 Dec | Gold build recording | not started | |
| G4 | Mon 7 Dec | Final GDD and Configuration; Harness; Gold build; Playtest Log update | not started | |
| G5 | Mon 14 Dec | Final game and AAR; Playtest Log; optional System Card Response | not started | |
| Capstone | 17–23 Dec | Engineering & Design Retrospective, walkthrough, live presentation | not started | |

## Engineering requirements carried from the midterm

These still hold for every PR (`AGENTS.md`, midterm checks 2c, 3b, 3c):

| Requirement | Status for versus play |
| --- | --- |
| Engine headless, no `pygame` in `pop/` | done (test exists) |
| Deterministic reset and traces | done for one seat; two seats done (`tests/test_versus.py`, `test_swordplay.py`, `test_guards.py`, `test_disguise.py`), on `main` |
| Legal and illegal actions validated, refused action changes no state | done for one seat; two seats done (`tests/test_versus.py::test_refused_input_changes_nothing_and_is_counted`) |
| Step, model-call and timeout limits with terminal reasons | done: versus runner with the 3,600-frame limit, 6-frame cadence and 5 s timeout, on `main` (#5, #24) |
| Hidden-information tests: current room only | done for one seat |
| Hidden-information tests: disguise identity, trap ownership | disguise identity and suspicion done (`tests/test_disguise.py`); flips and bodies out of sight done (`tests/test_flip_review.py`, R-V22, R-V23); trap ownership done for the loose-floor rig (T06b, closed at Gate 2), on `main`; gate plate not built |
| Server sends each client only its own seat's observation | done for the online server (T13, T18, T25; boundary tests at Gate 2 with notes). Not yet run on two real machines. The hosted static page (#12) has no server: its bridge draws one seat only, but the whole state lives in the browser, which is accepted for human vs AI only |
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

Saad, 2026-11-17 ([`VERSUS_SPEC.md`](VERSUS_SPEC.md), **approved as written**,
including its numbers, observation fields and key map):

- Swordplay in the style of *Nidhogg* (stances, matched-height blocks,
  disarms); lunge, sword throw, dive kick and sweep in the first playable;
  3 hearts kept.
- CQ-1 timing: real-time ticks, 12 frames per second, both seats overlap.
- OQ-2 and OQ-5: guards downed for good by one clean hit or a trap; DOWN
  takes the uniform; suspicion meter kept, shown only to the suspected rival.

Pending: engine choice recommendation in
[`ENGINE_DECISION.md`](ENGINE_DECISION.md) (stay on Python/Pygame).

Saad, 2026-11-23 and 2026-11-24 (verbatim answers and the orchestrator's reading:
[`orchestration/DECISIONS-2026-11-23.md`](orchestration/DECISIONS-2026-11-23.md),
[`orchestration/DECISIONS-2026-11-24.md`](orchestration/DECISIONS-2026-11-24.md);
what each changes: [`GDD.md`](GDD.md) and [`CONFIGURATION.md`](CONFIGURATION.md),
"Changes since the last gate"):

- #1 online play deferred, shown locally; #12, #13 a hosted Pyodide + Phaser
  build by G2/G3 (online human vs human still deferred); #25 pins (Pyodide
  0.27.7, Phaser 3.88.2).
- #2, #22 traps are a G2 target: one-shot, 4 per rival, owner can be hurt,
  loose floor first; closes OQ-6.
- #3 the AI rival is a small PPO policy we train (the Haiku model player is
  legacy); #23 macro vocabulary, closes CQ-1; #24 runner policy (6-frame
  cadence, 5 s timeout, labelled `WAIT` fallback, `seed_key`).
- #5 duel limit 5 minutes = 3,600 frames; closes OQ-3.
- #4, #18 hop while disguised +48 suspicion; #15 `TAKE` always legal; #17
  R-V25 masking; #19 lingering; #20, #21 test changes at integration.
- #8 live spending under $1, smoke only (replaces $5); #9 scenarios D1, B2,
  I3, F5 and held-out H6.
- #6, #10 official-repository method and tracker in this repository; the move
  is due Sat 28 Nov, 11:59 p.m.
- #7 the T02/T01 chain is the routed handoff; Saad writes the Student decision.
- #14, #26 to #29 GitHub handoffs, publishing, pushing and commits to `main`
  under the orchestration rules; merging stays Saad's. #16 workers use Sonnet.
- #30 "Update the outdated docs" (T10a, then refreshed by T10b).
- #31 to #118, 2026-11-24 to 2026-11-26: CLIMB both ways (#31); online human vs human restored, LAN server, rooms, disconnect rule (#35 to #38, #41, #45 to #49, #52 to #57, #62, #63, #95 to #97, #102); numpy and websockets as extras (#34, #37, #40); PPO training and evaluation (#42 to #44, #47, #50, #51, #58 to #66, #71, #74 to #80, #84); controls, flip, grace window and kneel (#53 to #55, #73, #89, #94, #98, #101); playtest telemetry (#67 to #69, #81 to #83, #85, #86); three modes (#87 to #92); the side-scroller and step-size studies and the freeze (#105 to #108, #118); official-repository copy and Student decision (#103, #104, #116, #117). What each changes: [`GDD.md`](GDD.md) and [`CONFIGURATION.md`](CONFIGURATION.md), "Changes since the last gate (as of 2026-11-26)". Decisions #103 to #118 are in [`orchestration/DECISIONS-2026-11-26.md`](orchestration/DECISIONS-2026-11-26.md).

## Open decisions blocking work

Closed since 2026-11-16: OQ-11 (#12, #25), CQ-1 (#23), OQ-3 (#5), OQ-6 (#22),
CQ-7 (commit 2d40972); closed 2026-11-24 to 26: OQ-7 (#55, #89), OQ-10 for
G2/G3 (#36), OQ-13 (#38), the B2 threshold (#58, #76), D1 "on screen" (#59),
CLIMB down (#31). Still open or waiting on Saad: the rows below, plus the
items in [`orchestration/STATUS.md`](orchestration/STATUS.md) "Waiting on
Saad" (sprung trap costs 1 heart in all, macro cadence of 4 decisions,
nearest-figure targeting, reward defaults, the T19 suspicion surcharge, the
the T26 tap-size option, the playtest protocol and consent sentence, the Student
decision, and the official-repository move; the scope lock draft needs his
approval).


| ID | Blocks | Needed by |
| --- | --- | --- |
| OQ-11 | ~~Browser client technology~~ closed 2026-11-23 (#12) | Sun 22 Nov |
| OQ-7 | ~~Key map~~ closed 2026-11-24/25 (#55, #89) | Sun 22 Nov |
| OQ-10 | ~~Hosting of a game server~~ closed for G2/G3 2026-11-24 (#36, Saad's laptop on a LAN); the static page's Pages deploy is blocked (404) | Thu 26 Nov |
| CQ-1 | ~~Macro-action vocabulary for the AI rival~~ closed 2026-11-23 (#23) | Thu 26 Nov |
| CQ-6 | Playtest log format (kit drafted, unapproved) | Fri 27 Nov |
| OQ-12 | Network delay a sword fight tolerates (no two-machine run yet) | Playtest |
