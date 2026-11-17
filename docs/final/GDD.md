# Shadow Masque — Game Design Document

**Version:** Initial (G1), 2026-11-15
**Working title:** *Shadow Masque*
**Owner:** Saad Satter, as Design Lead; approved as Creative Director
**Gate approver:** instructor
**Drafted by:** the implementation agent (Claude Code), from Saad's pitch decisions. Saad reviews and owns every decision in this file.

Every statement below carries one of three labels, as reader Section 5.2 asks:

- **[Implemented]**: exists in this repository from the midterm, covered by tests.
- **[Planned]**: designed for the final project, not yet built.
- **[Open]**: undecided. Each one has an ID (`OQ-n`) and is listed in [Open questions](#open-questions).

Nothing here is **[Verified]** by a player yet. No playtest of this concept has been run.

### Decisions confirmed by Saad (2026-11-15)

The agent drafted these decisions. Saad confirmed them on 2026-11-15:

| Decision | Confirmed value | Still open |
|---|---|---|
| Working title | *Shadow Masque* | — |
| Trap types | Loose floor and gate plate (Section 5.2) | — |
| Trap limit | Each rival can set 4 traps | OQ-6: re-arm time |
| Health rule | Each rival has 3 hearts. Each stab, trap or damaging fall costs 1 heart. 0 hearts is death | — |
| AI decision cadence | One macro-action about every 4 s per AI seat | OQ-9 / CQ-3: whether it plays well, checked at the first playtest |
| Play context (2026-11-16) | **Online**, each rival on their own screen. Replaces local split screen, because on a shared screen each player can see the other's half | OQ-10 hosting, OQ-11 browser client, OQ-12 latency |
| Art (2026-11-16, OQ-8) | Our own **medieval stone dungeon** art, made with PixelLab plus hand-drawn frames; 32 px rivals and guards; pillars in the background; frameless iron portcullis gates. Committed in `assets/generated/` ([`ART_PROVENANCE.md`](ART_PROVENANCE.md)). Saad's reading of PixelLab's terms (30 Oct 2026): outputs may be published in the public repository | Second rival is the first recoloured crimson (same frames, same size) |
| Arena size (2026-11-16, OQ-4) | **Six rooms** in a 3 x 2 loop, our own layouts ([`pop/arena.py`](../../pop/arena.py)); see Section 5.2 | Guard routes and two-seat starts wait for the two-seat engine (CQ-1) |

---

## 1. The X

> Two rivals sneak through a guarded palace, hide in stolen guard uniforms, rig traps for each other, and race to strike the other down first.

- **Action:** sneak, disguise, trap, duel.
- **Experience:** paranoia ("which guard is my rival?"), then the thrill of the reveal.

## 2. Player, platform and genre

| Item | Decision | Label |
|---|---|---|
| Players | Two rivals. Each seat is a human or an AI agent. | Planned |
| Context | Two players online, each on their own computer and screen | Planned |
| Platform | An authoritative Python game server runs the `pop/` engine; each player opens a browser page (OQ-11). The desktop Pygame frontend stays for development, replays and watching AI vs AI | Implemented (single-player Pygame); Planned (server, browser client) |
| Genre | 2D cinematic platformer with versus stealth and duelling | Planned |
| Session | One duel, about 5 minutes (OQ-3) | Planned |

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
| **Act** | Move, climb, take a fallen guard's uniform, rig a trap, draw your sword | Movement [Implemented]; disguise, trap, sword [Planned] |
| **Respond** | Scripted guards attack anyone undisguised, running or armed. A rigged floor drops whoever steps on it. The rival moves. | Guard rule, traps [Planned]; loose floors and gates [Implemented as level hazards] |
| **Interpret** | Read the suspicion icon. Which guard broke its patrol? Is that tile rigged? | HUD [Planned] |
| **Next action** | Shadow a suspect, strike to unmask, lure them onto your trap, or slip away | — |

- **Dynamics we expect** (hypotheses): bluffing between rivals; mimicry of the guard patrol; baiting the rival onto a trap; risky unmasking strikes.
- **Aesthetics:** Competition, Challenge, Sensation (Section 2).

## 5. World and mechanics

### 5.1 Inherited from the midterm [Implemented]

The headless, deterministic engine in `pop/` is the base: fixed-step kinematics, gravity, collision, landing damage, gates, pressure plates, loose floors, spikes and potions. Its rules and their evidence are in [`docs/RULE_SOURCE_MAP.md`](../RULE_SOURCE_MAP.md); tests are in `tests/`. Human and agent play call the same `engine.step`.

### 5.2 New for the final project [Planned]

| Mechanic | Rule (initial) | Open questions |
|---|---|---|
| **Arena** | Six rooms of our own layouts (no original level data), `pop/arena.py`: West Cells, Gatehouse, East Tower above Barracks, Undercroft, Pit Hall, linked in a loop with a shaft from the Gatehouse to the Undercroft. Rivals start in the West Cells and East Tower (mirror images). Each middle room has an open gate between two drop plates (the gate-plate trap spots); Barracks and Pit Hall each hold a guard post. Every row of every room is reachable from both starts in the real engine (`tools/check_arena.py`) | Decided 2026-11-16 (OQ-4) |
| **Second player** | Two prince-type characters in one `GameState`, stepped in the same frame | — |
| **Sword** | `STRIKE` and `BLOCK`, close range. Each rival has 3 hearts. Each stab, trap or damaging fall costs 1 heart; 0 hearts is death. | — |
| **Disguise** | Interact with a downed guard to take the uniform. While disguised and walking, guards ignore you. Running, climbing, drawing the sword or striking breaks the disguise. | OQ-2 exact break conditions |
| **Guards** | Scripted, not AI. Fixed patrol routes. Attack any undisguised rival in view, or a disguised one who breaks the disguise rules. Hostile to both rivals equally. | OQ-5 how guards are downed |
| **Suspicion** | Per-rival meter shown on that rival's HUD; rises when acting oddly near a guard | Cut candidate (yes/no rule) |
| **Traps** | Two types: **loose floor** (rig a floor tile so it drops whoever steps on it next) and **gate plate** (rig a plate to slam a gate). Traps hurt everyone, including the rival who set them; a sprung trap costs 1 heart. Each rival can set 4 traps. A rigged tile looks normal to everyone else. | OQ-6 re-arm time |
| **Online play** | One server holds the only `GameState` and steps it. Each browser sends its player's inputs and receives only its own seat's observation. An AI seat runs on the server and gets the same per-seat observation. | OQ-10, OQ-11, OQ-12 |
| **Disconnect** | A rival who disconnects for more than a grace period loses the duel (proposal) | OQ-13 |
| **Modes** | Human vs human, human vs AI, AI vs AI (watch or test) | — |

### 5.3 Win, loss and edge cases [Planned]

| Situation | Outcome |
|---|---|
| A rival's health reaches 0 from a strike, guard, trap or fall | The other rival wins |
| Both rivals die in the same frame | Draw |
| Time limit reached (OQ-3) | Draw |
| A rival dies on their own trap | The other rival wins |
| An invalid action | Refused, counted, changes no state (as in the midterm runner) |
| An AI seat times out | Labelled fallback action (Section 8 of the [Configuration Document](CONFIGURATION.md)) |
| A human rival disconnects | Proposal: the other rival wins after a grace period (OQ-13) |

No score beyond win, draw or loss is planned.

## 6. Controls and feedback [Planned]

- **Controls:** each player uses their own keyboard with the same key map (OQ-7). Inputs map to the same actions an AI seat sends, as in the midterm; the server validates them.
- **Own screen:** each browser shows only its own rival's current room and HUD. There is no shared screen to look at, so a disguise cannot be seen through by watching the other player's view.
- **HUD:** three hearts, the suspicion icon, a disguised/undisguised marker.
- **Reveal:** a short flash and sound-free animation when a disguise breaks. No sound: excluded, as in the midterm.

## 7. Information boundaries

- **World state (engine only):** both rivals' true positions and uniforms, every guard's patrol and suspicion, which tiles are rigged and by whom, all rooms, and the RNG seed.
- **What the server sends a client:** that seat's observation only. The browser never holds the `GameState`, the other seat's observation or the arena layout, so reading the page's network traffic reveals nothing a player could not see on screen.
- **What a player or AI seat sees:** its own room only; figures in view, with a disguised rival drawn as a guard; a rigged tile drawn as normal unless you rigged it; its own health and suspicion; its legal actions.

The midterm's hidden-information tests (`observe` and `legal_actions` reveal nothing outside the current room) carry over. New tests must check that disguise identity and trap ownership never leak.

## 8. Content scope

| Included by G2/G3 | Excluded | Cut first, in order |
|---|---|---|
| One arena of 4–6 rooms · sword strike and block · disguises · 2 trap types · scripted guards · online play (one server, one browser per rival) · 3 modes · traces and tests | Accounts, matchmaking, more than one duel per server at a time · Levels 2–14 · original level data · sound · AI or adaptive guards · more than two players | 1. Rooms 6 → 3 · 2. Suspicion meter → yes/no rule · 3. One trap type · 4. AI vs AI becomes test-only · 5. Public hosting → two computers on one local network, same server. Never cut: the duel or the disguise. |

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
| OQ-2 | Exactly which actions break a disguise | Saad | Greybox duel |
| OQ-3 | Duel time limit (5 min assumed) | Saad | First playtest |
| OQ-4 | **Decided 2026-11-16:** six rooms (`pop/arena.py`) | Saad | Before G2 |
| OQ-5 | How a guard is downed so its uniform can be taken | Saad | Combat work |
| OQ-6 | Trap re-arm time (limit of 4 per rival is decided) | Saad | Trap work |
| OQ-7 | Key map (one per player, each on their own keyboard) | Saad | Browser client work |
| OQ-8 | **Decided 2026-11-16:** our own PixelLab-generated medieval dungeon art (`assets/generated/`, [`ART_PROVENANCE.md`](ART_PROVENANCE.md)) | Saad (IP) | Before the server is reachable by anyone outside the course |
| OQ-9 | Whether a 4 s AI decision cadence is playable in a sword fight | Playtest evidence | G2 |
| OQ-10 | Where the server is hosted, and who can reach it | Saad (Producer) | First playable recording |
| OQ-11 | Browser client technology (proposal: a small HTML canvas page in plain JavaScript that only draws observations) | Saad, on the agent's proposal | Sun 22 Nov |
| OQ-12 | How much network delay a sword fight tolerates | Playtest evidence | G2 |
| OQ-13 | Disconnect rule and grace period | Saad | Server work |
