"""The Pygame frontend: animation clips, keys, replay, watch mode, boundaries.

These tests need neither pygame nor the original images (CI has neither);
the one drawing smoke test is skipped without pygame.
"""

from __future__ import annotations

import ast
import os
import queue
from pathlib import Path

import pytest

import play
from play import Driver, WatchedPlayer, action_for, check_step, held_repeat, load_trace
from pop.interface import SITUATION_DEFAULT
from pop.runner import run_episode
from render import anim, assets
from solutions import SOLUTIONS

ROOT = Path(__file__).resolve().parent.parent


def _play_route(sid: str):
    d = Driver(sid, 0, max_actions=None)
    for action in SOLUTIONS[sid]:
        yield d.apply(action)


@pytest.mark.parametrize("sid", sorted(SOLUTIONS))
def test_every_step_is_one_clip_of_the_engines_frames(sid):
    """R-D26: a clip shows exactly the frames the engine spent on the step."""
    for shown in _play_route(sid):
        assert shown.accepted and shown.poses
        assert all(p.frame == 0 or p.frame in anim.ALL_FRAMES for p in shown.poses)


@pytest.mark.parametrize("sid", sorted(SOLUTIONS))
def test_clip_length_equals_step_frames(sid):
    d = Driver(sid, 0, max_actions=None)
    for action in SOLUTIONS[sid]:
        before_frames = d.outcome()["frames"]
        shown = d.apply(action)
        spent = d.outcome()["frames"] - before_frames
        assert len(shown.poses) == max(spent, 1), (sid, action)


def test_clip_ends_where_the_engine_put_the_kid():
    d = Driver("S1", 0, max_actions=None)
    for action in ("RIGHT", "RIGHT", "JUMP_RIGHT"):
        shown = d.apply(action)
        k = shown.after["kid"]
        last = shown.poses[-1]
        assert (last.x, last.y) == anim.stand_point(k["row"], k["col"])
        assert last.facing == 1


def test_run_clip_starts_at_the_start_cell():
    shown = Driver("S1", 0, max_actions=None).apply("RIGHT")
    x0 = anim.stand_point(1, 1)[0]
    x1 = anim.stand_point(1, 2)[0]
    xs = [p.x for p in shown.poses]
    assert x0 < xs[0] <= xs[-1] == x1
    assert all(p.frame in anim.START_RUN for p in shown.poses)


def test_refused_action_shows_no_movement():
    d = Driver("S1", 0, max_actions=None)
    shown = d.apply("FLY")
    assert not shown.accepted and len(shown.poses) == 1
    assert shown.after["kid"] == shown.before["kid"]


def test_deaths_and_win_end_in_the_matching_pose():
    d = Driver("S1", 0, max_actions=None)
    for a in ("RIGHT", "RIGHT", "RIGHT", "DOWN", "DOWN"):
        shown = d.apply(a)
    assert d.outcome()["reason"] == "died:spikes"
    assert shown.poses[-1].frame == anim.IMPALED and d.idle().frame == anim.IMPALED
    d = Driver("S3", 0, max_actions=None)
    for shown in _play_route("S3"):
        pass
    assert shown.poses[0].frame in anim.STAIRS
    assert not shown.poses[-1].visible


def test_every_animation_frame_has_a_dos_image():
    nums = {assets.image_for(f) for f in anim.ALL_FRAMES}
    assert all(401 <= n <= 616 for n in nums)
    assert assets.image_for(anim.STAND) == 415          # checked by eye (docs/ASSETS.md)


def test_missing_images_mean_placeholder_mode(tmp_path, monkeypatch):
    monkeypatch.setenv("POP_ASSETS", str(tmp_path))
    assert assets.asset_dir() is None


@pytest.mark.parametrize("key,held,shift,expected", [
    ("right", set(), False, "RIGHT"),
    ("left", set(), True, "STEP_LEFT"),
    ("right", {"up"}, False, "JUMP_RIGHT"),
    ("right", {"up"}, True, "RUN_JUMP_RIGHT"),
    ("up", {"left"}, False, "JUMP_LEFT"),
    ("up", set(), False, "UP"),
    ("down", set(), False, "DOWN"),
    ("space", set(), False, "WAIT"),
    ("x", set(), False, None),
])
def test_keys_map_to_the_agents_actions(key, held, shift, expected):
    """R-D07: human keys produce the same action names agents submit."""
    assert action_for(key, held, shift) == expected


def test_holding_a_direction_repeats_the_run_but_never_a_jump():
    assert held_repeat({"right"}, False) == "RIGHT"
    assert held_repeat({"left"}, True) == "STEP_LEFT"
    assert held_repeat({"left", "up"}, False) is None


@pytest.mark.parametrize("path", sorted((ROOT / "traces" / "eval").glob("*-baseline-*.jsonl")),
                         ids=lambda p: p.name)
def test_replay_reproduces_committed_traces(path):
    header, steps = load_trace(path)
    d = play.replay_driver(header)
    for rec in steps:
        shown = d.apply(rec["action"], rec["source"])
        assert check_step(shown, rec) is None
    assert d.outcome()["reason"] == header["outcome"]["reason"]


def test_replay_reports_a_tampered_trace():
    header, steps = load_trace(ROOT / "traces/eval/20261026T060347Z-baseline-S1-100.jsonl")
    d = play.replay_driver(header)
    rec = dict(steps[0], kid=dict(steps[0]["kid"], col=steps[0]["kid"]["col"] + 1))
    assert "kid" in check_step(d.apply(rec["action"]), rec)


def test_watch_reports_each_submitted_step_with_its_source():
    from agents.baseline import BaselinePlayer
    q: queue.Queue = queue.Queue()
    result = run_episode(WatchedPlayer(BaselinePlayer(), q), "S1", 0)
    seen = [q.get_nowait() for _ in range(q.qsize())]
    assert [s["action"] for s in seen] == [r["action"] for r in result["trace"]]
    assert {s["source"] for s in seen} == {"baseline"}
    # The display copy of the episode reproduces the runner's.
    d = Driver("S1", 0, max_actions=SITUATION_DEFAULT)
    for s, rec in zip(seen, result["trace"]):
        assert check_step(d.apply(s["action"], s["source"]), rec) is None


def test_watch_labels_fallback_moves_as_fallback():
    from agents.model_player import ModelPlayer
    from agents.providers import FakeProvider
    q: queue.Queue = queue.Queue()
    player = ModelPlayer(FakeProvider(["no action here"]), variant="history")
    run_episode(WatchedPlayer(player, q), "S1", 0)
    seen = [q.get_nowait() for _ in range(q.qsize())]
    assert seen and all(s["source"] == "fallback" and s["action"] == "WAIT" for s in seen)


@pytest.mark.parametrize("argv", [
    ["S1", "--watch", "model-history"],                      # no --live
    ["H1", "--watch", "model-history", "--live"],            # held-out case
    ["S1", "--watch", "baseline", "--replay", "x.jsonl"],
])
def test_play_refuses_unsafe_watch_options(argv):
    with pytest.raises(SystemExit) as exc:
        play.main(argv)
    assert exc.value.code == 2


FORBIDDEN_FOR_RENDER = ("pop.engine", "pop.mechanics", "pop.situations", "pop.interface",
                        "pop.runner", "pop.observation", "agents", "evaluate", "play")


def test_render_reads_observations_only():
    """render/ never touches engine state: it gets observation dicts and poses."""
    for path in (ROOT / "render").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module or ""] + [f"{node.module}.{a.name}" for a in node.names]
            elif isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            else:
                continue
            for name in names:
                assert not name.startswith(FORBIDDEN_FOR_RENDER), (path.name, name)


def test_no_original_images_are_tracked():
    """R-D02: original art stays local (vendor/ is git-ignored)."""
    import subprocess
    try:
        out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True,
                             check=True).stdout.split()
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("not a git checkout")
    assert not [f for f in out if f.lower().endswith((".png", ".pal", ".dat", ".bmp"))]
    assert not [f for f in out if f.startswith("vendor/")]


def test_window_draws_in_placeholder_mode(tmp_path):
    pytest.importorskip("pygame")
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    shot = tmp_path / "shot.png"
    assert play.main(["S2", "--placeholder", "--screenshot", str(shot),
                      "--keys", "RIGHT,RIGHT"]) == 0
    assert shot.stat().st_size > 0
