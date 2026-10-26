"""Every committed trace replays identically through the current engine.

This is the guard that engine changes (bug fixes, Level 1 mechanics) leave
the frozen suite's recorded behavior unchanged: same seed + same submitted
actions must give the same acceptance, effect, frames, kid and room at every
step, and the same outcome.
"""

import json
from pathlib import Path

import pytest

from pop.interface import Episode

TRACES = sorted(Path(__file__).resolve().parent.parent.glob("traces/*/*.jsonl"))


def _load(path: Path):
    header, steps = None, []
    for line in path.read_text().splitlines():
        if line.strip():
            rec = json.loads(line)
            if rec.get("type") == "episode":
                header = rec
            elif rec.get("type") == "step":
                steps.append(rec)
    return header, steps


def test_there_are_committed_traces():
    assert len(TRACES) >= 15


@pytest.mark.parametrize("path", TRACES, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_committed_trace_replays_identically(path):
    header, steps = _load(path)
    assert header is not None, path
    limits = header.get("limits") or {}
    kwargs = {}
    if "max_actions" in limits:
        kwargs["max_actions"] = limits["max_actions"]
    if "max_consecutive_invalid" in limits:
        kwargs["max_consecutive_invalid"] = limits["max_consecutive_invalid"]
    ep = Episode(header["situation"], **kwargs)
    ep.reset(header["seed"])
    for rec in steps:
        res = ep.step("kid", rec["action"])
        assert res["accepted"] == rec["accepted"], rec["i"]
        if rec["accepted"]:
            assert res["effect"] == rec["effect"], rec["i"]
        assert res["frames"] == rec["frames"], rec["i"]
        if rec.get("kid") is not None:
            assert res["observation"]["kid"] == rec["kid"], rec["i"]
        if rec.get("room") is not None:
            assert res["observation"]["room"] == rec["room"], rec["i"]
    if "outcome" in header and header.get("outcome"):
        out = ep.outcome()
        rec_out = header["outcome"]
        # Runner-only reasons (call_limit) are not visible to a bare Episode.
        if rec_out["reason"] not in ("call_limit",):
            assert out["reason"] == rec_out["reason"]
        assert out["actions"] == rec_out["actions"]
        assert out["frames"] == rec_out["frames"]
