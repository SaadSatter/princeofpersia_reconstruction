"""T20: tools/telemetry/summarize.py on a fixture directory (tests/data/t20_telemetry)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from tools.telemetry import summarize

FIXTURE = Path(__file__).parent / "data" / "t20_telemetry"


def run(out: Path, src: Path = FIXTURE) -> dict:
    assert summarize.main([str(src), "--out", str(out)]) == 0
    return json.loads((out / "summary.json").read_text())


def seat(doc: dict, name: str) -> dict:
    return next(s for s in doc["seats"] if s["file"] == name)


def test_stalls(tmp_path):
    doc = run(tmp_path)
    a = seat(doc, "2026-11-25-ABCD-001-A.jsonl")["stalls"]
    assert a["idle_spells"] == 1 and a["idle_total_s"] == 7.167
    assert a["refused_runs"] == [{"action": "LUNGE", "start_t": 5, "end_t": 8, "length": 4}]
    assert a["stuck_rooms"] == []
    b2 = seat(doc, "2026-11-25-ABCD-002-B.jsonl")["stalls"]
    assert b2["stuck_rooms"] == ["room-ccc"] and b2["longest_room_s"] == 83.333


def test_quits(tmp_path):
    doc = run(tmp_path)
    q = {s["file"]: s["quits"] for s in doc["seats"]}
    assert q["2026-11-25-ABCD-001-B.jsonl"]["disconnects"] == 1
    assert q["2026-11-25-ABCD-001-B.jsonl"]["reconnects"] == 1
    assert q["2026-11-25-ABCD-001-B.jsonl"]["no_rematch"] is True
    assert q["2026-11-25-ABCD-001-A.jsonl"]["rematch_pressed"] is True
    assert q["2026-11-25-ABCD-002-B.jsonl"]["forfeit"] == "me"
    assert q["2026-11-25-ABCD-002-A.jsonl"]["forfeit"] == "rival"
    assert q["2026-11-25-EFGH-001-A.jsonl"]["duel_abandoned"] is True
    assert [d["duel"] for d in doc["duels"]] == [1, 2, 1]


def test_mechanics_never_used_or_used_once(tmp_path):
    m = run(tmp_path)["mechanics"]
    assert m["never_used"] == ["sheathe", "sword_pickup"]
    assert m["used_once"] == ["RIG", "TAKE", "block", "draw", "flip"]
    assert m["totals"]["lunge"] == 2


def test_output_is_byte_identical_on_two_runs(tmp_path):
    run(tmp_path / "one")
    shutil.copytree(FIXTURE, tmp_path / "copy")          # same input, another place
    run(tmp_path / "two", tmp_path / "copy")
    for name in ("summary.json", "summary.md"):
        assert (tmp_path / "one" / name).read_bytes() == (tmp_path / "two" / name).read_bytes()
    run(tmp_path / "three")
    assert (tmp_path / "one" / "summary.md").read_bytes() == (tmp_path / "three" / "summary.md").read_bytes()


def test_a_real_log_from_the_server_summarizes(tmp_path):
    from tests.test_t20_telemetry import drive, join, make
    m = make(tmp_path / "logs")
    join(m)
    drive(m, 600)
    doc = run(tmp_path / "out", tmp_path / "logs")
    assert doc["logs"] == 2 and {d["seat"] for d in doc["seats"]} == {"A", "B"}
