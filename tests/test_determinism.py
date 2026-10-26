"""Same seed and same actions give identical episodes."""

from pop.interface import Episode
from pop.runner import ScriptedPlayer, run_episode
from solutions import SOLUTIONS


def _strip(trace):
    return [{k: v for k, v in r.items() if k != "latency_ms"} for r in trace]


def test_same_seed_same_actions_same_trace_and_state():
    a = run_episode(ScriptedPlayer(SOLUTIONS["S3"]), "S3", seed=100)
    b = run_episode(ScriptedPlayer(SOLUTIONS["S3"]), "S3", seed=100)
    assert _strip(a["trace"]) == _strip(b["trace"]) and a["outcome"] == b["outcome"]


def test_reset_with_same_seed_gives_same_state():
    e1, e2 = Episode("S3"), Episode("S3")
    e1.reset(5)
    e2.reset(5)
    for a in SOLUTIONS["S3"][:20]:
        e1.step("kid", a)
        e2.step("kid", a)
    assert e1._game.snapshot() == e2._game.snapshot()
