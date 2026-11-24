"""Seat controllers (pop/seats.py; docs/final/VERSUS_RUNNER.md, task T04).

Deterministic, offline. A controller sees one seat's observation and legal
list (copies) and answers one input name.
"""

from __future__ import annotations

from pop.seats import (KINDS, HumanController, PolicyController, RandomController,
                       ScriptedController, SeatController, WaitController, controller_seed)

LEGAL = ("WAIT", "LEFT", "RIGHT", "DRAW")


def test_builtin_controllers_follow_the_protocol():
    ctrls = [HumanController(), ScriptedController(["LEFT"]), WaitController(),
             PolicyController(lambda o, l: "WAIT"), RandomController()]
    for c in ctrls:
        assert isinstance(c, SeatController)
        assert c.kind in KINDS
        assert isinstance(c.name, str) and c.name
    assert [c.kind for c in ctrls] == ["human", "scripted", "fallback", "policy", "scripted"]


def test_scripted_plays_its_list_then_waits():
    c = ScriptedController(["LEFT", "DRAW"])
    assert [c.decide({}, LEGAL) for _ in range(4)] == ["LEFT", "DRAW", "WAIT", "WAIT"]


def test_scripted_reset_restarts_the_script():
    c = ScriptedController(["LEFT"])
    c.decide({}, LEGAL)
    c.reset(7)
    assert c.decide({}, LEGAL) == "LEFT"


def test_two_scripted_instances_share_no_state():
    script = ["LEFT", "RIGHT"]
    a, b = ScriptedController(script), ScriptedController(script)
    assert a.decide({}, LEGAL) == "LEFT"
    assert b.decide({}, LEGAL) == "LEFT"           # a's pop did not consume b's script
    script.append("DRAW")                          # the caller's list is not shared either
    assert a.decide({}, LEGAL) == "RIGHT"
    assert a.decide({}, LEGAL) == "WAIT"


def test_human_returns_latest_queued_input_then_waits():
    h = HumanController()
    assert h.decide({}, LEGAL) == "WAIT"
    h.queue("LEFT")
    h.queue("RIGHT")                               # a newer input replaces an older one
    assert h.decide({}, LEGAL) == "RIGHT"
    assert h.decide({}, LEGAL) == "WAIT"


def test_wait_controller_is_the_labelled_fallback_kind():
    w = WaitController()
    assert w.kind == "fallback"
    assert w.decide({"anything": 1}, LEGAL) == "WAIT"


def test_policy_controller_delegates_to_its_policy():
    seen = []

    def policy(obs, legal):
        seen.append((obs, legal))
        return legal[-1]

    p = PolicyController(policy, name="toy")
    assert p.decide({"x": 1}, LEGAL) == "DRAW"
    assert seen == [({"x": 1}, LEGAL)]
    assert p.name == "toy" and p.kind == "policy"


def test_random_controller_is_seeded_and_picks_only_legal_inputs():
    a, b = RandomController(), RandomController()
    a.reset(3)
    b.reset(3)
    picks_a = [a.decide({}, LEGAL) for _ in range(30)]
    picks_b = [b.decide({}, LEGAL) for _ in range(30)]
    assert picks_a == picks_b
    assert set(picks_a) <= set(LEGAL) and len(set(picks_a)) > 1


def test_controller_seed_is_per_seat_and_not_the_episode_seed():
    assert controller_seed(5, "A") == controller_seed(5, "A")
    assert controller_seed(5, "A") != controller_seed(5, "B")
    assert controller_seed(5, "A") != controller_seed(6, "A")
    assert all(controller_seed(s, seat) != s for s in range(50) for seat in "AB")


def test_keyed_controller_seed_differs_from_unkeyed_and_by_key():
    assert controller_seed(5, "A", key=b"k1") != controller_seed(5, "A")
    assert controller_seed(5, "A", key=b"k1") != controller_seed(5, "A", key=b"k2")
    assert controller_seed(5, "A", key=b"k1") == controller_seed(5, "A", key=b"k1")


def test_keyed_controller_seed_is_not_recoverable_without_the_key():
    s = controller_seed(4242, "B", key=b"held-by-the-evaluator")
    assert all(controller_seed(c, seat) != s for c in range(20_000) for seat in "AB")
