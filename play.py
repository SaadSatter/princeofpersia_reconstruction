"""Pygame frontend: play, watch an agent, or replay a trace.

Working directory: the project folder.

    uv sync --extra play
    uv run python play.py                         # the three-mode menu (agents/modes.py)
    uv run python play.py --classic               # the old single-prince level (S3)
    uv run python play.py S3                      # play with the keyboard (bundled original art)
    uv run python play.py S3 --art generated      # Shadow Masque's own dungeon art
    uv run python play.py S3 --placeholder        # placeholder shapes instead
    uv run python play.py ARENA --art generated   # walk the six-room arena (pop/arena.py)
    uv run python play.py ARENA --versus          # two rivals, two panels, one keyboard (testing)
    uv run python play.py S1 --watch baseline     # watch the baseline play
    uv run python play.py S1 --watch model-history --live   # watch the model (paid calls)
    uv run python play.py --replay traces/eval/20261026T060347Z-baseline-S3-100.jsonl
    uv run python play.py L1                      # original Level 1 (after tools/fetch_level1.py)

Keys: Left/Right run (or turn), Shift+Left/Right careful step, Up climb /
exit, Down crouch / hang / drop / drink, Up+Left/Right jump,
Shift+Up+Left/Right running jump, Space wait, R restart, Esc quit.

Every mode goes through the same five operations and the same engine
(R-D07). Each step is shown as one clip of the step's frames at 12 frames/s
(R-D26). Watch mode runs the real episode runner (pop/runner.py) and shows
each submitted action with its source; fallback moves are labeled
"fallback", never as the player's own.
"""

from __future__ import annotations

import argparse
import json
import queue
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from agents import modes
from pop import levels
from pop.interface import PLAYER_ID, SITUATION_DEFAULT, Episode
from pop.situations import SITUATIONS
from render import anim

FPS = 12
TUNING_SITUATIONS = {"S1", "S2", "S3"}


# --- keys (pure) ------------------------------------------------------------
def action_for(key: str, held: set[str], shift: bool) -> str | None:
    """Map one key press to an action. `key` and `held` use the names
    left/right/up/down/space; `held` is what else is held down."""
    if key in ("left", "right"):
        d = key.upper()
        if "up" in held:
            return f"RUN_JUMP_{d}" if shift else f"JUMP_{d}"
        return f"STEP_{d}" if shift else d
    if key == "up":
        for d in ("left", "right"):
            if d in held:
                return f"RUN_JUMP_{d.upper()}" if shift else f"JUMP_{d.upper()}"
        return "UP"
    if key == "down":
        return "DOWN"
    if key == "space":
        return "WAIT"
    return None


def held_repeat(held: set[str], shift: bool) -> str | None:
    """Holding a direction keeps running (or stepping), as in the original."""
    if "up" in held:
        return None
    for d in ("left", "right"):
        if d in held:
            return f"STEP_{d.upper()}" if shift else d.upper()
    return None


# --- versus keys (pure) -----------------------------------------------------
# Local testing only: both rivals on one keyboard, each panel drawing only its
# own seat's observation. Real play is one player per screen (online, GDD).
VERSUS_KEYS = {
    "A": {"left": "a", "right": "d", "up": "w", "down": "s", "attack": "f", "draw": "g",
          "take": "t", "shift": "lshift"},
    "B": {"left": "left", "right": "right", "up": "up", "down": "down", "attack": ".",
          "draw": "/", "take": "'", "shift": "rshift"},
}


def running_dir(me: dict) -> str | None:
    """"left"/"right" while this seat's own rival is mid-run (a run's motion in
    its own observation), else None. A careful step is not a run."""
    from pop import physics as P
    m = me.get("motion")
    if m and m["effect"] == "moved" and m["frames"] == P.RUN:
        return me["facing"]
    return None


def versus_input(held: set[str], shift: bool, armed: bool = False,
                 running: str | None = None) -> str | None:
    """The action a held key set asks for this frame (left/right/up/down/attack/draw).
    Re-sent every frame while held; the duel starts it when the rival is free.
    Swordplay keys (VERSUS_SPEC 2.3): attack = lunge, with Up a throw, with Down
    a sweep (and in the air a dive kick, chosen by the caller when KICK is legal);
    while the sword is drawn, Up/Down change stance. Up + direction out of a run
    in that direction (`running`, see running_dir) is a running jump, as in the
    original game; from a standstill it is a standing jump unless Shift is held.
    Every directional jump is a flip (Saad #53, 2026-11-24, R-V22). A direction and
    a jump pressed within 2 ticks of each other need nothing here: the engine joins
    them into one flip (R-V35, `Duel._grace_jump`), the same for every front end.
    This local test mode keeps seat A on the WASD set and seat B on the arrows (#55);
    the hosted page and the online game accept either set for the player's own seat."""
    if "take" in held:
        return "TAKE"                                     # a downed guard's uniform (R-V17)
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


def menu_entries() -> list[tuple[str, str]]:
    """(mode id, label) for the start menu: the shared list of agents/modes.py."""
    return [(m.id, m.label) for m in modes.MODES]


def ai_key_names() -> dict:
    """pygame key code -> ("A", logical key) for both key sets: against an AI the human's own
    seat accepts WASD and the arrows alike (decision #89, reading #55)."""
    import pygame
    return {pygame.key.key_code(v): ("A", k) for m in VERSUS_KEYS.values()
            for k, v in m.items() if k != "shift"}


def new_recorder(args, ep, seats=None, kind="human"):
    """T20: the local test's playtest logs (docs/final/playtest/TELEMETRY.md). One file
    per human seat, room "LOCAL"; the same recorder the online server uses. Against an AI
    (T22 modes) `seats` is just ("A",) and `kind` the mode id: the AI seat gets no log, and
    its observation, inputs and fallbacks never reach one (T22-fix2)."""
    from pop.versus import SEATS
    from server.telemetry import Telemetry
    args._rec_seats, args._rec_kind = tuple(seats or SEATS), kind
    mode = "play.py --versus" if kind == "human" else f"play.py --mode {kind}"
    args._telemetry = Telemetry(args.telemetry_dir, "LOCAL",
                                info={"build": "local", "mode": mode})
    return args._telemetry.new_duel(ep, args._rec_seats, kind, time.monotonic())


def restart_recorder(args, ep, rec):
    """R: the same duel again. The old logs close (abandoned if it had not ended)."""
    if rec is not None:
        rec.close(time.monotonic(), "restart" if rec.ended else "abandoned")
    ep.reset(args.seed)
    return args._telemetry.new_duel(ep, args._rec_seats, args._rec_kind, time.monotonic())


def record_tick(rec, ep, logged_before: int) -> None:
    """After `ep.tick()`: log this frame's accepted inputs and any result."""
    from server.telemetry import seat_outcome
    now = time.monotonic()
    rec.after_tick([(seat, act) for _, seat, act in ep.log[logged_before:]], now)
    out = ep.outcome()
    if out["status"] == "terminal":
        rec.end({s: seat_outcome(out["reason"], s) for s in rec.seats}, now)


def versus_main(args, rival=None) -> int:
    """Two seats on real-time ticks (pop/versus.py), one panel per seat. With `rival` (T22:
    an AI mode, agents/modes.py) seat A is the human on either key set, seat B is the rival
    (it sees only its own observation) and there is one panel: the human's."""
    import os
    if args.screenshot:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame
    from pop.versus import SEATS, arena_episode
    from render import draw, versus_view

    ep = arena_episode(args.seed)
    if rival is not None:
        rival.reset(args.seed)
    shown_seats = ("A",) if rival is not None else SEATS
    # T20: off unless --playtest. Against an AI only the human seat is logged (T22-fix2).
    rec = (new_recorder(args, ep, shown_seats, getattr(args, "mode", None) or "human")
           if args.playtest else None)
    pygame.init()
    scale = max(1, args.scale)
    gap = 4 * scale
    panel_w, panel_h = draw.SCREEN_W * scale, draw.SCREEN_H * scale
    info_h = 22 * scale // 3
    n_panels = len(shown_seats)
    window = pygame.display.set_mode((n_panels * panel_w + (n_panels - 1) * gap, panel_h + info_h))
    pygame.display.set_caption("Shadow Masque: " + (
        f"you vs {rival.mode_label}" if rival is not None else "local versus test"))
    # Shadow Masque's own art by default: the versus game never uses the original images.
    art = "placeholder" if args.placeholder else (args.art or "generated")
    renderer = draw.Renderer(original=art == "original", art=art)
    colours = {"A": "indigo", "B": "crimson"}
    other = {"A": "B", "B": "A"}
    font = pygame.font.Font(None, 9 * scale)
    clock = pygame.time.Clock()
    caches = {seat: {} for seat in SEATS}
    scripted = [k for k in args.keys.split(",") if k]       # "A:RIGHT" tokens, one per frame
    frames_left = None if not args.screenshot else max(60, 2 * len(scripted) + 40)
    tick = 0
    names = ai_key_names() if rival is not None else {
        pygame.key.key_code(v): (seat, k) for seat, m in VERSUS_KEYS.items()
        for k, v in m.items() if k != "shift"}

    counts = ({k: v["n"] for k, v in renderer.dungeon.meta["rival"].items()}
              if renderer.dungeon else {})
    guard_counts = ({k: v["n"] for k, v in renderer.dungeon.meta["guard"].items()}
                    if renderer.dungeon else {})

    def draw_guard(s, view, room="", cache=None, key=None):
        """Anything observed as a guard: guard looks from guard_sprite; any other
        move (run, jump, climb, hang) with the rival's clips on the guard strips."""
        if renderer.dungeon:
            spr = versus_view.guard_sprite(view, guard_counts)
            if spr is None:
                p = versus_view.pose(view, room, cache, key)
                renderer.dungeon.draw_kid(s, p, who="guard")
                return
            renderer.dungeon.blit_actor(s, "guard", spr.strip, spr.index, spr.x, spr.y, spr.facing)
        else:
            from render.anim import stand_point
            x, y = stand_point(view["row"], view["col"])
            pygame.draw.rect(s, (90, 110, 70), (x - 4, y - 30, 9, 30))

    def draw_actor(s, view, room, seat_colour, cache_key, cache):
        spr = versus_view.sprite(view, counts) if renderer.dungeon else None
        if spr is not None:
            renderer.dungeon.blit_actor(s, "rival", spr.strip, spr.index, spr.x, spr.y,
                                        spr.facing, seat_colour)
            return
        p = versus_view.pose(view, room, cache, cache_key)
        if renderer.dungeon:
            renderer.dungeon.draw_kid(s, p, seat_colour)
        else:
            renderer.draw_kid(s, p)

    def draw_meter(s, entry):
        """A guard's suspicion of this seat (R-V19): an eye and a bar above its head,
        amber below 70, red above. Only the suspected seat has these entries."""
        from render.anim import stand_point
        x, y = (round(v) for v in stand_point(entry["row"], entry["col"]))
        y -= 36
        col = (230, 170, 40) if entry["level"] < 70 else (220, 50, 40)
        pygame.draw.rect(s, (14, 15, 20), (x - 9, y - 1, 18, 5))
        pygame.draw.rect(s, (60, 60, 70), (x - 8, y, 16, 3))
        pygame.draw.rect(s, col, (x - 8, y, round(16 * entry["level"] / 100), 3))
        for dx, dy in ((-2, -4), (-1, -5), (0, -5), (1, -5), (2, -4), (-1, -3), (0, -3), (1, -3)):
            s.set_at((x + dx, y + dy), (235, 230, 215))
        s.set_at((x, y - 4), (14, 15, 20))

    def draw_swords(s, swords):
        """Dropped swords lie on the floor; a thrown one flies at chest height."""
        from render.anim import stand_point
        for sw in swords:
            x, y = stand_point(sw["row"], sw["col"])
            y = y - 18 if sw["flying"] else y - 1
            pygame.draw.line(s, (220, 231, 236), (x - 7, y), (x + 6, y))
            pygame.draw.line(s, (69, 78, 106), (x - 8, y - 1), (x - 8, y + 1))

    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                running = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_r:
                if args.playtest:
                    rec = restart_recorder(args, ep, rec)
                else:
                    ep.reset(args.seed)
                if rival is not None:
                    rival.reset(args.seed)             # one press restarts against an AI (#41)
        pressed = pygame.key.get_pressed()
        mods = pygame.key.get_mods()
        logged_before = len(ep.log)
        for seat in shown_seats:
            held = {k for code, (s_, k) in names.items() if s_ == seat and pressed[code]}
            shift = bool(mods & (pygame.KMOD_SHIFT if rival is not None else
                                 pygame.KMOD_LSHIFT if seat == "A" else pygame.KMOD_RSHIFT))
            legal = ep.legal_actions(seat)
            mine = ep.observe(seat)["me"]
            act = versus_input(held, shift, armed=mine["armed"], running=running_dir(mine))
            if act == "LUNGE" and "KICK" in legal:
                act = "KICK"                                  # attack in the air: dive kick
            if act and act in legal:
                ep.step(seat, act)
            else:
                if act and rec is not None:
                    rec.refused(seat, act)
                ep.release(seat)                              # T23 (#93): same call as the hosted page
        if scripted:
            seat, _, act = scripted.pop(0).partition(":")
            ep.step(seat, act)
        if rival is not None:
            modes.step_ai_seat(ep, rival)              # its own observation and legal list only
        ep.tick()
        if rec is not None:
            record_tick(rec, ep, logged_before)

        window.fill((0, 0, 0))
        for i, seat in enumerate(shown_seats):
            obs = ep.observe(seat)
            panel = pygame.Surface((draw.SCREEN_W, draw.SCREEN_H))
            renderer.draw_room(panel, obs, tick)
            draw_swords(panel, obs["swords"])
            for j, fig in enumerate(obs["figures"]):
                if fig["kind"] == "rival":
                    draw_actor(panel, fig, obs["room"], colours[other[seat]], ("fig", j), caches[seat])
                else:
                    draw_guard(panel, fig, obs["room"], caches[seat], ("guard", j))
            if obs["me"]["disguised"]:
                draw_guard(panel, obs["me"], obs["room"], caches[seat], "me")   # in uniform (R-V18)
            else:
                draw_actor(panel, obs["me"], obs["room"], colours[seat], "me", caches[seat])
            for entry in obs["suspicion"]:
                draw_meter(panel, entry)
            renderer.draw_hud(panel, obs)
            x = i * (panel_w + gap)
            window.blit(pygame.transform.scale(panel, (panel_w, panel_h)), (x, 0))
            label = (f"rival {seat} ({colours[seat]})  hearts {obs['me']['hp']}"
                     + ("  DISGUISED" if obs["me"]["disguised"] else ""))
            if rival is not None:
                label = f"you (A) vs {rival.mode_label}   hearts {obs['me']['hp']}" + (
                    "  DISGUISED" if obs["me"]["disguised"] else "")
            window.blit(font.render(label, True, (200, 200, 200)), (x + 6, panel_h + 2))
        out = ep.outcome()
        if out["status"] == "terminal":
            vs = f" vs {rival.mode_label}" if rival is not None else ""
            msg = font.render(f"{out['reason']}{vs}   R to restart, Esc to quit", True, (240, 220, 120))
            window.blit(msg, (panel_w - msg.get_width() // 2, panel_h + 2))
        pygame.display.flip()
        tick += 1
        if frames_left is not None:
            frames_left -= 1
            if frames_left <= 0:
                pygame.image.save(window, args.screenshot)
                break
            continue
        clock.tick(FPS * args.speed)
    if rec is not None:
        rec.close(time.monotonic())
    pygame.quit()
    if rival is not None and rival.fallback_log:
        print(f"AI seat B: {len(rival.fallback_log)} fallback(s) to no input (source: fallback)")
    return 0


def mode_main(ap, args) -> int:
    """`--mode ai|baseline|human` and `--menu` (T22, decisions #87 to #89). The mode list is
    agents/modes.py; the menu is render/menu.py. AI modes play the ARENA against that
    controller; human is the local two-player game (`--versus`)."""
    if args.watch or args.replay:
        ap.error("--mode and --menu play the ARENA: not with --watch or --replay")
    try:
        import pygame
    except ImportError:
        print("pygame is not installed. Run: uv sync --extra play", file=sys.stderr)
        return 2
    import os
    if args.screenshot or args.menu_keys:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    args.situation = "ARENA"
    if args.menu:
        from render import draw, menu
        pygame.init()
        scale = max(1, args.scale)
        window = pygame.display.set_mode((draw.SCREEN_W * scale, draw.SCREEN_H * scale))
        pygame.display.set_caption("Shadow Masque")
        scripted = [k for k in args.menu_keys.split(",") if k] if args.menu_keys else None
        args.mode = menu.run_menu(window, scale, menu_entries(), scripted)
        pygame.quit()
        if args.mode is None:
            return 0
    rival = None
    if modes.get(args.mode).ai:
        from agents.rl.policy import WeightsError
        try:
            rival = modes.make_seat_rival(args.mode)     # by hash; a wrong file is an error
        except WeightsError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    return versus_main(args, rival)


# --- driving the episode (pure) ----------------------------------------------
@dataclass
class Shown:
    """One step as the frontend shows it."""
    action: str
    accepted: bool
    poses: list
    before: dict
    after: dict
    source: str = "human"
    error: str | None = None
    mismatch: str | None = None


@dataclass
class Driver:
    """Holds the Episode for the frontend and turns steps into clips."""
    situation: str
    seed: int = 0
    max_actions: object = None
    ep: Episode = field(init=False)
    obs: dict = field(init=False)
    anim_state: anim.AnimState = field(init=False)

    def __post_init__(self):
        self.ep = Episode(self.situation, max_actions=self.max_actions)
        self.reset()

    def reset(self) -> None:
        self.obs = self.ep.reset(self.seed)
        self.anim_state = anim.AnimState()

    def intro(self) -> Shown | None:
        """The entry the player watched before control began (Level 1 drop, R-D29),
        rebuilt from the first observation's last_result."""
        res = self.obs.get("last_result")
        if not res or not res.get("frames"):
            return None
        after = self.obs["kid"]
        before = dict(after, row=after["row"] - res["fell_rows"], posture="falling")
        # All of the entry's frames show the drop (stepfall); the landing is
        # the idle pose that follows. Display only.
        p0 = anim.stand_point(before["row"], before["col"])
        p1 = anim.stand_point(after["row"], after["col"])
        f = 1 if after["facing"] == "right" else -1
        n = res["frames"]
        poses = [anim.Pose(fr, *anim.lerp(p0, p1, ((i + 1) / n) ** 2), f, "fall")
                 for i, fr in enumerate(anim.resample(anim.FALL, n))]
        return Shown("enter", True, poses, self.obs, self.obs, "game")

    def legal(self) -> list[str]:
        return self.ep.legal_actions(PLAYER_ID)

    def outcome(self) -> dict:
        return self.ep.outcome()

    def apply(self, action: str, source: str = "human") -> Shown:
        before = self.obs
        res = self.ep.step(PLAYER_ID, action)
        after = res["observation"]
        self.obs = after
        if not res["accepted"]:
            pose = anim.idle_pose(before["kid"])
            return Shown(action, False, [pose], before, after, source, res["error"])
        out = self.ep.outcome()
        step = anim.Step(action=res["action"], before=before["kid"], after=after["kid"],
                         before_room=before["room"], after_room=after["room"],
                         effect=res["effect"], frames=res["frames"],
                         fell_rows=res["fell_rows"],
                         terminal=out["reason"] if out["status"] == "terminal" else None)
        return Shown(res["action"], True, anim.clip(step, self.anim_state), before, after, source)

    def idle(self) -> anim.Pose:
        out = self.ep.outcome()
        fell = (self.obs["last_result"] or {}).get("fell_rows", 0)
        return anim.idle_pose(self.obs["kid"], out["reason"], fell)


# --- replay (pure) -----------------------------------------------------------
def load_trace(path: str | Path) -> tuple[dict, list[dict]]:
    header, steps = None, []
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("type") == "episode":
            header = rec
        elif rec.get("type") == "step":
            steps.append(rec)
    if header is None:
        raise ValueError(f"{path}: no episode header")
    return header, steps


def replay_driver(header: dict) -> Driver:
    limits = header.get("limits") or {}
    return Driver(header["situation"], header["seed"],
                  max_actions=limits.get("max_actions", SITUATION_DEFAULT))


def check_step(shown: Shown, rec: dict) -> str | None:
    """None if the engine reproduced the recorded step, else what differs."""
    if shown.accepted != rec["accepted"]:
        return f"step {rec['i']}: accepted {shown.accepted}, trace says {rec['accepted']}"
    if rec.get("kid") is not None and shown.after["kid"] != rec["kid"]:
        return f"step {rec['i']}: kid {shown.after['kid']}, trace says {rec['kid']}"
    if rec.get("room") is not None and shown.after["room"] != rec["room"]:
        return f"step {rec['i']}: room differs from the trace"
    return None


# --- watch (pure) ------------------------------------------------------------
class WatchedPlayer:
    """Wraps a player for the runner and reports each submitted step.

    The runner calls `commit` after every step with what was actually
    submitted (pop/runner.py), so fallbacks arrive labeled as fallbacks."""

    def __init__(self, inner, out: queue.Queue):
        self.inner = inner
        self.out = out
        self.name = inner.name
        self.source = inner.source
        self.uses_model = inner.uses_model

    def decide(self, observation, legal_actions):
        return self.inner.decide(observation, legal_actions)

    def commit(self, observation, action, source, error):
        if hasattr(self.inner, "commit"):
            self.inner.commit(observation, action, source, error)
        self.out.put({"action": action, "source": source, "error": error})


def start_watch(kind: str, situation: str, seed: int, provider: str, model: str | None,
                out: queue.Queue) -> threading.Thread:
    from evaluate import make_player
    from pop.runner import run_episode

    player = WatchedPlayer(make_player(kind, provider, model), out)

    def run():
        try:
            result = run_episode(player, situation, seed)
            out.put({"done": result})
        except Exception as exc:  # noqa: BLE001 - shown in the window, not swallowed
            out.put({"crashed": f"{type(exc).__name__}: {exc}"})

    t = threading.Thread(target=run, daemon=True)
    t.start()
    return t


# --- window ------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("situation", nargs="?", default=None,
                    choices=sorted(SITUATIONS) + list(levels.EXHIBITION_IDS),
                    help="a single-player situation (default S3); with no situation and no flag "
                         "the three-mode menu opens")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--placeholder", action="store_true", help="draw placeholder shapes")
    ap.add_argument("--versus", action="store_true",
                    help="two rivals on one keyboard, one panel each (ARENA only; testing)")
    ap.add_argument("--mode", choices=modes.MODE_IDS,
                    help="start the ARENA duel in a mode, skipping the menu: "
                         + "; ".join(f"{m.id} = {m.label}" for m in modes.MODES))
    ap.add_argument("--classic", action="store_true",
                    help="the single-prince level (situation S3 unless one is named), "
                         "without the menu")
    ap.add_argument("--menu", action="store_true", help="show the start menu (the three modes)")
    ap.add_argument("--menu-keys", default="", help=argparse.SUPPRESS)   # scripted menu keys for checks
    ap.add_argument("--art", choices=("original", "generated", "placeholder"),
                    help="art to draw (default: original if bundled, else generated)")
    ap.add_argument("--scale", type=int, default=3)
    ap.add_argument("--speed", type=float, default=1.0, help="animation speed multiplier")
    ap.add_argument("--watch", choices=("baseline", "model-history", "model-obs-only"))
    ap.add_argument("--live", action="store_true", help="allow paid model calls in --watch")
    ap.add_argument("--provider", default="anthropic")
    ap.add_argument("--model", default=None)
    ap.add_argument("--replay", metavar="TRACE")
    ap.add_argument("--playtest", action="store_true",
                    help="with --versus: write playtest telemetry, one log per seat "
                         "(docs/final/playtest/TELEMETRY.md)")
    ap.add_argument("--telemetry-dir", default="traces/playtest",
                    help="where --playtest logs go (git-ignored)")
    ap.add_argument("--screenshot", metavar="PNG", help=argparse.SUPPRESS)
    ap.add_argument("--keys", default="", help=argparse.SUPPRESS)   # scripted input for checks
    args = ap.parse_args(argv)

    # Decision #92: a bare `play.py` opens the three-mode menu. Naming a situation, or any of
    # --classic/--versus/--watch/--replay (or scripted --keys/--screenshot without menu keys),
    # keeps the single-player behaviour.
    if args.situation is None:
        if not (args.mode or args.menu or args.classic or args.versus or args.watch or args.replay
                or ((args.keys or args.screenshot) and not args.menu_keys)):
            args.menu = True
        else:
            args.situation = "S3"
    if args.playtest and not (args.versus or args.mode or args.menu):
        ap.error("--playtest goes with --versus or a --mode (the online server has its own --playtest)")
    if args.mode or args.menu:
        return mode_main(ap, args)
    if args.versus:
        if args.situation != "ARENA" or args.watch or args.replay:
            ap.error("--versus plays the ARENA only, without --watch or --replay")
        try:
            import pygame  # noqa: F401
        except ImportError:
            print("pygame is not installed. Run: uv sync --extra play", file=sys.stderr)
            return 2
        return versus_main(args)
    if args.watch and args.replay:
        ap.error("choose --watch or --replay, not both")
    if args.situation in levels.EXHIBITION_IDS and not args.replay:
        try:
            levels.get(args.situation)
        except (levels.LevelDataMissing, levels.LevelDataMismatch) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        if args.watch and args.watch.startswith("model"):
            ap.error(f"model players are not set up for {args.situation} yet "
                     "(its tile legend is not in the prompt)")
    if args.watch and args.watch.startswith("model"):
        if not args.live:
            ap.error("model players make paid API calls; pass --live")
        if args.situation not in TUNING_SITUATIONS:
            ap.error("watch a model only on S1-S3: H1-H3 are held out until the final trials")
        from agents.providers import ProviderConfigError, check_credentials
        try:
            check_credentials(args.provider)
        except ProviderConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    try:
        import pygame
    except ImportError:
        print("pygame is not installed. Run: uv sync --extra play", file=sys.stderr)
        return 2
    from render import draw

    if args.screenshot:
        import os
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

    # Episode and mode
    replay_steps: list[dict] = []
    if args.replay:
        header, replay_steps = load_trace(args.replay)
        driver = replay_driver(header)
        title = f"replay {header['player']} {header['situation']} seed {header['seed']}"
    elif args.watch:
        driver = Driver(args.situation, args.seed, max_actions=SITUATION_DEFAULT)
        title = f"watch {args.watch} {args.situation} seed {args.seed}"
    else:
        driver = Driver(args.situation, args.seed, max_actions=None)
        title = f"play {args.situation}"

    pygame.init()
    scale = max(1, args.scale)
    info_h = 22 * scale // 3 * 2
    window = pygame.display.set_mode((draw.SCREEN_W * scale, draw.SCREEN_H * scale + info_h))
    pygame.display.set_caption(f"Prince of Persia L1 reconstruction: {title}")
    screen = pygame.Surface((draw.SCREEN_W, draw.SCREEN_H))
    art = "placeholder" if args.placeholder else (args.art or draw.default_art())
    renderer = draw.Renderer(original=art == "original", art=art)
    font = pygame.font.Font(None, 9 * scale)
    clock = pygame.time.Clock()

    watch_q: queue.Queue = queue.Queue()
    if args.watch:
        start_watch(args.watch, args.situation, args.seed, args.provider, args.model, watch_q)

    names = {pygame.K_LEFT: "left", pygame.K_RIGHT: "right", pygame.K_UP: "up",
             pygame.K_DOWN: "down", pygame.K_SPACE: "space"}
    held: set[str] = set()
    pending: list[str] = []
    scripted = [k for k in args.keys.split(",") if k]
    clip_poses: list = []
    clip_i = 0
    current: Shown | None = None
    status = f"{renderer.art} art" + ("" if renderer.art == art else f" ({art} images missing)")
    message = ""
    replay_i = 0
    watch_done = None
    tick = 0
    # Screenshot checks: enough frames for every scripted key (each clip <= 12 frames).
    frames_left = None if not args.screenshot else 400 + 16 * len(scripted)

    def begin(shown: Shown):
        nonlocal clip_poses, clip_i, current, message
        current = shown
        clip_poses, clip_i = shown.poses, 0
        tag = "" if shown.source == "human" else f"[{shown.source}] "
        message = f"{tag}{shown.action}" + ("" if shown.accepted else f": refused ({shown.error})")
        if shown.mismatch:
            message = "REPLAY MISMATCH " + shown.mismatch

    if driver.intro() is not None:
        begin(driver.intro())

    running = True
    while running:
        shift = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key == pygame.K_r and not (args.watch or args.replay):
                    driver.reset()
                    pending.clear()
                    clip_poses, clip_i, message = [], 0, "restarted"
                    if driver.intro():
                        begin(driver.intro())
                elif ev.key in names and not (args.watch or args.replay):
                    a = action_for(names[ev.key], held, shift)
                    if a:
                        pending[:] = [a]
                if ev.key in names:
                    held.add(names[ev.key])
            elif ev.type == pygame.KEYUP and ev.key in names:
                held.discard(names[ev.key])

        animating = clip_i < len(clip_poses)
        if not animating and driver.outcome()["status"] == "ongoing":
            if args.replay:
                if replay_i < len(replay_steps):
                    rec = replay_steps[replay_i]
                    replay_i += 1
                    shown = driver.apply(rec["action"], rec.get("source", "?"))
                    shown.mismatch = check_step(shown, rec)
                    begin(shown)
            elif args.watch:
                try:
                    item = watch_q.get_nowait()
                except queue.Empty:
                    item = None
                if item and "action" in item:
                    shown = driver.apply(item["action"], item["source"])
                    if item["error"] and item["source"] == "fallback":
                        shown.error = item["error"]
                    begin(shown)
                elif item and "done" in item:
                    watch_done = item["done"]
                elif item and "crashed" in item:
                    message = "runner error: " + item["crashed"]
            else:
                if scripted and not pending:
                    pending.append(scripted.pop(0))
                legal = driver.legal()
                if legal == ["WAIT"]:
                    pending[:] = ["WAIT"]               # falling: the only legal action
                if not pending:
                    rep = held_repeat(held, shift)
                    if rep and current is not None and current.action == rep:
                        pending.append(rep)
                if pending:
                    begin(driver.apply(pending.pop(0)))
        if args.watch and watch_done is None and not animating:
            try:
                item = watch_q.get_nowait()
                if "done" in item:
                    watch_done = item["done"]
                else:
                    watch_q.queue.appendleft(item)
            except queue.Empty:
                pass

        # draw
        if clip_i < len(clip_poses):
            pose = clip_poses[clip_i]
            t = (clip_i + 1) / len(clip_poses)
            clip_i += 1
        else:
            pose, t = driver.idle(), 1.0
        gate_pct = draw.interp_gates(current.before if current else None, driver.obs, t)
        renderer.draw_room(screen, driver.obs, tick, gate_pct)
        renderer.draw_kid(screen, pose)
        if pose.flash:
            renderer.flash(screen)
        renderer.draw_hud(screen, driver.obs)
        window.fill((0, 0, 0))
        window.blit(pygame.transform.scale(screen, (draw.SCREEN_W * scale,
                                                    draw.SCREEN_H * scale)), (0, 0))
        out = driver.outcome()
        o = driver.obs
        left = "-" if o["actions_left"] is None else o["actions_left"]
        line1 = f"{title}   |   {o['minutes_left']} min   actions left {left}   |   {status}"
        if out["status"] == "terminal":
            end = "ESCAPED!" if out["reason"] == "won" else out["reason"]
            line2 = f"{end}   (actions {out['actions']}, invalid {out['invalid_actions']})"
            if not (args.watch or args.replay):
                line2 += "   R to restart, Esc to quit"
        else:
            line2 = message
        if watch_done is not None:
            wd = watch_done
            line2 += (f"   | runner: {wd['outcome']['reason']}, calls {wd['model_calls']},"
                      f" failed {wd['failed_calls']}, fallbacks {wd['fallbacks']}")
        y = draw.SCREEN_H * scale + 2
        for text, colour in ((line1, (170, 170, 170)), (line2, (240, 220, 120))):
            window.blit(font.render(text, True, colour), (6, y))
            y += font.get_height()
        pygame.display.flip()
        tick += 1
        if frames_left is not None:
            frames_left -= 1
            idle = not (clip_i < len(clip_poses)) and not scripted and not pending
            if frames_left <= 0 or (idle and (out["status"] == "terminal" or not args.keys)
                                    and not args.replay and not args.watch) \
                    or (idle and (args.replay and replay_i >= len(replay_steps))):
                pygame.image.save(window, args.screenshot)
                break
            continue
        clock.tick(FPS * args.speed)
    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
