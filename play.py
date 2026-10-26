"""Pygame frontend: play, watch an agent, or replay a trace.

Working directory: the project folder.

    uv sync --extra play
    uv run python play.py S3                      # play with the keyboard (bundled original art)
    uv run python play.py S3 --placeholder        # placeholder shapes instead
    uv run python play.py S1 --watch baseline     # watch the baseline play
    uv run python play.py S1 --watch model-history --live   # watch the model (paid calls)
    uv run python play.py --replay traces/eval/20261026T060347Z-baseline-S3-100.jsonl

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
from dataclasses import dataclass, field
from pathlib import Path

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
    ap.add_argument("situation", nargs="?", default="S3", choices=sorted(SITUATIONS))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--placeholder", action="store_true", help="draw placeholder shapes")
    ap.add_argument("--scale", type=int, default=3)
    ap.add_argument("--speed", type=float, default=1.0, help="animation speed multiplier")
    ap.add_argument("--watch", choices=("baseline", "model-history", "model-obs-only"))
    ap.add_argument("--live", action="store_true", help="allow paid model calls in --watch")
    ap.add_argument("--provider", default="anthropic")
    ap.add_argument("--model", default=None)
    ap.add_argument("--replay", metavar="TRACE")
    ap.add_argument("--screenshot", metavar="PNG", help=argparse.SUPPRESS)
    ap.add_argument("--keys", default="", help=argparse.SUPPRESS)   # scripted input for checks
    args = ap.parse_args(argv)

    if args.watch and args.replay:
        ap.error("choose --watch or --replay, not both")
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
    renderer = draw.Renderer(original=not args.placeholder)
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
    status = ("original art" if renderer.original else
              "placeholder art" + ("" if args.placeholder else
                                   " (bundled images missing)"))
    message = ""
    replay_i = 0
    watch_done = None
    tick = 0
    frames_left = None if not args.screenshot else 400

    def begin(shown: Shown):
        nonlocal clip_poses, clip_i, current, message
        current = shown
        clip_poses, clip_i = shown.poses, 0
        tag = "" if shown.source == "human" else f"[{shown.source}] "
        message = f"{tag}{shown.action}" + ("" if shown.accepted else f": refused ({shown.error})")
        if shown.mismatch:
            message = "REPLAY MISMATCH " + shown.mismatch

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
