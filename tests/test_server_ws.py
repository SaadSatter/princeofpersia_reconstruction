"""T13: the server over real WebSockets on localhost, with an injected clock.

The clock is a list the test moves; `OnlineServer.pump()` is the one step the
tick loop repeats, so nothing here waits for wall time except a few ms of
socket delivery. Needs the `online` extra (skipped without it).
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

websockets = pytest.importorskip("websockets")

from server.app import OnlineServer           # noqa: E402
from server.match import FORFEIT_GRACE_S, Match, TICK_S   # noqa: E402

SITE = None


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    from tools.web import build
    out = tmp_path_factory.mktemp("site")
    build.build(out)
    return out


def run(coro):
    return asyncio.run(asyncio.wait_for(coro, 60))


async def settle(ms: int = 60):
    await asyncio.sleep(ms / 1000)


async def drain(ws) -> list[dict]:
    out = []
    while True:
        try:
            out.append(json.loads(await asyncio.wait_for(ws.recv(), 0.1)))
        except asyncio.TimeoutError:
            return out


async def join(port, token=None):
    ws = await websockets.connect(f"ws://127.0.0.1:{port}/ws")
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
        self.server.close()
        await self.server.wait_closed()

    async def ticks(self, n):
        for _ in range(n):
            self.now[0] += TICK_S
            await self.srv.pump()
        await settle()


def test_two_clients_get_two_seats_a_third_is_told_full_and_closed(site):
    async def go():
        async with Rig(site) as r:
            wa, ha = await join(r.port)
            wb, hb = await join(r.port)
            wc, hc = await join(r.port)
            assert (ha["type"], ha["seat"], hb["seat"]) == ("hello", "A", "B")
            assert ha["token"] != hb["token"]
            assert hc["type"] == "error" and hc["code"] == "full"
            with pytest.raises(websockets.ConnectionClosed):
                await asyncio.wait_for(wc.recv(), 2)
            for w in (wa, wb):
                await w.close()
    run(go())


def test_keys_move_your_own_rival_and_each_client_gets_only_its_own_payload(site):
    async def go():
        async with Rig(site) as r:
            wa, ha = await join(r.port)
            wb, hb = await join(r.port)
            await settle()
            await drain(wa), await drain(wb)
            a0 = r.match.episode.observe("A")["me"]["col"]
            b0 = r.match.episode.observe("B")["me"]["col"]
            await wa.send(json.dumps({"type": "keys", "keys": ["d"]}))
            await wb.send(json.dumps({"type": "keys", "keys": ["a"]}))     # A's key: ignored
            await settle()
            await r.ticks(24)
            assert r.match.episode.observe("A")["me"]["col"] != a0
            assert r.match.episode.observe("B")["me"]["col"] == b0
            ma, mb = await drain(wa), await drain(wb)
            sa = [x for x in ma if x["type"] == "state"]
            sb = [x for x in mb if x["type"] == "state"]
            assert sa and sb and {x["seat"] for x in sa} == {"A"} and {x["seat"] for x in sb} == {"B"}
            assert hb["token"] not in json.dumps(ma) and ha["token"] not in json.dumps(mb)
            await wa.close(), await wb.close()
    run(go())


def test_junk_from_a_client_never_crashes_the_server(site):
    async def go():
        async with Rig(site) as r:
            wa, _ = await join(r.port)
            wb, _ = await join(r.port)
            before = None
            for junk in ("not json", "[]", '{"type":"keys","keys":[1]}', b"\x00\xff",
                         "x" * 70_000, json.dumps({"type": "keys", "seat": "B", "keys": ["left"]}),
                         json.dumps({"type": "outcome", "reason": "won:A"})):
                await wa.send(junk)
            await settle()
            await r.ticks(12)
            assert r.match.state == "playing"
            assert r.match.episode.outcome()["status"] == "ongoing"
            assert r.match.episode.outcome()["invalid_inputs"] == {"A": 0, "B": 0}
            await wb.send(json.dumps({"type": "keys", "keys": ["left"]}))
            await settle()
            await r.ticks(6)
            assert any(x["type"] == "state" for x in await drain(wb))
            await wa.close(), await wb.close()
    run(go())


def test_a_dropped_seat_pauses_resumes_on_its_token_and_a_bad_token_is_refused(site):
    async def go():
        async with Rig(site) as r:
            wa, ha = await join(r.port)
            wb, hb = await join(r.port)
            await r.ticks(6)
            f = r.match.episode.outcome()["frames"]
            await wb.close()
            await settle()
            assert r.match.state == "paused"
            await r.ticks(12 * 5)
            assert r.match.episode.outcome()["frames"] == f
            texts = [x["text"] for x in await drain(wa) if x["type"] == "status"]
            assert "Rival disconnected, waiting up to 15 s" in texts
            wx, bad = await join(r.port, "wrong-token")
            assert bad["type"] == "error" and bad["code"] == "bad_token"
            wb2, back = await join(r.port, hb["token"])
            assert back["type"] == "hello" and back["seat"] == "B"
            await r.ticks(3)
            assert r.match.state == "playing"
            assert r.match.episode.outcome()["frames"] == f + 3
            await wa.close(), await wb2.close()
    run(go())


def test_no_reconnect_ends_the_duel_for_both_with_the_reason(site):
    async def go():
        async with Rig(site) as r:
            wa, _ = await join(r.port)
            wb, _ = await join(r.port)
            await r.ticks(3)
            await wb.close()
            await settle()
            r.now[0] += FORFEIT_GRACE_S + 1
            await r.srv.pump()
            await settle()
            end = [x for x in await drain(wa) if x["type"] == "state"][-1]
            assert end["outcome"] == {"status": "terminal", "reason": "rival_disconnected",
                                      "result": "won"}
            await wa.close()
    run(go())


def test_the_rematch_message_over_the_wire(site):
    async def go():
        async with Rig(site, seed=4) as r:
            wa, _ = await join(r.port)
            wb, _ = await join(r.port)
            await r.ticks(3)
            r.match.episode._duel.terminal = "won:B"
            await r.ticks(1)
            await drain(wa), await drain(wb)
            await wa.send(json.dumps({"type": "rematch"}))
            await settle()
            st = [x for x in await drain(wa) if x["type"] == "status"][-1]
            assert st["text"] == "Waiting for rival…"
            await wb.send(json.dumps({"type": "rematch"}))
            await settle()
            assert r.match.state == "playing" and r.match.episode.seed == 4
            await wa.close(), await wb.close()
    run(go())


# --- the page is served by the same port ------------------------------------------
async def http_get(port, path):
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    writer.write(f"GET {path} HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n".encode())
    await writer.drain()
    raw = await reader.read()
    writer.close()
    head, _, body = raw.partition(b"\r\n\r\n")
    return int(head.split()[1]), head.decode("latin-1"), body


def test_the_server_serves_the_online_page_and_art_and_nothing_else(site):
    async def go():
        async with Rig(site) as r:
            code, head, body = await http_get(r.port, "/")
            assert code == 200 and b"online.js" in body and b"pyodide" not in body.lower()
            assert b"phaser" in body.lower()
            code, _, body = await http_get(r.port, "/art/tiles.png")
            assert code == 200 and body.startswith(b"\x89PNG")
            for path in ("/manifest.json", "/online.js", "/keys.js", "/draw.js", "/ui.js"):
                assert (await http_get(r.port, path))[0] == 200, path
            for path in ("/nope", "/../pyproject.toml", "/%2e%2e/pyproject.toml",
                         "/art/../../pyproject.toml", "/server/match.py", "/pop/versus.py",
                         "//etc/passwd",
                         "/game.zip", "/index.html", "/main.js"):      # engine code stays home
                assert (await http_get(r.port, path))[0] == 404, path
    run(go())
