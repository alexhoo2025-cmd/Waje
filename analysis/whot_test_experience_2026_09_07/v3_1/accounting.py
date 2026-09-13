"""Certified, balanced test-chip ledger only; no averaging per-round ratios."""
from decimal import Decimal, InvalidOperation


def reconcile(row):
    required=('stake','gross_return','fee','bonus','adjustment','balance_before','balance_after_debit','balance_after')
    if row.get('semantics_status')!='certified' or not row.get('asset_unit'):
        return {'status':'unknown','reason':'semantics_unverified'}
    try:
        v={k:Decimal(str(row[k])) for k in required}
        if not all(x.is_finite() for x in v.values()) or v['stake']<=0 or v['fee']<0 or v['gross_return']<0:
            raise ValueError()
    except (KeyError,ValueError,InvalidOperation):return {'status':'unknown','reason':'missing_or_invalid_ledger'}
    if row.get('fee_timing') not in ('entry','settlement'):return {'status':'unknown','reason':'fee_timing_unknown'}
    entry_fee=v['fee'] if row['fee_timing']=='entry' else Decimal(0)
    if v['balance_after_debit']!=v['balance_before']-v['stake']-entry_fee:
        return {'status':'mismatch','reason':'entry_balance_mismatch'}
    expected=v['balance_before']-v['stake']+v['gross_return']-v['fee']+v['bonus']+v['adjustment']
    if expected!=v['balance_after']:return {'status':'mismatch','reason':'settlement_balance_mismatch'}
    return {'status':'ok','stake':str(v['stake']),'gross_return':str(v['gross_return']),'asset_unit':row['asset_unit']}


def aggregate(rows):
    records=[reconcile(r) for r in rows]
    if not records or any(r['status']!='ok' for r in records):return {'rtp':None,'status':'ledger_unverified','n':len(rows)}
    if len({r['asset_unit'] for r in records})!=1:return {'rtp':None,'status':'unit_mismatch','n':len(rows)}
    stake=sum(Decimal(r['stake']) for r in records);returned=sum(Decimal(r['gross_return']) for r in records)
    return {'rtp':str(returned/stake),'stake':str(stake),'gross_return':str(returned),'n':len(rows),'status':'certified_ledger'}


def can_enter(balance,entry_debit):
    try:
        b,d=Decimal(str(balance)),Decimal(str(entry_debit))
        return b.is_finite() and d.is_finite() and d>0 and b>=d
    except InvalidOperation:return False
