# Playtest protocol

**Status:** Approved by Saad 2026-11-27 (decision #126); frozen from this date — a change is a new version (kit drafted in T11). A change is a new protocol version, recorded in
`LOG.md` with its date and reason.

Files in this kit:

| File | Use |
|---|---|
| [`CONSENT.md`](CONSENT.md) | Read aloud before play; debrief text |
| [`PROTOCOL.md`](PROTOCOL.md) | This script and the frozen definitions |
| [`QUESTIONNAIRE.md`](QUESTIONNAIRE.md) | Per-round and end-of-session questions |
| [`OBSERVATION_TEMPLATE.md`](OBSERVATION_TEMPLATE.md) | Timestamped sheet, observations before interpretation |
| [`LOG.md`](LOG.md) | Playtest log template (proposal for CQ-6) |

Sources: FINAL_REQUIREMENTS section 5 (external core-loop playtest at
G2/G3 [R]; playtest log fields [R]; counterbalanced, blind comparison and
identification definitions [+]); the G1 playtest question
(`docs/final/CONFIGURATION.md` A7); the G1 motivations (`docs/final/GDD.md`
section 2); Saad's decisions of 2026-11-23 #1 (local demo: human vs human
on two panels; human vs AI with only the human's panel) and #3 (the AI rival
is a trained PPO policy; the scripted baseline is the comparison).

---

## 1. Roles

| Role | Who | Does |
|---|---|---|
| Facilitator | Saad or a helper | Reads consent, explains controls, starts rounds, asks the questions. Says nothing about strategy or the rivals during play |
| Observer | Saad or a helper (may be the facilitator in a one-person session) | Fills the observation sheet: what is seen and heard, with times. No interpretation on the sheet |
| Player | External person (not Saad, not on the project, not an agent) | Plays |

An agent never acts as player or observer and never fills in any sheet.

## 2. Session types

Three types: A (core loop, required), R (external retest of a revised
encounter, required [R] between G2/G3 and G4) and B (comparative,
recommended). A and R are not comparative tests.

### Session A: G2/G3 core-loop session (required [R])

**Purpose:** observe at least one external player using the core loop
(act, respond, interpret, next action; GDD section 4) and collect first
answers to OQ-9 and the balance questions. It does **not** test the
comparative hypothesis.

**Build:** whatever the G2/G3 build is on the day, at a recorded commit or
deployed version. Use the first that is available:

0. **Preferred, hosted web build (Saad's decisions of 2026-11-23 #12-13:
   Pyodide + Phaser, due by G2/G3):** URL `<TO BE FILLED IN BY SAAD>`.
   Record the URL, the build id or commit the page reports, and the date.
   Do not assume it writes a round file: the per-round trace download is
   planned (T14) and **not yet verified**; use consent option (a) unless the
   facilitator has seen the file saved (`CONSENT.md`, "Logging rule").
   The remaining options are the local bench, kept as the fallback if the
   hosted build is down or not ready.
1. **Local bench, when T12 is merged:** human vs scripted baseline,
   `play.py ARENA --versus --rival baseline` showing only the human's panel.
   Identification events can be scored (Section 3).
2. **Otherwise (local fallback):** human vs human on the two-panel bench,
   `play.py ARENA --versus` (one keyboard, two panels). Both panels are on
   one screen, so each player can see where the other is and who wears a
   uniform. **Identification events are not scored** in this setup; the
   sheet marks the session `identification: contaminated`. A physical
   divider over the middle of the screen reduces this but does not remove
   it (the players sit side by side). If the second player is Saad or a
   project member, mark it: they know the rules and the arena.

**Script (about 20 minutes):**

| Time | Step |
|---|---|
| 0:00 | Consent (`CONSENT.md`), player code card, recording answers on the sheet header |
| 0:03 | Controls card and one sentence of goal: "Bring your rival's hearts to zero before they do it to you. Guards attack anyone who is not in uniform." Nothing about tactics |
| 0:05 | Round 1 (up to 5 min). Observer fills the sheet |
| 0:10 | Round questions (`QUESTIONNAIRE.md` part R), about 1 min. Note whether a rematch is asked for and how many seconds after the round ended, **before** offering one |
| 0:11 | Round 2 (up to 5 min), questions |
| 0:17 | Round 3 only if time allows and the player wants it |
| 0:17 | End questions (part E), debrief (`CONSENT.md`) |

### Session R: external retest of a revised encounter (required [R])

**Purpose:** FINAL_REQUIREMENTS asks for an external test of the revised
encounter between G2/G3 and G4. Each Session R tests one specific change made
in response to an earlier finding, so the playtest log shows finding ->
change -> retest.

**Link to a change (filled before the session, never invented):** the sheet
header names

1. the finding (log row and its source session or review, e.g. a Session A
   observation);
2. the change (commit or pull request that made it);
3. what would count as the change working, written before the session in
   words the observer can check on the sheet (for example "player names the
   rival without a prompt", or "no `STUCK` at the door").

A Session R without all three is run as Session A instead. If several
findings were fixed, test the most important one per session and list the
rest. Use a different external player where possible; a returning player (a
code seen before) is marked as such and does not replace a fresh one.

**Script:** as Session A (about 20 minutes), rounds on the revised build
only, same questions. Results go in `LOG.md` section 6 (changes and
verification) next to the change they test, whatever the outcome; "the
change did not work" is a valid, recorded result. Hypotheses are not tested
here.

### Session B: comparative session (recommended [+]; G4 at the earliest)

**Purpose:** answer the G1 playtest question: do players misidentify the
disguised policy rival more often than the scripted one, and rate it more
tense (1–7)? The rival does not need to win, and the hypothesis does not
need to be confirmed.

**Conditions:**

| Code on the sheet | Rival seat |
|---|---|
| X or Y (sealed) | Scripted baseline (`agents/baseline.py`, versus macro version from T05) |
| X or Y (sealed) | Trained PPO policy (T07), weights frozen and hashed before the first session |

The mapping of X and Y to rival types is written by someone other than the
observer (or generated by a script) and sealed until the session's results
are tallied. The facilitator launches by condition code and does not know
which rival it is.

**Blindness:** same rival name ("Rival"), same sprite and colour, same start
rules, same HUD, same end screen in both conditions. The human sees only
their own panel; the other seat's panel is never drawn. The facilitator tells
the player only "You will play against computer-controlled rivals."
Disclosed risk: the two rivals may differ in reaction speed or decision
cadence, which a player could notice; the end questions check blindness
(part E, question E3).

**Counterbalancing:**

- Each player plays one round in each condition: order XY or YX.
- Orders alternate by arrival: P01 XY, P02 YX, P03 XY, ... The list is written
  before the first session; a player who stops early keeps their slot.
- If a player has time for four rounds, use XYYX or YXXY (the same
  alternation). Report two-round and four-round players separately.
- Map asymmetry: the human's start (West Cells or East Tower) alternates
  within each player, so each condition is played from both starts across
  players. Keep the human's colour fixed (the rival is always the same
  colour) when the seat changes.
- Seeds: a list of playtest seeds is fixed before the first session and
  assigned in order. Playtest seeds are not taken from the held-out H6 set,
  and nothing is tuned on playtest results before the comparison is closed.

**Script (about 20 minutes):** as Session A, except: a practice round of at
most 2 minutes first (rival seat idle, or no rival if the build allows),
never counted; then the two counted rounds in the assigned order; then the
end questions, including E3 (blindness check) before the debrief reveals
anything.

## 3. Frozen definitions

These are scored from the two-seat trace (ground truth of who wears which
uniform; Session B needs it, see Section 4 item 4) together with the observation sheet and the player's answers, after
the session. The observer does not judge them live.

**Disguised rival.** The rival seat is wearing a guard uniform (R-V17,
R-V18): it is drawn as a guard and observed through the same fields as a guard.
This is **not** a claim that it is indistinguishable. Known remaining tells
(not hidden by the build):

- position: real guards never leave their room or row (GATE-T01-eval tells
  list, tell 1);
- reaction: a real guard draws on an undisguised rival in front of it, a
  disguised rival does not (tell 2);
- stillness and patrol: stillness beyond a guard's, or off its patrol, ends
  it (tell 3); repeated WAIT beside a guard resets the stillness counter
  (GATE-T01-qa QA3);
- movements no guard makes: falling, hanging, dead postures (QA2), a
  disguised step into the next room (QA1: `motion.to` null for 8 frames),
  hop, jump, climb, unarmed run (tell 4);
- a one-frame gap between moves (tell 5), and a meterless "guard" when both
  rivals are disguised (tell 6).

The playtest therefore records **which cue a player used** for each
identification (position, guard reaction, stillness, odd movement, other, or
guess); question R2 collects it and the observer notes any spoken reason
verbatim. Identification rates are reported with that cue breakdown and are
not read as evidence about the policy alone. Which tells are fixed by the
day of a session depends on the build; record the build.

**Identification opportunity.** An interval during which the disguised rival
is in the human seat's current room, so it appears in the human's
observation. It starts on the first frame this is true and ends on the first
frame it is no longer true: either leaves the room, the disguise breaks, or
the round ends. Each opportunity is tagged:

- `with-decoy` if at least one real standing guard is in the same view at
  any frame of the interval; otherwise `solo`.

**Correct identification.** During an opportunity, or within 2 s after it
ends, the human either

- (strike) starts an attack (lunge, throw, kick, sweep) aimed at the
  disguised rival: the attack hits it, is blocked by it, or targets the cell
  it occupies; or
- (named) says aloud that a specific figure is the rival, and that figure is
  the disguised rival (observer records the words and time; checked against
  the trace).

**False identification.** At any time, the human strikes a **real guard**
or names a real guard as the rival, **and** the player's answer to the
round question R3 says they thought that guard was the rival. A strike on a
guard for another reason (to take its uniform, self-defence, accident) is a
*guard strike, other intent* and is not a false identification. If R3 is
not answered, the strike is scored `unknown intent` and reported separately.

**Missed rival.** An opportunity that ends with no correct identification.
Sub-tagged by how it ended: `rival left`, `human left`, `disguise broke
(not by the human)`, `round ended`.

**No encounter.** A round with no identification opportunity at all. Such a
round contributes to tension, fairness and rematch measures but not to
identification rates.

**Undisguised meetings** (the rival is visible as itself) are recorded but
are not identification opportunities.

**Measures per condition** (reported with counts, not only rates):

| Measure | Definition |
|---|---|
| Opportunities | Number, split `with-decoy` / `solo` |
| Correct identification rate | Correct identifications / opportunities |
| Missed rate | Missed rivals / opportunities |
| False identifications | Count per round (not per opportunity: a guard can be struck when no rival is in view) |
| Misidentification (G1 question) | Missed + false identifications, reported as both counts and their sum |
| Time to identify | Seconds from opportunity start to correct identification |
| Tension | Round answer R1, 1–7 |
| Fairness | Round answer R4, 1–7 |
| Rematch | R5, and the observed seconds to a spontaneous rematch request |
| Motivation signals | From the sheet: rematch within 30 s; changed approach after a loss; spoken reveal reaction ("that was you?!" or similar) |

With the expected number of players (a handful), results are described, not
tested for significance. Every round is reported, including no-encounter
rounds and stopped sessions.

## 4. What must be built for Session B (input to T12)

Session B cannot run until all of these exist and are tested:

1. `play.py ARENA --versus --rival baseline|policy` with only the human's
   panel drawn (T12), and a way to launch by sealed condition code so the
   facilitator does not see the rival type on the command line or window
   title.
2. The scripted baseline on the versus macro layer (T05) and a frozen PPO
   policy with a recorded weights hash (T07).
3. Identical presentation in both conditions: name, sprite, colour, HUD, end
   screen, no rival-type text anywhere on screen.
4. A two-seat trace written per round, with: build commit, condition code,
   seat, start, seed, time limit, and per frame which figure is the disguised
   rival (ground truth for Section 3). The trace must stay out of the
   player's view. Status: not verified in any build at this kit's base
   (local bench: in-memory only; hosted build: planned in T14). Session B
   cannot be scored without it.
5. A clock or frame counter the observer can see, matching the trace, so
   sheet times line up with trace frames.
6. The 5-minute duel limit (Saad's decision of 2026-11-23 #5: 3,600 frames
   at 12 fps). It is the default since T01, so it is not set by hand. Check,
   do not assume: at the start of each session the observer confirms that the
   build shows 5:00 (or 3,600 frames) at round start and records it in the
   sheet header.
7. A quick rematch key on the end screen, so a rematch request can be acted
   on and timed.
8. Optional: an idle-rival practice mode.

Session A (options 0 and 1) needs items 1 (baseline only), 5 and 6; item 4
(the trace) only if consent option (b) is to be used, otherwise sessions run
on notes and answers alone and identification is scored from the sheet and
answers with the build's ground truth left unavailable (record that). Session
A (option 2) needs only item 6 and a recorded commit.

## 5. During play

- Do not help, hint or react. If asked "what does this do?", answer only
  controls questions.
- If the build crashes: note the time and what was on screen, restart the
  round on the same seed if the player agrees, and record the crash as a
  finding.
- If the player stops: thank them, ask whether the notes may be kept
  (`CONSENT.md`), and record "stopped at mm:ss" without a reason unless they
  give one.
