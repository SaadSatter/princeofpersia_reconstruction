"""The course workflow template stays inside the submission boundary (3c)."""

from pathlib import Path

WORKFLOW = Path(__file__).resolve().parent.parent / "ci" / "midterm-saadsatter.yml"


def test_course_workflow_is_scoped_to_the_folder_and_needs_no_secrets():
    text = WORKFLOW.read_text()
    assert "pull_request:" in text
    assert "- 'midterms/saadsatter/**'" in text
    assert "working-directory: midterms/saadsatter" in text
    assert "secrets." not in text and "pull_request_target" not in text
    assert "--live" not in text and "ANTHROPIC_API_KEY" not in text
    assert "uv run --frozen pytest -q" in text
    # Every path filter points into our folder or at this workflow itself.
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("- '") and "/" in s:
            assert s in ("- 'midterms/saadsatter/**'",
                         "- '.github/workflows/midterm-saadsatter.yml'"), s
