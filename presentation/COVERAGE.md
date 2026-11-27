# Recording-requirements coverage checklist (spec deliverable 7)

Copied unchanged from the Requirements Auditor's report `docs/final/orchestration/reports/T33-requirements-auditor.md` at commit `c3ba2b0` (branch `audit/T33`), which audited deck `task/T33` b64f58c. Row statuses are the auditor's, as of that commit. Fixes made afterwards in T33-fix1 (Keynote-importable deck, tracked MP4, slide 3, 6 and 1 wording, clip-timed narration) are listed in `docs/final/orchestration/reports/T33-fix1-tech-lead.md`; this file is not re-audited.


# T33: requirements-auditor report

Status: done. Read-only audit; nothing run except `git show`, a python-pptx dump of the shipped pptx (read only), and viewing the seven slide JPGs at `presentation/out/slides/` on b64f58c.

Source used for every row: Saad's specification `G23_PRESENTATION_REQUEST.md` (sections 1, 3, 5) and the G2/G3 lines of `FINAL_REQUIREMENTS.md` section 6 (2026-11-23). Evidence is on `task/T33` at b64f58c, not on `main`. Notes quoted below are the shipped pptx speaker notes (the same text is in `presentation/NARRATION.md`). I did not play the video in PowerPoint (QA's job) and did not re-run the replay hash, so those are marked as taken from the tech-lead report where relevant.

## Verdict in brief

No requirement is MISSING from the deck. Main gaps: (a) the standalone MP4 is not tracked on `task/T33` (the repo's `.gitignore` has `*.mp4`; only the copy inside the pptx, `ppt/media/media1.mp4`, 1,468,240 bytes, exists in git); (b) deliverables 7 (coverage checklist) and 8 (QA report) are not in the tech-lead's output (7 is this report; 8 is the next gate); (c) slide 3 cannot show what the player would lose without the learned rival, because no comparison exists (stated honestly on the slide); (d) the scope lock's fallbacks have no per-item trigger; (e) two PARTIALs are limited to what the records can support, not to a deck defect.

## Compliance matrix

Status key: PASS / PARTIAL / MISSING / BLOCKED / N/A. "S" = slide, "N" = speaker note (also in NARRATION.md).

### Spec section 1: recording requirements

| Section | Requirement (short) | Label | Status | Evidence | Gap |
| --- | --- | --- | --- | --- | --- |
| 1 | Core loop played: act, respond, interpret, next action, with the in-game agent taking part | [R] G2/G3 core loop | PARTIAL | S2 loop diagram (Act, Game responds, Interpret, Next action) and box 4 "Meet the PPO-controlled rival ... Its move decides mine"; N2 narration and `DEMO_RUNBOOK.md` route | The play itself is live, to be done by Saad. Nothing is pre-recorded. The slide 4 clip (a replay) shows a human vs the rival, so it backs the loop in part. Closes when Saad records. |
| 1 | Agent contribution and what the player would lose if the baseline replaced it, with a trace or result | [G1] | PARTIAL | S3 "OBSERVED" box (16 duels, 13/2/1, bar 14, NOT SUPPORTED) and "NOT OBSERVED" box (H1, H2 untested; "what a player would lose ... is an open question") | The result supports capability only. No trace or comparison shows the loss, and the deck says so (correct, not invented). Closes only with Session B (human vs baseline), not by deck edit. |
| 1 | One external playtest: observed behaviour before interpretation, then change or open question | [R] | PASS | S4: observer notes box (LOG.md s4, verbatim) above the interpretation box (LOG.md s6, verbatim), then OPEN QUESTION; N4 | Order on the slide is observations, replay box, interpretation, question. "Resulting change": none exists, the slide gives an open question as allowed. |
| 1 | Two tailored starter agents and one genuine handoff with the student decision | [R] | PASS | S5: Tech Lead and QA as "course agent"; T02 chain with "I consider this handoff complete." (7c4fc1d); N5 sources `handoff-drafts/2026-11-24-qa-to-tech.md` | Quote and commits taken from the deck/notes; I did not re-open the handoff file for each sha (QA to verify). |
| 1 | Deterministic tests passing in CI, and budgeted live evaluation: trials, outcomes, cost, failures | [R] | PARTIAL | S6 verification box (dev CI green, run 46065581056; local 2376 passed, 11 skipped, 5 xfailed; official CI queued); S3 footer: cost "$0 API", "Final-project paid LLM calls: none", failures "0 aborted, 0 runner fallbacks in 48 trial rows", inference errors "not recorded"; N3 | There is no budgeted live (paid) evaluation to show: the under-$1 smoke is unspent (S3). The deck states that plainly. Trials/outcomes/cost/failures are given for the PPO run. Gap is in the project, not the deck. |
| 1 | Scope lock, exclusions, fallbacks with triggers and actions | [R] | PARTIAL | S6 IN SCOPE, OUT/DEFERRED, FALLBACKS boxes; N6 | See section 3 row "Fallbacks". Triggers are thin because SCOPE_LOCK has only "if time runs out". |
| 1 | Alpha Dec 2, Beta Dec 4, Gold Dec 5 acceptance checks | [R] G4 | PASS | S7 three milestone cards, each with checks and "Proposed, not yet approved"; N7 states the records name no approved Alpha/Beta check | Checks are proposals, labelled as the spec requires. Saad must approve (no approval on record). |
| 1 | Explicit G2 and G3 approval requests, and what resolves a Hold | [R] | PASS | S7 "G2 APPROVAL", "G3 APPROVAL" with the spec's wording; "HOLD, if" lists open items; N7 | Hold box names the unresolved items but not the closing action per item beyond "Resolve each before approval" (see Contradictions). |
| 1 | Do not invent results, evidence, approvals or behaviour | [R] honesty | PASS | S4 "Replay shows" box vs notes (decision #135); S3 numbers match SCOPE_LOCK known limitations (13/2/1 of 16, bar 14, NOT SUPPORTED, #77); N2 "Do not describe the live rival's moves as scripted" | Spot-check only. Full fact check is QA's job. |

### Spec section 3: slide structure

| Section | Requirement (short) | Label | Status | Evidence | Gap |
| --- | --- | --- | --- | --- | --- |
| 3 | At most 7 slides, narrated, 3-5 min | [R] | PASS | pptx has 7 slides, notes slots sum 0:00 to 4:30 (N1 to N7) | Spoken words about 568 (tech-lead est. 3:47 at 150 wpm); 4:30 depends on the clip and live demo. QA times it. |
| 3.1 | Slide 1: competitive two-player stealth platformer, rival swordsmen, disguise, environment, eliminate each other | [R] | PASS | S1 "A competitive two-player stealth platformer"; "Two rival swordsmen share one palace. Each can disguise himself as a guard, set traps, and try to eliminate the other." | "Manipulate the environment" is covered by "set traps". |
| 3.1 | Slide 1: tension, deception, uncertainty, tactical combat | [R] | PASS | S1 four tiles, plus the line "you cannot tell a rival from a guard until it is too late" | None. |
| 3.1 | Slide 1: actual gameplay screenshot or title art | [R] | PASS | S1 picture `presentation/shots/rehearsal-guard-down.jpg` (real renderer, generated art), captioned as a real frame; N1 says it is a scripted rehearsal frame | The on-slide caption says "the player has struck down a palace guard" and does not say "scripted rehearsal"; only the notes do. Minor. |
| 3.1 | Slide 1: Saad's name and "G2/G3 First Playable"; 15 s | [R] | PASS | S1 "Saad Satter / G2/G3 First Playable"; N1 slot [0:00 to 0:15] | None. |
| 3.2 | Slide 2: dedicated demo slide | [R] | PASS | S2 "First Playable: Live Gameplay Demo" | None. |
| 3.2 | Slide 2: Act, Game responds, Interpret, Next action | [R] | PASS | S2 four boxes with arrows | None. |
| 3.2 | Slide 2: short demo sequence: movement, guard fight and uniform, disguise and suspicion, PPO rival, combat/evasion/trap, rival's influence on next decision | [R] | PASS | S2 cues 1 to 4 (cue 4: "combat, evasion or a trap. Its move decides mine."); `DEMO_RUNBOOK.md` "Route and beats" steps 1 to 5 | Route is checked only with a scripted bot and the rival out of the way (runbook). A live run may differ; the runbook gives a 0:50 cut-off. |
| 3.2 | Slide 2: gameplay screenshot and a few visual cues, not detailed instructions | [R] | PASS | S2: three stills + four cues; controls only in notes | Stills are labelled on-slide as a scripted rehearsal. |
| 3.2 | Slide 2: exact launch command in notes; reliable starting configuration | [R] | PASS | N2 `uv run --extra play python play.py ARENA --mode ai --seed 0 --scale 3`; runbook says it matches the playtest seed 0; tech-lead reports the command exits 0 with `--screenshot` | Not re-run by me. The `ARENA` argument and mode are existing options. |
| 3.2 | Slide 2: no rule change; scripted demo not passed off as spontaneous AI | [R] | PASS | N2 last lines; S2 footer "scripted rehearsal ... The live demo is played by hand."; runbook "What is real and what is not" | None. |
| 3.3 | Slide 3: PPO vs scripted baseline; diagram Partial observation, PPO policy, Legal action, Game engine | [R] | PASS | S3 four-box diagram with those labels | None. |
| 3.3 | Slide 3: what the learned rival contributes and what could be lost; observed vs hypotheses | [G1] | PARTIAL | S3 OBSERVED vs NOT OBSERVED boxes; H1, H2 labelled untested | The deck gives no observed player-experience contribution (none exists); the playtest observations are on S4. Honest, but the "contribution" is only capability. |
| 3.3 | Slide 3: held-out T09: 16 trials, 13 W, 2 D, 1 L, bar 14, NOT SUPPORTED | [G1] | PASS | S3 box and N3; matches `SCOPE_LOCK.md` known limitations at 43e9ce1 ("13 W, 2 D, 1 L of 16 held-out duels, bar 14, NOT SUPPORTED (#77)") | I did not open `evaluation/RESULTS-T09.md`; the second source is the scope lock. QA/Evaluation to confirm. |
| 3.3 | Slide 3: strong capabilities but missed the pre-registered threshold | [G1] | PASS | S3 "It won most duels but fell under the bar set in advance"; N3 "not that the rival is weak" | "Strong capabilities" is carried only by the win rate; the playtest wording is on S4. |
| 3.3 | Slide 3: actual cost, failures, trial counts; do not confuse local PPO with paid LLM evaluation | [G1] | PASS | S3 footer: "$0 API", "Final-project paid LLM calls: none", "0 aborted, 0 runner fallbacks in 48 trial rows. The policy's own inference errors were not recorded"; N3 "Do NOT say" list | "48 trial rows" next to "16 duels" may confuse a viewer (16 duels x 3 trials, the slide says "3 trials per duel"). The spoken line avoids "48". |
| 3.4 | Slide 4: use the actual LOG.md Human vs AI playtest | [R] | PASS | S4 "room XGJT, duel 1"; LOG.md s3 row for XGJT at 43e9ce1 (A1, P01, external yes) | None. |
| 3.4 | Slide 4: Saad's five observations | [R] | PASS (as verbatim) | S4 observer-notes box quotes LOG.md s4 in full; the notes are worded slightly differently from the request ("struggled to counter ... and interrupt its attack sequences") | They are quoted verbatim from LOG.md per decision #135, not paraphrased. |
| 3.4 | Slide 4: observations before interpretation; Saad's interpretation | [R] | PASS | S4 order: observer notes, interpretation (LOG.md s6 verbatim) | None. |
| 3.4 | Slide 4: the open design question, exact text | [R] | PASS | S4 red box: "Can human players develop effective counterstrategies against the trained rival, or does combat need balancing?" | None. |
| 3.4 | Slide 4: inspect telemetry and identify the room and duel | [R] | PASS | `REPLAY_AUDIT.md`; tech-lead report: XGJT duel 1, XUKM is Human vs Human; LOG.md s3 | I did not rerun this. |
| 3.4 | Slide 4: decide full / partial / impossible and replay deterministically with matching build, verified events | [R] | PASS (per tech-lead; not independently reproduced) | Tech-lead report: `server.trace.replay` gives outcome `won:B`, 465 frames, hash `5dadb78e...a910` equal to recorded; version diff from `6eaced529faf` and `cca7002` to ab395fc empty; events (hits 417/441/465, sword drop 465, rooms) agree. N4 repeats it | QA must reproduce the hash. Verdict "full" is stated in the report, the pptx and N4. |
| 3.4 | Slide 4: real renderer and assets; representative 20-25 s segment; label; MP4 embedded | [R] | PARTIAL | pptx contains `ppt/media/media1.mp4`; S4 shows the clip's poster with the label "External playtest — reconstructed from telemetry" on the frame; clip is 22.83 s (tech-lead ffprobe); ticks 216 to 465 | Playback inside PowerPoint not tested by tech lead. The standalone MP4 is not in git (see Deliverables). The segment shows hits on the human, not the "disarming" or "attack sequences" the spec prefers (the replay does not support them, N6/#135). |
| 3.4 | Slide 4: no invented AI actions; partial labelling rules | [R] | PASS | Slide captions state replay facts only; "Replay shows" box; N4 "The replay supports strong combat, not every item in my notes" | Labelled "reconstructed", not "full original footage": viewer is Seat A with the pygame renderer, not the Phaser client the player used (N4 says so; the slide does not). |
| 3.4 | Slide 4: verify consent and publication; no personal data | [R] | PASS | S4 footer "Published with the player's consent (option b)"; N4 cites LOG.md s3 ("Notes publishable: yes", decision #130); player code only, no name on the slide | Telemetry JSON is not published on the slide; the file path appears only in the notes. |
| 3.4 | Slide 4: 45 s including the video | [R] | PARTIAL | N4 slot [1:55 to 2:40]; clip 22.83 s plus about 22 s narration | Tight, with a dense slide (12.5 pt verbatim quotes, per tech-lead). QA to time and check readability. |
| 3.5 | Slide 5: Student, Opus Orchestrator, Sonnet Tech Lead and QA with supporting specialists | [R] | PASS | S5 left diagram | None. |
| 3.5 | Slide 5: two formal agents separate from supporting workers and the PPO rival | [R] | PASS | S5 "course agent" labels; "Supporting workers: Evaluation Specialist, Requirements Auditor, rules reviewer"; red box "In-game PPO rival: a game feature, not a production agent" | None. |
| 3.5 | Slide 5: Tech Lead and QA responsibilities | [R] | PASS | S5 text under the diagram, matching the spec wording | None. |
| 3.5 | Slide 5: T02 chain and the specific leak | [R] | PASS | S5 five boxes (QA finds the leak, Student approves, Tech Lead fixes, QA verifies, Student accepts); "Why it mattered" line about motion metadata | None. |
| 3.5 | Slide 5: student decisions: hopping raising suspicion, disguised movement treatment | [R] | PASS | S5 "Hop +6 suspicion per frame (48 per hop, #18); DOWN reads as standing still"; decision numbers #4, #7, #18, #120 | "DOWN reads as standing still" is the treatment as the deck words it; check against the decision text (QA). |
| 3.5 | Slide 5: 650 passed, 12 skipped, 2 expected failures, verified against the handoff | [R] | PASS (unverified here) | S5 "650 passed, 12 skipped, 2 xfailed" at 72f6552; N5 says the 2 xfails are open T04 findings | I did not open the handoff file. Spec says "unrelated expected failures": N5 agrees. QA to confirm. |
| 3.5 | Slide 5: commit references or links | [R] | PASS | S5 shows 558ef6d, a1100f6, 72f6552, 7c4fc1d, 13c7488; N5 lists both repo URLs | No clickable links on the slide, short shas only. |
| 3.6 | Slide 6: latest deterministic results and green dev CI | [R] | PASS | S6 "Dev CI: green ... run 46065581056, success"; "Local suite: 2376 passed, 11 skipped, 5 xfailed" (tech-lead run at 74a918e) | CI status was read at 15:56 ET by the tech lead; it must be re-read before recording (note N6 says so). Local run is on a different commit from the CI run (74a918e vs main 43e9ce1). |
| 3.6 | Slide 6: disclose official CI queued if still so | [R] | PASS | S6 "Official repo CI: not passed ... queued on the course runner (run 46058158697) at last check" | Status could change by recording time; N6 tells him to re-check. |
| 3.6 | Slide 6: In scope (duel/disguise/suspicion/guards, six rooms and 5 min, loose-floor traps, PPO and baseline, modes and deployment) | [R] | PASS | S6 IN SCOPE box; matches `SCOPE_LOCK.md` In-scope table | None. |
| 3.6 | Slide 6: Excluded vs deferred, from the actual lock | [R] | PASS | S6 "Out: gate-plate trap, accounts, public server, levels 2-14, original level data, sound, LLM rival" vs "Deferred (needs approval, #123): retraining PPO, AI trap rigging, movement changes or side-scroll" matches SCOPE_LOCK | "Adaptive guards", "more than two players", "matchmaking" are omitted for space. The lock calls the public server "not excluded forever (#123)"; the slide lists it under "Out", then #123 under "Deferred", which blurs the split slightly. |
| 3.6 | Slide 6: every approved fallback, with trigger and action | [R] | PARTIAL | S6 FALLBACKS box: the five-step cut order ("If time runs out, cut in order ..."), plus AI timeout and Human-drops fallbacks from GDD s5 (per N6) | Scope lock has only the cut order, with one trigger ("if time runs out"). The two runtime fallbacks are from the GDD failure table, not the scope lock; N6 discloses this. No per-fallback trigger exists to show. |
| 3.6 | Slide 6: limitations: threshold not met, online testing limits | [R] | PASS | S6 LIMITATIONS: rival missed the bar; online on localhost only, no two-machine or latency test; hosted page devtools | Other lock limitations (taps move a whole block, no AI traps) omitted. |
| 3.7 | Slide 7: Alpha Dec 2, Beta Dec 4, Gold Dec 5 timeline | [R] | PASS | S7 three cards with dates | None. |
| 3.7 | Slide 7: each milestone has an observable acceptance check from the plan and lock; else proposed | [R] | PASS | S7 checks labelled "Proposed, not yet approved"; N7: no approved Alpha/Beta check exists in PROJECT_PLAN.md or SCOPE_LOCK.md (only "Sat 5 Dec Gold build recording") | Not independently grepped for a Beta check in PROJECT_PLAN; I did not search it. Some checks (e.g. "All three modes launch from the menu") are observable; "Combat-balance question has a test plan" is weaker. |
| 3.7 | Slide 7: G2, G3 and Hold requests; official repository link | [R] | PASS | S7 G2/G3 boxes, HOLD box, link `https://github.com/columbia-university-ai-games/final-saadsatter` and "G2/G3 commit a251335" | None. |
| 3 | Style: dark medieval palace, real screenshots, large type, minimal text, no mock-ups | [R] | PARTIAL | S1, S2, S4 use real renderer images; dark navy/gold palette. S3 to S7 are text boxes | S4, S6 and S7 are text-dense and mostly small type (S4 quotes 12.5 pt per the tech-lead). Spec asks for minimal text. Readability is QA's check. |
| 3 | Detailed speaker notes with narration and timing per slide; total 4:30 | [R] | PASS | Every slide has notes beginning `[start to end (n s)]` with NARRATION; slots total 4:30 | None. |

### Spec section 5: deliverables

| # | Deliverable | Status | Evidence | Gap |
| --- | --- | --- | --- | --- |
| 1 | Editable PPTX, at most 7 slides | PASS | `presentation/out/ShadowMasque-G2G3.pptx` at b64f58c, 7 slides, 7 notes; `build_deck.py` | None. |
| 2 | PDF of slides | PASS | `presentation/out/ShadowMasque-G2G3.pdf` (Keynote export of a notes-free copy; tech-lead says slides are identical) | I did not open the PDF. The PDF carries no speaker notes (disclosed). |
| 3 | Reconstructed external-playtest MP4 | PARTIAL | Not in `git ls-tree` at b64f58c: `.gitignore` line 33 is `*.mp4`. Only `ppt/media/media1.mp4` inside the pptx. Report cites `presentation/out/xgjt-001-segment.mp4` (22.83 s) and runbook fallback 4 tells Saad to play it from Finder | The standalone file exists only in the tech-lead's local worktree if at all. Closes by extracting it from the pptx, or force-adding it, or saying it is local-only. Runbook fallback 4 depends on it. |
| 4 | Embedded video playback in the PPTX | PARTIAL | MEDIA shape on slide 4, `media1.mp4` present in the package | Not played in PowerPoint or Keynote (tech-lead states Keynote cannot open the shipped pptx). Poster shows tick 420 in PowerPoint, the first frame in Keynote. Needs QA to try PowerPoint. |
| 5 | Speaker notes and a standalone narration script with timestamps | PASS | notes on all 7 slides; `presentation/NARRATION.md` with slots | The standalone script omits the SOURCES and PROVENANCE blocks (they are only in the notes). |
| 6 | Live demo runbook with commands, steps, fallback | PASS | `presentation/DEMO_RUNBOOK.md`: command, route in five beats, four ordered fallbacks, "what is real" section | Route not tested with a hand-played run or with the live rival. Fallback 2 and 3 need pygame and the network once. |
| 7 | Recording-requirements coverage checklist | PARTIAL | Not in the tech-lead's `presentation/` tree. This report's matrix is the coverage map | No checklist file lives in `presentation/`. Close by committing this matrix (or a copy) to the presentation folder at Gate 3. |
| 8 | QA report (evidence accuracy, provenance, readability, playback, timing) | N/A to this task | QA stage `gate/T33-qa` not yet run | Pending QA. |
| 9 | Presentation directory with source and generation scripts | PASS | `presentation/build_deck.py`, `render_replay.py`, `shots.py`, `export_keynote.applescript`, `README.md` | None. |
| 10 | Render and inspect every slide; test video where supported; report limits | PASS | `presentation/out/slides/slide-001..007.jpg` (JPGs; I viewed all seven); tech-lead states the playback limit | Clipping: I saw none in the seven images. S4 and S6 are the densest. |
| 11 | Do not record Saad's narration | PASS | None recorded (`git ls-tree` shows no audio) | None. |
| 12 | Isolated from the graded snapshot; no gameplay change | PASS | Tech-lead: `git diff --name-only ab395fc..HEAD` lists only `presentation/**` and the report | I did not rerun the diff. |

### G2/G3 lines of FINAL_REQUIREMENTS.md section 6

These concern the recording and the gate. Repository and README items are outside the scope of T33 (status shown for the recording only).

| Section | Requirement (short) | Label | Status | Evidence | Gap |
| --- | --- | --- | --- | --- | --- |
| 6 G2/G3 | Official repository migration, README/tracker links, scope lock, dated GDD/config update | [R] | N/A to T33 | The deck links the official repository on S7 and notes (a251335); the migration itself is T03 (REVIEW_LOG: official PR #2 merged to a251335) | Not audited in this task. |
| 6 G2/G3 | Two tailored production agents, coverage map, one routed handoff and student decision | [R] | PARTIAL | S5 shows the two agents and the T02 handoff with the Student's acceptance | The coverage map is not shown on any slide, and the spec does not ask for it in the recording. |
| 6 G2/G3 | External core-loop playtest, deterministic CI, live evaluation evidence | [R] | PARTIAL | S4 (playtest), S6 (CI), S3 (evaluation) | One external player, official CI queued, no paid live evaluation. Shown honestly. |
| 6 G2/G3 | Demonstrate integrated duel, disguise, scripted guards, model rival; document approved scope cuts and current limitations | [G1] | PARTIAL | S2 and runbook (demo), S6 (cuts, limitations) | The demo is Saad's live run, not yet done. |
| 6 G2/G3 | Push graded version to main; submit 3-5 minute recording and discussion link; check Gate decisions issue | [R] | N/A to T33 / BLOCKED | Deck prepares the recording; Saad must record and submit it | Recording and submission are Saad's actions; not done. The deck is not on `main`. |
| 6 G2/G3 | Three Braintrust replies by Mon Nov 30 | [R] | N/A to T33 | Not part of this task | None. |

## G2/G3 blockers

1. Saad must record the narration in one continuous session; nothing is recorded (by design). Live demo is unrehearsed with the real rival.
2. Official CI run 46058158697 is "queued" at last check; re-read it before recording and change slide 6 if it moves. Until it passes the deck says "not passed".
3. The standalone MP4 is missing from `task/T33` (gitignored). Needed for runbook fallback 4 and deliverable 3.
4. Video playback inside PowerPoint is untested (QA gate).
5. Alpha and Beta checks are proposals; G3 asks Saad to approve them. No approval on record.
6. Decision #135 handling of observer-note claims the replay does not support: recorded and shown on S4; Saad has already decided (#135). Not a blocker, noted for completeness.

## G4 blockers

1. No approved Alpha or Beta check exists; Gold check list is a proposal.
2. G4 needs at least two distinct external players; the log lists one (P01). S7 shows this as a Hold item.
3. G4 needs at least three production agents, a three-role routed chain, and an agent revised after a handoff; S5 shows two agents only. Not shown in this deck and not audited here.
4. Combat-balance question is open; a post-Alpha external test of a revised encounter is required between G2/G3 and G4 (FINAL_REQUIREMENTS s5). No change exists yet.
5. No budgeted live evaluation has been run; the "fuller live suite" Beta check depends on Saad's approval of any paid call.

## Contradictions

- `SCOPE_LOCK.md` (43e9ce1) says the external playtest is "still pending until Saad conducts it", while LOG.md s3 records the XGJT session on 2026-11-27 and the deck presents it. The lock's limitation row is stale (not edited by T33; report only).
- Spec s3 asks "disarming opponents" and "defeating scripted guards" as observations; the replay supports neither (tech-lead and T33-eval N6). The deck resolves it by quoting Saad's notes verbatim and adding a separate "Replay shows" box (decision #135). Residual tension: the spec's request wording and the shipped box differ.
- S3 says "48 trial rows" and "16 duels" together; 3 identical trials per duel, so the numbers are consistent but easy to misread.
- Local suite on S6 (2376 passed, 11 skipped, 5 xfailed) vs the T03 CI record (14 skipped, per the tech-lead). Skips depend on installed extras. The slide labels the first as "Local suite".
- Tech-lead report says Slide 7 Hold items are "candidates"; S7 phrases them as "Open now ... Resolve each before approval" (a statement, not a question to Saad).
- S5 shows 650 passed (T02 close) and S6 shows 2376 passed (today); both are labelled by commit or by "Local suite", consistent.

## Friction on record

Only what the tech-lead report records (path and date, no inference): `docs/final/orchestration/reports/T33-tech-lead.md` (2026-11-27): Keynote cannot open python-pptx's notes master, worked around with a notes-free copy; `tests/test_frontend.py::test_tracked_images_are_the_bundle_or_nothing` rejects tracked PNGs, so images are JPG; held-out ledger tests failed on a dirty tree. No other friction was checked by me.

## Playtest evidence

LOG.md s3 at 43e9ce1: one session, 2026-11-27 XGJT, type A1, external yes, consent option (b), notes publishable yes, 1 duel; telemetry file `docs/final/playtest/telemetry/2026-11-27/online/duel-XGJT-001-seed0.json`. The replay verdict (full, hash match) is the tech-lead's claim; I did not reproduce it.

## Tracker status

Not read in this audit (no tracker file was named in the brief). Not verified.

## Tests run

None. This is a documentation audit; I ran no test suite and made no paid call.

## Requested next action

QA (`gate/T33-qa`): reproduce the hash, play the clip in PowerPoint, time the narration, re-read both CI runs, check the S5 handoff quotes and the S3/S6 numbers against their sources. Orchestrator: decide whether to track the MP4 (or state it is local-only), whether to add a coverage checklist file to `presentation/`, and whether to record the stale scope-lock playtest row as a finding.

Commit to review: the commit on `audit/T33` that adds this file.
What changed: this report only.
How to check it: open `task/T33` at b64f58c and the rows above.
What I am unsure about: rows marked "not independently reproduced" rest on the tech-lead's report.
Touches the knowledge boundary or AI seat: no.

## Student decision required

none.
