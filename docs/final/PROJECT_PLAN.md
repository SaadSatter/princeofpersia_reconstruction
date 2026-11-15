# Shadow Masque — Initial Project Plan

**Version:** Initial (G1), 2026-11-15
**Owner:** Saad Satter, as Producer
**Drafted by:** the implementation agent (Claude Code). Saad reviews and owns it.
**Next step:** after the G1 decision, this plan moves into Asana, with owners, acceptance criteria and dependencies per task. The full Risk Register follows at G2/G3.

## Gate dates

| Date | Gate or event |
|---|---|
| Mon 9 Nov 2026 | First pitch round (sixty-second pitch) — done |
| Sun 15 Nov 2026, 11:59 p.m. | G1 post due: recording, deck, GDD, Configuration Document, this plan |
| Mon 16 Nov 2026 | **G1 Concept review** in class |
| Tue 17 Nov 2026 | G1 decision (Approve or Hold) posted on CourseWorks |
| Thu 19 Nov 2026, 11:59 p.m. | Two Braintrust replies due |
| Mon 23 Nov 2026 | Graded G1 feedback returned |
| **[Open] — see syllabus** | **G2 Prototype / G3 Production** (combined review) |
| [Open] — see syllabus | G4 Final / Pre-Launch Review |
| [Open] — see syllabus | G5 Retrospective / Closure |

The G2–G5 dates are not in the course repository. Fill them in from the published syllabus.

## Goal through G2

By G2, two players can fight a full duel in a greybox arena, with disguises and one or two traps, against each other or against the AI rival. We will know whether players misidentify the disguised rival, from at least one observed external playtest.

## First tasks through G2

| Week | Task | Delegated role | Acceptance (initial) |
|---|---|---|---|
| 16 Nov | Move this plan into Asana; add owners and acceptance criteria | Producer (Saad) | Asana project exists, linked from this file |
| 16 Nov | Close OQ-1, OQ-2 and OQ-5 (health, disguise rules, downing guards) on paper | Design Lead (Saad) | GDD updated with decisions |
| 16 Nov | Rule-map rows for sword, disguise and traps, labelled `design` | Design Lead, implementation agent | Rows in `docs/RULE_SOURCE_MAP.md` |
| 16 Nov | Greybox arena: 3 rooms of our own layout; two rivals in one `GameState`; split-screen view | Tech Lead (implementation agent) | Two humans can move in separate rooms; tests green |
| 23 Nov | `STRIKE` and `BLOCK`, with failing tests first | Tech Lead | Rule-invariant tests pass; rules-reviewer has no blocking findings |
| 23 Nov | Disguise and scripted guard rule; leak test for disguise identity | Tech Lead, QA (`game-rules-audit`) | Audit report shows no leak |
| 23 Nov | Traps: loose floor and gate plate; leak test for trap ownership | Tech Lead, QA | Tests pass; audit report |
| 23 Nov | Scripted rival on the existing baseline | Tech Lead | Wins against a do-nothing rival on fixed seeds |
| 30 Nov | AI rival through the existing runner; fake-provider tests | Tech Lead | CI green; no live calls in CI |
| 30 Nov | Live tuning runs within the $5 cap; re-measure latency and cost (CQ-4) | Tech Lead, BI | Results JSON in `traces/live/` |
| 30 Nov | First playtest with external pairs; playtest log (CQ-6) | Design Lead, QA, BI | Observations recorded before interpretation |
| Before G2 | Update GDD, Configuration Document, plan and Risk Register | Producer (Saad) | Documents labelled "Update" |

Tasks are in week order. Exact dates depend on the G2 date.

## Initial Risk Register

The six-dimension Risk Profile from the pitch, in the reader's Section 5.4 form. It will be expanded at G2/G3.

| Risk | Evidence or trigger | Rating | Responsible role | Mitigation | Contingency |
|---|---|---|---|---|---|
| **IP / Concept:** if original art or names appear in a public build, the project infringes Ubisoft's rights | *Prince of Persia* belongs to Ubisoft; the source README grants no rights | High | Producer | Original title and rooms; original art only on the private course branch; placeholders in public | Ship with placeholder art only |
| **Technology:** if AI decisions stay at about 3 s, the AI rival cannot keep up in a sword fight | Measured mean latency 3.0 s (single player) | High | Tech Lead | Macro-actions only; scripted frames; 5 s timeout with labelled fallback | Scripted rival only; AI vs AI becomes test-only |
| **Genre / Mechanics:** if the greybox duel is not fun, the concept fails | Combat was deferred in the midterm; disguise and traps are untested | High | Design Lead | Greybox duel and paper test in week 1, before art | Cut to 3 rooms and one trap type |
| **Business / Audience:** if pairs of testers are hard to find, the playtest question goes unanswered | Needs two people at one machine; no playtest yet | Medium | Producer | AI seat lets one person play | Test human vs AI only |
| **Team:** if Saad's review capacity runs out, changes ship unreviewed | One student plus an agent team | Medium | Producer | Independent reviewer agent; small, explainable changes | Reduce scope per the cut order |
| **Timeline:** if combat takes longer than a week, everything after it slips | Engine exists; combat, two players and traps are new | Medium | Producer | Cut order in the GDD, Section 8 | Rooms 6 → 3, then the suspicion meter, then one trap type |

**Shared cause:** the Technology and Genre/Mechanics Highs both come from real-time combat that is not built yet. The IP High is separate.
