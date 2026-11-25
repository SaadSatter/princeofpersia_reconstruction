#!/usr/bin/env python3
"""Report which models actually ran in a Claude Code session and its subagents.

The orchestrator uses this to record *verified* runtime models in
``docs/final/orchestration/REVIEW_LOG.md``, instead of trusting an agent's
own statement of its model or the configured value in ``.claude/agents``.

Claude Code (checked on 2.1.331) writes, per project:

    ~/.claude/projects/<encoded-cwd>/<session-id>.jsonl            main session
    ~/.claude/projects/<encoded-cwd>/<session-id>/subagents/
        agent-<id>.jsonl        the subagent's transcript
        agent-<id>.meta.json    {"agentType": ..., "model": ..., ...}

Each assistant line carries ``message.model``: the model id on the API
response. That is the evidence this script reports. Read-only, stdlib only,
no network.

Usage:
    python3 tools/orchestration/verify_models.py --latest
    python3 tools/orchestration/verify_models.py --session <id> --json
    python3 tools/orchestration/verify_models.py --latest \\
        --expect-main claude-opus-5-5 --expect-worker claude-sonnet-5-5
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# The named workers whose model is pinned in .claude/agents/*.md. Built-in
# helpers (Explore, web-fetch, claude-code-guide) run on their own models and
# are reported but not checked against --expect-worker.
NAMED_WORKERS = frozenset(
    {"tech-lead", "qa", "evaluation-specialist", "requirements-auditor", "rules-reviewer"}
)


def encode_project_dir(cwd: Path) -> str:
    """Claude Code's folder name for a project: every non-alphanumeric is '-'."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(cwd))


def default_projects_root(cwd: Path) -> Path:
    return Path.home() / ".claude" / "projects" / encode_project_dir(cwd)


def response_models(transcript: Path) -> list[str]:
    """Distinct model ids on assistant responses, in first-seen order."""
    seen: list[str] = []
    if not transcript.exists():
        return seen
    with transcript.open(encoding="utf-8") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("type") != "assistant":
                continue
            msg = rec.get("message")
            model = msg.get("model") if isinstance(msg, dict) else None
            if model and model != "<synthetic>" and model not in seen:
                seen.append(model)
    return seen


def session_report(root: Path, session_id: str) -> dict:
    main = root / f"{session_id}.jsonl"
    if not main.exists():
        raise FileNotFoundError(f"no transcript {main}")
    subagents = []
    sub_dir = root / session_id / "subagents"
    for meta_path in sorted(sub_dir.glob("agent-*.meta.json")) if sub_dir.is_dir() else []:
        agent_id = meta_path.name[len("agent-"):-len(".meta.json")]
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            meta = {}
        subagents.append(
            {
                "agent_id": agent_id,
                "agent_type": meta.get("agentType"),
                "description": meta.get("description"),
                "meta_model": meta.get("model"),
                "response_models": response_models(sub_dir / f"agent-{agent_id}.jsonl"),
                "spawn_depth": meta.get("spawnDepth"),
                "finished": meta.get("finished"),
            }
        )
    return {
        "session_id": session_id,
        "main_response_models": response_models(main),
        "subagents": subagents,
    }


def latest_session(root: Path) -> str:
    candidates = sorted(root.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    if not candidates:
        raise FileNotFoundError(f"no session transcripts in {root}")
    return candidates[-1].stem


def check(report: dict, expect_main: str | None, expect_worker: str | None) -> list[str]:
    """Return mismatch messages; an empty list means every expectation held."""
    problems: list[str] = []
    if expect_main:
        models = report["main_response_models"]
        if models != [expect_main]:
            problems.append(f"main session models {models}, expected only {expect_main}")
    if expect_worker:
        for sub in report["subagents"]:
            if sub["agent_type"] not in NAMED_WORKERS:
                continue
            models = sub["response_models"]
            if models != [expect_worker]:
                problems.append(
                    f"{sub['agent_type']} ({sub['agent_id']}) models {models}, expected only {expect_worker}"
                )
    return problems


def render_text(report: dict) -> str:
    lines = [
        f"session {report['session_id']}",
        f"  main: {', '.join(report['main_response_models']) or '(no assistant responses)'}",
    ]
    if not report["subagents"]:
        lines.append("  subagents: none")
    for sub in report["subagents"]:
        lines.append(
            f"  subagent {sub['agent_id']} type={sub['agent_type']} "
            f"meta_model={sub['meta_model']} responses={','.join(sub['response_models']) or '-'} "
            f"desc={sub['description']!r}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    which = ap.add_mutually_exclusive_group(required=True)
    which.add_argument("--session", help="session id (the transcript's file stem)")
    which.add_argument("--latest", action="store_true", help="newest session for this project")
    ap.add_argument("--root", type=Path, help="transcript folder (default: ~/.claude/projects/<cwd>)")
    ap.add_argument("--json", action="store_true", help="print JSON instead of text")
    ap.add_argument("--expect-main", help="fail unless the main session used only this model")
    ap.add_argument("--expect-worker", help="fail unless every named worker used only this model")
    args = ap.parse_args(argv)

    root = args.root or default_projects_root(Path.cwd())
    try:
        session_id = args.session or latest_session(root)
        report = session_report(root, session_id)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    problems = check(report, args.expect_main, args.expect_worker)
    report["problems"] = problems
    print(json.dumps(report, indent=2) if args.json else render_text(report))
    for p in problems:
        print(f"MISMATCH: {p}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
