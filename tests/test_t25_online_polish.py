"""T25 (decisions #95, #96, #97, #98): online page polish.

No browser here (the look is for Saad's next playtest). These tests pin the pure
page rules (node), the page's CSS and source, and the server's quiet handshake log
and private AI rooms over real localhost sockets. Needs node and the `online` extra
for the parts that use them.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
NODE = shutil.which("node")
needs_node = pytest.mark.skipif(NODE is None, reason="node not installed")
KNEEL = "kneel: sword or uniform (sheathe first if your sword is drawn)"


def _js(expr: str):
    code = f"const K = require({json.dumps(str(WEB / 'keys.js'))}); console.log(JSON.stringify({expr}));"
    r = subprocess.run([NODE, "-e", code], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


# --- item 4, decision #98: the key hint ------------------------------------------------

@needs_node
def test_hint_for_seat_a_says_what_s_does_and_the_sheathe_nuance():
    assert "S " + KNEEL in _js('K.keyHints("human_vs_ai", "A")')


@needs_node
def test_hint_for_seat_b_names_its_own_down_key():
    h = _js('K.keyHints("human_vs_ai", "B")')
    assert "Down " + KNEEL in h and "S " + KNEEL not in h


@needs_node
def test_local_two_player_hint_names_each_seats_kneel_key():
    h = _js('K.keyHints("local_two_players", "A")')
    assert "S " + KNEEL in h and "Down " + KNEEL in h


# --- item 1, decision #95: private AI match with one click ------------------------------

@needs_node
def test_ai_and_baseline_start_at_once_and_show_neither_code_nor_join():
    for m in ("ai", "baseline"):
        v = _js(f'K.lobbyView("{m}")')
        assert v == {"startsAtOnce": True, "showCreateJoin": False, "showCode": False}, m


@needs_node
def test_human_vs_human_keeps_create_join_and_the_code():
    v = _js('K.lobbyView("human")')
    assert v == {"startsAtOnce": False, "showCreateJoin": True, "showCode": True}


@needs_node
def test_no_mode_chosen_yet_shows_only_the_picker():
    v = _js('K.lobbyView(null)')
    assert v == {"startsAtOnce": False, "showCreateJoin": False, "showCode": False}


def test_the_page_uses_the_lobby_rules_and_wraps_create_join_in_one_block():
    js = (WEB / "online.js").read_text()
    html = (WEB / "online.html").read_text()
    assert "SMKeys.lobbyView" in js
    assert 'id="human-lobby"' in html
    block = html.split('id="human-lobby"', 1)[1].split('<div id="room"', 1)[0]
    assert 'id="create-room"' in block and 'id="join-room"' in block and 'id="code-input"' in block
    assert 'id="mode-pick"' not in block                       # the picker stays visible always


def test_the_page_still_sends_only_join_keys_and_rematch():
    types = set(re.findall(r'type:\s*"(\w+)"', (WEB / "online.js").read_text()))
    assert types == {"join", "keys", "rematch"}


# --- item 2, decision #96: the loading screen is centred --------------------------------

def test_loading_status_is_a_centred_full_window_overlay_in_css():
    html = (WEB / "online.html").read_text()
    m = re.search(r'#status\[data-state="loading"\]\s*\{([^}]*)\}', html)
    assert m, "no CSS rule for the loading state"
    css = re.sub(r"\s+", " ", m.group(1))
    assert "position: fixed" in css
    assert "display: flex" in css and "align-items: center" in css and "justify-content: center" in css
    assert "inset: 0" in css or ("top: 0" in css and "left: 0" in css and "right: 0" in css
                                 and "bottom: 0" in css)   # viewport-relative, so a resize recentres it


# --- item 3, decision #97: quiet handshake failures --------------------------------------

websockets = pytest.importorskip("websockets")
from server.app import OnlineServer   # noqa: E402
from server.match import Match         # noqa: E402


def run(coro):
    return asyncio.run(asyncio.wait_for(coro, 60))


async def _serve(srv):
    server = await srv.start("127.0.0.1", 0)
    return server, server.sockets[0].getsockname()[1]


def _ws_records(caplog):
    return [r for r in caplog.records if r.name.startswith(("websockets", "server.ws"))]


def test_an_unused_browser_connection_logs_one_short_line_below_error(caplog):
    caplog.set_level(logging.DEBUG)

    async def go():
        srv = OnlineServer(Match())
        server, port = await _serve(srv)
        for _ in range(3):                                   # a browser's spare connections
            r, w = await asyncio.open_connection("127.0.0.1", port)
            w.close()
            await asyncio.sleep(0.15)
        server.close()
        await server.wait_closed()
    run(go())
    recs = [r for r in _ws_records(caplog) if "handshake" in r.getMessage().lower()
            or "unused" in r.getMessage().lower()]
    assert recs, "the quiet line should still be there"
    for r in recs:
        assert r.levelno < logging.ERROR
        assert r.exc_info is None
        assert len(r.getMessage()) <= 100 and "\n" not in r.getMessage()


def test_a_real_handshake_error_is_still_logged_as_an_error_with_its_traceback(caplog):
    caplog.set_level(logging.DEBUG)

    async def go():
        srv = OnlineServer(Match())

        def boom(connection, request):
            raise RuntimeError("real bug")
        srv._http = boom
        server, port = await _serve(srv)
        r, w = await asyncio.open_connection("127.0.0.1", port)
        w.write(b"GET / HTTP/1.1\r\nHost: x\r\n\r\n")
        await w.drain()
        await asyncio.sleep(0.3)
        w.close()
        server.close()
        await server.wait_closed()
    run(go())
    errs = [r for r in _ws_records(caplog) if r.levelno >= logging.ERROR]
    assert errs and errs[0].exc_info is not None and errs[0].exc_info[0] is RuntimeError


# --- item 1, server side: an AI room is private ------------------------------------------

def test_an_ai_room_cannot_be_joined_by_its_code_and_leaks_nothing_to_the_joiner():
    from server import modes as room_modes

    async def go():
        made = []

        def factory(code, mode=None):
            made.append(mode)
            return room_modes.make_match(mode or "human")
        srv = OnlineServer(match_factory=factory)
        server, port = await _serve(srv)
        a = await websockets.connect(f"ws://127.0.0.1:{port}/ws")
        await a.send(json.dumps({"type": "join", "create": True, "mode": "baseline"}))
        hello = json.loads(await asyncio.wait_for(a.recv(), 2))
        assert hello["type"] == "hello" and hello["seat"] == "A" and made == ["baseline"]
        b = await websockets.connect(f"ws://127.0.0.1:{port}/ws")
        await b.send(json.dumps({"type": "join", "code": hello["code"]}))
        got = json.loads(await asyncio.wait_for(b.recv(), 2))
        assert got["type"] == "error" and got["code"] == "full"
        assert hello["token"] not in json.dumps(got) and hello["code"] not in got.get("text", "")
        await a.close(), await b.close()
        server.close()
        await server.wait_closed()
    run(go())
