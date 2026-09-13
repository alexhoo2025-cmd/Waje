"""Import a recovered settlement observed on an already-running 6001 page.

The record is deliberately non-strategy-eligible: no entry event or turn
coverage is inferred. Only the visible signed settlement row is retained.
"""
import argparse, hashlib, json
from pathlib import Path
from ingest_live import ingest
from record_resident_settlement import own_result_display


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('source', type=Path)
    ap.add_argument('--expected-bet', type=int, required=True)
    ap.add_argument('--match-id', required=True)
    args = ap.parse_args()

    raw = args.source.read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    recovery_only = any(e.get('kind') == 'recovery_start' for e in rows)
    if not rows or (rows[-1].get('kind') != 'closed' and not recovery_only):
        raise ValueError('session_not_closed')
    endings = [e for e in rows if e.get('kind') == 'settlement_capture']
    seen = [e for e in rows if e.get('kind') == 'settlement_seen']
    if len(endings) != 1 or (len(seen) != 1 and not recovery_only):
        raise ValueError('ambiguous_recovered_settlement')
    if any(e.get('kind') == 'scope_violation' for e in rows):
        raise ValueError('scope_violation')

    end = endings[0]
    if end.get('expected_bet') is not None and end.get('expected_bet') != args.expected_bet:
        raise ValueError('expected_bet_mismatch')
    page = own_result_display(end.get('numeric_evidence', {}))
    data = {
        'match_id': args.match_id,
        'game_id': 6001,
        'bet': args.expected_bet,
        'actual_players': None,
        'actual_players_source': 'unknown_recovered_settlement',
        'result': end.get('result', 'unknown'),
        'balance_before': None,
        'balance_after_debit': None,
        'balance_after': None,
        'page_return': None,
        'page_net_change_displayed': None,
        'player_points': None,
        'opponent_points': None,
        'page_settlement_displayed': page['value'] if page else None,
        'page_settlement_raw': page['raw'] if page else None,
        'page_settlement_semantics': 'unverified_gross_vs_net',
        'player_cards': None,
        'opponent_cards': None,
        'end_reason': 'unknown_recovered_settlement',
        'control_source': 'recovered_existing_unknown_control',
        'strategy_eligible': False,
        'settlement_observation_eligible': True,
        'formal_rtp_status': 'unverified',
        'coverage_verified': False,
        'numeric_status': end.get('numeric_status'),
        'numeric_evidence': end.get('numeric_evidence'),
        'source_file': args.source.name,
        'source_sha256': hashlib.sha256(raw).hexdigest(),
        'submitted_logical_actions': sum(e.get('kind') == 'action_submitted' for e in rows),
        'accepted_logical_actions': sum(e.get('accepted') is True for e in rows if e.get('kind') == 'action_terminal'),
        'unknown_logical_actions': sum(e.get('accepted') is None for e in rows if e.get('kind') == 'action_terminal'),
        'events': rows,
        'notes': [
            'Recovered from a page already in progress; no new BET click was issued.',
            'Read-only settlement tail is accepted when the source contains recovery_start and settlement_capture.',
            'No hand, turn or action evidence was observed; excluded from strategy evaluation.',
            'Only the signed settlement row is retained; balance and missing fields remain unknown.',
        ],
    }
    out = Path(__file__).with_name(args.match_id + '.json')
    encoded = json.dumps(data, ensure_ascii=False, indent=2)
    if out.exists() and out.read_text() != encoded:
        raise ValueError('source_changed_requires_revision')
    if not out.exists():
        out.write_text(encoded)
    ingest(out)
    print(json.dumps({k: data[k] for k in ('match_id', 'result', 'bet', 'page_settlement_displayed', 'strategy_eligible')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
