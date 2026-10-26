"""The authoritative engine stays headless."""

from pathlib import Path

POP = Path(__file__).resolve().parent.parent / "pop"


def test_engine_never_imports_pygame():
    for path in POP.glob("*.py"):
        text = path.read_text()
        assert "import pygame" not in text and "from pygame" not in text, path.name
