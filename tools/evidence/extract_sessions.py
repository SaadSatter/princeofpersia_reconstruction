"""Extract redacted, factual records from local Claude Code and Codex transcripts.

Usage (repository root):
    python3 -I tools/evidence/extract_sessions.py --out <facts.json>
        [--claude-dir <dir> ...] [--codex-dir ~/.codex/sessions]
        [--repo-marker princeofpersia_reconstruction] [--exclude <session-id-prefix> ...]

The output is a working file for writing `docs/agent-sessions/*.md`; it is not
committed (it quotes instructions at length). Everything in it is passed through
`redact()`. The script only reads transcripts; it never writes next to them.

What is extracted, per session file:
  tool, session id, parent id (Codex subagents), model ids, first/last event (UTC),
  git branches / cwd, classification, human instructions (redacted), skills and
  subagents used, files edited, git commits and PR URLs seen in tool output,
  test-run summary lines seen in tool output, and the final assistant message.
Nothing is inferred: a field that the transcript does not contain stays empty.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from redact import redact  # noqa: E402

COMMIT = re.compile(r"^\[([\w./\-]+)(?: \(root-commit\))? ([0-9a-f]{7,12})\] (.+)$", re.M)
PR_URL = re.compile(r"https://github\.com/[\w\-]+/[\w\-.]+/pull/\d+")
# The example submission URL quoted in docs/midterm/MIDTERM_GUIDELINES.md. A
# session that reads the guidelines prints it; it is not a PR of this project.
EXAMPLE_PRS = frozenset({"https://github.com/columbia-university-ai-games/game-dev-f26/pull/123"})
TESTS = re.compile(r"^\s*(?:Test Files|Tests)\s+.*\b(?:passed|failed)\b.*$", re.M)
TSC_FAIL = re.compile(r"error TS\d{4}")
INJECTED = (
    "# AGENTS.md", "<environment_context", "<user_instructions", "<permissions",
    "The following is the Codex agent history", "<app-context", "<INSTRUCTIONS>",
)


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, dict):
                if c.get("type") in ("text", "input_text", "output_text"):
                    parts.append(c.get("text", ""))
                elif c.get("type") == "tool_result":
                    parts.append(text_of(c.get("content")))
        return "\n".join(parts)
    return ""


def deep_strings(value, depth: int = 0):
    """Yield every string inside a value, decoding JSON-encoded strings (Codex nests them)."""
    if depth > 4:
        return
    if isinstance(value, str):
        s = value.strip()
        if s[:1] in "{[":
            try:
                yield from deep_strings(json.loads(s), depth + 1)
                return
            except json.JSONDecodeError:
                pass
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from deep_strings(v, depth + 1)
    elif isinstance(value, list):
        for v in value:
            yield from deep_strings(v, depth + 1)


def scan_output(rec: dict, out: str) -> None:
    for branch, sha, msg in COMMIT.findall(out):
        item = {"branch": branch, "sha": sha, "subject": redact(msg.strip())[:160]}
        if item not in rec["commits"]:
            rec["commits"].append(item)
    for u in PR_URL.findall(out):
        if u in EXAMPLE_PRS:
            rec["example_prs_seen"] = True
            continue
        if u not in rec["prs"]:
            rec["prs"].append(u)
    for line in TESTS.findall(out):
        line = re.sub(r"\x1b\[[0-9;]*m", "", line).strip()
        rec["test_lines"].append(line[:160])
    if TSC_FAIL.search(out):
        rec["typecheck_errors_seen"] = True


def new_record(tool: str, path: str) -> dict:
    return {
        "tool": tool, "id": None, "parent_id": None, "file": redact(path),
        "models": [], "first": None, "last": None, "branches": [], "cwd": [],
        "instructions": [], "skills": [], "subagents": [], "files_edited": [],
        "commits": [], "prs": [], "test_lines": [], "typecheck_errors_seen": False,
        "final_message": "", "kind": None, "agent_path": None,
    }


def claude_file(path: str) -> dict:
    rec = new_record("claude", path)
    rec["id"] = os.path.basename(path)[:-6]
    last_assistant = ""
    for line in open(path, errors="ignore"):
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = d.get("timestamp")
        if ts:
            rec["first"] = rec["first"] or ts
            rec["last"] = ts
        if d.get("gitBranch") and d["gitBranch"] not in rec["branches"]:
            rec["branches"].append(d["gitBranch"])
        if d.get("cwd") and redact(d["cwd"]) not in rec["cwd"]:
            rec["cwd"].append(redact(d["cwd"]))
        m = d.get("message") or {}
        if d.get("type") == "assistant":
            mid = m.get("model")
            if mid and mid != "<synthetic>" and mid not in rec["models"]:
                rec["models"].append(mid)
            for c in m.get("content") or []:
                if not isinstance(c, dict):
                    continue
                if c.get("type") == "text" and c.get("text", "").strip():
                    last_assistant = c["text"]
                if c.get("type") == "tool_use":
                    inp = c.get("input") or {}
                    if c["name"] == "Skill":
                        s = str(inp.get("skill"))
                        if s not in rec["skills"]:
                            rec["skills"].append(s)
                    if c["name"] in ("Agent", "Task"):
                        s = str(inp.get("subagent_type") or "general-purpose")
                        if s not in rec["subagents"]:
                            rec["subagents"].append(s)
                    if c["name"] in ("Edit", "Write", "NotebookEdit"):
                        fp = redact(str(inp.get("file_path", "")))
                        if fp and fp not in rec["files_edited"]:
                            rec["files_edited"].append(fp)
        if d.get("type") == "user":
            content = m.get("content")
            out = text_of(content)
            if isinstance(content, list) and any(isinstance(c, dict) and c.get("type") == "tool_result" for c in content):
                scan_output(rec, out)
                continue
            # A slash-command skill (/name) is loaded as a meta message naming its directory.
            for s in re.findall(r"^Base directory for this skill: \S*/skills/([A-Za-z0-9_.:\-]+)", out, re.M):
                if s not in rec["skills"]:
                    rec["skills"].append(s)
            if d.get("isMeta") or d.get("isCompactSummary"):
                continue
            t = out.strip()
            if not t or t.startswith(("<local-command", "<command-name>", "<bash-stdout>", "<task-notification", "Caveat:")):
                continue
            if t.startswith("This session is being continued from a previous conversation"):
                continue
            rec["instructions"].append({"ts": ts, "text": redact(t)})
    rec["final_message"] = redact(last_assistant)[:2000]
    return rec


def codex_file(path: str) -> dict:
    rec = new_record("codex", path)
    last_assistant = ""
    metas = []
    for line in open(path, errors="ignore"):
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = d.get("timestamp")
        if ts:
            rec["first"] = rec["first"] or ts
            rec["last"] = ts
        p = d.get("payload") or {}
        if d.get("type") == "session_meta":
            metas.append(p)
            if p.get("cwd") and redact(p["cwd"]) not in rec["cwd"]:
                rec["cwd"].append(redact(p["cwd"]))
        if d.get("type") == "turn_context" and p.get("model") and p["model"] not in rec["models"]:
            rec["models"].append(p["model"])
        if p.get("type") == "message":
            t = text_of(p.get("content")).strip()
            if p.get("role") == "user" and t and not t.startswith(INJECTED):
                rec["instructions"].append({"ts": ts, "text": redact(t)})
            if p.get("role") == "assistant" and t:
                last_assistant = t
        if p.get("type") in ("function_call_output", "custom_tool_call_output", "item_completed"):
            for s in deep_strings(p):
                scan_output(rec, s)
        if p.get("type") in ("function_call", "custom_tool_call"):
            args = p.get("arguments") or p.get("input") or ""
            args = args if isinstance(args, str) else json.dumps(args)
            for s in re.findall(r"\.agents/skills/([a-z0-9\-]+)/SKILL\.md", args):
                if s not in rec["skills"]:
                    rec["skills"].append(s)
            for f in re.findall(r"\*\*\* (?:Add|Update|Delete) File: ([^\s\\]+)", args):
                f = redact(f)
                if f not in rec["files_edited"]:
                    rec["files_edited"].append(f)
    # The first session_meta describes this thread; later ones are inherited context.
    if metas:
        me = metas[0]
        rec["id"] = me.get("id")
        src = me.get("source")
        if isinstance(src, dict) and "subagent" in src:
            sub = src["subagent"]
            if isinstance(sub, dict) and "thread_spawn" in sub:
                rec["parent_id"] = sub["thread_spawn"].get("parent_thread_id")
                rec["agent_path"] = sub["thread_spawn"].get("agent_path")
                rec["kind"] = "codex-subagent"
            else:
                rec["kind"] = "codex-permission-check"  # "guardian" auto-review of tool calls
        else:
            rec["kind"] = "codex-work-session"
    if "codex-auto-review" in rec["models"]:
        rec["kind"] = "codex-permission-check"
    rec["final_message"] = redact(last_assistant)[:2000]
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--claude-dir", action="append", default=None,
                    help="Claude Code project transcript folder(s); default: every ~/.claude/projects folder "
                         "whose name contains the repo marker (covers worktrees such as princeofpersia_reconstruction worktrees)")
    ap.add_argument("--codex-dir", default=os.path.expanduser("~/.codex/sessions"))
    ap.add_argument("--repo-marker", default="princeofpersia_reconstruction")
    ap.add_argument("--exclude", action="append", default=[])
    a = ap.parse_args()

    claude_dirs = a.claude_dir or sorted(
        glob.glob(os.path.expanduser(f"~/.claude/projects/*{a.repo_marker.replace('_', '-')}*")))
    records = []
    for f in sorted(f for d in claude_dirs for f in glob.glob(os.path.join(d, "*.jsonl"))):
        if any(os.path.basename(f).startswith(x) for x in a.exclude):
            continue
        r = claude_file(f)
        r["kind"] = "claude-session"
        records.append(r)
    for f in sorted(glob.glob(os.path.join(a.codex_dir, "**", "*.jsonl"), recursive=True)):
        try:
            if a.repo_marker not in open(f, errors="ignore").read():
                continue
        except OSError:
            continue
        r = codex_file(f)
        if any((r["id"] or "").startswith(x) for x in a.exclude):
            continue
        records.append(r)
    records.sort(key=lambda r: r["first"] or "")
    with open(a.out, "w") as fh:
        json.dump(records, fh, indent=1)
    for r in records:
        print(f"{r['tool']:6} {r['kind']:24} {(r['id'] or '')[:36]:36} {(r['first'] or '')[:16]} "
              f"instr={len(r['instructions']):3} commits={len(r['commits']):2} prs={len(r['prs'])} "
              f"tests={len(r['test_lines'])} skills={','.join(r['skills'])}")
    print(f"{len(records)} transcript files", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
