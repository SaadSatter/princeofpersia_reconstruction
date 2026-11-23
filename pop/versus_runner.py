"""Versus runner: ticks one VersusEpisode and asks each seat's controller on a
fixed cadence (docs/final/VERSUS_RUNNER.md, task T04).

The runner is the trusted side. It owns the episode; controllers get only deep
copies of their own seat's observation and a tuple of its legal inputs. Every
answer is checked against that seat's current legal list before it reaches
`step`. A controller exception, a decision slower than `timeout_s` (measured
with the injectable `clock`, and also bounded in real time by a worker
thread), or an illegal or malformed answer is replaced by `WAIT` labelled
`source: "fallback"` and counted for that seat. One seat's fallback never
stops the other seat's cadence.

Lockstep: game frames do not advance while a controller thinks, so a slow
controller costs a fallback, not frames. A real-time server (deferred, Saad
2026-11-23) would tick on a wall clock instead; that is not this module.

Both seats are asked at the same frames, from observations taken before
either seat's answer is submitted, so seat order never matters.
"""

from __future__ import annotations

import copy
import hashlib
import json
import time
from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

from . import GAME_VERSION
from .runner import _call_with_timeout, safe_error_text
from .seats import controller_seed

SEATS = ("A", "B")                     # pop/versus.py SEATS (not imported: no edits there)
FALLBACK_ACTION = "WAIT"
DEFAULT_DECISION_EVERY = 6             # 0.5 s at 12 fps; PLAN-2026-11-23-v2, proposed
DEFAULT_TIMEOUT_S = 5.0                # task T04 / AUDIT-C, proposed
MAX_ANSWER_CHARS = 80


@dataclass
class VersusLimits:
    max_decisions: int | None = None   # per seat; the run ends when a seat would need one more
    max_fallbacks: int | None = None   # per seat; the run ends when a seat exceeds it
    timeout_s: float = DEFAULT_TIMEOUT_S
    max_frames: int | None = None      # safety cap; the duel limit comes from the episode


def digest(value) -> str:
    """Stable hash of a JSON-like value (observations, legal lists, snapshots)."""
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), default=repr)
    return hashlib.sha256(text.encode()).hexdigest()


def snapshot(episode) -> dict:
    """The complete authoritative state, for traces and replay checks only.
    VersusEpisode has no public snapshot yet (pop/versus.py is owned by T01),
    so this reads the duel's own `snapshot()`; it never goes to a controller."""
    if hasattr(episode, "snapshot"):
        return copy.deepcopy(episode.snapshot())
    return episode._duel.snapshot()        # already a deep copy


def winner(reason: str | None, seating: Mapping[str, str]) -> tuple[str | None, str | None]:
    """(winning seat, controller slot that played it) from a terminal reason."""
    if reason and reason.startswith("won:"):
        seat = reason.split(":", 1)[1]
        return seat, seating.get(seat)
    return None, None


def _answer_text(value) -> str:
    text = value if isinstance(value, str) else repr(value)
    return text if len(text) <= MAX_ANSWER_CHARS else text[:MAX_ANSWER_CHARS] + "..."


class VersusRunner:
    def __init__(self, episode_factory: Callable[[], object], controllers: Mapping[str, object],
                 decision_every: int = DEFAULT_DECISION_EVERY,
                 limits: VersusLimits | None = None, swap_seats: bool = False,
                 clock: Callable[[], float] = time.perf_counter) -> None:
        if set(controllers) != set(SEATS):
            raise ValueError("controllers must be given for exactly seats A and B")
        if decision_every < 1:
            raise ValueError("decision_every must be at least 1")
        self.episode_factory = episode_factory
        self.controllers = dict(controllers)
        self.decision_every = decision_every
        self.limits = limits or VersusLimits()
        self.swap_seats = swap_seats
        self.clock = clock
        # seat -> controller slot that plays it
        self.seating = {"A": "B", "B": "A"} if swap_seats else {"A": "A", "B": "B"}

    # --- one decision ---------------------------------------------------------
    def _decide(self, seat: str, ctrl, obs: dict, legal: tuple[str, ...], frame: int) -> dict:
        t0 = self.clock()
        value, error, _kind, late = _call_with_timeout(
            ctrl.decide, (copy.deepcopy(obs), legal), self.limits.timeout_s)
        latency_ms = round(1000 * (self.clock() - t0), 1)
        reason = None
        if late is not None or latency_ms > 1000 * self.limits.timeout_s:
            reason, error = "timeout", "timeout"
        elif error is not None:
            reason = "error"
        elif not isinstance(value, str):
            reason, error = "malformed", "answer is not a string"
        elif value not in legal:
            reason, error = "illegal", "answer is not in the seat's legal list"
        if reason is None:
            chosen, source, answer = value, "controller", None
        else:
            chosen = FALLBACK_ACTION if FALLBACK_ACTION in legal else None
            source = "fallback"
            answer = None if reason in ("timeout", "error") else _answer_text(value)
        return {"frame": frame, "seat": seat, "slot": self.seating[seat],
                "controller": ctrl.name, "kind": ctrl.kind,
                "obs_sha256": digest(obs), "legal_sha256": digest(list(legal)),
                "input": chosen, "source": source, "fallback_reason": reason,
                "answer": answer, "error": error, "latency_ms": latency_ms}

    # --- one run ----------------------------------------------------------------
    def run(self, seed: int) -> dict:
        ep = self.episode_factory()
        ep.reset(seed)
        lim = self.limits
        by_seat = {seat: self.controllers[self.seating[seat]] for seat in SEATS}
        stats = {seat: {"slot": self.seating[seat], "controller": c.name, "kind": c.kind,
                        "decisions": 0, "fallbacks": 0, "refused": 0, "errors": 0,
                        "timeouts": 0, "reset_error": None}
                 for seat, c in by_seat.items()}
        for seat, c in by_seat.items():
            if hasattr(c, "reset"):
                try:
                    c.reset(controller_seed(seed, seat))
                except Exception as exc:  # noqa: BLE001 - recorded, the seat still plays
                    stats[seat]["reset_error"] = safe_error_text(exc)
        traces: dict[str, list[dict]] = {seat: [] for seat in SEATS}
        runner_terminal = None

        while ep.outcome()["status"] == "ongoing":
            frame = ep.outcome()["frames"]
            if lim.max_frames is not None and frame >= lim.max_frames:
                runner_terminal = "max_frames"
                break
            if frame % self.decision_every == 0:
                views = {seat: (ep.observe(seat), tuple(ep.legal_actions(seat)))
                         for seat in SEATS}
                asking = [seat for seat in SEATS if views[seat][1]]
                spent = [seat for seat in asking if lim.max_decisions is not None
                         and stats[seat]["decisions"] >= lim.max_decisions]
                if spent:
                    runner_terminal = "max_decisions:" + ",".join(spent)
                    break
                records = [self._decide(seat, by_seat[seat], *views[seat], frame)
                           for seat in asking]
                for rec in records:
                    seat, s = rec["seat"], stats[rec["seat"]]
                    s["decisions"] += 1
                    if rec["source"] == "fallback":
                        s["fallbacks"] += 1
                        key = {"timeout": "timeouts", "error": "errors"}.get(
                            rec["fallback_reason"], "refused")
                        s[key] += 1
                    if rec["input"] is not None:
                        result = ep.step(seat, rec["input"])
                        if not result.get("accepted", False):    # checked above; belt and braces
                            raise RuntimeError(f"step refused a validated input: {rec}")
                    traces[seat].append(rec)
                over = [seat for seat in SEATS if lim.max_fallbacks is not None
                        and stats[seat]["fallbacks"] > lim.max_fallbacks]
                if over:
                    runner_terminal = "max_fallbacks:" + ",".join(over)
                    break
            ep.tick()

        out = ep.outcome()
        final = snapshot(ep)
        win_seat, win_slot = winner(out["reason"], self.seating)
        status = (out["reason"] if out["status"] == "terminal"
                  else f"aborted:{runner_terminal}")
        return {
            "game_version": GAME_VERSION,
            "seed": seed,
            "decision_every": self.decision_every,
            "swap_seats": self.swap_seats,
            "limits": asdict(lim),
            "seating": dict(self.seating),
            "seats": stats,
            "frames": out["frames"],
            "outcome": out,
            "runner_terminal": runner_terminal,
            "status": status,
            "winner_seat": win_seat,
            "winner_slot": win_slot,
            "final_snapshot": final,
            "final_snapshot_sha256": digest(final),
            "traces": traces,
        }


# --- traces on disk and replay ------------------------------------------------------
def save_traces(result: dict, directory: str | Path) -> dict[str, Path]:
    """One JSONL file per seat: a run header, one line per decision, an end line.
    The final snapshot itself is not written (only its hash)."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    header = {k: result[k] for k in ("game_version", "seed", "decision_every", "swap_seats",
                                     "limits", "seating")}
    end = {k: result[k] for k in ("frames", "outcome", "runner_terminal", "status",
                                  "winner_seat", "winner_slot", "final_snapshot_sha256")}
    paths = {}
    for seat in SEATS:
        path = directory / f"seat-{seat}.jsonl"
        with path.open("w") as f:
            f.write(json.dumps({"type": "run", "seat": seat, **header,
                                "controller": result["seats"][seat]}) + "\n")
            for rec in result["traces"][seat]:
                f.write(json.dumps({"type": "decision", **rec}) + "\n")
            f.write(json.dumps({"type": "end", **end}) + "\n")
        paths[seat] = path
    return paths


def load_traces(paths: Iterable[str | Path]) -> dict:
    """Read per-seat JSONL files back into what `replay` needs."""
    loaded: dict = {"traces": {}}
    for path in paths:
        lines = [json.loads(line) for line in Path(path).read_text().splitlines() if line]
        head, end = lines[0], lines[-1]
        if head.get("type") != "run" or end.get("type") != "end":
            raise ValueError(f"{path}: not a versus seat trace")
        for key in ("seed", "decision_every"):
            if key in loaded and loaded[key] != head[key]:
                raise ValueError(f"{path}: {key} differs from the other seat's trace")
            loaded[key] = head[key]
        for key in ("frames", "final_snapshot_sha256"):
            if key in loaded and loaded[key] != end[key]:
                raise ValueError(f"{path}: {key} differs from the other seat's trace")
            loaded[key] = end[key]
        loaded["traces"][head["seat"]] = [
            {k: v for k, v in rec.items() if k != "type"} for rec in lines[1:-1]]
    if set(loaded["traces"]) != set(SEATS):
        raise ValueError("need one trace per seat")
    return loaded


def replay(episode_factory: Callable[[], object], result: Mapping) -> dict:
    """Re-feed the recorded inputs (controller and fallback alike) at their
    frames and return the final authoritative snapshot."""
    ep = episode_factory()
    ep.reset(result["seed"])
    at: dict[int, list[tuple[str, str]]] = {}
    for seat in SEATS:
        for rec in result["traces"][seat]:
            if rec["input"] is not None:
                at.setdefault(rec["frame"], []).append((seat, rec["input"]))
    target = result["frames"]
    while True:
        frame = ep.outcome()["frames"]
        for seat, action in at.get(frame, []):
            if not ep.step(seat, action).get("accepted", False):
                raise ValueError(f"replay diverged: {seat} {action!r} refused at frame {frame}")
        if frame >= target or ep.outcome()["status"] != "ongoing":
            break
        ep.tick()
    return snapshot(ep)
