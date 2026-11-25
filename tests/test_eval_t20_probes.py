"""T20 Gate 2 (evaluation specialist) probes: knowledge boundary by non-interference,
determinism across seeds and the AI seat, and what the summarizer's counts measure.

A seat's log may not depend on anything its own observation hides. Method: run the same
inputs for seat A twice, once with seat B idle and once with B doing things A cannot see
(disguise, rigging a trap, wandering in its own room); A's log must be byte-identical.
Nothing here tunes against held-out scenarios.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path

import pytest

pytest.importorskip("websockets")

from server.match import TICK_S, Match            # noqa: E402
from server.telemetry import Telemetry            # noqa: E402
from tools.telemetry import summarize             # noqa: E402

SEED = 4242


def mk(tmp, seed=SEED, rival=None):
    tele = None if tmp is None else Telemetry(tmp, "EVAL", info={"build": "ev"},
                                              today=lambda: "2026-11-25")
    return Match(seed=seed, rival=rival, telemetry=tele, rival_budget_s=1.0)


def run(tmp, b_script, a_script, ticks=140, hidden=None, seed=SEED):
    m = mk(tmp, seed)
    m.join(None, 0.0), m.join(None, 0.0)
    d = m.episode._duel
    now = 0.0
    for i in range(ticks):
        if hidden and i == 5:
            hidden(d)
        for seat, script in (("A", a_script), ("B", b_script)):
            if i % 6 == 0:
                keys = script[(i // 6) % len(script)]
                m.receive(seat, json.dumps({"type": "keys", "keys": keys}), now)
        now += TICK_S
        m.advance(now)
    return m


def a_log(tmp):
    return (tmp / "2026-11-25-EVAL-001-A.jsonl").read_text()


def hidden_b(d):
    d.rivals["B"].disguised = True
    k = d.rivals["B"].kid
    d.place_rig("B", (k.room, k.row, k.col - 1))
    d.traps_left["B"] -= 1


B_BUSY = [["g"], ["t"], ["a"], ["a"], ["f"], [], ["d"], ["w", "d"], ["s"], ["lshift", "a"]]
A_WALK = [[], [], ["d"], ["d"], [], ["f"], [], ["g"], []]


def test_a_log_is_identical_whatever_b_hides(tmp_path):
    base, busy = tmp_path / "idle", tmp_path / "busy"
    run(base, [[]], A_WALK)
    run(busy, B_BUSY, A_WALK, hidden=hidden_b)
    assert a_log(base) == a_log(busy)
    kinds = {json.loads(x)["type"] for x in a_log(busy).splitlines()[1:]}
    assert not kinds & {"disguise_on", "disguise_broken", "trap_rigged", "trap_sprung"}
    assert "disguise" not in a_log(busy).lower()


@pytest.mark.parametrize("seed", [1, 7, 4242, 99])
@pytest.mark.parametrize("rival", [None, "baseline"])
def test_trace_hash_and_messages_equal_with_and_without_logging(tmp_path, seed, rival):
    outs = []
    for tmp in (None, tmp_path):
        m = mk(tmp, seed, rival)
        m.join(None, 0.0)
        if rival is None:
            m.join(None, 0.0)
        rng = random.Random(seed)
        keysets = [[], ["d"], ["a"], ["w", "d"], ["f"], ["g"], ["t"], ["s"], ["left"], ["."], ["/"]]
        now, sent = 0.0, []
        for i in range(900):
            if i % 5 == 0:
                for s in m.human_seats:
                    m.receive(s, json.dumps({"type": "keys", "keys": rng.choice(keysets)}), now)
            now += TICK_S
            m.advance(now)
            for s in ("A", "B"):
                sent += [(s, x) for x in m.drain(s)]
        outs.append((m.trace(), json.dumps(sent)))
    assert outs[0][0] == outs[1][0] and outs[0][1] == outs[1][1]
    assert outs[0][0]["state_hash"] == outs[1][0]["state_hash"]


def test_recorder_source_only_reads():
    """The recorder calls no step, tick, reset, engine internals, RNG or clock (ast, so
    docstrings that name them do not count)."""
    import ast
    tree = ast.parse(Path("server/telemetry.py").read_text())
    called = {n.func.attr for n in ast.walk(tree)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert not called & {"step", "tick", "reset", "rematch", "press"}, called
    # T20-fix1 (#81, #85): the one added read is the seat's own resolved move
    assert "started_move" in called
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert not any(a.startswith("_duel") or a == "rivals" for a in attrs)
    assert not attrs & {"_move_action", "_rewrite", "_started"}, attrs
    imported = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    assert not imported & {"random", "time"}, imported


def test_tap_counts_one_use_not_one_per_tick(tmp_path):
    """A one-tick tap of each mechanic key: how many uses does the summarizer count?"""
    res = {}
    for name, keys in (("TAKE", ["g"]), ("RIG", ["t"]), ("flip", ["d", "w"])):
        tmp = tmp_path / name
        m = mk(tmp)
        m.join(None, 0.0), m.join(None, 0.0)
        now = 0.0
        m.receive("A", json.dumps({"type": "keys", "keys": keys}), now)
        now += TICK_S
        m.advance(now)
        m.receive("A", json.dumps({"type": "keys", "keys": []}), now)
        for _ in range(40):
            now += TICK_S
            m.advance(now)
        rows = [json.loads(x) for x in a_log(tmp).splitlines()]
        res[name] = summarize.mechanics_used(rows[1:])
    print({k: {kk: vv for kk, vv in v.items() if vv} for k, v in res.items()})
    assert res["TAKE"]["TAKE"] <= 1 and res["RIG"]["RIG"] <= 1 and res["flip"]["flip"] <= 1


def test_a_queued_direction_is_not_credited_with_the_running_flip(tmp_path):
    m = mk(tmp_path)
    m.join(None, 0.0), m.join(None, 0.0)
    now = 0.0
    for keys, n in ((["d", "w"], 1), (["a"], 3), ([], 14)):
        m.receive("A", json.dumps({"type": "keys", "keys": keys}), now)
        for _ in range(n):
            now += TICK_S
            m.advance(now)
    m.close()
    rows = [json.loads(x) for x in a_log(tmp_path).splitlines()[1:]]
    assert summarize.mechanics_used(rows)["flip"] == 1


def test_grace_resolved_action_is_not_in_the_public_read_surface(tmp_path):
    """For the F2 fix: the engine resolves RUN_JUMP_RIGHT (submitted, in ep.log) to JUMP_RIGHT,
    and `observe(seat)["me"]["motion"]["effect"]` is "flipped" for both. A recorder that reads
    only the public surface cannot tell grace from a plain jump; the resolved action is
    private to the Duel (`_move_action`)."""
    effects = []
    for script in ([["d"], ["d", "w"], [], []], [["d", "w"], [], [], []]):
        m = mk(None)
        m.join(None, 0.0), m.join(None, 0.0)
        now = 0.0
        for keys in script:
            m.receive("A", json.dumps({"type": "keys", "keys": keys}), now)
            now += TICK_S
            m.advance(now)
        effects.append((m.episode.observe("A")["me"]["motion"] or {}).get("effect"))
        assert m.episode.legal_actions("A") is not None
    assert effects[0] == effects[1] == "flipped"


# --- T20-fix1 Gate 2 (decision #86): the reporting-only `_rewrite` label and StartedMove ---
def test_rewrite_label_is_written_in_start_and_read_only_by_started_move():
    """Every use of `_rewrite` in pop/, agents/ and server/ (ast): one init, one write in
    `Duel._start`, one read in `VersusEpisode.started_move`. No rule, observation or
    snapshot reads it."""
    import ast
    uses = []
    paths = (sorted(Path("pop").glob("*.py")) + sorted(Path("agents").rglob("*.py"))
             + sorted(Path("server").glob("*.py")))
    for path in paths:
        tree = ast.parse(path.read_text())
        for fn in ast.walk(tree):
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for n in ast.walk(fn):
                    if isinstance(n, ast.Attribute) and n.attr == "_rewrite":
                        uses.append((str(path), fn.name, type(n.ctx).__name__))
    uses = sorted(set(uses))
    # `self._rewrite[seat] = x` is a Load of the dict attribute; only the __init__ line stores it
    assert uses == [("pop/versus.py", "__init__", "Store"),
                    ("pop/versus.py", "_start", "Load"),
                    ("pop/versus.py", "started_move", "Load")], uses
    src = Path("pop/versus.py").read_text()
    snap = src[src.index("def snapshot"):src.index("# --- what one seat sees")]
    assert "rewrite" not in snap


def _drive(seed, rival, ticks=700, blind=False):
    """A fuzz duel through the server Match; `blind` makes Duel._start drop the label."""
    from pop import versus
    orig = versus.Duel._start
    if blind:
        versus.Duel._start = lambda self, seat, action, rewrite=None: orig(self, seat, action, None)
    try:
        m = mk(None, seed, rival)
        m.join(None, 0.0)
        if rival is None:
            m.join(None, 0.0)
        rng = random.Random(seed)
        keysets = [[], ["d"], ["a"], ["w", "d"], ["w", "a"], ["w"], ["f"], ["g"], ["t"], ["s"],
                   ["lshift", "d"], ["."], ["/"]]
        now, sent, obs, labelled = 0.0, [], [], 0
        for i in range(ticks):
            if i % 3 == 0:
                for s in m.human_seats:
                    m.receive(s, json.dumps({"type": "keys", "keys": rng.choice(keysets)}), now)
            now += TICK_S
            m.advance(now)
            for s in ("A", "B"):
                sent += [(s, x) for x in m.drain(s)]
                obs.append(json.dumps([m.episode.observe(s), m.episode.legal_actions(s)],
                                      sort_keys=True))
                sm = m.episode.started_move(s)
                labelled += bool(sm is not None and sm.rewrite)
        return m.trace(), json.dumps(sent), obs, labelled
    finally:
        versus.Duel._start = orig


@pytest.mark.parametrize("seed", [1, 7, 4242])
@pytest.mark.parametrize("rival", [None, "baseline"])
def test_rewrite_label_changes_no_trace_hash_observation_or_message(seed, rival):
    """Same duel with the label and with `_start` forced to drop it: trace, state hash,
    every client message, every observation and legal-action list are identical."""
    a = _drive(seed, rival)
    b = _drive(seed, rival, blind=True)
    assert a[0] == b[0] and a[0]["state_hash"] == b[0]["state_hash"]
    assert a[1] == b[1]
    assert a[2] == b[2]
    assert b[3] == 0           # the blind run really had no labels


def test_labelled_run_actually_exercises_labels():
    assert sum(_drive(s, None)[3] for s in (1, 7, 4242, 99, 5)) > 0


def _play(tmp, script):
    m = mk(tmp)
    m.join(None, 0.0), m.join(None, 0.0)
    now = 0.0
    for keys, n in script:
        m.receive("A", json.dumps({"type": "keys", "keys": keys}), now)
        for _ in range(n):
            now += TICK_S
            m.advance(now)
    m.close()
    return [json.loads(x) for x in a_log(tmp).splitlines()[1:]]


def test_a_running_jump_is_counted_as_a_flip(tmp_path):
    rows = _play(tmp_path, [(["d"], 8), (["d", "w"], 1), ([], 14)])
    assert [e["move"] for e in rows if e["type"] == "move"][-1] == "RUN_JUMP_RIGHT"
    assert summarize.mechanics_used(rows)["flip"] == 1


def test_a_held_draw_key_is_one_use(tmp_path):
    rows = _play(tmp_path, [(["g"], 30)])
    used = summarize.mechanics_used(rows)
    assert used["draw"] <= 1 and used["sheathe"] <= 1


def test_no_seat_surface_names_a_rewrite():
    """Observation, legal actions and client messages never carry rewrite/grace/started/hop."""
    for seed in (1, 7):
        _, sent, obs, _ = _drive(seed, None)
        blob = sent + "".join(obs)
        for word in ("rewrite", "grace", "hop_turn", "_HOP_FLIP", "started_move", "StartedMove"):
            assert word not in blob, word
