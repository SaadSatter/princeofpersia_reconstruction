"""T20: playtest telemetry (decisions #67, #68). One JSON Lines log per room, duel and seat.

Acceptance: off by default; both seats' logs in tick order with the #68 event types; no
hidden fact of the other seat in a log; the duel trace and state hash and every client
message are the same with and without telemetry.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from server.match import TICK_S, Match
from server.telemetry import EVENT_TYPES, IDLE_THRESHOLD_S, Telemetry

SEED = 4242
KEYSETS = [[], [], ["d"], ["a"], ["w", "d"], ["w", "a"], ["f"], ["g"], ["t"], ["s"], ["d", "lshift"],
           ["left"], ["right"], ["up", "right"], ["."], ["/"], ["'"], ["down"]]


def make(tmp: Path | None, seed: int = SEED, room: str = "TEST", rival=None) -> Match:
    tele = None if tmp is None else Telemetry(tmp, room, info={"build": "t20test"},
                                              today=lambda: "2026-11-25")
    return Match(seed=seed, rival=rival, telemetry=tele, rival_budget_s=1.0)


def drive(m: Match, ticks: int, rng_seed: int = 7, start: float = 0.0) -> tuple[float, list]:
    """Hold random key sets for both seats; return the end time and every message sent."""
    rng = random.Random(rng_seed)
    now, sent = start, []
    for i in range(ticks):
        if i % 6 == 0:
            for seat in m.human_seats:
                m.receive(seat, json.dumps({"type": "keys", "keys": rng.choice(KEYSETS)}), now)
        now += TICK_S
        m.advance(now)
        for seat in ("A", "B"):
            sent += [(seat, x) for x in m.drain(seat)]
    return now, sent


def join(m: Match):
    return m.join(None, 0.0), m.join(None, 0.0)


def logs(tmp: Path, seat: str) -> list[dict]:
    files = sorted(tmp.glob(f"*-{seat}.jsonl"))
    assert files, f"no {seat} log in {tmp}"
    return [json.loads(line) for line in files[0].read_text().splitlines()]


def test_off_by_default_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    m = make(None)
    join(m)
    drive(m, 200)
    assert list(tmp_path.iterdir()) == []


def test_the_server_flag_is_store_true_and_off_by_default():
    import server.__main__ as sm
    src = Path(sm.__file__).read_text()
    assert '"--playtest", action="store_true"' in src


def test_both_seats_logged_in_tick_order_with_known_types(tmp_path):
    m = make(tmp_path)
    join(m)
    drive(m, 900)
    for seat in ("A", "B"):
        rows = logs(tmp_path, seat)
        head, events = rows[0], rows[1:]
        assert head["type"] == "header" and head["seat"] == seat and head["room"] == "TEST"
        assert head["seed"] == SEED and head["rival"] == "human" and head["duel"] == 1
        assert head["build"] == "t20test"
        assert events[0]["type"] == "duel_start" and events[0]["t"] == 0
        assert [e["t"] for e in events] == sorted(e["t"] for e in events)
        assert [e["s"] for e in events] == sorted(e["s"] for e in events)
        assert all(e["type"] in EVENT_TYPES and e["seat"] == seat for e in events)
        assert any(e["type"] == "action" and e["accepted"] for e in events)
        assert any(e["type"] == "action" and not e["accepted"] for e in events)


def test_a_refused_input_is_logged(tmp_path):
    m = make(tmp_path)
    join(m)
    now = 0.0
    m.receive("A", json.dumps({"type": "keys", "keys": ["f"]}), now)   # attack, sword sheathed
    for _ in range(3):
        now += TICK_S
        m.advance(now)
    acts = [e for e in logs(tmp_path, "A")[1:] if e["type"] == "action"]
    assert acts and all(a["accepted"] is False and a["action"] == "LUNGE" for a in acts)


def test_idle_spell_start_and_end(tmp_path):
    m = make(tmp_path)
    join(m)
    now = 0.0
    for _ in range(int(IDLE_THRESHOLD_S * 12) + 6):
        now += TICK_S
        m.advance(now)
    m.receive("A", json.dumps({"type": "keys", "keys": ["d"]}), now)
    now += TICK_S
    m.advance(now)
    idle = [e for e in logs(tmp_path, "A")[1:] if e["type"] == "idle"]
    assert [e["phase"] for e in idle] == ["start", "end"]
    assert idle[1]["seconds"] >= IDLE_THRESHOLD_S


def test_connection_events_and_forfeit(tmp_path):
    m = make(tmp_path)
    join(m)
    now, _ = drive(m, 30)
    m.connection_lost("B", now)
    m.join(m.tokens["B"], now + 1)                      # back within 15 s
    now, _ = drive(m, 20, start=now + 1)
    m.connection_lost("A", now)
    m.advance(now + 16)                                 # past the grace: A forfeits
    a, b = logs(tmp_path, "A")[1:], logs(tmp_path, "B")[1:]
    ta, tb = [e["type"] for e in a], [e["type"] for e in b]
    assert "disconnect" in tb and "reconnect" in tb
    assert "disconnect" in ta and "reconnect" not in ta
    assert [e["phase"] for e in a if e["type"] == "pause"] == ["start", "end", "start"]
    fa = next(e for e in a if e["type"] == "forfeit")
    fb = next(e for e in b if e["type"] == "forfeit")
    assert (fa["by"], fb["by"]) == ("me", "rival")
    ea = next(e for e in a if e["type"] == "duel_end")
    assert ea["result"] == "lost" and ea["reason"] == "you_disconnected"
    m.close()                                           # nobody pressed rematch
    assert any(e["type"] == "rematch" and e["pressed"] is False for e in logs(tmp_path, "B")[1:])


def test_rematch_pressed_and_second_duel_has_its_own_files(tmp_path):
    m = make(tmp_path)
    join(m)
    now, _ = drive(m, 20)
    m._end_by_forfeit("B")                              # end the duel quickly
    m.receive("A", json.dumps({"type": "rematch"}), now)
    m.receive("B", json.dumps({"type": "rematch"}), now)
    assert m.state == "playing"
    drive(m, 10, start=now)
    assert sorted(p.name for p in tmp_path.glob("*.jsonl")) == [
        "2026-11-25-TEST-001-A.jsonl", "2026-11-25-TEST-001-B.jsonl",
        "2026-11-25-TEST-002-A.jsonl", "2026-11-25-TEST-002-B.jsonl"]
    first = [json.loads(x) for x in (tmp_path / "2026-11-25-TEST-001-A.jsonl").read_text().splitlines()]
    assert any(e["type"] == "rematch" and e["pressed"] for e in first)


def test_abandoned_duel_is_closed_with_duel_end(tmp_path):
    m = make(tmp_path)
    join(m)
    drive(m, 20)
    m.close()
    end = [e for e in logs(tmp_path, "A")[1:] if e["type"] == "duel_end"]
    assert len(end) == 1 and end[0]["reason"] == "abandoned"
    assert (tmp_path / "2026-11-25-TEST-001-host.json").is_file()


def test_a_second_server_run_never_appends_to_old_files(tmp_path):
    for _ in range(2):
        m = make(tmp_path)
        join(m)
        drive(m, 5)
    assert len(list(tmp_path.glob("*-A.jsonl"))) == 2


# --- knowledge boundary -----------------------------------------------------------
def test_other_seats_disguise_and_traps_never_appear_in_a_log(tmp_path):
    m = make(tmp_path)
    join(m)
    d = m.episode._duel
    drive(m, 5)
    d.rivals["B"].disguised = True                     # B puts on a costume
    k = d.rivals["B"].kid
    assert d.place_rig("B", (k.room, k.row, k.col - 1))       # and owns a trap
    d.traps_left["B"] -= 1
    drive(m, 120, start=0.5)
    text = (tmp_path / "2026-11-25-TEST-001-A.jsonl").read_text()
    kinds = {e["type"] for e in logs(tmp_path, "A")[1:]}
    assert not kinds & {"disguise_on", "disguise_broken", "trap_rigged", "trap_sprung"}
    for word in ("disguise", "guard", "uniform", "rigged", '"rig"', "trap_", "owner"):
        assert word not in text.lower(), word
    assert any(e["type"] == "disguise_on" for e in logs(tmp_path, "B")[1:])   # its own, in its own log


def test_own_trap_is_logged_for_the_owner_only(tmp_path):
    m = make(tmp_path)
    join(m)
    d = m.episode._duel
    now = 0.0
    k = d.rivals["B"].kid
    assert d.place_rig("B", (k.room, k.row, k.col - 1))
    for step in range(9):
        if step == 5:
            d.rigs.clear()                              # the rig is gone: sprung or spent
        now += TICK_S
        m.advance(now)
    b = [e["type"] for e in logs(tmp_path, "B")[1:]]
    a = [e["type"] for e in logs(tmp_path, "A")[1:]]
    assert "trap_rigged" in b and "trap_sprung" in b
    assert "trap_rigged" not in a and "trap_sprung" not in a


def test_headers_hold_no_names_addresses_or_tokens(tmp_path):
    m = make(tmp_path)
    a, b = join(m)
    drive(m, 5)
    for seat, res in (("A", a), ("B", b)):
        text = (tmp_path / f"2026-11-25-TEST-001-{seat}.jsonl").read_text()
        assert res["token"] not in text
        assert set(logs(tmp_path, seat)[0]) == {
            "type", "schema", "build", "seed", "rival", "room", "duel", "duel_frames",
            "ticks_per_second", "idle_threshold_s", "seat"}


# --- determinism and payloads --------------------------------------------------------
def run_duel(tmp: Path | None, rival=None):
    m = make(tmp, rival=rival)
    if rival:
        m.join(None, 0.0)
    else:
        join(m)
    _, sent = drive(m, 1500)
    return m.trace(), sent


def test_trace_hash_and_every_client_message_are_the_same_with_telemetry(tmp_path):
    t0, s0 = run_duel(None)
    t1, s1 = run_duel(tmp_path)
    assert t0["state_hash"] == t1["state_hash"]
    assert t0 == t1
    assert json.dumps(s0) == json.dumps(s1)
    assert list(tmp_path.glob("*.jsonl"))


def test_same_with_the_ai_seat(tmp_path):
    t0, s0 = run_duel(None, rival="baseline")
    t1, s1 = run_duel(tmp_path, rival="baseline")
    assert t0["state_hash"] == t1["state_hash"] and t0["ticks"] == t1["ticks"]
    assert json.dumps(s0) == json.dumps(s1)
    assert list(tmp_path.glob("*-A.jsonl")) and not list(tmp_path.glob("*-B.jsonl"))


def test_telemetry_failure_never_reaches_the_duel(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    m = make(blocker / "sub")                           # cannot be created
    join(m)
    t0, s0 = run_duel(None)
    _, sent = drive(m, 1500)
    assert m.trace()["state_hash"] == t0["state_hash"]
    assert json.dumps(sent) == json.dumps(s0)


def test_room_failed_closes_the_logs(tmp_path):
    import pytest
    pytest.importorskip("websockets")
    from server.app import OnlineServer
    from server.rooms import Room
    m = make(tmp_path)
    join(m)
    drive(m, 10)
    OnlineServer._room_failed(Room("ZZZZ", m))
    end = [e for e in logs(tmp_path, "A")[1:] if e["type"] == "duel_end"]
    assert end and end[0]["reason"] == "room_failed"


def hold(m, seat, keys, ticks, now):
    m.receive(seat, json.dumps({"type": "keys", "keys": keys}), now)
    for _ in range(ticks):
        now += TICK_S
        m.advance(now)
    return now


def test_sword_drop_and_pickup_but_not_draw_or_sheathe(tmp_path):
    m = make(tmp_path)
    join(m)
    d = m.episode._duel
    now = hold(m, "A", ["g"], 1, 0.0)                   # DRAW
    now = hold(m, "A", [], 8, now)
    now = hold(m, "A", ["g"], 1, now)                   # SHEATHE
    now = hold(m, "A", [], 8, now)
    kinds = [e["type"] for e in logs(tmp_path, "A")[1:]]
    assert "sword_drop" not in kinds and "sword_pickup" not in kinds
    now = hold(m, "A", ["g"], 1, now)                   # DRAW again
    now = hold(m, "A", [], 20, now)
    d.drop_sword(d.rivals["A"], behind=True)            # knocked away by a rival
    now = hold(m, "A", [], 2, now)
    d.swords.append(d.rivals["A"].kid.cell)             # one lies at its feet
    now = hold(m, "A", ["s"], 10, now)                  # DOWN picks it up
    rows = logs(tmp_path, "A")[1:]
    drops = [e for e in rows if e["type"] == "sword_drop"]
    assert [e["cause"] for e in drops] == ["knocked_away"]
    assert any(e["type"] == "sword_pickup" for e in rows)
    assert not any(e["type"] in ("sword_drop", "sword_pickup") for e in logs(tmp_path, "B")[1:])
