"""T20-fix2: one use counts once, whatever the move's first frames read (E2, E3, `moves` note).

The summarizer counts a mechanic's uses from the engine's own started moves (`move` rows).
A running jump starts as a run and becomes the flip inside the same move; a held draw key
toggles DRAW and SHEATHE. Every mechanic in the summary has a test here: one press, and one
held key, each count 1, driven through the real engine and recorder.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

pytest.importorskip("websockets")

from pop import arena                                   # noqa: E402
from pop.versus import SEATS, VersusEpisode             # noqa: E402
from server.match import TICK_S, Match                  # noqa: E402
from server.telemetry import Telemetry                  # noqa: E402
from tools.telemetry import summarize                   # noqa: E402


def rows_of(tmp, seat="A"):
    f = sorted(Path(tmp).glob(f"*-{seat}.jsonl"))[0]
    return [json.loads(x) for x in f.read_text().splitlines()[1:]]


# --- through the web match: keys, as a player holds them -------------------------------
def match_rows(tmp, steps, seed=4242):
    tele = Telemetry(tmp, "FIX2", info={}, today=lambda: "2026-11-25")
    m = Match(seed=seed, rival=None, telemetry=tele, rival_budget_s=1.0)
    m.join(None, 0.0)
    m.join(None, 0.0)
    now = 0.0
    for keys, n in steps:
        m.receive("A", json.dumps({"type": "keys", "keys": keys}), now)
        for _ in range(n):
            now += TICK_S
            m.advance(now)
    m.close()
    return rows_of(tmp)


def test_a_running_jump_is_one_flip(tmp_path):
    rows = match_rows(tmp_path, [(["d"], 8), (["d", "w"], 1), ([], 14)])
    assert [r["move"] for r in rows if r["type"] == "move"][-1] == "RUN_JUMP_RIGHT"
    assert summarize.mechanics_used(rows)["flip"] == 1
    assert summarize.moves_started(rows) == {"RIGHT": 2, "RUN_JUMP_RIGHT": 1}


def test_a_standing_jump_is_one_flip(tmp_path):
    rows = match_rows(tmp_path, [(["d", "w"], 1), ([], 14)])
    assert summarize.mechanics_used(rows)["flip"] == 1


@pytest.mark.parametrize("held", [1, 5, 30])
def test_a_held_running_jump_is_one_flip(tmp_path, held):
    rows = match_rows(tmp_path, [(["d"], 8), (["d", "w"], held), ([], 20)])
    assert summarize.mechanics_used(rows)["flip"] == 1


def test_a_shift_running_jump_is_one_flip(tmp_path):
    rows = match_rows(tmp_path, [(["d", "w", "lshift"], 1), ([], 16)])
    assert summarize.mechanics_used(rows)["flip"] == 1


def test_two_separate_jumps_are_two_flips(tmp_path):
    rows = match_rows(tmp_path, [(["d", "w"], 1), ([], 16), (["a", "w"], 1), ([], 16)])
    assert summarize.mechanics_used(rows)["flip"] == 2


def test_a_held_draw_key_is_one_use(tmp_path):
    rows = match_rows(tmp_path, [(["g"], 30)])
    used = summarize.mechanics_used(rows)
    assert (used["draw"], used["sheathe"]) == (1, 0)
    moves = [r for r in rows if r["type"] == "move"]
    assert moves[0]["move"] == "DRAW" and "repeat" not in moves[0]
    assert len(moves) > 2 and all(r.get("repeat") for r in moves[1:])   # the toggles that follow


def test_separate_draw_then_sheathe_presses_are_two_uses(tmp_path):
    rows = match_rows(tmp_path, [(["g"], 1), ([], 10), (["g"], 1), ([], 10)])
    used = summarize.mechanics_used(rows)
    assert (used["draw"], used["sheathe"]) == (1, 1)


def test_a_new_press_of_the_draw_key_is_a_new_use(tmp_path):
    rows = match_rows(tmp_path, [(["g"], 14), ([], 10), (["g"], 14)])
    used = summarize.mechanics_used(rows)
    assert used["draw"] + used["sheathe"] == 2


def test_moves_minus_repeats_reconciles_where_one_move_is_one_mechanic(tmp_path):
    rows = match_rows(tmp_path, [(["g"], 1), ([], 10), (["f"], 30)])
    used = summarize.mechanics_used(rows)
    moves, rep = summarize.moves_started(rows), summarize.repeats_by_move(rows)
    assert rep["LUNGE"] > 0
    assert moves["LUNGE"] - rep["LUNGE"] == used["lunge"] == 1
    toggles = ("DRAW", "SHEATHE")
    assert (sum(moves.get(k, 0) - rep.get(k, 0) for k in toggles)
            == used["draw"] + used["sheathe"] == 1)


def test_flip_does_not_reconcile_by_name_alone(tmp_path):
    """Documented: a held jump is several starts and one flip; `moves - repeats` counts
    every new start (the run, the jump), not flips."""
    rows = match_rows(tmp_path, [(["d"], 8), (["d", "w"], 30), ([], 20)])
    moves, rep = summarize.moves_started(rows), summarize.repeats_by_move(rows)
    assert summarize.mechanics_used(rows)["flip"] == 1
    assert sum(moves.values()) - sum(rep.values()) > 1       # RIGHT as well as the jump


def test_summary_has_a_per_seat_repeats_count(tmp_path):
    match_rows(tmp_path, [(["d"], 40), ([], 10)])
    doc = summarize.summarize(tmp_path)
    seat = next(s for s in doc["seats"] if s["seat"] == "A")
    assert seat["repeats"] > 0
    assert seat["repeats"] == sum(seat["repeats_by_move"].values())
    assert seat["repeats"] < sum(seat["moves"].values())
    assert "held key running on" in summarize.markdown(doc)


def test_is_flip_rows():
    f = summarize.is_flip
    assert f({"move": "RUN_JUMP_LEFT", "effect": "moved"})
    assert f({"move": "JUMP_LEFT", "effect": "flipped"})
    assert f({"move": "_HOP_FLIP_RIGHT", "effect": "flipped"})
    assert not f({"move": "JUMP_LEFT", "effect": "bumped"})
    assert not f({"move": "RIGHT", "effect": "moved"})
    assert not f({"move": "STEP_RIGHT", "effect": "moved"})
    assert not f({"move": "KICK", "effect": "kicked"})


# --- every mechanic, one engine, a press and a held key --------------------------------
def episode(a=(2, 0, 1, +1), b=(3, 2, 7, -1), posts=None, seed=0):
    return VersusEpisode(arena.situation("A"), dict(arena.STARTS, A=a, B=b), seed, guard_posts=posts)


def recorder(ep):
    tmp = Path(tempfile.mkdtemp())
    rec = Telemetry(tmp, "EP", info={}, today=lambda: "2026-11-25").new_duel(ep, SEATS, "human", 0.0)
    return rec, tmp


def drive(ep, rec, action, held, rest=24):
    """Ask `action` on `held` consecutive ticks (a held key), then let the move finish."""
    for i in range(held + rest):
        before = len(ep.log)
        if i < held:
            ep.step("A", action)
        ep.tick()
        rec.after_tick([(s, a) for _, s, a in ep.log[before:]], 0.0)


def counted(rec, tmp):
    rec.close(0.0)
    rows = rows_of(tmp)
    return summarize.mechanics_used(rows), rows


@pytest.mark.parametrize("held", [1, 20])
def test_rig_counts_once(held):
    ep = episode()
    rec, tmp = recorder(ep)
    drive(ep, rec, "RIG", held)
    used, rows = counted(rec, tmp)
    assert used["RIG"] == 1
    assert sum(1 for r in rows if r["type"] == "trap_rigged") == 1


@pytest.mark.parametrize("held", [1, 20])
def test_take_counts_once_and_the_disguise_once(held):
    ep = episode(a=(2, 0, 1, +1), posts={"g": (2, 0, (2, 2))})
    ep._duel.guards["g"].downed = True
    rec, tmp = recorder(ep)
    drive(ep, rec, "TAKE", held)
    used, _ = counted(rec, tmp)
    assert used["TAKE"] == 1 and used["disguise"] == 1


@pytest.mark.parametrize("action,name", [("LUNGE", "lunge"), ("THROW", "throw")])
@pytest.mark.parametrize("held", [1, 20])
def test_armed_attacks_count_once(action, name, held):
    ep = episode()
    rec, tmp = recorder(ep)
    drive(ep, rec, "DRAW", 1)
    drive(ep, rec, action, held)
    used, _ = counted(rec, tmp)
    assert used["draw"] == 1 and used[name] == 1


@pytest.mark.parametrize("held", [1, 20])
def test_sweep_counts_once(held):
    ep = episode()
    rec, tmp = recorder(ep)
    drive(ep, rec, "SWEEP", held)
    used, _ = counted(rec, tmp)
    assert used["sweep"] == 1


def test_a_kick_over_a_jump_is_one_kick_and_one_flip():
    ep = episode(a=(2, 0, 2, +1), b=(2, 0, 4, -1))
    rec, tmp = recorder(ep)
    drive(ep, rec, "DRAW", 1, rest=14)
    drive(ep, rec, "JUMP_RIGHT", 1, rest=6)
    drive(ep, rec, "KICK", 1, rest=14)
    used, rows = counted(rec, tmp)
    assert [r["move"] for r in rows if r["type"] == "move"][-2:] == ["JUMP_RIGHT", "KICK"]
    assert used["kick"] == 1 and used["flip"] == 1


def test_a_hop_turned_into_a_flip_is_one_flip():
    ep = episode(a=(2, 0, 1, +1), b=(3, 2, 7, -1))
    rec, tmp = recorder(ep)
    drive(ep, rec, "UP", 1, rest=0)
    drive(ep, rec, "JUMP_RIGHT", 1, rest=16)
    used, rows = counted(rec, tmp)
    assert used["flip"] == 1, [r["move"] for r in rows if r["type"] == "move"]


@pytest.mark.parametrize("held", [1, 20])
def test_block_stance_counts_once(held):
    ep = episode()
    rec, tmp = recorder(ep)
    drive(ep, rec, "DRAW", 1, rest=14)
    drive(ep, rec, "STANCE_UP", held)
    used, _ = counted(rec, tmp)
    assert used["block"] == 1


@pytest.mark.parametrize("held", [1, 20])
def test_sword_pickup_counts_once(held):
    ep = episode()
    d = ep._duel
    d.rivals["A"].sword = "none"                    # DOWN picks up only when unarmed
    d.swords.append(d.rivals["A"].kid.cell)
    rec, tmp = recorder(ep)
    drive(ep, rec, "DOWN", held)
    used, _ = counted(rec, tmp)
    assert used["sword_pickup"] == 1


def test_two_separate_stance_presses_are_two_blocks():
    ep = episode()
    rec, tmp = recorder(ep)
    drive(ep, rec, "DRAW", 1, rest=14)
    drive(ep, rec, "STANCE_UP", 1, rest=8)
    drive(ep, rec, "STANCE_DOWN", 1, rest=8)
    used, _ = counted(rec, tmp)
    assert used["block"] == 2


def test_a_held_stance_key_marks_its_later_ticks_repeat():
    ep = episode()
    rec, tmp = recorder(ep)
    drive(ep, rec, "DRAW", 1, rest=14)
    drive(ep, rec, "STANCE_DOWN", 1, rest=8)          # mid to low, so UP has two steps to go
    drive(ep, rec, "STANCE_UP", 8, rest=8)
    rec.close(0.0)
    stance = [r for r in rows_of(tmp) if r["type"] == "action" and r["action"] == "STANCE_UP"]
    assert len(stance) >= 2 and "repeat" not in stance[0]
    assert all(r.get("repeat") for r in stance[1:])


def test_a_log_without_a_stance_repeat_marker_still_counts_each_press_once():
    rows = [{"type": "action", "action": "STANCE_UP", "accepted": True, "t": 1},
            {"type": "move", "move": "RIGHT", "effect": "moved", "t": 2}]
    assert summarize.mechanics_used(rows)["block"] == 1
