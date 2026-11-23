# AUDIT-D report (requirements auditor, temporary), 2026-11-23

Condensed by the orchestrator from the subagent's final message (matrix and findings kept; some rows merged). Side effect disclosed and undone: `team/__pycache__` in /home/claude/final-saadsatter, deleted.

Tests: 419 passed, 12 skipped at 13c7488 (python3 -m pytest). Session 13 record reports 443 passed, 1 skipped with uv (gap likely pygame-only tests; not verified).

## Compliance matrix
| § | Requirement | Label | Status | Evidence | Gap |
|---|---|---|---|---|---|
| 1 | Competitive stealth-platformer, scripted guards | G1 | PARTIAL | pop/versus.py, pop/guards.py, tests | Rival traps; deployable 2-player build |
| 1 | HvH, HvAI, AIvAI; one sim; separate obs | G1 | PARTIAL | VersusEpisode; determinism test | HvH local bench only; no versus AI controller |
| 1 | Rooms, movement, sword, uniforms, guards, traps, suspicion, split screen | G1 | PARTIAL | 6 rooms; R-V01–R-V21 | Traps; split screen replaced by online (dbb66ff, 2026-11-16), not built |
| 1 | Keep duel/disguise; cut order; online/sound/AI guards out | G1 | PARTIAL | duel, disguise kept | Online moved in (dated decision); extra moves 2026-11-17; no Changes section |
| 1 | Knowledge boundary; illegal refused | G1 | PARTIAL | test_disguise, test_versus, test_flip_review | Traps, server message; flip fixes not re-reviewed |
| 1 | Macro-actions ~4 s; controller | G1 | MISSING | — | CQ-1 open; CONFIG A1 vs VERSUS_SPEC §7 contradict |
| 1 | Hypothesis | G1 | MISSING (evidence) | GDD §2, CONFIG A7 | No protocol/runs |
| 1 | Baseline | G1 | MISSING | CONFIG A6 "Planned" | Versus baseline |
| 1 | Budget basis; $5 is a request | G1 | BLOCKED | CONFIG A4; traces/live/20261026T180142Z | No recorded authorisation; re-measure needs Saad |
| 1 | Keep model rival; no screen-peeking | + | PARTIAL | Online decision | Local bench shows both panels |
| 2 | Migrate to official repo by Nov 28; post link | R | MISSING | template only | All; old course PR #57 state unverified |
| 2 | README links | R | MISSING | dev README is midterm | Rewrite |
| 2 | Graded = last push to main | R | MISSING | dev main = midterm | Gate decisions issue not accessible |
| 2 | Tracker: Tasks, PPP, Risk | R | MISSING | PROJECT_PLAN says "moves into Asana" | No link, no PPP |
| 2 | Deterministic CI every PR, required | R | PARTIAL | dev ci.yml | Protection unverifiable; official placeholder |
| 3 | G1 record | R | PARTIAL | docs/final/README.md links | G1 decision and feedback not recorded |
| 3 | GDD content | R | PARTIAL | GDD §4, §5.3, §9; VERSUS_SPEC | Stale [Planned] labels; no trap rules; OQ-3, OQ-6 |
| 3 | Configuration content | R | PARTIAL | CONFIG A1–A9 | No retrieval, no version history; fallback contradicts spec; B1 omits Codex reviewer, session-evidence |
| 3 | Dated Changes since last gate | R | MISSING | both "Initial (G1), 2026-11-15" | Add |
| 3 | Executable extension + manifest | R | PARTIAL | game-rules-audit, session-evidence skills | No consolidated manifest (CQ-7); tools/evidence untested |
| 4 | Tailor implementer + reviewer | R | PARTIAL | CLAUDE.md, rules-reviewer.md (43c5520, b58cdd0) | Not in course format |
| 4 | team init/render/validate | R | MISSING | no agent-team/ anywhere | Run in official repo |
| 4 | Coverage map | R | PARTIAL | CONFIG B2 prose | Not other-roles.md/coverage-map.md |
| 4 | G2/G3 2 agents + handoff + decision | R | PARTIAL | flip review cycle | Not in agent-team/handoffs; decision not in Saad's words |
| 4 | G4 items; friction-based agent | R | MISSING | candidate friction below | Saad picks role |
| 5 | Extend deterministic + live suites | R | PARTIAL | versus deterministic tests | No versus live suite; last live 2026-10-26 single-player |
| 5 | Human playtests | R | MISSING | Saad's own play only (2026-11-17) | External testers |
| 5 | Five-op interface | + | PASS | pop/versus.py:949-1017; test_versus.py | Per-seat runner limits |
| 5 | Predeclared scenarios; leak tests; counterbalanced comparison | + | MISSING/PARTIAL/MISSING | — | — |
| 5 | G2/G3 external player | R | MISSING | — | — |
| 5 | Playtest log | R | BLOCKED | CQ-6 | Format, consent |
| 6 | G2/G3 rows | R/G1 | MISSING or PARTIAL | — | see blockers |
| 6 | G4, G5 rows | R | MISSING (not yet due) | — | — |

## Documentation
GDD covers mechanics, dynamics/aesthetics, win/edge cases, balance (untested); scoring only win/draw/loss. CONFIGURATION covers affordances, context/boundary, model, limits (5 s timeout, 0 retries, ≤100 calls, ≤$0.25/seat, $5), fallback, evaluation, logging/override; not retrieval or config versions. No dated Changes sections.

## Agents and handoffs
Exists: CLAUDE.md/AGENTS.md, .claude/agents/rules-reviewer.md, .codex/agents/pop-rule-reviewer.toml, two skills, AGENT-TEAM.md (still midterm text, says no review run yet — false). No agent-team/. Strongest handoff candidate: flip cycle (audit + review 2026-11-18 -> Saad decisions 2026-11-23 quoted in S13 -> fixes 13c7488); Saad must write the decision; fixes need independent re-review.

## Friction on record (paths and dates; conversation logs are gitignored, not available)
First agent commits: rules-reviewer and game-rules-audit 8295fc0 (2026-10-26); session-evidence and Codex reviewer 43c5520 (2026-11-16).
- Design: dfc8ade (2026-11-17) TAKE over a downed guard did nothing; 05fe136 (2026-11-17) flip re-specified; S13 (2026-11-23) three rule questions; S06 (2026-10-26) request conflicted with CLAUDE.md.
- Art: S12 2026-11-17 (gate look corrected twice, sprite size, black-box bug); fbcff5b retries; 3784127 wrong lunge pose; fa086fe missing guard clips.
- Evaluation/live: S04 2026-10-26 40/40 calls failed (empty key); S09 live episode did not run; S03 pricing re-verify.
- Release/provenance: c3aa550, bb89412, 0e5df5f (2026-10-26) three "(student instruction)" provenance corrections; S05–S07 course boundary check failed each time.

## Tracker, playtests, README
No tracker (Asana planned); Risk Register in PROJECT_PLAN (7 risks); no PPP. No external playtest, consent text or log format; silent-playtester notes not in repo. README is midterm; versus replay not implemented.

## Contradictions
1 AI seat design: CONFIG A1/A5 macro-actions + baseline fallback vs VERSUS_SPEC §2.1/§7 (approved) raw inputs + WAIT fallback; checklist says CQ-1 open. 2 OQ-7 approved in VERSUS_SPEC but open in GDD and checklist. 3 Gate dates Mon 30 Nov / Mon 7 Dec vs Sat 28 Nov / Sat 5 Dec. 4 Online out in pitch, in in GDD §8, no Changes section. 5 GDD [Planned] labels and "numbers open" vs approved spec. 6 Stale headers in EVIDENCE_INDEX and checklist. 7 ENGINE_DECISION "pending" vs CLAUDE.md decided. 8 Checklist flip "done" vs S13 not re-reviewed.

## G2/G3 blockers (priority)
1 Official repo import + collisions + final.yml test step. 2 team init, tailor tech/qa, other-roles, flip handoff (Saad writes decision). 3 AI rival seat (needs CQ-1). 4 One trap type. 5 Two-machine play or approved fallback (OQ-10, OQ-11). 6 Live smoke run (approval). 7 External playtest (CQ-6). 8 Changes sections, scope lock, tracker. 9 Push, recording, link.

## G4 blockers
Third agent + origin note; 3-role chain + revision; manifest; fuller live suite with frozen scenarios; two playtests with ≥2 external players; archived release with versus replay; final GDD/Config.

## Scope reductions
One trap type; AI vs AI test-only; localhost/LAN hosting; freeze moves; ~6 macros (WAIT, FOLLOW, STRIKE, FLEE, DISGUISE, BLEND); keep 6 rooms and suspicion; if online slips, human-vs-AI demo with only human panel (Saad decision).

## Decisions for Saad
CQ-1 + fallback; scope cuts; OQ-3, OQ-6, OQ-10, OQ-11, OQ-13, CQ-6, CQ-7, confirm OQ-7; budget authorisation; merges and history import; flip handoff; third agent role; ENGINE_DECISION and online acknowledgement; commit S13 files.

Limitations: GitHub PR state, Gate decisions issue, branch protection, Braintrust posts, recording, conversation logs not checked.
