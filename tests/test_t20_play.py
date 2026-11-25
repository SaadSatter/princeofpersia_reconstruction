"""T20: play.py --versus --playtest writes one log per seat; without the flag, nothing."""

from __future__ import annotations

import json
import os

import pytest


def run(tmp_path, *flags):
    pytest.importorskip("pygame")
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import play
    shot = tmp_path / "v.png"
    return play.main(["ARENA", "--versus", "--screenshot", str(shot), "--keys",
                      "A:RIGHT,B:LEFT,A:RIGHT,B:LEFT", *flags])


def test_playtest_flag_writes_both_seats(tmp_path):
    out = tmp_path / "pt"
    assert run(tmp_path, "--playtest", "--telemetry-dir", str(out)) == 0
    files = sorted(p.name for p in out.glob("*.jsonl"))
    assert len(files) == 2 and files[0].endswith("-A.jsonl") and "LOCAL" in files[0]
    rows = [json.loads(x) for x in (out / files[0]).read_text().splitlines()]
    assert rows[0]["type"] == "header" and rows[1]["type"] == "duel_start"
    assert any(r["type"] == "action" and r["accepted"] for r in rows)
    assert rows[-1]["type"] == "duel_end" and rows[-1]["reason"] == "abandoned"


def test_no_flag_no_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert run(tmp_path) == 0
    assert not (tmp_path / "traces").exists()


def test_playtest_needs_versus():
    import play
    with pytest.raises(SystemExit):
        play.main(["S3", "--playtest"])
