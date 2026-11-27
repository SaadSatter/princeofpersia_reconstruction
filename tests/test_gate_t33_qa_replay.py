"""T33 QA: independent reproduction of the XGJT-001 replay claims on slide 4.

Reads only the committed telemetry; replays with the repository's own engine and
`server.trace.replay`. Does not import anything from `presentation/`.
"""
import json
from pathlib import Path

import pytest

pytest.importorskip("server.trace")

from pop.versus import arena_episode
from server.trace import replay

ROOT = Path(__file__).resolve().parent.parent
TRACE = ROOT / "docs/final/playtest/telemetry/2026-11-27/online/duel-XGJT-001-seed0.json"
A_LOG = ROOT / "docs/final/playtest/telemetry/2026-11-27/playtest/2026-11-27-XGJT-001-A.jsonl"
HASH = "5dadb78e1da67d1fb312711bd48dbc60a2a4f71f5000fb00b14ec1463572a910"


@pytest.fixture(scope="module")
def trace():
    return json.loads(TRACE.read_text())


def test_replay_hash_and_outcome(trace):
    outcome, h = replay(trace)
    assert h == HASH == trace["state_hash"]
    assert outcome == trace["outcome"]
    assert outcome["reason"] == "won:B" and outcome["frames"] == 465
    assert len(trace["ticks"]) == 465


def test_replay_events_match_human_seat_log(trace):
    ep = arena_episode(trace["seed"])
    rooms, hearts, last_room, last_hp = [], [], None, None
    sword_by_tick = {}
    for tick, (inputs, released) in enumerate(zip(trace["ticks"], trace["releases"]), 1):
        for seat, act in inputs:
            ep.step(seat, act)
        for seat in released:
            ep.release(seat)
        ep.tick()
        o = ep.observe("A")
        if o["room"] != last_room:
            rooms.append(tick)
            last_room = o["room"]
        if o["me"]["hp"] != last_hp:
            hearts.append((tick, o["me"]["hp"]))
            last_hp = o["me"]["hp"]
    assert hearts[-3:] == [(417, 2), (441, 1), (465, 0)]
    assert [t for t in rooms if t > 1] == [67, 153, 246]
    log = [json.loads(line) for line in A_LOG.read_text().splitlines()]
    assert [e["t"] for e in log if e.get("type") == "hit"] == [417, 441, 465]
    drops = [e for e in log if e.get("type") == "sword_drop"]
    assert [(e["t"], e.get("cause")) for e in drops] == [(465, "thrown")]


def test_human_sends_throw_before_the_only_drop(trace):
    a_inputs = [(t, act) for t, inp in enumerate(trace["ticks"], 1) for s, act in inp if s == "A"]
    assert (463, "THROW") in a_inputs
    # human idle between the inputs at 240 and 372 (the audit says "240 to 372"; both ends are inputs)
    assert not [t for t, _ in a_inputs if 240 < t < 372]
