"""GATE-T13-fix1 QA: regression probes against the per-seat queues, the background close,
the 3 s + 3 s keepalive, the Origin check and the per-duel fallback log.

Localhost only. One test uses the production 3 s + 3 s keepalive in real time (about 7 s).
Needs the `online` extra.
"""

from __future__ import annotations

import asyncio
import json
import threading
import time

import pytest

websockets = pytest.importorskip("websockets")

from server.app import MAX_QUEUED, OnlineServer, SeatLink                # noqa: E402
from server.match import TICK_S, Match                                   # noqa: E402
from server.trace import replay                                          # noqa: E402
from tests.test_gate_t13_qa_online import (Client, Rig, drain, join, run,  # noqa: E402,F401
                                           settle, site)


def state(i):
    return json.dumps({"type": "state", "seat": "A", "n": i}, separators=(",", ":"))


def status(name):
    return json.dumps({"type": "status", "state": name}, separators=(",", ":"))


class FakeWS:
    """A socket whose send can be held shut, to model a slow link."""

    def __init__(self, delay=0.0):
        self.sent, self.delay = [], delay
        self.gate = asyncio.Event()
        self.gate.set()
        self.aborted = False
        outer = self

        class T:
            def abort(self):
                outer.aborted = True
        self.transport = T()

    async def send(self, text):
        await self.gate.wait()
        if self.delay:
            await asyncio.sleep(self.delay)
        self.sent.append(text)


# --- the per-seat queue ----------------------------------------------------------------

def test_queue_keeps_every_status_in_order_and_drops_only_old_state_frames():
    async def go():
        ws = FakeWS()
        ws.gate.clear()                                   # the link is stalled
        link = SeatLink(ws, send_timeout=5)
        link.start()
        for i in range(300):
            link.put(state(i), True)
            if i in (60, 150, 299):
                name = {60: "paused", 150: "playing", 299: "ended"}[i]
                link.put(status(name), False)
        await asyncio.sleep(0.05)
        assert sum(1 for t in link.q if t.startswith('{"type":"state"')) <= MAX_QUEUED + 1
        ws.gate.set()
        await asyncio.sleep(0.1)
        got = [json.loads(t) for t in ws.sent]
        stat = [g["state"] for g in got if g["type"] == "status"]
        assert stat == ["paused", "playing", "ended"], stat         # none lost
        ns = [g["n"] for g in got if g["type"] == "state"]
        assert ns == sorted(ns), "state frames reordered"
        assert ns[-1] == 299, "newest frame was dropped"
        assert got[-1] == {"type": "status", "state": "ended"}      # nothing stale after the end
        link.stop()
    run(go())


def test_slow_but_alive_link_lags_at_most_the_queue_depth_and_is_not_dropped():
    async def go():
        ws = FakeWS(delay=0.02)
        link = SeatLink(ws, send_timeout=1)
        link.start()
        for i in range(120):
            link.put(state(i), True)
        await asyncio.sleep(0.2)
        assert len(link.q) <= MAX_QUEUED + 1
        assert not ws.aborted
        link.stop()
    run(go())


def test_a_send_that_never_completes_aborts_only_that_socket():
    async def go():
        a, b = FakeWS(), FakeWS()
        a.gate.clear()
        la, lb = SeatLink(a, 0.1), SeatLink(b, 0.1)
        la.start(), lb.start()
        la.put(state(1), True), lb.put(state(1), True)
        await asyncio.sleep(0.3)
        assert a.aborted and not b.aborted and b.sent
        la.stop(), lb.stop()
    run(go())


# --- reconnect racing the background close ------------------------------------------------

def test_reconnect_storm_with_one_token_ends_with_exactly_the_last_socket_seated(site):
    async def go():
        async with Rig(site) as r:
            wa, ha, wb, hb = await r.duel()
            socks = [wa]
            t0 = time.monotonic()
            for _ in range(6):
                w, first = await join(r.port, ha["token"])
                assert first["type"] == "hello"
                socks.append(w)
            assert time.monotonic() - t0 < 3
            await settle(400)
            assert r.match.connected["A"] and r.match.state == "playing"
            assert r.srv.conns["A"] is r.srv.links["A"].ws
            assert len(r.srv.links) == 2
            assert not r.match.deadline, "an old socket's close started a grace"
            await socks[-1].send(json.dumps({"type": "keys", "keys": ["d"]}))
            await settle(100)
            assert r.match.held["A"]
            await r.ticks(5)
            got = await drain(socks[-1])
            assert any(m["type"] == "state" for m in got)
            for s in socks + [wb]:
                s.transport.abort()
    run(go())


def test_new_socket_dropping_right_after_hello_while_old_is_closing_still_pauses_and_resumes(site):
    async def go():
        async with Rig(site) as r:
            wa, ha, wb, hb = await r.duel()
            w2, first = await join(r.port, ha["token"])
            w2.transport.abort()
            await settle(300)
            assert not r.match.connected["A"] and r.match.state == "paused"
            assert "A" in r.match.deadline
            w3, f3 = await join(r.port, ha["token"])
            await settle(100)
            assert f3["type"] == "hello" and r.match.state == "playing" and r.match.connected["A"]
            w3.transport.abort(), wb.transport.abort(), wa.transport.abort()
    run(go())


def test_old_socket_close_never_clears_the_new_sockets_held_keys_or_link(site):
    async def go():
        async with Rig(site) as r:
            wa, ha, wb, hb = await r.duel()
            w2, _ = await join(r.port, ha["token"])
            await w2.send(json.dumps({"type": "keys", "keys": ["d"]}))
            await settle(300)
            assert r.match.held["A"] == {"d"}
            assert r.srv.links["A"].task and not r.srv.links["A"].task.done()
            w2.transport.abort(), wa.transport.abort(), wb.transport.abort()
    run(go())


# --- keepalive in production constants --------------------------------------------------------

def test_a_silent_drop_is_noticed_in_about_six_seconds_with_the_production_constants(site):
    async def go():
        async with Rig(site) as r:
            assert (r.srv.ping_interval, r.srv.ping_timeout) == (3.0, 3.0)
            wa = Client(await websockets.connect(f"ws://127.0.0.1:{r.port}/ws", ping_interval=None))
            await wa.send(json.dumps({"type": "join"}))
            await wa.recv()
            wb, hb = await join(r.port)
            await wa.send(json.dumps({"type": "keys", "keys": ["d"]}))
            await settle(100)
            wa.transport.pause_reading()
            t0 = time.monotonic()
            while r.match.connected["A"] and time.monotonic() - t0 < 12:
                await settle(100)
            took = time.monotonic() - t0
            assert not r.match.connected["A"], "never detected"
            assert 2.5 < took < 9.0, took
            assert r.match.held["A"] == set()
            wa.transport.abort(), wb.transport.abort()
    run(go(), limit=30)


# --- Origin ---------------------------------------------------------------------------------------

async def raw_upgrade(port, headers, host=None):
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    lines = ["GET /ws HTTP/1.1"]
    if host is not None:
        lines.append(f"Host: {host}")
    lines += ["Upgrade: websocket", "Connection: Upgrade",
              "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==", "Sec-WebSocket-Version: 13"]
    lines += [f"{k}: {v}" for k, v in headers]
    writer.write(("\r\n".join(lines) + "\r\n\r\n").encode())
    try:
        data = await asyncio.wait_for(reader.read(200), 3)
    except asyncio.TimeoutError:
        data = b""
    writer.close()
    return data.split(b"\r\n", 1)[0].decode(errors="replace")


def test_origin_policy_on_the_variants_a_browser_can_send(site):
    async def go():
        async with Rig(site) as r:
            p = r.port
            ok = [
                (f"127.0.0.1:{p}", f"http://127.0.0.1:{p}"),
                (f"localhost:{p}", f"http://localhost:{p}"),
                (f"LOCALHOST:{p}", f"http://localhost:{p}"),
                (f"127.0.0.1:{p}", f"https://127.0.0.1:{p}"),
            ]
            for host, origin in ok:
                line = await raw_upgrade(p, [("Origin", origin)], host=host)
                assert " 101 " in line, (host, origin, line)
            bad = [
                (f"127.0.0.1:{p}", "http://evil.example"),
                (f"127.0.0.1:{p}", "null"),
                (f"localhost:{p}", f"http://127.0.0.1:{p}"),
                (f"127.0.0.1:{p}", f"http://user@127.0.0.1:{p}"),
                (f"127.0.0.1:{p}", f"http://127.0.0.1:{p + 1}"),
            ]
            for host, origin in bad:
                line = await raw_upgrade(p, [("Origin", origin)], host=host)
                assert " 403 " in line, (host, origin, line)
            line = await raw_upgrade(p, [], host=f"127.0.0.1:{p}")
            assert " 101 " in line
    run(go())


def test_two_origin_headers_or_a_missing_host_never_crash_the_server(site):
    async def go():
        async with Rig(site) as r:
            p = r.port
            for hdrs, host in (([("Origin", f"http://127.0.0.1:{p}"),
                                 ("Origin", "http://evil.example")], f"127.0.0.1:{p}"),
                               ([("Origin", f"http://127.0.0.1:{p}")], None)):
                line = await raw_upgrade(p, hdrs, host=host)
                assert " 101 " not in line, (hdrs, line)
            w, first = await join(p)
            assert first["type"] == "hello"
            w.transport.abort()
    run(go())


def test_the_lan_address_of_this_machine_is_accepted_when_page_and_socket_agree(site):
    from server.__main__ import lan_ip
    ip = lan_ip()
    if ip == "127.0.0.1":
        pytest.skip("no LAN address on this machine")

    async def go():
        srv = OnlineServer(Match(), site_dir=site)
        server = await srv.start("0.0.0.0", 0)
        port = server.sockets[0].getsockname()[1]
        try:
            w = await websockets.connect(f"ws://{ip}:{port}/ws",
                                         additional_headers={"Origin": f"http://{ip}:{port}"})
            await w.send(json.dumps({"type": "join"}))
            assert json.loads(await asyncio.wait_for(w.recv(), 2))["type"] == "hello"
            w.transport.abort()
        finally:
            for ws in list(srv.conns.values()):
                ws.transport.abort()
            server.close()
            await server.wait_closed()
    run(go())


# --- per-duel fallbacks ---------------------------------------------------------------------------

class Boom:
    name, kind = "boom", "scripted"

    def reset(self, seed):
        pass

    def decide(self, obs, legal):
        raise RuntimeError("boom")


def ticks(m, n, now):
    for _ in range(n):
        now += TICK_S
        m.advance(now)
    return now


def test_each_of_four_duels_logs_exactly_its_own_fallbacks_and_past_traces_do_not_change():
    m = Match(seed=2, rival="baseline", rival_budget_s=1.0)
    m.game.rival.inner.controller = Boom()
    m.join(None, 0.0)
    now = 0.0
    sizes = []
    for duel in range(4):
        now = ticks(m, 60 + 30 * duel, now)
        mine = m.trace()["fallbacks"]
        sizes.append(len(mine))
        assert all(f["source"] == "fallback" for f in mine)
        frames = [f["frame"] for f in mine]
        assert frames == sorted(frames) and frames[-1] <= m.episode.outcome()["frames"]
        assert frames[0] <= 2, "a later duel's log must start at its own frame 0"
        m.state = "ended"
        m._press_rematch("A", now)
    assert sizes[0] < sizes[1] < sizes[2] < sizes[3], sizes
    assert [len(t["fallbacks"]) for t in m.past_traces] == sizes
    assert sum(sizes) == len(m._fallbacks)


def test_fallback_log_is_per_duel_when_answers_are_late_and_the_reset_is_queued():
    class Late(Boom):
        def decide(self, obs, legal):
            time.sleep(0.05)
            return "WAIT"
    m = Match(seed=2, rival="baseline", rival_budget_s=0.001)
    m.game.rival.inner.controller = Late()
    m.join(None, 0.0)
    now = ticks(m, 40, 0.0)
    n1 = len(m.trace()["fallbacks"])
    assert n1 > 5
    m.state = "ended"
    m._press_rematch("A", now)
    now = ticks(m, 40, now)
    n2 = len(m.trace()["fallbacks"])
    assert 5 < n2 < 41
    assert len(m.past_traces[0]["fallbacks"]) == n1
    outcome, h = replay(m.trace())
    assert h == m.trace()["state_hash"]
    m.close()


# --- worker threads ---------------------------------------------------------------------------------

def _workers():
    return sum(1 for t in threading.enumerate() if t.is_alive()
               and getattr(getattr(t, "_target", None), "__name__", "") == "_work")


def test_many_lobby_resets_leave_no_rival_worker_threads_behind():
    before = _workers()
    m = Match(seed=1, rival="baseline")
    for _ in range(15):
        m.join(None, 0.0)
        m.state = "ended"
        m.connection_lost("A", 1.0)                                     # everyone left: reset lobby
    m.close()
    for _ in range(100):
        if _workers() <= before:
            break
        time.sleep(0.02)
    assert _workers() <= before, (before, _workers())


def test_rival_reset_calls_never_run_the_controller_reset_in_two_threads_at_once():
    from server.rival import TimeLimitedRival

    class Inner:
        name, kind = "x", "scripted"

        def __init__(self):
            self.inside, self.overlap = 0, False
            self.lock = threading.Lock()

        def reset(self, seed):
            with self.lock:
                self.inside += 1
                self.overlap |= self.inside > 1
            time.sleep(0.002)
            with self.lock:
                self.inside -= 1

        def __call__(self, obs, legal):
            time.sleep(0.001)
            return "WAIT"
    inner = Inner()
    rival = TimeLimitedRival(inner, budget_s=0.0005)
    for i in range(400):
        rival({}, ["WAIT"])
        rival.reset(i)
    time.sleep(0.5)
    rival.close()
    assert not inner.overlap, "two resets overlapped (tech-lead open point 1)"
