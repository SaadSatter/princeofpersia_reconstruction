# Shadow Masque: scope lock for G2/G3

**Draft, not approved by Saad.** Written 2026-11-26 by the tech-lead worker (task T10b) from Saad's recorded decisions. Every line cites the decision it comes from. Nothing here is a new decision. Saad approves, edits or rejects it; until he does, it is a proposal. Decision files: [`DECISIONS-2026-11-23.md`](orchestration/DECISIONS-2026-11-23.md), [`DECISIONS-2026-11-24.md`](orchestration/DECISIONS-2026-11-24.md) (to #102), `DECISIONS-2026-11-26.md` (#103 and later, on `main`).

Approval line for Saad: `Approved by Saad: ______ (date)`.

**Scope baseline (decision #123):** the current playable build (`main` 271d1ee or later) is the scope baseline. Evidence-driven improvements before Gold remain possible, each with Saad's approval (see "Deferred" below). The refresh rules are Saad's decision #123 in `DECISIONS-2026-11-26.md`; this file only applies them and quotes nothing else in his voice. Refreshed 2026-11-27 by the tech-lead worker (task T30).

## In scope for the graded G2/G3 build

| Item | Decision |
| --- | --- |
| Two rivals in one `GameState`, sword strike and block, 3 hearts, disguise and uniform taking, suspicion, scripted guards | G1 decisions in [`GDD.md`](GDD.md); #4, #15, #17 to #19 |
| Six-room arena of our own layouts (OQ-4) | G1 (2026-11-16); kept for G2/G3 by #118 |
| One duel is 5 minutes = 3,600 frames; a time-up is a draw | #5 |
| Loose-floor traps: one-shot, 4 per rival, owner can be hurt | #2, #22 |
| AI rival is a small PPO policy we trained, plus a scripted baseline on the same interface | #3, #23, #24, #51 |
| Three modes: AI Model (trained), Baseline (scripted), Human vs Human, in pygame, the hosted page and the online server | #87, #88, #92 |
| Online human vs human on a LAN (a LAN server is sufficient for G2/G3; a public multiplayer server is not required, #123). The server owns the only `GameState`; clients send input intents and receive only their own seat's view. Saad's laptop, rooms with a 4-letter code, pause 15 s then forfeit, rematch when both press | #35 to #38, #41, #46, #48, #52, #56, #57 |
| Private one-click AI and Baseline matches online | #95 to #97, #102 |
| Hosted static page (Pyodide 0.27.7, Phaser 3.88.2) for human vs AI. The page is static and runs the engine in the browser, so it is a different thing from the LAN server below, where the server owns the only `GameState` | #12, #13, #25 |
| Controls: WASD or arrows on a player's own machine; flip jumps; 2-tick grace; kneel takes the uniform | #53 to #55, #89, #94, #98, #101 |
| Scenario suite D1, B2, I3, F5 and held-out H6, with the one held-out result reported as it came out | #9, #58 to #66, #74 to #80 |
| Optional host-side playtest telemetry, off by default | #67 to #69 |
| Paid model calls under $1 total, smoke only; the PPO rival needs none | #8 |
| Fix for the "direction keeps running after landing" bug (T23 / T23-fix1): closed at Gate 3 (`orch/reviewed` 41550f9) and merged to `main` in PR #12 (4e20b83) | #93, #105, #118; REVIEW_LOG (T23 Gate 3, 2026-11-26 and 2026-11-27 merge row) |
| Deterministic CI green on `main`: the T29 fix landed with PR #12 (merge 4e20b83) and CI run 46038977033 succeeded on `main` 271d1ee | #104; REVIEW_LOG (T29 Gate 3, PR #12 and #13 merge row) |
| Three-mode menu, kneel-takes-uniform and online polish, on `main` | PR #12 (4e20b83), #103, #119 |
| Hosted page deployed by GitHub Actions (`pages.yml` run 46040177615, success); the custom domain `shadowmasque.com` is still waiting on DNS records at the registrar (Saad) | REVIEW_LOG (Pages row, 2026-11-27) |
| The official-repository copy (T03); needs Saad's approval of this file first | #117, #123 |

## Out of scope for G2/G3

| Item | Decision |
| --- | --- |
| Gate-plate trap (loose floor only) | #2, #22 (gate plate "if there is time"; not built) |
| Accounts, matchmaking, a public-internet game server (LAN online play suffices; this is not excluded forever, #123), levels 2 to 14, original level data, sound, adaptive guards, more than two players | GDD Section 8 (G1); #123 for the public server |
| LLM rival in the game (the Haiku player stays as the legacy midterm rival) | #3 |

## Deferred: may be reconsidered before Gold on external-playtest findings or evaluation evidence, with Saad's approval

Decision #123: these are deferred, not excluded. Each needs Saad's approval before any work. The G2/G3 graded build stays frozen (#118) and none of them enters it.

| Item | Source |
| --- | --- |
| Retraining the PPO rival (needs his approval with runtime and cost known) | #51 (one run); T09 note: weights kept; #111 ("ask me then"); #123 |
| The AI rival rigging traps (`RIG_TRAP` is masked for the AI today) | #43; #123 |
| Movement adjustments: tap or step size, and a side-scrolling view in place of six rooms (study done; line `experiment/scroll`, held until after Sat 2026-11-28) | #106, #107, #108, #112, #118; #123 |
| Other gameplay improvements | #118 (freeze); #123 |

## Possible third production role for G4

A formal course production-agent role for a telemetry analyst or BI agent is not excluded. It is listed as a possible third production role for G4. Today the host-side playtest telemetry is optional and off by default (#67 to #69), and no such role exists. Source: #123, #69.

## Cut order, if time runs out

From GDD Section 8, unchanged: 1. rooms 6 to 3; 2. suspicion meter to a yes/no rule; 3. one trap type (already the case: loose floor only); 4. AI vs AI becomes test-only; 5. public hosting to two computers on one local network (already the case for online play, #36). Never cut the duel or the disguise.

## Known limitations to state at the gate

| Limitation | Evidence |
| --- | --- |
| The trained rival did not beat the baseline at the pre-registered bar: 13 W, 2 D, 1 L of 16 held-out duels, bar 14, "NOT SUPPORTED" (#77). The threshold was not changed after the result (#123) | [`evaluation/RESULTS-T09.md`](evaluation/RESULTS-T09.md) |
| The rival's own inference errors were not recorded in the held-out rows (#84) | [`evaluation/RESULTS-T09.md`](evaluation/RESULTS-T09.md) |
| External playtest: still pending until Saad conducts it; the playtest protocol and consent sentence are unapproved drafts | [`playtest/LOG.md`](playtest/LOG.md), #123 |
| Online play is tested on localhost only; not run on two machines; no latency measurement (OQ-12) | [`ONLINE_PLAY.md`](ONLINE_PLAY.md) |
| The hosted page runs the engine in the browser, so devtools can read hidden state (accepted for human vs AI only; the LAN server does not have this limit). The page deploys through GitHub Actions (run 46040177615); the custom domain `shadowmasque.com` has no public DNS records yet | [`WEB_BUILD.md`](WEB_BUILD.md), GDD "Changes since", REVIEW_LOG (Pages row, 2026-11-27) |
| Left/right taps move a whole block (movement adjustments are deferred, above) | T26 report (`task/T26`), #106, #123 |
| Gate-plate trap not built; the AI never sets traps (deferred, above) | [`TRAPS_SPEC.md`](TRAPS_SPEC.md), #43, #123 |

## Freeze

The G2/G3 graded build is frozen (#118). T23-fix1 landed before the freeze (PR #12). T26, T27 and the scrolling line (T28) wait until after Sat 2026-11-28 and are deferred items above. Documentation, CI and the official-repository copy may still change.
