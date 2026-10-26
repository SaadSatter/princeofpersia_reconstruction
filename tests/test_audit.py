"""The audit frontend must use the real interface without changing rules."""
import pickle
import json
import subprocess
import sys

from audit import command
from pop.interface import Episode


def test_illegal_action_keeps_entire_game_and_observation(capsys):
    ep = Episode('S1')
    before = pickle.dumps(ep._game)
    observation = ep.observe('kid')
    command(ep, 'step NOT_AN_ACTION')
    result = json.loads(capsys.readouterr().out)
    assert result['step']['accepted'] is False
    assert result['observation_unchanged'] and result['frames_unchanged']
    assert pickle.dumps(ep._game) == before
    assert ep.observe('kid') == observation
    assert ep.outcome()['invalid_actions'] == 1  # refusal bookkeeping is intentional
    assert ep.outcome()['actions'] == 0


def test_readme_operations_reach_real_terminal():
    commands = 'reset 0\nobserve\nlegal_actions\nstep NOT_AN_ACTION\nstep RIGHT\noutcome\n'
    commands += 'step RIGHT\nstep JUMP_RIGHT\n' + 'step RIGHT\n' * 6
    commands += 'step RUN_JUMP_RIGHT\nstep RIGHT\nstep UP\noutcome\nquit\n'
    proc = subprocess.run([sys.executable, 'audit.py', '--scenario', 'S1'],
                          input=commands, text=True, capture_output=True, check=True)
    rows = [json.loads(line) for line in proc.stdout.splitlines()[1:]]
    assert rows[3]['step']['accepted'] is False
    assert rows[3]['observation_unchanged']
    assert rows[-1]['outcome']['reason'] == 'won'
    assert rows[-1]['outcome']['invalid_actions'] == 1


def test_missing_key_stops_without_a_trace(tmp_path, monkeypatch):
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    proc = subprocess.run([sys.executable, 'audit.py', '--episode', 'live', '--out', str(tmp_path)],
                          text=True, capture_output=True)
    assert proc.returncode == 2
    assert 'No episode was run' in proc.stderr
    assert list(tmp_path.iterdir()) == []
