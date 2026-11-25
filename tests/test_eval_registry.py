"""T08: scenario registry, the frozen held-out set H6, and the freeze checks.

Decisions: #9 (D1, B2, I3, F5 approved, H6 held out), #60 (H6-4's B start moved
off a tuning cell, chosen from the cell set, not from policy results), #61.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path

import pytest

from evaluation import manifest, spec
from pop import arena
from tools.rl import env

ROOT = Path(__file__).resolve().parent.parent
HELD = ROOT / "evaluation" / "heldout" / "H6.json"


def tuning():
    return spec.load_scenario_file(manifest.TUNING_PATH, "tuning")


def heldout():
    return manifest.load_heldout()


def rival_cells(scenarios):
    return {(st.rivals[s][0], st.rivals[s][1], st.rivals[s][2])
            for sc in scenarios.values() for st in sc.starts for s in "AB"}


def guard_posts(scenarios):
    return {(g[0], g[1], g[2]) for sc in scenarios.values() for st in sc.starts
            for g in st.guards.values()}


def guard_cells(scenarios):
    return {(g[0], g[1], c) for sc in scenarios.values() for st in sc.starts
            for g in st.guards.values() for c in range(g[2][0], g[2][1] + 1)}


# --- the registry ------------------------------------------------------------------------
def test_tuning_split_has_the_four_approved_scenarios_with_three_or_more_starts():
    t = tuning()
    assert list(t) == ["D1", "B2", "I3", "F5"]
    assert [t[k].kind for k in t] == ["disguise", "blend", "identify", "fight"]
    assert all(len(sc.starts) >= 3 for sc in t.values())
    assert all(sc.split == "tuning" and sc.subject == "A" for sc in t.values())


def test_each_scenario_quotes_saads_words():
    t = tuning()
    assert "kills a guard and picks up the disguise" in t["D1"].definition
    assert "doesn't notice it or keeps low suspicion" in t["B2"].definition
    assert "distinguish between player guard and real guard" in t["I3"].definition
    assert "wins a duel against a player or guard" in t["F5"].definition


def test_heldout_split_is_one_full_duel_scenario_h6_with_four_starts():
    h = heldout()
    assert list(h) == ["H6"] and h["H6"].kind == "duel" and h["H6"].split == "heldout"
    assert h["H6"].duration_frames == 3600                        # the 5 minute duel, decision #5
    assert [s.id for s in h["H6"].starts] == ["H6-1", "H6-2", "H6-3", "H6-4"]


def test_every_start_validates_and_is_a_walkable_cell_in_distinct_rooms_or_cells():
    for scenarios in (tuning(), heldout()):
        for sc in scenarios.values():
            for st in sc.starts:
                a, b = st.rivals["A"], st.rivals["B"]
                assert a[:3] != b[:3]


def test_parse_rejects_a_start_inside_a_wall():
    raw = json.loads(manifest.TUNING_PATH.read_text())
    bad = copy.deepcopy(raw)
    bad["scenarios"][0]["starts"][0]["rivals"]["A"] = [1, 2, 0, 1]      # '#' wall at room 1 col 0
    with pytest.raises(spec.SpecError):
        spec.parse_scenarios(bad, "tuning")


def test_parse_rejects_a_wrong_split_a_duplicate_start_and_an_unknown_kind():
    raw = json.loads(manifest.TUNING_PATH.read_text())
    with pytest.raises(spec.SpecError):
        spec.parse_scenarios(raw, "heldout")
    dup = copy.deepcopy(raw)
    dup["scenarios"][0]["starts"].append(copy.deepcopy(dup["scenarios"][0]["starts"][0]))
    with pytest.raises(spec.SpecError):
        spec.parse_scenarios(dup, "tuning")
    kind = copy.deepcopy(raw)
    kind["scenarios"][0]["kind"] = "nope"
    with pytest.raises(spec.SpecError):
        spec.parse_scenarios(kind, "tuning")


def test_parse_rejects_a_guard_patrol_across_a_gap_and_an_absurd_duration():
    raw = json.loads(manifest.TUNING_PATH.read_text())
    gap = copy.deepcopy(raw)
    gap["scenarios"][0]["starts"][0]["guards"] = {"x": [1, 2, [5, 8], 1]}   # room 1 row 2 col 7 is a shaft
    with pytest.raises(spec.SpecError):
        spec.parse_scenarios(gap, "tuning")
    long = copy.deepcopy(raw)
    long["scenarios"][0]["duration_frames"] = 99999
    with pytest.raises(spec.SpecError):
        spec.parse_scenarios(long, "tuning")


def test_scenario_episode_applies_hearts_and_disguise_after_every_reset():
    t = tuning()
    start = t["F5"].start("F5-b")
    ep = spec.episode_factory(t["F5"], "F5-b")()
    assert ep._duel.rivals["A"].kid.hp == start.hearts["A"] == 2
    ep.step("A", "WAIT")
    ep.tick()
    ep.reset(7)
    assert ep._duel.rivals["A"].kid.hp == 2 and ep._duel.frames == 0
    b2 = spec.episode_factory(t["B2"], "B2-a")()
    assert b2._duel.rivals["A"].disguised is True and b2._duel.rivals["B"].disguised is False
    i3 = spec.episode_factory(t["I3"], "I3-a")()
    assert i3._duel.rivals["B"].disguised is True


def test_scenario_episode_places_rivals_and_guard_posts_from_the_start():
    t = tuning()
    ep = spec.episode_factory(t["D1"], "D1-a")()
    st = t["D1"].start("D1-a")
    k = ep._duel.rivals["A"].kid
    assert (k.room, k.row, k.col, k.facing) == tuple(st.rivals["A"])
    assert set(ep._duel.guards) == set(st.guards)


def test_make_monitor_builds_the_scenarios_monitor_with_the_start_values():
    t = tuning()
    mon = spec.make_monitor(t["B2"], t["B2"].start("B2-a"))
    assert mon.kind == "blend" and mon.low == 50
    f5b = spec.make_monitor(t["F5"], t["F5"].start("F5-b"))
    assert f5b.kind == "fight"
    i3 = spec.make_monitor(t["I3"], t["I3"].start("I3-a"))
    assert i3.rival_hp_start == 3


# --- the held-out freeze (decision #9 freeze rule, decision #60) -------------------------------
def test_heldout_file_matches_its_recorded_sha256_and_the_protocol_names_it():
    got = hashlib.sha256(HELD.read_bytes()).hexdigest()
    assert got == manifest.HELDOUT_SHA256
    assert manifest.verify_heldout() == got
    protocol = (ROOT / "docs" / "final" / "evaluation" / "PROTOCOL.md").read_text()
    assert manifest.HELDOUT_SHA256 in protocol
    readme = (ROOT / "evaluation" / "heldout" / "README.md").read_text()
    assert manifest.HELDOUT_SHA256 in readme and "OFF LIMITS" in readme


def test_an_edited_heldout_file_is_refused_before_it_is_parsed(tmp_path):
    edited = tmp_path / "H6.json"
    edited.write_text(HELD.read_text().replace('"H6-1"', '"H6-X"'))
    with pytest.raises(manifest.FreezeError):
        manifest.load_heldout(edited)
    with pytest.raises(manifest.FreezeError):
        manifest.verify_heldout(tmp_path / "missing.json")


def test_h6_shares_no_start_cell_with_the_eight_tuning_starts():
    assert len(env.TUNING_STARTS) == 8
    train = {(s[0], s[1], s[2]) for pair in env.TUNING_STARTS for s in pair}
    h6 = rival_cells(heldout())
    assert h6.isdisjoint(train), h6 & train


def test_h6_4_b_start_is_off_the_tuning_cell_and_off_every_other_cell_in_use():
    """Decision #60: the old B start (1,2,3,+1) is a tuning start (pair 2, seat A)."""
    h4 = heldout()["H6"].start("H6-4")
    b = h4.rivals["B"]
    assert tuple(b[:3]) != (1, 2, 3)
    assert b[0] == 1 and b[1] == 2                                  # same room and row
    cells = {tuple(s[:3]) for pair in env.TUNING_STARTS for s in pair}
    assert tuple(b[:3]) not in cells
    # The chosen rule (docs/final/evaluation/PROTOCOL.md): scan right from the old column and
    # take the first floor cell no tuning start, other H6 start or H6-4 guard patrol uses.
    assert tuple(b) == (1, 2, 4, 1)


def test_h6_rivals_do_not_start_inside_a_guard_patrol_of_their_own_start():
    for st in heldout()["H6"].starts:
        for seat in "AB":
            room, row, col, _ = st.rivals[seat]
            for g in st.guards.values():
                assert not (g[0] == room and g[1] == row and g[2][0] <= col <= g[2][1])


def test_h6_shares_no_start_cell_or_guard_post_with_tuning_scenarios_or_the_arena():
    h, t = heldout(), tuning()
    assert rival_cells(h).isdisjoint(rival_cells(t))
    assert rival_cells(h).isdisjoint({tuple(v[:3]) for v in arena.STARTS.values()})
    assert guard_posts(h).isdisjoint(guard_posts(t))
    assert guard_posts(h).isdisjoint({(g[0], g[1], g[2]) for g in arena.GUARD_POSTS.values()})


def test_h6_has_no_downed_guard_and_every_start_has_full_hearts_and_no_disguise():
    for st in heldout()["H6"].starts:
        assert st.hearts == {"A": 3, "B": 3} and st.disguised == {"A": False, "B": False}
        assert st.other_controller is None


def test_training_and_policy_code_never_read_the_heldout_directory():
    """T07 training must not be able to see H6 (decision #9 held-out rule)."""
    for sub in ("agents/rl", "tools/rl"):
        for path in sorted((ROOT / sub).rglob("*.py")):
            text = path.read_text()
            assert "heldout" not in text.lower().replace("held-out", ""), path
            assert "evaluation/" not in text, path
            for node in ast.walk(ast.parse(text)):
                names = ([a.name for a in node.names] if isinstance(node, ast.Import)
                         else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
                assert not any(n == "evaluation" or n.startswith("evaluation.") for n in names), path


def test_the_pop_engine_and_agents_do_not_import_the_evaluation_package():
    for sub in ("pop", "agents", "render", "server"):
        for path in sorted((ROOT / sub).rglob("*.py")):
            for node in ast.walk(ast.parse(path.read_text())):
                names = ([a.name for a in node.names] if isinstance(node, ast.Import)
                         else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
                assert not any(n == "evaluation" or n.startswith("evaluation.") for n in names), path


# --- the run-once ledger -----------------------------------------------------------------
def test_a_second_heldout_run_for_the_same_frozen_policy_is_refused(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    row = manifest.claim_heldout_run("abc123", {"run_id": "r1"}, ledger)
    assert row["heldout_sha256"] == manifest.HELDOUT_SHA256
    with pytest.raises(manifest.FreezeError):
        manifest.claim_heldout_run("abc123", {"run_id": "r2"}, ledger)
    manifest.claim_heldout_run("other-policy", {"run_id": "r3"}, ledger)       # another policy may run
    assert len(manifest.read_ledger(ledger)) == 2
    with pytest.raises(manifest.FreezeError):
        manifest.claim_heldout_run("", {}, ledger)
