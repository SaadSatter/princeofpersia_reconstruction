"""T08-fix1 item 7 and 8 (decisions #66, #75, #76, #77, E-6): the claims the documents make,
and the evaluator-side script that generates the F-3 exposure table.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from evaluation import manifest, stats
from pop import arena
from tools.eval import exposure_table

ROOT = Path(__file__).resolve().parent.parent
PROTOCOL = (ROOT / "docs/final/evaluation/PROTOCOL.md").read_text()
README = (ROOT / "evaluation/heldout/README.md").read_text()


def section(text, start, end):
    i = text.index(start)
    return text[i:text.index(end, i)]


def test_section_3_claims_unseen_start_pairs_and_guard_layouts_not_unseen_cells():
    s3 = section(PROTOCOL, "## 3. Splits", "## 4. Freeze rule")
    assert "unseen start pairs and guard layouts" in s3
    assert "patrol ranges are not" in s3
    assert "start cells and guard post tuples are disjoint" in s3
    assert "no H6 guard post is a tuning-scenario post or a default arena post" not in s3 \
        or "tuple" in s3


def test_the_readme_says_the_same_and_no_longer_says_appear_nowhere_else():
    assert "unseen start pairs and guard layouts" in README
    assert "patrol ranges are not" in README
    assert "appear nowhere else" not in README
    assert "OFF LIMITS" in README


def test_the_pre_registered_t09_bar_is_written_down_before_the_run():
    assert "at least 14 of the 16" in PROTOCOL
    assert "no aborted duel" in PROTOCOL
    assert "not supported" in PROTOCOL
    assert "7 of 8 per 4 starts" in PROTOCOL
    assert "pre-registered" in PROTOCOL.lower()


def test_h_b_says_the_skill_scenarios_are_a_result_not_a_defect():
    assert "trained for duels only" in PROTOCOL
    assert "a result, not a defect" in PROTOCOL


def test_the_best_possible_intervals_for_the_new_sizes_are_stated_and_correct():
    # 16 held-out duels: 14 of 16 clears 0.5; 13 of 16 does not clear 0.6
    assert round(stats.wilson(16, 16)[0], 2) == 0.81
    assert round(stats.wilson(14, 16)[0], 2) == 0.64
    for needle in ("0.81", "0.64", "0.44", "0.61"):
        assert needle in PROTOCOL, needle
    # 6 starts per skill scenario (3 + 3 mirrored)
    assert round(stats.wilson(6, 6)[0], 2) == 0.61
    assert round(stats.wilson(3, 3)[0], 2) == 0.44


def test_b2_and_d1_text_matches_decisions_59_66_76():
    assert "still disguised at the end" in PROTOCOL
    assert "#76" in PROTOCOL and "#66" in PROTOCOL
    assert "the agent struck" in PROTOCOL or "in the guard's room" in PROTOCOL
    assert "#64" in PROTOCOL and "engine commit" in PROTOCOL
    assert "refusals.jsonl" in PROTOCOL


def test_the_protocol_no_longer_says_four_starts_or_eight_guard_posts():
    s3 = section(PROTOCOL, "## 3. Splits", "### 3.1")
    assert "four full-duel starts, eight guard posts" not in s3
    assert "eight full-duel starts" in s3 and "sixteen guard posts" in s3


# --- item 8: the exposure table is generated, not hand-written -----------------------------------------
def training_cells():
    out = set()
    for room, row, (c0, c1), _ in arena.GUARD_POSTS.values():
        out |= {(room, row, c) for c in range(c0, c1 + 1)}
    return out


def test_the_exposure_table_reproduces_the_gate_2_numbers_for_the_first_four_starts():
    starts = json.loads(manifest.HELDOUT_PATH.read_text())["scenarios"][0]["starts"][:4]
    table = exposure_table.exposure(starts)
    assert (table["full"], table["partial"], table["none"]) == (2, 1, 5)
    assert table["posts"] == 8


def test_the_exposure_table_covers_all_eight_starts_and_labels_each_start():
    starts = json.loads(manifest.HELDOUT_PATH.read_text())["scenarios"][0]["starts"]
    table = exposure_table.exposure(starts)
    assert table["posts"] == 16
    assert table["full"] + table["partial"] + table["none"] == 16
    assert [r["start"] for r in table["per_start"]] == [s["id"] for s in starts]
    for r in table["per_start"]:
        assert r["label"] in ("training-like", "partly training-like", "unseen layout")
    text = exposure_table.render(starts)
    assert "H6-1" in text and "H6-8" in text and "generated" in text.lower()


def test_exposure_counts_a_post_by_the_training_patrol_cells_it_covers():
    t = exposure_table.exposure([{"id": "x", "guards": {"a": [4, 2, [1, 3], 1],
                                                       "b": [4, 2, [7, 9], 1],
                                                       "c": [2, 2, [1, 3], 1]}}])
    assert (t["full"], t["partial"], t["none"]) == (1, 1, 1)
    assert re.fullmatch(r"[a-z ]+", t["per_start"][0]["label"].replace("-", " "))
