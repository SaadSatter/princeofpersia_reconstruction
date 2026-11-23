# AUDIT-D: Requirements, documentation, agents, tracker and playtests (read-only)
Assigned agent: `agents/requirements-auditor.md`
Setup: `tasks/_AUDIT_COMMON.md`
Requirements: every line of `/home/claude/sm/inputs/FINAL_REQUIREMENTS.md`.
Permitted write paths: none.

Produce the full compliance matrix (one row per requirement line), judged mainly on `final/versus-engine` 13c7488 plus the uncommitted patch, with other branches noted where they matter. Then specifically:
1. G2/G3 (Sat Nov 28) blockers and G4 (Sat Dec 5) blockers.
2. Documentation: GDD and Configuration — do they cover mechanics, dynamics, aesthetics, scoring, win conditions, edge cases, balance; affordances, tools, context, retrieval, evaluation, adversarial failures, model id/settings, versions, timeout/retry/spend limits, fallback, knowledge boundary? Is there a dated "Changes since the last gate" section? Do they still say split screen while decisions say online?
3. Production agents: what exists (`CLAUDE.md`, `.claude/agents/rules-reviewer.md`, `.codex/agents/pop-rule-reviewer.toml`, skills, `AGENT-TEAM.md`), whether `agent-team/` exists anywhere, what the course `team` tool expects (`/home/claude/final-saadsatter/team/README.md`, `team/defaults/`), coverage map status, handoffs so far (any reviewer → implementer cycle with a recorded Saad decision, e.g. the 2026-11-18 flip review), and which existing reviews could legitimately become a recorded handoff.
4. Friction on record: dated instances of repeated commands, corrections or slow steps in `docs/agent-sessions/`, `docs/reviews/`, `docs/audits/`, `AGENT-TEAM.md` and the four root conversation logs (`1st conversaiton.txt` … `4th Conversation.txt`) that could support an origin note for a third agent (e.g. evaluation, design, art, release). Quote path + date + a short paraphrase only. Do not infer friction that is not written.
5. Tracker: any Notion/GitHub Projects/Issues link, Weekly PPP, Risk Register (`docs/final/PROJECT_PLAN.md`)?
6. Playtests: any external playtest record, consent text, playtest log format (CQ-6), silent-playtester notes.
7. README state and official-repo migration readiness.
