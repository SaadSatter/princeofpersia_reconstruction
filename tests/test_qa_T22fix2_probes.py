"""QA probes for T22-fix2: R restart with --playtest, the menu with --playtest, and
telemetry never changing a local AI run."""

from __future__ import annotations

import json
import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
pygame = pytest.importorskip("pygame")
import play  # noqa: E402
from agents import modes  # noqa: E402


def rows(path):
    return [json.loads(x) for x in path.read_text().splitlines()]


def run_with_r(monkeypatch, tmp_path, argv, r_on_calls=(3,)):
    """Run play.main headless, injecting an R key press on the given event.get() calls."""
    real = pygame.event.get
    n = {"i": 0}

    def fake(*a, **k):
        n["i"] += 1
        ev = list(real(*a, **k))
        if n["i"] in r_on_calls:
            ev.append(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r))
        return ev
    monkeypatch.setattr(pygame.event, "get", fake)
    return play.main([*argv, "--scale", "1", "--screenshot", str(tmp_path / "s.png")])


@pytest.mark.parametrize("mode, seats", [("ai", ["A"]), ("baseline", ["A"]), ("human", ["A", "B"])])
def test_r_restart_with_playtest_opens_a_second_log_per_logged_seat(monkeypatch, tmp_path, mode, seats):
    out = tmp_path / "pt"
    keys = ",".join(["A:RIGHT"] * 8)
    assert run_with_r(monkeypatch, tmp_path, ["--mode", mode, "--playtest", "--telemetry-dir", str(out),
                                               "--keys", keys]) == 0
    names = sorted(p.name for p in out.glob("*.jsonl"))
    for duel in ("001", "002"):
        for s in seats:
            assert any(f"-LOCAL-{duel}-{s}.jsonl" in n for n in names), (duel, s, names)
    if mode != "human":
        assert not any(n.endswith("-B.jsonl") for n in names)
    assert not any("-003-" in n for n in names)
    first = rows(next(out.glob("*-001-A.jsonl")))
    second = rows(next(out.glob("*-002-A.jsonl")))
    assert first[-1]["type"] == "duel_end" and first[-1]["reason"] in ("abandoned", "restart")
    assert second[0]["type"] == "header" and second[0]["rival"] == mode
    assert second[1]["type"] == "duel_start"
    assert [r for r in second if r["type"] == "action"]


def test_r_restart_without_playtest_writes_nothing_and_still_restarts(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert run_with_r(monkeypatch, tmp_path, ["--mode", "ai", "--keys", "A:RIGHT,A:RIGHT,A:RIGHT,A:RIGHT"]) == 0
    assert not (tmp_path / "traces").exists()


def test_r_restart_resets_the_ai_rival_once_more(monkeypatch, tmp_path):
    resets = []
    real = modes.make_seat_rival

    def spy(mode, **kw):
        r = real(mode, **kw)
        orig = r.reset
        r.reset = lambda seed, _o=orig: (resets.append(seed), _o(seed))[1]
        return r
    monkeypatch.setattr(modes, "make_seat_rival", spy)
    out = tmp_path / "pt"
    run_with_r(monkeypatch, tmp_path, ["--mode", "baseline", "--playtest", "--telemetry-dir", str(out),
                                       "--keys", "A:RIGHT,A:RIGHT,A:RIGHT,A:RIGHT"])
    assert len(resets) == 2                       # once at start, once on R


def test_menu_with_playtest_logs_the_chosen_mode_and_only_seat_a(tmp_path):
    out = tmp_path / "pt"
    assert play.main(["--menu", "--menu-keys", "down,return", "--playtest", "--telemetry-dir", str(out),
                      "--scale", "1", "--screenshot", str(tmp_path / "s.png")]) == 0
    files = sorted(p.name for p in out.glob("*.jsonl"))
    assert len(files) == 1 and files[0].endswith("-A.jsonl")
    assert rows(out / files[0])[0]["rival"] == "baseline"


def test_ai_log_never_names_the_ai_seat_or_fallbacks(tmp_path):
    out = tmp_path / "pt"
    play.main(["--mode", "ai", "--playtest", "--telemetry-dir", str(out), "--scale", "1",
               "--screenshot", str(tmp_path / "s.png"), "--keys", ",".join(["A:RIGHT"] * 10)])
    text = "".join(p.read_text() for p in out.iterdir())
    low = text.lower()
    assert "fallback" not in low and "policy" not in low
    assert '"seat":"B"' not in text and '"seat": "B"' not in text
    assert all(r.get("seat", "A") == "A" for p in out.glob("*.jsonl") for r in rows(p))


@pytest.mark.parametrize("mode", ["ai", "baseline", "human"])
def test_playtest_does_not_change_a_local_run(tmp_path, mode):
    keys = ",".join(["A:RIGHT", "A:RIGHT", "A:DRAW", "A:LUNGE"] * 3)
    base = ["--mode", mode, "--seed", "4", "--scale", "1", "--keys", keys]
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    assert play.main([*base, "--screenshot", str(a)]) == 0
    assert play.main([*base, "--screenshot", str(b), "--playtest", "--telemetry-dir", str(tmp_path / "pt")]) == 0
    assert a.read_bytes() == b.read_bytes()


def test_playtest_still_refused_for_single_player():
    with pytest.raises(SystemExit):
        play.main(["S3", "--playtest"])
    with pytest.raises(SystemExit):
        play.main(["S3", "--classic", "--playtest"])


def test_weights_cache_recovers_when_the_file_is_restored(tmp_path):
    """Item 3: edit -> refused, restore -> accepted again, and the shared net is reused."""
    import shutil
    from agents.rl import policy
    src = policy.SHIPPED_WEIGHTS if hasattr(policy, "SHIPPED_WEIGHTS") else None
    if src is None:
        pytest.skip("no SHIPPED_WEIGHTS constant")
    w = tmp_path / "w.json"
    shutil.copy(src, w)
    a = modes.make_controller("ai", weights=w)
    good = w.read_bytes()
    st = w.stat()
    w.write_bytes(good[:-2] + (b"0 " if good[-2:] != b"0 " else b"1 "))
    os.utime(w, ns=(st.st_atime_ns, st.st_mtime_ns))
    with pytest.raises(policy.WeightsError):
        modes.make_controller("ai", weights=w)
    w.write_bytes(good)
    b = modes.make_controller("ai", weights=w)
    assert a.policy_macro.net is b.policy_macro.net
