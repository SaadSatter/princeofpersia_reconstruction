# AUDIT-A: Architecture, branches and integration strategy (read-only)
Assigned agent: `agents/tech-lead.md` (audit mode)
Setup: `tasks/_AUDIT_COMMON.md`
Requirements: FINAL_REQUIREMENTS §1 (design contract), §2 (branch audit [+]), §6 G2/G3 "integrated competitive duel, disguise, scripted guards and model rival".
Permitted write paths: none (scratch checkouts under /home/claude/sm/wt/AUDIT-A only).

Determine, with commits and paths as evidence:
1. Branch ancestry: merge-bases and ahead/behind counts between all six branches; which branch contains which other; what is unique to each (`git log A..B --oneline`, `git diff --stat`).
2. Implemented gameplay per branch, verified by reading code and tests, not branch names: two seats/real-time ticks, swordplay, hearts, scripted guards, disguise + suspicion, flips, traps (loose floor, gate plate; ownership), arena rooms (count), win/draw/time limit, human controls (play.py keys for two seats), AI rival seat for versus (does `agents/model_player.py` or the baseline drive a versus seat yet?), macro-action vocabulary, online server/web client (`server/`, `web/`).
3. Game modes that actually run today: human vs human (local? online?), human vs AI, AI vs AI, and the command for each, or "not runnable".
4. Conflicting implementations or docs across branches (e.g. split screen vs online play; art branch vs versus branch).
5. Reusable engine components (interface five operations, observation, runner limits/timeouts/traces, evaluate.py, replay).
6. Missing gameplay for the G2/G3 core loop versus `docs/final/VERSUS_SPEC.md` (approved 2026-11-17) and the G1 cut order.
7. Recommended integration strategy: target branch, order of merges, conflicts expected, and what to move into the official repo (`/home/claude/final-saadsatter`) and how (preserving the course template, `team/`, `final.yml`).
Run the suite on each branch that has a different `tests/` tree and report the result lines.
