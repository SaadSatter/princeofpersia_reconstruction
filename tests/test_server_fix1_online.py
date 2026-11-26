"""T13-fix1: corrections to the online server (QA-1, QA-2, EVAL-2, EVAL-3, EVAL-4, Origin, keepalive).

Localhost only, short fake timeouts, no network beyond 127.0.0.1. Needs the `online` extra.
"""

from __future__ import annotations

import asyncio
import json
import threading
import time
from pathlib import Path

import pytest

websockets = pytest.importorskip("websockets")

from server.match import Match, TICK_S                             # noqa: E402
from server.rival import TimeLimitedRival                          # noqa: E402
from tests.test_gate_t13_qa_online import (Client, Rig, drain, join, run,   # noqa: E402,F401
                                           settle, site)

ROOT = Path(__file__).resolve().parent.parent


def test_a_stalled_reader_is_dropped_alone_and_the_other_seat_keeps_playing(site):
    async def go():
        async with Rig(site) as r:
            r.srv.send_timeout = 0.3
            wa, ha, wb, hb = await r.duel()
            wa.transport.pause_reading()
            for _ in range(2500):
                r.now[0] += TICK_S
                await asyncio.wait_for(r.srv.pump(), 0.5)         # the loop never waits on A
                await asyncio.sleep(0)
                if not r.match.connected["A"]:
                    break
            await settle(200)
            assert not r.match.connected["A"] and r.match.state == "paused"
            assert r.match.connected["B"] and wb.q.qsize() > 100      # B kept receiving
            assert r.srv.conns.get("A") is None
            wa.transport.abort(), wb.transport.abort()
    run(go())


def test_a_reconnect_hello_arrives_in_under_a_second_over_a_half_open_old_socket(site):
    async def go():
        async with Rig(site) as r:
            wa, ha, wb, hb = await r.duel()
            wa.transport.pause_reading()                          # old socket never answers the close
            t0 = time.monotonic()
            w2, first = await join(r.port, ha["token"])
            assert first["type"] == "hello" and first["seat"] == "A"
            assert time.monotonic() - t0 < 1.0
            wa.transport.abort(), w2.transport.abort(), wb.transport.abort()
    run(go())


def test_a_silent_drop_is_detected_by_keepalive_keys_cleared_and_grace_starts(site):
    async def go():
        async with Rig(site) as r:
            # 3 s / 3 s / 1 s in production; short fake values here.
            r.srv.ping_interval, r.srv.ping_timeout, r.srv.close_timeout = 0.2, 0.2, 0.2
            r.server.close()
            await r.server.wait_closed()
            r.server = await r.srv.start("127.0.0.1", 0)
            r.port = r.server.sockets[0].getsockname()[1]
            wa = Client(await websockets.connect(f"ws://127.0.0.1:{r.port}/ws", ping_interval=None))
            await wa.send(json.dumps({"type": "join"}))
            assert json.loads(await wa.recv())["seat"] == "A"
            wb, hb = await join(r.port)
            await wa.send(json.dumps({"type": "keys", "keys": ["d"]}))
            await settle(100)
            assert r.match.held["A"]
            wa.transport.pause_reading()                          # silent: no pong, no close
            t0 = time.monotonic()
            while r.match.connected["A"] and time.monotonic() - t0 < 5:
                await settle(50)
            took = time.monotonic() - t0
            assert not r.match.connected["A"], "half-open seat never detected"
            assert took < 2.0, took                               # about 0.2 + 0.2 + 0.2 here
            assert r.match.held["A"] == set()
            assert r.match.state == "paused" and "A" in r.match.deadline
            wa.transport.abort(), wb.transport.abort()
    run(go())


def test_production_keepalive_defaults_are_3_and_3():
    from server import app
    assert (app.PING_INTERVAL_S, app.PING_TIMEOUT_S) == (3.0, 3.0)


def test_origin_must_match_host(site):
    async def go():
        async with Rig(site) as r:
            url = f"ws://127.0.0.1:{r.port}/ws"
            with pytest.raises(websockets.exceptions.InvalidStatus) as e:
                await websockets.connect(url, additional_headers={"Origin": "http://evil.example"})
            assert e.value.response.status_code == 403
            assert not r.match.tokens
            ok = await websockets.connect(url, additional_headers={"Origin": f"http://127.0.0.1:{r.port}"})
            await ok.send(json.dumps({"type": "join"}))
            assert json.loads(await asyncio.wait_for(ok.recv(), 2))["type"] == "hello"
            ok.transport.abort()
    run(go())


class _Slow:
    name, kind = "slow", "scripted"

    def __init__(self):
        self.gate, self.resets = threading.Event(), []

    def __call__(self, obs, legal):
        self.gate.wait(3)
        return "WAIT"

    def reset(self, seed):
        self.resets.append(seed)


def _workers(rival):
    return [t for t in threading.enumerate() if t.is_alive() and t._target == rival._work]


def test_rival_reset_while_the_worker_is_busy_still_takes_effect():
    inner = _Slow()
    rival = TimeLimitedRival(inner, budget_s=0.01)
    assert rival({}, ["WAIT"]) is None                           # worker now busy and blocked
    rival.reset(7)
    inner.gate.set()
    for _ in range(100):
        if inner.resets:
            break
        time.sleep(0.02)
    assert inner.resets == [7]
    rival.close()


def test_rival_close_stops_the_worker_thread():
    rival = TimeLimitedRival(_Slow(), budget_s=0.01)
    assert len(_workers(rival)) == 1
    rival.close()
    for _ in range(100):
        if not _workers(rival):
            break
        time.sleep(0.02)
    assert _workers(rival) == []


def test_lobby_reset_closes_the_rival_worker():
    m = Match(seed=1, rival="baseline")
    worker = m.game.rival
    assert len(_workers(worker)) == 1
    m._reset_lobby()
    for _ in range(100):
        if not _workers(worker):
            break
        time.sleep(0.02)
    assert _workers(worker) == []
    m.close()


def test_online_js_does_not_reconnect_after_replaced_and_says_why():
    js = (ROOT / "web" / "online.js").read_text()
    assert "This seat was opened in another tab" in js and '"replaced"' in js
    assert js.index('"replaced"') < js.index("window.setTimeout(connect")


def test_traces_online_is_git_ignored():
    assert "traces/online/" in (ROOT / ".gitignore").read_text().split()
