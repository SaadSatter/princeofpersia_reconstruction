"""Checks on the native agent hierarchy (docs/final/orchestration/README.md).

These guard the *configuration*: which model each agent is pinned to, who may
spawn whom, where each worker's procedure lives, and the handoff template.
They cannot prove which model ran; tools/orchestration/verify_models.py reads
that from session transcripts, and its parsing is tested here on fixtures.
No network, no Claude Code needed.
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = ROOT / ".claude" / "agents"
ORCH = ROOT / "docs" / "final" / "orchestration"

OPUS = "claude-opus-5-5"
SONNET = "claude-sonnet-5-5"
WORKERS = ("tech-lead", "qa", "evaluation-specialist", "requirements-auditor")
SPAWNABLE = set(WORKERS) | {"rules-reviewer"}


def frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    assert m, f"{path} has no front matter"
    fields = {}
    for line in m.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep and not line.startswith(" "):
            fields[key.strip()] = value.strip()
    return fields, m.group(2)


def tool_list(value: str) -> list[str]:
    """Split a tools line on commas that are not inside Agent(...)."""
    return [t.strip() for t in re.split(r",\s*(?![^()]*\))", value) if t.strip()]


def test_orchestrator_is_pinned_to_opus_and_can_spawn_only_named_workers():
    fm, body = frontmatter(AGENTS_DIR / "orchestrator.md")
    assert fm["name"] == "orchestrator"
    assert fm["model"] == OPUS
    tools = tool_list(fm["tools"])
    agent_entries = [t for t in tools if t.startswith("Agent(")]
    assert len(agent_entries) == 1, tools
    allowed = {a.strip() for a in agent_entries[0][len("Agent("):-1].split(",")}
    assert SPAWNABLE <= allowed
    # No generic or forked worker can stand in for a named one.
    assert not allowed & {"general-purpose", "claude", "fork", "orchestrator"}
    # A disallowedTools entry of the form Agent(x) removed the whole Agent
    # tool in Claude Code 2.1.331 (probe, 2026-11-24); keep the allowlist form.
    assert "disallowedTools" not in fm
    assert "docs/final/orchestration/agents/orchestrator.md" in body


@pytest.mark.parametrize("name", WORKERS)
def test_workers_are_pinned_to_sonnet_isolated_and_cannot_spawn(name):
    fm, body = frontmatter(AGENTS_DIR / f"{name}.md")
    assert fm["name"] == name
    assert fm["model"] == SONNET
    assert fm.get("isolation") == "worktree"
    tools = tool_list(fm["tools"])
    assert not any(t.startswith(("Agent", "Task")) for t in tools), tools
    procedure = f"docs/final/orchestration/agents/{name}.md"
    assert procedure in body
    assert (ROOT / procedure).is_file()
    # A worker that reads CLAUDE.md must not take on the orchestrator role.
    assert "not the orchestrator" in " ".join(body.split())


def test_rules_reviewer_stays_read_only_on_sonnet():
    fm, _ = frontmatter(AGENTS_DIR / "rules-reviewer.md")
    assert fm["model"] == SONNET
    assert set(tool_list(fm["tools"])) == {"Read", "Grep", "Glob"}


def test_qa_and_auditor_cannot_write_production_code_by_their_definitions():
    _, qa_body = frontmatter(AGENTS_DIR / "qa.md")
    assert "Never edit production code" in " ".join(qa_body.split())
    fm, _ = frontmatter(AGENTS_DIR / "requirements-auditor.md")
    assert "Edit" not in tool_list(fm["tools"])


def test_project_settings_select_the_orchestrator_without_permission_bypass():
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text())
    assert settings["agent"] == "orchestrator"
    assert settings["model"] == OPUS
    text = json.dumps(settings)
    assert "bypassPermissions" not in text and "dangerously" not in text.lower()
    assert "CLAUDE_CODE_SUBAGENT_MODEL" not in text


def test_claude_md_routes_roles_and_keeps_agents_md():
    text = (ROOT / "CLAUDE.md").read_text()
    assert "@AGENTS.md" in text
    assert "docs/final/orchestration/agents/orchestrator.md" in text
    for name in SPAWNABLE:
        assert f"`{name}`" in text


def test_every_role_procedure_exists():
    for name in ("orchestrator", *WORKERS):
        assert (ORCH / "agents" / f"{name}.md").is_file()


REQUIRED_REPORT_FIELDS = (
    "handoff_id", "task_id", "date", "from", "to", "configured_model",
    "runtime_model", "consumed", "source_branch", "source_commit",
    "reviewed_commit", "verdict",
)
REQUIRED_REPORT_HEADINGS = (
    "Work completed", "Paths", "Acceptance criteria", "Tests run", "Findings",
    "Known limitations", "Unresolved findings", "Requested next action",
    "Student decision required",
)


def test_report_template_carries_every_handoff_field():
    fm, body = frontmatter(ORCH / "reports" / "_TEMPLATE.md")
    for field in REQUIRED_REPORT_FIELDS:
        assert field in fm, field
    for heading in REQUIRED_REPORT_HEADINGS:
        assert f"## {heading}" in body, heading
    protocol = (ORCH / "HANDOFF_PROTOCOL.md").read_text()
    for field in REQUIRED_REPORT_FIELDS:
        assert f"`{field}`" in protocol or field in protocol, field


def test_agent_config_has_the_course_manifest_fields():
    cfg = json.loads((ROOT / "agent-config.json").read_text())
    for key in (
        "schema_version", "purpose", "tools_available", "prohibited_actions",
        "memory_policy", "context_sources", "model_choice",
        "prompts_or_system_instructions", "named_failure_modes",
        "evaluation_cases", "logging_policy", "human_override_points",
        "test_command", "ci_workflow_path", "native_artifact", "limits",
        "fallback", "limitations", "agent_team", "playing_agent_interface",
    ):
        assert key in cfg, key
    assert (ROOT / cfg["ci_workflow_path"]).is_file()
    assert (ROOT / ".claude/skills/evaluate-rival/SKILL.md").is_file()
    for member in cfg["agent_team"]:
        for path in member["native_artifact"].split(", "):
            assert (ROOT / path).is_file(), path


# --- tools/orchestration/verify_models.py ---------------------------------

def _load_verify_models():
    path = ROOT / "tools" / "orchestration" / "verify_models.py"
    spec = importlib.util.spec_from_file_location("verify_models", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _write_jsonl(path: Path, models: list[str]) -> None:
    lines = [{"type": "user", "message": {"role": "user", "content": "x"}}]
    lines += [{"type": "assistant", "message": {"model": m, "content": []}} for m in models]
    lines.append({"type": "assistant", "message": {"model": "<synthetic>", "content": []}})
    path.write_text("\n".join(json.dumps(l) for l in lines) + "\nnot json\n")


def _fixture(tmp_path: Path, worker_model: str = SONNET) -> Path:
    sid = "s1"
    _write_jsonl(tmp_path / f"{sid}.jsonl", [OPUS, OPUS])
    sub = tmp_path / sid / "subagents"
    sub.mkdir(parents=True)
    for aid, kind, model in (("a1", "tech-lead", worker_model), ("a2", "web-fetch", "claude-haiku-5-5")):
        (sub / f"agent-{aid}.meta.json").write_text(json.dumps({"agentType": kind, "model": model}))
        _write_jsonl(sub / f"agent-{aid}.jsonl", [model])
    return tmp_path


def test_verify_models_reads_main_and_subagent_models(tmp_path):
    vm = _load_verify_models()
    report = vm.session_report(_fixture(tmp_path), "s1")
    assert report["main_response_models"] == [OPUS]
    by_type = {s["agent_type"]: s for s in report["subagents"]}
    assert by_type["tech-lead"]["response_models"] == [SONNET]
    assert by_type["tech-lead"]["meta_model"] == SONNET
    assert vm.check(report, OPUS, SONNET) == []  # built-in web-fetch is not checked


def test_verify_models_flags_a_worker_on_the_wrong_model(tmp_path, capsys):
    vm = _load_verify_models()
    root = _fixture(tmp_path, worker_model=OPUS)
    code = vm.main(["--session", "s1", "--root", str(root),
                    "--expect-main", OPUS, "--expect-worker", SONNET])
    assert code == 1
    assert "tech-lead" in capsys.readouterr().err


def test_verify_models_latest_and_missing_session(tmp_path):
    vm = _load_verify_models()
    root = _fixture(tmp_path)
    assert vm.latest_session(root) == "s1"
    assert vm.main(["--session", "nope", "--root", str(root)]) == 2


def test_project_folder_encoding_matches_claude_code():
    vm = _load_verify_models()
    assert vm.encode_project_dir(Path("/Users/a/AI_Pract/pop_x")) == "-Users-a-AI-Pract-pop-x"
