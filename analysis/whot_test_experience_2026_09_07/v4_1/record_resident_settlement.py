"""Append a closed BET1 calibration session without certifying strategy or RTP."""
import argparse,hashlib,json
from pathlib import Path
from ingest_live import ingest
from resident_calibration import valid_numeric

def own_result_display(evidence):
    """6001 calibrated first settlement row only; never use list order.

    The signed display is retained as a page value, not certified net profit.
    Missing boxes or multiple candidate values remain unknown.
    """
    candidates=[]
    for item in evidence.get('returns',[]):
        box=item.get('box');value=item.get('value','')
        if not isinstance(value,str) or not valid_numeric(value,signed=True):continue
        if not isinstance(box,list) or len(box)!=4:continue
        if not all(isinstance(x,(int,float)) for x in box):continue
        x,y,w,h=box
        if .40<=x and x+w<=.54 and .31<=y and y+h<=.40:
            candidates.append(value)
    if len(candidates)!=1:return None
    return {'raw':candidates[0],'value':float(candidates[0].replace(',','')),
            'row':'player_first_row','semantics':'unverified_gross_vs_net'}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('source',type=Path);ap.add_argument('--number',type=int,required=True)
    ap.add_argument('--balance-before',type=float)
    args=ap.parse_args();raw=args.source.read_bytes()
    rows=[json.loads(line) for line in raw.splitlines()]
    assert rows[-1]['kind']=='closed','session_not_closed'
    endings=[e for e in rows if e['kind']=='settlement_capture']
    entries=[e for e in rows if e['kind']=='entry_submitted' and e['receipt']['operation']=='bet1_entry_click']
    assert len(endings)==1 and len(entries)==1,'ambiguous_session'
    assert not any(e['kind']=='scope_violation' for e in rows),'scope_violation'
    last=endings[0];balance=last['numeric_evidence'].get('balance',[])
    numeric_balance=float(balance[0]['value'].replace(',','')) if len(balance)==1 else None
    terminals=[e for e in rows if e['kind']=='action_terminal']
    page_value=own_result_display(last['numeric_evidence'])
    data=dict(match_id=f'v41-native-calibration-{args.number:03d}',game_id=6001,bet=1,
              actual_players=2,actual_players_source='two_row_settlement_layout',result=last['result'],
              balance_before=args.balance_before,balance_before_source='homepage_visible_readback' if args.balance_before is not None else 'not_collected_by_request',
              balance_after_debit=None,balance_after=numeric_balance,
              page_return=None,page_net_change_displayed=None,player_points=None,opponent_points=None,
              page_settlement_displayed=page_value['value'] if page_value else None,
              page_settlement_raw=page_value['raw'] if page_value else None,
              page_settlement_semantics='unverified_gross_vs_net',
              player_cards=None,opponent_cards=None,end_reason='unknown',
              control_source='mixed_unknown_after_input_stop',strategy_eligible=False,
              settlement_observation_eligible=True,formal_rtp_status='unverified',coverage_verified=False,
              numeric_status=last['numeric_status'],numeric_evidence=last['numeric_evidence'],
              operation_source=args.source.name,operation_source_sha256=hashlib.sha256(raw).hexdigest(),
              submitted_logical_actions=sum(e['kind']=='action_submitted' for e in rows),
              accepted_logical_actions=sum(e.get('accepted') is True for e in terminals),
              unknown_logical_actions=sum(e.get('accepted') is None for e in terminals),
              events=rows,
              notes=['Native input acknowledgements are not game acceptance.',
                     'Post-stop control is unknown; no strategy qualification.',
                     'Missing return/points are not zero-filled; raw numeric OCR retained.',
                     'Observed-turn timings do not independently prove actual turn onset.'])
    out=Path(__file__).with_name(f'settlement_{args.number:03d}.json')
    with out.open('x') as f:json.dump(data,f,ensure_ascii=False,indent=2)
    ingest(out)
    print(json.dumps({k:data[k] for k in ('match_id','result','balance_after','numeric_status',
                                         'submitted_logical_actions','accepted_logical_actions','unknown_logical_actions')}))

if __name__=='__main__':main()
