"""The shipped weights of PPO run 1 (decision #51, task T07-run1).

Checks the file, its hash chain (constant, summary.json, file), the format and
the pure-Python rival built from it. Tuning-start evidence only; no strength claim.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from agents.rl import policy as pol
from agents.rl.encoder import MACRO_SLOTS, N_FEATURES
from agents.rl.policy import load_net, make_rl_rival
from pop import arena
from pop.seats import WaitController
from pop.versus import VersusEpisode
from pop.versus_runner import VersusLimits, VersusRunner

ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / "tools" / "rl" / "runs" / "run-1"
EXPECTED = "80e4a1100fddbdbbb8a4504fc8f7a2aa1b6d8a28bb4b053519634d742b5aba4c"


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def test_shipped_constants_name_the_committed_file_and_its_hash():
    assert Path(pol.SHIPPED_WEIGHTS) == ROOT / "agents" / "rl" / "weights" / "ppo-run-1.json"
    assert pol.SHIPPED_SHA256 == EXPECTED
    assert _sha(pol.SHIPPED_WEIGHTS) == pol.SHIPPED_SHA256


def test_hash_chain_summary_and_file_agree():
    summary = json.loads((RUN / "summary.json").read_text())
    assert summary["weights_sha256"] == pol.SHIPPED_SHA256
    assert summary["weights_failed"] is False and summary["weights_file"] == "weights.json"
    assert not (RUN / "weights.failed.json").exists()
    assert summary["policy_errors"] == 0 and summary["checkpoint_chosen_by_score"] is False


def test_evidence_matches_the_run_counts():
    summary = json.loads((RUN / "summary.json").read_text())
    rows = [json.loads(x) for x in (RUN / "log.jsonl").read_text().splitlines() if x.strip()]
    assert len(rows) == summary["updates"] == 1568
    assert rows[-1]["steps"] == summary["steps"] == 1487955
    assert summary["episodes"] == 25088
    assert "exit=0" in (RUN / "run-1.meta").read_text()


def test_file_is_plain_json_in_the_trained_format_and_sizes():
    data = json.loads(Path(pol.SHIPPED_WEIGHTS).read_text())
    assert data["format"] == pol.FORMAT == "sm-ppo-mlp-1"
    assert data["sizes"] == [N_FEATURES, 64, 64, len(MACRO_SLOTS)] == [251, 64, 64, 9]
    assert data["macros"] == list(MACRO_SLOTS)
    assert all(isinstance(v, float) for v in data["layers"][0]["b"])


def test_load_net_loads_it_and_refuses_a_wrong_hash():
    net = load_net(pol.SHIPPED_WEIGHTS, pol.SHIPPED_SHA256)
    assert net.sizes == (251, 64, 64, 9)
    with pytest.raises(pol.WeightsError):
        load_net(pol.SHIPPED_WEIGHTS, "0" * 64)


def test_short_duel_with_the_shipped_rival_is_deterministic_with_no_fallbacks():
    def go():
        rival = make_rl_rival(pol.SHIPPED_WEIGHTS, pol.SHIPPED_SHA256)
        res = VersusRunner(lambda: VersusEpisode(arena.situation("A"), arena.STARTS, 0, 3600,
                                                 arena.GUARD_POSTS),
                           {"A": rival, "B": WaitController()}, copy_mode="json",
                           threaded=False, limits=VersusLimits(max_frames=600)).run(3)
        return res["final_snapshot_sha256"], res["seats"]["A"]["fallbacks"], rival.policy_errors()
    a, b = go(), go()
    assert a == b and a[1] == 0 and a[2] == 0
