"""Run the versus suite: one row per trial, traces per trial, replay.

Library behind `tools/eval/run_versus_suite.py`. Decision #24 (runner policy):
aborted runs are reported (never dropped), the seed key is secret (never
written to a result or trace; only a short id), and every trial gets fresh
controllers. Success is computed by a monitor from true state through the
runner's `on_frame` hook and is never shown to a controller.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from dataclasses import asdict
from pathlib import Path

from pop import GAME_VERSION
from pop.versus_runner import (VersusLimits, VersusRunner, digest, load_traces, replay,
                               save_traces)

from . import SCHEMA_VERSION, controllers as C, manifest, monitors
from .spec import Scenario, episode_factory, make_monitor

ROOT = Path(__file__).resolve().parent.parent
CONFIG_LETTERS = {"S": "scripted", "M": "policy"}
CONFIGS = ("SvS", "MvS", "SvM", "MvM")
TEST_ONLY_CONFIGS = ("MvM",)
DEFAULT_DECISION_EVERY = 6
DRY_RUN_KEY = b"dry-run-public-key"
DRY_RUN_KEY_ID = "dry-run-public"
PENDING_SAAD = {
    "B2_low_threshold": {"value": monitors.B2_LOW_THRESHOLD, "status": "pending Saad",
                         "meaning": "suspicion strictly below this (of 100) at every frame"},
    "B2_min_cells_active_reading": {"value": monitors.B2_MIN_CELLS, "status": "pending Saad",
                                    "meaning": "alternate reading: distinct cells visited"},
    "D1_copresence_scope": {"value": monitors.D1_COPRESENCE_SCOPE, "status": "pending Saad",
                            "meaning": "the other rival is not in the agent's room at any "
                                       "frame of the scenario"},
}


def parse_config(config: str) -> tuple[str, str]:
    if config not in CONFIGS:
        raise ValueError(f"configuration must be one of {CONFIGS}")
    return config[0], config[2]


def git_state(root: Path = ROOT) -> dict:
    def run(*args):
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True,
                              timeout=20).stdout.strip()
    try:
        return {"commit": run("rev-parse", "HEAD") or "unknown",
                "dirty": bool(run("status", "--porcelain", "--untracked-files=no"))}
    except (OSError, subprocess.SubprocessError):
        return {"commit": "unknown", "dirty": None}


def seed_key_id(key: bytes) -> str:
    return hashlib.sha256(b"seed-key-id:" + key).hexdigest()[:8]


def load_seed_key(path: str | Path) -> bytes:
    key = Path(path).read_text().strip().encode()
    if len(key) < 16:
        raise ValueError("the seed key must be at least 16 characters")
    return key


def _result_for(reason: str | None, seat: str) -> str:
    if reason is None:
        return "unfinished"
    if reason.startswith("won:"):
        return "win" if reason.endswith(seat) else "loss"
    return "draw"


def _latency(records: list[dict]) -> dict:
    values = [r["latency_ms"] for r in records]
    return {"basis": "measured (time.perf_counter, per decision)", "n": len(values),
            "mean_ms": round(sum(values) / len(values), 3) if values else None,
            "max_ms": max(values) if values else None}


class Trial:
    """What one trial needs (so a test can build one without the CLI)."""

    def __init__(self, scenario: Scenario, start_id: str, config: str, trial: int, seed: int,
                 *, policy_factory=None, force_wait: bool = False, test_only: bool = False):
        self.scenario, self.start_id, self.config = scenario, start_id, config
        self.trial, self.seed = trial, seed
        self.policy_factory, self.force_wait, self.test_only = policy_factory, force_wait, test_only

    @property
    def row_id(self) -> str:
        return f"{self.scenario.id}/{self.start_id}/{self.config}/t{self.trial}"

    def build_controllers(self) -> tuple[dict, dict]:
        """Fresh controllers; seat B's is forced when the start says so."""
        start = self.scenario.start(self.start_id)
        letters = parse_config(self.config)
        built, forced = {}, {}
        for seat, letter in zip("AB", letters):
            kind = "wait" if self.force_wait else CONFIG_LETTERS[letter]
            if seat == "B" and start.other_controller and not self.force_wait:
                kind, forced["B"] = start.other_controller, start.other_controller
            built[seat] = C.build(kind, self.policy_factory)
            if kind == "policy" and built[seat].kind != "policy":
                raise ValueError("a policy factory must build kind='policy' controllers")
        return built, forced


def run_trial(t: Trial, out_dir: Path, *, seed_key: bytes, key_id: str, run_id: str,
              git: dict, dry_run: bool, decision_every: int = DEFAULT_DECISION_EVERY,
              limits: VersusLimits | None = None, scope: str = monitors.D1_COPRESENCE_SCOPE
              ) -> dict:
    sc = t.scenario
    start = sc.start(t.start_id)
    row = {"schema": SCHEMA_VERSION, "run_id": run_id, "row_id": t.row_id,
           "scenario": sc.id, "scenario_kind": sc.kind, "split": sc.split,
           "start_id": t.start_id, "config": t.config, "trial": t.trial, "seed": t.seed,
           "subject_seat": sc.subject, "duration_frames": sc.duration_frames,
           "commit": git["commit"], "dirty": git["dirty"], "game_version": GAME_VERSION,
           "dry_run": dry_run, "test_only": t.test_only, "forced_controllers": {},
           "decision_every": decision_every, "seed_key_id": key_id,
           "aborted": False, "abort_reason": None, "error": None}
    try:
        ctrls, forced = t.build_controllers()
        row["forced_controllers"] = forced
        row["controllers"] = {seat: C.describe(c) for seat, c in ctrls.items()}
        extra = {"scope": scope} if sc.kind == "disguise" else {}
        mon = make_monitor(sc, start, **extra)

        def hook(frame, view):
            mon.observe(frame, monitors.extract_state(view.snapshot()))

        runner = VersusRunner(episode_factory(sc, t.start_id), ctrls,
                              decision_every=decision_every, limits=limits, on_frame=hook,
                              seed_key=seed_key)
        res = runner.run(t.seed)
    except Exception as exc:  # noqa: BLE001 - a failed trial is reported, never dropped
        row.update(aborted=True, abort_reason="exception", error=f"{type(exc).__name__}: {exc}")
        row.setdefault("controllers", {})
        return row
    verdict = mon.result()
    status = res["status"]
    aborted = res["runner_terminal"] is not None
    reason = res["outcome"]["reason"]
    trace_dir = out_dir / "traces" / sc.id / t.start_id / f"{t.config}-t{t.trial}"
    paths = save_traces(res, trace_dir)
    meta = {"schema": SCHEMA_VERSION, "row_id": t.row_id, "scenario": sc.id,
            "start_id": t.start_id, "split": sc.split, "seed": t.seed, "config": t.config,
            "commit": git["commit"], "final_snapshot_sha256": res["final_snapshot_sha256"],
            "frames": res["frames"], "decision_every": decision_every}
    (trace_dir / "meta.json").write_text(json.dumps(meta, indent=1) + "\n")
    row.update(
        outcome={"status": status, "reason": reason, "frames": res["frames"],
                 "winner_seat": res["winner_seat"], "winner_slot": res["winner_slot"],
                 "result_A": _result_for(reason, "A"), "result_B": _result_for(reason, "B"),
                 "result_subject": _result_for(reason, sc.subject)},
        termination=status, aborted=aborted,
        abort_reason=res["runner_terminal"],
        success=verdict["success"], success_reason=verdict["reason"],
        metrics=verdict["metrics"],
        seats={seat: {k: s[k] for k in ("decisions", "fallbacks", "refused", "errors",
                                        "timeouts", "busy", "reset_error")}
               for seat, s in res["seats"].items()},
        invalid_inputs=res["outcome"]["invalid_inputs"],
        stale_inputs=res["outcome"]["stale_inputs"],
        replaced_inputs=res["outcome"]["replaced_inputs"],
        latency={seat: _latency(res["traces"][seat]) for seat in res["traces"]},
        final_snapshot_sha256=res["final_snapshot_sha256"],
        trace_paths={seat: str(p.relative_to(out_dir)) for seat, p in paths.items()},
        limits=res["limits"], runner=res["runner"])
    return row


def replay_dir(trace_dir: str | Path, scenarios: dict[str, Scenario]) -> dict:
    """Re-feed a two-seat trace and compare the final snapshot hash."""
    d = Path(trace_dir)
    meta = json.loads((d / "meta.json").read_text())
    sc = scenarios[meta["scenario"]]
    loaded = load_traces([d / "seat-A.jsonl", d / "seat-B.jsonl"])
    final = replay(episode_factory(sc, meta["start_id"]), loaded)
    got = digest(final)
    return {"row_id": meta["row_id"], "frames": final["frames"], "expected": loaded["final_snapshot_sha256"],
            "replayed": got, "ok": got == loaded["final_snapshot_sha256"] == meta["final_snapshot_sha256"]}


def plan_trials(scenarios: dict[str, Scenario], ids: list[str], configs: list[str], trials: int,
                seed_base: int, **kw) -> list[Trial]:
    out = []
    for sid in ids:
        sc = scenarios[sid]
        for start in sc.starts:
            for config in configs:
                for n in range(trials):
                    out.append(Trial(sc, start.id, config, n, seed_base + n,
                                     test_only=config in TEST_ONLY_CONFIGS, **kw))
    return out


def write_results(out_dir: Path, header: dict, rows: list[dict]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "results.json"
    path.write_text(json.dumps({"schema": SCHEMA_VERSION + "/results", "run": header,
                                "rows": rows}, indent=1, default=str) + "\n")
    return path


def new_run_id() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


__all__ = ["Trial", "run_trial", "replay_dir", "plan_trials", "write_results", "asdict"]
