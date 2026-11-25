"""The three ways to play, in one list (task T22, decisions #87 to #90).

    ai        "AI Model (trained)"   the shipped PPO rival, loaded by SHA-256
    baseline  "Baseline (scripted)"  agents/versus_baseline.make_baseline()
    human     "Human vs Human"       no controller: two people

Every front end (pygame `play.py`, the hosted page, the online server) reads this
list, so they offer the same modes under the same names. Standard library only
(it ships in the browser build); `pop/` never imports it.

An AI seat is driven through `SeatControllerRival` (web/bridge.py), the same hook
the hosted page and the server use: it sees only its own seat's observation and
legal tuple. `ModeRival` adds a fallback log. A failed or illegal answer, and an
inference error the policy answered with WAIT, is "no input" for that decision
and is recorded as `{"source": "fallback"}`; it is never hidden and never
replaced by the baseline. A wrong or missing weights hash is an error (decision
#3: the in-game rival is the trained policy).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class ModeError(ValueError):
    """An unknown mode id, or a mode that has no controller."""


@dataclass(frozen=True)
class Mode:
    id: str
    label: str          # shown on the menu, the HUD and the end screen (#88)
    ai: bool            # True: the other seat is a controller


MODES: tuple[Mode, ...] = (
    Mode("ai", "AI Model (trained)", True),
    Mode("baseline", "Baseline (scripted)", True),
    Mode("human", "Human vs Human", False),
)
MODE_IDS: tuple[str, ...] = tuple(m.id for m in MODES)
LABELS: dict[str, str] = {m.id: m.label for m in MODES}


def get(mode_id: str) -> Mode:
    for m in MODES:
        if m.id == mode_id:
            return m
    raise ModeError(f"unknown mode {mode_id!r}; choose one of {', '.join(MODE_IDS)}")


def label(mode_id: str) -> str:
    return get(mode_id).label


def manifest_modes() -> list[dict]:
    """The list as the build writes it into manifest.json for the two pages."""
    return [{"id": m.id, "label": m.label, "ai": m.ai} for m in MODES]


# --- controllers ------------------------------------------------------------------------
def _policy():
    from agents.rl import policy            # lazy: only the AI mode needs the weights
    return policy


def verify_shipped() -> str:
    """Check the shipped weights by hash (no inference). Raises WeightsError. Returns the hash."""
    policy = _policy()
    path = Path(policy.SHIPPED_WEIGHTS)
    if not path.is_file():
        raise policy.WeightsError(f"shipped weights are missing: {path}")
    got = policy.file_sha256(path)
    if got != policy.SHIPPED_SHA256:
        raise policy.WeightsError(
            f"weights hash mismatch: file {got}, expected {policy.SHIPPED_SHA256}")
    return got


def make_controller(mode_id: str, weights=None, sha256: str | None = None):
    """A fresh seat controller for an AI mode. The weights default to the shipped file and
    the shipped hash; a wrong hash or a missing file raises `WeightsError` (no fallback)."""
    m = get(mode_id)
    if not m.ai:
        raise ModeError(f"{m.label} has no controller: two people play")
    if m.id == "baseline":
        from agents.versus_baseline import make_baseline
        return make_baseline()
    policy = _policy()
    path = Path(weights) if weights is not None else Path(policy.SHIPPED_WEIGHTS)
    if not path.is_file():
        raise policy.WeightsError(f"weights are missing: {path}")
    return policy.make_rl_rival(path, sha256 if sha256 is not None else policy.SHIPPED_SHA256)


def _rival_class():
    from web.bridge import SeatControllerRival

    class ModeRival(SeatControllerRival):
        """SeatControllerRival plus a log of every fallback, labelled as one."""

        def __init__(self, controller, mode_id: str, every: int = 6):
            super().__init__(controller, every)
            self.mode_id = mode_id
            self.fallback_log: list[dict] = []
            self._calls = 0
            self._seen = (0, 0)

        @property
        def mode_label(self) -> str:
            return label(self.mode_id)

        @property
        def policy_errors(self) -> int:
            f = getattr(self.controller, "policy_errors", None)
            return f() if callable(f) else 0

        def reset(self, seed: int) -> None:
            super().reset(seed)
            self._calls, self._seen = 0, (0, self.policy_errors)

        def __call__(self, observation, legal):
            out = super().__call__(observation, legal)
            self._calls += 1
            now = (self.fallbacks, self.policy_errors)
            for i, reason in enumerate(("controller_failed_no_input", "policy_error")):
                for _ in range(max(0, now[i] - self._seen[i])):
                    self.fallback_log.append({"call": self._calls, "seat": "B",
                                              "source": "fallback", "reason": reason})
            self._seen = now
            return out

    return ModeRival


def make_seat_rival(mode_id: str, weights=None, sha256: str | None = None):
    """The hook `WebGame` and `play.py` call each tick: `rival(observation, legal) -> action | None`."""
    return _rival_class()(make_controller(mode_id, weights, sha256), mode_id)


def step_ai_seat(ep, rival, seat: str = "B"):
    """One tick of an AI seat on a `VersusEpisode`: it is shown its own observation and
    legal list only, and its answer (if any) is submitted like any seat's input."""
    act = rival(ep.observe(seat), ep.legal_actions(seat))
    if act is not None:
        ep.step(seat, act)
    return act
