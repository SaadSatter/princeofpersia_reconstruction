# Decisions 2026-11-26

## G2/G3 readiness (session c612c020)

Saad's choices (AskUserQuestion), quoted verbatim. Recorded by the orchestrator (session c612c020).

| # | Question (short) | Saad's answer (verbatim choice) | Orchestrator's reading and effect |
|---|---|---|---|
| 103 | When to merge PR #12 (orch/reviewed dfe2d90 → main) and PR #6 (T10a docs) | "Merge both once green (Recommended)" | Saad merges both himself after the orchestrator posts the suite result on the PR #12 merge. T03 copies `main` only after both merges |
| 104 | How `main` reaches `columbia-university-ai-games/final-saadsatter` (T03) | "Copy files, keep template (Recommended)" | Copy the game and gate files into the official repository's `main`, keeping its `team/`, `final.yml` and template files. One commit, no shared history |
| — | Which Saad-only items are done (playtest, recording, Student decision, coverage map) | "What do you mean student decision in handoff draft? Isnt that what you have been doing, you are handoffing work to different agents?" | No item marked done. Saad asked for an explanation of the Student decision; answered in chat. Not a decision |

## Addendum: Thu 2026-11-26 (T23 status, step size, scrolling arena)

Saad's request: "every movement left or right, moves the player many units left and right, it shouldnt move them so much. Maybe to make the game smoother, make it a side scroller platform game, instead of 6 discontinuous maps". His choices (AskUserQuestion), quoted verbatim. Recorded by the orchestrator (session 8e40f288). He also asked: "also record this as student decision for a handoff between orchestrator and tech lead". The orchestrator does not write Student decisions (HANDOFF_PROTOCOL), so it drafted `handoff-drafts/2026-11-26-orchestrator-to-tech.md` with that section left for Saad.

| # | Question (short) | Saad's answer (verbatim choice) | Orchestrator's reading and effect |
|---|---|---|---|
| 105 | T23-fix1 now that T22 is closed? | "Dispatch now (Recommended)" | T23-fix1 runs from `orch/reviewed` dfe2d90 with `task/T23` 0c7d73a merged in |
| 106 | How should a left/right tap behave (whole-block moves, R-D01/R-C07)? | "Investigate first (Recommended)" | Task T26: measure tap and hold in every front end, then propose options with numbers. No rule change until Saad picks |
| 107 | Six rooms (OQ-4) → one continuous side-scroller? | "Feasibility study first (Recommended)" | Task T27: scoped report (view window in place of "own room", hidden information, server boundary, PPO, schedule). No code until Saad decides |
| 108 | T27 option: (a) camera, (b) scrolling window post-gold / now, or no change | Other: "Perform the scrolling window change in a seperate branch or worktree so it doesn't impact the current workings but we should get starting on it sooner than later" | Option (b), started now on its own line (`experiment/scroll`, from dfe2d90), isolated from `orch/reviewed` and the gold build. Its sub-decisions (layout, window, retrain) go to Saad before the build brief |

## G2/G3 readiness, continued (session c612c020)

Renumbered from #109–#111 (b4aa069) to **#116–#118** (corrected 2026-11-26: an earlier renumbering, f7ab21b, wrongly also changed the parallel session's #109–#111 and collided with its #113–#114; both restored). The parallel session's rows are #109–#114. Brief T28 (CI) renamed T29 for the same reason.

Saad's choices (AskUserQuestion) after AUDIT-G23, quoted verbatim.

| # | Question (short) | Saad's answer (verbatim choice) | Orchestrator's reading and effect |
|---|---|---|---|
| 116 | Student decision record for G2/G3 | "You can do A and tell me a sample of what #62 and 63 reasoning would be, and then give me the file path to fill it in" | The routed handoff is the T18 chain (`handoff-drafts/2026-11-24-qa-eval-to-tech-T18.md`, 5e2e16c). Saad writes its Student decision himself; the orchestrator gave a sample in chat only |
| 117 | Agent tasks for Saturday | "CI fix, T10b docs refresh, T03 move, Session record" | Briefs T29 (CI), T10b, T03; session record at the end. **Amends #103:** PR #6 is not merged as is; T10b refreshes it first (AUDIT-G23: its "Changes since" stops at #30) |
| 118 | G2/G3 gameplay freeze | "Freeze after T23-fix1 (Recommended)" | T23-fix1 may land if its gates close by Fri 2026-11-27 night; T26, T27 and the #108 scrolling branch wait until after Sat 2026-11-28 for the graded `main` |
| 109 | Scrolling layout | "Scroll both axes (Recommended)" | Keep the 3x2 loop and shaft (OQ-4 layout kept); the view scrolls horizontally and vertically over the joined rooms |
| 110 | View window size (replaces "own room", CQ-1) | "One room's size (Recommended)" | 10 columns x 3 rows centred on the seat's own rival; visible iff inside the window |
| 111 | PPO retrain on the scrolling line | "Ask me then (Recommended)" | No training run until the engine passes QA and Eval and Saad approves with runtime and cost known |
| 112 | Tap size (T26) | Other: "Land T23-fix1 and merge it in before doing anything else" | T23-fix1 goes through its gates and is integrated into `orch/reviewed` first. T28 (scrolling) is dispatched only after that, from the new tip. No tap-size rule change |
| 113 | T23-fix1: `test_server_match.py` replay test ignores releases | "Use trace.replay (Recommended)" | Approved edit to that existing test: replay through `server.trace.replay(tr)`; listed old → new |
| 114 | T23-fix1: `test_t22fix2_overlap.py::test_ai_room_logs_only_the_human_seat` ends `duel_end`, `rematch` | "Accept rematch row (Recommended)" | Approved edit to that existing test: accept a `rematch` row after `duel_end`; listed old → new |

## Merges for G2/G3 (session c612c020, 2026-11-27)

| # | Question (short) | Saad's answer (verbatim) | Orchestrator's reading and effect |
|---|---|---|---|
| 119 | Merge PR #12 and PR #13 into `main` | "Merge in the the PRs" | PR #12 merged by the orchestrator (4e20b83, CI green). PR #13 merged locally (271d1ee) because GitHub reported a false conflict (two merge bases); CI run 46038977033 on 271d1ee succeeded before `main` was moved to it. PR #6 (superseded by #13) is left open for Saad to close. T03 may start (brief `tasks/T03.md`) |

| # | Question (short) | Saad's answer (verbatim choice) | Orchestrator's reading and effect |
|---|---|---|---|
| 120 | Which handoff carries the G2/G3 Student decision | "Commit it, use T02 (Recommended)" | Saad wrote his Student decision in `handoff-drafts/2026-11-24-qa-to-tech.md` (T02 → T01, R-V23 re-review; his pick #7). Committed unchanged from his working copy. T03 carries T02 as the graded handoff; the T18 record goes too, its decision empty. Supersedes the handoff choice in #116 |

## Coverage map and role approval (session c612c020, 2026-11-27)

Saad's message, quoted verbatim (his own words; the coverage-map lines go into `agent-team/other-roles.md` on official PR #2 as he wrote them):

> For the coverage map, use the following decisions:
>
> - producer: student — I own production priorities, scope, milestones, approvals and resource allocation, supported by the orchestrator.
> - design: student — I own gameplay mechanics, balancing, controls and the intended player experience.
> - art: student — I direct the visual style and approve assets, using AI-assisted asset generation where appropriate.
> - narrative: not needed, because Shadow Masque is a competitive stealth platformer without a substantial narrative or dialogue system.
> - bi: student — I oversee evaluation and playtest analysis, supported by the Evaluation Specialist and telemetry tools. We can consider establishing a formal BI agent for G4 based on documented production friction.
> - release: student — I retain authority over merges, deployment, release approval and course submissions, with technical assistance from the production agents.
>
> I approve the Tech Lead and QA role definitions. Ensure QA's declared permissions allow it to write tests and handoff notes, but never modify production game code.
>
> Show me the current SCOPE_LOCK.md before I approve it.
>
> Update the coverage map, regenerate the course team artifacts using `python -m team render`, and run `python -m team validate`. Preserve these as my student decisions on PR #2.

| # | Decision | Effect |
|---|---|---|
| 121 | Coverage map (the six lines above) | `agent-team/other-roles.md` on `g23-migration` gets Saad's lines verbatim; render + validate |
| 122 | Tech Lead and QA course roles approved; QA never modifies production game code | `agent-team/roles/qa.md` `permissions.writes` states the limit explicitly; render + validate |
| — | SCOPE_LOCK.md | Shown to Saad; not yet approved |

## Scope lock refresh (session c612c020, 2026-11-27)

Saad's message, quoted verbatim:

> Yes, proceed with the documentation refresh and have QA independently review it.
>
> For the scope lock:
>
> - Update the stale CI, three-mode menu, hosted page and T23-fix1 references to reflect their current status.
> - Keep the external playtest marked as pending until I conduct it.
> - LAN-based online multiplayer is sufficient for the current gate. A public multiplayer server is not required.
> - Do not categorically exclude PPO retraining, AI trap usage, movement adjustments or other gameplay improvements. Defer them for now, but allow reconsideration based on external playtest findings and evaluation evidence, subject to my approval.
> - Do not exclude a formal telemetry analyst or BI agent. This remains a potential third production role for G4.
> - Preserve the actual PPO evaluation result and its NOT SUPPORTED conclusion. Do not change the success threshold retrospectively.
> - Preserve the distinction between the hosted frontend and the LAN multiplayer server.
>
> The current playable build should be our scope baseline, but I want to retain the ability to make evidence-driven improvements before Gold.
>
> Once QA has reviewed the refreshed document, show it to me for final approval before copying it into PR #2.
>
> The coverage map formatting is acceptable. Do not modify the course's tooling just to display my explanations in the generated map.

| # | Decision | Effect |
|---|---|---|
| 123 | Scope lock refresh rules (above) | Task T30 (tech-lead → qa → Gate 3 → shown to Saad → PR to `main` and copy into official PR #2 only after his approval) |
| 124 | Coverage-map formatting accepted; course tooling not modified | No change to `team/` |

| # | Question (short) | Saad's answer (verbatim choice) | Effect |
|---|---|---|---|
| 125 | Official `final.yml` 10-minute limit vs an 8–9 minute suite | "Run a smaller suite" | Task T31: keep `timeout-minutes: 10`; "Your tests" runs a fast deterministic subset; the full suite stays in `shadow_masque` CI |
| 126 | Playtest kit approval (asked: approve PROTOCOL.md, the hypotheses in LOG.md, the Section 3 definitions, and the telemetry consent sentence before the session) | "Everything is approved" | The playtest kit is approved and frozen as of 2026-11-27: `playtest/PROTOCOL.md` (incl. Section 3 definitions), the hypotheses in `playtest/LOG.md`, `CONSENT.md` with the telemetry sentence drafted in `TELEMETRY.md` ("Draft for CONSENT.md"). Task T32 records the status in those files. Read as **not** covering `SCOPE_LOCK.md`, which Saad asked to see after QA (#123) |
