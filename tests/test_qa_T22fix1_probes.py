"""QA (Gate 1) probes for T22-fix1: WAIT forwarding, labels, play.py defaults, hosted chooser,
weights cache, fallback log, docs. Headless, no network, no training, no --live."""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from agents import modes                      # noqa: E402
from agents.rl import policy                  # noqa: E402
from server import modes as smodes            # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
NODE = shutil.which("node")


class Scripted:
    name, kind = "scripted", "test"

    def __init__(self, answers):
        self.answers, self.i = list(answers), 0

    def reset(self, seed):
        self.i = 0

    def decide(self, observation, legal):
        a = self.answers[min(self.i, len(self.answers) - 1)]
        self.i += 1
        if isinstance(a, Exception):
            raise a
        return a


def _rival(answers):
    return modes._rival_class()(Scripted(answers), "baseline")


# --- WAIT forwarding ---------------------------------------------------------------------------
@pytest.mark.parametrize("seed", (1, 2, 5))
def test_game_path_matches_runner_path_on_other_seeds(seed):
    from pop.versus_runner import snapshot
    from tests.test_eval_T22_parity import _game, _runner
    res = _runner(seed)
    ep, game_b, b = _game(seed)
    runner_b = [(r["frame"], r["input"]) for r in res["traces"]["B"] if r["input"] not in (None, "WAIT")]
    assert runner_b == [x for x in game_b if x[1] != "WAIT"]
    assert res["final_snapshot"] == snapshot(ep)
    assert b.fallback_log == []


@pytest.mark.parametrize("bad", ["wait", "Wait", " WAIT", "", b"WAIT", ["WAIT"], 0, False])
def test_near_miss_wait_answers_are_labelled_fallbacks_not_wait(bad):
    r = _rival([bad])
    r.reset(0)
    assert r({}, ["RIGHT", "WAIT"]) is None
    assert [e.get("source") for e in r.fallback_log] == ["fallback"]


def test_exception_then_wait_then_legal_sequence_keeps_cadence_and_log():
    r = _rival([RuntimeError("x"), "WAIT", "RIGHT"])
    r.reset(0)
    out = [r({}, ["RIGHT"]) for _ in range(18)]
    assert out[0] is None and out[6] == "WAIT" and out[12] == "RIGHT"
    assert len(r.fallback_log) == 1 and r.fallback_log[0]["source"] == "fallback"


def test_reset_restarts_cadence_and_clears_the_log_and_the_counters():
    r = _rival(["bogus"])
    r.reset(0)
    for _ in range(13):
        r({}, ["RIGHT"])
    assert len(r.fallback_log) == 3 and r.fallbacks == 3
    r.reset(0)
    assert r.fallback_log == [] and r.fallbacks == 0
    assert r({}, ["RIGHT"]) is None and len(r.fallback_log) == 1     # tick 0 is a decision tick again


def test_wait_is_exactly_the_engine_constant():
    from pop.seats import WAIT
    r = _rival([WAIT])
    r.reset(0)
    assert r({}, []) == "WAIT"


# --- #91 labels ---------------------------------------------------------------------------------
def test_every_server_room_path_is_honest_and_the_old_label_is_nowhere_in_server_cli():
    src = (ROOT / "server/__main__.py").read_text()
    assert "legacy" not in src and "honest=not" not in src and "AI rival" not in src
    for mode_id, label in (("baseline", "Baseline (scripted)"), ("ai", "AI Model (trained)")):
        m = smodes.make_match(mode_id, seed=1)
        try:
            assert m.honest is True
            assert getattr(m.game, "rival_label", None) == label
        finally:
            m.close()


def test_neutral_flag_never_shows_the_old_label():
    m = smodes.make_match("baseline", seed=1, neutral=True)
    try:
        assert m.neutral is True
        assert "AI rival" not in str(m.game.payload().get("rival"))
    finally:
        m.close()


def test_the_page_default_rival_label_is_honest():
    from web.bridge import make_game
    g = make_game("human_vs_ai", "A", 0, "baseline", honest=True)
    assert "Baseline (scripted)" in str(g.payload()["rival"])
    assert "true);" in (ROOT / "web/main.js").read_text()


# --- #92 play.py ---------------------------------------------------------------------------------
@pytest.fixture
def pgplay(monkeypatch):
    pytest.importorskip("pygame")
    import play
    import pygame

    class Reached(Exception):
        pass
    seen = []
    monkeypatch.setattr(play, "mode_main", lambda ap, args: (seen.append(("mode", args.menu, args.mode)), 0)[1])
    monkeypatch.setattr(play, "versus_main", lambda args: (seen.append(("versus",)), 0)[1])

    def stop(*a, **k):
        seen.append(("classic",))
        raise Reached
    monkeypatch.setattr(pygame, "init", stop)
    return play, seen, Reached


def _run(pgplay, argv):
    play, seen, Reached = pgplay
    seen.clear()
    try:
        play.main(argv)
    except Reached:
        pass
    return list(seen)


def test_bare_play_py_variants_open_the_menu(pgplay):
    assert _run(pgplay, []) == [("mode", True, None)]
    assert _run(pgplay, ["--seed", "3"]) == [("mode", True, None)]
    assert _run(pgplay, ["--placeholder"]) == [("mode", True, None)]
    assert _run(pgplay, ["--menu-keys", "escape", "--screenshot", "x.png"]) == [("mode", True, None)]


@pytest.mark.parametrize("argv", [["--classic"], ["S3"], ["S1"], ["--keys", "RIGHT"], ["--screenshot", "x.png"],
                                  ["--watch", "baseline"], ["S2", "--seed", "4"]])
def test_old_single_player_level_stays_reachable(pgplay, argv):
    assert _run(pgplay, argv) == [("classic",)]


def test_classic_with_a_named_situation_keeps_that_situation(pgplay, monkeypatch):
    play, seen, Reached = pgplay
    got = []
    orig = play.Driver
    monkeypatch.setattr(play, "Driver", lambda sit, *a, **k: (got.append(sit), orig(sit, *a, **k))[1])
    _run(pgplay, ["S2", "--classic"])
    assert got == ["S2"]


def test_versus_and_mode_flags_still_dispatch(pgplay):
    assert _run(pgplay, ["ARENA", "--versus"]) == [("versus",)]
    assert _run(pgplay, ["--mode", "ai"]) == [("mode", False, "ai")]
    assert _run(pgplay, ["--menu"]) == [("mode", True, None)]


def test_bare_versus_is_still_the_same_usage_error_as_before(pgplay):
    with pytest.raises(SystemExit):
        pgplay[0].main(["--versus"])


def test_replay_without_a_file_does_not_open_the_menu(pgplay):
    play, seen, Reached = pgplay
    seen.clear()
    with pytest.raises(Exception) as ei:
        play.main(["--replay", str(ROOT / "nope.json")])
    assert not isinstance(ei.value, Reached) and seen == []


def test_help_mode_text_comes_from_the_list():
    out = subprocess.run(["python3", str(ROOT / "play.py"), "--help"], capture_output=True, text=True,
                         cwd=ROOT, timeout=60).stdout
    flat = " ".join(out.split())
    for m in modes.MODES:
        assert f"{m.id} = {m.label}" in flat
    assert "--classic" in out


def test_help_source_has_no_hand_written_label():
    src = (ROOT / "play.py").read_text()
    i = src.index('"--mode"')
    assert "modes.MODES" in src[i:i + 500] and "AI Model" not in src[i:i + 500]


# --- #92 hosted page ------------------------------------------------------------------------------
needs_node = pytest.mark.skipif(NODE is None, reason="node not installed")


@needs_node
@pytest.mark.parametrize("search, chooser", [
    ("?seed=3&seat=B", True), ("?label=neutral", True), ("?seat=B", True), ("?seed=", True),
    ("?foo=1", True), ("?play=", False), ("?play=bogus", False), ("?mode=", False),
    ("?rival=", False), ("?seed=3&play=ai", False), ("?seat=B&mode=ai", False),
    ("?PLAY=ai", True), ("#play=ai", True),
])
def test_needs_chooser_edge_cases(search, chooser):
    code = ("const K=require(process.argv[1]);"
            "console.log(JSON.stringify(K.needsChooser(process.argv[2])))")
    out = subprocess.run([NODE, "-e", code, str(ROOT / "web/keys.js"), search],
                         capture_output=True, text=True, timeout=30)
    assert out.stdout.strip() == ("true" if chooser else "false"), out.stderr


@needs_node
def test_needs_chooser_tolerates_missing_argument():
    out = subprocess.run([NODE, "-e", "const K=require(process.argv[1]);console.log(K.needsChooser())",
                          str(ROOT / "web/keys.js")], capture_output=True, text=True, timeout=30)
    assert out.stdout.strip() == "true"


@needs_node
def test_page_unit_tests_and_syntax_still_pass():
    for cmd in (["--check", "web/main.js"], ["--check", "web/keys.js"], ["web/keys.test.js"], ["web/ui.test.js"]):
        r = subprocess.run([NODE, *cmd], capture_output=True, text=True, cwd=ROOT, timeout=60)
        assert r.returncode == 0, (cmd, r.stderr[-500:])


def test_chooser_branch_returns_before_python_starts():
    main = (ROOT / "web/main.js").read_text()
    i = main.index("if (SMKeys.needsChooser(window.location.search)) {")
    j = main.index("return;", i)
    assert "startPython" not in main[i:j]
    assert main.index("await startPython();", i) > j


def test_chooser_marks_no_mode_current_and_smoke_picks_one_of_three():
    main = (ROOT / "web/main.js").read_text()
    assert "needsChooser(window.location.search) ? null" in main
    m = (ROOT / "tools/web/smoke.cjs").read_text()
    assert 'href="?play=baseline"' in m and "modeCount !== 3" in m


def test_online_page_is_untouched_by_the_chooser():
    assert "needsChooser" not in (ROOT / "web/online.js").read_text()


def test_the_smoke_workflow_still_runs_smoke_cjs_and_the_node_unit_tests():
    wf = (ROOT / ".github/workflows/web-smoke.yml").read_text()
    assert "tools/web/smoke.cjs" in wf and "web/keys.test.js" in wf


# --- weights cache ----------------------------------------------------------------------------------
@pytest.fixture
def weights_copy(tmp_path):
    p = tmp_path / "w.json"
    shutil.copy(policy.SHIPPED_WEIGHTS, p)
    modes._NET_CACHE.clear()
    yield p
    modes._NET_CACHE.clear()


def test_cache_refuses_wrong_hash_cold_and_warm_and_does_not_cache_the_failure(weights_copy):
    with pytest.raises(policy.WeightsError):
        modes.make_controller("ai", weights=weights_copy, sha256="0" * 64)          # cold
    assert modes._NET_CACHE == {}
    modes.make_controller("ai", weights=weights_copy, sha256=policy.SHIPPED_SHA256)
    n = len(modes._NET_CACHE)
    for bad in ("0" * 64, policy.SHIPPED_SHA256[:-1] + "0", ""):
        with pytest.raises(policy.WeightsError):
            modes.make_controller("ai", weights=weights_copy, sha256=bad)           # warm
    assert len(modes._NET_CACHE) == n


def test_cache_does_not_serve_one_path_for_another(weights_copy, tmp_path):
    modes.make_controller("ai", weights=weights_copy)
    other = tmp_path / "other.json"
    other.write_text("{}")
    with pytest.raises(Exception):
        modes.make_controller("ai", weights=other)           # a different, broken file: not the cached net
    with pytest.raises(policy.WeightsError):
        modes.make_controller("ai", weights=tmp_path / "missing.json")


def test_same_content_other_path_is_checked_again(weights_copy, tmp_path, monkeypatch):
    calls = []
    real = policy.load_net
    monkeypatch.setattr(policy, "load_net", lambda p, s: (calls.append(str(p)), real(p, s))[1])
    modes.make_controller("ai", weights=weights_copy)
    twin = tmp_path / "twin.json"
    shutil.copy(weights_copy, twin)
    modes.make_controller("ai", weights=twin)
    modes.make_controller("ai", weights=twin)
    assert len(calls) == 2


def test_cache_rechecks_when_size_changes(weights_copy):
    modes.make_controller("ai", weights=weights_copy)
    weights_copy.write_bytes(weights_copy.read_bytes() + b" ")
    with pytest.raises(policy.WeightsError):
        modes.make_controller("ai", weights=weights_copy)


def _flip_one_byte(path):
    data = bytearray(path.read_bytes())
    data[-3] = ord("0") if data[-3] != ord("0") else ord("1")
    path.write_bytes(bytes(data))


def test_cache_rechecks_when_mtime_changes_at_the_same_size(weights_copy):
    modes.make_controller("ai", weights=weights_copy)
    st = weights_copy.stat()
    _flip_one_byte(weights_copy)
    os.utime(weights_copy, ns=(st.st_atime_ns, st.st_mtime_ns + 5_000_000_000))
    with pytest.raises(policy.WeightsError):
        modes.make_controller("ai", weights=weights_copy)


def test_cache_rechecks_a_same_size_edit_with_the_mtime_restored(weights_copy):
    modes.make_controller("ai", weights=weights_copy)
    st = weights_copy.stat()
    _flip_one_byte(weights_copy)
    os.utime(weights_copy, ns=(st.st_atime_ns, st.st_mtime_ns))
    with pytest.raises(policy.WeightsError):
        modes.make_controller("ai", weights=weights_copy)


def test_each_room_gets_its_own_controller_state_over_the_shared_net():
    a = modes.make_seat_rival("ai")
    b = modes.make_seat_rival("ai")
    assert a.controller is not b.controller
    assert a.controller.policy_macro is not b.controller.policy_macro
    assert a.controller.policy_macro.net is b.controller.policy_macro.net


def test_shared_net_is_not_mutated_by_play():
    from pop.versus import arena_episode
    a = modes.make_seat_rival("ai")
    net = a.controller.policy_macro.net

    def snap(n):
        return hashlib.sha256(repr(sorted((k, repr(v)) for k, v in vars(n).items())).encode()).hexdigest()
    before = snap(net)
    ep = arena_episode(0)
    ep.reset(0)
    a.reset(0)
    for _ in range(240):
        modes.step_ai_seat(ep, a, "B")
        ep.tick()
    assert snap(net) == before


# --- fallback log reaches the console only --------------------------------------------------------------
def test_page_payload_and_server_state_carry_no_fallback_log():
    from web.bridge import make_game
    g = make_game("human_vs_ai", "A", 0, "ai", honest=True)
    g.rival.fallback_log.append({"source": "fallback", "frame": 1})
    assert "fallback" not in g.tick_json()
    m = smodes.make_match("ai", seed=2)
    try:
        assert "fallback" not in str(m.game.payload())
    finally:
        m.close()


def test_main_js_fallback_goes_to_console_warn_only():
    js = (ROOT / "web/main.js").read_text()
    i = js.index("function reportFallbacks")
    body = js[i:js.index("function stepGame")]
    assert "console.warn" in body
    for sink in ("textContent", "innerHTML", "alert(", "setStatus"):
        assert sink not in body
    assert "loggedFallbacks = 0" in js


# --- docs -----------------------------------------------------------------------------------------
def test_docs_state_the_required_sentences():
    gm = (ROOT / "docs/final/GAME_MODES.md").read_text()
    flat = " ".join(gm.split())
    assert "synchronously" in flat and "no time budget" in flat and "0.04 s" in flat
    assert "label, not a claim" in flat and "No win rate" in flat
    assert "T09" in flat and "not supported" in flat
    assert "--classic" in gm
    on = " ".join((ROOT / "docs/final/ONLINE_PLAY.md").read_text().split())
    assert 'the old "AI rival: ..." label is gone from the server command' in on
    wb = " ".join((ROOT / "docs/final/WEB_BUILD.md").read_text().split())
    assert "opens on the mode chooser" in wb


def test_no_win_rate_or_strength_figure_in_menu_hud_or_end_screen():
    for p in list((ROOT / "render").glob("*.py")) + [ROOT / "web/main.js", ROOT / "web/bridge.py",
                                                      ROOT / "agents/modes.py"]:
        t = p.read_text().lower()
        assert not re.search(r"win[ _-]?rate|win %|% win", t), p.name


def test_web_build_mode_ai_row_names_the_label_the_page_shows():
    wb = (ROOT / "docs/final/WEB_BUILD.md").read_text()
    assert 'labelled "AI rival: versus-baseline (scripted)"' not in wb


# --- scope -------------------------------------------------------------------------------------------
def test_no_forbidden_path_is_touched():
    r = subprocess.run(["git", "diff", "--name-only", "0ff9d4a..19dc355"], capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        pytest.skip("history not available")
    for f in r.stdout.split():
        assert not f.startswith(("pop/", "agents/rl/", "tools/rl/", "evaluation/", "web/bridge.py")), f
        assert f != "agents/versus_baseline.py"
