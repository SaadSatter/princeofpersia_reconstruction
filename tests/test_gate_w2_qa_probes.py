"""GATE-w2 (QA, Gate 1): independent probes of T01-fix1/fix2 and T04-fix2 on cd5c4aa.

Passing tests pin the closed findings (each was written to fail if the fix is
removed; see the gate report for the revert experiments). No production code
is touched.
"""

from __future__ import annotations

import itertools
import threading
import time

import pytest

from pop import arena
from pop.seats import WaitController
from pop.versus import VersusEpisode, arena_episode
from pop.versus_runner import VersusLimits, VersusRunner


def episode(a, b, posts):
    return VersusEpisode(arena.situation("A"), dict(arena.STARTS, A=a, B=b), 0,
                         guard_posts=posts)


# --- R-V26: TAKE over a downed guard -----------------------------------------------
# (actor cell, guard post): standing over the body, and facing it from one cell away.
CASES = {"ahead": ((2, 0, 4, +1), (5, 5)), "over": ((2, 0, 5, +1), (5, 5)),
         "over_left": ((2, 0, 5, -1), (5, 5)), "ahead_left": ((2, 0, 6, -1), (5, 5))}


def _setup(case, uniform, seat, sword):
    me, post = CASES[case]
    far = (1, 2, 2, +1)
    a, b = (me, far) if seat == "A" else (far, me)
    ep = episode(a, b, {"g": (2, 0, post, -1)})
    g = ep._duel.guards["g"]
    g.knock_out()
    g.uniform = uniform
    r = ep._duel.rivals[seat]
    if sword == "drawn":
        r.sword, r.stance = "drawn", "mid"
    ep.tick()
    return ep


@pytest.mark.parametrize("case", sorted(CASES))
@pytest.mark.parametrize("seat", ["A", "B"])
@pytest.mark.parametrize("sword", ["sheathed", "drawn"])
def test_take_is_legal_either_way_and_the_other_seat_cannot_tell(case, seat, sword):
    other = "B" if seat == "A" else "A"
    runs = {}
    for uniform in (True, False):
        ep = _setup(case, uniform, seat, sword)
        legal = (ep.legal_actions(seat), ep.legal_actions(other))
        assert "TAKE" in legal[0]
        res = ep.step(seat, "TAKE")
        assert res["accepted"]
        seen = []
        for _ in range(11):                      # the 12 TAKE frames, until the figure changes
            ep.tick()
            seen.append((ep.observe(other), ep.legal_actions(other), ep.outcome()))
        runs[uniform] = (legal, res, seen)
    assert runs[True][0] == runs[False][0]       # legal actions, both seats, before the input
    assert runs[True][1] == runs[False][1]       # the step reply
    assert runs[True][2] == runs[False][2]       # everything the other seat can read


def test_take_without_a_uniform_leaves_sword_and_state_alone_and_reports_to_the_actor_only():
    ep = _setup("ahead", False, "B", "drawn")
    ep.step("B", "TAKE")
    for _ in range(14):
        ep.tick()
    r = ep._duel.rivals["B"]
    assert (r.sword, r.stance, r.disguised) == ("drawn", "mid", False)
    assert ep.observe("B")["last_result"]["effect"] == "no_uniform"
    assert "no_uniform" not in repr(ep.observe("A")) + repr(ep.legal_actions("A"))
    assert ep.outcome()["invalid_inputs"] == {"A": 0, "B": 0}


def test_take_is_not_legal_when_disguised_or_with_no_body_in_reach():
    ep = _setup("ahead", True, "B", "sheathed")
    ep._duel.rivals["B"].disguised = True
    assert "TAKE" not in ep.legal_actions("B")
    ep = _setup("ahead", False, "B", "sheathed")
    ep._duel.rivals["B"].kid.col = 0             # out of reach
    ep.tick()
    assert "TAKE" not in ep.legal_actions("B")
    ep = episode((1, 2, 2, +1), (2, 0, 4, +1), {"g": (2, 0, (5, 5), -1)})   # guard alive
    ep.tick()
    assert "TAKE" not in ep.legal_actions("B")


def test_uniform_flag_never_appears_in_any_observation_or_reply():
    for uniform in (True, False):
        ep = _setup("ahead", uniform, "B", "sheathed")
        ep.step("B", "TAKE")
        for _ in range(14):
            ep.tick()
            for s in "AB":
                text = repr(ep.observe(s)) + repr(ep.legal_actions(s)) + repr(ep.outcome())
                assert "uniform" not in text.replace("no_uniform", "").replace("took_uniform", "")


# --- L2: figure order does not leak what stands behind a figure -----------------
@pytest.mark.parametrize("names", list(itertools.permutations(["a", "m", "z"])))
def test_figure_order_ignores_guard_names_and_rival_identity(names):
    def order(disguised):
        posts = {n: (2, 0, (5, 5), -1) for n in names[:2]}
        ep = episode((2, 0, 5, -1), (2, 1, 0, +1), posts)
        for n in names[:2]:
            ep._duel.guards[n].pause = 10_000
        if disguised:
            r = ep._duel.rivals["A"]
            r.disguised, r.sword, r.stance = True, "sheathed", None
            del ep._duel.guards[names[1]]
            ep._duel.guards[names[1]] = None
            del ep._duel.guards[names[1]]
        ep.tick()
        return [(f["kind"], f["row"], f["col"], f["posture"]) for f in ep.observe("B")["figures"]]
    assert order(False) == order(False)
    # a guard tied with a disguised rival lists in the same order whichever object is first
    ep1 = episode((2, 0, 5, -1), (2, 1, 0, +1), {"a": (2, 0, (5, 5), -1)})
    ep2 = episode((2, 0, 5, -1), (2, 1, 0, +1), {"z": (2, 0, (5, 5), -1)})
    for ep in (ep1, ep2):
        r = ep._duel.rivals["A"]
        r.disguised, r.sword, r.stance = True, "sheathed", None
        ep.tick()
    f = lambda ep: [x for x in ep.observe("B")["figures"] if x["row"] == 0]
    assert f(ep1) == f(ep2)


# --- T04-fix2 ------------------------------------------------------------------
class Ans:
    kind = "scripted"

    def __init__(self, ans):
        self.name, self.ans = "x", ans

    def decide(self, obs, legal):
        return self.ans


def _run(ans, threaded=True):
    return VersusRunner(lambda: arena_episode(time_limit_frames=30), {"A": Ans(ans), "B": WaitController()},
                        clock=lambda: 0.0, threaded=threaded).run(1)


class ClassProp:
    @property
    def __class__(self):
        return str


class ClassRaises:
    @property
    def __class__(self):
        raise RuntimeError("no class")


class StrClassWithBadRepr:
    @property
    def __class__(self):
        return str

    def __repr__(self):
        raise RuntimeError("no repr")


class SubclassClassProp(str):
    @property
    def __class__(self):
        return int


@pytest.mark.parametrize("make", [ClassProp, ClassRaises, StrClassWithBadRepr, lambda: SubclassClassProp("WAIT")])
@pytest.mark.parametrize("threaded", [True, False])
def test_class_spoofing_answers_never_crash_the_run(make, threaded):
    res = _run(make(), threaded)
    real_str = issubclass(type(make()), str)
    assert res["seats"]["A"]["fallbacks"] == (0 if real_str else res["seats"]["A"]["decisions"])
    assert res["outcome"]["status"] in ("terminal", "running")


def test_numpy_str_answers_still_work():
    import numpy as np
    res = _run(np.str_("WAIT"))
    assert res["seats"]["A"]["fallbacks"] == 0


class Slow:
    kind = "scripted"

    def __init__(self, delay):
        self.name, self.delay, self.active, self.max_active = "slow", delay, 0, 0
        self.lock = threading.Lock()

    def decide(self, obs, legal):
        with self.lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        time.sleep(self.delay)
        with self.lock:
            self.active -= 1
        return "WAIT"


def test_busy_is_shared_across_runner_instances_even_when_started_concurrently():
    s = Slow(0.25)
    lim = VersusLimits(timeout_s=0.02)
    f = lambda: arena_episode(time_limit_frames=24)
    out = []
    ts = [threading.Thread(target=lambda: out.append(
        VersusRunner(f, {"A": s, "B": WaitController()}, limits=lim).run(1))) for _ in range(3)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    assert s.max_active == 1
    assert len(out) == 3


def test_busy_clears_after_the_late_call_returns_across_runners():
    s = Slow(0.1)
    f = lambda: arena_episode(time_limit_frames=24)
    lim = VersusLimits(timeout_s=0.02)
    VersusRunner(f, {"A": s, "B": WaitController()}, limits=lim).run(1)
    time.sleep(0.3)
    res = VersusRunner(f, {"A": WaitController(), "B": WaitController()}, limits=lim).run(1)
    s2 = Slow(0.0)
    res = VersusRunner(f, {"A": s, "B": WaitController()}, limits=VersusLimits(timeout_s=1.0)).run(1)
    assert res["seats"]["A"]["busy"] == 0 and res["seats"]["A"]["timeouts"] == 0


@pytest.mark.parametrize("bad", [True, False, 1.5, 2.0, "3", None, [1]])
def test_decision_every_rejects_non_int(bad):
    with pytest.raises((TypeError, ValueError)):
        VersusRunner(lambda: arena_episode(time_limit_frames=12),
                     {"A": WaitController(), "B": WaitController()}, decision_every=bad)


@pytest.mark.parametrize("bad", [0, -1])
def test_decision_every_rejects_non_positive(bad):
    with pytest.raises(ValueError):
        VersusRunner(lambda: arena_episode(time_limit_frames=12),
                     {"A": WaitController(), "B": WaitController()}, decision_every=bad)


def test_decision_every_accepts_plain_ints():
    for n in (1, 2, 6):
        VersusRunner(lambda: arena_episode(time_limit_frames=12),
                     {"A": WaitController(), "B": WaitController()}, decision_every=n)
