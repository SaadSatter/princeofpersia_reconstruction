# Requirements Checklist

Maps every rubric check in `docs/MIDTERM_GUIDELINES.md` to deliverables,
tests, and evidence. Status values: **done** (evidence exists and is
linked), **partial**, **todo**, **at risk** (todo and likely to slip).
Only mark **done** with a link to evidence. Updated: 2026-10-26 (engine + interface). "Passing locally" is not CI evidence; CI is not set up yet.

## Rubric checks

| Check | Requirement (short) | Deliverable | Test / verification | Evidence location | Status |
| --- | --- | --- | --- | --- | --- |
| 1a | Every rule labeled code/manual/observed/assumed/design with locators | `docs/RULE_SOURCE_MAP.md`, copied/summarized into README | Reviewer check 1; audit F1–F2 | `docs/RULE_SOURCE_MAP.md` | partial — map drafted; no `manual`/`observed` evidence yet; impl column empty |
| 1b | Scope and exclusions explicit; adaptations explained | `docs/GAME_SPEC.md` §1, §10; README scope | Reviewer; playtest finds no unexplained change | `docs/GAME_SPEC.md` | partial — scope approved (Level 1 mechanics, authored rooms); README scope statement todo |
| 1c | Sources credited; reuse terms checked and stated | README "Sources and terms"; `CLAUDE.md` source-use rules | Reviewer; instructor ruling on level data | `CLAUDE.md`, `docs/GAME_SPEC.md` §9 | partial — decision: no original data/assets committed; README terms section todo |
| 2a | Complete core loop to a clear ending, no crash/dead end | Engine + `play.py`; S3 escape completable | `tests/test_situations.py::test_scripted_route_wins_within_limits` (all 6 situations) | `traces/dev/S3-scripted-route-100.jsonl` | partial — engine episode wins; Pygame frontend and human playthrough todo |
| 2b | Model player picks and submits actions via interface; no repo tools/hidden state; fallbacks labeled | `agents/model_player.py`, `pop/runner.py` | `tests/test_model_player.py` (fake provider); audit B5, D3 | `traces/*.jsonl` | todo |
| 2c | Observation per role; legal list leaks nothing; leakage test | `pop/observation.py`, `pop/interface.py` | `tests/test_leakage.py` (8 tests) | audit reports | partial — tests pass locally; no audit yet |
| 3a | Fresh clone runs setup/play/eval from README in project folder | README commands; `pyproject.toml`, `uv.lock` | Fresh-clone dry run recorded in EVALUATION.md | EVALUATION.md | todo |
| 3b | Runner owns state; step, call, timeout limits; terminal reasons | `pop/runner.py`, `pop/interface.py` | `tests/test_runner.py`, `tests/test_interface.py` | traces show `reason` | partial — enforced and tested with fake players; no live model yet |
| 3c | CI: invariants, legal/illegal, terminal outcome, observed regression, limits; green | `ci/midterm-saadsatter.yml` → course `.github/workflows/midterm-saadsatter.yml` | the five test groups below | course PR checks tab | todo — course workflow must run in course repo |
| 3d | Implementation agent, reusable skill, independent review, each with artifact + session link | `CLAUDE.md`, `.claude/skills/game-rules-audit/SKILL.md`, `.claude/agents/rules-reviewer.md`, `review.md`, `docs/audits/` | Skill invoked in 2 separate sessions; reviewer run in a session that did not build | AGENT-TEAM.md links | partial — configs exist; no sessions run yet |
| 4a | Choices named with the alternative they beat | GAME_SPEC §9–10, RULE_SOURCE_MAP design rows, README "Design choices" | Reviewer check 1 | `docs/RULE_SOURCE_MAP.md` R-D01..R-D12 | partial |
| 4b | Credible baseline; suite can separate players; result interpreted | `agents/baseline.py`; suite in `docs/EVALUATION_SUITE.md` | Baseline completes ≥1 situation; results table | EVALUATION.md | todo |
| 5a | Suite declared before tuning; held-out cases; same cases; outcomes, invalid actions, limits, latency, tokens, dated cost; failures | `EVALUATION.md`, `evaluate.py`, `traces/` | `evaluate.py` writes all fields; suite commit precedes first prompt-tuning commit | git history + EVALUATION.md | partial — suite declared in `docs/EVALUATION_SUITE.md` (freeze commit = first commit); results todo |
| 5b | Agent-team log and limitations in student's voice; decisions named; peer notes used | `AGENT-TEAM.md` (student-authored), EVALUATION.md limitations | Student writes; not the agent | AGENT-TEAM.md | todo — student-owned |
| 5c | 3–5 min recording, agent playing without manual moves, limits stated | Recording link in README and PR | — | README | todo — student-owned |

## CI test groups required by 3c

| Group | Planned tests | Status |
| --- | --- | --- |
| Rule invariants | `tests/test_rules.py` (32 tests) | passing locally |
| Legal / illegal actions | `tests/test_interface.py` | passing locally |
| Terminal outcome | `tests/test_situations.py`, `test_interface.py::test_death_is_terminal_with_reason`, `test_rules.py::test_clock_runs_out` | passing locally |
| Observed regression | `tests/test_regressions.py::test_regression_fall_death_reported_full_hp` | passing locally |
| Episode limits | `tests/test_runner.py`, `tests/test_interface.py` (`step_limit`, `call_limit`, timeouts, `invalid_limit`) | passing locally |
| (extra) Determinism | `tests/test_determinism.py` | passing locally |
| (extra) Leakage | `tests/test_leakage.py` | passing locally |
| (extra) Architecture | `tests/test_architecture.py` | passing locally |

## Checkpoint — Session 7, October 26

| Item | Status |
| --- | --- |
| Engine runs behind the five operations | done locally — `pop/interface.py`, 83 tests |
| Baseline completes an episode | todo |
| Model player completes ≥1 live episode with a trace | todo |
| First comparison table | todo |
| CI green on deterministic checks | todo |

## Submission — November 7, 11:59 p.m.

| Item | Location | Status |
| --- | --- | --- |
| Project in `game-dev-f26/midterms/saadsatter/` | course repo branch `saadsatter/midterm` | todo |
| Only that folder + `.github/workflows/midterm-saadsatter.yml` changed | PR diff | todo |
| README.md (scope, setup/play/test/eval commands with working dir, rule map, sources/terms, recording link) | `README.md` | todo |
| EVALUATION.md (suite, table, traces, CI evidence, limitations) | `EVALUATION.md` | todo |
| AGENT-TEAM.md (student-authored one-page log) | `AGENT-TEAM.md` | template only |
| review.md (independent review findings) | `review.md` | todo |
| Peer playtest notes, received and given | `docs/peer-notes/` or linked | todo — partner notes due Nov 6 |
| 3–5 min recording linked from README and PR | README + PR | todo |
| PR description: login, title, links to README, EVALUATION, AGENT-TEAM, peer notes, recording | PR | todo |
| PR URL submitted on CourseWorks | CourseWorks | todo |
| No secrets, playtester personal data, caches, or large generated files | repo | todo — `.gitignore` in place |
