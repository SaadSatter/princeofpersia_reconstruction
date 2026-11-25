"""T22-fix2: where the T22 modes and the T20 playtest telemetry meet.

An AI room or `play.py --mode ai|baseline` with telemetry on logs only the human seat A, in
that seat's own terms; the AI seat gets no file, its observation, inputs and fallbacks never
reach a log; the duel is the same with and without the flag; every mode takes `--playtest`.
"""

from __future__ import annotations

import asyncio
import json
import os
import random
from pathlib import Path
from types import SimpleNamespace

import pytest

from server import modes as room_modes
from server.match import TICK_S
from server.telemetry import Telemetry

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

KEYSETS = [[], ["d"], ["a"], ["w", "d"], ["f"], ["d", "lshift"], ["right"], ["up", "right"], ["down"]]


def room(mode: str, tmp: Path | None, budget: float = 1.0):
    tele = None if tmp is None else Telemetry(tmp, "ROOM", info={"build": "t"}, today=lambda: "2026-11-25")
    m = room_modes.make_match(mode, seed=11, telemetry=tele, rival_budget_s=budget)
    m.join(None, 0.0)
    return m


def drive(m, ticks=900):
    rng, now, sent = random.Random(5), 0.0, []
    for i in range(ticks):
        if i % 6 == 0:
            m.receive("A", json.dumps({"type": "keys", "keys": rng.choice(KEYSETS)}), now)
        now += TICK_S
        m.advance(now)
        sent += m.drain("A")
    return sent


@pytest.mark.parametrize("mode", ["ai", "baseline"])
def test_ai_room_logs_only_the_human_seat(tmp_path, mode):
    m = room(mode, tmp_path)
    drive(m, 300)
    m.close_telemetry("abandoned")
    assert [p.name for p in tmp_path.glob("*.jsonl")] == ["2026-11-25-ROOM-001-A.jsonl"]
    rows = [json.loads(x) for x in (tmp_path / "2026-11-25-ROOM-001-A.jsonl").read_text().splitlines()]
    assert rows[0]["rival"] == mode and rows[0]["seat"] == "A"
    assert {r["seat"] for r in rows[1:]} == {"A"}
    assert rows[-1]["type"] == "duel_end"


def test_ai_room_log_has_nothing_of_the_ai_seat_or_its_fallbacks(tmp_path):
    m = room("ai", tmp_path, budget=0.0)          # every answer is late: fallbacks on the server
    drive(m, 300)
    m.close_telemetry("abandoned")
    assert m.trace()["fallbacks"]                  # the server did record them (trace only)
    text = (tmp_path / "2026-11-25-ROOM-001-A.jsonl").read_text().lower()
    for word in ("fallback", "source", "policy", "ppo", "macro", "seat b", '"b"'):
        assert word not in text, word


@pytest.mark.parametrize("mode", ["ai", "baseline"])
def test_telemetry_leaves_the_ai_duel_and_every_message_unchanged(tmp_path, mode):
    a, b = room(mode, None), room(mode, tmp_path)
    sa, sb = drive(a), drive(b)
    assert a.trace()["state_hash"] == b.trace()["state_hash"]
    assert json.dumps(sa) == json.dumps(sb)
    assert list(tmp_path.glob("*-A.jsonl"))


def test_human_room_still_logs_both_seats(tmp_path):
    m = room_modes.make_match("human", seed=3, telemetry=Telemetry(tmp_path, "R", today=lambda: "d"))
    m.join(None, 0.0)
    m.join(None, 0.0)
    m.advance(TICK_S)
    assert sorted(p.name for p in tmp_path.glob("*.jsonl")) == ["d-R-001-A.jsonl", "d-R-001-B.jsonl"]


def test_server_wires_playtest_into_every_room_mode(tmp_path, monkeypatch):
    """`python -m server --playtest` hands a Telemetry to the home room and to a created room
    of any mode (the merge of T20's `make_match` and T22's `mode` argument)."""
    from server import __main__ as srv_main
    import server.app as app

    seen = {}

    class FakeServer:
        def __init__(self, match, site_dir=None, match_factory=None):
            seen["home"], seen["factory"] = match, match_factory

        async def start(self, host, port):
            return SimpleNamespace(sockets=[SimpleNamespace(getsockname=lambda: ("x", 1))])

        async def run_ticks(self):
            raise asyncio.CancelledError

    monkeypatch.setattr(app, "OnlineServer", FakeServer)
    ns = SimpleNamespace(trace_dir=None, rival="none", seed=0, neutral=False, playtest=True,
                         telemetry_dir=str(tmp_path), host="127.0.0.1", port=0)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(srv_main.serve_forever(ns))
    assert seen["home"].telemetry is not None
    for mode, rival in (("ai", "ai"), ("baseline", "baseline"), ("human", None)):
        mt = seen["factory"]("XYZ", mode)
        assert mt.telemetry is not None and mt.rival == rival
    ns.playtest = False
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(srv_main.serve_forever(ns))
    assert seen["home"].telemetry is None and seen["factory"]("Q", "ai").telemetry is None


# --- play.py ------------------------------------------------------------------------------
def play_run(tmp_path, *argv, name="s.png"):
    pytest.importorskip("pygame")
    import play
    png = tmp_path / name
    assert play.main([*argv, "--scale", "1", "--screenshot", str(png)]) == 0
    return png


def jsonl(out: Path):
    return sorted(out.glob("*.jsonl"))


@pytest.mark.parametrize("mode", ["ai", "baseline"])
def test_play_mode_ai_playtest_logs_only_seat_a(tmp_path, mode):
    out = tmp_path / "pt"
    play_run(tmp_path, "--mode", mode, "--playtest", "--telemetry-dir", str(out),
             "--keys", "A:RIGHT,A:RIGHT,A:DRAW")
    files = jsonl(out)
    assert [f.name.rsplit("-", 1)[1] for f in files] == ["A.jsonl"]
    rows = [json.loads(x) for x in files[0].read_text().splitlines()]
    assert rows[0]["rival"] == mode and rows[0]["room"] == "LOCAL"
    assert {r["seat"] for r in rows[1:]} == {"A"}
    assert any(r["type"] == "action" and r["accepted"] for r in rows)
    assert rows[-1]["type"] == "duel_end"


def test_play_mode_human_playtest_logs_both_seats(tmp_path):
    out = tmp_path / "pt"
    play_run(tmp_path, "--mode", "human", "--playtest", "--telemetry-dir", str(out),
             "--keys", "A:RIGHT,B:LEFT")
    assert [f.name.rsplit("-", 1)[1] for f in jsonl(out)] == ["A.jsonl", "B.jsonl"]
    assert json.loads(jsonl(out)[0].read_text().splitlines()[0])["rival"] == "human"


def test_play_menu_choice_then_playtest(tmp_path):
    out = tmp_path / "pt"
    play_run(tmp_path, "--menu", "--menu-keys", "return", "--playtest", "--telemetry-dir", str(out))
    assert [f.name.rsplit("-", 1)[1] for f in jsonl(out)] == ["A.jsonl"]


def test_play_mode_without_the_flag_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    play_run(tmp_path, "--mode", "ai", "--keys", "A:RIGHT")
    assert not (tmp_path / "traces").exists()


def test_play_playtest_does_not_change_an_ai_run(tmp_path):
    keys = ("--seed", "3", "--keys", "A:RIGHT,A:RIGHT,A:DRAW")
    a = play_run(tmp_path, "--mode", "ai", *keys, name="a.png")
    b = play_run(tmp_path, "--mode", "ai", "--playtest", "--telemetry-dir", str(tmp_path / "pt"),
                 *keys, name="b.png")
    assert a.read_bytes() == b.read_bytes()


def test_play_playtest_still_needs_a_versus_or_mode_game():
    import play
    with pytest.raises(SystemExit):
        play.main(["S3", "--playtest"])
