"""T20-fix1: count a use once, log the move the engine started (decisions #81 to #83).

Covers: one held key is one use; a key queued during a running flip is not a flip; the
R-V35 grace marker and the summary dropping the superseded direction; a kick that replaced
a jump and a hop that turned into a flip log as the engine's move; determinism and the
recorder's read surface; the pause end on forfeit (F3); the 12-tick refused-run threshold.
"""

from __future__ import annotations

import ast
import json
import random
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("websockets")

from pop import arena                                   # noqa: E402
from pop import versus as V                             # noqa: E402
from pop.versus import SEATS, VersusEpisode             # noqa: E402
from server.match import TICK_S, Match                  # noqa: E402
from server.telemetry import Telemetry                  # noqa: E402
from tools.telemetry import summarize                   # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def mk(tmp, seed=4242):
    tele = None if tmp is None else Telemetry(tmp, "FIX1", info={"build": "f1"},
                                              today=lambda: "2026-11-25")
    m = Match(seed=seed, rival=None, telemetry=tele, rival_budget_s=1.0)
    m.join(None, 0.0)
    m.join(None, 0.0)
    return m


def hold(m, keys, ticks, now, seat="A"):
    m.receive(seat, json.dumps({"type": "keys", "keys": keys}), now)
    for _ in range(ticks):
        now += TICK_S
        m.advance(now)
    return now


def rows_of(tmp, seat="A"):
    f = sorted(tmp.glob(f"*-{seat}.jsonl"))[0]
    return [json.loads(x) for x in f.read_text().splitlines()[1:]]


def summary_of(tmp, seat="A"):
    doc = summarize.summarize(tmp)
    return next(s for s in doc["seats"] if s["seat"] == seat)


def script(tmp, steps):
    m = mk(tmp)
    now = 0.0
    for keys, n in steps:
        now = hold(m, keys, n, now)
    m.close()
    return rows_of(tmp)


# --- 1: one use, counted at the move's start --------------------------------------------
@pytest.mark.parametrize("held", [1, 4, 10, 11])
def test_one_held_flip_is_one_flip(tmp_path, held):
    script(tmp_path, [(["d", "w"], held), ([], 24)])
    assert summary_of(tmp_path)["mechanics"]["flip"] == 1


def test_a_jump_then_three_left_ticks_is_one_flip(tmp_path):
    rows = script(tmp_path, [(["d", "w"], 1), (["a"], 3), ([], 16)])
    assert summary_of(tmp_path)["mechanics"]["flip"] == 1
    left = [r for r in rows if r["type"] == "move" and r["move"] == "LEFT"]
    assert left and all(r["effect"] != "flipped" for r in left)   # its own effect, not the flip's


def test_two_separate_taps_are_two_flips(tmp_path):
    script(tmp_path, [(["d", "w"], 1), ([], 20), (["d", "w"], 1), ([], 20)])
    assert summary_of(tmp_path)["mechanics"]["flip"] == 2


def test_action_rows_have_no_effect_and_move_rows_carry_the_started_effect(tmp_path):
    rows = script(tmp_path, [(["d", "w"], 3), ([], 16)])
    acts = [r for r in rows if r["type"] == "action"]
    assert acts and all("effect" not in r for r in acts)
    moves = [r for r in rows if r["type"] == "move"]
    assert moves[0]["move"] == "JUMP_RIGHT" and moves[0]["effect"] == "flipped"
    assert acts[0]["started"] == "JUMP_RIGHT" and acts[1]["started"] is None


# --- 2: R-V35 grace (decision #82) ------------------------------------------------------
def test_grace_jump_row_is_marked_and_the_summary_drops_the_direction(tmp_path):
    rows = script(tmp_path, [(["d"], 1), (["d", "w"], 1), ([], 16)])
    moves = [r for r in rows if r["type"] == "move"]
    assert [r["move"] for r in moves][:2] == ["RIGHT", "JUMP_RIGHT"]      # append-only: both written
    assert moves[1].get("grace") is True and "grace" not in moves[0]
    jump_actions = [r for r in rows if r["type"] == "action" and r["action"] == "RUN_JUMP_RIGHT"]
    assert jump_actions and jump_actions[0]["started"] == "JUMP_RIGHT" and jump_actions[0]["grace"]
    s = summary_of(tmp_path)
    assert "RIGHT" not in s["moves"] and s["moves"]["JUMP_RIGHT"] == 1
    assert s["mechanics"]["flip"] == 1


def test_a_plain_jump_is_not_grace(tmp_path):
    rows = script(tmp_path, [(["d", "w"], 1), ([], 20)])
    assert not any(r.get("grace") for r in rows)


def test_recorder_grace_agrees_with_the_engines_own_cancel(tmp_path, monkeypatch):
    """Differential fuzz: every jump the engine started by cancelling a direction (R-V35)
    carries the marker, and no other move does."""
    truth: list[tuple[int, str]] = []
    real = V.Duel._grace_jump

    def spy(self, seat):
        out = real(self, seat)
        if out is not None:
            truth.append((self.frames, seat))
        return out

    monkeypatch.setattr(V.Duel, "_grace_jump", spy)
    keysets = [[], ["d"], ["a"], ["d", "w"], ["a", "w"], ["w"], ["d"], ["a"], []]
    marked = 0
    for seed in (1, 2, 3):
        d = tmp_path / str(seed)
        truth.clear()
        m = mk(d, seed)
        rng, now = random.Random(seed), 0.0
        for _ in range(250):
            for seat in ("A", "B"):
                m.receive(seat, json.dumps({"type": "keys", "keys": rng.choice(keysets)}), now)
            for _ in range(rng.randint(1, 3)):
                now += TICK_S
                m.advance(now)
        m.close()
        for seat in SEATS:
            got = {r["t"] for r in rows_of(d, seat) if r["type"] == "move" and r.get("grace")}
            want = {t for t, s in truth if s == seat}
            assert got == want, (seed, seat, got, want)
            marked += len(got)
    assert marked > 0, "the fuzz never hit a grace cancel; widen it"


# --- 3: kick swap and hop turn log as the engine's move ---------------------------------
def _episode_recorder(tmp, a, b):
    ep = VersusEpisode(arena.situation("A"), dict(arena.STARTS, A=a, B=b), 0)
    tele = Telemetry(tmp, "EP", info={}, today=lambda: "2026-11-25")
    rec = tele.new_duel(ep, SEATS, "human", 0.0)
    return ep, rec


def _tick(ep, rec, steps=()):
    before = len(ep.log)
    for seat, action in steps:
        ep.step(seat, action)
    ep.tick()
    rec.after_tick([(s, a) for _, s, a in ep.log[before:]], 0.0)


def test_a_kick_that_replaced_a_jump_logs_as_a_kick(tmp_path):
    ep, rec = _episode_recorder(tmp_path, (2, 0, 2, +1), (2, 0, 4, -1))
    _tick(ep, rec, [("A", "DRAW"), ("B", "DRAW")])
    for _ in range(V.DRAW_FRAMES + 1):
        _tick(ep, rec)
    _tick(ep, rec, [("A", "JUMP_RIGHT")])
    for _ in range(6):
        _tick(ep, rec)
    _tick(ep, rec, [("A", "KICK")])
    rec.close(0.0)
    moves = [r["move"] for r in rows_of(tmp_path) if r["type"] == "move"]
    assert moves[-2:] == ["JUMP_RIGHT", "KICK"]
    assert summary_of(tmp_path)["mechanics"]["kick"] == 1


def test_a_hop_that_turned_into_a_flip_logs_as_the_flip(tmp_path):
    ep, rec = _episode_recorder(tmp_path, (2, 0, 1, +1), (3, 2, 7, -1))
    _tick(ep, rec, [("A", "UP")])
    _tick(ep, rec, [("A", "JUMP_RIGHT")])
    for _ in range(14):
        _tick(ep, rec)
    rec.close(0.0)
    moves = [r for r in rows_of(tmp_path) if r["type"] == "move"]
    assert [m["move"] for m in moves[:2]] == ["UP", "_HOP_FLIP_RIGHT"]
    assert moves[1]["effect"] == "flipped"
    assert summary_of(tmp_path)["mechanics"]["flip"] == 1       # the hop is not a flip, the turn is


# --- 4: determinism and the read surface -----------------------------------------------
KEYSETS = [[], [], ["d"], ["a"], ["w", "d"], ["w", "a"], ["f"], ["g"], ["t"], ["s"], ["d", "lshift"],
           ["up", "right"], ["down"]]


@pytest.mark.parametrize("seed", [1, 7])
@pytest.mark.parametrize("rival", [None, "baseline"])
def test_trace_hash_and_messages_equal_with_and_without_logging(tmp_path, seed, rival):
    outs = []
    for tag in ("off", "on"):
        tele = None if tag == "off" else Telemetry(tmp_path / tag, "DET", info={},
                                                   today=lambda: "2026-11-25")
        m = Match(seed=seed, rival=rival, telemetry=tele, rival_budget_s=1.0)
        m.join(None, 0.0)
        if rival is None:
            m.join(None, 0.0)
        rng, now, sent = random.Random(seed), 0.0, []
        for i in range(700):
            if i % 5 == 0:
                for s in m.human_seats:
                    m.receive(s, json.dumps({"type": "keys", "keys": rng.choice(KEYSETS)}), now)
            now += TICK_S
            m.advance(now)
            for s in SEATS:
                sent += [(s, x) for x in m.drain(s)]
        outs.append((m.trace(), json.dumps(sent)))
    assert outs[0][0] == outs[1][0] and outs[0][1] == outs[1][1]
    assert outs[0][0]["state_hash"] == outs[1][0]["state_hash"]


def test_recorder_reads_only_observe_legal_outcome_and_started_move():
    tree = ast.parse((ROOT / "server/telemetry.py").read_text())
    called = {n.func.attr for n in ast.walk(tree)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert not called & {"step", "tick", "reset", "rematch", "press", "submit"}, called
    assert "started_move" in called
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert not any(a.startswith("_duel") or a in ("rivals", "_move_action", "_started") for a in attrs)
    imported = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    assert not imported & {"random", "time"}


# --- 5: F3, pause end on forfeit -------------------------------------------------------
def test_a_paused_duel_that_ends_by_forfeit_logs_the_pause_end(tmp_path):
    m = mk(tmp_path)
    now = hold(m, [], 10, 0.0)
    m.connection_lost("B", now)
    m.advance(now + 16)
    for seat in SEATS:
        ev = rows_of(tmp_path, seat)
        phases = [e["phase"] for e in ev if e["type"] == "pause"]
        assert phases == ["start", "end"], (seat, phases)
        types = [e["type"] for e in ev]
        assert types.index("pause", types.index("pause") + 1) < types.index("forfeit")


def test_no_pause_end_is_invented_when_there_was_no_pause(tmp_path):
    rows = script(tmp_path, [([], 10)])
    assert not [r for r in rows if r["type"] == "pause"]


# --- 6: thresholds (decision #83) ------------------------------------------------------
def test_thresholds_are_named_constants():
    from server import telemetry
    assert summarize.REFUSED_RUN_MIN == 12 and summarize.STUCK_ROOM_S == 60.0
    assert telemetry.IDLE_THRESHOLD_S == 3


def test_a_three_tick_refusal_is_not_a_stall_and_twelve_is():
    def run_of(n):
        ev = [{"type": "action", "action": "LUNGE", "accepted": False, "t": i} for i in range(n)]
        return summarize.refused_runs(ev)
    assert run_of(3) == [] and run_of(11) == []
    assert run_of(12)[0]["length"] == 12


# --- 7: a schema 2 fixture, byte-identical output --------------------------------------
def test_schema_2_fixture_summarizes_with_grace_and_repeat(tmp_path):
    fx = ROOT / "tests/data/t20_telemetry/v2"
    outs = []
    for name in ("one", "two"):
        r = subprocess.run([sys.executable, str(ROOT / "tools/telemetry/summarize.py"), str(fx),
                            "--out", str(tmp_path / name)], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        outs.append(tmp_path / name)
    for n in ("summary.json", "summary.md"):
        assert (outs[0] / n).read_bytes() == (outs[1] / n).read_bytes()
    doc = json.loads((outs[0] / "summary.json").read_text())
    seat = doc["seats"][0]
    assert seat["mechanics"]["flip"] == 2 and seat["mechanics"]["TAKE"] == 1
    assert seat["moves"] == {"JUMP_LEFT": 2, "JUMP_RIGHT": 1, "TAKE": 2}
