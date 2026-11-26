"""QA probes for T20-fix2: every use counts once under realistic play, and old logs still read."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("websockets")

from tests.test_t20fix2_counts import match_rows   # noqa: E402
from tools.telemetry import summarize               # noqa: E402


def used(tmp, steps, seed=4242):
    rows = match_rows(tmp, steps, seed)
    return rows, summarize.mechanics_used(rows)


def test_running_jump_then_held_direction_is_one_flip(tmp_path):
    _, u = used(tmp_path, [(["d"], 8), (["d", "w"], 1), (["d"], 20), ([], 5)])
    assert u["flip"] == 1


def test_two_run_up_jumps_in_a_row_are_two_flips(tmp_path):
    _, u = used(tmp_path, [(["d"], 8), (["d", "w"], 1), ([], 20), (["d"], 8), (["d", "w"], 1), ([], 20)])
    assert u["flip"] == 2


def test_standing_jump_into_a_wall_is_not_a_flip(tmp_path):
    _, u = used(tmp_path, [(["a"], 200), ([], 5), (["a", "w"], 1), ([], 14)])
    assert u["flip"] == 0


@pytest.mark.parametrize("armed", [False, True])
def test_held_up_plus_direction_is_one_flip(tmp_path, armed):
    pre = [(["g"], 1), ([], 10)] if armed else []
    _, u = used(tmp_path, pre + [(["w", "d"], 20), ([], 5)])
    assert u["flip"] == 1


@pytest.mark.parametrize("keys", [["w"], ["s"]])
def test_held_stance_with_nothing_else_is_one_block(tmp_path, keys):
    _, u = used(tmp_path, [(["g"], 1), ([], 10), (keys, 20), ([], 5)])
    assert u["block"] == 1 and u["draw"] == 1


def test_stance_up_then_down_then_up_is_three_blocks(tmp_path):
    _, u = used(tmp_path, [(["g"], 1), ([], 10), (["w"], 10), (["s"], 10), (["w"], 10), ([], 5)])
    assert u["block"] == 3


def test_held_draw_key_marks_every_later_toggle_repeat(tmp_path):
    rows, u = used(tmp_path, [(["g"], 30)])
    assert (u["draw"], u["sheathe"]) == (1, 0)
    first, *rest = [r for r in rows if r["type"] == "move"]
    assert "repeat" not in first and rest and all(r.get("repeat") for r in rest)


def test_repeats_reconcile_for_a_held_draw(tmp_path):
    rows, u = used(tmp_path, [(["g"], 30)])
    mv, rp = summarize.moves_started(rows), summarize.repeats_by_move(rows)
    assert sum(mv.values()) - sum(rp.values()) == u["draw"] + u["sheathe"]


# --- old logs ---------------------------------------------------------------------------
def _log(tmp, schema, events):
    head = {"type": "header", "schema": schema, "build": "x", "seed": 1, "rival": "human",
            "room": "OLD", "duel": 1, "duel_frames": 3600, "ticks_per_second": 12,
            "idle_threshold_s": 3.0, "seat": "A"}
    rows = [head] + [dict(t=i, s=i / 12, seat="A", **e) for i, e in enumerate(events)]
    (tmp / "2026-11-25-OLD-001-A.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")


def test_schema_1_log_summarizes_per_accepted_action(tmp_path):
    _log(tmp_path, 1, [
        {"type": "duel_start", "room": "r", "hearts": 3, "armed": False, "traps_left": 4},
        {"type": "action", "action": "DRAW", "accepted": True},
        {"type": "action", "action": "STANCE_UP", "accepted": True},
        {"type": "action", "action": "JUMP_RIGHT", "accepted": True, "effect": "flipped"},
        {"type": "duel_end", "result": "draw", "reason": "time"}])
    doc = summarize.summarize(tmp_path)
    m = doc["seats"][0]
    assert m["mechanics"]["draw"] == 1 and m["mechanics"]["block"] == 1 and m["mechanics"]["flip"] == 1
    assert m["repeats"] == 0 and m["moves"] == {}
    assert summarize.markdown(doc)


def test_early_schema_2_log_without_stance_repeat_or_effect_summarizes(tmp_path):
    _log(tmp_path, 2, [
        {"type": "duel_start", "room": "r", "hearts": 3, "armed": False, "traps_left": 4},
        {"type": "action", "action": "STANCE_UP", "accepted": True},
        {"type": "move", "move": "RUN_JUMP_RIGHT"},                # no effect key
        {"type": "move", "move": "DRAW", "effect": "moved"},
        {"type": "action", "action": "STANCE_DOWN", "accepted": True},
        {"type": "duel_end", "result": "draw", "reason": "time"}])
    doc = summarize.summarize(tmp_path)
    m = doc["seats"][0]
    assert m["mechanics"]["flip"] == 1 and m["mechanics"]["draw"] == 1 and m["mechanics"]["block"] == 2
    assert summarize.markdown(doc)


def test_committed_fixtures_summarize_without_error():
    root = Path(__file__).parent / "data" / "t20_telemetry"
    for d in (root, root / "v2"):
        assert summarize.summarize(d)["logs"] > 0
