---
handoff_id: HO-AUDIT-G23-requirements-auditor
task_id: AUDIT-G23
date: 2026-11-26
from: requirements-auditor
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/AUDIT-G23.md@4120a54
source_branch: audit/AUDIT-G23
source_commit: 4120a54 (the base; a report-only task, per the template)
reviewed_commit: n/a
verdict: n/a
---

# AUDIT-G23: requirements-auditor report (G2/G3 readiness, due Sat 2026-11-28, 11:59 p.m.)

Status: done

## Work completed

Read-only audit of `main` (4120a54) plus `orch/reviewed` dfe2d90 (PR #12, open, unmerged) against `inputs/FINAL_REQUIREMENTS.md` section 6 "G2/G3" and the [R] lines of sections 2 to 5, with `COURSE_ROLE_MAP.md`. The official repository (`columbia-university-ai-games/final-saadsatter`) was read with `gh api` (signed in, read only). I ran the suite on `main` once (result below). No paid call, no training, nothing pushed to the course repository.

**Requirement sources used.** "FR" = `inputs/FINAL_REQUIREMENTS.md` (Saad's checklist, 2026-11-23, which folds in the reduced production-agent announcement). "TR" = official repo `team/README.md` and `.github/workflows/final.yml` as read 2026-11-26. "AG" = `AGENTS.md`. I did not have the original course announcement text, so FR is trusted for what the course says.

## Bottom line

Nothing in section 6 is fully done. The gameplay and evaluation side is far ahead of the course-facing side. Five things stand between today and a compliant Saturday, and only one of them is an agent job.

1. **CI on `main` is red** since the PR #11 merge (a93d36a, 2026-11-26 03:19Z). One test needs `websockets`, and `ci.yml` does not install the `online` extra. PR #12's own CI run is also red. Agent task, about 10 minutes.
2. **The official repository is an untouched template** (one commit, "Initial commit", placeholder README, no `agent-team/`). T03 has not started. Saad's layout decision comes first, then an agent can do the work.
3. **No external playtest exists.** `docs/final/playtest/LOG.md` is empty by design, the protocol, hypotheses and consent sentence are unapproved drafts, and no player code is recorded. Saad only.
4. **The G2/G3 handoff has no Student decision.** Saad only.
5. **The dated "Changes since the last gate" is not on `main`.** It exists only on `orch/T10a` (PR #6, open) and is stale against decisions #31 to #102.

## Compliance matrix

Status key as in the procedure. "main" means 4120a54. "PR #12" means `orch/reviewed` dfe2d90, not on `main` until Saad merges.

### Section 6, G2/G3 (all six lines, split into sub-rows)

| Section | Requirement (short) | Label | Status | Evidence | Gap |
| --- | --- | --- | --- | --- | --- |
| 6 G2/G3 line 1 | Move game and gate artifacts into official private repo by Nov 28 11:59 p.m. | [R] | **MISSING** | `gh api .../final-saadsatter/contents`: root has `.github`, `.gitignore`, `AGENTS.md`, `CLAUDE.md`, `README.md`, `team/`, `tests/` only. `gh api .../commits`: one commit, "Initial commit". `docs/final/orchestration/STATUS.md` table: T03 "not started" | T03 (plan below). Saad must pick the layout first |
| 6 line 1 | Preserve course template | [R] | **PASS (as found)** | Official repo is the unmodified template. Nothing of ours is in it, so nothing can have broken it yet | Must stay true during T03 (see risks) |
| 6 line 1 | Close applicable old course-repository PR | [R] | **BLOCKED** (needs Saad) | `gh pr list -R columbia-university-ai-games/game-dev-f26 --author SaadSatter`: #57 (Prince of Persia midterm draft) CLOSED 2026-10-29; #92 ("Oath and Ember", a different project, branch `saadsatter/midterm-oath-and-ember`) OPEN, not draft; #7 merged | Which PR is "applicable" is unclear. #92 is a different game's midterm. Do not close it without Saad, and he may want to ask staff. May be N/A for Shadow Masque |
| 6 line 1 | Post repository link in the discussion by Nov 28 | [R] | **MISSING** (not verified) | I could not see course discussions from here. Official repo issue #1 "Gate decisions": 0 comments on 2026-11-26 | Saad only |
| 6 line 1 | README links game, gate documents, agent-team folder, tracker; launch/replay instructions; asset attribution/rights | [R] | **MISSING** | Official README is the placeholder. Our root `README.md` on main is still the midterm README ("Prince of Persia mechanics reconstruction", Week 7 audit quickstart). `docs/final/README.md` is headed "G1 Concept" and links only G1 items | New root README for the official repo, filled in the template's three placeholders (game folder, gate documents, tracker). T03 |
| 6 line 1 | Tracker (Tasks, Weekly PPP, Risk Register) | [R] | **MISSING** | `docs/final/TRACKER.md` does not exist on main or dfe2d90 (`git ls-tree`). Decision #10 (2026-11-23): "Keep everything in the current repo for now." Initial Risk Register exists in `PROJECT_PLAN.md`. `STATUS.md` has a task table, which is not the Weekly PPP | Saad picks the tool (decision #10 predates the move). Then an agent builds it. T10b item |
| 6 line 1 | Scope lock | [R] | **MISSING** | `PROJECT_PLAN.md:50` plans "Scope-lock plan ... Fri 27 Nov"; no such document exists. Cut order is in GDD section 8 (`docs/final/GDD.md:134-138`). The GDD section 8 table says "Included by G2/G3 ... online play ... 3 modes" and lists a five-step cut order | A short scope-lock document (what stays, what is cut, limits). Saad approves. Agent can draft |
| 6 line 1 | Dated GDD/config "Changes since the last gate" | [R] | **PARTIAL** | Not on main: `grep "Changes since" docs/final/GDD.md` returns nothing on main. It exists on `orch/T10a` a1b9738 (PR #6, open, 11 files, QA ACCEPT WITH NOTES x3): GDD:9 and CONFIGURATION:8, dated 2026-11-24, covering decisions #1 to #30 | PR #6 is stale (see Contradictions 5). Needs a refresh through decision #102 and the facts after 11-24, then a merge. T10a-refresh (agent) then Saad merges |
| 6 line 2 | Two tailored production agents (tech, qa) | [R] | **MISSING** | No `agent-team/` anywhere (main, dfe2d90, official repo). The native `tech-lead` and `qa` exist (`.claude/agents/`) and are mapped in `COURSE_ROLE_MAP.md`, but that file says they count only "once `agent-team/roles/tech.md` exists and is tailored" | `python -m team init`, tailor `roles/tech.md` and `roles/qa.md`, `render`. T03 |
| 6 line 2 | Coverage map: every role one line | [R] | **MISSING** | `COURSE_ROLE_MAP.md` "G2/G3" table: "Not started. Every line is Saad's call". Template `other-roles.md` lists the six others | Saad writes one line each for producer, design, art, narrative, bi, release. Agent only pastes |
| 6 line 2 | One routed handoff with a student decision | [R] | **PARTIAL / BLOCKED** | Draft `docs/final/orchestration/handoff-drafts/2026-11-24-qa-to-tech.md` (frontmatter `from: qa, to: tech, column: prototype`, headings match the template's `handoff-template.md`; `prototype` is a valid `columns.json` id). Its sources exist on main: `docs/reviews/INDEPENDENT-REVIEW-r-v23-and-f1-2026-11-24.md`, `tests/test_qa_t02_disguise_tells.py`, `tests/test_qa_t02_r_v23.py`. Saad chose it, decision #7 "Yes let this be my tech handoff". The draft's own header says "Student decision empty, for Saad" | Saad writes the Student decision himself. Copy to `agent-team/handoffs/` happens after `init`. `validate` has not been run on this file (no `agent-team/` yet), so format acceptance is unverified |
| 6 line 3 | External core-loop playtest | [R] | **MISSING** | `docs/final/playtest/LOG.md` on main: sections 1 to 9 are blank templates, status line "No session has been run"; section 1 "Commit that froze them: ______". Kit is `status: draft kit (T11)`, "Approved by Saad: not yet" (LOG section 10). `STATUS.md` "Waiting on Saad": the CONSENT "What is recorded" sentence is unapproved (T20). Saad's own playtests (decisions #93 to #98, 2026-11-25) are the owner playing, not an external player | Saad approves PROTOCOL, hypotheses and consent; one external player plays Session A; observer is Saad or a helper, never an agent. See checklist |
| 6 line 3 | Deterministic CI | [R] | **PARTIAL** | Workflow: `.github/workflows/ci.yml` (pytest on 3.11 and 3.12, `uv sync --frozen --extra train`). Run history `main`: last success d35fe93 (2026-11-25 19:31Z); every push since a93d36a failed (24 runs through 4120a54, which was still running). Log of run 45762288977: `FAILED tests/test_online_boundary.py::test_hello_goes_to_its_own_client_and_error_messages_are_fixed_text - ModuleNotFoundError: No module named 'websockets'`, `1 failed, 1754 passed, 34 skipped, 3 xfailed`. PR #12 head dfe2d90: Deterministic checks run 45764999518 = failure; Web smoke (Playwright) run 45764999546 = success. I reproduced locally on main: `uv run --extra train pytest -q -p no:cacheprovider` gives `1 failed, 1756 passed, 32 skipped, 3 xfailed, 2 warnings in 128.08s` (the same single test). Branch protection ("passing checks required to merge") not verified | Add `--extra online` to both steps in `ci.yml` (the `online` extra and its lock entry exist: `pyproject.toml:12`, commit 198e731), or make that test skip when `websockets` is absent like the other online tests (`importorskip`, which is an existing-test edit and needs Saad). Also the rubric needs CI in the official repo (T03) |
| 6 line 3 | CI covers invariants, valid path/terminal outcome, invalid-action rejection, observed regression | [R] | **PASS (content), CI red** | Tests exist on main, e.g. `tests/test_versus.py::test_refused_input_changes_nothing_and_is_counted` (cited in `REQUIREMENTS_CHECKLIST.md`), `tests/test_determinism.py`, `tests/test_architecture.py`; the 1756 passing tests ran here. Whether each rubric category maps to named tests was not re-audited line by line | Fix the red check first |
| 6 line 3 | Live evaluation evidence appropriate to gate | [R] | **PARTIAL (judgment call)** | In-game rival is a PPO policy (decision #3), so no paid model call exists and none is needed (#8: under $1, smoke only; "No paid run has been made" per GDD changes table on PR #6). Run evidence on main: T07-run1, `tools/rl/runs/run-1/`, weights SHA-256 `80e4a110...ba4c`, 128-duel check 120 W / 8 D / 0 L (tuning set, not held-out). T09 held-out H6: `docs/final/evaluation/RESULTS-T09.md`: **NOT SUPPORTED**, 13 W / 2 D / 1 L of 16 against a pre-registered bar of 14; 0 aborted; the three trials per cell were identical, so effective n is 16 cells (nearer 8 starts). Both are real runs, not replays | Whether "repeated live-model evaluation" is met by a trained-policy run is for Saad and staff. Not shown here: a small re-run on the current build (T22 to T25 changed modes and the kneel rule after T09's code, 0ea8d73). Report T09 honestly, with its limits, in the recording. Do not call it a success |
| 6 line 4 | Demonstrate integrated duel, disguise, scripted guards and model rival; document scope cuts and limitations | [G1] | **PARTIAL** | Engine pieces are on main: `pop/versus.py`, `pop/guards.py`, tests `test_swordplay.py`, `test_disguise.py`, `test_guards.py`; PPO rival, runner, macros, web build, online server are on main via PR #11 (a93d36a). **Not on main:** the three-mode menu and online one-click AI match (T22, `agents/modes.py`, `docs/final/GAME_MODES.md`), kneel-takes-uniform (T24), T25 polish. `git merge-base --is-ancestor 083546e 4120a54` and `... 6efecbe 4120a54` both false. These arrive only with PR #12 | Saad merges PR #12 (after CI is fixed) so the graded main has the demo. Limitations document: the GDD "Changes" section on PR #6 says "Nothing in this project has been playtested", which is still true, but its other lines are stale |
| 6 line 4 | Hosted build live (class guidance, decisions #12, #13: "G2/G3, Sat Nov 28") | [+] (Saad's decision, not an [R] line) | **BLOCKED** | `pages.yml` deploy fails: run 45762288967 "Failed to create deployment (status: 404) ... Ensure GitHub Pages has been enabled". `WEB_BUILD.md` states no live URL. A browser run does exist in CI (Web smoke, Playwright, success on dfe2d90). T13 two-machine playtest and a real-hosting browser run are "not yet verified" in `STATUS.md` | Saad enables Pages (settings) on whichever repo hosts it, or records a decision to demo locally. Note the official repo is private |
| 6 line 5 | Push graded version to main; no force push | [R] | **MISSING** (not yet possible) | Graded version is the last push to `main` before the recording deadline. `main` has no force pushes on record in what I read; not verified exhaustively | After T03, the official repo's `main`. Saad only for merges |
| 6 line 5 | 3 to 5 minute recording | [R] | **MISSING** (Saad only) | No recording is referenced for G2/G3. Videos are never committed (`docs/final/README.md`) | Saad. Script from `docs/final/orchestration/` can be drafted by an agent |
| 6 line 5 | Discussion repository link; check Gate decisions issue | [R] | **PARTIAL** | Issue #1 "Gate decisions" (opened 2026-11-21): 0 comments on 2026-11-26. The G1 decision is not recorded there ("from G2/G3 on"). No Hold to resolve as of today | Re-check on Sat before submitting |
| 6 line 6 | Three Braintrust replies by Mon Nov 30 11:59 p.m. | [R] | **MISSING** (not verified, Saad only) | No record in the repository. `REQUIREMENTS_CHECKLIST.md` row is `not started` | Saad |

### Sections 2 to 5, [R] lines that G2/G3 depends on

| Section | Requirement (short) | Label | Status | Evidence | Gap |
| --- | --- | --- | --- | --- | --- |
| 2 | Preserve midterm graded record separately | [R] | **PARTIAL** | Midterm docs stay in `docs/`; `docs/MIDTERM_GUIDELINES.md` untouched; midterm tag/branch history on `final/*` and course branch `saadsatter/midterm` (PR #57 closed). I did not open the course branch | State in the new README where the midterm record lives |
| 2 | Graded version = last push to main; no force pushes; Holds resolved | [R] | **PARTIAL** | See line 5 above | |
| 2 | Tracker linked to tasks, tests and decisions | [R] | **MISSING** | See tracker row. Cross-links exist in `REVIEW_LOG.md` and `STATUS.md` (task, report sha, test result lines) but not in a tracker | Export from `STATUS.md` and `REVIEW_LOG.md` into the tracker |
| 2 | Deterministic CI, required to merge | [R] | **PARTIAL** | See CI row | Also confirm branch protection after T03 |
| 3 | G1 record preserved (pitch, recording) | [R] | **PASS (linked)** | `docs/final/README.md` links the G1 recording and deck (Google Drive, Slides). I did not open the links; the course staff feedback is not in the repository | Open the links once before the README move |
| 3 | GDD (mechanics, dynamics, aesthetics, scoring, win, edge cases, balance) | [R] | **PARTIAL** | `docs/final/GDD.md` exists (G1 text, section 9 "Balance (initial, untested)", numbers "[Open]") | Balance is untested by players. State that |
| 3 | Configuration (model id, versions, timeouts, spending limits, fallback, boundary) | [R] | **PARTIAL** | `docs/final/CONFIGURATION.md` on main is the G1 text (Claude Haiku 4.5). The PPO decision is only in PR #6. `agent-config.json` on main is dated 2026-11-24 and its `status_note` says the rival code is "not on main yet" and "No trained weights exist yet" (false now) | Refresh; same task as GDD |
| 3 | Dated "Changes since the last gate" at G2/G3 | [R] | **PARTIAL** | See line 1. Dated 2026-11-24 only | |
| 3 | One executable agent extension with manifest | [R] (G4) | **PARTIAL** | `agent-config.json` (course-1 schema) on main with purpose, tools, prohibited actions, memory policy; refreshed content is in the dfe2d90 diff. QA of its completeness is not in this audit's scope for G2/G3 | G4 item |
| 4 | Start with implementation and independent reviewer | [R] | **PARTIAL** | Native `tech-lead`, `qa`, `rules-reviewer` in `.claude/agents/`; chains logged in `REVIEW_LOG.md` (orchestrator-verified models claude-sonnet-5-5) | Not in course form until T03 |
| 4 | `python -m team init/render/validate`, no hand-edited generated files | [R] | **MISSING** | `python -m team` has not been run here. In the official repo `team/` exists and the CI step runs `validate` and `render --today from-team-json` | T03 |
| 4 | Add agent after friction twice; origin note links two dated instances | [R] (G4) | **N/A for G2/G3** | G2/G3 needs only the two starters. Friction pointers on record are under "Friction on record" below | G4 |
| 5 | Extend deterministic and live evaluation suite; bound and record | [R] | **PARTIAL** | `evaluation/`, `tools/eval/`, `docs/final/evaluation/PROTOCOL.md`; scenarios D1, B2, I3, F5, H6 (decision #9); ledger and results above | See live-evaluation row. B2 "low suspicion" number and D1 "on screen" still wait on Saad (`STATUS.md`) |
| 5 | Human playtests; validate any model-grading rubric against human judgment | [R] | **MISSING** | No human session recorded. No model-graded rubric is in use for the PPO rival | |
| 5 | External player observed using the core loop (G2/G3) | [R] | **MISSING** | Playtest row above | |

## G2/G3 blockers, who closes each, and the order

"Agent" means a task under a committed brief, Saad approving where `CLAUDE.md` says so.

| # | Gap | Who | Smallest concrete step | Depends on |
| --- | --- | --- | --- | --- |
| B1 | CI red on main and PR #12 | Agent (tech-lead, then QA) | Edit `.github/workflows/ci.yml`: `uv sync --frozen --extra train --extra online` and `uv run --frozen --extra train --extra online pytest -q`. Check the run is green on both Python versions. Needs a branch off `orch/reviewed` so PR #12 turns green, and the same file on `main` | none. Do first |
| B2 | PR #12 merge | Saad | Merge once B1 is green. The PR body lists only T24 and T25 but the diff also carries T22 + fixes (modes, menu, online AI match); the orchestrator should correct the body | B1 |
| B3 | Docs refresh and PR #6 | Agent writes, Saad merges | A T10a-refresh brief: update the "Changes since the last gate" table in GDD and CONFIGURATION through decision #102 and the 2026-11-26 state (online back in via T13, weights exist, T09 NOT SUPPORTED, modes), refresh `agent-config.json`, `REQUIREMENTS_CHECKLIST.md`, `EVIDENCE_INDEX.md`, README | Decisions text only; B2 helps (so "on main" claims are true) |
| B4 | Scope lock | Saad approves, agent drafts | One page, `docs/final/SCOPE_LOCK.md`: what stays, what is cut (GDD section 8 order), known limitations (T09, T23 bug, untested online, no hosted URL) | B3 |
| B5 | Tracker | Saad chooses tool, agent builds | If in-repo: `docs/final/TRACKER.md` with Tasks (from `STATUS.md`), Weekly PPP (dated by Saad), Risk Register (from `PROJECT_PLAN.md`) | Saad's choice (decision #10 predates the move) |
| B6 | Layout decision for T03 | Saad | Choose A (game in `game/`, recommended) or B (game at the repo root). See T03 plan | none |
| B7 | T03 move, `init`, tailor roles, `render`, `validate` | Agent (tech-lead) under a T03 brief; Saad tailors or approves roles | T03 steps 1 to 12 below | B1, B2, B3 (so the snapshot is green and current), B6 |
| B8 | Coverage map lines | Saad | One line each: producer, design, art, narrative, bi, release | B7 `init` |
| B9 | Handoff Student decision | Saad | Write the decision into the copied `agent-team/handoffs/2026-11-24-qa-to-tech.md` | B7 `init` |
| B10 | External playtest | Saad (and one external person) | Approve PROTOCOL, hypotheses (freeze by commit), CONSENT sentence; run one Session A round; fill LOG sections 1 to 5 | CONSENT approval; a build both can run (B2 or local) |
| B11 | Recording and submission | Saad | Record 3 to 5 minutes on the merged build; post the repository link in the discussion | B2, B7, B10 |
| B12 | Braintrust replies | Saad | Three replies by Mon 2026-11-30 11:59 p.m. | none |

Not blockers but open and known: T23 (a released direction still runs after landing, decision #93, T23-fix1 queued, no result on record) is a playtest-visible bug on `orch/reviewed`; whether to fix it before the external playtest is Saad's call. T21 needs a session restart to be spawnable. The open items in `STATUS.md` "Waiting on Saad" (B2 threshold, D1 "on screen", trap cost "1 heart in all", macro cadence, T19 a/b/c) are unchanged by this audit.

## G4 blockers (for planning only)

| Requirement | Status | Note |
| --- | --- | --- |
| Three production agents; one added on evidence; origin note with two dated friction links before its first commit | MISSING | Pointers only, see below. Whether any justifies a role is Saad's decision (`COURSE_ROLE_MAP.md`) |
| Chain of three roles, two handoffs, each with a Student decision; one agent revised because a handoff exposed a weakness | MISSING | Only one handoff draft exists |
| Fuller live suite, revised-encounter playtest, post-Alpha release playtest, triage | MISSING | Needs an external playtest first (B10) |
| At least two distinct external players across G2 to G4 | MISSING | Zero today |
| Executable extension with complete manifest | PARTIAL | `agent-config.json`; refresh and review needed (CQ-7 closed by commit 2d40972 per `STATUS.md`; I did not re-verify) |
| Archived runnable release, replay instructions, fallback | PARTIAL | Replay: traces and `docs/final/VERSUS_RUNNER.md` exist; no archived release |
| Pages hosting working | BLOCKED | Pages 404 today |
| Final dated GDD/config update | MISSING | After B3 |

## T03 plan: official-repository move (decision #6)

**Decision needed first (Saad).** Decision #6 says "do the same as we did for the midterm" (a squashed snapshot in a folder of `game-dev-f26`, with a folder-scoped workflow, as a PR). FR section 2 and `team/README.md` now say the game goes into `final-saadsatter`, a template whose root already holds `AGENTS.md`, `CLAUDE.md`, `README.md`, `tests/` and `.github/workflows/final.yml`. These two do not obviously agree, and I could not find a decision that resolves it. Recommended reading: the official repo is the target, as FR says; PR-into-`game-dev-f26` was the midterm method.

**Recommended layout (A).** The game goes under `game/`; the template root stays as is. Reasons: our `AGENTS.md`, `CLAUDE.md`, `README.md`, `tests/`, `pyproject.toml` and `.github/workflows/` would all collide with the template's; the template's tests (`tests/test_team_*.py`) must stay at root for `final.yml`; and our docs and tests use project-root-relative paths that stay valid if `game/` is treated as the project root. Cost: Claude Code started at the repo root reads the template's `AGENTS.md`/`CLAUDE.md`, not ours. The native `.claude/agents/`, `.claude/skills/`, `.claude/settings.json` (`"agent": "orchestrator"`) and the orchestration tests (`tests/test_orchestration_config.py`, `tools/orchestration/verify_models.py` on dfe2d90) assume the project root. Options: run Claude Code from `game/`, or move `.claude/` to the repo root and fix those tests. This needs its own check; I have not tested either.

**Steps.**

1. Preconditions: B1 green, B2 merged, B3 merged (so the snapshot is the current, green, documented `main`). Record the snapshot sha.
2. Clone `final-saadsatter`; read `team/README.md`, `AGENTS.md`, `final.yml`, `tests/test_team_ci.py` (do not edit them; "inspect template before modifying").
3. Run `python -m team init` at the repo root first. It writes `agent-team/{roles/tech.md,roles/qa.md,handoffs/,other-roles.md}`, then renders `.claude/agents/team-tech.md`, `team-qa.md`, `.agents/skills/team-*/SKILL.md`, `agent-team/{board.html,coverage-map.md,team.json}`. Commit this alone.
4. Create the snapshot with `git archive <sha>` (tracked files only) into `game/`. This excludes untracked files, `.venv`, `.claude/worktrees`, transcripts and local scratch. Then verify: `git ls-files assets/original` shows only `MANIFEST.tsv`; no `assets/original/*/` images; no `data/levels/`, `vendor/`, `*conversation*.txt`; `grep -R "ANTHROPIC_API_KEY\|sk-"` finds no secret values. `assets/generated/` is our own PixelLab art and may go (`docs/final/ART_PROVENANCE.md`).
5. Keep `docs/MIDTERM_GUIDELINES.md` and the midterm docs as they are (the midterm record stays separate).
6. Adapt CI. In `.github/workflows/final.yml`, replace only the "Your tests" step with `uv sync --frozen --extra train --extra online` and `uv run --frozen --extra train --extra online pytest -q` using `working-directory: game` (add `astral-sh/setup-uv` and keep Python 3.12). Keep `permissions: contents: read`, `persist-credentials: false`, no secrets, no `pull_request_target` (the template's `test_team_ci.py` checks these). Run `python -m unittest discover -s tests -p "test_team_*.py"` locally before pushing. Do not drop our `ci.yml`, `pages.yml`, `web-smoke.yml` into the root unchanged: their paths and permissions (`pages: write`, `id-token: write`) are not covered by the template test, so check them.
7. Tailor `agent-team/roles/tech.md` and `qa.md` to Shadow Masque from `.claude/agents/tech-lead.md` and `qa.md` (and `docs/final/orchestration/agents/*.md`). Keep QA "writes tests, never game code". Saad approves the text. Then `python -m team render` and commit the generated files together with the edit (never hand-edit them).
8. Copy `docs/final/orchestration/handoff-drafts/2026-11-24-qa-to-tech.md` to `agent-team/handoffs/2026-11-24-qa-to-tech.md`. Saad writes the Student decision. Run `python -m team validate`; fix whatever it reports (expect to check the extra `# Handoff` title line against the template).
9. `agent-team/other-roles.md`: one line each for `producer`, `design`, `art`, `narrative`, `bi`, `release`, in the template's syntax (`student`, `not needed, <reason>`, or `agent <path>`). Saad's decisions. Do not invent reasons.
10. Root `README.md`: keep the template headings but fill the placeholders. Must link: the game (`game/`), the gate documents (`game/docs/final/`, GDD, CONFIGURATION, SCOPE_LOCK, playtest log), `agent-team/`, the tracker, launch commands (`uv run python play.py`, `python -m server`), replay instructions (`docs/final/VERSUS_RUNNER.md`), asset attribution and rights (`docs/ASSET_PROVENANCE.md`, `docs/final/ART_PROVENANCE.md`, Prince of Persia is Ubisoft's; historicalsource README grants no rights), and where the graded midterm record lives.
11. `python -m team render --today from-team-json` then `git diff --exit-code` locally to mirror the CI check. Push to `main` of the official repository only after Saad's go (pushing branches is pre-approved, decisions #27 and #28; merging is not).
12. Saad posts the repository link in the discussion; the orchestrator re-checks Gate decisions issue #1. The old PR: see the BLOCKED row; Saad decides which PR, if any, to close.

**Risks.**

- Private original assets. They exist only on the course branch `saadsatter/midterm`. The official repo must never receive them (`AGENTS.md`). Verify in step 4 and again with `git ls-files` after the commit.
- `AGENTS.md` collision. The template's root `AGENTS.md` says "QA writes tests, never game code" and "you never approve a gate"; ours has the engine invariants. Do not overwrite the template file. If merged into one, that is a change to course tooling and needs Saad's approval.
- CI. `final.yml` runs on a single Python 3.12 with a 10-minute timeout; our suite took 128 s here (4 min in CI on 3.11), so it fits, but the first run has no uv cache. The template test asserts the workflow's token and credential settings. A repo-root `.github/workflows` with pages deploy is untested against it.
- Hosting. The official repo is private; Pages may not be available. Today Pages fails with 404 in the personal repo. Decisions #12 and #13 promised a hosted build for G2/G3.
- Layout A breaks the repo-root assumptions of `.claude/settings.json` and the orchestration tests. Test before relying on it.
- Generated files drift. CI fails if `render` output differs from what is committed.
- Time. A tailored role pair and the Student decision are Saad's words; the agent cannot finish those steps without him.

## Other requested statuses

**Deterministic CI.** Does not pass on `main` (above). It passed through d35fe93 (2026-11-25 19:31Z). Cause is a missing extra in CI, not a game regression: the failing test is the only failure, locally and in CI, and the extra installs fine (`pyproject.toml:12`). Local reproduction ran on this checkout, not on dfe2d90; PR #12's CI log shows `failure` for the same workflow, but I did not open that log (the run was still in progress when I first looked), so I have not verified that the cause is the same there.

**Live evaluation evidence.** See the row. No paid call exists (decision #8). Bounded, recorded runs exist: T07-run1 (tuning) and T09 (held-out, NOT SUPPORTED). Not on record: a run on the current build after T22 to T25; PPO inference errors were not recorded in H6 rows (`RESULTS-T09.md`), and T08-fix2 adds them for later runs.

**Scope lock and dated changes.** Not present on `main`. Present as a stale PR (#6). Scope-lock document does not exist.

**T10b follow-ups in `STATUS.md:90`.** All listed as "not started": GDD sections 2 and 6 labels, `LINGER_AFTER` location (GDD:105), `EVIDENCE_INDEX.md` pass, tracker `docs/final/TRACKER.md` (verified absent), scope lock (verified absent). I re-checked only the tracker and scope-lock files. `EVIDENCE_INDEX.md` on main is dated "Updated 2026-11-16, branch `final/g1-shadow-masque`" and its last row says "First playable, playtest log, scope lock: *planned*". Saad's uncommitted edits to it (STATUS, "Uncommitted work") could not be checked from here.

**Session-record numbering clash.** Still present on main. `docs/agent-sessions/` holds two `13-` files (`13-t01-engine-fixes.md`, `13-T04-versus-runner.md`), three `14-` files (`14-T05-macros-baseline.md`, `14-t06b-traps.md`, `14-t14-web-build.md`) and `15-T05-fix1-macros-baseline.md`; the number STATUS names, Saad's `15-native-orchestration.md`, is not in the tree, so the clash it describes is not yet visible; later records (T07-run1, T08-*, T13-*, T18-*, T19, T20-*, T21) have no number. `docs/agent-sessions/README.md` indexes only sessions 11, 12 and 20. Fixing it renames committed evidence, which links point to, so it needs a decision on which numbers to keep, then a T10b-style evidence pass.

## Contradictions

1. `STATUS.md` header says gameplay on `main` is "unchanged since 721b3e6" and the T01 fixes, runner, macros, PPO and web build are "not on main". `main` contains the PR #11 merge (a93d36a, ancestor of 4120a54), and the repository tree on main has `pop/versus_runner.py`, `agents/macros.py`, `agents/rl/`, `server/`, `web/`. Its "Branches" table (orch/reviewed f08c1a8) and "Next eligible task" (T19) are also stale; its task table runs to T25.
2. PR #12's body says "What is new since PR #11: T24 + T24-fix1, T25". The T22 chain (Gate 3 at 083546e) is also not on main (`git merge-base --is-ancestor` false for 083546e and 6efecbe against 4120a54), and the diff main..dfe2d90 adds `agents/modes.py`, `render/menu.py`, `server/modes.py`, `docs/final/GAME_MODES.md`.
3. Dates. `PROJECT_PLAN.md:21` and `REQUIREMENTS_CHECKLIST.md` put G2/G3 deliverables on Mon 30 Nov; FR, `COURSE_ROLE_MAP.md`, STATUS and Saad's brief say Sat 28 Nov 11:59 p.m. for the recording and repository move (and Mon 30 Nov for the Braintrust replies). FR says the newer announcement controls; I used Sat 28 Nov.
4. `REQUIREMENTS_CHECKLIST.md` on main (updated 2026-11-16) lists "Server sends each client only its own seat's observation: not started", "G2+G3 ... not started", and "AI cadence one macro about every 4 s", all superseded by T13 (decisions #36 to #38, #48, #49), #24 and #3.
5. PR #6's Changes table (2026-11-24) says online human vs human is "deferred" (#1; superseded for hosting by #12 and later by T13, decision #36), "No trained weights exist" (weights `ppo-run-1.json` now exist, T07-run1), scenario suite "WIP" (T08/T09 closed), "T07 review pending". It cites decisions only to #30. Merging it as is would put false statements on main.
6. `agent-config.json` on main: `status_note` says rival code is "not on main yet" and "No trained weights exist yet"; both false after a93d36a.
7. Decision #6 (squashed folder in `game-dev-f26`, midterm method) versus FR section 2 and `team/README.md` (official repo is a template with its own root files). And the midterm PR #92 in `game-dev-f26` belongs to "Oath and Ember"; the Prince of Persia PR #57 is already closed.
8. `GDD.md` section 8 on main lists "online play ... 3 modes" as included by G2/G3, while PR #6's Changes table, written two days earlier, says online is deferred. The two cannot both be current.
9. `docs/final/README.md` is titled "G1 Concept" and describes the repo as G1; the root `README.md` is still the midterm README.
10. `DECISIONS-2026-11-24.md` also holds 2026-11-25 and 2026-11-26 entries (#87 to #102), and `STATUS.md` records that PPO decisions #74 to #77 were first numbered #67 to #70. Numbering is consistent now but the file name is misleading.

## Friction on record

From `COURSE_ROLE_MAP.md` "G4", which cites `reports/AUDIT-D-requirements.md`. Paths and dates only. I did not open the underlying commits or session records and cannot confirm that any of them is repeated friction of the kind the course requires. Whether any justifies a role is Saad's decision.

- Design: dfc8ade (2026-11-17), 05fe136 (2026-11-17), session record S13 (2026-11-23), S06 (2026-10-26).
- Art: S12 (2026-11-17), fbcff5b, 3784127, fa086fe (dates not given there).
- Evaluation/live: S04 (2026-10-26), S09, S03.
- Release/provenance: c3aa550, bb89412, 0e5df5f (2026-10-26), S05 to S07.

## Scope changes since G1, and whether each has a dated Saad decision

All are in `DECISIONS-2026-11-23.md` and `DECISIONS-2026-11-24.md` with verbatim answers. Decision numbers below are cited from those files.

| Change | Decision | Dated | Note |
| --- | --- | --- | --- |
| AI rival is a trained PPO policy; LLM out of scope | #3 | 2026-11-23 | Replaces G1's Claude Haiku rival. Spending cap under $1 (#8) |
| Duel limit 5 minutes | #5 | 2026-11-23 | OQ-3 closed |
| Traps in G2; loose floor first | #2, #22 | 2026-11-23 | Gate plate not built per PR #6 table; I did not re-check on dfe2d90 |
| Hosted Pyodide + Phaser build by G2/G3 | #12, #13, #25 | 2026-11-23 | Hosting currently fails (Pages 404) |
| Online human vs human back in scope, LAN server, rooms | #36 to #38, #41, #46, #48, #49, #52 to #57 | 2026-11-24 | Reverses #1's deferral. The text of #36 should be read in the file before the GDD cites it |
| Three modes (AI Model, Baseline, Human vs Human); menu default | #87 to #92 | 2026-11-25 | |
| Kneel takes uniform; hang wins at a ledge; sheathe first | #94, #98, #101 | 2026-11-25 | |
| Online AI/Baseline private match, centred loading screen | #95 to #97, #102 | 2026-11-25/26 | |
| Macro vocabulary, runner policy, cadence | #23, #24 | 2026-11-23 | Cadence value 4 decisions still "waiting on Saad" |
| Disguise rule changes (R-V24 to R-V26, linger) | #4, #15, #17, #18, #19 | 2026-11-23 | |

Cut order (GDD section 8: rooms 6 to 3, suspicion meter, one trap type, AI vs AI test-only, public hosting) has not been invoked by any decision I found.

## Tests run

```
uv run --extra train pytest -q -p no:cacheprovider      (on main 4120a54, this worktree)
1 failed, 1756 passed, 32 skipped, 3 xfailed, 2 warnings in 128.08s (0:02:08)
FAILED tests/test_online_boundary.py::test_hello_goes_to_its_own_client_and_error_messages_are_fixed_text
```

Not run: `python -m team validate/render` (no `agent-team/` exists), any suite on dfe2d90, any browser, any live model call.

## Ordered checklist for the next 48 hours

Thursday 2026-11-26 (today)

1. Orchestrator: dispatch the CI fix (B1) from `orch/reviewed`; confirm green on 3.11 and 3.12; apply the same to `main`. (agent)
2. Orchestrator: correct PR #12's body (T22 is in it); after B1 is green, Saad merges PR #12 (B2). (Saad)
3. Saad: decide the T03 layout (B6), the tracker tool (B5), and which old course PR, if any, to close.
4. Saad: approve `docs/final/playtest/PROTOCOL.md`, the hypotheses and the CONSENT "What is recorded" sentence; freeze them by commit (B10 prerequisites). Decide whether T23 is fixed before the playtest.
5. Orchestrator: dispatch the docs refresh (B3) and the scope-lock draft (B4); tell the workers to cite PR/commit shas, not branch names. (agent)
6. Saad: schedule one external player (not an agent, not Saad) and an observer.

Friday 2026-11-27

7. Saad: review and merge the refreshed docs (PR #6 replaced or refreshed) and approve the scope lock.
8. Orchestrator: dispatch T03 (B7) with the plan above, once B1, B2, B3 are on main. T03 runs `init`, snapshot, CI adaptation, README, tracker, `validate`, `render`; pushes a branch to the official repo (pre-approved), no merge. (agent)
9. Saad: tailor or approve `roles/tech.md` and `roles/qa.md`; write the `other-roles.md` lines (B8); write the Student decision on the handoff (B9).
10. Saad: run the external Session A playtest (one round is enough for "observe at least one external player using the core loop"); an agent may only copy the factual sheet rows into `LOG.md`; Saad writes the interpretation (B10).
11. Saad: enable Pages or record a decision to demo locally (B2/hosting row).

Saturday 2026-11-28

12. Orchestrator: re-run `python -m team validate`, `render` and the full suite on the official repo; read the Gate decisions issue; check the final `main` sha. (agent)
13. Saad: merge T03 into the official repo's `main`; post the repository link in the discussion; close the old PR if he decides to.
14. Saad: record 3 to 5 minutes on the graded build; say honestly that T09 was NOT SUPPORTED, that nothing is balance-tested by players beyond the one external session, and name the known limitations (T23 if unfixed, hosting). Submit before 11:59 p.m.
15. Monday 2026-11-30: three Braintrust replies by 11:59 p.m. (Saad)

## Findings

- [major, reproduced] CI on `main` is red since a93d36a. Reproduced here (see Tests run). Fix is in B1.
- [major, verified] Official repo contains only the template; T03 not started.
- [major, verified] No external playtest, no tracker, no scope lock, no `agent-team/`.
- [minor, verified] Contradictions 1 to 10 above.
- [unverified concerns] Branch protection and required checks on either repository; whether PR #12's CI failure has the same cause; Pages availability for the private official repo; the contents of course discussions; whether the G1 recording and deck links still open.

## Known limitations

I trusted FR for the course text and did not re-read the original announcement. I did not open Saad's uncommitted files. Evidence counts in `REVIEW_LOG.md` (for example `2245 passed` at T25 Gate 2) were not reproduced; my own run was on `main` only.

## Unresolved findings

All of the above except where marked verified as met.

## Requested next action

Orchestrator: read this report at the sha that records it, brief B1 immediately, then B3 and T03 after Saad answers B6. Saad: items 2 to 4 of the checklist.

## Student decision required

1. T03 layout: game under `game/` in the official repo (recommended) or at the root; and whether decision #6's PR-into-`game-dev-f26` method still applies.
2. Which old course PR, if any, to close (#92 is a different project's midterm).
3. Tracker tool and location.
4. Whether T23 is fixed before the external playtest.
5. Hosting for the recording: enable Pages, or demo locally.
6. The Student decision text on the G2/G3 handoff, the coverage-map lines, and the CONSENT sentence. These are yours alone to write.
