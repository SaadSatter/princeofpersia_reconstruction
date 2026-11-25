# Shadow Masque — Final requirements and evidence checklist

**Status:** Working compliance checklist, 2026-11-23. Unchecked means not verified, not necessarily unimplemented.

## Instructions for Claude Code and Codex

Read this file before planning, implementing, reviewing or releasing. The student retains Executive Producer and Creative Director authority. Do not change approved scope, spend money on live model calls, publish a release, or claim a gate is passed without student approval. Course staff decide gates. QA may write tests and report findings but must not modify production game code. Preserve existing course tooling and instructions. Never fabricate evidence, playtests, consent, origin notes, dates, costs or agent transcripts.

Labels: **[R]** explicit course requirement; **[G1]** pitch commitment (subject to documented student-approved scope changes and gate decisions); **[+]** recommended safeguard, not a course mandate. Mark a checkbox complete only with a commit, PR, test output, trace, playtest entry, recording timestamp or other appropriate evidence. Use `PASS / PARTIAL / MISSING / BLOCKED / N/A` in audits; explain N/A. Do not equate a plan or replay with a successful live run. If sources conflict, the newer course announcement controls its stated changes; otherwise retain the original final brief. Check the Gate decisions issue and current course schedule before locking scope.

## 1. Design contract

- [ ] [G1] Competitive stealth-platformer: two rivals sneak, disguise, rig traps and duel; intended experience is paranoia and thrill of reveal. Not cooperative PvE; palace guards are scripted.
- [ ] [G1] Human vs human, human vs model-driven rival, AI vs AI (may become test-only). One authoritative seeded simulation, interchangeable controllers and separate partial observations.
- [ ] [G1] Original palace rooms (4–6 planned), movement/climbing, sword strike/block, stolen uniforms, scripted guards, floor/gate traps, suspicion feedback and split-screen. Guards and traps obey fixed rules and can harm either rival, including trap owner.
- [ ] [G1] Preserve duel and disguise. Approved cut order: rooms to three, suspicion meter, one trap type, AI vs AI to test-only. Online multiplayer, sound, levels 2–14 and model-driven guards are out of G1 scope.
- [ ] [G1] Rival observes own room, visible figures, own HUD and legal actions. Disguised rival appears as guard; enemy-rigged tiles appear normal. No hidden identities, remote positions, trap ownership or RNG leakage. Validate legal actions; refuse and count illegal actions without action-induced state changes.
- [ ] [G1] Model selects bounded macro-actions (blend, disguise, rig trap, wait, follow, strike, flee, climb) approximately every four seconds; deterministic controller handles frame-level fencing. Record any approved changes.
- [ ] [G1] Hypothesis: humans misidentify disguised model rivals more often than scripted rivals and rate tension higher (1–7). Competition, challenge/mastery and thrill are intended motivations; observe rematches, changed tactics and reveal reactions.
- [ ] [G1] Baseline: nearest uniform, shortest path toward target, adjacent strike; same view and actions. Document any strengthening of baseline before evaluation.
- [ ] [G1] Historical budget basis: Claude Haiku 4.5, 3 s mean decision (Oct 26 engine run), 5 s timeout then labeled fallback, ~$0.0023/call, ~$0.17 per five-minute human/AI duel and ~$0.34 AI/AI. Pitch requested up to $5 live spending before G2; request is not authorization. Re-measure on current build.
- [ ] [+] Keep model-driven rival available in release even if hypothesis fails; scripted default is acceptable as a design choice, but removing deployed AI risks violating final requirement. Avoid screen-peeking in human/AI evaluation; show human view only.

## 2. Repository, tracker and CI

- [ ] [R] Move game and gate artifacts into official private `columbia-university-ai-games/final-saadsatter` by Nov 28, 11:59 p.m.; preserve course template and close applicable old course-repository PR. Post repository link in discussion by same deadline.
- [ ] [R] README links game, gate documents, agent-team folder and tracker; include launch/replay instructions and asset attribution/rights. Preserve midterm graded record separately.
- [ ] [R] Graded version is last push to `main` before each recording deadline; no force pushes. Check Gate decisions issue and resolve Holds.
- [ ] [R] Tracker includes Tasks, Weekly PPP (progress/plans/problems) and Risk Register; Notion or equivalent GitHub Issues/Projects/Asana. Link tasks to tests and decisions. If Notion, student is sole member and staff are guests.
- [ ] [R] Deterministic CI on every PR; passing checks required to merge. Cover rule/state invariants, valid path/terminal outcome, invalid-action rejection and observed regression.
- [ ] [+] Audit all existing final branches, dependencies, commits and tests before merging; distinguish verified behavior from branch names. Preserve provenance; do not assume old Prince reconstruction README describes Shadow Masque.

## 3. G1 record and living documents

- [ ] [R] G1 pitch/deck and 3–5 minute recording: concept, core loop, references/attribution, systems diagram, six-dimension risk profile with mitigations, initial project plan, initial GDD/configuration, testable AI hypothesis, motivations, scripted baseline, playtest question and latency/cost budgets. G1 deadline Nov 15; preserve submitted record and feedback.
- [ ] [R] GDD specifies mechanics, dynamics, intended aesthetics, scoring, win conditions, edge cases and balance.
- [ ] [R] Configuration specifies affordances, tools, context, retrieval, evaluation and adversarial failures. Record model identifier/settings, configuration versions, timeout/retry/spending limits, fallback and world-state/agent-knowledge boundary.
- [ ] [R] GDD and configuration may be one living file. Add dated **Changes since the last gate** at top for G2/G3 and G4; do not rewrite history. G3 locks scope; G4 records release implementation.
- [ ] [R] At least one executable agent extension (skill, plugin, tool bundle, MCP server, function-calling interface or platform equivalent). Manifest: purpose/tools/prohibited actions; memory policy/named context sources; model/prompts; named failure modes/evaluation cases; logging/human override; test command/CI workflow path. Rival callable interface is a candidate, not automatically verified compliance.

## 4. Production agents (updated workload)

- [ ] [R] G1 plans team. Start with implementation and independent reviewer; tailor both to Shadow Masque by G2/G3.
- [ ] [R] Use course `python -m team init` as appropriate; inspect template before modifying. Maintain role sources and render generated files with `python -m team render`; validate with `python -m team validate`. Follow actual template instructions; do not hand-edit generated artifacts.
- [ ] [R] Coverage map: every development role one line, named agent / student / not needed with reason. Roles: producer, design, tech, art, narrative, QA, business intelligence, release. For agents record path, purpose, context, tools/write permissions, outputs, handoffs, evaluation and approval boundary.
- [ ] [R] G2/G3: two tailored starter agents and at least one routed handoff with student decision.
- [ ] [R] G4: at least three production agents; at least one added based on evidence; routed chain of three roles (two handoffs); at least one agent revised because a handoff exposed a weakness.
- [ ] [R] Add agent after friction occurs twice (repeated command/correction/slow step). Origin note links two real instances dated before first agent commit. Existing agents can count with retrospective note and predating evidence. Keep origin notes and handoffs as plain Markdown in `agent-team/handoffs/` per announcement/course tool conventions.
- [ ] [+] Suggested chain: Design Lead -> Tech Lead -> QA, only if evidence justifies Design Lead. Student can cover remaining roles. In-game rival is separate from production-agent count.
- [ ] [+] Handoff records date, sender/receiver, artifact/commit, acceptance criteria, findings, student decision and follow-up evidence. Revision records before/after configuration and triggering handoff.

## 5. Evaluation harness and playtests

- [ ] [R] Extend deterministic and repeated live-model evaluation suite. Run small live suite when models/prompts/tools/memory/permissions change and fuller suite before gates. Bound trials and spending; record model/config, outcomes, latency, cost and unavailable/failed runs. Replays are not current live evidence.
- [ ] [R] Human playtests assess experience; validate any model-grading rubric against human judgment.
- [ ] [+] Retain five-operation interface where useful: reset(seed), observe(player_id), legal_actions(player_id), step(player_id, action), outcome(). Exact midterm interface/trial counts are not restated as final mandates.
- [ ] [+] Predeclare scenarios, seeds, metrics, limits and baseline; freeze configs for final comparison. Suggested three repeated trials per condition per scenario: disguise/blending, traps, identification and held-out full duel. Use same observations/action affordances; baseline cannot target hidden rival position. Separate tuning and held-out runs.
- [ ] [+] Test leakage through observations, action masks, IDs, errors, logs and controller pathfinding; test symmetric traps, disguise/reveal, terminal outcome, timeout fallback, stale actions and replay determinism. Track illegal actions, timeouts, fallback frequency, token usage and cost.
- [ ] [+] Compare human vs scripted and human vs model in counterbalanced order, blind condition if practical. Define identification opportunity and misidentification in advance; distinguish false identification, missed rival and no encounter. Record tension 1–7, tactics, fairness, rematch/reveal reactions. Do not require model to win or hypothesis to be confirmed.
- [ ] [R] G2/G3: observe at least one external player using core loop.
- [ ] [R] Between G2/G3 and G4: external test of revised encounter; link finding to change.
- [ ] [R] G4: external release playtest after Alpha and before Gold recording; triage findings and verify fixes. At least two distinct players across G2–G4.
- [ ] [R] Final playtest log: hypotheses, consent, anonymous observations before interpretation, build/config versions, changes, verification and future recommendations.
- [ ] [R] Between G4 and G5: play three assigned classmates' builds and collect showcase feedback.

## 6. Gate checklist

### G2/G3 — Saturday Nov 28, 11:59 p.m.
- [ ] [R] Official repository migration, README/tracker links, scope lock and dated GDD/config update.
- [ ] [R] Two tailored production agents, coverage map, one routed handoff and student decision.
- [ ] [R] External core-loop playtest, deterministic CI and live evaluation evidence appropriate to gate.
- [ ] [G1] Demonstrate integrated competitive duel, disguise, scripted guards and model rival; document approved scope cuts and current limitations.
- [ ] [R] Push graded version to main; submit 3–5 minute recording and discussion repository link. Check Gate decisions issue.
- [ ] [R] Three Braintrust replies by Monday Nov 30, 11:59 p.m.

### G4 — Saturday Dec 5
- [ ] [R] End-to-end playable game, deployed in-game AI, deterministic fallback, CI evidence, replay instructions and archived runnable release.
- [ ] [R] Final dated GDD/config update, executable extension and complete manifest.
- [ ] [R] Three production agents, evidence-backed origin note, three-role chain/two handoffs, handoff-driven revision and student decisions.
- [ ] [R] Fuller live suite, revised encounter playtest, post-Alpha release playtest, triage and verified fixes; two distinct external players across gates.
- [ ] [R] Push graded version to main before recording deadline; 3–5 minute recording; three Braintrust replies before class. Confirm exact deadline time in course schedule.

### G5 / Finals
- [ ] [R] Three assigned peer playtests and showcase feedback; G5 peer review of draft AAR/showcase evidence, no additional G5 recording.
- [ ] [R] AAR: Process; Production; Team & Communication; Tech & Tools; Playtesting & QA; Top Three lessons. First five explain what went right/wrong/learned. Account for whole agent team and retained student decisions.
- [ ] [R] Retrospective answers six questions: intent/outcome; causes (design and in-game AI); production team/student decisions and boundary slips; failure/mitigation; research (at least two sources used in argument); transfer to next game/beyond.
- [ ] [R] Open retrospective with six-line index pointing to answers; link each claim to commit, trace, playtest entry or recording moment. Appendix: `git shortlog`, `gh pr list --author`, human/agent authorship where recorded, tracker task export linked to tests/decisions.
- [ ] [R] Finals signup by Dec 14; speaking order Dec 15; live presentation Dec 18, 21 or 22 (7:10–10 p.m. Zoom), about four minutes plus two minutes questions; stay for whole evening.
- [ ] [R] Submit retrospective and separate 8–10 minute recorded walkthrough by Wednesday Dec 23, 11:59 p.m.; incorporate showcase and Finals feedback.

## 7. Required agent reporting format

For each work session report: requirement IDs/section, current status, changed files and commits, tests actually executed and results, evidence links, unresolved risks, scope/budget implications, and decisions needed from student. Independent QA should distinguish reproducible failures from unverified concerns. Never mark a requirement complete solely because a file exists.

## Source register

- Original course Final brief, supplied as `Pasted markdown.md`, sections Final and Presentations/participation/feedback.
- Updated course final workload announcement supplied in prior conversation: simplified production-agent progression, origin notes, handoffs, living documents, official repo and tracker. This checklist reflects the announcement details available in conversation; verify against the actual announcement and gate decisions before treating it as definitive.
- `Shadow Masque — G1 Pitch.pdf`, slides 1–8, design/scope/hypothesis/budgets/attribution.
- Course template `team/README.md`, `AGENTS.md`, CI workflow: inspect current official repository for authoritative tool behavior.
