"""The browser build's game loop (T14). Runs under CPython and Pyodide; standard library only.

The page (web/main.js) holds no game logic. Each tick it hands this module
the physical keys held down, calls `tick()`, and draws the returned payload:

    {"mode", "seat", "rival", "seat_view": observe(seat), "draw": [...],
     "hud": {...}, "outcome": {"status", "reason", "result"}}

`seat_view` is the human seat's observation (pop/versus.py `observe`), and
`draw` and `hud` are computed from it alone (render/draw_list.py). The other
seat's observation, the seed and the `Duel` are never in a payload
(tests/test_web_bridge.py). Limitation, stated in docs/final/WEB_BUILD.md:
on a static page the engine itself runs in the browser, so a player with
devtools can read the whole state. That is acceptable for human vs AI and
for local play, not for online human vs human (which needs a server).

Modes:

* `human_vs_ai`: one human seat, keys as in `play.py --versus` for that seat;
  the other seat is driven by `rival(observation, legal_actions)`, which sees
  only its own seat. Until the trained rival lands (T05/T07) the default is
  a clearly labelled placeholder (`IdleRival`).
* `local_two_players`: both seats on one keyboard, one payload per seat, two
  panels. A local test mode, like `play.py ARENA --versus`: both players see
  both panels.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from pop import physics as P
from pop.versus import SEATS, TICKS_PER_SECOND, VersusEpisode, arena_episode
from render import draw_list

MODES = ("human_vs_ai", "local_two_players")
LOCAL_LABEL = ("Local test mode: both players share one keyboard and see both panels. "
               "Not the online game.")

# play.py VERSUS_KEYS (tests/test_web_bridge.py keeps them equal): physical key
# names per seat, spelled as play.py spells them.
KEY_MAP = {
    "A": {"left": "a", "right": "d", "up": "w", "down": "s", "attack": "f", "draw": "g",
          "take": "t", "shift": "lshift"},
    "B": {"left": "left", "right": "right", "up": "up", "down": "down", "attack": ".",
          "draw": "/", "take": "'", "shift": "rshift"},
}


def running_dir(me: dict) -> str | None:
    """play.py running_dir: "left"/"right" while this seat's own rival is mid-run."""
    m = me.get("motion")
    if m and m["effect"] == "moved" and m["frames"] == P.RUN:
        return me["facing"]
    return None


def seat_input(held: set[str], shift: bool, armed: bool = False,
               running: str | None = None) -> str | None:
    """play.py versus_input: the action a held key set asks for this frame."""
    if "take" in held:
        return "TAKE"
    if "draw" in held:
        return "SHEATHE" if armed else "DRAW"
    if "attack" in held:
        if "up" in held:
            return "THROW"
        if "down" in held:
            return "SWEEP"
        return "LUNGE"
    horiz = next((d for d in ("left", "right") if d in held), None)
    if horiz and "up" in held:
        run_jump = shift or running == horiz
        return f"RUN_JUMP_{horiz.upper()}" if run_jump else f"JUMP_{horiz.upper()}"
    if horiz:
        return f"STEP_{horiz.upper()}" if shift else horiz.upper()
    if "up" in held:
        return "STANCE_UP" if armed else "UP"
    if "down" in held:
        return "STANCE_DOWN" if armed else "DOWN"
    return None


# --- the other seat in human_vs_ai -----------------------------------------------
class IdleRival:
    """Placeholder: never submits an input. Replaced by the trained rival (T05/T07)."""
    label = "Placeholder rival (idle): stands still. Not the AI rival."

    def reset(self, seed: int) -> None:
        pass

    def __call__(self, observation: dict, legal: list[str]) -> str | None:
        return None


class RandomRival:
    """Placeholder: a random legal input about twice a second, from its own RNG."""
    label = "Placeholder rival (random legal inputs). Not the AI rival."

    def __init__(self, seed: int = 0):
        self.reset(seed)

    def reset(self, seed: int) -> None:
        self.rng = random.Random(seed)

    def __call__(self, observation: dict, legal: list[str]) -> str | None:
        if not legal or self.rng.random() > 2 / TICKS_PER_SECOND:
            return None
        return self.rng.choice(sorted(legal))


# --- art sizes ----------------------------------------------------------------------
_ART: dict | None = None


def load_art() -> dict:
    """web/art.json when packed by tools/web/build.py, else measured from
    assets/generated/ (CPython in the repository)."""
    global _ART
    if _ART is None:
        packed = Path(__file__).with_name("art.json")
        if packed.is_file():
            _ART = json.loads(packed.read_text())
        else:
            from render import genart, webart
            _ART = json.loads(json.dumps(webart.art_meta(genart.PACK_DIR)))
    return _ART


class WebGame:
    def __init__(self, mode: str = "human_vs_ai", seed: int = 0, human_seat: str = "A",
                 rival=None, art: dict | None = None, episode: VersusEpisode | None = None):
        """episode: a prepared VersusEpisode (tests); default the arena duel.
        rival: callable(observation, legal_actions) -> action or None."""
        if mode not in MODES:
            raise ValueError(f"unknown mode {mode!r}")
        if human_seat not in SEATS:
            raise ValueError(f"unknown seat {human_seat!r}")
        self.mode = mode
        self.seed = seed
        self.human_seat = human_seat
        self.ai_seat = next(s for s in SEATS if s != human_seat)
        self.rival = rival if rival is not None else IdleRival()
        self.art = art if art is not None else load_art()
        self.episode = episode if episode is not None else arena_episode(seed)
        self.humans = SEATS if mode == "local_two_players" else (human_seat,)
        self._keys: dict[str, bool] = {}
        self._caches = {seat: {} for seat in SEATS}
        self.display_tick = 0

    # --- input --------------------------------------------------------------
    def press(self, keys: dict) -> dict:
        """Set the physical keys held now ({"a": True, "lshift": False, ...}).
        Returns each human seat's logical keys: {seat: {"held": [...], "shift"}}."""
        self._keys = {str(k): bool(v) for k, v in dict(keys).items()}
        return {seat: self._held(seat) for seat in self.humans}

    def _held(self, seat: str) -> dict:
        m = KEY_MAP[seat]
        held = sorted(k for k, name in m.items() if k != "shift" and self._keys.get(name))
        return {"held": held, "shift": bool(self._keys.get(m["shift"]))}

    def rematch(self) -> None:
        """R: the same duel again from the same seed (play.py --versus)."""
        self.episode.reset(self.seed)
        if hasattr(self.rival, "reset"):
            self.rival.reset(self.seed)
        self._caches = {seat: {} for seat in SEATS}
        self.display_tick = 0

    # --- one frame ----------------------------------------------------------
    def tick(self) -> dict:
        ep = self.episode
        for seat in SEATS:                           # A then B, as play.py
            if seat in self.humans:
                k = self._held(seat)
                legal = ep.legal_actions(seat)
                me = ep.observe(seat)["me"]
                act = seat_input(set(k["held"]), k["shift"], armed=me["armed"],
                                 running=running_dir(me))
                if act == "LUNGE" and "KICK" in legal:
                    act = "KICK"                     # attack in the air: dive kick
                if act and act in legal:
                    ep.step(seat, act)
            else:
                act = self.rival(ep.observe(seat), ep.legal_actions(seat))
                if act is not None:
                    ep.step(seat, act)               # refused input is counted (runner rules)
        ep.tick()
        self.display_tick += 1
        return self.payload()

    def tick_json(self) -> str:
        return json.dumps(self.tick(), separators=(",", ":"))

    # --- what the page receives ---------------------------------------------
    def _seat_payload(self, seat: str) -> dict:
        other = next(s for s in SEATS if s != seat)
        obs = self.episode.observe(seat)
        p = draw_list.seat_payload(obs, draw_list.COLOURS[seat], draw_list.COLOURS[other],
                                   self.display_tick, self.art, self._caches[seat])
        p["outcome"] = self._outcome(seat)
        return p

    def _outcome(self, seat: str) -> dict:
        o = self.episode.outcome()             # only status and reason leave the bridge
        reason = o["reason"]
        result = None
        if reason is not None:
            result = "draw" if reason.startswith("draw") else (
                "won" if reason == f"won:{seat}" else "lost")
        return {"status": o["status"], "reason": reason, "result": result}

    def payload(self) -> dict:
        if self.mode == "local_two_players":
            seats = {seat: self._seat_payload(seat) for seat in SEATS}
            return {"mode": self.mode, "label": LOCAL_LABEL, "seats": seats,
                    "outcome": {k: v for k, v in seats["A"]["outcome"].items() if k != "result"}}
        p = self._seat_payload(self.human_seat)
        return {"mode": self.mode, "seat": self.human_seat,
                "rival": getattr(self.rival, "label", "AI rival"), **p}
