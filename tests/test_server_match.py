"""T13: the online duel's rules, with no sockets and an injected clock (server/match.py).

`Match` is the server's whole game logic: seats, tokens, held keys, pacing,
disconnects and rematch. The WebSocket layer (server/app.py) only moves its
messages. Wall time never enters: every call is given `now`.
"""

from __future__ import annotations

import json

import pytest

from pop.versus import arena_episode
from pop.versus_runner import digest, snapshot
from server.trace import replay
from server.match import FORFEIT_GRACE_S, Match, TICK_S

T = TICK_S


def two(**kw) -> tuple[Match, dict, dict]:
    m = Match(**kw)
    a = m.join(None, 0.0)
    b = m.join(None, 0.0)
    return m, a, b


def frames(m: Match) -> int:
    return m.episode.outcome()["frames"]


def run(m: Match, start: float, ticks: int, keys=None) -> float:
    """Advance `ticks` ticks, one at a time; `keys` is {seat: [names]} held throughout."""
    now = start
    for seat, names in (keys or {}).items():
        m.receive(seat, json.dumps({"type": "keys", "keys": names}), now)
    for _ in range(ticks):
        now += T
        m.advance(now)
    return now


def pos(m: Match, seat: str) -> tuple:
    me = m.episode.observe(seat)["me"]
    return (me["row"], me["col"])


# --- seats and tokens ----------------------------------------------------------
def test_first_joiner_is_seat_a_second_is_seat_b_third_is_told_full():
    m, a, b = two()
    assert (a["ok"], a["seat"]) == (True, "A")
    assert (b["ok"], b["seat"]) == (True, "B")
    c = m.join(None, 0.0)
    assert c == {"ok": False, "code": "full"}
    assert a["token"] != b["token"] and len(a["token"]) >= 16 and len(b["token"]) >= 16


def test_a_wrong_token_never_takes_a_seat_even_a_free_one():
    m = Match()
    m.join(None, 0.0)
    assert m.join("not-a-token", 0.0) == {"ok": False, "code": "bad_token"}
    assert m.join("x" * 10_000, 0.0) == {"ok": False, "code": "bad_token"}
    assert m.join(None, 0.0)["seat"] == "B"          # no token at all is a new joiner


def test_tokens_are_never_in_any_message_to_the_other_seat():
    m, a, b = two()
    run(m, 0.0, 12)
    text_a = json.dumps(m.drain("A"))
    text_b = json.dumps(m.drain("B"))
    assert b["token"] not in text_a and a["token"] not in text_b


# --- inputs ---------------------------------------------------------------------
def test_each_seats_keys_move_only_its_own_rival():
    m, _, _ = two()
    a0, b0 = pos(m, "A"), pos(m, "B")
    run(m, 0.0, 24, {"A": ["d"], "B": []})
    assert pos(m, "A") != a0 and pos(m, "B") == b0
    m2, _, _ = two()
    run(m2, 0.0, 24, {"A": [], "B": ["left"]})
    assert pos(m2, "A") == a0 and pos(m2, "B") != b0


def test_keys_from_the_other_seats_map_do_nothing():
    m, _, _ = two()
    ctrl, _, _ = two()
    run(m, 0.0, 24, {"A": ["left", "right", "up", ".", "/", "'", "rshift"]})
    run(ctrl, 0.0, 24)
    assert digest(snapshot(m.episode)) == digest(snapshot(ctrl.episode))


@pytest.mark.parametrize("raw", [
    "not json", "{", "[]", "null", "42", '"keys"', "{}", '{"type":"keys"}',
    '{"type":"keys","keys":"a"}', '{"type":"keys","keys":[1,null,{"a":1}]}',
    '{"type":"nope","keys":["d"]}', '{"type":"outcome","status":"terminal","reason":"won:A"}',
    '{"type":"keys","seat":"B","keys":["d"]}',              # claims another seat
    '{"type":"keys","keys":["zz"],"seed":3,"state":{"frames":9999}}',
    '{"type":"keys","keys":[' + ",".join(['"d"'] * 5000) + "]}",   # oversize
    "x" * 100_000, b"\xff\xfe", b'{"type":"keys","keys":["d"]}' * 100,
])
def test_malformed_unknown_oversize_and_other_seat_messages_are_ignored(raw):
    m, _, _ = two()
    ctrl, _, _ = two()
    m.receive("A", raw, 0.0)
    now = 0.0
    for _ in range(24):
        now += T
        m.advance(now)
        ctrl.advance(now)
    assert digest(snapshot(m.episode)) == digest(snapshot(ctrl.episode))
    assert m.state == "playing" and m.episode.outcome()["status"] == "ongoing"


def test_unknown_keys_are_dropped_and_the_known_ones_in_the_same_message_kept():
    m, _, _ = two()
    a0 = pos(m, "A")
    run(m, 0.0, 24, {"A": ["d", "bogus", "F13", "r", "left"]})
    assert pos(m, "A") != a0


def test_illegal_inputs_are_filtered_by_legal_actions_not_refused():
    m, _, _ = two()
    run(m, 0.0, 36, {"A": ["f", "g", "t"], "B": ["'", "."]})
    assert m.episode.outcome()["invalid_inputs"] == {"A": 0, "B": 0}


def test_a_client_cannot_end_the_duel_or_move_the_other_seat():
    m, _, _ = two()
    for raw in ('{"type":"end","reason":"won:A"}',
                '{"type":"state","outcome":{"status":"terminal"}}',
                '{"type":"move","seat":"B","action":"LUNGE"}', '{"type":"rematch"}'):
        m.receive("A", raw, 0.0)
    assert m.episode.outcome()["status"] == "ongoing" and frames(m) == 0


def test_a_seat_with_no_message_holds_nothing():
    m, _, _ = two()
    a0, b0 = pos(m, "A"), pos(m, "B")
    run(m, 0.0, 24)
    assert pos(m, "A") == a0 and pos(m, "B") == b0


# --- pacing ---------------------------------------------------------------------
def test_twelve_ticks_a_second_and_none_before_the_second_player_joins():
    m = Match()
    m.join(None, 0.0)
    m.advance(5.0)
    assert frames(m) == 0 and m.state == "waiting"
    m.join(None, 10.0)
    m.advance(10.0)
    assert frames(m) == 0
    run(m, 10.0, 12)
    assert frames(m) == 12


def test_a_stall_does_not_fast_forward_the_duel():
    m, _, _ = two()
    m.advance(60.0)                                       # one minute stall
    assert frames(m) <= 3
    m.advance(60.0 + TICK_S)
    assert frames(m) <= 4


# --- determinism ----------------------------------------------------------------
def test_the_input_trace_replays_to_the_same_outcome_and_state_hash():
    m, _, _ = two(seed=7)
    now = 0.0
    sets = [["d"], ["d", "w"], ["a"], ["f"], ["g"], ["d", "lshift"], ["s"], ["d", "w", "f"]]
    sets_b = [["left"], ["left", "up"], ["right"], ["."], ["/"], ["'"], ["down"], []]
    for i in range(8 * 30):
        if i % 30 == 0:
            m.receive("A", json.dumps({"type": "keys", "keys": sets[i // 30]}), now)
            m.receive("B", json.dumps({"type": "keys", "keys": sets_b[i // 30]}), now)
        now += T
        m.advance(now)
    tr = m.trace()
    assert tr["seed"] == 7 and len(tr["ticks"]) == frames(m)
    outcome, h = replay(tr)       # #113: the trace also holds each human release (#93)
    assert outcome == m.episode.outcome()
    assert h == tr["state_hash"] == digest(snapshot(m.episode))


def test_the_trace_holds_inputs_not_what_clients_sent():
    m, _, _ = two()
    run(m, 0.0, 12, {"A": ["d", "bogus"]})
    assert "bogus" not in json.dumps(m.trace())


# --- disconnect (#38) -----------------------------------------------------------
def test_a_drop_pauses_both_seats_and_the_other_is_told_only_the_one_text():
    m, _, _ = two()
    now = run(m, 0.0, 6)
    f = frames(m)
    m.drain("A"), m.drain("B")
    m.connection_lost("B", now)
    assert m.state == "paused"
    now += 10.0
    m.advance(now)
    assert frames(m) == f
    texts = [x["text"] for x in m.drain("A") if x["type"] == "status"]
    assert texts and set(texts) == {"Rival disconnected, waiting up to 15 s"}


def test_a_reconnect_with_the_token_inside_the_window_resumes_from_the_same_frame():
    m, _, b = two()
    now = run(m, 0.0, 6)
    f = frames(m)
    m.connection_lost("B", now)
    now += FORFEIT_GRACE_S - 0.5
    m.advance(now)
    back = m.join(b["token"], now)
    assert back == {"ok": True, "seat": "B", "token": b["token"]}
    assert m.state == "playing" and frames(m) == f
    m.advance(now + T)
    assert frames(m) == f + 1
    assert m.episode.outcome()["status"] == "ongoing"


def test_no_reconnect_within_15_seconds_the_dropped_seat_loses():
    m, _, b = two()
    now = run(m, 0.0, 6)
    m.connection_lost("B", now)
    m.advance(now + FORFEIT_GRACE_S + 0.1)
    assert m.state == "ended"
    last = [x for x in m.drain("A") if x["type"] == "state"][-1]
    assert last["outcome"] == {"status": "terminal", "reason": "rival_disconnected",
                               "result": "won"}
    back = m.join(b["token"], now + 20)
    assert back["ok"] is True
    last_b = [x for x in m.drain("B") if x["type"] == "state"][-1]
    assert last_b["outcome"] == {"status": "terminal", "reason": "you_disconnected",
                                 "result": "lost"}


def test_a_wrong_token_cannot_take_the_dropped_seat():
    m, _, b = two()
    now = run(m, 0.0, 6)
    m.connection_lost("B", now)
    assert m.join("guess", now + 1) == {"ok": False, "code": "bad_token"}
    assert m.join(None, now + 1) == {"ok": False, "code": "full"}
    assert m.join("A" + b["token"], now + 1) == {"ok": False, "code": "bad_token"}
    assert m.state == "paused"


def test_the_pause_message_does_not_depend_on_hidden_state():
    def status_texts(disguised: bool):
        ep = arena_episode(3)
        ep._duel.rivals["B"].disguised = disguised
        m, _, _ = two(episode=ep)
        now = run(m, 0.0, 6)
        m.drain("A")
        m.connection_lost("B", now)
        m.advance(now + 3)
        return json.dumps([x for x in m.drain("A") if x["type"] == "status"], sort_keys=True)
    assert status_texts(False) == status_texts(True)


def test_dropping_while_waiting_frees_the_seat():
    m = Match()
    a = m.join(None, 0.0)
    m.connection_lost("A", 1.0)
    assert m.join(a["token"], 2.0) == {"ok": False, "code": "bad_token"}
    assert m.join(None, 2.0)["seat"] == "A"


# --- rematch (#41, #25) -----------------------------------------------------------
def ended(**kw):
    ep = arena_episode(kw.pop("seed", 5))
    m, a, b = two(episode=ep, **kw)
    now = run(m, 0.0, 3)
    ep._duel.terminal = "won:A"
    m.advance(now + T)
    assert m.state == "ended"
    return m, a, b, now + T


def test_rematch_is_ignored_while_the_duel_is_running():
    m, _, _ = two()
    m.receive("A", '{"type":"rematch"}', 0.0)
    m.receive("B", '{"type":"rematch"}', 0.0)
    assert frames(m) == 0 and m.state == "playing"
    run(m, 0.0, 5)
    assert frames(m) == 5


def test_one_press_waits_and_both_presses_restart_with_the_same_seed():
    m, _, _, now = ended(seed=5)
    m.drain("A"), m.drain("B")
    m.receive("A", '{"type":"rematch"}', now)
    sa = [x for x in m.drain("A") if x["type"] == "status"][-1]
    sb = [x for x in m.drain("B") if x["type"] == "status"][-1]
    assert sa["state"] == "ended" and sa["rematch"] == "waiting"
    assert sa["text"] == "Waiting for rival…"
    assert sb["rematch"] == "rival_wants" and sb["text"] == "Rival wants a rematch"
    assert m.state == "ended"
    m.receive("B", '{"type":"rematch"}', now)
    assert m.state == "playing" and frames(m) == 0
    assert m.episode.seed == 5 and m.episode.outcome()["status"] == "ongoing"
    m.advance(now + T)
    assert frames(m) == 1


def test_a_second_press_by_the_same_seat_does_not_restart():
    m, _, _, now = ended()
    m.receive("A", '{"type":"rematch"}', now)
    m.receive("A", '{"type":"rematch"}', now)
    assert m.state == "ended"


def test_rematch_status_is_the_same_whatever_the_hidden_state():
    def texts(disguised):
        ep = arena_episode(5)
        ep._duel.rivals["B"].disguised = disguised
        m, _, _ = two(episode=ep)
        now = run(m, 0.0, 3)
        ep._duel.terminal = "won:A"
        m.advance(now + T)
        m.receive("A", '{"type":"rematch"}', now + T)
        return json.dumps([x for x in m.drain("B") if x["type"] == "status"], sort_keys=True)
    assert texts(False) == texts(True)


def test_the_trace_of_each_duel_is_kept_across_a_rematch():
    m, _, _, now = ended()
    first = m.trace()
    m.receive("A", '{"type":"rematch"}', now)
    m.receive("B", '{"type":"rematch"}', now)
    assert m.past_traces and m.past_traces[-1]["seed"] == first["seed"]
    assert m.trace()["ticks"] == []


def test_in_the_ai_mode_one_press_restarts():
    m = Match(seed=2, rival="baseline")
    a = m.join(None, 0.0)
    assert a["seat"] == "A" and m.state == "playing"
    assert m.join(None, 0.0) == {"ok": False, "code": "full"}
    now = run(m, 0.0, 5)
    assert frames(m) == 5
    m.episode._duel.terminal = "won:B"
    m.advance(now + T)
    assert m.state == "ended"
    m.receive("A", '{"type":"rematch"}', now + T)
    assert m.state == "playing" and frames(m) == 0 and m.episode.seed == 2


def test_the_ai_rival_acts_through_its_own_observation_and_is_labelled():
    m = Match(seed=2, rival="baseline")
    m.join(None, 0.0)
    run(m, 0.0, 120)
    st = [x for x in m.drain("A") if x["type"] == "state"][-1]
    assert "AI rival" in st["rival"]
    assert any(s == "B" for t in m.trace()["ticks"] for s, _ in t)


def test_forfeit_rule_has_a_rule_source_map_row():
    from pathlib import Path
    text = (Path(__file__).resolve().parent.parent / "docs" / "RULE_SOURCE_MAP.md").read_text()
    row = next(line for line in text.splitlines() if line.startswith("| R-S01 "))
    assert "`design`" in row and "#38" in row and "server/match.py" in row


# --- inherited GATE-wave3 QA findings (T14-fix1) ------------------------------------
def test_a_slow_ai_rival_never_stalls_the_tick_loop_and_is_labelled():
    import time
    from server.rival import TimeLimitedRival

    class Slow:
        label = "AI rival: slow (test)"

        def __call__(self, obs, legal):
            time.sleep(0.6)
            return legal[0] if legal else None

    m = Match(seed=1, rival="baseline", rival_budget_s=0.01)
    m.game.rival = TimeLimitedRival(Slow(), 0.01)
    m.join(None, 0.0)
    t0 = time.perf_counter()
    run(m, 0.0, 30)
    assert time.perf_counter() - t0 < 0.5            # 30 ticks, one 0.6 s answer pending
    assert frames(m) == 30
    st = [x for x in m.drain("A") if x["type"] == "state"][-1]
    assert "WAIT" not in st["rival"] and "fallback" not in st["rival"].lower().replace("fallback(s)", "")
    assert all(s != "B" for t in m.trace()["ticks"] for s, _ in t)   # labelled WAIT, no input
    fb = m.trace()["fallbacks"]
    assert fb and all(f["source"] == "fallback" and f["seat"] == "B" for f in fb)
    assert "fallback" not in json.dumps(m.drain("A"))                # never sent to the human


def test_labels_human_vs_human_has_no_rival_kind_and_neutral_hides_the_ai_kind():
    m, _, _ = two()
    run(m, 0.0, 3)
    assert all("rival" not in x for x in m.drain("A") if x["type"] == "state")
    n = Match(seed=1, rival="baseline", neutral=True)
    n.join(None, 0.0)
    run(n, 0.0, 3)
    assert [x for x in n.drain("A") if x["type"] == "state"][-1]["rival"] == "Rival"
    k = Match(seed=1, rival="baseline")
    k.join(None, 0.0)
    run(k, 0.0, 3)
    assert "AI rival" in [x for x in k.drain("A") if x["type"] == "state"][-1]["rival"]


def test_online_page_publishes_no_test_hook():
    from pathlib import Path
    src = (Path(__file__).resolve().parent.parent / "web" / "online.js").read_text()
    assert "__smLast" not in src and "exposeForTests" not in src
