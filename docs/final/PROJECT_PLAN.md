# Shadow Masque — Initial Project Plan

**Version:** Initial (G1), 2026-11-15
**Owner:** Saad Satter, as Producer
**Drafted by:** the implementation agent (Claude Code). Saad reviews and owns it.
**Current plan (2026-11-24):** this G1 plan is kept for the record. The plan in force is [`orchestration/PLAN-2026-11-23-v2.md`](orchestration/PLAN-2026-11-23-v2.md) with [`orchestration/PLAN-2026-11-23-v3-delta.md`](orchestration/PLAN-2026-11-23-v3-delta.md) (hosting by G2/G3). Task state is in [`orchestration/STATUS.md`](orchestration/STATUS.md). Where this file disagrees with them, they win; the changes that matter are in the risk notes below and in [`GDD.md`](GDD.md) and [`CONFIGURATION.md`](CONFIGURATION.md), "Changes since the last gate". Gate dates are unchanged.
**Next step (G1 text):** after the G1 decision, this plan moves into Asana, with owners, acceptance criteria and dependencies per task. The full Risk Register follows at G2/G3.

## Gate dates

From the course syllabus (weeks 9–13 and finals).

| Date | Gate or event | Due |
|---|---|---|
| Sun 15 Nov 2026, 11:59 p.m. | G1 post | Recording, deck, Initial GDD and Configuration Document, this plan and Risk Register |
| Mon 16 Nov 2026 (week 9) | **G1 Concept** review | — |
| Week 9, after the G1 post | Silent-playtester notes | Notes on three assigned midterm recordings (Saad) |
| Tue 17 Nov 2026 | G1 decision (Approve or Hold) | — |
| Thu 19 Nov 2026, 11:59 p.m. | Braintrust | Two replies in the G1 discussion |
| Mon 23 Nov 2026 (week 10) | Working session; **checkpoint**; graded G1 feedback | Deployed model call, isolated session state and forced-timeout fallback, in class or by recording |
| Sat 28 Nov 2026 | First playable recording | Recording |
| Mon 30 Nov 2026 (week 11) | **G2 Prototype and G3 Production**, combined | First playable; Initial Playtest Log; Scope-lock plan; Update GDD and Configuration Document; updated Risk Register; Braintrust notes |
| Sat 5 Dec 2026 | Gold build recording | Recording |
| Mon 7 Dec 2026 (week 12) | **G4 Final / Pre-Launch Review** | Final GDD and Configuration Document; Harness; Gold build; Update Playtest Log; Braintrust notes |
| Mon 14 Dec 2026 (week 13) | **G5 Retrospective / Closure**; showcase | Final game and AAR; Playtest Log; optional System Card Response |
| 17–23 Dec 2026 | Capstone presentations | Engineering & Design Retrospective with recorded walkthrough; live presentation |

## Goal through G2

By Sat 28 Nov (the first playable recording), two players can fight a full duel in a greybox arena, with disguises and traps, against each other or against the AI rival. At least one external playtest has been observed, so we know whether players misidentify the disguised rival.

## First tasks through G2

G2 is two weeks after G1, so the cut order in GDD Section 8 applies from the start.

| By | Task | Delegated role | Acceptance (initial) |
|---|---|---|---|
| Wed 18 Nov | Move this plan into Asana; add owners and acceptance criteria | Producer (Saad) | Asana project exists, linked from this file |
| Wed 18 Nov | Close OQ-2 and OQ-5 (disguise rules, downing guards) on paper | Design Lead (Saad) | GDD updated with decisions |
| Wed 18 Nov | Rule-map rows for sword, hearts, disguise and traps, labelled `design` | Design Lead, implementation agent | Rows in `docs/RULE_SOURCE_MAP.md` |
| Sun 22 Nov | Greybox arena: 3 rooms of our own layout; two rivals in one `GameState` | Tech Lead (implementation agent) | Two seats move in separate rooms through the interface; tests green |
| Sun 22 Nov | Game server (authoritative, WebSocket) and browser client on localhost; each client receives only its seat's observation | Tech Lead | Two browser tabs play one duel; leak test on the server's outgoing messages; tests green |
| Sun 22 Nov | **Checkpoint work:** AI rival seat makes a deployed model call through the runner; each seat has its own isolated session state; forced-timeout fallback | Tech Lead | Fake-provider tests for isolation and forced timeout in CI; one live call shown in class or by recording on Mon 23 Nov |
| Tue 24 Nov | `STRIKE` and `BLOCK`; 3 hearts, 1 per stab, trap or damaging fall; failing tests first | Tech Lead | Rule-invariant tests pass; rules-reviewer has no blocking findings |
| Wed 25 Nov | Disguise and scripted guard rule; leak test for disguise identity | Tech Lead, QA (`game-rules-audit`) | Audit report shows no leak |
| Wed 25 Nov | Traps: loose floor and gate plate, 4 per rival; leak test for trap ownership | Tech Lead, QA | Tests pass; audit report |
| Thu 26 Nov | Scripted rival on the existing baseline; AI rival in versus play | Tech Lead | Scripted rival beats a do-nothing rival on fixed seeds; CI green, no live calls in CI |
| Thu 26 Nov | Live tuning runs within the $5 cap; re-measure latency and cost (CQ-4) | Tech Lead, BI | Results JSON in `traces/live/` |
| Thu 26 Nov | Host the server (OQ-10) with our own or placeholder art (OQ-8) | Producer (Saad), Tech Lead | Two testers on different computers reach one duel |
| Fri 27 Nov | First playtest with external testers; Initial Playtest Log (CQ-6) | Design Lead, QA, BI | Observations recorded before interpretation |
| Fri 27 Nov | Scope-lock plan: what stays, what is cut | Producer, Design Lead | Document in `docs/final/` |
| Sat 28 Nov | **First playable recording** | Saad | Recording linked from `docs/final/README.md` |
| Sun 29 Nov | Update GDD, Configuration Document and Risk Register; Braintrust notes | Producer (Saad) | Documents labelled "Update" |

## Risk updates since G1 (2026-11-24)

The original rows below are kept. These dated notes record what changed in them. Ratings are not re-scored here; Saad owns the Risk Register update at G2/G3.

| Risk row | What changed | Source |
|---|---|---|
| Technology (AI decisions at about 3 s) | The AI rival is a small PPO policy deciding at 6-frame runner decisions with no model latency, not an LLM. The 3 s latency concern applies only to the legacy LLM player. The new risks are the untrained policy (no weights yet, so no strength claim), over-fitting to two tuning starts and a leak through the features | #3, #24; `agent-config.json` |
| Network (online delay) | Online human vs human is deferred, so network delay is not a G2/G3 risk. The hosted page runs the engine in the browser, so devtools could read hidden state: acceptable for human vs AI, not for online human vs human | #1, #12 |
| Business / Audience (pairs of testers) | Local two-panel human vs human is available on one computer and a human vs AI mode on the hosted page. Whether testers are found is unchanged | #1, #12 |
| Timeline (combat) | Combat, disguise and loose-floor traps are built on branches but not merged or playtested. The hosted build must be live by Sat 28 Nov (#13). New: the official-repository move is due the same day | #13, #6; `STATUS.md` |
| Spending (the "$5 live budget" in tasks below) | Replaced by under $1 total, smoke only; the PPO rival needs no paid call | #8 |
| IP / Concept | Unchanged. The hosted page is a static public build, so it must serve only our own art (OQ-8) | #12 |

Task rows in the G1 task table above that name Asana, a WebSocket server, two browser tabs, a live model call or the $5 cap are superseded by #10, #1/#12, #3 and #8 respectively; they are left as written.

## Initial Risk Register

The six-dimension Risk Profile from the pitch, in the reader's Section 5.4 form. It will be expanded at G2/G3.

| Risk | Evidence or trigger | Rating | Responsible role | Mitigation | Contingency |
|---|---|---|---|---|---|
| **IP / Concept:** if original art or names appear in a public build, the project infringes Ubisoft's rights | *Prince of Persia* belongs to Ubisoft; the source README grants no rights | High | Producer | Original title and rooms; original art only on the private course branch; placeholders in public | Ship with placeholder art only |
| **Technology:** if AI decisions stay at about 3 s, the AI rival cannot keep up in a sword fight | Measured mean latency 3.0 s (single player) | High | Tech Lead | Macro-actions only; scripted frames; 5 s timeout with labelled fallback | Scripted rival only; AI vs AI becomes test-only |
| **Genre / Mechanics:** if the greybox duel is not fun, the concept fails | Combat was deferred in the midterm; disguise and traps are untested | High | Design Lead | Greybox duel and paper test in week 1, before art | Cut to 3 rooms and one trap type |
| **Business / Audience:** if pairs of testers are hard to find, the playtest question goes unanswered | Needs two people online at the same time; no playtest yet | Medium | Producer | AI seat lets one person play | Test human vs AI only |
| **Network:** if network delay makes sword timing feel unfair, the duel fails online | Online play decided 2026-11-16; nothing measured yet | Medium | Tech Lead | One authoritative server; small messages (one seat's observation); measure round-trip time at the first playtest (OQ-12) | Two computers on one local network |
| **Team:** if Saad's review capacity runs out, changes ship unreviewed | One student plus an agent team | Medium | Producer | Independent reviewer agent; small, explainable changes | Reduce scope per the cut order |
| **Timeline:** if combat takes longer than a week, everything after it slips | G2 is Mon 30 Nov, two weeks after G1; combat, two players and traps are new | Medium | Producer | Cut order in the GDD, Section 8 | Rooms 6 → 3, then the suspicion meter, then one trap type |

**Shared cause:** the Technology and Genre/Mechanics Highs both come from real-time combat that is not built yet. The IP High is separate, and online play raises it: a reachable server must not serve the original sprites (GDD OQ-8).
