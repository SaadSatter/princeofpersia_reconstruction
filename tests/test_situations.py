"""The suite: layouts match the frozen declaration and every situation is winnable."""

import re
from pathlib import Path

import pytest

from pop.interface import Episode
from pop.situations import SITUATIONS
from solutions import SOLUTIONS

SUITE = Path(__file__).resolve().parent.parent / "docs" / "EVALUATION_SUITE.md"


def _section(sid: str) -> str:
    text = SUITE.read_text()
    m = re.search(rf"^#{{2,3}} {sid} .*?(?=^#{{2,3}} |\Z)", text, re.S | re.M)
    assert m, sid
    return m.group(0)


@pytest.mark.parametrize("sid", sorted(SITUATIONS))
def test_layout_matches_declared_suite(sid):
    section = _section(sid)
    for rows in SITUATIONS[sid].rooms.values():
        for row in rows:
            assert row in section, (sid, row)
    s = SITUATIONS[sid]
    assert f"{s.max_actions} " in section or f"{s.max_actions} /" in section


@pytest.mark.parametrize("sid", sorted(SITUATIONS))
def test_scripted_route_wins_within_limits(sid):
    ep = Episode(sid)
    ep.reset(100)
    for a in SOLUTIONS[sid]:
        assert ep.step("kid", a)["accepted"], (sid, a)
    out = ep.outcome()
    assert out["reason"] == "won" and out["score"] == 1
    assert out["actions"] <= SITUATIONS[sid].max_actions


def test_held_out_flags():
    assert {s for s, v in SITUATIONS.items() if v.held_out} == {"H1", "H2", "H3"}
