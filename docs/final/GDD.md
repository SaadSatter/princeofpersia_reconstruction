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

---

## 1. The X

> Two rivals sneak through a guarded palace, hide in stolen guard uniforms, rig traps for each other, and race to strike the other down first.

- **Action:** sneak, disguise, trap, duel.
- **Experience:** paranoia ("which guard is my rival?"), then the thrill of the reveal.

## 2. Player, platform and genre

| Item | Decision | Label |
|---|---|---|
| Players | Two rivals. Each seat is a human or an AI agent. | Planned |
| Context | Two friends at one computer (local split screen) | Planned |
| Platform | Desktop Python 3.11+ with Pygame, the midterm frontend | Implemented (single player) |
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
| **Arena** | 4–6 rooms of our own layouts (no original level data); both rivals start in different rooms | OQ-4 layout size |
| **Second player** | Two prince-type characters in one `GameState`, stepped in the same frame | — |
| **Sword** | `STRIKE` and `BLOCK`, close range. A hit costs 1 health; 0 health is death. | OQ-1 health and damage values |
| **Disguise** | Interact with a downed guard to take the uniform. While disguised and walking, guards ignore you. Running, climbing, drawing the sword or striking breaks the disguise. | OQ-2 exact break conditions |
| **Guards** | Scripted, not AI. Fixed patrol routes. Attack any undisguised rival in view, or a disguised one who breaks the disguise rules. Hostile to both rivals equally. | OQ-5 how guards are downed |
| **Suspicion** | Per-rival meter shown on that rival's HUD; rises when acting oddly near a guard | Cut candidate (yes/no rule) |
| **Traps** | Two types: **loose floor** (rig a floor tile so it drops whoever steps on it next) and **gate plate** (rig a plate to slam a gate). Traps hurt everyone, including the rival who set them. A rigged tile looks normal to everyone else. | OQ-6 limit per player, re-arm time |
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

No score beyond win, draw or loss is planned.

## 6. Controls and feedback [Planned]

- **Controls:** two keyboard layouts on one keyboard (OQ-7: final key map). Per-frame inputs map to the same actions an AI seat sends, as in the midterm.
- **Split screen:** each half shows only its own rival's current room and HUD.
- **HUD:** health flasks, the suspicion icon, a disguised/undisguised marker.
- **Reveal:** a short flash and sound-free animation when a disguise breaks. No sound: excluded, as in the midterm.

## 7. Information boundaries

- **World state (engine only):** both rivals' true positions and uniforms, every guard's patrol and suspicion, which tiles are rigged and by whom, all rooms, and the RNG seed.
- **What a player or AI seat sees:** its own room only; figures in view, with a disguised rival drawn as a guard; a rigged tile drawn as normal unless you rigged it; its own health and suspicion; its legal actions.

The midterm's hidden-information tests (`observe` and `legal_actions` reveal nothing outside the current room) carry over. New tests must check that disguise identity and trap ownership never leak.

## 8. Content scope

| Included by G2/G3 | Excluded | Cut first, in order |
|---|---|---|
| One arena of 4–6 rooms · sword strike and block · disguises · 2 trap types · scripted guards · split screen · 3 modes · traces and tests | Online play · Levels 2–14 · original level data · sound · AI or adaptive guards · more than two players | 1. Rooms 6 → 3 · 2. Suspicion meter → yes/no rule · 3. One trap type · 4. AI vs AI becomes test-only. Never cut: the duel or the disguise. |

## 9. Balance (initial, untested)

- Strikes and traps must both be able to win a duel; neither should dominate. We will measure it by counting how each duel ends in playtests and AI-vs-AI runs.
- The disguise should survive careful play but not a sword draw.

All numbers are **[Open]** until the greybox duel (see [Project Plan](PROJECT_PLAN.md)).

## 10. References and attribution

| Source | Specific moment or mechanic | Borrowed / changed | Terms |
|---|---|---|---|
| *Prince of Persia* (1989), Jordan Mechner | Level 1 movement, loose floors, gates and plates; guard sword duels | Rules re-written in our own Python (`pop/`); versus play, disguises and player-set traps are new | `historicalsource/princeofpersia` at `2b4ddb5`: README permits study and modification, grants no rights in Prince of Persia (Ubisoft franchise) |
| Original DOS sprites (207 images) | Prince and tile art | Drawn as-is only on the private course branch; placeholder art in public | Basis recorded in [`docs/ASSET_PROVENANCE.md`](../ASSET_PROVENANCE.md); not licensed by the README or SDLPoP's GPL |
| *SpyParty* (Chris Hecker) | The spy must act like the party's scripted guests | Idea only; here both rivals hide among scripted guards | No assets or code |
| *Hitman* (IO Interactive) | Taking a downed enemy's uniform | Idea only; guards judge behaviour, not faces | No assets or code |
| Our midterm (this repository) | Engine, runner, baseline, model player, tests | Reused and extended | Our own work |

Guard and disguise art is unresolved (OQ-8).

## Open questions

| ID | Question | Who decides | Needed by |
|---|---|---|---|
| OQ-1 | Health and damage per strike, trap and fall | Saad (Design Lead) | Greybox duel |
| OQ-2 | Exactly which actions break a disguise | Saad | Greybox duel |
| OQ-3 | Duel time limit (5 min assumed) | Saad | First playtest |
| OQ-4 | Arena size: 4, 5 or 6 rooms | Saad, after the greybox duel | Before G2 |
| OQ-5 | How a guard is downed so its uniform can be taken | Saad | Combat work |
| OQ-6 | Trap limit per rival and re-arm time | Saad | Trap work |
| OQ-7 | Two-player key map on one keyboard | Saad | Split screen work |
| OQ-8 | Guard and uniform art: original sprites (private branch) or our own | Saad (IP) | Before public builds |
| OQ-9 | Whether a 4 s AI decision cadence is playable in a sword fight | Playtest evidence | G2 |
