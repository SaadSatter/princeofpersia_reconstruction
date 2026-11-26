"""Gate 2 (Evaluation Specialist) review of T04: knowledge boundary, seat
fairness, fallback semantics, determinism and throughput of the versus runner.

Independent tests written by the reviewer (GATE-T04-eval). Passing tests are
evidence; tests marked xfail(strict=True) are findings against af76c30.
Deterministic and offline except for short real-time sleeps in the timeout
probes (all well under one second).
"""

from __future__ import annotations

import json
import threading
import time

import pytest

from pop.seats import RandomController, ScriptedController, WaitController, controller_seed
from pop.versus import SEATS, arena_episode
from pop.versus_runner import VersusLimits, VersusRunner, digest, load_traces, replay, save_traces


def factory(limit: int = 120):
    return lambda: arena_episode(time_limit_frames=limit)


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class Recorder:
    kind = "scripted"

    def __init__(self, name: str) -> None:
        self.name = name
        self.seen: list[tuple[dict, tuple]] = []

    def decide(self, observation, legal):
        self.seen.append((observation, legal))
        return "WAIT"


def _strip_latency(traces):
    return {s: [{k: v for k, v in r.items() if k != "latency_ms"} for r in traces[s]]
            for s in traces}


# --- evidence (expected to pass) ----------------------------------------------
def test_both_seats_are_asked_on_identical_frames():
    res = VersusRunner(factory(240), {"A": RandomController("x"), "B": RandomController("y")},
                       clock=FakeClock()).run(9)
    frames = {s: [r["frame"] for r in res["traces"][s]] for s in SEATS}
    # A seat with no legal input is skipped; otherwise the frames must coincide.
    common = set(frames["A"]) & set(frames["B"])
    assert len(common) >= min(len(frames["A"]), len(frames["B"])) - 2
    assert all(f % 6 == 0 for s in SEATS for f in frames[s])


def test_seat_swap_pair_mirrors_slots_and_keeps_both_seats_on_equal_terms():
    ctrls = lambda: {"A": RandomController("slotA"), "B": RandomController("slotB")}  # noqa: E731
    plain = VersusRunner(factory(240), ctrls(), clock=FakeClock()).run(4)
    swapped = VersusRunner(factory(240), ctrls(), swap_seats=True, clock=FakeClock()).run(4)
    assert plain["seats"]["A"]["controller"] == swapped["seats"]["B"]["controller"] == "slotA"
    assert plain["seats"]["B"]["controller"] == swapped["seats"]["A"]["controller"] == "slotB"
    for res in (plain, swapped):
        if res["winner_seat"] is not None:
            assert res["seats"][res["winner_seat"]]["slot"] == res["winner_slot"]


def test_per_seat_trace_files_hold_only_that_seats_decisions(tmp_path):
    res = VersusRunner(factory(120), {"A": RandomController(), "B": RandomController()},
                       clock=FakeClock()).run(2)
    paths = save_traces(res, tmp_path)
    for seat, path in paths.items():
        lines = [json.loads(x) for x in path.read_text().splitlines()]
        assert lines[0]["controller"]["slot"] == res["seating"][seat]
        decisions = [x for x in lines if x["type"] == "decision"]
        assert decisions and all(d["seat"] == seat for d in decisions)
        other = "B" if seat == "A" else "A"
        other_hashes = {r["obs_sha256"] for r in res["traces"][other]}
        assert not other_hashes & {d["obs_sha256"] for d in decisions}
        # Observations themselves are not written, only their hashes.
        assert all("observation" not in d and "obs" not in d for d in decisions)


def test_exception_text_never_reaches_the_other_seat():
    secret = "SEAT-A-PRIVATE-ERROR-TEXT"

    class Raiser:
        kind, name = "policy", "raiser"

        def decide(self, observation, legal):
            raise RuntimeError(secret)

    rec = Recorder("b")
    res = VersusRunner(factory(48), {"A": Raiser(), "B": rec}, clock=FakeClock()).run(0)
    assert secret in res["traces"]["A"][0]["error"]
    assert all(secret not in json.dumps(o) for o, _ in rec.seen)
    assert all(secret not in json.dumps(r) for r in res["traces"]["B"])


def test_legal_hash_is_the_hash_of_the_list_the_controller_saw():
    rec = Recorder("a")
    res = VersusRunner(factory(24), {"A": rec, "B": WaitController()}, clock=FakeClock()).run(0)
    for (obs, legal), r in zip(rec.seen, res["traces"]["A"]):
        assert r["legal_sha256"] == digest(list(legal))
        assert r["obs_sha256"] == digest(obs)


def test_determinism_holds_with_the_real_clock_apart_from_latency():
    pair = lambda: {"A": RandomController(), "B": RandomController()}  # noqa: E731
    r1 = VersusRunner(factory(600), pair()).run(13)
    r2 = VersusRunner(factory(600), pair()).run(13)
    assert _strip_latency(r1["traces"]) == _strip_latency(r2["traces"])
    assert r1["final_snapshot_sha256"] == r2["final_snapshot_sha256"]


def test_replay_from_disk_matches_for_a_swapped_run(tmp_path):
    res = VersusRunner(factory(600), {"A": RandomController(), "B": RandomController()},
                       swap_seats=True, clock=FakeClock()).run(21)
    loaded = load_traces(save_traces(res, tmp_path).values())
    assert digest(replay(factory(600), loaded)) == res["final_snapshot_sha256"]


def test_throughput_is_adequate_for_policy_training():
    # Reviewer measured about 2,500 decisions/s (cadence 6) on the sandbox; this
    # floor only catches an order-of-magnitude regression.
    t0, decisions = time.perf_counter(), 0
    for seed in range(5):
        res = VersusRunner(factory(2000), {"A": RandomController(), "B": RandomController()}
                           ).run(seed)
        decisions += sum(res["seats"][s]["decisions"] for s in SEATS)
    assert decisions / (time.perf_counter() - t0) > 250


# --- findings -------------------------------------------------------------------------
class _Thief:
    """Enumerates small episode seeds and checks them against the seed it got."""
    kind, name = "scripted", "thief"

    def __init__(self) -> None:
        self.found = None

    def reset(self, s):
        for cand in range(20_000):
            for seat in SEATS:
                if controller_seed(cand, seat) == s:
                    self.found = (cand, seat)
                    return

    def decide(self, observation, legal):
        return "WAIT"


def test_keyed_controller_seed_cannot_be_recovered_by_enumeration():
    # Decision #24 (GATE-T04-eval-1): evaluation runs pass a seed_key.
    thief = _Thief()
    VersusRunner(factory(6), {"A": WaitController(), "B": thief}, clock=FakeClock(),
                 seed_key=b"evaluator-secret").run(4242)
    assert thief.found is None


def test_unkeyed_controller_seed_is_reproducible_but_recoverable_by_design():
    # Documented default (docs/final/VERSUS_RUNNER.md): no key, so runs repeat
    # without one, and a controller can invert a small seed. Not for evaluation.
    thief = _Thief()
    VersusRunner(factory(6), {"A": WaitController(), "B": thief}, clock=FakeClock()).run(4242)
    assert thief.found == (4242, "B")


def test_decide_is_never_called_while_an_abandoned_call_is_still_running():
    class Slow:
        kind, name = "policy", "slow"

        def __init__(self) -> None:
            self.active = 0
            self.overlaps = 0
            self.lock = threading.Lock()

        def decide(self, observation, legal):
            with self.lock:
                self.active += 1
                if self.active > 1:
                    self.overlaps += 1
            time.sleep(0.15)
            with self.lock:
                self.active -= 1
            return "WAIT"

    slow = Slow()
    VersusRunner(factory(24), {"A": slow, "B": WaitController()},
                 limits=VersusLimits(timeout_s=0.03)).run(0)
    time.sleep(0.2)
    assert slow.overlaps == 0


def test_controller_reset_is_bounded_by_the_timeout():
    class SlowReset:
        kind, name = "policy", "slow-reset"

        def reset(self, seed):
            time.sleep(0.5)

        def decide(self, observation, legal):
            return "WAIT"

    t0 = time.perf_counter()
    VersusRunner(factory(6), {"A": SlowReset(), "B": WaitController()},
                 limits=VersusLimits(timeout_s=0.05)).run(0)
    assert time.perf_counter() - t0 < 0.4


def test_base_exception_in_decide_is_labelled_error():
    class Exiter:
        kind, name = "policy", "exiter"

        def decide(self, observation, legal):
            raise SystemExit("policy process gone")

    res = VersusRunner(factory(6), {"A": Exiter(), "B": WaitController()},
                       clock=FakeClock()).run(0)
    rec = res["traces"]["A"][0]
    assert rec["source"] == "fallback" and rec["input"] == "WAIT"
    assert rec["fallback_reason"] == "error"
