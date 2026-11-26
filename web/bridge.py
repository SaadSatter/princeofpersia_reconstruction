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

* `human_vs_ai`: one human seat. Both key sets drive it (decision #55): WASD, F, G, T,
  left Shift and arrows, `.`, `/`, `'`, right Shift, combined as one seat's held keys;
  the other seat is driven by `rival(observation, legal_actions)`, which sees
  only its own seat. The page's default rival is the scripted baseline
  (`SeatControllerRival` around `agents/versus_baseline.make_baseline()`, made
  by `make_game`); `WebGame` itself defaults to the labelled `IdleRival`. The
  trained rival (T07) plugs in the same way: a `SeatController` in the adapter.
* `local_two_players`: both seats on one keyboard (A = WASD set, B = arrows set),
  one payload per seat, two panels. A local test mode, like `play.py ARENA --versus`: both players see
  both panels.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from pop import physics as P
from pop.versus import SEATS, TICKS_PER_SECOND, VersusEpisode, arena_episode
from pop.seats import WAIT
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


# T19, decision #55 (Saad, 2026-11-24): outside local two-player, both sets drive the
# player's own seat. Logical key name -> the physical names of both sets.
ALL_KEY_NAMES = frozenset(name for m in KEY_MAP.values() for name in m.values())
_LOGICAL = {name: logical for m in KEY_MAP.values() for logical, name in m.items()}


def to_seat_keys(seat: str, names) -> set[str]:
    """Physical key names from either set, renamed into `seat`'s own set (the online
    server uses one two-seat game, whose seats read their own names). Unknown
    names, and anything that is not text, are dropped."""
    mine = KEY_MAP[seat]
    return {mine[_LOGICAL[n]] for n in names if isinstance(n, str) and n in _LOGICAL}


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


class SeatControllerRival:
    """Adapts a `SeatController` (pop/seats.py, e.g. agents.macros.MacroController) to the hook.

    The hook is called every tick; a controller decides once per runner
    decision (T04: every 6 ticks, 0.5 s) and answers WAIT for "no input". So:
    `decide(obs, tuple(legal))` on ticks 0, every, 2*every, ...; WAIT becomes
    None; the ticks between submit nothing (as `run_versus` between decisions).
    An answer that is not a legal action string, or an exception, is replaced
    by no input and counted in `fallbacks`, and the label says so.

    One controller per game (GATE-T04-QA-5): `make_game` builds a fresh one,
    and the controller is never also used for the human seat. This bypasses
    the T04 runner (no limits, timeouts or traces in the web build)."""

    def __init__(self, controller, every: int = 6):
        if every < 1:
            raise ValueError("every must be at least 1")
        self.controller, self.every = controller, every
        self.fallbacks = 0
        self._tick = 0

    @property
    def label(self) -> str:
        name = getattr(self.controller, "name", "controller")
        kind = getattr(self.controller, "kind", "unknown")
        note = f"; {self.fallbacks} fallback(s) to no input" if self.fallbacks else \
            "; any failed answer falls back to no input"
        return f"AI rival: {name} ({kind}){note}"

    def reset(self, seed: int) -> None:
        self._tick = 0
        self.fallbacks = 0
        if hasattr(self.controller, "reset"):
            self.controller.reset(seed)

    def __call__(self, observation: dict, legal: list[str]) -> str | None:
        due = self._tick % self.every == 0
        self._tick += 1
        if not due:
            return None
        legal = tuple(legal)
        try:
            action = self.controller.decide(observation, legal)
        except Exception:                       # a failing controller must not stop the page
            self.fallbacks += 1
            return None
        if action == WAIT:
            return None
        if not isinstance(action, str) or action not in legal:
            self.fallbacks += 1
            return None
        return action


NEUTRAL_LABEL = "Rival"
RIVALS = ("baseline", "idle", "random", "ai")


def make_game(mode: str = "human_vs_ai", seat: str = "A", seed: int = 0,
              rival: str = "baseline", neutral: bool = False, honest: bool = False) -> "WebGame":
    """What the page calls (web/main.js). `rival` is ai (the shipped PPO rival, by hash; a
    wrong hash raises), baseline (default), idle or random; anything else is the baseline.
    neutral shows the label "Rival" for every kind (blind playtest sessions); it changes
    no play. honest (T22, decision #88) labels the AI kinds "AI Model (trained)" and
    "Baseline (scripted)" (agents/modes.py); "ai" is always labelled so."""
    label = None
    if rival == "random":
        r = RandomRival(seed)
    elif rival == "idle":
        r = IdleRival()
    elif rival == "ai" or (honest and rival == "baseline"):
        from agents import modes                            # shipped in game.zip
        r = modes.make_seat_rival("ai" if rival == "ai" else "baseline")
        label = r.mode_label
    else:
        from agents.versus_baseline import make_baseline    # shipped in game.zip
        r = SeatControllerRival(make_baseline())
    g = WebGame(mode=mode, seed=seed, human_seat=seat, rival=r)
    g.neutral = bool(neutral)
    g.rival_label = label
    return g


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
        self.neutral = False                   # make_game: label the rival just "Rival"
        self.rival_label: str | None = None    # make_game (T22): the honest mode label, if any

    # --- input --------------------------------------------------------------
    def press(self, keys: dict) -> dict:
        """Set the physical keys held now ({"a": True, "lshift": False, ...}).
        Returns each human seat's logical keys: {seat: {"held": [...], "shift"}}."""
        self._keys = {str(k): bool(v) for k, v in dict(keys).items()}
        return {seat: self._held(seat) for seat in self.humans}

    def _held(self, seat: str) -> dict:
        """The seat's logical keys. Human vs AI reads both sets (#55); local two-player
        keeps seat A on its set and seat B on its own."""
        maps = list(KEY_MAP.values()) if self.mode == "human_vs_ai" else [KEY_MAP[seat]]
        held = sorted({k for m in maps for k, name in m.items()
                       if k != "shift" and self._keys.get(name)})
        return {"held": held, "shift": any(self._keys.get(m["shift"]) for m in maps)}

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
        label = NEUTRAL_LABEL if self.neutral else (
            self.rival_label or getattr(self.rival, "label", "AI rival"))
        return {"mode": self.mode, "seat": self.human_seat, "rival": label, **p}
