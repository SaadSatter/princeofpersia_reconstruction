"""Every committed trace replays identically through the current engine.

The guard that engine changes (bug fixes, Level 1 mechanics) leave the
frozen suite's recorded behavior unchanged. For each committed trace, with
the same seed and the same submitted actions:

1. every recorded field (acceptance, effect, frames, kid, room) and the
   final outcome match the trace;
2. the **complete authoritative state** after reset and after every step
   (kid incl. fall progress and sword, frames, terminal, all rooms' tiles,
   every gate/exit/plate/spike/loose-floor timer, episode counters) matches
   the fingerprint made by replaying the trace with the engine **at the
   commit that recorded it** (`tests/data/trace_states.json`, generated in
   session 10 from temporary worktrees at those commits);
3. the kid is in a physically consistent state at every step.

Never regenerate the golden file to make this pass: a divergence means the
engine changed recorded behavior, which needs the student's decision.
"""

import json
from pathlib import Path

import pytest

from consistency import assert_consistent
from pop.interface import Episode
from trace_state import episode_kwargs, load_trace, replay_fingerprints

ROOT = Path(__file__).resolve().parent.parent
TRACES = sorted(ROOT.glob("traces/*/*.jsonl"))
GOLDEN = json.loads((ROOT / "tests" / "data" / "trace_states.json").read_text())
IDS = lambda p: f"{p.parent.name}/{p.name}"  # noqa: E731


def test_every_committed_trace_has_a_golden_state_record():
    assert len(TRACES) == 16
    assert {str(p.relative_to(ROOT)) for p in TRACES} == set(GOLDEN)


@pytest.mark.parametrize("path", TRACES, ids=IDS)
def test_committed_trace_replays_identically(path):
    header, steps = load_trace(path)
    assert header is not None, path
    ep = Episode(header["situation"], **episode_kwargs(header))
    ep.reset(header["seed"])
    assert_consistent(ep._game, "reset")
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
        assert_consistent(ep._game, f"step {rec['i']}")
    if header.get("outcome"):
        out, rec_out = ep.outcome(), header["outcome"]
        # Runner-only reasons (call_limit) are not visible to a bare Episode.
        if rec_out["reason"] != "call_limit":
            assert out["reason"] == rec_out["reason"]
        assert out["actions"] == rec_out["actions"]
        assert out["frames"] == rec_out["frames"]


@pytest.mark.parametrize("path", TRACES, ids=IDS)
def test_complete_state_matches_the_recording_engine(path):
    golden = GOLDEN[str(path.relative_to(ROOT))]
    now = replay_fingerprints(Episode, path)
    assert len(now) == len(golden["fingerprints"])
    for i, (a, b) in enumerate(zip(now, golden["fingerprints"])):
        assert a == b, (f"state after {'reset' if i == 0 else f'step {i - 1}'} differs from "
                        f"the engine at {golden['recorded_with']}")
