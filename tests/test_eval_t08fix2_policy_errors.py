"""T08-fix2 (decision #84): PPO inference errors are written into every result row.

`agents/rl/policy.py` swallows an inference exception into WAIT and counts it
(`policy_errors()`); a silent WAIT looks like a passive seat. These tests use a
network that raises, scripted and WAIT seats, and short frame caps. No real policy run.
"""

from __future__ import annotations

import copy
import json

from agents.macros import MacroController
from agents.rl.policy import PolicyMacro
from evaluation import analysis, controllers as C, manifest, spec, suite

GIT = {"commit": "0" * 40, "dirty": False}


class BrokenNet:
    def act(self, x, mask):
        raise RuntimeError("inference failed")


def broken_rival():
    pm = PolicyMacro(BrokenNet(), 1, 6)
    ctrl = MacroController(pm, name="ppo-broken", kind="policy", decision_every=6, macro_every=1)
    ctrl.policy_errors = lambda: pm.errors
    return ctrl


def tiny(frames=60):
    raw = copy.deepcopy(json.loads(manifest.TUNING_PATH.read_text()))
    for sc in raw["scenarios"]:
        sc["duration_frames"] = frames
    return spec.parse_scenarios(raw, "tuning")


def run(config, factory, tmp_path):
    [t] = [t for t in suite.plan_trials(tiny(), ["D1"], [config], 1, 0, policy_factory=factory)
           if t.start_id == "D1-a"]
    return suite.run_trial(t, tmp_path, seed_key=suite.DRY_RUN_KEY, key_id="k", run_id="r",
                           git=GIT, dry_run=True)


def test_a_policy_seat_whose_network_raises_shows_policy_errors(tmp_path):
    row = run("MvS", broken_rival, tmp_path)
    assert row["seats"]["A"]["policy_errors"] > 0
    assert row["seats"]["B"]["policy_errors"] is None         # a scripted seat has no counter


def test_non_policy_seats_record_null(tmp_path):
    row = run("SvS", None, tmp_path)
    assert row["seats"]["A"]["policy_errors"] is None and row["seats"]["B"]["policy_errors"] is None


def test_the_counter_helper():
    assert C.policy_errors_of(broken_rival()) == 0
    assert C.policy_errors_of(C.build("wait")) is None


def _row(row_id, split, a, b, config="MvS"):
    return {"row_id": row_id, "scenario": "H6", "start_id": "s", "config": config, "split": split,
            "aborted": False, "seats": {"A": {"policy_errors": a}, "B": {"policy_errors": b}}}


def test_the_analysis_sums_per_condition_and_lists_odd_rows():
    rows = [_row("r0", "heldout", 0, None), _row("r1", "heldout", 3, None),
            _row("r2", "heldout", 2, None)]
    assert analysis.policy_error_totals(rows) == [
        {"scenario": "H6", "start_id": "s", "config": "MvS", "policy_errors": 5,
         "rows_with_errors": 2}]
    text = "\n".join(analysis.policy_error_lines(rows))
    assert "r1" in text and "r2" in text and "r0" not in text
    assert "harness error" in text


def test_old_rows_without_the_field_are_read_as_not_recorded():
    old = {"row_id": "r", "scenario": "H6", "start_id": "s", "config": "MvS", "split": "heldout",
           "aborted": False, "seats": {"A": {"errors": 0}}}
    assert analysis.policy_error_totals([old])[0]["policy_errors"] == 0
    assert "not recorded" in "\n".join(analysis.policy_error_lines([old]))


def test_the_section_names_odd_rows():
    text = "\n".join(analysis.policy_error_lines([_row("r1", "heldout", 4, None)]))
    assert "Odd rows" in text and "r1" in text
