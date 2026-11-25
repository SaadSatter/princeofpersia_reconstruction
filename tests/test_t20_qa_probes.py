"""T20 QA probes (Gate 1): lifecycle with the flag off, a room that fails, a real scripted
duel through the summarizer, privacy of every written file, and two findings (xfail strict)."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from server.match import TICK_S, Match
from server.telemetry import Telemetry

ROOT = Path(__file__).resolve().parents[1]


def mk(tmp, **kw):
    tele = None if tmp is None else Telemetry(tmp, "QAQA", info={"build": "qa"},
                                              today=lambda: "2026-11-25")
    return Match(seed=4242, rival=None, telemetry=tele, rival_budget_s=1.0, **kw)


def hold(m, seat, keys, ticks, now):
    m.receive(seat, json.dumps({"type": "keys", "keys": keys}), now)
    for _ in range(ticks):
        now += TICK_S
        m.advance(now)
    return now


def lifecycle(m):
    """join, play, pause, reconnect, forfeit, rematch pressed, close."""
    a, b = m.join(None, 0.0), m.join(None, 0.0)
    now = hold(m, "A", ["g"], 1, 0.0)
    now = hold(m, "A", [], 15, now)
    m.connection_lost("B", now)
    m.join(b["token"], now + 1)
    now = hold(m, "B", ["left"], 5, now + 1)
    m.connection_lost("A", now)
    m.advance(now + 20)
    m.receive("B", json.dumps({"type": "rematch"}), now + 20)
    m.close()
    return a, b


def test_flag_off_writes_no_file_anywhere(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    lifecycle(mk(None))
    assert list(tmp_path.rglob("*")) == []


def test_room_failed_after_the_trace_writer_raises_still_closes_logs_once(tmp_path):
    pytest.importorskip("websockets")
    from server.app import OnlineServer
    from server.rooms import Room

    def boom(trace):
        raise OSError("trace dir unwritable")
    m = mk(tmp_path, on_finish=boom)
    m.join(None, 0.0)
    m.join(None, 0.0)
    now = hold(m, "A", ["d"], 10, 0.0)
    m.connection_lost("A", now)
    with pytest.raises(OSError):
        m.advance(now + 20)                 # forfeit -> _record -> boom
    OnlineServer._room_failed(Room("QAQA", m))
    OnlineServer._room_failed(Room("QAQA", m))          # twice is harmless
    for seat in "AB":
        rows = [json.loads(x) for x in
                (tmp_path / f"2026-11-25-QAQA-001-{seat}.jsonl").read_text().splitlines()]
        assert [r["type"] for r in rows].count("duel_end") == 1
        assert [r["type"] for r in rows].count("forfeit") == 1
        assert [r["t"] for r in rows[1:]] == sorted(r["t"] for r in rows[1:])
    assert (tmp_path / "2026-11-25-QAQA-001-host.json").is_file()


def test_lifecycle_events_and_privacy_of_every_file(tmp_path):
    a, b = lifecycle(mk(tmp_path))
    files = sorted(tmp_path.iterdir())
    assert len(files) == 3
    blob = "\n".join(p.read_text() for p in files)
    for secret in (a["token"], b["token"]):
        assert secret not in blob
    assert not re.search(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", blob)
    for word in ("user-agent", "mozilla", "origin", "token", "name", "ip"):
        assert not re.search(rf'"{word}"', blob.lower()), word
    ev = [json.loads(x) for x in (tmp_path / "2026-11-25-QAQA-001-A.jsonl").read_text().splitlines()[1:]]
    kinds = [e["type"] for e in ev]
    for k in ("disconnect", "forfeit", "duel_end"):
        assert k in kinds
    assert kinds.index("disconnect") < kinds.index("forfeit") < kinds.index("duel_end")
    evb = [json.loads(x) for x in (tmp_path / "2026-11-25-QAQA-001-B.jsonl").read_text().splitlines()[1:]]
    kb = [(e["type"], e.get("phase")) for e in evb]
    assert ("disconnect", None) in kb and ("reconnect", None) in kb
    assert ("pause", "start") in kb and ("pause", "end") in kb


def test_real_scripted_duel_summarizes_deterministically(tmp_path):
    m = mk(tmp_path)
    m.join(None, 0.0)
    m.join(None, 0.0)
    now = hold(m, "A", ["g"], 1, 0.0)
    now = hold(m, "A", [], 20, now)
    now = hold(m, "A", ["g"], 1, now)               # sheathe
    now = hold(m, "A", [], 40, now)                  # idle spell > 3 s
    now = hold(m, "A", ["f"], 5, now)                # refused lunges (no sword)
    m.close()
    outs = []
    for name in ("one", "two"):
        out = tmp_path / name
        r = subprocess.run([sys.executable, str(ROOT / "tools/telemetry/summarize.py"),
                            str(tmp_path), "--out", str(out)], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        outs.append(out)
    for n in ("summary.json", "summary.md"):
        assert (outs[0] / n).read_bytes() == (outs[1] / n).read_bytes()
    doc = json.loads((outs[0] / "summary.json").read_text())
    sa = next(s for s in doc["seats"] if s["seat"] == "A")
    assert sa["mechanics"]["draw"] == 1 and sa["mechanics"]["sheathe"] == 1
    assert sa["stalls"]["idle_spells"] >= 1
    assert sa["stalls"]["refused_runs"] and sa["stalls"]["refused_runs"][0]["action"] == "LUNGE"
    assert sa["quits"]["duel_abandoned"] is True
    assert "TAKE" in doc["mechanics"]["never_used"]


def _flips(tmp_path, held_ticks):
    m = mk(tmp_path)
    m.join(None, 0.0)
    m.join(None, 0.0)
    now = hold(m, "A", ["d", "w"], held_ticks, 0.0)
    hold(m, "A", [], 20, now)
    m.close()
    r = subprocess.run([sys.executable, str(ROOT / "tools/telemetry/summarize.py"), str(tmp_path)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    doc = json.loads((tmp_path / "summary.json").read_text())
    return next(s for s in doc["seats"] if s["seat"] == "A")["mechanics"]["flip"]


@pytest.mark.xfail(strict=True, reason="QA-T20-F1: a held key counts one flip per tick")
def test_one_held_jump_is_one_flip_not_one_per_tick(tmp_path):
    assert _flips(tmp_path, 10) == 1


@pytest.mark.xfail(strict=True, reason="QA-T20-F2: R-V35 grace: the dropped direction is logged as accepted")
def test_a_direction_cancelled_by_a_jump_within_grace_logs_as_the_jump_only(tmp_path):
    m = mk(tmp_path)
    m.join(None, 0.0)
    m.join(None, 0.0)
    now = hold(m, "A", ["d"], 1, 0.0)
    now = hold(m, "A", ["d", "w"], 1, now)
    hold(m, "A", [], 15, now)
    m.close()
    ev = [json.loads(x) for x in (tmp_path / "2026-11-25-QAQA-001-A.jsonl").read_text().splitlines()[1:]]
    acc = [e["action"] for e in ev if e["type"] == "action" and e["accepted"]]
    assert acc == ["RUN_JUMP_RIGHT"], acc
