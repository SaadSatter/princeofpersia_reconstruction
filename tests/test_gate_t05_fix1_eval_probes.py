"""Gate 2 (Evaluation Specialist) probes for T05-fix1, commit ce8c8c0. Offline, no training, no API.

1. Boundary: over full-length duels in which the baseline walks every floor, takes a
   uniform (so `last_result` is read) and meets guards, it reads only fields a human seat
   could see, and under `last_result` only `effect`.
2. Seat symmetry: baseline vs baseline from the default start (QA N1).
"""

from __future__ import annotations

import collections

from agents.versus_baseline import make_baseline
from pop import arena
from pop.seats import WaitController
from pop.versus import VersusEpisode
from pop.versus_runner import VersusLimits, VersusRunner
from tests.test_gate_t05_eval_baseline import ALLOWED_FIGURE, _Logged, _Spy

ALLOWED_TOP = {"room", "edges", "tiles", "state", "kid", "me", "figures", "suspicion", "last_result"}


def _episode():
    return VersusEpisode(arena.situation("A"), dict(arena.STARTS), 0, 3600, arena.GUARD_POSTS)


def test_gate2_fix1_baseline_reads_only_visible_fields_over_full_duels():
    _Logged.used = collections.Counter()
    for seed in (0, 1, 2):
        for swap in (False, True):
            ctrls = {"A": _Spy(make_baseline()), "B": WaitController()}
            if swap:
                ctrls = {"A": WaitController(), "B": _Spy(make_baseline())}
            res = VersusRunner(_episode, ctrls, limits=VersusLimits(max_frames=3600),
                               copy_mode="json", threaded=False).run(seed)
            assert res["outcome"]["reason"].startswith("won:")
    top = {k.split(".")[1].rstrip("[]") for k in _Logged.used}
    assert top <= ALLOWED_TOP, top - ALLOWED_TOP
    assert {k.split(".")[2] for k in _Logged.used if k.startswith("obs.figures[].")} <= ALLOWED_FIGURE
    lr = {k for k in _Logged.used if k.startswith("obs.last_result.")}
    assert lr <= {"obs.last_result.effect"}, lr
    # `last_result` is read only after a TAKE; the duels above may not reach that branch, so
    # also scan the source: the only use in the baseline path is `.get("effect")`.
    import pathlib
    for f in ("agents/macros.py", "agents/versus_baseline.py"):
        src = pathlib.Path(f).read_text()
        assert src.count("last_result") == src.count('get("last_result") or {}).get("effect")'), f


def test_gate2_fix1_mirror_match_is_one_trace_decided_by_seat_order():
    """Documents QA N1: the seed does not change the mirror match; one seat wins every time."""
    reasons = collections.Counter()
    for seed in range(6):
        res = VersusRunner(_episode, {"A": make_baseline("a"), "B": make_baseline("b")},
                           limits=VersusLimits(max_frames=3600), clock=lambda: 0.0).run(seed)
        reasons[res["outcome"]["reason"]] += 1
    assert len(reasons) == 1, reasons
