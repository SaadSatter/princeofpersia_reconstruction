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

A call that outlives `timeout_s` cannot be killed. Its controller is "busy"
until that call returns: the runner never calls it again meanwhile (not for
`decide`, not for `reset`) and gives its seat a `WAIT` labelled
`fallback_reason: "busy"` instead (GATE-T04-eval-2).

Isolation between the runner and a controller in the same process is by
convention (copies, no references handed out), not enforced: Python code can
reach any object through `gc` or frame introspection. A controller that is
not trusted must run in another process (docs/final/VERSUS_RUNNER.md).
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import threading
import time
from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

from . import GAME_VERSION
from .runner import safe_error_text
from .seats import controller_seed

SEATS = ("A", "B")                     # pop/versus.py SEATS (not imported: no edits there)
FALLBACK_ACTION = "WAIT"
DEFAULT_DECISION_EVERY = 6             # 0.5 s at 12 fps; PLAN-2026-11-23-v2, proposed
DEFAULT_TIMEOUT_S = 5.0                # task T04 / AUDIT-C, proposed
MAX_ANSWER_CHARS = 80
COPY_MODES = ("deepcopy", "json")      # how a controller's observation copy is made
BUSY_ERROR = "an earlier call to this controller has not returned"

# id(controller) -> its call that timed out and may still be running. Module
# level, so it holds across runner instances sharing a controller (the
# seat-swapped pair; GATE-T04-fix1-QA-F2). While the thread lives it holds the
# controller's bound method, so the id cannot be reused by another object.
_LATE: dict[int, threading.Thread] = {}
_LATE_LOCK = threading.Lock()


@dataclass
class VersusLimits:
    max_decisions: int | None = None   # per seat; the run ends when a seat would need one more
    max_fallbacks: int | None = None   # per seat; the run ends when a seat exceeds it
    timeout_s: float = DEFAULT_TIMEOUT_S
    max_frames: int | None = None      # safety cap; the duel limit comes from the episode

    def __post_init__(self) -> None:
        for name in ("max_decisions", "max_fallbacks", "max_frames"):
            value = getattr(self, name)
            if value is None:
                continue
            if type(value) is not int:             # bool is not a count
                raise TypeError(f"{name} must be an int or None, not {type(value).__name__}")
            if value < 0:
                raise ValueError(f"{name} must not be negative")
        t = self.timeout_s
        if type(t) not in (int, float):
            raise TypeError(f"timeout_s must be a number of seconds, not {type(t).__name__}")
        if not math.isfinite(t) or t <= 0:
            raise ValueError("timeout_s must be a finite number of seconds above 0")


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


def _is_str(value) -> bool:
    """True only if the value's real type is a str (or subclass). `isinstance`
    asks `value.__class__`, which an answer can spoof (GATE-T04-fix1-QA-F1)."""
    return issubclass(type(value), str)


def _plain_str(value: str) -> str:
    """An exact `str` with the same characters. A str subclass can override
    `__eq__` (passes `in legal`, GATE-T04-QA-1) or `strip` (the episode would
    play another input than the trace records, QA-2); `str.__str__` ignores
    both and returns plain text (numpy.str_ answers keep working)."""
    return str.__str__(value)


def _answer_text(value) -> str:
    """A refused answer, printable and short, for the trace. Never raises
    (a `__repr__` that raises is QA-3)."""
    try:
        if _is_str(value):
            text = _plain_str(value)
        else:
            text = repr(value)
        if type(text) is not str:
            raise TypeError
    except BaseException:  # noqa: BLE001 - controller-made object; record its type only
        text = f"<unprintable {type(value).__name__}>"
    return text if len(text) <= MAX_ANSWER_CHARS else text[:MAX_ANSWER_CHARS] + "..."


def _error_text(exc: BaseException) -> str:
    """`safe_error_text`, or the exception's type if its `__str__` raises."""
    try:
        return safe_error_text(exc)
    except BaseException:  # noqa: BLE001 - controller-made exception
        return f"{type(exc).__name__}: <unprintable>"


def _call(fn, args: tuple, timeout_s: float, threaded: bool):
    """Run one controller call. Returns (value, error, late_thread).

    Threaded (default): on a daemon worker thread, bounded by `timeout_s` of
    real time; `late_thread` is the still-running thread after a timeout.
    Inline (trusted fast path): on the runner's thread with no real-time
    bound. Any exception, BaseException included (SystemExit from a policy is
    an error, eval-4), becomes `error`; KeyboardInterrupt still stops an
    inline run, as the person at the keyboard meant."""
    if not threaded:
        try:
            return fn(*args), None, None
        except KeyboardInterrupt:
            raise
        except BaseException as exc:  # noqa: BLE001 - any controller failure is an error
            return None, _error_text(exc), None
    box: dict = {}

    def target():
        try:
            box["value"] = fn(*args)
        except BaseException as exc:  # noqa: BLE001 - any controller failure is an error
            box["error"] = _error_text(exc)

    thread = threading.Thread(target=target, daemon=True, name="versus-controller-call")
    thread.start()
    thread.join(timeout_s)
    if thread.is_alive():
        return None, "timeout", thread
    if "error" in box:
        return None, box["error"], None
    return box.get("value"), None, None


def _json_copy(value):
    return json.loads(json.dumps(value))


class EpisodeView:
    """What `on_frame` gets: read-only, copy-returning access to the episode,
    for runner-side scenario metrics. It has no `step`, `tick` or `reset`,
    and it is never handed to a controller. Trusted evaluator code only: the
    episode is reachable through the closures, as anything is in-process."""

    __slots__ = ("legal_actions", "observe", "outcome", "snapshot")

    def __init__(self, episode) -> None:
        object.__setattr__(self, "observe", lambda seat: copy.deepcopy(episode.observe(seat)))
        object.__setattr__(self, "legal_actions",
                           lambda seat: tuple(episode.legal_actions(seat)))
        object.__setattr__(self, "outcome", lambda: copy.deepcopy(episode.outcome()))
        object.__setattr__(self, "snapshot", lambda: snapshot(episode))

    def __setattr__(self, name, value):
        raise AttributeError("EpisodeView is read-only")


class VersusRunner:
    def __init__(self, episode_factory: Callable[[], object], controllers: Mapping[str, object],
                 decision_every: int = DEFAULT_DECISION_EVERY,
                 limits: VersusLimits | None = None, swap_seats: bool = False,
                 clock: Callable[[], float] = time.perf_counter, *,
                 on_frame: Callable[[int, EpisodeView], None] | None = None,
                 copy_mode: str = "deepcopy", threaded: bool = True,
                 seed_key: bytes | None = None) -> None:
        """`on_frame(frame, view)`, if given, is called after every tick with
        the number of frames played and an `EpisodeView`; it is runner-side
        only. `copy_mode="json"` and `threaded=False` are the trusted fast
        path for training (cheaper copies, no worker thread, so no real-time
        bound on a call). `seed_key` keys `controller_seed`; it is never
        recorded in the result or the traces."""
        if set(controllers) != set(SEATS):
            raise ValueError("controllers must be given for exactly seats A and B")
        if type(decision_every) is not int:        # bool and floats are not a cadence
            raise TypeError(
                f"decision_every must be an int, not {type(decision_every).__name__}")
        if decision_every < 1:
            raise ValueError("decision_every must be at least 1")
        if copy_mode not in COPY_MODES:
            raise ValueError(f"copy_mode must be one of {COPY_MODES}")
        self.on_frame = on_frame
        self.copy_mode = copy_mode
        self.threaded = bool(threaded)
        self._copy = copy.deepcopy if copy_mode == "deepcopy" else _json_copy
        self._seed_key = seed_key
        self.episode_factory = episode_factory
        self.controllers = dict(controllers)
        self.decision_every = decision_every
        self.limits = limits or VersusLimits()
        self.swap_seats = swap_seats
        self.clock = clock
        # seat -> controller slot that plays it
        self.seating = {"A": "B", "B": "A"} if swap_seats else {"A": "A", "B": "B"}

    # --- one call to a controller ------------------------------------------------
    def _busy(self, ctrl) -> bool:
        with _LATE_LOCK:
            late = _LATE.get(id(ctrl))
            if late is not None and not late.is_alive():
                del _LATE[id(ctrl)]
                late = None
            return late is not None

    def _call(self, ctrl, fn, args: tuple):
        """(value, error, busy). A busy controller is not called at all."""
        if self._busy(ctrl):
            return None, BUSY_ERROR, True
        value, error, late = _call(fn, args, self.limits.timeout_s, self.threaded)
        if late is not None:
            with _LATE_LOCK:
                _LATE[id(ctrl)] = late
        return value, error, False

    # --- one decision ---------------------------------------------------------
    def _decide(self, seat: str, ctrl, obs: dict, legal: tuple[str, ...], frame: int) -> dict:
        t0 = self.clock()
        value, error, busy = self._call(ctrl, ctrl.decide, (self._copy(obs), legal))
        latency_ms = round(1000 * (self.clock() - t0), 1)
        reason = None
        if busy:
            reason = "busy"
        elif error == "timeout" or latency_ms > 1000 * self.limits.timeout_s:
            reason, error = "timeout", "timeout"
        elif error is not None:
            reason = "error"
        else:
            # Normalise inside a guard: any failure is a malformed answer, never
            # a crash of the run (eval-1, QA-F1).
            try:
                text = _plain_str(value) if _is_str(value) else None
            except BaseException:  # noqa: BLE001 - controller-made object
                text = None
            if text is None:
                reason, error = "malformed", "answer is not a string"
            elif text not in legal:
                reason, error = "illegal", "answer is not in the seat's legal list"
        if reason is None:
            chosen, source, answer = text, "controller", None
        else:
            chosen = FALLBACK_ACTION if FALLBACK_ACTION in legal else None
            source = "fallback"
            answer = (None if reason in ("timeout", "error", "busy")
                      else _answer_text(value))
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
                        "timeouts": 0, "busy": 0, "reset_error": None}
                 for seat, c in by_seat.items()}
        for seat, c in by_seat.items():
            if hasattr(c, "reset"):
                # Bounded like decide (QA-4 / eval-3). A failed, slow or busy
                # reset is recorded and the seat still plays (busy until it returns).
                _, error, busy = self._call(
                    c, c.reset, (controller_seed(seed, seat, self._seed_key),))
                stats[seat]["reset_error"] = "busy" if busy else error
        traces: dict[str, list[dict]] = {seat: [] for seat in SEATS}
        runner_terminal = None
        view = None

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
                        key = {"timeout": "timeouts", "error": "errors",
                               "busy": "busy"}.get(rec["fallback_reason"], "refused")
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
            if self.on_frame is not None:
                if view is None:
                    view = EpisodeView(ep)
                self.on_frame(ep.outcome()["frames"], view)

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
            "runner": {"copy_mode": self.copy_mode, "threaded": self.threaded},
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
                                     "limits", "runner", "seating") if k in result}
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
