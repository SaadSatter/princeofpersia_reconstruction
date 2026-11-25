"""T13: what the server sends a client is that seat's payload and nothing else (GDD Section 6).

Every message to seat A is recorded over duels in which seat B disguises, rigs
a trap and holds keys. Nothing of B's may appear, and a disguised rival must be
indistinguishable from a real guard in what A receives (R-V25).
"""

from __future__ import annotations

import json
from pathlib import Path

from pop.versus import arena_episode
from server.match import TICK_S, Match

T = TICK_S
SEED = 918273
ALLOWED_STATE = {"type", "seat", "rival", "seat_view", "draw", "hud", "outcome"}
ALLOWED_TYPES = {"state", "status"}
ALLOWED_STATUS = {"type", "state", "text", "rematch"}
ALLOWED_OUTCOME = {"status", "reason", "result"}
FORBIDDEN_KEYS = {"seed", "token", "_duel", "duel", "snapshot", "owner", "trap_owner",
                  "rigged_by", "pending", "rng", "disguised_rivals", "inputs", "invalid_inputs",
                  "stale_inputs", "replaced_inputs", "trace", "connection", "address",
                  "peer", "guard_script", "rigs", "traps"}


def walk(value, path=()):
    if isinstance(value, dict):
        for k, v in value.items():
            yield path, k, v
            yield from walk(v, path + (k,))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from walk(v, path + (i,))


def start(ep=None, seed=SEED):
    m = Match(seed=seed, episode=ep)
    a = m.join(None, 0.0)
    b = m.join(None, 0.0)
    return m, a, b


def b_disguises_and_rigs(m: Match) -> list[dict]:
    """Drive seat B through the engine: put it in a guard's costume and rig a cell."""
    d = m.episode._duel
    d.rivals["B"].disguised = True
    m.episode.step("B", "RIG")
    sent = []
    now = 0.0
    m.receive("B", json.dumps({"type": "keys", "keys": ["left", "'"]}), now)
    m.receive("A", json.dumps({"type": "keys", "keys": ["d"]}), now)
    for _ in range(80):
        now += T
        m.advance(now)
        sent += m.drain("A")
    return sent


def test_every_message_to_a_is_allow_listed_and_holds_none_of_bs_secrets():
    m, a, b = start()
    sent = b_disguises_and_rigs(m)
    assert sent
    states = [x for x in sent if x["type"] == "state"]
    assert states and {x["type"] for x in sent} <= ALLOWED_TYPES
    for msg in sent:
        if msg["type"] == "state":
            assert set(msg) <= ALLOWED_STATE, set(msg)
            assert set(msg["outcome"]) == ALLOWED_OUTCOME
            assert msg["seat"] == "A"
        else:
            assert set(msg) <= ALLOWED_STATUS
        for _, k, _v in walk(msg):
            assert k not in FORBIDDEN_KEYS, k
    text = json.dumps(sent)
    assert b["token"] not in text and a["token"] not in text
    assert str(SEED) not in text
    # B's own observation is never inside A's messages.
    b_obs = json.dumps(m.episode.observe("B")["me"], sort_keys=True)
    assert b_obs not in text
    # A's own seat_view is A's observation (its `my_traps` is A's, empty here).
    last = states[-1]
    assert last["seat_view"] == json.loads(json.dumps(m.episode.observe("A")))
    assert last["seat_view"]["my_traps"] == []
    # The only `disguised` flag in a payload is the receiver's own.
    paths = [p + (k,) for p, k, _ in walk(last) if k == "disguised"]
    assert paths == [("seat_view", "me", "disguised"), ("hud", "disguised")]
    assert last["seat_view"]["me"]["disguised"] is False
    assert all(f["kind"] == "guard" or f["kind"] == "rival"
               for f in last["seat_view"]["figures"])


def test_a_rig_and_a_disguise_in_the_other_room_change_nothing_a_receives():
    """Same inputs from A; B idle versus B disguised and rigging: A's bytes are equal."""
    def run(hidden: bool) -> str:
        m, _, _ = start()
        d = m.episode._duel
        if hidden:
            d.rivals["B"].disguised = True
            m.episode.step("B", "RIG")
        m.receive("A", json.dumps({"type": "keys", "keys": ["d"]}), 0.0)
        out, now = [], 0.0
        for _ in range(40):
            now += T
            m.advance(now)
            out += m.drain("A")
        return json.dumps(out, sort_keys=True)
    assert run(False) == run(True)


def _guard_scene(disguised_rival: bool):
    """Seat A beside one figure at col 8: either the disguised seat B or a real guard."""
    ep = arena_episode(0)
    d = ep._duel
    a, b = d.rivals["A"], d.rivals["B"]
    g = next(iter(d.guards.values()))
    a.kid.room, a.kid.row, a.kid.col = g.room, g.row, 1
    if disguised_rival:
        b.kid.room, b.kid.row, b.kid.col, b.kid.facing = g.room, g.row, 8, g.facing
        b.disguised = True
        g.room = 5 if g.room != 5 else 4          # the real guard is elsewhere
        # (the two scenes then have one figure each, so A's message can be equal)
    else:
        g.col = 8
    return ep


def test_a_disguised_rival_and_a_real_guard_give_a_the_same_bytes():
    ref = _guard_scene(False)
    obs_ref = ref.observe("A")
    fig = [f for f in obs_ref["figures"] if f["col"] == 8]
    assert len(fig) == 1 and fig[0]["kind"] == "guard"

    msgs = []
    for disguised in (True, False):
        ep = _guard_scene(disguised)
        m, _, _ = start(ep)
        m.drain("A")
        m.advance(T)                              # the first tick's payload
        states = [x for x in m.drain("A") if x["type"] == "state"]
        msgs.append(json.dumps(states[0], sort_keys=True))
    assert msgs[0] == msgs[1]


def test_status_messages_are_identical_for_every_hidden_state():
    def statuses(hidden):
        ep = arena_episode(1)
        ep._duel.rivals["B"].disguised = hidden
        ep._duel.suspicion[(next(iter(ep._duel.guards)), "B")] = 50 if hidden else 0
        m, _, _ = start(ep)
        m.drain("A")
        out, now = [], 0.0
        for i in range(30):
            now += T
            m.advance(now)
            if i == 10:
                m.connection_lost("B", now)
            if i == 20:
                m.join(None, now)                  # refused: full
            out += [x for x in m.drain("A") if x["type"] == "status"]
        return json.dumps(out, sort_keys=True)
    assert statuses(False) == statuses(True)


def test_hello_goes_to_its_own_client_and_error_messages_are_fixed_text():
    from server.app import error_message, hello_message
    h = hello_message("A", "tok", None)
    assert h["type"] == "hello" and h["seat"] == "A" and h["token"] == "tok"
    assert error_message("full") == error_message("full")
    assert set(error_message("full")) == {"type", "code", "text"}
    assert error_message("bad_token")["text"] != error_message("full")["text"]


def test_no_module_outside_server_imports_websockets():
    root = Path(__file__).resolve().parent.parent
    for rel in ("pop", "agents", "render"):
        for p in (root / rel).rglob("*.py"):
            assert "websockets" not in p.read_text(), p
    for rel in ("play.py", "web/bridge.py", "server/match.py", "server/trace.py"):
        assert "websockets" not in (root / rel).read_text(), rel
