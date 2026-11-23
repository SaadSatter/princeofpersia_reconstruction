"""Small, observation-only command frontend for the Week 7 pair audit."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from pop.interface import Episode, PLAYER_ID


def emit(value):
    print(json.dumps(value, sort_keys=True), flush=True)


def command(ep, text):
    words = text.split()
    if not words:
        return
    op, *args = words
    if op == 'reset':
        emit({'reset': ep.reset(int(args[0]) if args else 0)})
    elif op == 'observe':
        emit({'observation': ep.observe(PLAYER_ID)})
    elif op == 'legal_actions':
        emit({'legal_actions': ep.legal_actions(PLAYER_ID)})
    elif op == 'step' and len(args) == 1:
        before = ep.observe(PLAYER_ID)
        frames = ep.outcome()['frames']
        result = ep.step(PLAYER_ID, args[0])
        emit({'step': result, 'observation_unchanged': before == ep.observe(PLAYER_ID),
              'frames_unchanged': frames == ep.outcome()['frames']})
    elif op == 'outcome':
        emit({'outcome': ep.outcome()})
    else:
        raise ValueError('Use reset [seed], observe, legal_actions, step ACTION, outcome, quit')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--scenario', choices=['S1', 'S2', 'S3'], default='S1')
    ap.add_argument('--episode', choices=['baseline', 'live'])
    ap.add_argument('--out', type=Path, default=Path('traces/audit'))
    args = ap.parse_args(argv)
    if args.episode:
        from evaluate import game_version, make_player
        from pop.runner import Limits, run_episode, save_trace
        if args.episode == 'live':
            from agents.providers import ProviderConfigError, check_credentials
            try:
                check_credentials('anthropic')
            except ProviderConfigError as exc:
                ap.exit(2, f'{exc} No episode was run.\n')
        kind = 'baseline' if args.episode == 'baseline' else 'model-history'
        player = make_player(kind, 'anthropic', 'claude-haiku-4-5')
        # Audit-only runner budget; frozen scenarios and evaluation suites unchanged.
        limits = Limits(max_calls=4, call_timeout_s=8) if args.episode == 'live' else Limits()
        result = run_episode(player, args.scenario, 0, limits)
        result['game_version'] = game_version()
        result['suite'] = 'pair-audit-smoke (not final evaluation)'
        args.out.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        path = args.out / f'{stamp}-{kind}-{args.scenario}-0.jsonl'
        save_trace(result, path)
        emit({'outcome': result['outcome'], 'calls': result['model_calls'],
              'failed_calls': result['failed_calls'], 'fallbacks': result['fallbacks'],
              'trace': str(path), 'usage': result['usage']})
        if args.episode == 'live' and result['failed_calls'] == result['model_calls']:
            print('No successful live model response; this is NOT live gameplay evidence.')
            return 1
        return 0
    ep = Episode(args.scenario)
    print('Commands: reset [seed], observe, legal_actions, step ACTION, outcome, quit', flush=True)
    import sys
    for line in sys.stdin:
        if line.strip() == 'quit':
            break
        try:
            command(ep, line)
        except (ValueError, IndexError) as exc:
            emit({'error': str(exc)})
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
