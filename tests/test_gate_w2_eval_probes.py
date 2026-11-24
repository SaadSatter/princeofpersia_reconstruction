"""Gate 2 (Evaluation Specialist) re-review of wave 2 (cd5c4aa): boundary probes for
R-V26 (TAKE), QA1, QA3 and the T04-fix2 runner checks. Offline, no keys."""

from __future__ import annotations

import json
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


def body_world(uniform: bool, actor="B"):
    """A downed guard in front of `actor` (B); A is the other seat, in view, at a
    different spot. `uniform` says whether the body is still dressed."""
    ep = episode((2, 0, 1, +1), (2, 0, 4, +1), {"g": (2, 0, (5, 5), -1)})
    g = ep._duel.guards["g"]
    g.knock_out()
    g.uniform = uniform
    ep.tick()
    return ep


def j(x):
    return json.dumps(x, sort_keys=True, default=repr)


# --- R-V26: the other seat learns nothing from a TAKE over a stripped body ----

def test_other_seat_view_identical_during_every_take_frame():
    """B takes (or fails to take). A's observation and legal actions must be
    identical in both worlds for each frame of the TAKE, until the disguise
    itself appears (the one legitimate difference)."""
    worlds = [body_world(True), body_world(False)]
    for w in worlds:
        assert w.step("B", "TAKE")["accepted"]
    diverged = None
    for t in range(16):
        views = [(j(w.observe("A")), w.legal_actions("A")) for w in worlds]
        if views[0] != views[1]:
            diverged = t
            break
        for w in worlds:
            w.tick()
    # With a uniform the actor becomes a 'guard' in A's view at completion; that
    # is allowed, but it must not precede the TAKE animation's last frames.
    assert diverged is None or diverged >= 10, diverged


def test_failed_take_leaves_no_trace_in_the_other_seats_observation_afterwards():
    """After a TAKE over a stripped body completes, A sees B exactly as it would
    have seen B after any other 14 frames of standing still (no marker)."""
    stripped = body_world(False)
    stripped.step("B", "TAKE")
    idle = body_world(False)
    for _ in range(16):
        stripped.tick()
        idle.tick()
    sa, ia = stripped.observe("A"), idle.observe("A")
    fig = lambda o: [f for f in o["figures"] if f["kind"] == "rival"]
    assert [(f["row"], f["col"], f["posture"]) for f in fig(sa)] == \
           [(f["row"], f["col"], f["posture"]) for f in fig(ia)]
    assert "no_uniform" not in j(sa) and "no_uniform" not in j(stripped.legal_actions("A"))


def test_no_uniform_is_not_in_the_other_seats_observation_or_outcome():
    ep = body_world(False)
    ep.step("B", "TAKE")
    for _ in range(16):
        ep.tick()
    assert "no_uniform" not in j(ep.observe("A"))
    assert "no_uniform" not in j(ep.legal_actions("A"))


def test_take_legality_is_state_independent_over_any_body():
    """The acting seat's legal list is the same whether or not the body is dressed
    (closes GATE-T01 L1 for both seats)."""
    assert body_world(True).legal_actions("B") == body_world(False).legal_actions("B")
    assert body_world(True).legal_actions("A") == body_world(False).legal_actions("A")


def test_attempting_take_does_cost_the_actor_time_and_reveals_stripped_to_actor_only():
    """Disclosure for evaluation design: a TAKE attempt is the one probe that tells
    the actor whether another rival already stripped the body (cost: TAKE frames,
    sword state unchanged). The actor's own observation carries the answer."""
    ep = body_world(False)
    ep.step("B", "TAKE")
    for _ in range(16):
        ep.tick()
    assert ep._duel.last_result["B"]["effect"] == "no_uniform"
    assert not ep._duel.rivals["B"].disguised


# --- QA3: WAIT lingering is not observable as a different motion ---------------

def test_resent_wait_is_shown_as_standing_still_like_no_input():
    def view(send_wait):
        ep = episode((2, 0, 3, +1), (2, 1, 0, +1), {"g": (2, 0, (5, 5), -1)})
        r = ep._duel.rivals["A"]
        r.disguised, r.sword, r.stance = True, "sheathed", None
        out = []
        for _ in range(20):
            if send_wait:
                ep.step("A", "WAIT")
            ep.tick()
            out.append(j(ep.observe("B")["figures"]))
        return out
    assert view(True) == view(False)


# --- QA1: no figure shows `to: None` as a disguised move; arrival still visible --

def test_disguised_step_into_the_next_room_is_not_flagged_by_a_null_destination():
    ep = episode((2, 0, 0, -1), (2, 1, 5, +1), {})
    r = ep._duel.rivals["A"]
    r.disguised, r.sword, r.stance = True, "sheathed", None
    for _ in range(30):
        ep.step("A", "STEP")
        ep.tick()
        for f in ep.observe("B")["figures"]:
            m = f.get("motion")
            assert m is None or m["to"] is not None


# --- T04-fix2 -------------------------------------------------------------------

class Ans:
    kind = "scripted"

    def __init__(self, ans):
        self.name, self.ans = "x", ans

    def decide(self, obs, legal):
        return self.ans


def _run(ans, threaded=True):
    class C:
        def __call__(self):
            return 0.0
    return VersusRunner(lambda: arena_episode(time_limit_frames=30),
                        {"A": Ans(ans), "B": WaitController()}, clock=C(), threaded=threaded).run(1)


class StrSpoofSub(str):
    """A genuine str subclass that also lies about __class__ and __str__."""
    @property
    def __class__(self):
        return int

    def __str__(self):
        raise RuntimeError("no")


class RaisingClass:
    @property
    def __class__(self):
        raise RuntimeError("no class")


class RaisingHash(str):
    def __hash__(self):
        raise RuntimeError("no hash")


@pytest.mark.parametrize("threaded", [True, False])
@pytest.mark.parametrize("make", [lambda: StrSpoofSub("WAIT"), RaisingClass, lambda: RaisingHash("WAIT")],
                         ids=["strsub-lies", "class-raises", "hash-raises"])
def test_more_spoofed_answers_never_crash_the_run(make, threaded):
    res = _run(make(), threaded)
    recs = res["traces"]["A"]
    assert recs and all(r["input"] in ("WAIT", None) for r in recs)
    json.dumps(res["traces"])


@pytest.mark.parametrize("bad", [1.5, True, False, 2.0, "2", None])
def test_decision_every_rejects_non_int(bad):
    with pytest.raises((TypeError, ValueError)):
        VersusRunner(lambda: arena_episode(time_limit_frames=30),
                     {"A": WaitController(), "B": WaitController()}, decision_every=bad)


def test_decision_every_zero_and_negative_still_refused():
    for bad in (0, -3):
        with pytest.raises(ValueError):
            VersusRunner(lambda: arena_episode(time_limit_frames=30),
                         {"A": WaitController(), "B": WaitController()}, decision_every=bad)


class Slow:
    kind, name = "scripted", "slow"

    def __init__(self, delay):
        self.delay, self.active, self.max_active, self.lock = delay, 0, 0, threading.Lock()

    def decide(self, obs, legal):
        with self.lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        time.sleep(self.delay)
        with self.lock:
            self.active -= 1
        return "WAIT"


def test_busy_holds_when_two_runners_run_at_the_same_time_in_threads():
    """The seat-swapped pair run in parallel (the realistic pool): the shared
    controller is never called concurrently."""
    s = Slow(0.25)
    lim = VersusLimits(timeout_s=0.02)
    mk = lambda: VersusRunner(lambda: arena_episode(time_limit_frames=24),
                              {"A": s, "B": WaitController()}, limits=lim)
    ts = [threading.Thread(target=lambda: mk().run(1)) for _ in range(2)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert s.max_active == 1


def test_busy_clears_after_the_call_returns_and_the_controller_is_used_again():
    s = Slow(0.1)
    lim = VersusLimits(timeout_s=0.02)
    f = lambda: arena_episode(time_limit_frames=24)
    VersusRunner(f, {"A": s, "B": WaitController()}, limits=lim).run(1)
    time.sleep(0.3)
    res = VersusRunner(f, {"A": s, "B": WaitController()}, limits=VersusLimits(timeout_s=1.0)).run(1)
    assert res["seats"]["A"]["busy"] == 0
    assert res["seats"]["A"].get("reset_error") in (None, "")


def test_busy_registry_is_not_left_holding_finished_calls():
    from pop import versus_runner as vr
    s = Slow(0.05)
    VersusRunner(lambda: arena_episode(time_limit_frames=24), {"A": s, "B": WaitController()},
                 limits=VersusLimits(timeout_s=0.01)).run(1)
    time.sleep(0.3)
    VersusRunner(lambda: arena_episode(time_limit_frames=24), {"A": s, "B": WaitController()},
                 limits=VersusLimits(timeout_s=1.0)).run(1)
    assert id(s) not in vr._LATE
