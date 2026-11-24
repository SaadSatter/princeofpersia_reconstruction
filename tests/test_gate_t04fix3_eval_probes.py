"""T04-fix3 (Gate 2, evaluation specialist): seat isolation, seed_key and
shared-controller probes. Offline, deterministic (events, no timing asserts).
Tests named `finding_` document reproduced weaknesses and pass by asserting the
current behaviour."""

from __future__ import annotations

import json
import threading

import pytest

from pop import versus_runner
from pop.seats import WaitController, controller_seed
from pop.versus import SEATS, arena_episode
from pop.versus_runner import VersusLimits, VersusRunner


def F():
    return arena_episode(time_limit_frames=12)


class Recorder:
    kind, name = "scripted", "rec"

    def __init__(self):
        self.seeds = []

    def reset(self, s):
        self.seeds.append(s)

    def decide(self, observation, legal):
        return "WAIT"


class Gate:
    """Blocks inside decide until released, so another runner overlaps."""
    kind, name = "scripted", "gate"

    def __init__(self):
        self.inside, self.release = threading.Event(), threading.Event()
        self.calls, self.seen, self.active, self.max_active = 0, [], 0, 0
        self.lock = threading.Lock()

    def decide(self, observation, legal):
        with self.lock:
            self.calls += 1
            self.active += 1
            self.max_active = max(self.max_active, self.active)
            self.seen.append(json.dumps(observation, sort_keys=True, default=str) + str(list(legal)))
        self.inside.set()
        assert self.release.wait(10)
        with self.lock:
            self.active -= 1
        return "WAIT"


def test_busy_fallback_reveals_nothing_to_the_controller_or_the_other_seat():
    """Runner 1 holds the shared controller inside decide; runner 2 (same
    controller, seat A) gets busy. The controller is never told, its inputs
    contain no busy text, and runner 2's seat B record and final state equal a
    run whose seat A simply waits."""
    g = Gate()
    lim = VersusLimits(timeout_s=30)
    t = threading.Thread(target=lambda: VersusRunner(
        F, {"A": g, "B": WaitController()}, limits=lim).run(1))
    t.start()
    assert g.inside.wait(10)
    base = VersusRunner(F, {"A": WaitController(), "B": WaitController()}, limits=lim).run(2)
    busy = VersusRunner(F, {"A": g, "B": WaitController()}, limits=lim).run(2)
    g.release.set()
    t.join()
    assert busy["seats"]["A"]["busy"] > 0
    assert g.max_active == 1                 # never two calls at once
    blob = " ".join(g.seen).lower()
    assert "busy" not in blob and "an earlier call" not in blob
    assert busy["seats"]["B"]["busy"] == 0
    assert busy["final_snapshot_sha256"] == base["final_snapshot_sha256"]
    rec = busy["traces"]["A"][0]
    assert rec["source"] == "fallback" and rec["fallback_reason"] == "busy"
    strip = lambda rows: [{k: v for k, v in r.items() if k != "latency_ms"} for r in rows]
    assert strip(busy["traces"]["B"]) == strip(base["traces"]["B"])


def test_the_shared_controller_value_error_names_no_hidden_fact():
    s = WaitController()
    with pytest.raises(ValueError) as e:
        VersusRunner(F, {"A": s, "B": s})
    assert str(e.value) == "seats A and B need separate controller instances"


def test_seed_key_is_not_in_result_or_traces_and_changes_controller_seeds():
    key = b"k" * 16
    ra, rb = Recorder(), Recorder()
    res = VersusRunner(F, {"A": ra, "B": rb}, seed_key=key).run(7)
    text = json.dumps(res, default=str)
    assert key.decode() not in text and key.hex() not in text
    assert ra.seeds == [controller_seed(7, "A", key)]
    assert rb.seeds == [controller_seed(7, "B", key)]
    assert ra.seeds != [controller_seed(7, "A")] and ra.seeds != rb.seeds
    assert controller_seed(7, "A", key) != controller_seed(7, "A", b"j" * 16)
    got = ra.seeds[0]
    assert all(controller_seed(c, s) != got for c in range(5000) for s in SEATS)


@pytest.mark.parametrize("bad", [b"", 5])
def test_finding_degenerate_seed_keys_are_accepted_silently(bad):
    """FINDING (minor, pop/seats.py): `bytes(key)` accepts an int (5 -> five NUL
    bytes) and the empty key. A caller who passes either believes the run is
    keyed, but the seed is recoverable by enumeration. Not a runner bug for a
    correct harness (T08 must pass a random key of >= 16 bytes); a guard would
    be a Tech Lead change."""
    got = controller_seed(4242, "B", bad)
    k = bytes(bad)
    assert any(controller_seed(c, s, k) == got for c in range(20_000) for s in SEATS)


def test_finding_two_instances_sharing_state_are_not_detected():
    """The ValueError checks identity only. Two objects that share a mutable
    (a module global, a shared list) are a seat channel the runner cannot see.
    Documented limit: harnesses must build independent controllers."""
    shared = []

    class C:
        kind, name = "scripted", "c"

        def decide(self, observation, legal):
            shared.append(1)
            return "WAIT"

    VersusRunner(F, {"A": C(), "B": C()}).run(1)       # not refused
    assert shared


@pytest.mark.parametrize("threaded", [True, False])
def test_one_controller_per_worker_never_sees_busy_in_parallel(threaded):
    ctrls = [(Recorder(), WaitController()) for _ in range(4)]
    res = [None] * 4

    def work(i):
        res[i] = VersusRunner(F, {"A": ctrls[i][0], "B": ctrls[i][1]}, threaded=threaded,
                              seed_key=b"x" * 16).run(i)

    ts = [threading.Thread(target=work, args=(i,)) for i in range(4)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert all(r["seats"][s]["busy"] == 0 and r["seats"][s]["fallbacks"] == 0
               for r in res for s in SEATS)
    assert all(id(c) not in versus_runner._LATE for p in ctrls for c in p)


@pytest.mark.parametrize("threaded", [True, False])
def test_a_controller_shared_across_worker_threads_gets_busy_not_a_double_call(threaded):
    """The note for T08: one controller shared by workers gives `busy`
    fallbacks (counted in the stats), never two concurrent calls."""
    g = Gate()
    lim = VersusLimits(timeout_s=30)
    t = threading.Thread(target=lambda: VersusRunner(
        F, {"A": g, "B": WaitController()}, threaded=threaded, limits=lim).run(1))
    t.start()
    assert g.inside.wait(10)
    r2 = VersusRunner(F, {"A": g, "B": WaitController()}, threaded=threaded, limits=lim).run(1)
    g.release.set()
    t.join()
    assert g.max_active == 1
    assert r2["seats"]["A"]["busy"] == r2["seats"]["A"]["fallbacks"] > 0
