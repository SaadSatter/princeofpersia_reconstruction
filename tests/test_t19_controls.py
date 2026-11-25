"""T19, decision #55 (Saad, 2026-11-24): either control scheme.

Human vs AI and online: WASD + F/G/T/left Shift and arrows + . / ' right Shift both drive
the player's own seat, and keys from both sets held together combine as one seat's keys.
Local two-player on one keyboard keeps seat A = WASD set, seat B = arrows set.
"""

from __future__ import annotations

import json

import pytest

import play
from server.match import TICK_S, Match
from web import bridge

WASD = {"left": "a", "right": "d", "up": "w", "down": "s", "attack": "f", "draw": "g",
        "take": "t", "shift": "lshift"}
ARROWS = {"left": "left", "right": "right", "up": "up", "down": "down", "attack": ".",
          "draw": "/", "take": "'", "shift": "rshift"}


def art():
    return bridge.load_art()


def test_play_py_and_the_bridge_still_agree_on_the_two_sets():
    assert bridge.KEY_MAP == {"A": WASD, "B": ARROWS} == play.VERSUS_KEYS


@pytest.mark.parametrize("seat", ["A", "B"])
@pytest.mark.parametrize("scheme", [WASD, ARROWS])
def test_human_vs_ai_either_set_drives_the_players_seat(seat, scheme):
    g = bridge.WebGame(mode="human_vs_ai", seed=1, human_seat=seat, art=art())
    held = g.press({scheme["right"]: True, scheme["shift"]: True})
    assert held == {seat: {"held": ["right"], "shift": True}}


def test_human_vs_ai_combines_keys_from_both_sets_as_one_seats_held_keys():
    g = bridge.WebGame(mode="human_vs_ai", seed=1, human_seat="A", art=art())
    held = g.press({"a": True, "up": True, "'": True})          # WASD left, arrow up, arrow take
    assert held == {"A": {"held": ["left", "take", "up"], "shift": False}}
    assert g.press({"d": True, "right": True}) == {"A": {"held": ["right"], "shift": False}}
    assert g.press({"rshift": True}) == {"A": {"held": [], "shift": True}}


def moved(seat, keys, mode="human_vs_ai"):
    g = bridge.WebGame(mode=mode, seed=3, human_seat=seat, art=art())
    for _ in range(30):
        g.press(keys)
        p = g.tick()
    return json.dumps(g.episode.observe(seat)["me"], sort_keys=True)


@pytest.mark.parametrize("seat", ["A", "B"])
def test_the_arrows_and_wasd_both_move_the_players_seat_in_human_vs_ai(seat):
    idle = moved(seat, {})
    assert moved(seat, {"left": True}) != idle
    assert moved(seat, {"a": True}) != idle
    assert moved(seat, {"d": True}) != idle


def test_local_two_players_still_splits_the_sets():
    g = bridge.WebGame(mode="local_two_players", seed=1, art=art())
    held = g.press({"a": True, "lshift": True, "up": True, "'": True})
    assert held == {"A": {"held": ["left"], "shift": True},
                    "B": {"held": ["take", "up"], "shift": False}}


def test_local_two_players_a_ignores_the_arrows_and_b_ignores_wasd():
    idle = [moved("A", {}, "local_two_players"), moved("B", {}, "local_two_players")]
    assert moved("A", {"left": True, "right": True, "up": True}, "local_two_players") == idle[0]
    assert moved("B", {"a": True, "d": True, "w": True}, "local_two_players") == idle[1]


def test_to_seat_keys_renames_either_set_into_the_seats_own_names():
    assert bridge.to_seat_keys("A", ["left", "up", "rshift", "'"]) == {"a", "w", "lshift", "t"}
    assert bridge.to_seat_keys("B", ["a", "w", "lshift", "t", "d"]) == {"left", "up", "rshift", "'", "right"}
    assert bridge.to_seat_keys("A", ["zzz", 5, None]) == set()


def duel_match():
    m = Match(seed=11)
    m.join(None, 0.0)
    m.join(None, 0.0)
    return m


def run_match(m, keys_by_seat, ticks=40):
    now = 0.0
    for seat, keys in keys_by_seat.items():
        m.receive(seat, json.dumps({"type": "keys", "keys": keys}), now)
    for _ in range(ticks):
        now += TICK_S
        m.advance(now)
    return {s: json.dumps(m.episode.observe(s)["me"], sort_keys=True) for s in ("A", "B")}


def test_online_either_set_drives_the_senders_own_seat_only():
    idle = run_match(duel_match(), {})
    for seat, other in (("A", "B"), ("B", "A")):
        for keys in (["left"], ["a"], ["d"], ["right"]):
            got = run_match(duel_match(), {seat: keys})
            assert got[seat] != idle[seat], (seat, keys)
            assert got[other] == idle[other], (seat, keys)


def test_online_the_two_sets_give_the_same_play_for_a_seat():
    by_arrows = run_match(duel_match(), {"A": ["right", "rshift"]})
    by_wasd = run_match(duel_match(), {"A": ["d", "lshift"]})
    assert by_arrows == by_wasd


def test_online_keys_from_both_sets_combine():
    both = run_match(duel_match(), {"A": ["d", "up"]})
    arrows = run_match(duel_match(), {"A": ["right", "up"]})
    mixed = run_match(duel_match(), {"A": ["d", "up"]})
    assert both == arrows == mixed


def test_online_vs_ai_either_set_drives_seat_a():
    def play_ai(keys):
        m = Match(seed=5, rival="baseline")
        m.join(None, 0.0)
        now = 0.0
        m.receive("A", json.dumps({"type": "keys", "keys": keys}), now)
        for _ in range(30):
            now += TICK_S
            m.advance(now)
        m.close()
        return json.dumps(m.episode.observe("A")["me"], sort_keys=True)
    assert play_ai(["left"]) == play_ai(["a"]) != play_ai([])


def test_online_still_ignores_names_that_belong_to_no_seat():
    m = duel_match()
    m.receive("A", json.dumps({"type": "keys", "keys": ["zzz", "r", "Enter"]}), 0.0)
    assert m.held["A"] == set()
