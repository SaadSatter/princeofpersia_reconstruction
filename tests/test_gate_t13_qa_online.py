"""GATE-T13 QA: adversarial clients against the online server (real localhost sockets).

Only 127.0.0.1, a fake clock (`Rig.now`), and a few ms of real socket time. The
two reproduced defects are `xfail(strict=True)` so the suite stays green and the
finding flips loudly when the Tech Lead fixes it:
  T13-QA-1  a client that stops reading freezes the tick loop for the other seat.
  T13-QA-2  a seat can be left "connected" with a dead socket (no pause, no forfeit).
Needs the `online` extra (skipped without it).
"""

from __future__ import annotations

import asyncio
import json
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

websockets = pytest.importorskip("websockets")

from server.app import OnlineServer                                   # noqa: E402
from server.match import FORFEIT_GRACE_S, Match, TICK_S                # noqa: E402
from server.trace import replay                                       # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    from tools.web import build
    out = tmp_path_factory.mktemp("qa_site")
    build.build(out)
    return out


def run(coro, limit=90):
    return asyncio.run(asyncio.wait_for(coro, limit))


async def settle(ms: int = 80):
    await asyncio.sleep(ms / 1000)


class Client:
    """A scripted browser: always reading, so a slow test never backs up the server.
    `recv()` and `drain()` read what arrived; `transport` is the raw socket."""

    def __init__(self, ws):
        self.ws = ws
        self.q: asyncio.Queue = asyncio.Queue()
        self.closed: Exception | None = None
        self.task = asyncio.create_task(self._pump())

    async def _pump(self):
        try:
            async for m in self.ws:
                self.q.put_nowait(m)
        except Exception as e:                      # noqa: BLE001
            self.closed = e
        else:
            self.closed = self.ws.protocol.close_exc
        self.q.put_nowait(None)

    async def recv(self):
        m = await self.q.get()
        if m is None:
            self.q.put_nowait(None)
            raise self.closed if isinstance(self.closed, websockets.ConnectionClosed) \
                else websockets.ConnectionClosed(None, None)
        return m

    async def send(self, m):
        await self.ws.send(m)

    @property
    def transport(self):
        return self.ws.transport

    @property
    def state(self):
        return self.ws.state


async def drain(ws, wait: float = 0.1) -> list[dict]:
    out = []
    while True:
        try:
            out.append(json.loads(await asyncio.wait_for(ws.recv(), wait)))
        except (asyncio.TimeoutError, websockets.ConnectionClosed):
            return out


async def join(port, token=None):
    ws = Client(await websockets.connect(f"ws://127.0.0.1:{port}/ws"))
    await ws.send(json.dumps({"type": "join", **({"token": token} if token else {})}))
    first = json.loads(await asyncio.wait_for(ws.recv(), 2))
    return ws, first


class Rig:
    def __init__(self, site_dir, **match_kw):
        self.now = [100.0]
        self.match = Match(**match_kw)
        self.srv = OnlineServer(self.match, clock=lambda: self.now[0], site_dir=site_dir)

    async def __aenter__(self):
        self.server = await self.srv.start("127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]
        return self

    async def __aexit__(self, *exc):
        for ws in list(self.srv.conns.values()):                      # a failed assert must not hang
            ws.transport.abort()
        self.server.close()
        await self.server.wait_closed()

    async def ticks(self, n):
        for _ in range(n):
            self.now[0] += TICK_S
            await self.srv.pump()
        await settle()

    async def seconds(self, s):
        self.now[0] += s
        await self.srv.pump()
        await settle()

    async def duel(self):
        """Two joined clients, drained, ready."""
        wa, ha = await join(self.port)
        wb, hb = await join(self.port)
        await settle()
        await drain(wa), await drain(wb)
        return wa, ha, wb, hb


def frame(r):
    return r.match.episode.outcome()["frames"]


# --- joining ---------------------------------------------------------------------

def test_idle_sockets_that_never_join_do_not_take_a_seat(site):
    async def go():
        async with Rig(site) as r:
            idle = [Client(await websockets.connect(f"ws://127.0.0.1:{r.port}/ws")) for _ in range(5)]
            wa, ha, wb, hb = await r.duel()
            assert (ha["seat"], hb["seat"]) == ("A", "B")
            for w in idle + [wa, wb]:
                w.transport.abort()
    run(go())


def test_the_first_frame_must_be_a_join_and_a_second_join_is_ignored(site):
    async def go():
        async with Rig(site) as r:
            early = Client(await websockets.connect(f"ws://127.0.0.1:{r.port}/ws"))
            await early.send(json.dumps({"type": "keys", "keys": ["d"]}))
            with pytest.raises(websockets.ConnectionClosed):
                await asyncio.wait_for(early.recv(), 2)
            assert r.match.tokens == {}
            wa, ha, wb, hb = await r.duel()
            await wa.send(json.dumps({"type": "join"}))                       # again: ignored
            await wa.send(json.dumps({"type": "join", "token": hb["token"]}))  # B's token: ignored
            await settle()
            await r.ticks(3)
            assert set(r.match.tokens) == {"A", "B"} and r.match.state == "playing"
            wa.transport.abort(), wb.transport.abort()
    run(go())


def test_a_token_is_bound_to_its_own_seat_and_cannot_be_used_for_the_other(site):
    async def go():
        async with Rig(site) as r:
            wa, ha, wb, hb = await r.duel()
            wa.transport.abort()
            await settle()
            assert r.match.state == "paused"
            # B's token always means seat B; A's always seat A. A forged or cut token is refused.
            for bad in (ha["token"][:-1], ha["token"] + "x", ha["token"].upper(), "A", "B", " ",
                        hb["token"][::-1], "0" * 40, "x" * 300):
                w, first = await join(r.port, bad)
                assert first["type"] == "error" and first["code"] == "bad_token", bad[:20]
                w.transport.abort()
            long_ws = Client(await websockets.connect(f"ws://127.0.0.1:{r.port}/ws"))
            await long_ws.send(json.dumps({"type": "join", "token": "x" * 5000}))   # over 512: refused
            with pytest.raises(websockets.ConnectionClosed):
                await asyncio.wait_for(long_ws.recv(), 2)
            assert r.match.state == "paused" and r.match.connected["A"] is False
            w2, first = await join(r.port, ha["token"])
            assert (first["type"], first["seat"]) == ("hello", "A")
            w2.transport.abort(), wb.transport.abort()
    run(go())


def test_seat_b_cannot_move_seat_a_by_naming_it(site):
    async def go():
        async with Rig(site) as r:
            wa, ha, wb, hb = await r.duel()
            a0 = r.match.episode.observe("A")["me"]["col"]
            for msg in ({"type": "keys", "seat": "A", "keys": ["d"]},
                        {"type": "keys", "keys": ["d", "a", "w"]},        # A's names
                        {"type": "keys", "keys": [["d"], {"d": 1}, None, 7]},
                        {"type": "input", "seat": "A", "action": "RIGHT"},
                        {"type": "outcome", "result": "won"}, {"type": "state", "seat": "A"}):
                await wb.send(json.dumps(msg))
            await settle()
            await r.ticks(36)
            assert r.match.episode.observe("A")["me"]["col"] == a0
            assert r.match.episode.outcome()["status"] != "terminal"
            wa.transport.abort(), wb.transport.abort()
    run(go())


# --- malformed, oversize, flooding ----------------------------------------------------

def test_malformed_binary_and_odd_json_frames_are_ignored_and_play_goes_on(site):
    async def go():
        async with Rig(site) as r:
            wa, ha, wb, hb = await r.duel()
            junk = [b"\x00\xff\xfe", b"", "", "{", "null", "[]", "7", '"keys"', "[[[[[[[[[[[[[[[[[[[[[[[[",
                    '{"type":"keys","keys":"d"}', '{"type":"keys","keys":' + "[" + ",".join(['"d"'] * 40) + "]}",
                    '{"type":"keys"}', '{"type":null}', '{"type":["keys"]}', '{"seat":"B"}',
                    '{"type":"keys","keys":["d"],"seat":["B"]}', "9" * 5000, '{"a":' + "1" * 5000 + "}",
                    "{\"type\":\"rematch\"}", '{"type":"rematch","seat":"B"}',
                    "x" * 513, json.dumps({"type": "keys", "keys": ["d"], "pad": "z" * 600})]
            for j in junk:
                await wa.send(j)
            await settle()
            assert r.match.state == "playing" and r.match.connected == {"A": True, "B": True}
            held = set(r.match.held["A"])
            assert held <= {"a", "d", "w", "s", "f", "g", "t", "lshift"}
            await wa.send(json.dumps({"type": "keys", "keys": ["d"]}))
            await settle()
            f0 = frame(r)
            await r.ticks(24)
            assert frame(r) == f0 + 24
            assert [m for m in await drain(wb) if m["type"] == "state"]
            wa.transport.abort(), wb.transport.abort()
    run(go())


def test_a_two_megabyte_frame_drops_only_its_sender_and_the_pause_rule_applies(site):
    async def go():
        async with Rig(site) as r:
            wa, ha, wb, hb = await r.duel()
            await r.ticks(5)
            await wa.send("x" * (2 * 1024 * 1024))
            with pytest.raises(websockets.ConnectionClosed) as ei:
                while True:                                           # queued states first
                    await asyncio.wait_for(wa.recv(), 3)
            assert ei.value.rcvd is not None and ei.value.rcvd.code == 1009
            await settle()
            assert r.match.state == "paused" and r.match.connected["B"] is True
            f0 = frame(r)
            await r.seconds(3)
            assert frame(r) == f0                                     # paused: no ticks
            mb = await drain(wb)
            assert any(m["type"] == "status" and m["state"] == "paused" for m in mb)
            wa2, first = await join(r.port, ha["token"])
            assert first["seat"] == "A"
            await r.ticks(2)
            assert r.match.state == "playing" and frame(r) == f0 + 2
            wa2.transport.abort(), wb.transport.abort()
    run(go())


def test_flooding_with_keys_and_rematch_and_join_messages_is_cheap_and_harmless(site):
    async def go():
        async with Rig(site) as r:
            wa, ha, wb, hb = await r.duel()
            t0 = time.monotonic()
            for i in range(4000):
                await wa.send(json.dumps({"type": "keys", "keys": ["d"] if i % 2 else ["a"]}))
                if i % 4 == 0:
                    await wa.send('{"type":"rematch"}')
                    await wa.send('{"type":"join"}')
            await settle(300)
            assert time.monotonic() - t0 < 20
            await r.ticks(12)
            assert r.match.state == "playing"                         # rematch during play is a no-op
            assert r.match.rematch_pressed == set()
            assert [m for m in await drain(wb) if m["type"] == "state"]
            wa.transport.abort(), wb.transport.abort()
    run(go())


# --- reconnect races ----------------------------------------------------------------

def test_two_sockets_with_one_token_the_newer_wins_and_the_older_is_told_replaced(site):
    async def go():
        async with Rig(site) as r:
            wa, ha, wb, hb = await r.duel()
            wa2, first = await join(r.port, ha["token"])
            assert first["seat"] == "A" and first["token"] == ha["token"]
            await settle()
            with pytest.raises(websockets.ConnectionClosed) as ei:
                while True:
                    await asyncio.wait_for(wa.recv(), 3)
            assert ei.value.rcvd is not None and ei.value.rcvd.code == 1000
            assert ei.value.rcvd.reason == "replaced"
            # the replaced socket's death must not pause the duel
            await settle(200)
            assert r.match.state == "playing" and r.match.connected["A"] is True
            # old socket is dead: nothing it could send counts; the new one moves A
            a0 = r.match.episode.observe("A")["me"]["col"]
            await wa2.send(json.dumps({"type": "keys", "keys": ["d"]}))
            await settle()
            await r.ticks(30)
            assert r.match.episode.observe("A")["me"]["col"] != a0
            wa2.transport.abort(), wb.transport.abort()
    run(go())


def test_reconnect_from_a_second_tab_in_the_window_resumes_on_the_same_frame(site):
    async def go():
        async with Rig(site) as r:
            wa, ha, wb, hb = await r.duel()
            await r.ticks(10)
            f0 = frame(r)
            wa.transport.abort()
            await settle()
            assert r.match.state == "paused"
            await r.seconds(FORFEIT_GRACE_S - 3)
            assert frame(r) == f0 and r.match.state == "paused"
            wa2, first = await join(r.port, ha["token"])              # the other tab
            await settle()
            assert r.match.state == "playing" and frame(r) == f0
            ms = await drain(wa2)
            assert any(m["type"] == "state" for m in ms)              # gets the current picture
            await r.seconds(FORFEIT_GRACE_S + 5)                      # the old deadline passes
            assert r.match.forfeit is None and r.match.state == "playing"
            assert frame(r) > f0
            wa2.transport.abort(), wb.transport.abort()
    run(go())


def test_just_inside_the_window_resumes_and_at_the_deadline_forfeits(site):
    async def go():
        async with Rig(site) as r:
            wa, ha, wb, hb = await r.duel()
            wa.transport.abort()
            await settle()
            await r.seconds(FORFEIT_GRACE_S - 0.5)
            assert r.match.state == "paused"
            w2, _ = await join(r.port, ha["token"])
            assert r.match.state == "playing"
            w2.transport.abort()
            await settle()
            assert r.match.state == "paused"                         # a fresh 15 s, not the old one
            await r.seconds(FORFEIT_GRACE_S - 0.5)
            assert r.match.state == "paused"
            await r.seconds(1.0)
            assert r.match.state == "ended" and r.match.forfeit == "A"
            wb.transport.abort()
    run(go())


def test_reconnect_just_after_the_forfeit_gets_the_end_screen_and_can_rematch(site):
    async def go():
        async with Rig(site, seed=7) as r:
            wa, ha, wb, hb = await r.duel()
            wa.transport.abort()
            await settle()
            await r.seconds(FORFEIT_GRACE_S + 0.1)
            assert r.match.state == "ended"
            mb = await drain(wb)
            end_b = [m for m in mb if m["type"] == "state"][-1]["outcome"]
            assert (end_b["reason"], end_b["result"]) == ("rival_disconnected", "won")
            wa2, first = await join(r.port, ha["token"])              # late
            assert first["seat"] == "A"
            ma = await drain(wa2)
            end_a = [m for m in ma if m["type"] == "state"][-1]["outcome"]
            assert (end_a["reason"], end_a["result"]) == ("you_disconnected", "lost")
            assert any(m["type"] == "status" and m["state"] == "ended" for m in ma)
            await wb.send('{"type":"rematch"}')
            await settle()
            assert r.match.state == "ended"
            await wa2.send('{"type":"rematch"}')
            await settle()
            assert r.match.state == "playing" and r.match.seed == 7 and r.match.forfeit is None
            assert frame(r) == 0
            wa2.transport.abort(), wb.transport.abort()
    run(go())


def test_a_third_client_cannot_take_a_paused_seat(site):
    async def go():
        async with Rig(site) as r:
            wa, ha, wb, hb = await r.duel()
            wa.transport.abort()
            await settle()
            w3, first = await join(r.port)
            assert first["type"] == "error" and first["code"] == "full"
            assert r.match.connected["A"] is False and "A" in r.match.tokens
            wb.transport.abort()
    run(go())


def test_both_seats_dropping_the_earlier_deadline_forfeits_and_a_late_return_is_safe(site):
    async def go():
        async with Rig(site) as r:
            wa, ha, wb, hb = await r.duel()
            wa.transport.abort()
            await settle()
            await r.seconds(5)
            wb.transport.abort()
            await settle()
            await r.seconds(FORFEIT_GRACE_S - 5 + 0.1)                # A's deadline
            assert r.match.state == "ended" and r.match.forfeit == "A"
            wb2, first = await join(r.port, hb["token"])
            assert first["seat"] == "B"
            mb = await drain(wb2)
            out = [m for m in mb if m["type"] == "state"][-1]["outcome"]
            assert out["result"] == "won"
            wb2.transport.abort()
            await settle()
            # B left; A never returned: lobby resets, old tokens are void, a fresh pair can play
            assert r.match.state == "waiting" or not any(r.match.connected.values())
            w, first = await join(r.port, ha["token"])
            assert first["type"] in ("error", "hello")
            w.transport.abort()
    run(go())


# --- closing during a rematch ---------------------------------------------------------

def test_closing_during_a_rematch_clears_that_press_and_leaks_nothing(site):
    async def go():
        async with Rig(site, seed=3) as r:
            wa, ha, wb, hb = await r.duel()
            wb.transport.abort()
            await settle()
            await r.seconds(FORFEIT_GRACE_S + 0.1)
            assert r.match.state == "ended"
            wb2, _ = await join(r.port, hb["token"])
            await settle()
            await drain(wa), await drain(wb2)
            await wa.send('{"type":"rematch"}')
            await settle()
            mb = await drain(wb2)
            assert any(m["type"] == "status" and m["rematch"] == "rival_wants" for m in mb)
            wa.transport.abort()                                       # presser leaves
            await settle()
            assert "A" not in r.match.rematch_pressed
            await wb2.send('{"type":"rematch"}')                       # B presses alone
            await settle()
            assert r.match.state == "ended"                            # not restarted
            mb = await drain(wb2)
            st = [m for m in mb if m["type"] == "status"][-1]
            assert st["rematch"] == "waiting"                          # and A's old press is gone
            wa2, _ = await join(r.port, ha["token"])
            await settle()
            await wa2.send('{"type":"rematch"}')
            await settle()
            assert r.match.state == "playing" and frame(r) == 0 and r.match.seed == 3
            wa2.transport.abort(), wb2.transport.abort()
    run(go())


def test_both_leave_after_the_end_resets_the_lobby_and_the_same_seed_is_kept(site):
    async def go():
        async with Rig(site, seed=11) as r:
            wa, ha, wb, hb = await r.duel()
            wa.transport.abort()
            await settle()
            await r.seconds(FORFEIT_GRACE_S + 0.1)
            wb.transport.abort()
            await settle()
            assert r.match.state == "waiting" and r.match.tokens == {}
            w1, f1 = await join(r.port)
            w2, f2 = await join(r.port)
            assert (f1["seat"], f2["seat"]) == ("A", "B") and f1["token"] != ha["token"]
            assert r.match.seed == 11
            w1.transport.abort(), w2.transport.abort()
    run(go())


# --- statuses and messages do not depend on hidden state ----------------------------

def test_pause_and_resume_messages_are_the_same_whatever_the_rival_is_doing(site):
    async def script(r, keys_a):
        wa, ha, wb, hb = await r.duel()
        await wa.send(json.dumps({"type": "keys", "keys": keys_a}))
        await settle()
        await r.ticks(30)
        await drain(wb)
        wa.transport.abort()
        await settle()
        await r.seconds(4)
        wa2, _ = await join(r.port, ha["token"])
        await settle()
        statuses = [m for m in await drain(wb) if m["type"] == "status"]
        wa2.transport.abort(), wb.transport.abort()
        return statuses

    async def go():
        out = []
        for keys in ([], ["d"], ["t"], ["lshift", "d"]):
            async with Rig(site, seed=5) as r:
                out.append(await script(r, keys))
        assert all(o == out[0] for o in out), out
        assert {m["text"] for m in out[0]} <= {"", "Rival disconnected, waiting up to 15 s"}
    run(go())


def test_nothing_sent_to_a_client_names_the_seed_the_other_token_or_connections(site):
    async def go():
        async with Rig(site, seed=424242) as r:
            wa, ha, wb, hb = await r.duel()
            await wb.send(json.dumps({"type": "keys", "keys": ["right", "up"]}))
            await settle()
            await r.ticks(60)
            wb.transport.abort()
            await settle()
            await r.seconds(5)
            wb2, _ = await join(r.port, hb["token"])
            await r.ticks(10)
            allmsg = json.dumps(await drain(wa))
            for banned in (hb["token"], "424242", "seed", "127.0.0.1", "token", "owner",
                           "trap_owner", "rng", "script"):
                assert banned not in allmsg, banned
            wa.transport.abort(), wb2.transport.abort()
    run(go())


# --- authority + determinism under stress -----------------------------------------------

def test_trace_of_an_adversarial_duel_with_pauses_and_rematch_replays_exactly(site):
    async def go():
        async with Rig(site, seed=9) as r:
            wa, ha, wb, hb = await r.duel()
            await wa.send(json.dumps({"type": "keys", "keys": ["d", "lshift"]}))
            await wb.send(json.dumps({"type": "keys", "keys": ["left", "rshift", "a"]}))
            await settle()
            await r.ticks(40)
            wa.transport.abort()
            await settle()
            await r.seconds(6)
            wa2, _ = await join(r.port, ha["token"])
            await wa2.send("x" * 100)
            await wa2.send(json.dumps({"type": "keys", "keys": ["g", "f"]}))
            await settle()
            await r.ticks(60)
            tr = r.match.trace()
            outcome, h = replay(tr)
            assert h == tr["state_hash"] and outcome == tr["outcome"]
            assert tr["seed"] == 9 and tr["forfeit"] is None
            wa2.transport.abort(), wb.transport.abort()
    run(go())


def test_ai_seat_with_every_answer_late_still_replays_and_logs_fallbacks_server_side():
    m = Match(seed=2, rival="baseline", rival_budget_s=0.0)
    m.join(None, 0.0)
    t = 0.0
    m.receive("A", json.dumps({"type": "keys", "keys": ["d"]}), t)
    for _ in range(150):
        t += TICK_S
        m.advance(t)
    tr = m.trace()
    assert len(tr["ticks"]) >= 30 and tr["fallbacks"], tr["fallbacks"][:2]
    outcome, h = replay(tr)
    assert h == tr["state_hash"] and outcome == tr["outcome"]
    sent = json.dumps(m.drain("A"))
    hits = [w for w in ("fallback", "slow_answer", "controller_failed", "budget") if w in sent]
    assert not hits, hits
    labels = {m["rival"] for m in json.loads(sent) if m["type"] == "state"}
    assert labels == {"AI rival: versus-baseline (scripted)"}          # static, whatever the fallbacks


def test_a_second_human_is_refused_when_the_server_plays_seat_b():
    m = Match(seed=1, rival="baseline")
    assert m.join(None, 0.0)["ok"]
    assert m.join(None, 0.0) == {"ok": False, "code": "full"}


# --- HTTP surface -----------------------------------------------------------------------

def _http(port, raw: bytes) -> bytes:
    s = socket.create_connection(("127.0.0.1", port), timeout=3)
    try:
        s.sendall(raw)
        buf = b""
        while True:
            try:
                d = s.recv(65536)
            except socket.timeout:
                break
            if not d:
                break
            buf += d
        return buf
    finally:
        s.close()


def test_http_serves_only_the_allow_list_and_never_source_or_the_engine(site):
    async def go():
        async with Rig(site) as r:
            loop = asyncio.get_running_loop()
            paths = ["/server/app.py", "/pop/versus.py", "/game.zip", "/web/bridge.py", "/main.js",
                     "/index.html", "/../pyproject.toml", "/art/../online.html/../../x",
                     "/%2e%2e/pyproject.toml", "/art/%2e%2e/game.zip", "/art/", "/art",
                     "//etc/passwd", "/ws", "/online.html/", "/.git/config", "/traces/online/"]
            for p in paths:
                body = await loop.run_in_executor(
                    None, _http, r.port, f"GET {p} HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n".encode())
                head = body.split(b"\r\n", 1)[0]
                assert b" 404 " in head or b" 400 " in head or b" 426 " in head, (p, head)
                assert b"def " not in body and b"import " not in body, p
            for p in ("/", "/online.html", "/online.js", "/draw.js", "/ui.js", "/keys.js", "/manifest.json"):
                body = await loop.run_in_executor(
                    None, _http, r.port, f"GET {p} HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n".encode())
                assert b" 200 " in body.split(b"\r\n", 1)[0], p
            # odd verbs and a huge header: no crash, server still serves afterwards
            for raw in (b"POST / HTTP/1.1\r\nHost: x\r\nContent-Length: 3\r\n\r\nabc",
                        b"GET / HTTP/1.1\r\nHost: x\r\nX: " + b"a" * 70000 + b"\r\n\r\n",
                        b"\x00\x01\x02garbage\r\n\r\n", b"GET /\r\n\r\n"):
                await loop.run_in_executor(None, _http, r.port, raw)
            body = await loop.run_in_executor(
                None, _http, r.port, b"GET / HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n")
            assert b" 200 " in body.split(b"\r\n", 1)[0]
            wa, ha, wb, hb = await r.duel()
            wa.transport.abort(), wb.transport.abort()
    run(go())


# --- the two reproduced defects ---------------------------------------------------------

def test_a_client_that_stops_reading_must_not_freeze_the_other_seat(site):
    async def go():
        async with Rig(site) as r:
            wa, ha, wb, hb = await r.duel()
            wa.transport.pause_reading()                               # A: half-open / very slow
            try:
                for _ in range(1500):                                  # about two minutes of play
                    r.now[0] += TICK_S
                    await asyncio.wait_for(r.srv.pump(), 2)            # one stalled pump is the defect
                    await asyncio.sleep(0)
            finally:
                wa.transport.abort(), wb.transport.abort()
    run(go(), 120)


def test_a_seat_whose_socket_died_during_join_must_not_stay_connected(site):
    async def go():
        async with Rig(site) as r:
            wa, ha, wb, hb = await r.duel()
            wa.transport.pause_reading()                               # old socket never answers the close
            wa2 = await websockets.connect(f"ws://127.0.0.1:{r.port}/ws")     # raw: no reader
            await wa2.send(json.dumps({"type": "join", "token": ha["token"]}))
            await settle(200)                                          # server now awaits old.close()
            wa2.transport.abort()                                      # the new socket dies first
            await settle()
            wa.transport.abort()                                       # old.close() returns, hello fails
            await settle(300)
            alive = r.srv.conns.get("A")
            assert not (r.match.connected["A"] and (alive is None or alive.state.name == "CLOSED")), \
                "seat A is marked connected but its socket is closed: no pause, no forfeit"
            wb.transport.abort()
    run(go())


# --- real process: CLI, real clock, traces dir --------------------------------------------

def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


@pytest.mark.parametrize("rival", ["none", "baseline"])
def test_cli_process_two_scripted_clients_real_clock_and_trace_dir(tmp_path, rival):
    port = _free_port()
    trace_dir = tmp_path / "traces"
    proc = subprocess.Popen(
        [sys.executable, "-m", "server", "--host", "127.0.0.1", "--port", str(port),
         "--rival", rival, "--seed", "4", "--trace-dir", str(trace_dir)],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    async def go():
        for _ in range(100):
            try:
                socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
                break
            except OSError:
                await asyncio.sleep(0.1)
        else:
            raise AssertionError("server did not start")
        wa, ha = await join(port)
        assert ha["seat"] == "A"
        wb = None
        if rival == "none":
            wb, hb = await join(port)
            assert hb["seat"] == "B"
        w3, h3 = await join(port)
        assert h3["code"] == "full"
        await wa.send(json.dumps({"type": "keys", "keys": ["d"]}))
        ms = []
        end = time.monotonic() + 2.5
        while time.monotonic() < end:                                # real time: messages never stop
            try:
                ms.append(json.loads(await asyncio.wait_for(wa.recv(), 0.5)))
            except asyncio.TimeoutError:
                pass
        states = [m for m in ms if m["type"] == "state"]
        assert 20 <= len(states) <= 45, len(states)                  # about 12 per second
        cols = [m["seat_view"]["me"]["col"] for m in states if "seat_view" in m]
        assert cols and cols[-1] != cols[0]
        blob = json.dumps(ms)
        assert "fallback" not in blob and "seed" not in blob
        if rival == "baseline":
            assert any("AI rival" in str(m.get("rival")) for m in states)
        wa.transport.abort()
        if wb:
            wb.transport.abort()

    try:
        asyncio.run(asyncio.wait_for(go(), 40))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    assert proc.poll() is not None
