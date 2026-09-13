"""Executable contract examples; synthetic/local only, never a production adapter."""
from datetime import date,timedelta
from decimal import Decimal
from itertools import permutations

def windows(end):
    return {'current':(end-timedelta(days=29),end),'previous':(end-timedelta(days=59),end-timedelta(days=30))}

def cohort(reg,start,end):
    if reg is None:return 'unknown_registration'
    if reg>end:return 'outside_window'
    return 'new' if reg>=start else 'old'

def platform(host,os=None,display=None):
    if host=='app' and os in ('Android','iOS'):return 'APP',os
    if host=='browser' and display=='browser':return 'H5','browser'
    if host in ('web','browser') and display=='installed_pwa':return 'PWA','installed_pwa'
    return 'unknown','unknown'

def ratio(n,d):return n/d if d else None

def normalize_bets(rows,as_of):
    latest={}
    for r in rows:
        if r['version_at']>as_of:continue
        key=(r['namespace'],r['bet_id'],r['asset'])
        previous=latest.get(key)
        if previous and r['version_at']==previous['version_at'] and r!=previous:
            raise ValueError('Conflicting versions require source arbitration')
        if not previous or r['version_at']>previous['version_at']:latest[key]=r
    result=[]
    for key,r in latest.items():
        if r['status'] not in ('accepted','settled','cancelled'):continue
        stake=Decimal(str(r['stake']));refund=Decimal(str(r['refund']))
        if not Decimal(0)<=refund<=stake:raise ValueError('Refund out of range')
        net=Decimal(0) if r['status']=='cancelled' else stake-refund
        payout=Decimal(str(r['payout'])) if r['status']=='settled' and r['payout'] is not None else None
        if r['status']=='settled' and payout is None:raise ValueError('Final payout missing')
        result.append({**r,'net_stake':net,'settled_stake':net if payout is not None else Decimal(0),'final_payout':payout})
    return result

def return_status(start_platform,provider,events):
    """Events must already match product/window/currency/asset and be effective bets."""
    same=any(p==start_platform and v==provider for p,v in events)
    cross=any(p not in (start_platform,None,'unknown') and v==provider for p,v in events)
    if same:return 'same_platform_provider',cross
    unknown=any(v in (None,'unknown') or (v==provider and p in (None,'unknown')) for p,v in events)
    if unknown:return 'unresolved',cross
    if cross:return 'cross_platform_provider_only',True
    if events:return 'other_providers_only',False
    return 'no_observed_bet',False

def eligible(start,n,cutoff,complete_days):
    observed=start+timedelta(days=n-1)
    if observed>cutoff:return 'immature'
    return 'eligible' if observed in complete_days else 'missing_observation_day'

def participation(providers):
    s=set(providers)
    if {'Tada','PP'}<=s:return 'both'
    if s & {None,'unknown'}:return 'unresolved'
    if 'Tada' in s:return 'tada_only'
    if 'PP' in s:return 'pp_only'
    return 'neither'

def paid_at(first_pay,event_time):return first_pay is not None and first_pay<=event_time

def first_bet_conversion(opens,bets):
    """Open ID is a certified link; ambiguous/no-link events are kept out of numerator."""
    successful={o['id']:o for o in opens if o['status']=='success'}
    converted=set()
    for b in bets:
        o=successful.get(b.get('open_id'))
        if o and o['user']==b['user'] and o['game']==b['game'] and o['start']<=b['time']<o['end']:
            converted.add(o['id'])
    return len(converted),len(successful)

def shapley_product(a,b):
    if len(a)!=4 or len(b)!=4 or any(x is None or x<=0 for x in a+b):return None
    def prod(xs):
        out=1
        for x in xs:out*=x
        return out
    contributions=[0.0]*4
    for order in permutations(range(4)):
        working=list(a);before=prod(working)
        for i in order:
            working[i]=b[i];after=prod(working);contributions[i]+=(after-before)/24;before=after
    return contributions
