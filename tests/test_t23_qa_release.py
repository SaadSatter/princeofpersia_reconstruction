"""T23 QA (Gate 1, decisions #93/#99): Saad's sequence on every front end, replay, AI seats.

Hosted page = `web.bridge.WebGame` (covered by tests/test_t23_release.py); here: the server
(telemetry log and trace replay), `play.py --playtest` through pygame's key state, and AI seats.
"""

from __future__ import annotations

import json
import os

import pytest

pytest.importorskip("websockets")
from pop.versus import VersusEpisode                     # noqa: E402
from pop.versus_runner import digest, snapshot           # noqa: E402
from server.match import TICK_S, Match                    # noqa: E402
from server.telemetry import Telemetry                    # noqa: E402
from server.trace import replay                           # noqa: E402


def _duel(tmp, plan, seed=4242):
    tmp.mkdir(parents=True, exist_ok=True)
    tele = Telemetry(tmp, "T23Q", info={"build": "qa"}, today=lambda: "2026-11-26")
    m = Match(seed=seed, rival=None, telemetry=tele, rival_budget_s=1.0)
    m.join(None, 0.0)
    m.join(None, 0.0)
    now = 0.0
    for keys, n in plan:
        m.receive("A", json.dumps({"type": "keys", "keys": keys}), now)
        for _ in range(n):
            now += TICK_S
            m.advance(now)
    m.close()
    rows = [json.loads(x) for x in (tmp / "2026-11-26-T23Q-001-A.jsonl").read_text().splitlines()[1:]]
    return m, [r for r in rows if r["type"] == "move"]


@pytest.mark.parametrize("release_at", [3, 4, 5, 6, 8])
def test_server_saads_sequence_logs_only_the_flip(tmp_path, release_at):
    # flip right (d+w), keep d during the flight, release before landing, wait well past it
    m, mv = _duel(tmp_path / "a", [(["d", "w"], 2), (["d"], release_at - 2), ([], 80)])
    assert [e["move"] for e in mv] == ["JUMP_RIGHT"], mv
    base, _ = _duel(tmp_path / "b", [(["d", "w"], 2), ([], 80)])
    assert m.episode.observe("A")["me"]["col"] == base.episode.observe("A")["me"]["col"]


def test_server_holding_through_the_landing_still_runs_on(tmp_path):
    _, mv = _duel(tmp_path, [(["d", "w"], 2), (["d"], 80)])
    assert len(mv) >= 3, mv


@pytest.mark.parametrize("release_at", [3, 5, 8])
def test_server_replay_reproduces_outcome_and_hash(tmp_path, release_at):
    m, _ = _duel(tmp_path, [(["d", "w"], 2), (["d"], release_at - 2), ([], 60), (["a"], 10)])
    tr = m.trace()
    assert any(tr["releases"])
    outcome, h = replay(tr)
    assert outcome == m.episode.outcome()
    assert h == tr["state_hash"] == digest(snapshot(m.episode))


def test_replay_depends_on_the_recorded_releases(tmp_path):
    # a trace stripped of its releases diverges: the test is not satisfied by ignoring them
    m, _ = _duel(tmp_path, [(["d", "w"], 2), (["d"], 3), ([], 60)])
    tr = m.trace()
    bare = dict(tr, releases=[[] for _ in tr["ticks"]])
    assert replay(bare)[1] != tr["state_hash"]


def test_ai_seat_never_releases_on_the_server(monkeypatch):
    calls = []
    real = VersusEpisode.release

    def spy(self, seat):
        calls.append(seat)
        return real(self, seat)

    monkeypatch.setattr(VersusEpisode, "release", spy)
    m = Match(seed=11, rival="baseline", rival_budget_s=1.0)
    m.join(None, 0.0)
    now = 0.0
    for i in range(300):
        if i % 20 == 0:
            m.receive("A", json.dumps({"type": "keys", "keys": [["d"], ["d", "w"], []][i // 20 % 3]}), now)
        now += TICK_S
        m.advance(now)
    assert calls and set(calls) == {"A"}, set(calls)


def _play_playtest(monkeypatch, out, shot, held_at):
    """play.py --mode human --playtest with pygame's key state scripted per frame."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame = pytest.importorskip("pygame")
    import play
    n = {"i": -1}
    real_get = pygame.event.get

    def events(*a, **k):
        n["i"] += 1
        return real_get(*a, **k)

    class Pressed:
        def __getitem__(self, code):
            return code in held_at(n["i"])

    monkeypatch.setattr(pygame.event, "get", events)
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: Pressed())
    assert play.main(["--mode", "human", "--playtest", "--telemetry-dir", str(out), "--scale", "1",
                      "--screenshot", str(shot)]) == 0
    f = sorted(out.glob("*-A.jsonl"))[0]
    rows = [json.loads(x) for x in f.read_text().splitlines()[1:]]
    return [r for r in rows if r["type"] == "move"]


def test_play_playtest_saads_sequence_and_hold_through(monkeypatch, tmp_path):
    pygame = pytest.importorskip("pygame")
    D, W = pygame.K_d, pygame.K_w

    released = _play_playtest(monkeypatch, tmp_path / "r", tmp_path / "r.png",
                              lambda i: {D, W} if i < 3 else ({D} if i < 6 else set()))
    assert [e["move"] for e in released] == ["JUMP_RIGHT"], released
    held = _play_playtest(monkeypatch, tmp_path / "h", tmp_path / "h.png",
                          lambda i: {D, W} if i < 3 else {D})
    assert len(held) >= 3, held
