"""Compare fixed policies on identical visible frames. No live clicks."""
from collections import Counter
from policy import decide,ARMS

def evaluate(state,rules,now_ms):
    arms={arm:decide(state,rules,arm,now_ms) for arm in ARMS}
    baseline=arms[ARMS[0]]
    if baseline.get('action')!='play':return {'arms':arms,'shadow':None,'reason':baseline.get('reason','not_card_action')}
    hand=state['visible_hand'];points=rules.get('penalty_points',{})
    if rules.get('points_verified') is not True or any(f"{c['rank']}:{c['shape']}" not in points for c in hand):
        return {'arms':arms,'shadow':None,'reason':'penalty_map_unverified'}
    scores=[]
    for index in baseline['candidates']:
        remaining=hand[:index]+hand[index+1:];chosen=hand[index]
        penalty=sum(points[f"{c['rank']}:{c['shape']}"] for c in remaining)
        shapes=Counter(c['shape'] for c in remaining)
        connected=sum(c['rank']==20 or c['rank']==chosen['rank'] or c['shape']==chosen['shape'] for c in remaining)
        # Transparent lexicographic candidate, not learned optimal weights.
        score=(-penalty,connected,max(shapes.values(),default=0),-index)
        scores.append({'index':index,'score':score,'remaining_penalty':penalty,'next_connections':connected})
    best=max(scores,key=lambda x:x['score'])
    return {'arms':arms,'shadow':{'chosen_index':best['index'],'candidates':scores,'policy_version':'offline-lexicographic-1'},
            'reason':'shadow_only_not_strategy_assignment'}
