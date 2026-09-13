"""Record a manually observed aggregate settlement as an unqualified calibration row.

This command intentionally does not accept account ids, opponent names, cards,
tokens, or raw responses. It is for preserving a visible settlement when a
full turn capture was not running; the row cannot qualify for formal analysis.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from lab import ARMS, ROOT, Store, now


def record(args: argparse.Namespace) -> dict:
    if args.game not in ('6001', '9006'):
        raise ValueError('invalid_game')
    if args.strategy not in ARMS:
        raise ValueError('strategy_required')
    if args.stake <= 0 or args.reward < 0:
        raise ValueError('invalid_aggregate_values')
    store = Store(args.db)
    meta = {
        'client_game_id': args.game, 'phase': 'calibration',
        'strategy_arm': args.strategy, 'strategy_assignment': 'claimed_manual_observation',
        'ruleset_version': f'{args.game}-unverified', 'game_build': 'unknown',
        'vision_profile_version': 'not_running', 'controller_version': 'cua-observation-v1',
        'actual_player_count': 2, 'room_id': 'standard_1_2p', 'stake': args.stake,
        'browser_surface': 'ordinary_chrome', 'origin': 'test-h5.wajetan.com',
        'route': args.route, 'actual_control_source': 'cua_batch_unknown',
        'recording_quality': 'settlement_only', 'recorded_at': now(),
    }
    match_id = store.begin(meta)
    store.append(match_id, 2, {'type': 'action_unknown', 'reason': 'turn_capture_not_running'})
    store.append(match_id, 3, {'type': 'settlement_observed', 'source': 'visible_ui',
                               'player_points': args.player_points,
                               'opponent_points': args.opponent_points,
                               'opponent_remaining_cards': args.opponent_cards,
                               'displayed_reward': args.reward})
    settlement = {
        'visible': True, 'result': args.result, 'end_reason': args.end_reason,
        'stake': args.stake, 'gross_return_displayed': args.reward,
        'net_delta_displayed': args.reward - args.stake,
        'player_points': args.player_points, 'opponent_points': args.opponent_points,
        'opponent_remaining_cards': args.opponent_cards,
        'balance_before_displayed': args.balance_before,
        'balance_after_displayed': None,
        'balance_after_status': 'not_visible_in_settlement',
        'quality': 'mixed_or_unverified_control',
    }
    quality = store.finish(match_id, settlement)
    store.c.close()
    return {'status': 'recorded_unqualified', 'match_id': match_id,
            'quality': quality, 'reason': 'settlement_only'}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--db', type=Path, default=ROOT / 'samples.sqlite3')
    p.add_argument('--game', choices=('6001', '9006'), required=True)
    p.add_argument('--route', required=True)
    p.add_argument('--strategy', choices=ARMS, required=True)
    p.add_argument('--result', choices=('win', 'loss', 'draw'), required=True)
    p.add_argument('--end-reason', choices=('hand_empty', 'opponent_hand_empty', 'deck_exhausted', 'tie_break', 'unknown'), required=True)
    p.add_argument('--stake', type=float, required=True)
    p.add_argument('--reward', type=float, required=True)
    p.add_argument('--player-points', type=int, required=True)
    p.add_argument('--opponent-points', type=int, required=True)
    p.add_argument('--opponent-cards', type=int, required=True)
    p.add_argument('--balance-before', type=float, required=True)
    a = p.parse_args()
    print(json.dumps(record(a), ensure_ascii=False, indent=2))
