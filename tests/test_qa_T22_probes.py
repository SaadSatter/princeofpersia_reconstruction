"""QA probes for T22 (Gate 1): adversarial checks on the three modes, written by QA.

Headless; localhost sockets only; no network, no key, no training. Findings are
strict xfails named QA-T22-n (they pass the day the Tech Lead fixes them).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
import subprocess
import time
import zipfile
from pathlib import Path

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from agents import modes                      # noqa: E402
from agents.rl import policy                  # noqa: E402
from server import modes as smodes            # noqa: E402
from server.match import TICK_S               # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
AI_LABEL, BASE_LABEL = "AI Model (trained)", "Baseline (scripted)"
FORBIDDEN = {"seed", "token", "_duel", "duel", "snapshot", "owner", "trap_owner", "rigged_by",
             "pending", "rng", "inputs", "invalid_inputs", "trace", "fallback", "fallbacks",
             "source", "weights", "sha256", "policy"}


def walk(v):
    if isinstance(v, dict):
        for k, x in v.items():
            yield k
            yield from walk(x)
    elif isinstance(v, list):
        for x in v:
            yield from walk(x)


def ticks(m, now, n):
    for _ in range(n):
        now += TICK_S
        m.advance(now)
    return now


@pytest.fixture()
def tampered(tmp_path, monkeypatch):
    """The shipped weights with one byte appended: same JSON, different SHA-256."""
    bad = tmp_path / "ppo-tampered.json"
    bad.write_bytes(Path(policy.SHIPPED_WEIGHTS).read_bytes() + b"\n")
    monkeypatch.setattr(policy, "SHIPPED_WEIGHTS", bad)
    return bad


# --- one list, no second copy of a label -------------------------------------------------
def _label_files():
    pats = ("*.py", "web/*.js", "web/*.html", "render/*.py", "server/*.py", "agents/*.py",
            "tools/web/*.py", "tools/web/*.cjs")
    return [p for pat in pats for p in ROOT.glob(pat) if str(p.relative_to(ROOT)) != "agents/modes.py"]


def _copies():
    labels = [m.label for m in modes.MODES]
    return sorted({(str(p.relative_to(ROOT)), lab) for p in _label_files() for lab in labels
                   if lab in p.read_text()})


def test_no_file_but_agents_modes_spells_a_mode_label():
    assert _copies() == []


def test_label_copies_outside_the_list_are_only_help_text_and_comments():
    files = {f for f, _ in _copies()}
    assert files <= {"play.py", "web/bridge.py", "server/match.py"}, files
    labels = [m.label for m in modes.MODES]
    for name in ("web/bridge.py", "server/match.py"):
        for ln in (ROOT / name).read_text().splitlines():
            if any(lab in ln for lab in labels):
                assert "#" in ln or ln.lstrip().startswith(('"', "no play", "honest")), (name, ln)


def test_js_and_html_hold_no_label_text_and_both_pages_read_manifest_modes():
    for p in list((ROOT / "web").glob("*.js")) + list((ROOT / "web").glob("*.html")):
        t = p.read_text()
        assert not any(m.label in t for m in modes.MODES), p.name
    assert "manifest.modes" in (ROOT / "web/main.js").read_text()
    assert "manifest.modes" in (ROOT / "web/online.js").read_text()


# --- no silent fallback to the baseline when the weights are wrong ------------------------
def test_ai_everywhere_refuses_a_tampered_file(tampered):
    from web.bridge import make_game
    for fn in (lambda: modes.make_controller("ai"), lambda: modes.make_seat_rival("ai"),
               modes.verify_shipped,
               lambda: make_game("human_vs_ai", "A", 1, "ai", honest=True),
               lambda: make_game("human_vs_ai", "A", 1, "ai", honest=False)):
        with pytest.raises(policy.WeightsError):
            fn()
    # the baseline never reads the weights file, so it still works (that is not a fallback)
    assert make_game("human_vs_ai", "A", 1, "baseline", honest=True).rival_label == BASE_LABEL


def test_ai_everywhere_refuses_a_missing_file(tmp_path, monkeypatch):
    from web.bridge import make_game
    monkeypatch.setattr(policy, "SHIPPED_WEIGHTS", tmp_path / "nope.json")
    for fn in (lambda: modes.make_controller("ai"), modes.verify_shipped,
               lambda: make_game("human_vs_ai", "A", 1, "ai")):
        with pytest.raises(policy.WeightsError):
            fn()


def test_a_wrong_expected_hash_is_refused_even_for_the_good_file():
    with pytest.raises(policy.WeightsError):
        modes.make_controller("ai", sha256="0" * 64)


def test_pygame_ai_mode_with_bad_weights_exits_2_and_never_starts_a_duel(tampered, monkeypatch, capsys):
    pytest.importorskip("pygame")
    import play
    started = []
    monkeypatch.setattr(play, "versus_main", lambda args, rival=None: started.append(rival) or 0)
    assert play.main(["--mode", "ai"]) == 2
    assert started == []
    assert "error" in capsys.readouterr().err.lower()
    assert play.main(["--mode", "baseline"]) == 0 and started[0].mode_label == BASE_LABEL


def test_server_start_and_web_build_refuse_a_tampered_file(tampered, tmp_path):
    from server.__main__ import main
    with pytest.raises(SystemExit) as e:
        main(["--rival", "baseline", "--port", "0"])
    assert e.value.code == 2
    from tools.web import build
    with pytest.raises(policy.WeightsError):
        build.build(tmp_path / "site")


# --- the AI seat sees only its own seat -------------------------------------------------
def _assert_own_seat(obs, legal, ep):
    assert obs == ep.observe("B")
    assert tuple(legal) == tuple(ep.legal_actions("B"))
    assert not (set(walk(obs)) & {"seed", "_duel", "rng", "trap_owner", "owner", "rigged_by", "token"})


@pytest.mark.parametrize("mode", ["ai", "baseline"])
def test_pygame_ai_seat_gets_its_own_observation_and_legal_actions(mode, monkeypatch, tmp_path):
    pytest.importorskip("pygame")
    import play
    import pop.versus as pv
    seen, eps = [], []
    orig, real_make = pv.arena_episode, modes.make_seat_rival

    def grab(seed):
        eps.append(orig(seed))
        return eps[-1]
    monkeypatch.setattr(pv, "arena_episode", grab)

    def spy_make(mid, *a, **k):
        r = real_make(mid, *a, **k)
        base = r.__class__

        class Spy(base):
            def __call__(self, obs, legal):
                _assert_own_seat(obs, legal, eps[-1])
                seen.append(1)
                return base.__call__(self, obs, legal)
        r.__class__ = Spy
        return r
    monkeypatch.setattr(modes, "make_seat_rival", spy_make)
    assert play.main(["--mode", mode, "--seed", "4", "--keys", "A:RIGHT,A:RIGHT,A:DRAW",
                      "--screenshot", str(tmp_path / "s.png")]) == 0
    assert len(seen) >= 10 and eps


def test_pygame_ai_mode_is_deterministic_for_seed_and_keys(tmp_path):
    pytest.importorskip("pygame")
    import play
    shots = []
    for i in range(2):
        out = tmp_path / f"s{i}.png"
        assert play.main(["--mode", "ai", "--seed", "11", "--keys", "A:RIGHT,A:RIGHT,A:UP,A:DRAW,A:ATTACK",
                          "--screenshot", str(out)]) == 0
        shots.append(out.read_bytes())
    assert shots[0] == shots[1]


def test_pygame_both_key_sets_drive_the_human_seat_against_an_ai_and_local_keeps_the_split():
    pygame = pytest.importorskip("pygame")
    import play
    pygame.init()
    names = play.ai_key_names()
    for seat in ("A", "B"):
        for k, v in play.VERSUS_KEYS[seat].items():
            if k != "shift":
                assert names[pygame.key.key_code(v)] == ("A", k), (seat, k)
    assert all(s == "A" for s, _ in names.values())
    assert (play.VERSUS_KEYS["A"]["left"], play.VERSUS_KEYS["B"]["left"]) == ("a", "left")
    src = (ROOT / "play.py").read_text()
    assert "ai_key_names() if rival is not None else {" in src      # local mode keeps the per-seat table


def test_old_flags_still_parse_and_conflicts_are_errors(tmp_path):
    pytest.importorskip("pygame")
    import play
    out = tmp_path / "v.png"
    assert play.main(["ARENA", "--versus", "--seed", "2", "--keys", "A:RIGHT,B:LEFT", "--screenshot", str(out)]) == 0
    assert out.stat().st_size > 0
    for argv in (["--mode", "ai", "--watch"], ["--mode", "ai", "--replay", "x"], ["--menu", "--watch"],
                 ["--mode", "robot"]):
        with pytest.raises(SystemExit):
            play.main(argv)


def test_pygame_ai_decision_is_synchronous_so_a_slow_policy_blocks_the_frame():
    """Observation, not a brief criterion: #45 (0.04 s) names the live server only."""
    r = modes.make_seat_rival("baseline")
    r.reset(0)
    real = r.controller.decide

    def slow(obs, legal):
        time.sleep(0.15)
        return real(obs, legal)
    r.controller.decide = slow
    from pop.versus import arena_episode
    ep = arena_episode(1)
    t = time.perf_counter()
    modes.step_ai_seat(ep, r)
    assert time.perf_counter() - t >= 0.15


# --- the web bundle and ?play= ---------------------------------------------------------------
def test_bundle_ships_weights_with_the_right_hash_and_one_mode_list(tmp_path):
    from tools.web import build
    man = build.build(tmp_path / "site")
    assert man["weights_sha256"] == policy.SHIPPED_SHA256
    assert man["modes"] == modes.manifest_modes()
    assert json.loads((tmp_path / "site/manifest.json").read_text())["modes"] == modes.manifest_modes()
    with zipfile.ZipFile(tmp_path / "site/game.zip") as z:
        names = z.namelist()
        w = z.read("agents/rl/weights/ppo-run-1.json")
    assert {"agents/modes.py", "agents/rl/policy.py"} <= set(names)
    assert hashlib.sha256(w).hexdigest() == policy.SHIPPED_SHA256
    assert not [n for n in names if n.startswith(("tools/rl", "evaluation", "server"))]


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
@pytest.mark.parametrize("query, mode, rival", [
    ("?play=ai", "human_vs_ai", "ai"), ("?play=baseline", "human_vs_ai", "baseline"),
    ("?play=human", "local_two_players", "baseline"), ("?play=ai&rival=idle", "human_vs_ai", "ai"),
    ("?play=bogus", "human_vs_ai", "baseline"), ("?play=ai&mode=local", "local_two_players", "ai"),
    ("", "human_vs_ai", "baseline")])
def test_play_query_picks_the_controller(query, mode, rival):
    js = (f"const K=require({json.dumps(str(ROOT / 'web/keys.js'))});"
          f"console.log(JSON.stringify(K.parseOptions({json.dumps(query)})))")
    out = subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout
    o = json.loads(out)
    assert (o["mode"], o["rival"]) == (mode, rival)


def test_bridge_ai_game_spy_sees_only_seat_b_and_labels_honestly():
    from web.bridge import make_game
    g = make_game("human_vs_ai", "A", 5, "ai", honest=True)
    seen = []
    real = g.rival.controller.decide

    def spy(obs, legal):
        _assert_own_seat(obs, legal, g.episode)
        seen.append(1)
        return real(obs, legal)
    g.rival.controller.decide = spy
    for _ in range(60):
        g.tick()
    assert seen
    p = json.loads(g.tick_json())
    assert p["rival"] == AI_LABEL
    assert not (set(walk(p)) & {"fallback", "fallbacks", "source", "weights", "sha256"})


# --- online: the server side of an AI room ---------------------------------------------------
@pytest.mark.parametrize("mode", ["ai", "baseline"])
def test_server_ai_seat_gets_only_seat_b_and_a_slow_policy_is_a_logged_fallback_never_sent(mode):
    m = smodes.make_match(mode, seed=7)
    m.join(None, 0.0)
    ctrl = m.game.rival.inner.controller
    real = ctrl.decide
    delay = {"s": 0.0}

    def decide(obs, legal):
        _assert_own_seat(obs, legal, m.episode)
        time.sleep(delay["s"])
        return real(obs, legal)
    ctrl.decide = decide
    now = ticks(m, 0.0, 30)
    assert m.trace()["fallbacks"] == []
    delay["s"] = 0.30                                    # inject a slow policy
    worst = 0.0
    for _ in range(40):
        now += TICK_S
        t = time.perf_counter()
        m.advance(now)
        worst = max(worst, time.perf_counter() - t)
    assert worst < 0.04 + 0.05, worst                    # the 12 Hz loop is never stalled past the budget
    fb = m.trace()["fallbacks"]
    assert fb and all(f["source"] == "fallback" and f["seat"] == "B" for f in fb)
    assert any(f["reason"] == "slow_answer_replaced_by_wait" for f in fb)
    wire = json.dumps(m.drain("A"))
    for word in ("fallback", "source", "slow_answer", "policy_error"):
        assert word not in wire
    m.close()


def test_ai_and_baseline_rooms_differ_to_the_client_only_in_the_label():
    a, b = smodes.make_match("ai", seed=3), smodes.make_match("baseline", seed=3)
    for m in (a, b):
        m.join(None, 0.0)
        ticks(m, 0.0, 3)
    sa = [x for x in a.drain("A") if x["type"] == "state"][-1]
    sb = [x for x in b.drain("A") if x["type"] == "state"][-1]
    assert set(sa) == set(sb) and sa["rival"] == AI_LABEL and sb["rival"] == BASE_LABEL
    a.close(), b.close()


websockets = pytest.importorskip("websockets")
from server.app import OnlineServer           # noqa: E402


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

    async def ticks(self, n):
        for _ in range(n):
            self.now[0] += TICK_S
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


def go(coro):
    return asyncio.run(asyncio.wait_for(coro, 90))


def test_a_second_client_cannot_join_an_ai_room_and_the_owner_is_unharmed():
    async def body():
        async with Rig() as r:
            wa, ha = await conn(r.port, {"type": "join", "create": True, "mode": "ai"})
            assert ha["type"] == "hello" and ha["seat"] == "A"
            for first in ({"type": "join", "code": "AAAA"}, {"type": "join", "code": "AAAA", "seat": "B"},
                          {"type": "join", "code": "AAAA", "token": "x" * 20},
                          {"type": "join", "code": "AAAA", "mode": "human"}):
                wb, msg = await conn(r.port, first)
                assert msg["type"] == "error" and msg["code"] in ("full", "bad_token"), msg
                await wb.close()
            await r.ticks(10)
            st = [m for m in await drain(wa) if m["type"] == "state"]
            assert st and all(m["seat"] == "A" for m in st)
            assert r.made["AAAA"].state == "playing"
            await wa.close()
    go(body())


@pytest.mark.parametrize("bad", [["ai"], {"a": 1}, 1, True, "", "AI", "ai ", "ai\n", "x" * 60, "Ai", "__proto__"])
def test_bad_modes_are_refused_without_a_room_and_the_socket_can_retry(bad):
    async def body():
        async with Rig() as r:
            ws, msg = await conn(r.port, {"type": "join", "create": True, "mode": bad})
            assert msg["type"] == "error" and msg["code"] == "bad_mode", msg
            assert r.made == {} and r.srv.rooms == {}
            await ws.send(json.dumps({"type": "join", "create": True, "mode": "ai"}))   # same socket retries
            ok = json.loads(await asyncio.wait_for(ws.recv(), 2))
            assert ok["type"] == "hello" and r.made["AAAA"].rival == "ai"
            await ws.close()
    go(body())


def test_extra_create_fields_cannot_choose_the_seat_the_seed_or_the_rival():
    async def body():
        async with Rig() as r:
            ws, h = await conn(r.port, {"type": "join", "create": True, "mode": "ai", "seat": "B",
                                        "seed": 99, "rival": "human", "neutral": True, "token": "t",
                                        "weights": "/etc/passwd", "sha256": "0" * 64})
            assert h["type"] == "hello" and h["seat"] == "A"
            m = r.made["AAAA"]
            assert m.rival == "ai" and m.seed == 0 and not m.neutral
            await ws.close()
    go(body())


def test_ai_room_wire_traffic_has_no_hidden_field_and_junk_client_messages_are_ignored():
    async def body():
        async with Rig() as r:
            ws, h = await conn(r.port, {"type": "join", "create": True, "mode": "ai"})
            assert not (set(walk(h)) & (FORBIDDEN - {"token"}))
            for junk in ({"type": "keys", "seat": "B", "keys": ["d"]}, {"type": "mode", "mode": "human"},
                         {"type": "rematch", "seat": "B"}, {"type": "keys", "keys": "d" * 5000}, "not json",
                         {"type": "set_rival", "rival": "baseline"}, {"type": "keys", "keys": [1, None, {"a": 1}]}):
                await ws.send(json.dumps(junk))
            await r.ticks(40)
            msgs = await drain(ws)
            assert any(m["type"] == "state" for m in msgs)
            for m in msgs:
                assert not (set(walk(m)) & FORBIDDEN), m
                if m["type"] == "state":
                    assert m["rival"] == AI_LABEL and m["seat"] == "A"
            wire = json.dumps(msgs).lower()
            for word in ("ppo", "sha256", "weights", "fallback", '"seed"'):
                leaked = word in wire                    # (a bool: never print the whole wire)
                assert not leaked, word
            assert r.made["AAAA"].rival == "ai" and r.made["AAAA"].state == "playing"
            await ws.close()
    go(body())


def test_reconnect_with_the_token_returns_to_seat_a_of_the_ai_room_and_a_bad_token_does_not():
    async def body():
        async with Rig() as r:
            ws, h = await conn(r.port, {"type": "join", "create": True, "mode": "ai"})
            token = h.get("token")
            assert token
            await ws.close()
            await asyncio.sleep(0.05)
            await r.ticks(5)
            w2, msg = await conn(r.port, {"type": "join", "code": "AAAA", "token": token})
            assert msg["type"] == "hello" and msg["seat"] == "A"
            await r.ticks(10)
            assert [m for m in await drain(w2) if m["type"] == "state"]
            w3, bad = await conn(r.port, {"type": "join", "code": "AAAA", "token": "nope"})
            assert bad["type"] == "error"
            await w2.close()
            await w3.close()
    go(body())


def test_rematch_over_sockets_one_press_vs_ai_and_both_vs_human():
    async def body():
        async with Rig() as r:
            wa, _ = await conn(r.port, {"type": "join", "create": True, "mode": "ai"})
            await r.ticks(3)
            m = r.made["AAAA"]
            await wa.send(json.dumps({"type": "rematch"}))      # a press mid-duel changes nothing
            await r.ticks(2)
            assert m.state == "playing"
            m.episode._duel.terminal = "won:B"
            await r.ticks(3)
            assert m.state == "ended"
            await wa.send(json.dumps({"type": "rematch"}))
            await asyncio.sleep(0.1)
            await r.ticks(3)
            assert m.state == "playing"
            await wa.close()
            wh, _ = await conn(r.port, {"type": "join", "create": True, "mode": "human"})
            wj, j = await conn(r.port, {"type": "join", "code": "BBBB"})
            assert j["seat"] == "B"
            await r.ticks(3)
            hm = r.made["BBBB"]
            hm.episode._duel.terminal = "won:B"
            await r.ticks(3)
            assert hm.state == "ended"
            await wh.send(json.dumps({"type": "rematch"}))
            await asyncio.sleep(0.1)
            await r.ticks(2)
            assert hm.state == "ended"
            await wj.send(json.dumps({"type": "rematch"}))
            await asyncio.sleep(0.1)
            await r.ticks(2)
            assert hm.state == "playing"
            await wh.close()
            await wj.close()
    go(body())


def test_rematch_keeps_fallbacks_per_duel_and_labelled():
    m = smodes.make_match("ai", seed=2)
    m.join(None, 0.0)
    now = ticks(m, 0.0, 20)
    m.episode._duel.terminal = "won:B"
    now = ticks(m, now, 2)
    m.receive("A", '{"type":"rematch"}', now)
    assert m.state == "playing"
    ticks(m, now, 30)
    assert len(m.past_traces) == 1
    assert all(f["source"] == "fallback" for f in m.trace()["fallbacks"])
    m.close()


def test_label_honesty_is_missing_only_on_the_legacy_default_room_path():
    """Tech Lead concern 1. Everything built with honest=True or a chosen mode is labelled by
    agents.modes; the only path that still says "AI rival: ..." is `--rival baseline` with no
    creator-chosen mode (server/__main__.py `legacy`), plus the class defaults used by old tests."""
    from web.bridge import make_game
    for kind in ("ai", "baseline"):
        assert make_game("human_vs_ai", "A", 0, kind, honest=True).rival_label == modes.label(kind)
    assert make_game("human_vs_ai", "A", 0, "ai").rival_label == AI_LABEL      # ai is always honest
    assert make_game("human_vs_ai", "A", 0, "baseline").rival_label is None    # legacy default
    src = (ROOT / "server/__main__.py").read_text()
    assert 'legacy = mode is None and args.rival == "baseline"' in src
    assert smodes.make_match("baseline").honest is True
