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

Saad's choices (AskUserQuestion) after AUDIT-G23, quoted verbatim.

| # | Question (short) | Saad's answer (verbatim choice) | Orchestrator's reading and effect |
|---|---|---|---|
| 109 | Student decision record for G2/G3 | "You can do A and tell me a sample of what #62 and 63 reasoning would be, and then give me the file path to fill it in" | The routed handoff is the T18 chain (`handoff-drafts/2026-11-24-qa-eval-to-tech-T18.md`, 5e2e16c). Saad writes its Student decision himself; the orchestrator gave a sample in chat only |
| 110 | Agent tasks for Saturday | "CI fix, T10b docs refresh, T03 move, Session record" | Briefs T28 (CI), T10b, T03; session record at the end. **Amends #103:** PR #6 is not merged as is; T10b refreshes it first (AUDIT-G23: its "Changes since" stops at #30) |
| 111 | G2/G3 gameplay freeze | "Freeze after T23-fix1 (Recommended)" | T23-fix1 may land if its gates close by Fri 2026-11-27 night; T26, T27 and the #108 scrolling branch wait until after Sat 2026-11-28 for the graded `main` |
