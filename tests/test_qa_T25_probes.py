"""QA probes for T25 (decisions #95 to #98): private AI rooms, lobbyView, the quiet log filter,
the loading overlay CSS, the key hints. Real localhost sockets; no network, no keys, no browser."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
NODE = shutil.which("node")
needs_node = pytest.mark.skipif(NODE is None, reason="node not installed")

websockets = pytest.importorskip("websockets")
from server import modes as smodes                          # noqa: E402
from server.app import OnlineServer, QuietUnusedConnections  # noqa: E402
from server.match import FORFEIT_GRACE_S, TICK_S, Match     # noqa: E402


def go(coro):
    return asyncio.run(asyncio.wait_for(coro, 90))


def js(expr):
    code = f"const K=require({json.dumps(str(WEB / 'keys.js'))});console.log(JSON.stringify({expr}));"
    r = subprocess.run([NODE, "-e", code], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


class Rig:
    def __init__(self):
        self.now = [100.0]
        self.made = {}
        codes = iter(["AAAA", "BBBB", "CCCC", "DDDD", "EEEE", "FFFF"])

        def factory(code, mode=None):
            self.made[code] = smodes.make_match(mode or "human", seed=0)
            return self.made[code]
        self.srv = OnlineServer(None, clock=lambda: self.now[0], match_factory=factory,
                                code_factory=lambda: next(codes))

    async def __aenter__(self):
        self.server = await self.srv.start("127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]
        return self

    async def __aexit__(self, *exc):
        self.server.close()
        await self.server.wait_closed()

    async def ticks(self, n, dt=TICK_S):
        for _ in range(n):
            self.now[0] += dt
            await self.srv.pump()
        await asyncio.sleep(0.06)


async def conn(port, first):
    ws = await websockets.connect(f"ws://127.0.0.1:{port}/ws")
    await ws.send(first if isinstance(first, str) else json.dumps(first))
    return ws, json.loads(await asyncio.wait_for(ws.recv(), 2))


async def drain(ws):
    out = []
    while True:
        try:
            out.append(json.loads(await asyncio.wait_for(ws.recv(), 0.1)))
        except (asyncio.TimeoutError, websockets.ConnectionClosed):
            return out


# ---- private AI room -------------------------------------------------------------------

@pytest.mark.parametrize("mode", ["ai", "baseline"])
def test_second_client_cannot_enter_a_private_room_by_any_route(mode):
    async def body():
        async with Rig() as r:
            wa, hello = await conn(r.port, {"type": "join", "create": True, "mode": mode})
            code, token = hello["code"], hello["token"]
            await r.ticks(3)
            attempts = [
                {"type": "join", "code": code},
                {"type": "join", "code": code.lower()},
                {"type": "join", "code": f" {code} "},
                {"type": "join", "code": code, "mode": "human"},          # forged mode
                {"type": "join", "code": code, "seat": "B"},               # forged seat
                {"type": "join", "code": code, "token": "x" * 10},         # guessed token
                {"type": "join", "code": code, "token": ""},
                {"type": "join", "code": code, "token": None},
                {"type": "join", "code": code, "token": token[:-1]},       # near miss
                {"type": "join", "code": code, "token": token + "0"},
            ]
            for a in attempts:
                ws, got = await conn(r.port, a)
                assert got["type"] == "error" and got["code"] in ("full", "bad_token"), (a, got)
                assert token not in json.dumps(got) and code not in json.dumps(got), a
                await ws.close()
            assert r.made[code].tokens.keys() == {"A"}                     # B never seated
            await r.ticks(2)
            assert r.made[code].connected == {"A": True}
            # a "create" that carries the owner's token makes a NEW room; it never seats there
            wc, h2 = await conn(r.port, {"type": "join", "create": True, "mode": mode, "token": token})
            assert h2["code"] != code and h2["token"] != token
            await wc.close()
            await wa.close()
    go(body())


def test_owner_reconnects_by_token_and_the_old_socket_is_replaced():
    async def body():
        async with Rig() as r:
            wa, hello = await conn(r.port, {"type": "join", "create": True, "mode": "ai"})
            await r.ticks(3)
            w2, h2 = await conn(r.port, {"type": "join", "code": hello["code"], "token": hello["token"]})
            assert h2["type"] == "hello" and h2["seat"] == "A" and h2["token"] == hello["token"]
            await r.ticks(5)
            assert [m for m in await drain(w2) if m["type"] == "state"]
            await w2.close()
            await wa.close()
    go(body())


def test_room_is_reaped_after_the_player_leaves_and_its_code_then_answers_no_room():
    async def body():
        async with Rig() as r:
            wa, hello = await conn(r.port, {"type": "join", "create": True, "mode": "ai"})
            code = hello["code"]
            await r.ticks(3)
            await wa.close()
            await asyncio.sleep(0.1)
            await r.ticks(1)
            assert code in r.srv.rooms                              # still inside the 15 s grace
            await r.ticks(1, dt=FORFEIT_GRACE_S + 1)
            assert code not in r.srv.rooms
            ws, got = await conn(r.port, {"type": "join", "code": code, "token": hello["token"]})
            assert got["type"] == "error" and got["code"] == "no_room"
            await ws.close()
    go(body())


def test_ai_room_messages_carry_only_the_owners_payload():
    async def body():
        async with Rig() as r:
            wa, hello = await conn(r.port, {"type": "join", "create": True, "mode": "ai"})
            await r.ticks(10)
            msgs = [hello] + await drain(wa)
            assert set(hello) == {"type", "seat", "token", "rival", "code"}
            wire = json.dumps(msgs[1:]).lower()
            for w in ("seed", "token", hello["token"].lower(), '"code"', "ppo", "fallback", "weights"):
                assert w not in wire, w
            assert {m["type"] for m in msgs[1:]} <= {"state", "status"}
            assert all(m.get("seat", "A") == "A" for m in msgs)
            await wa.close()
    go(body())


def test_rematch_in_a_private_room_is_one_press():
    async def body():
        async with Rig() as r:
            wa, _ = await conn(r.port, {"type": "join", "create": True, "mode": "baseline"})
            await r.ticks(3)
            m = r.made["AAAA"]
            m.episode._duel.terminal = "won:B"
            await r.ticks(3)
            assert m.state == "ended"
            await wa.send(json.dumps({"type": "rematch"}))
            await asyncio.sleep(0.1)
            await r.ticks(3)
            assert m.state == "playing"
            await wa.close()
    go(body())


def test_human_room_still_gives_code_and_a_second_seat():
    async def body():
        async with Rig() as r:
            wa, h = await conn(r.port, {"type": "join", "create": True, "mode": "human"})
            assert h["code"] and h["seat"] == "A"
            wb, hb = await conn(r.port, {"type": "join", "code": h["code"]})
            assert hb["type"] == "hello" and hb["seat"] == "B"
            await wa.close()
            await wb.close()
    go(body())


# ---- lobbyView ----------------------------------------------------------------------------

@needs_node
@pytest.mark.parametrize("arg, want", [
    ('"ai"', (True, False, False)), ('"baseline"', (True, False, False)),
    ('"human"', (False, True, True)), ("null", (False, False, False)), ("undefined", (False, False, False)),
    ('"AI"', (False, False, False)), ('"Human"', (False, False, False)), ('""', (False, False, False)),
    ("0", (False, False, False)), ('["ai"]', (False, False, False)), ("{}", (False, False, False)),
    ('"__proto__"', (False, False, False)), ('"ai "', (False, False, False)),
])
def test_lobby_view_all_modes_and_bad_inputs(arg, want):
    v = js(f"K.lobbyView({arg})")
    assert (v["startsAtOnce"], v["showCreateJoin"], v["showCode"]) == want
    assert not (v["startsAtOnce"] and (v["showCreateJoin"] or v["showCode"]))   # never both


@needs_node
def test_lobby_view_with_no_argument_does_not_throw():
    assert js("K.lobbyView()")["startsAtOnce"] is False


# ---- the quiet filter ----------------------------------------------------------------------

def _raw(port, payload: bytes, wait=0.4):
    async def go_():
        r, w = await asyncio.open_connection("127.0.0.1", port)
        w.write(payload)
        await w.drain()
        await asyncio.sleep(wait)
        w.close()
    return go_()


def _errors(caplog):
    return [x for x in caplog.records if x.name == "server.ws" and x.levelno >= logging.ERROR]


@pytest.mark.parametrize("payload, label", [
    (b"garbage not http\r\n\r\n", "malformed"),
    (b"GET / HTTP/1.1\r\nHost: x\r\nX: " + b"a" * 20000 + b"\r\n\r\n", "oversized header"),
    (b"GET / HTTP/1.1\r\n" + b"X-A: b\r\n" * 500 + b"\r\n", "too many headers"),
    (b"GET /ws HTTP/1.1\r\nHost: x\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
     b"Sec-WebSocket-Key: !!!\r\nSec-WebSocket-Version: 13\r\n\r\n", "bad key"),
])
def test_malformed_or_oversized_requests_are_not_quieted(caplog, payload, label):
    caplog.set_level(logging.DEBUG)

    async def body():
        srv = OnlineServer(Match())
        server = await srv.start("127.0.0.1", 0)
        await _raw(server.sockets[0].getsockname()[1], payload)
        server.close()
        await server.wait_closed()
    go(body())
    recs = [x for x in caplog.records if x.name == "server.ws"]
    loud = [x for x in recs if x.levelno >= logging.ERROR]
    assert loud, (label, [(x.levelname, x.getMessage()) for x in recs])
    assert any(x.exc_info for x in loud), label


def test_server_side_exception_in_http_hook_still_error_with_traceback(caplog):
    caplog.set_level(logging.DEBUG)

    async def body():
        srv = OnlineServer(Match())

        def boom(connection, request):
            raise ValueError("bug")
        srv._http = boom
        server = await srv.start("127.0.0.1", 0)
        await _raw(server.sockets[0].getsockname()[1], b"GET / HTTP/1.1\r\nHost: x\r\n\r\n")
        server.close()
        await server.wait_closed()
    go(body())
    loud = _errors(caplog)
    assert loud and loud[0].exc_info and loud[0].exc_info[0] is ValueError


def test_empty_and_half_request_connections_are_quiet(caplog):
    caplog.set_level(logging.DEBUG)

    async def body():
        srv = OnlineServer(Match())
        server = await srv.start("127.0.0.1", 0)
        p = server.sockets[0].getsockname()[1]
        await _raw(p, b"", 0.1)
        await _raw(p, b"GET / HT", 0.1)                 # closed mid request line
        server.close()
        await server.wait_closed()
    go(body())
    assert not _errors(caplog)


def test_filter_unit_only_rewrites_benign_chains():
    from websockets.exceptions import InvalidMessage
    f = QuietUnusedConnections()

    def rec(exc):
        try:
            raise exc
        except BaseException:
            return logging.LogRecord("server.ws", logging.ERROR, "x", 1, "opening handshake failed",
                                     (), sys.exc_info())
    benign = InvalidMessage("did not receive a valid HTTP request")
    benign.__cause__ = EOFError("connection closed while reading HTTP request line")
    r = rec(benign)
    f.filter(r)
    assert r.levelno == logging.INFO and r.exc_info is None
    bad = InvalidMessage("x")
    bad.__cause__ = ValueError("bad")
    r = rec(bad)
    f.filter(r)
    assert r.levelno == logging.ERROR and r.exc_info
    r = rec(RuntimeError("bug"))
    f.filter(r)
    assert r.levelno == logging.ERROR and r.exc_info
    other = logging.LogRecord("server.ws", logging.ERROR, "x", 1, "some other error", (), None)
    f.filter(other)
    assert other.levelno == logging.ERROR


def test_bad_origin_is_refused_403():
    async def body():
        srv = OnlineServer(Match())
        server = await srv.start("127.0.0.1", 0)
        p = server.sockets[0].getsockname()[1]
        r, w = await asyncio.open_connection("127.0.0.1", p)
        w.write(b"GET /ws HTTP/1.1\r\nHost: 127.0.0.1\r\nOrigin: http://evil.example\r\n"
                b"Upgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
                b"Sec-WebSocket-Version: 13\r\n\r\n")
        await w.drain()
        data = await asyncio.wait_for(r.read(200), 3)
        w.close()
        server.close()
        await server.wait_closed()
        return data
    assert b" 403 " in go(body()).split(b"\r\n")[0]


# ---- centring and hints ----------------------------------------------------------------

def test_overlay_css_only_for_the_loading_state():
    html = (WEB / "online.html").read_text()
    css = html.split("<style>")[1].split("</style>")[0]
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    rules = re.findall(r"([^{}]*)\{([^{}]*)\}", css)
    fixed = [sel.strip() for sel, body in rules if "position: fixed" in body]
    assert fixed == ['#status[data-state="loading"]'], fixed


@needs_node
@pytest.mark.parametrize("seat, own, other", [("A", " S kneel", " Down kneel"), ("B", " Down kneel", " S kneel")])
@pytest.mark.parametrize("mode", ["human_vs_ai", "online", None])
def test_hints_match_the_seat(seat, own, other, mode):
    h = js(f'K.keyHints({json.dumps(mode)}, "{seat}")')
    assert own in h and other not in h
    assert "sheathe" in h and "sword or uniform" in h


@needs_node
def test_local_two_players_names_both_kneel_keys_once_each():
    h = js('K.keyHints("local_two_players", "A")')
    assert h.count(" S kneel") == 1 and h.count(" Down kneel") == 1
