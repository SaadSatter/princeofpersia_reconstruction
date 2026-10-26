"""The authoritative engine stays headless."""

from pathlib import Path

POP = Path(__file__).resolve().parent.parent / "pop"


def test_engine_never_imports_pygame():
    for path in POP.glob("*.py"):
        text = path.read_text()
        assert "import pygame" not in text and "from pygame" not in text, path.name


AGENTS = POP.parent / "agents"
FORBIDDEN_FOR_PLAYERS = ("pop.engine", "pop.situations", "pop.mechanics", "pop.physics",
                         "pop.interface", "pop.observation", "solutions", "evaluate")


def test_players_cannot_import_the_engine_situations_or_solutions():
    """Rubric 2b: players get observations and legal actions only."""
    import ast
    for path in AGENTS.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""] + [f"{node.module}.{a.name}" for a in node.names]
            else:
                continue
            for name in names:
                assert not name.startswith(FORBIDDEN_FOR_PLAYERS), (path.name, name)
