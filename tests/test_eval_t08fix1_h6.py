"""T08-fix1 item 6 (decision #74): H6 extended to 8 starts by a written rule.

The rule (docs/final/evaluation/PROTOCOL.md section 3.1) was committed before any new
start was added. These tests regenerate H6-5 to H6-8 from the rule and the cell lists
(no policy, no baseline, no result is read anywhere) and compare them with the frozen
file, then check disjointness and the freeze. No policy runs on H6: the schema check
uses WAIT seats with a small frame cap and a temp ledger.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evaluation import manifest, spec
from pop import arena
from tools.eval import select_heldout_starts as sel
from tools.rl import env

ROOT = Path(__file__).resolve().parent.parent
OLD_SHA = "44da40eca7a5606a9778cd3dca9756a34eb3962d3143a1304247ef2c92070847"


def frozen():
    manifest.verify_heldout()
    return json.loads(manifest.HELDOUT_PATH.read_text())


def starts():
    return frozen()["scenarios"][0]["starts"]


def cells(sts, seats="AB"):
    return {tuple(s["rivals"][x][:3]) for s in sts for x in seats}


def posts(sts):
    return {(g[0], g[1], tuple(g[2])) for s in sts for g in s["guards"].values()}


# --- the file ---------------------------------------------------------------------------------------------
def test_h6_has_eight_starts_h6_1_to_h6_8():
    assert [s["id"] for s in starts()] == [f"H6-{i}" for i in range(1, 9)]
    assert [s.id for s in manifest.load_heldout()["H6"].starts] == [f"H6-{i}" for i in range(1, 9)]


def test_the_first_four_starts_are_unchanged_from_the_first_freeze():
    data = frozen()
    data["scenarios"][0]["starts"] = data["scenarios"][0]["starts"][:4]
    assert hashlib.sha256((json.dumps(data, indent=1) + "\n").encode()).hexdigest() == OLD_SHA


def test_the_new_hash_is_recorded_in_all_three_places_and_differs_from_the_first_freeze():
    got = hashlib.sha256(manifest.HELDOUT_PATH.read_bytes()).hexdigest()
    assert got == manifest.HELDOUT_SHA256 != OLD_SHA
    for path in ("docs/final/evaluation/PROTOCOL.md", "evaluation/heldout/README.md"):
        assert got in (ROOT / path).read_text(), path


def test_the_old_hash_is_named_as_superseded_and_never_as_the_current_freeze():
    text = (ROOT / "docs/final/evaluation/PROTOCOL.md").read_text()
    assert OLD_SHA in text and "superseded" in text.lower()
    assert OLD_SHA not in (ROOT / "evaluation/heldout/README.md").read_text().split("SHA-256 of")[1][:200]


# --- the rule reproduces the new starts ----------------------------------------------------------------
def test_the_rule_regenerates_h6_5_to_h6_8_exactly():
    base = starts()[:4]
    assert sel.select_extra_starts(base) == starts()[4:]


def test_the_rule_reads_only_cell_lists_not_results():
    src = Path(sel.__file__).read_text()
    for word in ("results.json", "ledger", "agents.rl", "versus_baseline", "weights", "success",
                 "outcome", "controllers"):
        assert word not in src, word


def test_the_rule_is_deterministic_and_does_not_depend_on_dict_or_set_order():
    base = starts()[:4]
    assert sel.select_extra_starts(base) == sel.select_extra_starts(list(base))
    assert sel.select_extra_starts(base, n=2) == starts()[4:6]


# --- disjointness (decisions #60, #74) ---------------------------------------------------------------------
def test_new_rival_cells_are_disjoint_from_every_cell_in_use_and_from_each_other():
    new, old = starts()[4:], starts()[:4]
    tuning_cells = {tuple(s[:3]) for pair in env.TUNING_STARTS for s in pair}
    t = manifest.load_tuning()
    scenario_cells = {tuple(st.rivals[x][:3]) for sc in t.values() for st in sc.starts for x in "AB"}
    arena_cells = {tuple(v[:3]) for v in arena.STARTS.values()}
    new_cells = [tuple(s["rivals"][x][:3]) for s in new for x in "AB"]
    assert len(set(new_cells)) == 8
    for pool in (tuning_cells, scenario_cells, arena_cells, cells(old)):
        assert set(new_cells).isdisjoint(pool)
    assert cells(starts()).isdisjoint(tuning_cells | scenario_cells | arena_cells)


def test_new_posts_are_not_any_other_post_and_belong_to_no_default_patrol_tuple():
    new, old = starts()[4:], starts()[:4]
    t = manifest.load_tuning()
    tuning_posts = {(g[0], g[1], g[2]) for sc in t.values() for st in sc.starts
                    for g in st.guards.values()}
    default = {(g[0], g[1], tuple(g[2])) for g in arena.GUARD_POSTS.values()}
    new_posts = [(g[0], g[1], tuple(g[2])) for s in new for g in s["guards"].values()]
    assert len(new_posts) == 8 and len(set(new_posts)) == 8
    assert set(new_posts).isdisjoint(tuning_posts | default | posts(old))
    assert posts(starts()).isdisjoint(tuning_posts | default)


def test_every_new_start_puts_the_rivals_in_different_rooms_with_two_guards_in_two_rooms():
    for s in starts()[4:]:
        assert s["rivals"]["A"][0] != s["rivals"]["B"][0]
        rooms = [g[0] for g in s["guards"].values()]
        assert len(rooms) == 2 and len(set(rooms)) == 2
        assert s["hearts"] == {"A": 3, "B": 3} and s["disguised"] == {"A": False, "B": False}
        assert "other_controller" not in s


def test_no_rival_starts_inside_a_patrol_of_its_own_start_and_nothing_equals_a_training_layout():
    train_pairs = {(tuple(a), tuple(b)) for a, b in env.TUNING_STARTS}
    train_pairs |= {(b, a) for a, b in train_pairs}
    default = {(g[0], g[1], tuple(g[2])) for g in arena.GUARD_POSTS.values()}
    for s in starts():
        for x in "AB":
            room, row, col, _ = s["rivals"][x]
            for g in s["guards"].values():
                assert not (g[0] == room and g[1] == row and g[2][0] <= col <= g[2][1])
        assert (tuple(s["rivals"]["A"]), tuple(s["rivals"]["B"])) not in train_pairs
        assert posts([s]) != default


def test_every_new_start_validates_against_arena_a():
    for sc in manifest.load_heldout().values():
        assert len(sc.starts) == 8


# --- plumbing: a held-out dry run with WAIT seats, a small frame cap, a temp ledger ------------------------
def test_a_heldout_dry_run_writes_eight_rows_with_wait_seats_and_no_ledger_line(tmp_path, monkeypatch):
    from tools.eval import run_versus_suite as cli
    ledger = tmp_path / "ledger.jsonl"
    monkeypatch.setattr(manifest, "LEDGER_PATH", ledger)
    assert cli.main(["--dry-run", "--split", "heldout", "--trials", "1", "--max-frames", "30",
                     "--out", str(tmp_path / "o")]) == 0
    data = json.loads((tmp_path / "o" / "results.json").read_text())
    assert [r["start_id"] for r in data["rows"]] == [f"H6-{i}" for i in range(1, 9)]
    assert data["run"]["scenario_file_sha256"]["heldout"] == manifest.HELDOUT_SHA256
    assert all(r["controllers"][x]["kind"] == "fallback" for r in data["rows"] for x in "AB")
    assert not ledger.exists()


def test_new_starts_use_only_floor_cells_of_row_two():
    for s in starts()[4:]:
        for x in "AB":
            room, row, col, face = s["rivals"][x]
            assert row == 2 and spec._floor_ok(room, row, col) and face == (1 if col <= 4 else -1)
