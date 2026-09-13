"""Import only settled new-round boundaries from a closed continuous session.

The first joined settlement is excluded. No assumption that every observed
terminal is a new round; each imported group requires its own boundary event.
"""
import argparse,hashlib,json
from pathlib import Path
from ingest_live import ingest
from record_resident_settlement import own_result_display

def eligible_groups(rows):
    if not rows or rows[-1]['kind']!='closed':raise ValueError('session_not_closed')
    groups={}
    for event in rows:groups.setdefault(event.get('match_seq',0),[]).append(event)
    result=[]
    for seq,events in sorted(groups.items()):
        boundaries=[e for e in events if e['kind']=='new_round_observed']
        endings=[e for e in events if e['kind']=='settlement_capture']
        if not boundaries or not endings:continue
        if len(boundaries)!=1 or len(endings)!=1:raise ValueError('ambiguous_round_boundary')
        if any(e['kind']=='scope_violation' for e in events):continue
        result.append((seq,events,endings[0]))
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);a=ap.parse_args()
    raw=a.source.read_bytes();rows=[json.loads(line) for line in raw.splitlines()]
    for seq,events,end in eligible_groups(rows):
        sid=end['session_id'];mid=f'v41-continuous-{sid}-{seq}'
        value=own_result_display(end['numeric_evidence'])
        terminals=[e for e in events if e['kind']=='action_terminal']
        data=dict(match_id=mid,game_id=6001,bet=end['expected_bet'],actual_players=2,
                  result=end['result'],balance_collection_status='disabled_by_request',
                  page_settlement_raw=value['raw'] if value else None,
                  page_settlement_displayed=value['value'] if value else None,
                  page_settlement_semantics='unverified_gross_vs_net',formal_rtp_status='unverified',
                  control_source='mixed_or_incomplete' if any(e['kind']=='stopped' or e.get('autoplay') is True for e in events) else 'controller_observed_unverified_coverage',
                  strategy_eligible=False,coverage_verified=False,settlement_observation_eligible=True,
                  source_file=a.source.name,source_sha256=hashlib.sha256(raw).hexdigest(),
                  accepted_actions=sum(e.get('accepted') is True for e in terminals),
                  unknown_actions=sum(e.get('accepted') is None for e in terminals),
                  events=events)
        out=Path(__file__).with_name(mid+'.json');encoded=json.dumps(data,ensure_ascii=False,indent=2)
        if out.exists():
            if out.read_text()!=encoded:raise ValueError('source_changed_requires_revision')
        else:
            with out.open('x') as f:f.write(encoded)
        ingest(out)

if __name__=='__main__':main()
