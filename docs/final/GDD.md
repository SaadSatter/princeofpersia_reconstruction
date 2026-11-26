# Shadow Masque — Game Design Document

**Version:** Initial (G1), 2026-11-15; "Changes since the last gate" added 2026-11-24 and refreshed 2026-11-26 (task T10b)
**Working title:** *Shadow Masque*
**Owner:** Saad Satter, as Design Lead; approved as Creative Director
**Gate approver:** instructor
**Drafted by:** the implementation agent (Claude Code), from Saad's pitch decisions. Saad reviews and owns every decision in this file.

## Changes since the last gate (G1 → G2/G3, as of 2026-11-26)

Dated 2026-11-26 (task T10b). It covers Saad's decisions #31 to #118 and **supersedes the 2026-11-24 entry below wherever they differ**. The 2026-11-24 entry is kept as history; the statements in it that are now false are listed first. Sources: [`orchestration/DECISIONS-2026-11-23.md`](orchestration/DECISIONS-2026-11-23.md) (#1 to #25), [`orchestration/DECISIONS-2026-11-24.md`](orchestration/DECISIONS-2026-11-24.md) (#26 to #102; the file also holds 2026-11-25 and 2026-11-26 entries) and [`orchestration/DECISIONS-2026-11-26.md`](orchestration/DECISIONS-2026-11-26.md) (#103 to #118). Where the work lives: `main` (PR #11, a93d36a) holds the engine, runner, macros, PPO rival and weights, scenario suite, online server, web build and telemetry. The three-mode menu (T22), kneel-takes-uniform (T24) and online polish (T25) are on `orch/reviewed` dfe2d90 (PR #12, open), which is not on `main` until Saad merges it. Task and branch state: [`orchestration/STATUS.md`](orchestration/STATUS.md) and [`TRACKER.md`](TRACKER.md).

**2026-11-24 statements now superseded:**

| 2026-11-24 statement | Now |
|---|---|
| "Online human vs human is **deferred**"; "still needs a server later" | Superseded by #35 to #38. Online human vs human is **in G2/G3 scope** and built (T13, T18, T25). The G2/G3 server runs on Saad's laptop on the same Wi-Fi (#36) |
| "**No trained weights exist**" | Weights exist: `agents/rl/weights/ppo-run-1.json`, SHA-256 `80e4a110...ba4c` (T07-run1, #51) |
| "Scenario suite on `orch/wip-T08` (unreviewed)"; "T07 review pending" | T07, T08 and T09 are closed at Gate 3. The suite is on `main` |
| "G2/G3 is shown locally (two-panel bench for human vs human)" | The build has a pygame menu, a hosted page and an online server, each offering the same three modes (#87) |
| "Nothing in this project has been playtested" | There is still no **external** playtest: the log is empty and the kit is an unapproved draft. Saad has played builds himself (#93 to #98, #101, #102) and those sessions changed rules; they are not a playtest of the concept |
| Loose floor "on `orch/preview`"; "Gate plate not built" | The loose-floor rig is built and closed (T06b). The gate-plate rig is still not built |

| Area | Change | Source | Where it lives |
|---|---|---|---|
| Online play | Human vs human online is back (reverses #1). One authoritative server holds the only `GameState` and sends each client its own seat's view only. Disconnect: the duel pauses 15 s, then the dropped seat forfeits (OQ-13 closed); a silent drop is noticed in about 6 s (ping every 3 s, 3 s timeout); the rematch starts only when both players press the Rematch button, drawn in the game's own style. Rooms: one player creates a room and gets a 4-letter code and the other types it; a code-less default room still works; 10 failed joins per connection per minute, at most 50 rooms, a room expires 10 min after creation with no second player or 15 s after both seats are gone (kept as built, #62). One room's error never stops the other rooms (#63). Online AI-seat fallbacks are logged and never abort a duel (#49); the live AI answer budget is 0.04 s (#45) | #35 to #38, #41, #45, #46, #48, #49, #52, #56, #57, #62, #63 | `main` (T13, T18); [`ONLINE_PLAY.md`](ONLINE_PLAY.md). Not yet verified on two real machines |
| Online AI and Baseline | Choosing AI Model or Baseline online starts a private match at once: no Create or Join step, no room code. The loading screen is centred, and also covers the game while reconnecting. Handshake noise from unused browser connections is logged quietly | #95, #96, #97, #102 | `orch/reviewed` (T25) |
| Hosting | The server is Saad's laptop on a LAN (OQ-10 closed for G2/G3), reached at `http://<laptop-ip>:<port>`. A static hosted page (Pyodide 0.27.7, Phaser 3.88.2) also exists for human vs AI. Because the engine runs in that page, devtools can read hidden state there. That is accepted for human vs AI and is **not** accepted for online human vs human, which uses the server. The GitHub Pages deploy returned 404 on 2026-11-26 and no live page URL is recorded | #12, #13, #25, #36 | `main` (T14, T13); [`WEB_BUILD.md`](WEB_BUILD.md) |
| Modes | Three modes in pygame, the hosted page and the online server, from one list: **AI Model (trained)**, **Baseline (scripted)** and **Human vs Human**. Honest names on the menu, HUD and end screen. A bare `python play.py` opens the menu; the old single-prince level stays behind a flag | #87, #88, #89, #91, #92 | `orch/reviewed` (T22); [`GAME_MODES.md`](GAME_MODES.md) |
| AI rival, trained | The PPO policy was trained once: 4,800 s cap, 2 workers, seed 0, 1,568 updates, 1,487,955 steps, 0 policy errors. Training stops on the first policy error and withholds failed weights (#47, #50). The shipped file is loaded only after a SHA-256 check. The AI rival never rigs traps (`RIG_TRAP` is masked for it) | #3, #42, #43, #44, #47, #50, #51 | `main` (T07, T07-run1, T16, T17); [`RL_POLICY.md`](RL_POLICY.md) |
| AI rival, evaluated | Scenario suite D1, B2, I3, F5 (tuning, with mirrored seat-B starts) and H6 (held-out, 8 starts, 16 duels, frozen by SHA-256 before any run). B2 succeeds only if the rival is still disguised and the guard's suspicion stayed below 50 of 100 (#58, #76). D1 succeeds only if the other rival is never in the agent's room (#59). Pre-registered bar: at least 14 of 16 wins and no aborted duel (#77). **The one held-out run: 13 W, 2 D, 1 L, bar not met, "NOT SUPPORTED".** That means the improvement over the scripted baseline was not shown at the bar, not that the rival is worse. The rival's own inference errors were not recorded in those rows (#84). The weights are kept without retraining | #58 to #66, #74 to #80, #84 | `main` (T08, T09); [`evaluation/RESULTS-T09.md`](evaluation/RESULTS-T09.md) |
| Macros | `CLIMB` goes up and also down safely (hang and drop, or a survivable drop); no new macro name. A jump away from the facing turns at once; runs and steps still turn first. The macro cadence (a new macro at most every 4 decisions) is still waiting on Saad | #31, #71; STATUS "Waiting on Saad" | `main` (T05-fix1) |
| Controls and jumps | Every directional jump is a flip in that direction (look and effect only; distances unchanged). A direction and a jump pressed within 2 ticks (about 170 ms) become one directional jump. Online and against an AI, a player's own seat accepts both WASD and the arrow keys; local two-player on one keyboard keeps A = WASD, B = arrows. This settles OQ-7 in effect. The crouch strip is drawn for kneeling actions; no dedicated kneel sprite is planned | #53, #54, #55, #73, #89 | `main` (T19) |
| Disguise and guards | Kneeling (`DOWN`) over a downed uniformed guard takes the uniform (amends R-V17), except at a ledge edge where `DOWN` still starts a hang and `TAKE` takes the uniform (#101). After a sword pickup, sheathe (G or `/`) or press T before taking the uniform | #94, #98, #101 | `orch/reviewed` (T24) |
| Known bug | A direction held in the air and then released can still move a rival a little after landing (reported by Saad). T23-fix1 is in progress. Under the freeze below it may land only if its gates close by Fri 2026-11-27 night | #93, #105, #118 | `task/T23`, not on `main` |
| Playtest telemetry | An optional host-side event log (`python -m server --playtest`, and the local `--versus` flag), off by default. Only room code, seat and ticks identify a player. A native `telemetry-analyst` worker counts the logs and reports facts, and Saad interprets them. It is not a formal course production agent; it would count only if Saad later writes an origin note | #67, #68, #69, #81 to #83, #85, #86 | `main` (T20, T21); [`playtest/TELEMETRY.md`](playtest/TELEMETRY.md) |
| Dependencies | Optional extras: `train` (numpy) and `online` (websockets). The base install needs neither, and numpy is not in `dev`. CI on `main` was red on 2026-11-26 because `ci.yml` did not install the `online` extra; T29 is the fix (closed at Gate 3, 2f3e493 on `orch/reviewed`; it reaches `main` with PR #12) | #34, #37, #40, #117 | `pyproject.toml`, `.github/workflows/ci.yml` |
| Side-scroller question | Saad asked whether one left/right tap moves a rival too far, and whether the six rooms could become a side-scroller. Two studies (T26 tap size, T27 feasibility) were run. For T27, option (b), a scrolling window on its own line, was chosen (#108); for T26, only the tap-size option is still open (#112: land T23-fix1 first). No rule changes until then. A scrolling window will be explored on its own line (`experiment/scroll`), isolated from the graded build. **The six-room arena (OQ-4) stays in force for G2/G3.** The scrolling line's own choices (decisions #109 to #112 of the other orchestrator session): scroll both axes over the 3 x 2 loop, a view of 10 columns x 3 rows centred on the seat's rival, no PPO retraining without Saad's approval, and T23-fix1 lands first; it is task T28, queued until after G2/G3 | #106, #107, #108, #109 to #112, #118 | Reports `T26-tech-lead.md` and `T27-tech-lead.md` on `task/T26` and `task/T27` |
| Freeze | G2/G3 gameplay is frozen after T23-fix1. T26, T27 and the scrolling line wait until after Sat 2026-11-28 | #118 | [`SCOPE_LOCK.md`](SCOPE_LOCK.md) (draft, not approved) |
| Process | Pushes, issues and PRs need no per-push approval; orchestration records go to `main`; other changes reach `main` only through a PR Saad merges (#27 to #29). The official repository is filled by copying files and keeping its template (#104). The routed handoff with a Student decision is the T18 chain, and Saad writes the decision (#116). PR #6 is not merged as it was; this task refreshes it (#117, amends #103) | #26 to #30, #103, #104, #116, #117 | `main`; [`TRACKER.md`](TRACKER.md) |

**Unchanged and still in force:** the duel limit of 5 minutes = 3,600 frames (#5); hop while disguised +48 suspicion (#18); R-V25 masking (#17); `TAKE` always legal (#15); lingering over 2 s (#19); traps one-shot, 4 per rival, the owner can be hurt, loose floor first (#2, #22); macro vocabulary and runner policy (#23, #24); paid model calls under $1 total, smoke only (#8); web pins (#25).

**Waiting on Saad:** the macro cadence (4 decisions), nearest-figure targeting and reward defaults; whether a sprung trap costs 1 heart in all cases; the 4 to 8 suspicion surcharge on discarded run frames (T19); which T26 tap-size option to take; the telemetry consent wording; approval of the playtest protocol; his Student decision.

**Not evidence yet:** no external player has played, so no claim about balance or fun rests on evidence. The playtest log is empty by design ([`playtest/LOG.md`](playtest/LOG.md)).

### Changes since the last gate (as of 2026-11-24, kept as history; superseded in part by the entry above)

Dated record of what changed after the G1 text below was written. The G1 text is kept; where a statement is superseded it carries an inline marker. Sources: Saad's decisions in [`orchestration/DECISIONS-2026-11-23.md`](orchestration/DECISIONS-2026-11-23.md) (#1 to #25) and [`orchestration/DECISIONS-2026-11-24.md`](orchestration/DECISIONS-2026-11-24.md) (#26 to #30). Branch names say where the work lives: `main` holds the merged G1 engine (PRs #1 to #4); anything marked `orch/preview`, `orch/reviewed` or WIP is **not on `main`**. Branch state: [`orchestration/STATUS.md`](orchestration/STATUS.md).

| Area | Change | Source | Where it lives |
|---|---|---|---|
| Play context | Online human vs human is **deferred**; G2/G3 is shown locally (two-panel bench for human vs human, one panel for human vs AI) | #1 | Planned |
| Platform | A **hosted static build**: the Python engine runs in the browser through Pyodide and a Phaser client draws only the human seat; live by G2/G3 (Sat 28 Nov). Online human vs human (two machines) still needs a server later. This supersedes #1 for hosting only. **Because the engine runs in the browser, the whole game state lives there and a human can read hidden state through the browser devtools.** That is acceptable for human vs AI and local play, but not for online human vs human, which needs the server (`PLAN-2026-11-23-v3-delta.md`, "Known limitation") | #12, #13 | `orch/preview` (T14, T14-fix1; fix1 review pending). No live page URL is recorded yet |
| Web pins | Pyodide 0.27.7 and Phaser 3.88.2 from a CDN; deploy job gets `pages: write` and `id-token: write`; rematch keeps the seed; the end screen states how the duel ended | #25 | `orch/preview` |
| AI rival | The AI seat is a **small PPO policy we train**, acting on macro-actions from its own seat's observation, compared against a scripted pathfinding baseline. The LLM (Claude Haiku 4.5) is no longer the rival; an LLM may be used only on a slow timescale, out of G2/G3 scope | #3 | encoder, policy and trainer on `orch/preview` (T07, review pending). **No trained weights exist** |
| AI cadence | The G1 "one macro about every 4 s" is replaced: the runner asks at 6-frame decisions (0.5 s) and the policy picks a new macro at most every 4 decisions (2 s). The 4-decision value is still waiting on Saad | #24; `STATUS.md` "Waiting on Saad" | `orch/preview` |
| Macro vocabulary | BLEND, DISGUISE, WAIT, FOLLOW, STRIKE, FLEE, CLIMB, SEARCH, plus RIG_TRAP once traps exist. CQ-1 closed. Whether CLIMB also goes down is still waiting on Saad | #23 | `orch/preview` (T05); CLIMB-down is WIP (`orch/wip-T05-fix1`) |
| Runner policy | One controller object in both seats is refused; evaluation runs pass a secret `seed_key`; a run over its fallback limit is "aborted", reported and never dropped; cadence 6 frames, timeout 5 s | #24 | `orch/preview`; the shared-controller refusal is WIP (`orch/wip-T04-fix3`) |
| Duel limit | Arena duel limit is **5 minutes = 3,600 frames** at 12 fps. OQ-3 closed. A time-up is a draw | #5 | `orch/reviewed` |
| Disguise rules | A hop (`UP`) while disguised raises suspicion by +6 on each of the 8 hop frames (+48 per hop; three hops in a guard's sight break the disguise) (R-V24) | #4, #18 | `orch/reviewed` |
| Disguise rules | A disguised rival's moves that no guard makes are observed as a guard standing still (R-V25) | #17 | `orch/reviewed` |
| Disguise rules | `TAKE` is legal over any downed guard; with no uniform left it fails with no state change (R-V26), so an AI seat learns only what a human learns | #15 | `orch/reviewed` |
| Disguise rules | Lingering within 1 cell of a guard for over 2 s raises suspicion even while the rival re-sends `WAIT` | #19 | `orch/reviewed` (T01-fix1) |
| Traps | Rival-rigged traps are a G2 target. Spec: one-shot (no re-arm, closes OQ-6); rig the cell ahead; 12-frame kneel; 4 per rival, shared across types; disguised rigging allowed with +3 suspicion per frame in a guard's sight; the owner can be hurt; a double rig is allowed; loose floor first, gate plate only if there is time; gate slam costs 1 heart; a cancelled rig spends the trap; one `RIG_TRAP` macro | #2, #22 | Loose floor on `orch/preview` (T06b, review pending), with `docs/final/TRAPS_SPEC.md` on that branch. Gate plate not built. "A sprung trap costs 1 heart in all" is still waiting on Saad |
| Evaluation scenarios | D1, B2, I3, F5 (tuning) and H6 (held-out), with Saad's success definitions, frozen before any comparative run. B2's "low suspicion" number and D1's "on screen" are still waiting on Saad | #9 | Scenario suite on `orch/wip-T08` (unreviewed) |
| Spending | Paid model calls are capped under $1 total, smoke test only; the G1 $5 pre-G2 cap is replaced. The PPO rival needs no paid call | #8 | No paid run has been made |
| Production | Work runs through a native orchestrator and named Sonnet workers with file-based handoffs ([`orchestration/README.md`](orchestration/README.md)). Merging stays Saad's | #16, #27 to #29 | `main` |
| Process | The tracker lives in this repository for now; the official-repository move (midterm method) is due Sat 28 Nov, 11:59 p.m. | #6, #10 | Move not started |

Not changed: the pillars, the three hearts, the six-room arena, the art direction, the Nidhogg-style swordplay and the 2026-11-17 disguise and guard rules ([`VERSUS_SPEC.md`](VERSUS_SPEC.md)). **Nothing in this project has been playtested.** No claim about balance or fun rests on evidence yet.

---

Every statement below carries one of three labels, as reader Section 5.2 asks:

- **[Implemented]**: exists in this repository and is covered by tests. From 2026-11-26 the label also covers final-project work; a note says whether it is on `main` or only on `orch/reviewed` (PR #12).
- **[Planned]**: designed for the final project, not yet built.
- **[Open]**: undecided. Each one has an ID (`OQ-n`) and is listed in [Open questions](#open-questions).

Nothing here is **[Verified]** by a player yet. No external playtest of this concept has been run.

### Decisions confirmed by Saad (2026-11-15)

The agent drafted these decisions. Saad confirmed them on 2026-11-15:

| Decision | Confirmed value | Still open |
|---|---|---|
| Working title | *Shadow Masque* | — |
| Trap types | Loose floor and gate plate (Section 5.2) *[Refined 2026-11-23, decisions #2, #22: loose floor first, gate plate if there is time]* | — |
| Trap limit | Each rival can set 4 traps | OQ-6: re-arm time *[Closed 2026-11-23, decision #22: one-shot]* |
| Health rule | Each rival has 3 hearts. Each stab, trap or damaging fall costs 1 heart. 0 hearts is death | — |
| AI decision cadence | One macro-action about every 4 s per AI seat *[Superseded 2026-11-23, decisions #3 and #24: see Changes. The AI is a PPO policy deciding at 6-frame runner decisions]* | OQ-9 / CQ-3: whether it plays well, checked at the first playtest |
| Play context (2026-11-16) | **Online**, each rival on their own screen. Replaces local split screen, because on a shared screen each player can see the other's half *[Superseded 2026-11-23, decisions #1, #12: online human vs human is deferred; G2/G3 is local plus a hosted Pyodide + Phaser build. See Changes]* | OQ-10 hosting, OQ-11 browser client, OQ-12 latency |
| Art (2026-11-16, OQ-8) | Our own **medieval stone dungeon** art, made with PixelLab plus hand-drawn frames; 32 px rivals and guards; pillars in the background; frameless iron portcullis gates. Committed in `assets/generated/` ([`ART_PROVENANCE.md`](ART_PROVENANCE.md)). Saad's reading of PixelLab's terms (30 Oct 2026): outputs may be published in the public repository | Second rival is the first recoloured crimson (same frames, same size) |
| Swordplay (2026-11-17) | *Nidhogg*-style: high/mid/low stances, block by matching height, disarm; lunge, sword throw, dive kick and sweep all in the first playable. **3 hearts kept**: a clean hit costs 1 heart. Rules and proposed numbers: [`VERSUS_SPEC.md`](VERSUS_SPEC.md) | Numbers approved 2026-11-17 |
| Two-seat timing (2026-11-17, CQ-1) | Real-time ticks: one shared game advanced 12 frames per second; both rivals' moves overlap | Observation fields and key map approved 2026-11-17 ([`VERSUS_SPEC.md`](VERSUS_SPEC.md)) |
| Disguise and guards (2026-11-17, OQ-2, OQ-5) | One clean hit or a trap downs a guard for good; DOWN beside it takes the uniform; running, jumping, climbing, a drawn sword or striking near a guard raise its suspicion, walking lowers it; full suspicion breaks the disguise; each meter is shown only to the suspected rival. The suspicion meter stays in scope | Rates approved 2026-11-17 ([`VERSUS_SPEC.md`](VERSUS_SPEC.md)) |
| Arena size (2026-11-16, OQ-4) | **Six rooms** in a 3 x 2 loop, our own layouts ([`pop/arena.py`](../../pop/arena.py)); see Section 5.2 | Guard routes and two-seat starts wait for the two-seat engine (CQ-1) |

---

## 1. The X

> Two rivals sneak through a guarded palace, hide in stolen guard uniforms, rig traps for each other, and race to strike the other down first.

- **Action:** sneak, disguise, trap, duel.
- **Experience:** paranoia ("which guard is my rival?"), then the thrill of the reveal.

## 2. Player, platform and genre

| Item | Decision | Label |
|---|---|---|
| Players | Two rivals. Each seat is a human or an AI agent *[the AI is a PPO policy since decision #3]*. | Implemented (T07, T22, T13) |
| Context | Two players online, each on their own computer and screen *[Deferred 2026-11-23 (#1), restored 2026-11-24 (#35 to #38): online human vs human on a LAN, plus local play and the hosted page. See Changes]* | Implemented (T13, T18, T25); not yet run on two real machines |
| Platform | An authoritative Python game server (`server/`) runs the `pop/` engine; each player opens a browser page (Phaser) and the server sends that seat's view only (#35 to #38). A hosted static page (Pyodide + Phaser, engine in the browser) serves human vs AI (#12, #13). The desktop Pygame frontend stays for development, replays and the three-mode menu | Implemented (Pygame, server, browser client, hosted page; modes menu on `orch/reviewed`) |
| Genre | 2D cinematic platformer with versus stealth and duelling | Implemented (greybox) |
| Session | One duel, 5 minutes = 3,600 frames (OQ-3 closed, decision #5) *[G1 text: "about 5 minutes (OQ-3)"; superseded by decision #5]* | Implemented (`pop/versus_runner.py`) |

### Player motivation (Motivation Atlas groups)

The source is the course's Motivation Atlas, section "The eleven motivators" (`columbia-university-ai-games/motivation-atlas`, `content/player-motivations.md`). Each group is a hypothesis paired with behaviour a playtest could observe.

| Atlas group | Why it fits, from the atlas | Observable behaviour if it works |
|---|---|---|
| **Competition over other people** (primary) | Player-killing and duels (Bartle's *Killer*); rivalry among friends; schadenfreude (Schell 2019, pp. 136, 157) | Gloating after a kill or a sprung trap; a rematch asked for within 30 s |
| **Challenge and mastery** | Opponent play (Hunicke et al. 2004, p. 3); uncertain goals through hidden information (Malone 1980, pp. 66–67); inventing new strategies (Lazzaro 2004b) | After a loss, the player tries a different approach instead of repeating the last one |
| **Sensation, thrill, and destruction** | "Fear minus death equals fun" (Schell 2019, p. 137); threats on an unpredictable schedule | A spoken reaction at a reveal, at least one "that was *you*?!" per round |

## 3. Pillars

1. **Rival versus rival.** A two-player duel: every system points at the other player. A strike on the wrong guard exposes you.
2. **Hide in plain sight.** The disguise is the core verb.
3. **Turn the palace against them.** Rig floors and gates. Traps and guards follow the same fixed rules for both rivals.

Use the pillars to decide between design options: a feature that serves none of them goes to the backlog.

## 4. Core loop (MDA view)

| Step | What happens | Mechanics involved |
|---|---|---|
| **Act** | Move, climb, take a fallen guard's uniform, rig a trap, draw your sword | Movement [Implemented]; take a uniform / disguise [Implemented on `main` (`pop/versus.py`, R-V17 to R-V21, the T01 fixes R-V24 to R-V26); kneeling over a downed guard (#94) is on `orch/reviewed`]; sword [Implemented on `main` (R-V01 to R-V12)]; rig a trap [Implemented on `main`: loose floor, human seats only; gate plate not built] |
| **Respond** | Scripted guards attack anyone undisguised, running or armed. A rigged floor drops whoever steps on it. The rival moves. | Guard rule [Implemented on `main` (`pop/guards.py`); the lingering rule R-V19 and its constant `LINGER_AFTER` are in `pop/versus.py`, with the WAIT-lingering fix], traps [Implemented: loose floor; gate plate not built], loose floors and gates [Implemented as level hazards] |
| **Interpret** | Read the suspicion icon. Which guard broke its patrol? Is that tile rigged? | HUD [Implemented on `main`: hearts in `render/draw.py`, suspicion eye/bar and DISGUISED marker in `play.py`, and the browser HUD] |
| **Next action** | Shadow a suspect, strike to unmask, lure them onto your trap, or slip away | — |

- **Dynamics we expect** (hypotheses): bluffing between rivals; mimicry of the guard patrol; baiting the rival onto a trap; risky unmasking strikes.
- **Aesthetics:** Competition, Challenge, Sensation (Section 2).

## 5. World and mechanics

### 5.1 Inherited from the midterm [Implemented]

The headless, deterministic engine in `pop/` is the base: fixed-step kinematics, gravity, collision, landing damage, gates, pressure plates, loose floors, spikes and potions. Its rules and their evidence are in [`docs/RULE_SOURCE_MAP.md`](../RULE_SOURCE_MAP.md); tests are in `tests/`. Human and agent play call the same `engine.step`.

### 5.2 New for the final project

*Status by row (checked 2026-11-26): **[Implemented on `main`]** arena, second player, sword, disguise, guards, suspicion, loose-floor traps, the online server with disconnect handling, and the seat controllers (`pop/versus.py`, `pop/guards.py`, `pop/arena.py`, `server/`). **[Implemented on `orch/reviewed` only, PR #12]** the three-mode menu and the one-click private AI match. **[Planned]** the gate-plate trap. Nothing is verified by a player.*

| Mechanic | Rule (initial) | Open questions |
|---|---|---|
| **Arena** | Six rooms of our own layouts (no original level data), `pop/arena.py`: West Cells, Gatehouse, East Tower above Barracks, Undercroft, Pit Hall, linked in a loop with a shaft from the Gatehouse to the Undercroft. Rivals start in the West Cells and East Tower (mirror images). Each middle room has an open gate between two drop plates (the gate-plate trap spots); Barracks and Pit Hall each hold a guard post. Every row of every room is reachable from both starts in the real engine (`tools/check_arena.py`) | Decided 2026-11-16 (OQ-4) |
| **Second player** | Two prince-type characters in one `GameState`, stepped in the same frame | — |
| **Sword** | `STRIKE` and `BLOCK`, close range. Each rival has 3 hearts. Each stab, trap or damaging fall costs 1 heart; 0 hearts is death. | — |
| **Disguise** | Interact (DOWN) with a downed guard to take the uniform. While disguised, guards ignore you until their suspicion of you is full. Running, jumping or climbing near a guard raises its suspicion; walking lowers it. Drawing the sword, striking or full suspicion breaks the disguise (decided 2026-11-17) | Rates and the full break list: [`VERSUS_SPEC.md`](VERSUS_SPEC.md) R-V17–R-V21 (approved 2026-11-17) |
| **Guards** | Scripted, not AI. Fixed patrol routes. Attack any undisguised rival in view, or a disguised one who breaks the disguise rules. Hostile to both rivals equally. | OQ-5 how guards are downed |
| **Suspicion** | Per-rival meter shown on that rival's HUD; rises when acting oddly near a guard | Cut candidate (yes/no rule) |
| **Traps** *[Refined 2026-11-23, decision #22: see Changes]* | Two types planned; **only the loose floor is built**. **Loose floor** (rig a floor tile so it drops whoever steps on it next); **gate plate** (rig a plate to slam a gate) is not built. Traps hurt everyone, including the rival who set them; a sprung trap costs 1 heart. Each rival can set 4 traps. A rigged tile looks normal to everyone else. | OQ-6 closed by decision #22 (one-shot) |
| **Online play** *[Deferred 2026-11-23 (#1); restored 2026-11-24 (#35 to #38), built in T13, T18, T25]* | One server holds the only `GameState` and steps it. Each browser sends its player's inputs and receives only its own seat's observation. An AI seat runs on the server and gets the same per-seat observation. | OQ-10 (closed for G2/G3, #36), OQ-11 (closed, #12), OQ-12 (open) |
| **Disconnect** | The duel pauses for both players for 15 s; a reconnect resumes it, otherwise the disconnected seat loses (#38, #48) | OQ-13 closed |
| **Modes** | AI Model (trained PPO), Baseline (scripted) and Human vs Human, offered by pygame, the hosted page and the online server (#87 to #92); AI vs AI stays a test and watch tool | — |

### 5.3 Win, loss and edge cases

*Status by row (checked 2026-11-26): **[Implemented on `main`]** hearts reaching 0, same-frame death draw, time-out draw at 3,600 frames, trap death, the AI-seat timeout and labelled fallback (versus runner), and disconnect forfeit (online server).*

| Situation | Outcome |
|---|---|
| A rival's health reaches 0 from a strike, guard, trap or fall | The other rival wins |
| Both rivals die in the same frame | Draw |
| Time limit reached (5 minutes, OQ-3 closed by decision #5) | Draw |
| A rival dies on their own trap | The other rival wins |
| An invalid action | Refused, counted, changes no state (as in the midterm runner) |
| An AI seat times out | Labelled `WAIT` fallback, counted per seat; a run over its fallback limit is "aborted" (decision #24; [Configuration Document](CONFIGURATION.md) A5) |
| A human rival disconnects | The duel pauses for 15 s. If the rival does not return, the other rival wins and the end screen says why (OQ-13 closed, #38). A silent drop is noticed in about 6 s (#48) |

No score beyond win, draw or loss is planned.

## 6. Controls and feedback [Implemented]

*[Status 2026-11-26: the online server and one-browser-per-rival design in the text below is built (T13). The hosted static page (Pyodide) is separate: it has no server, so devtools can read hidden state there, which is accepted for human vs AI only (#12). Key map: see the first bullet.]*

- **Controls:** each player uses their own keyboard. Online and against an AI, either WASD (with F, G, T and left Shift) or the arrow keys (with `.`, `/`, `'` and right Shift) drives the player's own seat (#55, #89). Local two-player on one keyboard keeps A = WASD, B = arrows. Inputs map to the same actions an AI seat sends, as in the midterm; the server validates them. A direction and a jump pressed within 2 ticks become one directional jump (#54).
- **Own screen:** each browser shows only its own rival's current room and HUD. There is no shared screen to look at, so a disguise cannot be seen through by watching the other player's view.
- **HUD:** three hearts, the suspicion icon, a disguised/undisguised marker.
- **Reveal:** a short flash and sound-free animation when a disguise breaks. No sound: excluded, as in the midterm.

## 7. Information boundaries

*[Status 2026-11-26: the text below is built for **online play** (T13): the server holds the only `GameState`. The hosted static page is different (decisions #1, #12): its engine runs in the browser through Pyodide, so the browser holds the `GameState` and devtools can read hidden state. That is accepted for human vs AI and not for human vs human, which uses the server (`PLAN-2026-11-23-v3-delta.md`, "Known limitation").]*

- **World state (engine only):** both rivals' true positions and uniforms, every guard's patrol and suspicion, which tiles are rigged and by whom, all rooms, and the RNG seed.
- **What the server sends a client:** that seat's observation only. The browser never holds the `GameState`, the other seat's observation or the arena layout, so reading the page's network traffic reveals nothing a player could not see on screen.
- **What a player or AI seat sees:** its own room only; figures in view, with a disguised rival drawn as a guard; a rigged tile drawn as normal unless you rigged it; its own health and suspicion; its legal actions.

The midterm's hidden-information tests (`observe` and `legal_actions` reveal nothing outside the current room) carry over. New tests must check that disguise identity and trap ownership never leak.

## 8. Content scope

| Included by G2/G3 | Excluded | Cut first, in order |
|---|---|---|
| One arena of 4–6 rooms · sword strike and block · disguises · 2 trap types · scripted guards · online play (one server, one browser per rival; the server may hold several duels in separate rooms, #52) *[Deferred 2026-11-23 (#1) and restored 2026-11-24 (#35 to #38); G2/G3 server is Saad's laptop on a LAN, #36]* · hosted static page for human vs AI · 3 modes (AI Model, Baseline, Human vs Human) · traces and tests | Accounts, matchmaking, a game server on the public internet (#36) · Levels 2–14 · original level data · sound · AI or adaptive guards · more than two players | 1. Rooms 6 → 3 · 2. Suspicion meter → yes/no rule · 3. One trap type · 4. AI vs AI becomes test-only · 5. Public hosting → two computers on one local network, same server. Never cut: the duel or the disguise. |

## 9. Balance (initial, untested)

- Strikes and traps must both be able to win a duel; neither should dominate. We will measure it by counting how each duel ends in playtests and AI-vs-AI runs.
- The disguise should survive careful play but not a sword draw.

All numbers are **[Open]** until the greybox duel (see [Project Plan](PROJECT_PLAN.md)).

## 10. References and attribution

| Source | Specific moment or mechanic | Borrowed / changed | Terms |
|---|---|---|---|
| *Prince of Persia* (1989), Jordan Mechner | Level 1 movement, loose floors, gates and plates; guard sword duels | Rules re-written in our own Python (`pop/`); versus play, disguises and player-set traps are new | `historicalsource/princeofpersia` at `2b4ddb5`: README permits study and modification, grants no rights in Prince of Persia (Ubisoft franchise) |
| Original DOS sprites (207 images) | Prince and tile art | Drawn as-is only on the private course branch; not used by the online build | Basis recorded in [`docs/ASSET_PROVENANCE.md`](../ASSET_PROVENANCE.md); not licensed by the README or SDLPoP's GPL |
| PixelLab (pixellab.ai) | Rival, guard and dungeon art generated from our own text prompts; gate, spikes, hang and climb frames hand-drawn by the agent | Our own designs in the genre's style; no original sprite was uploaded or traced and "Prince of Persia" was never in a prompt | PixelLab terms of 30 Oct 2026; [`ART_PROVENANCE.md`](ART_PROVENANCE.md) |
| *SpyParty* (Chris Hecker) | The spy must act like the party's scripted guests | Idea only; here both rivals hide among scripted guards | No assets or code |
| *Hitman* (IO Interactive) | Taking a downed enemy's uniform | Idea only; guards judge behaviour, not faces | No assets or code |
| Our midterm (this repository) | Engine, runner, baseline, model player, tests | Reused and extended | Our own work |

Guard and disguise art: one PixelLab guard; a disguised rival is drawn with the guard's own sprite, so the picture never reveals who wears the uniform (OQ-8, decided 2026-11-16).

## Open questions

| ID | Question | Who decides | Needed by |
|---|---|---|---|
| OQ-1 | **Decided 2026-11-15:** 3 hearts; 1 heart per stab, trap or damaging fall | Saad (Design Lead) | Greybox duel |
| OQ-2 | **Decided 2026-11-17:** drawing the sword, striking, or full suspicion break the disguise; running, jumping and climbing near a guard raise suspicion. Also a stance change or losing a heart (approved 2026-11-17, [`VERSUS_SPEC.md`](VERSUS_SPEC.md) R-V21) | Saad | Greybox duel |
| OQ-3 | **Decided 2026-11-23 (#5):** 5 minutes = 3,600 frames. (G1 text: Duel time limit, 5 min assumed) | Saad | First playtest |
| OQ-4 | **Decided 2026-11-16:** six rooms (`pop/arena.py`) | Saad | Before G2 |
| OQ-5 | **Decided 2026-11-17:** one clean hit or a trap; the guard stays down (R-V16) | Saad | Combat work |
| OQ-6 | **Decided 2026-11-23 (#22):** one-shot, no re-arm. (G1 text: trap re-arm time; limit of 4 per rival decided) | Saad | Trap work |
| OQ-7 | **Decided 2026-11-24/25 (#55, #89):** WASD or arrows on a player's own machine; local two-player A = WASD, B = arrows | Saad | Browser client work |
| OQ-8 | **Decided 2026-11-16:** our own PixelLab-generated medieval dungeon art (`assets/generated/`, [`ART_PROVENANCE.md`](ART_PROVENANCE.md)) | Saad (IP) | Before the server is reachable by anyone outside the course |
| OQ-9 | Whether the AI rival's cadence is playable in a sword fight. *The 4 s figure is superseded (#3, #24); open: no external player has played against it. T09 did not show the improvement over the baseline at the pre-registered bar* | Playtest evidence | G2 |
| OQ-10 | **Decided for G2/G3 (#36):** the server is Saad's laptop on the same Wi-Fi. *The static page is decided (#12, GitHub Pages), but the Pages deploy failed with 404 on 2026-11-26 and no URL is recorded* | Saad (Producer) | First playable recording |
| OQ-11 | **Decided 2026-11-23 (#12, #25):** Pyodide 0.27.7 + Phaser 3.88.2. (G1 proposal: a plain JavaScript canvas page) | Saad, on the agent's proposal | Sun 22 Nov |
| OQ-12 | How much network delay a sword fight tolerates. *Open; no two-machine playtest has been run* | Playtest evidence | G2 |
| OQ-13 | **Decided 2026-11-24 (#38):** pause 15 s, then forfeit; silent drops noticed in about 6 s (#48) | Saad | Server work |
