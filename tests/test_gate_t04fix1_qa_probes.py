"""Gate 1 QA re-review of T04-fix1 (commit 616ba8d): variants of each attack.

Passing tests pin closed findings. Tests marked xfail(strict=True) reproduce
new findings F1.. (see the QA report); they fail against 616ba8d.
"""

from __future__ import annotations

import json
import threading
import time

import pytest

from pop.seats import (PolicyController, RandomController, ScriptedController,
                       WaitController, controller_seed)
from pop.versus import arena_episode
from pop.versus_runner import (EpisodeView, VersusLimits, VersusRunner, save_traces, replay)


def still():
    return 0.0


def fac(limit=60):
    return lambda: arena_episode(time_limit_frames=limit)


class Answer:
    kind = "policy"

    def __init__(self, make, name="answer"):
        self.make, self.name = make, name

    def decide(self, observation, legal):
        return self.make()


def run(ctrl, **kw):
    return VersusRunner(fac(12), {"A": ctrl, "B": WaitController()}, clock=still, **kw).run(0)


# ---- QA-1/2/3 variants -------------------------------------------------------
class Eq(str):
    def __eq__(self, o):
        return True
    __hash__ = str.__hash__


class StrOverride(str):
    def __str__(self):
        return "WAIT"
    def __repr__(self):
        raise RuntimeError("no repr")
    def __len__(self):
        raise RuntimeError("no len")


class HashLiar(str):
    def __hash__(self):
        return hash("WAIT")
    def __eq__(self, o):
        return True
    def __contains__(self, o):
        return True
    def __iter__(self):
        raise RuntimeError


@pytest.mark.parametrize("cls", [Eq, StrOverride, HashLiar])
def test_str_subclass_variants_are_refused_or_played_as_plain_text(cls):
    res = run(Answer(lambda: cls("NOT_AN_ACTION")))
    recs = res["traces"]["A"]
    assert all(r["input"] in (None, "WAIT") for r in recs)
    assert all(r["source"] == "fallback" and r["fallback_reason"] == "illegal" for r in recs)
    json.dumps(res["traces"])


def test_str_subclass_with_legal_text_is_recorded_as_exact_str():
    class Sub(str):
        def strip(self, *a):
            return "JUMP_RIGHT"
    res = run(Answer(lambda: Sub("WAIT")))
    for r in res["traces"]["A"]:
        assert type(r["input"]) is str and r["input"] == "WAIT"


def test_numpy_str_answer_still_works():
    import numpy as np
    res = run(Answer(lambda: np.str_("WAIT")))
    assert all(r["source"] == "controller" and type(r["input"]) is str for r in res["traces"]["A"])


class Liar:
    """Not a str, but isinstance(x, str) is True."""
    @property
    def __class__(self):
        return str


def test_isinstance_spoofing_answer_is_a_fallback_not_a_crash():
    res = run(Answer(Liar))
    assert all(r["source"] == "fallback" for r in res["traces"]["A"])


class BadStrExc(Exception):
    def __str__(self):
        raise ValueError("x")
    def __repr__(self):
        raise ValueError("x")


def test_exception_with_raising_str_is_an_error_fallback():
    class Boom:
        kind, name = "policy", "boom"
        def decide(self, o, l):
            raise BadStrExc()
    res = run(Boom())
    assert {r["fallback_reason"] for r in res["traces"]["A"]} == {"error"}


def test_unhashable_and_weird_answers_are_malformed():
    for make in (lambda: ["WAIT"], lambda: {"WAIT"}, lambda: None, lambda: b"WAIT",
                 lambda: float("nan"), lambda: object()):
        res = run(Answer(make))
        assert {r["fallback_reason"] for r in res["traces"]["A"]} == {"malformed"}


# ---- reset / error variants -----------------------------------------------------
def test_reset_raising_baseexception_is_recorded_and_seat_plays():
    class C:
        kind, name = "policy", "c"
        def reset(self, seed):
            raise SystemExit(3)
        def decide(self, o, l):
            return "WAIT"
    res = run(C())
    assert res["seats"]["A"]["reset_error"].startswith("SystemExit")
    assert res["seats"]["A"]["fallbacks"] == 0


def test_decide_that_never_returns_hits_timeout_then_busy():
    gate = threading.Event()
    calls = []

    class Hang:
        kind, name = "policy", "hang"
        def decide(self, o, l):
            calls.append(1)
            gate.wait(5)
            return "WAIT"
    t0 = time.time()
    res = VersusRunner(fac(24), {"A": Hang(), "B": WaitController()},
                       limits=VersusLimits(timeout_s=0.05)).run(0)
    gate.set()
    assert len(calls) == 1
    reasons = [r["fallback_reason"] for r in res["traces"]["A"]]
    assert reasons[0] == "timeout" and set(reasons[1:]) == {"busy"}
    assert res["seats"]["A"]["busy"] == len(reasons) - 1
    assert time.time() - t0 < 3


def test_busy_recovers_after_late_call_returns():
    gate = threading.Event()
    seen = []

    class C:
        kind, name = "policy", "c"
        n = 0
        def decide(self, o, l):
            self.n += 1
            if self.n == 1:
                gate.wait(5)
            seen.append(self.n)
            return "WAIT"
    c = C()
    runner = VersusRunner(fac(6 * 8), {"A": c, "B": WaitController()},
                          limits=VersusLimits(timeout_s=0.05))
    orig = runner._decide
    def decide(seat, ctrl, obs, legal, frame):
        if frame == 12:
            gate.set()
            time.sleep(0.1)
        return orig(seat, ctrl, obs, legal, frame)
    runner._decide = decide
    res = runner.run(0)
    reasons = [r["fallback_reason"] for r in res["traces"]["A"]]
    assert reasons[0] == "timeout" and reasons[1] == "busy"
    assert reasons[2:] == [None] * (len(reasons) - 2)


def test_busy_counts_toward_max_fallbacks_and_aborts():
    gate = threading.Event()

    class Hang:
        kind, name = "policy", "hang"
        def decide(self, o, l):
            gate.wait(5)
            return "WAIT"
    res = VersusRunner(fac(120), {"A": Hang(), "B": WaitController()},
                       limits=VersusLimits(timeout_s=0.05, max_fallbacks=2)).run(0)
    gate.set()
    assert res["runner_terminal"] == "max_fallbacks:A"
    assert res["seats"]["A"]["fallbacks"] == 3


def test_busy_is_shared_across_runner_instances_for_one_controller():
    """F1: a second VersusRunner (e.g. the seat-swapped half of a pair) must not call a
    controller whose earlier call, started by another runner, is still running."""
    gate = threading.Event()
    active = []
    peak = [0]
    lock = threading.Lock()

    class C:
        kind, name = "policy", "c"
        n = 0
        def decide(self, o, l):
            with lock:
                self.n += 1
                first = self.n == 1
                active.append(1)
                peak[0] = max(peak[0], len(active))
            if first:
                gate.wait(3)
            with lock:
                active.pop()
            return "WAIT"
    c = C()
    lim = VersusLimits(timeout_s=0.05)
    VersusRunner(fac(6), {"A": c, "B": WaitController()}, limits=lim).run(0)
    VersusRunner(fac(6), {"A": c, "B": WaitController()}, limits=lim, swap_seats=True).run(0)
    gate.set()
    assert peak[0] == 1


# ---- on_frame / EpisodeView --------------------------------------------------------
def test_on_frame_view_is_never_given_to_a_controller_and_cannot_mutate():
    seen = []

    class Spy:
        kind, name = "policy", "spy"
        def decide(self, o, l):
            seen.append((o, l))
            return "WAIT"
    views = []
    VersusRunner(fac(12), {"A": Spy(), "B": WaitController()}, clock=still,
                 on_frame=lambda f, v: views.append(v)).run(0)
    assert views and all(isinstance(v, EpisodeView) for v in views)
    for o, l in seen:
        assert not any(isinstance(x, EpisodeView) for x in (o, l))
    v = views[0]
    for attr in ("step", "tick", "reset", "_ep", "episode"):
        assert not hasattr(v, attr)
    with pytest.raises(AttributeError):
        v.observe = None
    # mutating what the view returns does not change the episode
    snap = v.snapshot()
    o = v.observe("A")
    o.clear()
    v.snapshot()["frames"] = -1 if "frames" in v.snapshot() else None
    assert v.snapshot() == snap


def test_on_frame_does_not_change_results():
    mk = lambda: {"A": RandomController(), "B": RandomController()}
    a = VersusRunner(fac(120), mk(), clock=still).run(3)
    b = VersusRunner(fac(120), mk(), clock=still, on_frame=lambda f, v: (v.observe("A"), v.snapshot())).run(3)
    for k in ("final_snapshot_sha256", "traces", "frames", "status"):
        assert a[k] == b[k]


def test_on_frame_frames_are_consecutive_and_exception_propagates():
    got = []
    VersusRunner(fac(12), {"A": WaitController(), "B": WaitController()}, clock=still,
                 on_frame=lambda f, v: got.append(f)).run(0)
    assert got == list(range(1, len(got) + 1)) and got[-1] == 12

    def boom(f, v):
        raise ValueError("metric bug")
    with pytest.raises(ValueError):
        VersusRunner(fac(12), {"A": WaitController(), "B": WaitController()}, clock=still,
                     on_frame=boom).run(0)


def test_on_frame_view_observe_leaks_nothing_to_controller_via_shared_objects():
    """A metric that mutates the view's copy must not alter what a controller sees next."""
    class Rec:
        kind, name = "policy", "rec"
        def __init__(self):
            self.obs = []
        def decide(self, o, l):
            self.obs.append(json.dumps(o, sort_keys=True))
            return "WAIT"
    def trash(f, v):
        for s in ("A", "B"):
            v.observe(s).clear()
    r1, r2 = Rec(), Rec()
    VersusRunner(fac(36), {"A": r1, "B": WaitController()}, clock=still).run(0)
    VersusRunner(fac(36), {"A": r2, "B": WaitController()}, clock=still, on_frame=trash).run(0)
    assert r1.obs == r2.obs


# ---- fast path ----------------------------------------------------------------------
@pytest.mark.parametrize("kw", [dict(copy_mode="json"), dict(threaded=False),
                                dict(copy_mode="json", threaded=False)])
@pytest.mark.parametrize("swap", [False, True])
def test_fast_path_matches_default_for_a_deterministic_controller(kw, swap):
    mk = lambda: {"A": RandomController("x"), "B": RandomController("y")}
    base = VersusRunner(fac(240), mk(), clock=still, swap_seats=swap).run(5)
    fast = VersusRunner(fac(240), mk(), clock=still, swap_seats=swap, **kw).run(5)
    for k in ("final_snapshot_sha256", "frames", "status", "winner_slot"):
        assert base[k] == fast[k]
    assert base["traces"] == fast["traces"]
    assert fast["runner"] == {"copy_mode": kw.get("copy_mode", "deepcopy"),
                              "threaded": kw.get("threaded", True)}


def test_json_copy_gives_the_same_observation_as_deepcopy_for_a_controller():
    """F2 probe: what a controller sees must be equal in both modes (tuples/keys)."""
    def collect(mode):
        got = []
        class C:
            kind, name = "policy", "c"
            def decide(self, o, l):
                got.append((o, l))
                return "WAIT"
        VersusRunner(fac(60), {"A": C(), "B": WaitController()}, clock=still,
                     copy_mode=mode).run(2)
        return got
    assert collect("deepcopy") == collect("json")


@pytest.mark.parametrize("mode", ["deepcopy", "json"])
def test_controller_mutation_of_its_copy_cannot_reach_the_episode(mode):
    class Vandal:
        kind, name = "policy", "v"
        def decide(self, o, l):
            for v in list(o.values()):
                if isinstance(v, (dict, list)):
                    v.clear()
            o.clear()
            return "WAIT"
    a = VersusRunner(fac(60), {"A": Vandal(), "B": WaitController()}, clock=still,
                     copy_mode=mode, threaded=False).run(0)
    b = VersusRunner(fac(60), {"A": WaitController(), "B": WaitController()}, clock=still).run(0)
    assert a["final_snapshot_sha256"] == b["final_snapshot_sha256"]


def test_inline_mode_errors_are_fallbacks_and_keyboardinterrupt_propagates():
    class C:
        kind, name = "policy", "c"
        def decide(self, o, l):
            raise SystemExit(1)
    res = run(C(), threaded=False)
    assert {r["fallback_reason"] for r in res["traces"]["A"]} == {"error"}

    class K:
        kind, name = "policy", "k"
        def decide(self, o, l):
            raise KeyboardInterrupt
    with pytest.raises(KeyboardInterrupt):
        run(K(), threaded=False)


def test_inline_mode_slow_call_is_still_a_timeout_by_the_injected_clock():
    t = [0.0]
    clock = lambda: t[0]
    class Slow:
        kind, name = "policy", "slow"
        def decide(self, o, l):
            t[0] += 9.0
            return "WAIT"
    res = VersusRunner(fac(12), {"A": Slow(), "B": WaitController()}, clock=clock,
                       threaded=False).run(0)
    assert {r["fallback_reason"] for r in res["traces"]["A"]} == {"timeout"}


def test_bad_copy_mode_rejected():
    with pytest.raises(ValueError):
        VersusRunner(fac(), {"A": WaitController(), "B": WaitController()}, copy_mode="pickle")


# ---- seed_key ---------------------------------------------------------------------------
KEY = b"qa-secret-key-0123"


def test_seed_key_is_not_written_anywhere(tmp_path):
    res = VersusRunner(fac(24), {"A": RandomController(), "B": RandomController()},
                       clock=still, seed_key=KEY).run(9)
    paths = save_traces(res, tmp_path)
    blob = json.dumps(res, default=repr) + "".join(p.read_text() for p in paths.values())
    assert KEY.decode() not in blob and KEY.hex() not in blob and repr(KEY) not in blob
    assert "seed_key" not in blob


def test_seed_key_changes_controller_seed_and_is_deterministic():
    seen = []
    class C:
        kind, name = "policy", "c"
        def reset(self, seed):
            seen.append(seed)
        def decide(self, o, l):
            return "WAIT"
    for key in (None, KEY, KEY, b"other"):
        VersusRunner(fac(6), {"A": C(), "B": WaitController()}, clock=still, seed_key=key).run(1)
    assert seen[0] == controller_seed(1, "A") and seen[1] == seen[2] == controller_seed(1, "A", KEY)
    assert len({seen[0], seen[1], seen[3]}) == 3


def test_seed_key_not_in_runner_result_repr_or_error_text():
    r = VersusRunner(fac(6), {"A": WaitController(), "B": WaitController()}, seed_key=KEY)
    assert KEY.decode() not in repr(r.limits)
    res = r.run(0)
    assert KEY.decode() not in repr(res)


# ---- limits validation variants -------------------------------------------------------
@pytest.mark.parametrize("bad", [0, -1, float("nan"), float("inf"), None, True, "5", 0.0])
def test_timeout_validation(bad):
    with pytest.raises((TypeError, ValueError)):
        VersusLimits(timeout_s=bad)


@pytest.mark.parametrize("bad", [1.5, "6", None, True])
def test_decision_every_validation(bad):
    with pytest.raises((TypeError, ValueError)):
        VersusRunner(fac(), {"A": WaitController(), "B": WaitController()}, decision_every=bad)
