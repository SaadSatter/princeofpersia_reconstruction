"""T04-fix3 (QA, Gate 1): extra probes of the in-flight mark. No production code touched."""

from __future__ import annotations

import pytest

from pop import versus_runner
from pop.seats import WaitController
from pop.versus import arena_episode
from pop.versus_runner import VersusLimits, VersusRunner


def F():
    return arena_episode(time_limit_frames=12)


class Raiser:
    name = "raiser"
    kind = "test"

    def decide(self, observation, legal):
        raise RuntimeError("boom")


@pytest.mark.parametrize("threaded", [True, False])
def test_a_raising_controller_does_not_stay_marked_in_flight(threaded):
    r = Raiser()
    lim = VersusLimits(timeout_s=1.0)
    VersusRunner(F, {"A": r, "B": WaitController()}, limits=lim, threaded=threaded).run(1)
    assert id(r) not in versus_runner._LATE
    res = VersusRunner(F, {"A": r, "B": WaitController()}, limits=lim, threaded=threaded).run(1)
    assert res["seats"]["A"]["busy"] == 0


@pytest.mark.parametrize("threaded", [True, False])
def test_registry_is_empty_after_normal_runs(threaded):
    a, b = WaitController(), WaitController()
    VersusRunner(F, {"A": a, "B": b}, threaded=threaded).run(1)
    assert id(a) not in versus_runner._LATE and id(b) not in versus_runner._LATE


def test_sequential_reuse_of_one_controller_across_runners_is_never_busy():
    a = WaitController()
    for _ in range(3):
        res = VersusRunner(F, {"A": a, "B": WaitController()}).run(1)
        assert res["seats"]["A"]["busy"] == 0
