"""Recompute the observed Origin checks using aggregate-only BigQuery evidence."""
from decimal import Decimal
from pathlib import Path
import json

P = Path(__file__).resolve().parent

def main():
    rows = json.loads((P/'queries/10_one_day_money_reconciliation.result.json').read_text())
    row = next(r for r in rows if r['game_scope'] == 'all_games')
    observed = json.loads((P/'origin_crosscheck.json').read_text(), parse_float=Decimal)
    control = next(r for r in observed['rows'] if r['date'] == row['stat_date'])
    unit = Decimal(100)
    effective = (Decimal(row['source_bet_sum']) - row['source_refund_sum']) / unit
    payout = Decimal(row['source_settlement_sum']) / unit
    extra = Decimal(row['source_extra_sum']) / unit
    gaming_margin = effective - payout
    reported_revenue = gaming_margin + extra
    checks = {
        'reported_game_rounds_match': row['event_rows'] == control['game_rounds'],
        'effective_stake_match': effective == control['real_bet_amount'],
        'reported_revenue_match': reported_revenue == control['revenue'],
        'log_keys_unique_in_this_sample': row['event_rows'] == row['distinct_log_keys'],
        'user_game_round_keys_unique_in_this_sample': row['event_rows'] == row['distinct_user_game_round_keys'],
        'round_keys_present_in_this_sample': row['missing_round_key_rows'] == 0,
    }
    assert all(checks.values()), checks
    receipt = {
        'status': 'single_day_definition_checks_passed_full_window_pending',
        'business_date': row['stat_date'], 'checks': checks,
        'amount_unit': 'Origin report unit; /100 scaling reconciled, currency still to certify',
        'effective_stake': str(effective), 'settlement_sum': str(payout),
        'effective_stake_minus_settlement': str(gaming_margin),
        'extra_debits': str(extra), 'reported_revenue': str(reported_revenue),
        'formula': {'effective_stake': '(bet_num-refund_num)/100',
                    'reported_revenue': '(bet_num-refund_num+extra_num-cash_settlement)/100'},
        'user_count_difference': row['users']-control['game_users'],
        'remaining_checks': [
            'Explain the two-user count difference before certifying user penetration',
            'Certify settlement finality, cash/reward scope and currency before final RTP',
            'Validate effective bet count separately; GAMEEND counts do not replace bet_count',
            'Check duplicates, coverage and monetary definitions throughout Aug 1 to cutoff',
        ],
        'source_relationship': 'Origin and Metabase are same-BigQuery reporting layers, not independent evidence',
        'scope_warning': 'One-day validation is not the requested full-period analytical result',
    }
    (P/'money-reconciliation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(receipt,ensure_ascii=False))

if __name__ == '__main__':
    main()
