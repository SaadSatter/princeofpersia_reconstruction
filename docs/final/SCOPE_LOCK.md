# Shadow Masque: scope lock for G2/G3

**Draft, not approved by Saad.** Written 2026-11-26 by the tech-lead worker (task T10b) from Saad's recorded decisions. Every line cites the decision it comes from. Nothing here is a new decision. Saad approves, edits or rejects it; until he does, it is a proposal. Decision files: [`DECISIONS-2026-11-23.md`](orchestration/DECISIONS-2026-11-23.md), [`DECISIONS-2026-11-24.md`](orchestration/DECISIONS-2026-11-24.md) (to #102), `DECISIONS-2026-11-26.md` (#103 and later, on `main`). Where a decision number is shared by two sessions (#109 to #112 and #113 to #115), the orchestrator's renumbering applies.

Approval line for Saad: `Approved by Saad: ______ (date)`.

## In scope for the graded G2/G3 build

| Item | Decision |
| --- | --- |
| Two rivals in one `GameState`, sword strike and block, 3 hearts, disguise and uniform taking, suspicion, scripted guards | G1 decisions in [`GDD.md`](GDD.md); #4, #15, #17 to #19 |
| Six-room arena of our own layouts (OQ-4) | G1 (2026-11-16); kept for G2/G3 by #115 |
| One duel is 5 minutes = 3,600 frames; a time-up is a draw | #5 |
| Loose-floor traps: one-shot, 4 per rival, owner can be hurt | #2, #22 |
| AI rival is a small PPO policy we trained, plus a scripted baseline on the same interface | #3, #23, #24, #51 |
| Three modes: AI Model (trained), Baseline (scripted), Human vs Human, in pygame, the hosted page and the online server | #87, #88, #92 |
| Online human vs human on a LAN: Saad's laptop, rooms with a 4-letter code, pause 15 s then forfeit, rematch when both press | #35 to #38, #41, #46, #48, #52, #56, #57 |
| Private one-click AI and Baseline matches online | #95 to #97, #102 |
| Hosted static page (Pyodide 0.27.7, Phaser 3.88.2) for human vs AI | #12, #13, #25 |
| Controls: WASD or arrows on a player's own machine; flip jumps; 2-tick grace; kneel takes the uniform | #53 to #55, #89, #94, #98, #101 |
| Scenario suite D1, B2, I3, F5 and held-out H6, with the one held-out result reported as it came out | #9, #58 to #66, #74 to #80 |
| Optional host-side playtest telemetry, off by default | #67 to #69 |
| Paid model calls under $1 total, smoke only; the PPO rival needs none | #8 |
| Fix for the "direction keeps running after landing" bug (T23-fix1), only if its gates close by Fri 2026-11-27 night | #93, #105, #115 |
| Deterministic CI green on `main` (T29) and the official-repository copy (T03) | #104, #114 |

## Out of scope for G2/G3

| Item | Decision |
| --- | --- |
| Gate-plate trap (loose floor only) | #2, #22 (gate plate "if there is time"; not built) |
| The AI rival rigging traps (`RIG_TRAP` masked for it) | #43 |
| Retraining the PPO rival | #51 (one run), T09 note: weights kept; a retrain needs Saad's approval with runtime and cost known (decision #111, scrolling session: "ask me then") |
| A side-scrolling view in place of six rooms; any change to tap or step size | #106, #107, #108, #112, #115 (study done; build on `experiment/scroll`, after Sat 2026-11-28) |
| Accounts, matchmaking, a public-internet game server, levels 2 to 14, original level data, sound, adaptive guards, more than two players | GDD Section 8 (G1) |
| LLM rival in the game (the Haiku player stays as the legacy midterm rival) | #3 |
| Any further gameplay change after T23-fix1 | #115 |
| A formal course production-agent role for `telemetry-analyst` | #69 |

## Cut order, if time runs out

From GDD Section 8, unchanged: 1. rooms 6 to 3; 2. suspicion meter to a yes/no rule; 3. one trap type (already the case: loose floor only); 4. AI vs AI becomes test-only; 5. public hosting to two computers on one local network (already the case for online play, #36). Never cut the duel or the disguise.

## Known limitations to state at the gate

| Limitation | Evidence |
| --- | --- |
| The trained rival did not beat the baseline at the pre-registered bar: 13 W, 2 D, 1 L of 16 held-out duels, bar 14, "NOT SUPPORTED" (#77) | [`evaluation/RESULTS-T09.md`](evaluation/RESULTS-T09.md) |
| The rival's own inference errors were not recorded in the held-out rows (#84) | [`evaluation/RESULTS-T09.md`](evaluation/RESULTS-T09.md) |
| No external playtest; the playtest protocol and consent sentence are unapproved drafts | [`playtest/LOG.md`](playtest/LOG.md) |
| Online play is tested on localhost only; not run on two machines; no latency measurement (OQ-12) | [`ONLINE_PLAY.md`](ONLINE_PLAY.md) |
| No hosted page URL; the GitHub Pages deploy returned 404 on 2026-11-26. The hosted page runs the engine in the browser, so devtools can read hidden state (accepted for human vs AI only) | [`WEB_BUILD.md`](WEB_BUILD.md), GDD "Changes since" |
| Left/right taps move a whole block; a held key can move two blocks until T23-fix1 lands | T26 report (`task/T26`), #93, #106 |
| CI on `main` is red until T29 lands | AUDIT-G23 |
| Gate-plate trap not built; the AI never sets traps | [`TRAPS_SPEC.md`](TRAPS_SPEC.md), #43 |
| The three-mode menu, kneel-takes-uniform and online polish are on `orch/reviewed` (PR #12), not on `main` until Saad merges it | #103 |

## Freeze

Gameplay is frozen after T23-fix1, which may land only if its gates close by Fri 2026-11-27 night; T26, T27 and the scrolling line wait until after Sat 2026-11-28 for the graded `main` (#115). Documentation, CI and the official-repository copy may still change.
