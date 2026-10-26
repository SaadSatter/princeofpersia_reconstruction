"""Fidelity checks against the original Level 1 file (local only).

Skipped unless the pinned file is present (`uv run python tools/fetch_level1.py`).
CI never has it (decision D1), so these run on a maintainer's machine; the
session log records each run. They check aggregate facts and behavior,
never a committed copy of the layout.
"""

from collections import Counter, deque

import pytest

from pop import levelfile as LF
from pop import levels
from pop import tiles as T
from pop.interface import Episode

pytestmark = pytest.mark.skipif(not levels.available(),
                                reason="original Level 1 not fetched (tools/fetch_level1.py)")


@pytest.fixture(scope="module")
def L1():
    return levels.load_level1()


def reachable_rooms(s):
    seen, q = {s.start[0]}, deque([s.start[0]])
    while q:
        for nxt in s.links[q.popleft()]:
            if nxt and nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    return seen


def test_apple2_and_dos_files_have_identical_layouts():
    a = LF.parse((levels.LEVEL_DIR / levels.APPLE2.filename).read_bytes())
    d = LF.parse((levels.LEVEL_DIR / levels.DOS.filename).read_bytes())
    assert a.sha256 == levels.APPLE2.sha256 and d.sha256 == levels.DOS.sha256
    assert LF.same_layout(a, d)


def test_21_rooms_reachable_three_slots_unreachable(L1):
    """24 slots hold tiles, but rooms 13 and 18 are linked only from each other
    and room 24 from nowhere, so a player can reach 21 rooms."""
    assert len(L1.rooms) == 24
    assert len(reachable_rooms(L1)) == 21


def test_object_counts_in_the_reachable_rooms(L1):
    c = Counter(sym for r in reachable_rooms(L1) for row in L1.rooms[r] for sym in row)
    assert (c[T.SPIKES], c[T.GATE], c[T.RAISE_PLATE], c[T.DROP_PLATE], c[T.LOOSE],
            c[T.POTION], c[T.EXIT_LEFT], c[T.SWORD], c[T.BONES]) == (9, 5, 9, 2, 12, 4, 1, 1, 2)


def test_start_one_gate_open_at_load_exit_closed(L1):
    assert L1.start == (1, 0, 0, +1)
    assert len(L1.gates_open) == 1
    ep = Episode("L1")
    obs = ep.reset(0)
    assert (obs["kid"]["row"], obs["kid"]["col"], obs["kid"]["facing"]) == (1, 0, "right")
    assert all(g.pos == 0 for g in ep._game.mech.gates.values())     # the open one slammed
    assert not any(e.open for e in ep._game.mech.exits.values())


def test_two_guards_in_the_file(L1):
    lvl = LF.parse(levels.level1_path().read_bytes())
    assert len(lvl.guards) == 2 and {g.program for g in lvl.guards} == {0}


# Found by tools/solve_level1.py on 2026-10-26 (session 08): start -> sword in
# room 15 -> back to the exit in room 9. No guard yet (phase P5).
SWORD_ROUTE = """JUMP_RIGHT RIGHT RIGHT RIGHT JUMP_RIGHT WAIT LEFT JUMP_LEFT RUN_JUMP_LEFT UP LEFT LEFT RUN_JUMP_LEFT WAIT STEP_LEFT UP JUMP_LEFT LEFT JUMP_LEFT LEFT RIGHT RIGHT RUN_JUMP_RIGHT LEFT RUN_JUMP_LEFT RUN_JUMP_LEFT UP RUN_JUMP_LEFT RUN_JUMP_LEFT WAIT LEFT RUN_JUMP_LEFT WAIT STEP_LEFT JUMP_LEFT UP LEFT RUN_JUMP_LEFT RUN_JUMP_LEFT LEFT RUN_JUMP_LEFT WAIT DOWN LEFT RIGHT JUMP_RIGHT UP RUN_JUMP_RIGHT JUMP_RIGHT UP JUMP_RIGHT JUMP_RIGHT RIGHT RUN_JUMP_RIGHT RUN_JUMP_RIGHT RIGHT UP WAIT WAIT WAIT JUMP_RIGHT RUN_JUMP_RIGHT WAIT RUN_JUMP_RIGHT UP WAIT STEP_RIGHT JUMP_RIGHT JUMP_RIGHT JUMP_RIGHT JUMP_RIGHT RUN_JUMP_RIGHT RIGHT RUN_JUMP_RIGHT RUN_JUMP_RIGHT RUN_JUMP_RIGHT RUN_JUMP_RIGHT RIGHT LEFT UP RIGHT RIGHT JUMP_RIGHT RUN_JUMP_RIGHT LEFT RUN_JUMP_LEFT UP""".split()


def test_sword_route_completes_level1():
    ep = Episode("L1")
    ep.reset(0)
    for a in SWORD_ROUTE:
        assert ep.step("kid", a)["accepted"], a
    assert ep.observe("kid")["kid"]["sword"] is True
    out = ep.outcome()
    assert out["reason"] == "won" and out["actions"] == 87 and out["invalid_actions"] == 0
    assert out["actions"] <= levels.LEVEL1_LIMITS
