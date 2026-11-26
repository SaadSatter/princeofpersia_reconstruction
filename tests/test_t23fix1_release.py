"""T23-fix1 (decisions #93, #99, #100): the release rule reaches the server trace and play.py.

1. A server duel replays to the same outcome and state hash, because each human release
   is recorded in the trace (`releases`, one list of seats per tick; `ticks` is unchanged).
2. `play.py --versus` calls `ep.release(seat)` for a human seat with no legal key held,
   through the same method as the hosted page and the server; an AI seat never does.
3. The server's AI seat never calls `release`.
"""

from __future__ import annotations

import json
import os

import pytest

from pop.versus import VersusEpisode
from server.match import Match, TICK_S
from server.trace import replay

T = TICK_S
SETS_A = [["d"], ["d", "w"], ["a"], ["f"], ["g"], ["d", "lshift"], ["s"], ["d", "w", "f"]]
SETS_B = [["left"], ["left", "up"], ["right"], ["."], ["/"], ["'"], ["down"], []]


def duel(seed=7) -> Match:
    m = Match(seed=seed)
    m.join(None, 0.0)
    m.join(None, 0.0)
    now = 0.0
    for i in range(8 * 30):
        if i % 30 == 0:
            m.receive("A", json.dumps({"type": "keys", "keys": SETS_A[i // 30]}), now)
            m.receive("B", json.dumps({"type": "keys", "keys": SETS_B[i // 30]}), now)
        now += T
        m.advance(now)
    return m


def spy(monkeypatch) -> list:
    calls = []
    real = VersusEpisode.release

    def release(self, seat):
        calls.append(seat)
        return real(self, seat)

    monkeypatch.setattr(VersusEpisode, "release", release)
    return calls


def test_the_trace_records_each_release_per_tick():
    tr = duel().trace()
    assert len(tr["releases"]) == len(tr["ticks"])
    assert any(tr["releases"]) and all(s in ("A", "B") for r in tr["releases"] for s in r)


def test_a_server_trace_with_releases_replays_to_the_same_outcome_and_hash():
    m = duel()
    tr = m.trace()
    outcome, h = replay(tr)
    assert outcome == m.episode.outcome()
    assert h == tr["state_hash"]


def test_a_trace_without_releases_still_replays_its_inputs():
    tr = {"seed": 0, "ticks": [[["A", "RIGHT"]], []]}
    outcome, _ = replay(tr)
    assert outcome["frames"] == 2


def test_an_ai_seat_is_never_released(monkeypatch):
    calls = spy(monkeypatch)
    m = Match(seed=3, rival="baseline")
    m.join(None, 0.0)
    now = 0.0
    for _ in range(60):
        now += T
        m.advance(now)
    assert calls and set(calls) == {"A"}
    assert all(s == "A" for r in m.trace()["releases"] for s in r)


def run_play(tmp_path, monkeypatch, *flags):
    pytest.importorskip("pygame")
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    calls = spy(monkeypatch)
    import play
    assert play.main(["ARENA", "--versus", "--screenshot", str(tmp_path / "v.png"),
                      "--keys", "A:RIGHT,B:LEFT", *flags]) == 0
    return calls


def test_play_py_releases_both_human_seats(tmp_path, monkeypatch):
    assert {"A", "B"} <= set(run_play(tmp_path, monkeypatch))


def test_play_py_against_an_ai_releases_only_the_human_seat(tmp_path, monkeypatch):
    calls = run_play(tmp_path, monkeypatch, "--mode", "baseline")
    assert calls and set(calls) == {"A"}
