"""Versus runner (pop/versus_runner.py; docs/final/VERSUS_RUNNER.md, task T04).

Deterministic, offline. The runner ticks a VersusEpisode, asks each seat's
controller on a fixed cadence with copies of that seat's observation and legal
list only, validates every answer, and replaces a failed, slow, illegal or
malformed answer with a `WAIT` labelled `source: "fallback"`.
"""

from __future__ import annotations

import json
import math
import threading
import time

import pytest

from pop.seats import (RandomController, ScriptedController, WaitController,
                       controller_seed)
from pop.versus import SEATS, arena_episode
from pop.versus_runner import (FALLBACK_ACTION, VersusLimits, VersusRunner, digest,
                               load_traces, replay, save_traces, snapshot)

PLAIN = (dict, list, tuple, str, int, float, bool, type(None))


def factory(limit: int = 120):
    return lambda: arena_episode(time_limit_frames=limit)


class FakeClock:
    """Injectable clock: time moves only when a test says so."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class Spy:
    kind = "scripted"

    def __init__(self, name: str = "spy", answer: str = "WAIT") -> None:
        self.name = name
        self.answer = answer
        self.calls: list[tuple] = []
        self.resets: list = []

    def reset(self, seed):
        self.resets.append(seed)

    def decide(self, observation, legal):
        self.calls.append((observation, legal))
        return self.answer


class Raiser:
    kind = "policy"
    name = "raiser"

    def decide(self, observation, legal):
        raise RuntimeError("policy crashed")


class Slow:
    """Takes `seconds` of the injected clock per decision, then answers."""

    kind = "policy"
    name = "slow"

    def __init__(self, clock: FakeClock, seconds: float, answer: str = "RIGHT") -> None:
        self.clock, self.seconds, self.answer = clock, seconds, answer

    def decide(self, observation, legal):
        self.clock.now += self.seconds
        return self.answer


class Mutator:
    """Answers like a script but vandalises everything it is handed."""

    kind = "scripted"
    name = "mutator"

    def __init__(self, script):
        self.inner = ScriptedController(script)

    def decide(self, observation, legal):
        answer = self.inner.decide(observation, legal)
        observation["me"]["hp"] = 99
        observation["tiles"].clear()
        observation["figures"].append({"kind": "rival", "row": 0, "col": 0})
        observation.clear()
        try:
            legal.append("LUNGE")                   # a tuple: must not be possible
        except AttributeError:
            pass
        return answer


def run(controllers, limit=120, seed=0, **kw):
    kw.setdefault("clock", FakeClock())
    return VersusRunner(factory(limit), controllers, **kw).run(seed)


def walk_types(x):
    yield type(x)
    if isinstance(x, dict):
        for k, v in x.items():
            yield type(k)
            yield from walk_types(v)
    elif isinstance(x, (list, tuple)):
        for v in x:
            yield from walk_types(v)


# --- 1. isolation ----------------------------------------------------------
def test_controller_gets_only_plain_copies_of_its_own_seat():
    a, b = Spy("a"), Spy("b")
    run({"A": a, "B": b}, limit=12)
    fresh = factory(12)()                               # same duel limit as the run (T04-fix1)
    for seat, spy in (("A", a), ("B", b)):
        obs, legal = spy.calls[0]
        assert obs == fresh.observe(seat)               # its own seat, as at frame 0
        assert isinstance(legal, tuple) and all(isinstance(x, str) for x in legal)
        assert legal == tuple(fresh.legal_actions(seat))
        for _, (o, l) in enumerate(spy.calls):
            assert set(walk_types(o)) <= set(PLAIN)       # no episode, duel or rival object
    assert a.calls[0][0] is not b.calls[0][0]
    assert a.calls[0][0] != b.calls[0][0]


def test_controller_reset_gets_a_derived_seed_not_the_episode_seed():
    a, b = Spy("a"), Spy("b")
    run({"A": a, "B": b}, limit=6, seed=11)
    assert a.resets == [controller_seed(11, "A")]
    assert b.resets == [controller_seed(11, "B")]
    assert 11 not in a.resets + b.resets


def test_mutating_observation_cannot_affect_episode_or_other_seat():
    script = ["RIGHT", "RIGHT", "DRAW", "WAIT", "LEFT"]
    clean = run({"A": ScriptedController(script), "B": ScriptedController(script)})
    dirty = run({"A": Mutator(script), "B": ScriptedController(script)})
    assert dirty["final_snapshot"] == clean["final_snapshot"]
    assert dirty["traces"]["B"] == clean["traces"]["B"]
    strip = lambda recs: [{k: v for k, v in r.items() if k != "controller"} for r in recs]  # noqa: E731
    assert strip(dirty["traces"]["A"]) == strip(clean["traces"]["A"])


def test_two_controllers_sharing_a_script_list_do_not_share_state():
    script = ["RIGHT", "RIGHT"]
    res = run({"A": ScriptedController(script), "B": ScriptedController(script)}, limit=24)
    for seat in SEATS:
        assert [r["input"] for r in res["traces"][seat]][:3] == ["RIGHT", "RIGHT", "WAIT"]


def test_trace_hash_matches_the_observation_the_controller_saw():
    from pop.versus_runner import digest
    a, b = Spy("a"), Spy("b")
    res = run({"A": a, "B": b}, limit=24)
    for seat, spy in (("A", a), ("B", b)):
        assert [r["obs_sha256"] for r in res["traces"][seat]] == \
            [digest(o) for o, _ in spy.calls]
        assert [r["legal_sha256"] for r in res["traces"][seat]] == \
            [digest(list(l)) for _, l in spy.calls]


# --- 2. fallback -------------------------------------------------------------
def test_controller_exception_gives_labelled_wait_and_other_seat_keeps_cadence():
    res = run({"A": Raiser(), "B": ScriptedController(["RIGHT"] * 30)}, limit=60)
    ta, tb = res["traces"]["A"], res["traces"]["B"]
    assert [r["frame"] for r in ta] == [r["frame"] for r in tb] == list(range(0, 60, 6))
    assert all(r["source"] == "fallback" and r["input"] == FALLBACK_ACTION
               and r["fallback_reason"] == "error" for r in ta)
    assert all("policy crashed" in r["error"] for r in ta)
    assert all(r["source"] == "controller" and r["input"] == "RIGHT" for r in tb)
    assert res["seats"]["A"]["errors"] == res["seats"]["A"]["fallbacks"] == 10
    assert res["seats"]["B"]["fallbacks"] == 0
    assert res["outcome"]["reason"] == "draw:time_up"


def test_fallback_wait_plays_exactly_like_a_controller_wait():
    crashed = run({"A": Raiser(), "B": ScriptedController(["RIGHT"] * 30)}, limit=60)
    waited = run({"A": WaitController(), "B": ScriptedController(["RIGHT"] * 30)}, limit=60)
    assert crashed["final_snapshot"] == waited["final_snapshot"]
    assert crashed["traces"]["B"] == waited["traces"]["B"]


def test_slow_decision_on_injected_clock_is_a_labelled_timeout_fallback():
    clock = FakeClock()
    res = VersusRunner(factory(36), {"A": Slow(clock, 6.0), "B": ScriptedController(["LEFT"])},
                       clock=clock).run(0)
    ta = res["traces"]["A"]
    assert all(r["source"] == "fallback" and r["fallback_reason"] == "timeout"
               and r["input"] == "WAIT" and r["latency_ms"] == 6000.0 for r in ta)
    assert res["seats"]["A"]["timeouts"] == len(ta) == 6
    assert res["traces"]["B"][0]["input"] == "LEFT"
    assert res["traces"]["B"][0]["source"] == "controller"
    assert res["limits"]["timeout_s"] == 5.0                # the default


def test_decision_under_the_timeout_is_used():
    clock = FakeClock()
    res = VersusRunner(factory(6), {"A": Slow(clock, 4.9), "B": WaitController()},
                       clock=clock).run(0)
    rec = res["traces"]["A"][0]
    assert rec["source"] == "controller" and rec["input"] == "RIGHT"


def test_real_wall_clock_timeout_does_not_block_the_run():
    class Sleeper:
        kind, name = "policy", "sleeper"

        def decide(self, observation, legal):
            time.sleep(0.5)
            return "RIGHT"

    t0 = time.perf_counter()
    res = VersusRunner(factory(6), {"A": Sleeper(), "B": WaitController()},
                       limits=VersusLimits(timeout_s=0.05)).run(0)
    assert time.perf_counter() - t0 < 0.4
    assert res["traces"]["A"][0]["fallback_reason"] == "timeout"
    assert res["traces"]["A"][0]["input"] == "WAIT"


# --- 3. illegal and malformed answers ----------------------------------------
@pytest.mark.parametrize("answer,reason", [
    ("FLY", "illegal"),            # not an input at all
    ("LUNGE", "illegal"),          # an input, but not with a sheathed sword
    ("wait", "illegal"),           # inputs are exact names
    (42, "malformed"),
    (None, "malformed"),
    (["WAIT"], "malformed"),
])
def test_bad_answer_is_refused_counted_and_changes_nothing(answer, reason):
    bad = run({"A": Spy("bad", answer), "B": ScriptedController(["RIGHT"] * 10)}, limit=48)
    good = run({"A": WaitController(), "B": ScriptedController(["RIGHT"] * 10)}, limit=48)
    ta = bad["traces"]["A"]
    assert all(r["source"] == "fallback" and r["fallback_reason"] == reason
               and r["input"] == "WAIT" for r in ta)
    assert bad["seats"]["A"]["refused"] == len(ta) == 8
    assert bad["seats"]["B"]["refused"] == 0
    assert bad["final_snapshot"] == good["final_snapshot"]
    assert bad["outcome"]["invalid_inputs"] == {"A": 0, "B": 0}   # never reached step


# --- 4. determinism and replay ----------------------------------------------
def random_pair():
    return {"A": RandomController(name="rnd-a"), "B": RandomController(name="rnd-b")}


def test_same_seed_same_controllers_identical_trace_and_outcome():
    r1 = run(random_pair(), limit=240, seed=3)
    r2 = run(random_pair(), limit=240, seed=3)
    assert r1["traces"] == r2["traces"]
    assert r1["outcome"] == r2["outcome"]
    assert r1["final_snapshot_sha256"] == r2["final_snapshot_sha256"]
    moves = {r["input"] for seat in SEATS for r in r1["traces"][seat]}
    assert len(moves) > 3                                   # the run actually did things


def test_replay_reproduces_the_final_snapshot():
    res = run(random_pair(), limit=240, seed=5)
    assert replay(factory(240), res) == res["final_snapshot"]


def test_replay_from_saved_jsonl_traces(tmp_path):
    res = run({"A": Raiser(), "B": RandomController()}, limit=120, seed=2)
    paths = save_traces(res, tmp_path)
    assert set(paths) == set(SEATS)
    loaded = load_traces(paths.values())
    assert loaded["traces"] == res["traces"]
    final = replay(factory(120), loaded)
    assert final == res["final_snapshot"]
    assert loaded["final_snapshot_sha256"] == res["final_snapshot_sha256"]


def test_snapshot_helper_is_a_copy():
    ep = arena_episode()
    s = snapshot(ep)
    s["frames"] = 999
    assert snapshot(ep)["frames"] == 0


# --- 5. seat swap ---------------------------------------------------------------
def test_seat_swap_mirrors_seat_labels():
    ctrls = lambda: {"A": ScriptedController(["RIGHT"], name="alpha"),  # noqa: E731
                     "B": WaitController(name="beta")}
    plain = run(ctrls(), limit=24)
    swapped = run(ctrls(), limit=24, swap_seats=True)
    assert plain["seating"] == {"A": "A", "B": "B"}
    assert swapped["seating"] == {"A": "B", "B": "A"}
    for seat, other in (("A", "B"), ("B", "A")):
        assert swapped["seats"][seat]["controller"] == plain["seats"][other]["controller"]
        assert swapped["seats"][seat]["kind"] == plain["seats"][other]["kind"]
        assert swapped["seats"][seat]["slot"] == other
    assert swapped["traces"]["B"][0]["controller"] == "alpha"
    assert swapped["traces"]["B"][0]["input"] == "RIGHT"
    assert swapped["swap_seats"] is True


def test_winner_maps_back_to_the_controller_slot():
    from pop.versus_runner import winner
    assert winner("won:A", {"A": "B", "B": "A"}) == ("A", "B")
    assert winner("won:B", {"A": "A", "B": "B"}) == ("B", "B")
    assert winner("draw:time_up", {"A": "A", "B": "B"}) == (None, None)
    assert winner(None, {"A": "A", "B": "B"}) == (None, None)


# --- limits ----------------------------------------------------------------------
def test_duel_limit_comes_from_the_episode():
    res = run({"A": WaitController(), "B": WaitController()}, limit=60)
    assert res["outcome"]["reason"] == "draw:time_up"
    assert res["frames"] == 60 and res["runner_terminal"] is None
    assert res["status"] == "draw:time_up"
    assert res["seats"]["A"]["decisions"] == 10


def test_max_fallbacks_ends_the_run_with_a_seat_reason():
    res = run({"A": Raiser(), "B": WaitController()}, limit=600,
              limits=VersusLimits(max_fallbacks=2))
    assert res["runner_terminal"] == "max_fallbacks:A"
    assert res["status"] == "aborted:max_fallbacks:A"
    assert res["seats"]["A"]["fallbacks"] == 3
    assert res["outcome"]["status"] == "ongoing"
    assert res["frames"] == 12


def test_max_decisions_ends_the_run_when_a_seat_would_need_another():
    res = run({"A": WaitController(), "B": WaitController()}, limit=600,
              limits=VersusLimits(max_decisions=3))
    assert res["runner_terminal"] == "max_decisions:A,B"
    assert res["seats"]["A"]["decisions"] == res["seats"]["B"]["decisions"] == 3
    assert res["frames"] == 18


def test_replay_matches_a_run_stopped_by_a_runner_limit():
    res = run({"A": Raiser(), "B": RandomController()}, limit=600,
              limits=VersusLimits(max_fallbacks=4))
    assert replay(factory(600), res) == res["final_snapshot"]


def test_decision_cadence_is_configurable():
    res = run({"A": WaitController(), "B": WaitController()}, limit=24, decision_every=4)
    assert [r["frame"] for r in res["traces"]["A"]] == [0, 4, 8, 12, 16, 20]


def test_seat_with_no_legal_input_is_not_asked():
    class Frozen:
        """A minimal episode on the public API whose seat B can never act."""

        def __init__(self):
            self.reset(0)

        def reset(self, seed):
            self.frames, self.got = 0, []

        def observe(self, seat):
            return {"frame": self.frames, "seat_view": seat}

        def legal_actions(self, seat):
            return ["WAIT"] if seat == "A" else []

        def step(self, seat, action):
            self.got.append((self.frames, seat, action))
            return {"accepted": True}

        def outcome(self):
            done = self.frames >= 12
            return {"status": "terminal" if done else "ongoing",
                    "reason": "draw:time_up" if done else None, "frames": self.frames,
                    "inputs": {}, "invalid_inputs": {}}

        def tick(self):
            self.frames += 1

        def snapshot(self):
            return {"frames": self.frames, "got": list(self.got)}

    b = Spy("b")
    res = VersusRunner(Frozen, {"A": WaitController(), "B": b}, clock=FakeClock()).run(0)
    assert b.calls == [] and res["traces"]["B"] == []
    assert len(res["traces"]["A"]) == 2


def test_controllers_must_fill_both_seats_and_cadence_is_positive():
    with pytest.raises(ValueError):
        VersusRunner(factory(), {"A": WaitController()})
    with pytest.raises(ValueError):
        VersusRunner(factory(), {"A": WaitController(), "B": WaitController()},
                     decision_every=0)


# --- T04-fix1: gate findings and the trusted hooks ------------------------------------
class NpStr(str):
    """Like numpy.str_: a str subclass a policy may return."""


def test_str_subclass_answer_is_played_and_recorded_as_a_plain_str():
    res = run({"A": Spy("np", NpStr("RIGHT")), "B": WaitController()}, limit=12)
    rec = res["traces"]["A"][0]
    assert rec["source"] == "controller" and rec["input"] == "RIGHT"
    assert type(rec["input"]) is str


@pytest.mark.parametrize("bad", [None, 0, -1.0, math.nan, math.inf, "5", True])
def test_limits_reject_a_bad_timeout(bad):
    with pytest.raises((TypeError, ValueError)):
        VersusLimits(timeout_s=bad)


@pytest.mark.parametrize("field", ["max_decisions", "max_fallbacks", "max_frames"])
@pytest.mark.parametrize("bad", [-1, 1.5, "3", True])
def test_limits_reject_bad_counts(field, bad):
    with pytest.raises((TypeError, ValueError)):
        VersusLimits(**{field: bad})


def test_limits_accept_good_values():
    lim = VersusLimits(max_decisions=0, max_fallbacks=3, timeout_s=1, max_frames=None)
    assert lim.timeout_s == 1


def test_busy_seat_gets_a_labelled_fallback_until_its_late_call_returns():
    class Slow:
        kind, name = "policy", "slow"

        def __init__(self):
            self.calls = 0

        def decide(self, observation, legal):
            self.calls += 1
            time.sleep(0.15)
            return "WAIT"

    slow = Slow()
    res = VersusRunner(factory(24), {"A": slow, "B": WaitController()},
                       limits=VersusLimits(timeout_s=0.03)).run(0)
    reasons = [r["fallback_reason"] for r in res["traces"]["A"]]
    assert reasons == ["timeout", "busy", "busy", "busy"]
    assert all(r["input"] == "WAIT" and r["source"] == "fallback" for r in res["traces"]["A"])
    s = res["seats"]["A"]
    assert (s["timeouts"], s["busy"], s["fallbacks"], s["decisions"]) == (1, 3, 4, 4)
    assert slow.calls == 1
    assert res["seats"]["B"]["busy"] == 0


def test_seat_is_asked_again_once_its_late_call_has_returned():
    gate = threading.Event()

    class Late:
        kind, name = "policy", "late"

        def __init__(self):
            self.calls = 0

        def decide(self, observation, legal):
            self.calls += 1
            if self.calls == 1:
                gate.wait(1.0)
            return "WAIT"

    late = Late()
    runner = VersusRunner(factory(12), {"A": late, "B": WaitController()},
                          limits=VersusLimits(timeout_s=0.02))
    first = runner.run(0)
    assert [r["fallback_reason"] for r in first["traces"]["A"]] == ["timeout", "busy"]
    gate.set()
    time.sleep(0.05)
    second = runner.run(0)                             # same instance, next episode
    assert [r["source"] for r in second["traces"]["A"]] == ["controller", "controller"]


def test_slow_reset_is_recorded_as_a_timeout_and_the_seat_waits_for_it():
    class SlowReset(WaitController):
        def reset(self, seed):
            time.sleep(0.3)

    t0 = time.perf_counter()
    res = VersusRunner(factory(12), {"A": SlowReset(), "B": WaitController()},
                       limits=VersusLimits(timeout_s=0.03)).run(0)
    assert time.perf_counter() - t0 < 0.25
    assert res["seats"]["A"]["reset_error"] == "timeout"
    assert [r["fallback_reason"] for r in res["traces"]["A"]] == ["busy", "busy"]
    assert res["seats"]["B"]["reset_error"] is None


def test_keyboard_interrupt_in_decide_still_stops_an_inline_run():
    class Stopper:
        kind, name = "policy", "stopper"

        def decide(self, observation, legal):
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        run({"A": Stopper(), "B": WaitController()}, limit=6, threaded=False)


@pytest.mark.parametrize("threaded", [True, False])
def test_system_exit_in_decide_is_an_error_fallback(threaded):
    class Exiter:
        kind, name = "policy", "exiter"

        def decide(self, observation, legal):
            raise SystemExit("gone")

    res = run({"A": Exiter(), "B": WaitController()}, limit=6, threaded=threaded)
    assert res["traces"]["A"][0]["fallback_reason"] == "error"


# on_frame: a runner-side observer for scenario metrics, never given to a controller
def test_on_frame_sees_every_frame_and_changes_nothing():
    seen = []

    def on_frame(frame, view):
        seen.append((frame, view.outcome()["frames"], digest(view.snapshot())))

    plain = run(random_pair(), limit=60, seed=3)
    hooked = run(random_pair(), limit=60, seed=3, on_frame=on_frame)
    assert hooked["traces"] == plain["traces"]
    assert hooked["final_snapshot"] == plain["final_snapshot"]
    assert [f for f, _, _ in seen] == list(range(1, 61))
    assert all(f == frames for f, frames, _ in seen)
    assert seen[-1][2] == plain["final_snapshot_sha256"]


def test_on_frame_view_is_read_only_and_hands_out_copies():
    def on_frame(frame, view):
        for name in ("step", "tick", "reset", "_episode", "_ep"):
            assert not hasattr(view, name)
        view.snapshot()["frames"] = -1
        obs = view.observe("A")
        obs.clear()
        legal = view.legal_actions("A")
        assert isinstance(legal, tuple)

    plain = run(random_pair(), limit=30, seed=1)
    hooked = run(random_pair(), limit=30, seed=1, on_frame=on_frame)
    assert hooked["final_snapshot"] == plain["final_snapshot"]


def test_on_frame_view_never_reaches_a_controller():
    views, a, b = [], Spy("a"), Spy("b")
    run({"A": a, "B": b}, limit=24, on_frame=lambda f, v: views.append(v))
    for spy in (a, b):
        for obs, legal in spy.calls:
            assert set(walk_types(obs)) <= set(PLAIN)
            assert set(walk_types(legal)) <= set(PLAIN)
    assert views and not hasattr(a, "view") and not hasattr(b, "view")


def test_on_frame_runs_when_a_runner_limit_stops_the_run():
    seen = []
    res = run({"A": Raiser(), "B": WaitController()}, limit=600,
              limits=VersusLimits(max_fallbacks=2), on_frame=lambda f, v: seen.append(f))
    assert res["frames"] == 12 and seen == list(range(1, 13))


# trusted fast path for training: same results, cheaper copies, no worker thread
def test_fast_path_gives_the_same_run_as_the_default():
    slow = run(random_pair(), limit=240, seed=8)
    fast = run(random_pair(), limit=240, seed=8, copy_mode="json", threaded=False)
    assert fast["traces"] == slow["traces"]
    assert fast["final_snapshot"] == slow["final_snapshot"]
    assert fast["runner"] == {"copy_mode": "json", "threaded": False}
    assert slow["runner"] == {"copy_mode": "deepcopy", "threaded": True}


def test_fast_path_still_hands_out_copies():
    script = ["RIGHT", "RIGHT", "DRAW", "WAIT", "LEFT"]
    clean = run({"A": ScriptedController(script), "B": ScriptedController(script)})
    dirty = run({"A": Mutator(script), "B": ScriptedController(script)},
                copy_mode="json", threaded=False)
    assert dirty["final_snapshot"] == clean["final_snapshot"]


def test_fast_path_timeout_uses_the_injected_clock_only():
    clock = FakeClock()
    res = VersusRunner(factory(12), {"A": Slow(clock, 6.0), "B": WaitController()},
                       clock=clock, threaded=False).run(0)
    assert [r["fallback_reason"] for r in res["traces"]["A"]] == ["timeout", "timeout"]


def test_unknown_copy_mode_is_refused():
    with pytest.raises(ValueError):
        VersusRunner(factory(), {"A": WaitController(), "B": WaitController()},
                     copy_mode="none")


def test_default_runner_behaviour_is_recorded_in_the_result_and_trace_header(tmp_path):
    res = run(random_pair(), limit=12)
    head = json.loads(save_traces(res, tmp_path)["A"].read_text().splitlines()[0])
    assert head["runner"] == {"copy_mode": "deepcopy", "threaded": True}


def test_keyed_controller_seed_is_used_when_the_runner_has_a_key():
    a, b = Spy("a"), Spy("b")
    run({"A": a, "B": b}, limit=6, seed=11, seed_key=b"evaluation-secret")
    assert a.resets == [controller_seed(11, "A", key=b"evaluation-secret")]
    assert a.resets != [controller_seed(11, "A")]


@pytest.mark.parametrize("threaded", [True, False])
def test_exception_whose_str_raises_is_still_an_error_fallback(threaded):
    class Nasty(Exception):
        def __str__(self):
            raise RuntimeError("str failed")

    class Thrower:
        kind, name = "policy", "thrower"

        def decide(self, observation, legal):
            raise Nasty()

    res = run({"A": Thrower(), "B": WaitController()}, limit=12, threaded=threaded)
    assert [r["fallback_reason"] for r in res["traces"]["A"]] == ["error", "error"]
    assert "Nasty" in res["traces"]["A"][0]["error"]
