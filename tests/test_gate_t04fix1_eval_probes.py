"""Gate 2 (Evaluation Specialist) re-review of T04-fix1 (616ba8d): probes around
the fixes and the new surface (on_frame, fast path, seed_key, busy).
Offline; real-time sleeps well under one second."""

from __future__ import annotations

import gc
import json
import threading
import time

import pytest

from pop.seats import RandomController, WaitController, controller_seed
from pop.versus import SEATS, arena_episode
from pop.versus_runner import (EpisodeView, VersusLimits, VersusRunner, digest, load_traces,
                               replay, save_traces)


def factory(limit=360):
    return lambda: arena_episode(time_limit_frames=limit)


class Clock:
    def __call__(self):
        return 0.0


class Rec:
    kind = "scripted"

    def __init__(self, name, inner=None):
        self.name, self.inner, self.seen = name, inner or RandomController(name), []

    def reset(self, seed):
        self.inner.reset(seed)

    def decide(self, obs, legal):
        self.seen.append(json.dumps(obs, sort_keys=True, default=repr))
        return self.inner.decide(obs, legal)


def strip(res):
    out = json.loads(json.dumps(res, default=repr))
    for s in SEATS:
        for r in out["traces"][s]:
            r.pop("latency_ms")
    out.pop("runner")
    return out


# --- fast path: same results, same observations ---------------------------------
@pytest.mark.parametrize("seed", [1, 2, 5, 11])
@pytest.mark.parametrize("swap", [False, True])
def test_fast_path_matches_default_on_same_seed(seed, swap):
    runs = {}
    for mode, threaded in (("deepcopy", True), ("json", False), ("json", True), ("deepcopy", False)):
        c = {"A": Rec("a"), "B": Rec("b")}
        res = VersusRunner(factory(), c, clock=Clock(), swap_seats=swap, copy_mode=mode,
                           threaded=threaded).run(seed)
        runs[(mode, threaded)] = (strip(res), c["A"].seen, c["B"].seen)
    base = runs[("deepcopy", True)]
    for k, v in runs.items():
        assert v == base, k


def test_json_copy_turns_non_json_into_json_types_only_and_nan_is_not_silently_passed():
    # a controller given the JSON copy never sees a tuple the default would show
    class T(Rec):
        def decide(self, obs, legal):
            def walk(v):
                assert not isinstance(v, tuple), "tuple in json mode"
                if isinstance(v, dict):
                    [walk(x) for x in v.values()]
                elif isinstance(v, list):
                    [walk(x) for x in v]
            walk(obs)
            return "WAIT"
    VersusRunner(factory(240), {"A": T("a"), "B": T("b")}, clock=Clock(), copy_mode="json").run(3)


def test_fast_path_copy_is_still_a_copy():
    class Mut:
        kind, name = "scripted", "m"
        def decide(self, obs, legal):
            obs["me"] = "pwned"; obs.clear()
            return "WAIT"
    for mode in ("deepcopy", "json"):
        ep_holder = []
        def f():
            ep = arena_episode(time_limit_frames=120); ep_holder.append(ep); return ep
        VersusRunner(f, {"A": Mut(), "B": Mut()}, clock=Clock(), copy_mode=mode,
                     threaded=False).run(4)
        assert "me" in ep_holder[0].observe("A")


# --- on_frame ------------------------------------------------------------------
def test_on_frame_never_reaches_a_controller_and_view_has_no_mutators():
    seen = {}
    class Probe:
        kind, name = "scripted", "p"
        def decide(self, obs, legal):
            frame = __import__("sys")._getframe(1)
            seen.setdefault("locals", set()).update(
                type(v).__name__ for v in frame.f_locals.values())
            return "WAIT"
        def reset(self, seed):
            pass
    calls = []
    VersusRunner(factory(120), {"A": Probe(), "B": Probe()}, clock=Clock(),
                 on_frame=lambda f, v: calls.append((f, v))).run(2)
    assert calls and all(isinstance(v, EpisodeView) for _, v in calls)
    v = calls[0][1]
    for name in ("step", "tick", "reset", "_duel", "episode"):
        assert not hasattr(v, name)
    with pytest.raises(AttributeError):
        v.observe = None
    with pytest.raises(AttributeError):
        v.step = 1
    # frames are consecutive after each tick; frame 0 (initial state) is never reported
    assert [f for f, _ in calls][:3] == [1, 2, 3]


def test_on_frame_view_returns_copies():
    def hook(frame, view):
        o = view.observe("A"); o.clear()
        s = view.snapshot(); s.clear()
        view.legal_actions("A")
    a = VersusRunner(factory(120), {"A": Rec("a"), "B": Rec("b")}, clock=Clock()).run(6)
    b = VersusRunner(factory(120), {"A": Rec("a"), "B": Rec("b")}, clock=Clock(),
                     on_frame=hook).run(6)
    assert strip(a) == strip(b)


def test_on_frame_exception_propagates_not_swallowed():
    def hook(f, v):
        raise ValueError("metric bug")
    with pytest.raises(ValueError):
        VersusRunner(factory(60), {"A": WaitController(), "B": WaitController()},
                     clock=Clock(), on_frame=hook).run(1)


def test_on_frame_sees_other_seats_observation_with_disguise_identity_truth():
    # the scenario metrics need the TRUE state: snapshot reveals what a seat cannot
    got = []
    VersusRunner(factory(60), {"A": WaitController(), "B": WaitController()}, clock=Clock(),
                 on_frame=lambda f, v: got.append(v.snapshot())).run(1)
    assert got and isinstance(got[0], dict)


# --- seed_key --------------------------------------------------------------------
def test_seed_key_not_in_result_or_traces(tmp_path):
    key = b"SECRETKEYSECRET1"
    res = VersusRunner(factory(120), {"A": Rec("a"), "B": Rec("b")}, clock=Clock(),
                       seed_key=key).run(3)
    save_traces(res, tmp_path)
    blob = json.dumps(res, default=repr) + "".join(p.read_text() for p in tmp_path.iterdir())
    assert "SECRETKEY" not in blob and key.hex() not in blob and repr(key) not in blob
    runner = VersusRunner(factory(60), {"A": Rec("a"), "B": Rec("b")}, seed_key=key)
    # not reachable from a controller via public attributes of what it is given
    assert controller_seed(3, "A", key) != controller_seed(3, "A")


def test_seed_key_changes_controller_stream_but_replay_is_exact():
    r1 = VersusRunner(factory(240), {"A": RandomController("a"), "B": RandomController("b")},
                      clock=Clock()).run(3)
    r2 = VersusRunner(factory(240), {"A": RandomController("a"), "B": RandomController("b")},
                      clock=Clock(), seed_key=b"k" * 16).run(3)
    assert replay(factory(240), r2) == r2["final_snapshot"]
    # same seed + key reproduces
    r3 = VersusRunner(factory(240), {"A": RandomController("a"), "B": RandomController("b")},
                      clock=Clock(), seed_key=b"k" * 16).run(3)
    assert strip(r2) == strip(r3)
    assert strip(r1) != strip(r2)       # the key is a confound if mixed within a comparison


# --- busy --------------------------------------------------------------------------
class Slow:
    kind = "scripted"

    def __init__(self, name, delay):
        self.name, self.delay, self.calls, self.resets = name, delay, 0, 0
        self.active = 0
        self.max_active = 0
        self.lock = threading.Lock()

    def reset(self, seed):
        self.resets += 1

    def decide(self, obs, legal):
        with self.lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
            self.calls += 1
        time.sleep(self.delay)
        with self.lock:
            self.active -= 1
        return "WAIT"


def test_busy_never_runs_two_calls_concurrently_and_is_counted():
    s = Slow("s", 0.25)
    res = VersusRunner(factory(120), {"A": s, "B": WaitController()},
                       limits=VersusLimits(timeout_s=0.05)).run(1)
    assert s.max_active == 1
    st = res["seats"]["A"]
    assert st["timeouts"] >= 1 and st["busy"] >= 1
    assert st["fallbacks"] == st["timeouts"] + st["busy"] + st["errors"] + st["refused"]
    recs = res["traces"]["A"]
    assert all(r["input"] == "WAIT" and r["source"] == "fallback" for r in recs)
    assert {r["fallback_reason"] for r in recs} <= {"timeout", "busy"}


def test_same_instance_in_both_seats_is_refused():
    # Decision #24 (QA-5) and #33: one controller object in both seats is a
    # channel between seats, so the runner refuses it.
    s = Slow("s", 0.25)
    with pytest.raises(ValueError):
        VersusRunner(factory(120), {"A": s, "B": s}, limits=VersusLimits(timeout_s=0.05))


def test_busy_recovers_after_late_call_returns():
    s = Slow("s", 0.12)
    res = VersusRunner(factory(240), {"A": s, "B": WaitController()},
                       limits=VersusLimits(timeout_s=0.03)).run(1)
    reasons = [r["fallback_reason"] for r in res["traces"]["A"]]
    assert "timeout" in reasons and "busy" in reasons


def test_reset_skipped_when_controller_still_busy_from_previous_episode():
    """FINDING candidate: run 2 does not reset a controller whose run-1 late call
    is still alive; it records reset_error 'busy' and plays on with run-1 state."""
    s = Slow("s", 0.4)
    r = VersusRunner(factory(24), {"A": s, "B": WaitController()},
                     limits=VersusLimits(timeout_s=0.02))
    r.run(1)
    resets_after_first = s.resets
    res2 = r.run(2)
    assert res2["seats"]["A"]["reset_error"] == "busy"
    assert s.resets == resets_after_first        # reset was NOT delivered for seed 2


def test_busy_trace_is_wallclock_dependent_but_replay_is_exact():
    s = Slow("s", 0.1)
    f = factory(120)
    res = VersusRunner(f, {"A": s, "B": RandomController("b")},
                       limits=VersusLimits(timeout_s=0.03)).run(2)
    assert replay(f, res) == res["final_snapshot"]
    # round trip through JSONL
    import tempfile, pathlib
    d = pathlib.Path(tempfile.mkdtemp())
    save_traces(res, d)
    loaded = load_traces(d.glob("*.jsonl"))
    assert replay(f, loaded)["frames"] == res["frames"]


def test_busy_state_is_shared_across_runner_instances():
    """Two runners sharing one controller never call it concurrently (T04-fix2 closes the gap
    this probe documented in T04-fix1)."""
    s = Slow("s", 0.3)
    f = factory(24)
    lim = VersusLimits(timeout_s=0.02)
    VersusRunner(f, {"A": s, "B": WaitController()}, limits=lim).run(1)
    VersusRunner(f, {"A": s, "B": WaitController()}, limits=lim).run(1)
    assert s.max_active == 1


def test_inline_mode_has_no_real_time_bound_but_labels_slow_call_by_clock():
    s = Slow("s", 0.08)
    res = VersusRunner(factory(24), {"A": s, "B": WaitController()}, threaded=False,
                       limits=VersusLimits(timeout_s=0.03)).run(1)
    assert res["seats"]["A"]["timeouts"] >= 1 and res["seats"]["A"]["busy"] == 0


# --- variants of the original attacks ---------------------------------------------
class Ans:
    kind = "scripted"

    def __init__(self, ans, name="x"):
        self.name, self.ans = name, ans

    def decide(self, obs, legal):
        return self.ans


def _run(ans, threaded=True):
    return VersusRunner(factory(30), {"A": Ans(ans), "B": WaitController()}, clock=Clock(),
                        threaded=threaded).run(1)


class EqAll(str):
    def __eq__(self, o): return True
    def __hash__(self): return 1
    def __ne__(self, o): return False


class Spoof:
    @property
    def __class__(self):            # isinstance(x, str) is True, but it is not a str
        return str


class StrLen(str):
    def __len__(self): return 0
    def __str__(self): return "WAIT"
    def __repr__(self): raise RuntimeError("no")


class Cont(list):
    pass


@pytest.mark.parametrize("threaded", [True, False])
@pytest.mark.parametrize("ans", [EqAll("ZZZ"), StrLen("ZZZ"), b"WAIT", ["WAIT"], None,
                                 Cont(["WAIT"]), 5, float("nan"), object()],
                         ids=lambda a: type(a).__name__ + str(id(a) % 7))
def test_weird_answers_never_crash_and_never_reach_step(ans, threaded):
    res = _run(ans, threaded)
    recs = res["traces"]["A"]
    assert recs and all(r["input"] in ("WAIT", None) for r in recs)
    assert all(r["source"] == "fallback" for r in recs)
    json.dumps(res["traces"])      # trace must serialise


def test_exact_legal_str_subclass_is_played_as_plain_text():
    class S(str):
        def strip(self): return "ZZZ"
    res = VersusRunner(factory(30), {"A": Ans(S("WAIT")), "B": WaitController()}, clock=Clock()).run(1)
    assert all(type(r["input"]) is str and r["input"] == "WAIT" for r in res["traces"]["A"])
    assert replay(factory(30), res) == res["final_snapshot"]


@pytest.mark.parametrize("exc", [SystemExit(3), GeneratorExit(), KeyboardInterrupt()])
def test_baseexception_in_threaded_decide_is_error(exc):
    class Boom:
        kind, name = "scripted", "b"
        def decide(self, o, l): raise exc
    res = VersusRunner(factory(30), {"A": Boom(), "B": WaitController()}, clock=Clock()).run(1)
    assert {r["fallback_reason"] for r in res["traces"]["A"]} == {"error"}


def test_reset_that_hangs_is_bounded_and_reset_error_recorded():
    class H:
        kind, name = "scripted", "h"
        def reset(self, s): time.sleep(0.3)
        def decide(self, o, l): return "WAIT"
    t0 = time.perf_counter()
    res = VersusRunner(factory(24), {"A": H(), "B": WaitController()},
                       limits=VersusLimits(timeout_s=0.05)).run(1)
    assert time.perf_counter() - t0 < 0.25
    assert res["seats"]["A"]["reset_error"] == "timeout"
    assert res["traces"]["A"][0]["fallback_reason"] == "busy"


@pytest.mark.parametrize("bad", [None, 0, -1, float("nan"), float("inf"), True, "5", 0.0])
def test_timeout_validation(bad):
    with pytest.raises((TypeError, ValueError)):
        VersusLimits(timeout_s=bad)


def test_unkeyed_seed_still_enumerable_documented():
    target = controller_seed(37, "A")
    assert [s for s in range(1000) if controller_seed(s, "A") == target] == [37]


@pytest.mark.parametrize("threaded", [True, False])
def test_class_spoofing_answer_is_malformed_not_a_crash(threaded):
    res = _run(Spoof(), threaded)
    assert {r["fallback_reason"] for r in res["traces"]["A"]} == {"malformed"}
