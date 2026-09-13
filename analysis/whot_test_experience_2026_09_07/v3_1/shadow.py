"""Offline visible-state feature ranking, never connected to live action selection."""
from collections import Counter
from lab import decide, ARMS


def rank_candidates(state,rules,at_ms):
    baseline=decide(state,rules,ARMS[0],at_ms)
    if baseline['action']!='play':return {'status':'not_actionable','candidates':[]}
    rows=[]
    for c in baseline['candidates']:
        remaining=list(state['visible_hand']);remaining.pop(c['index'])
        points=rules.get('points',{})
        if any(f"{x['rank']}:{x['shape']}" not in points for x in remaining):
            return {'status':'scoring_unverified','candidates':[]}
        shapes=Counter(x['shape'] for x in remaining if x['rank']!=rules['wild_rank'])
        ranks=Counter(x['rank'] for x in remaining)
        connections=sum(a['rank']==b['rank'] or a['shape']==b['shape'] for i,a in enumerate(remaining) for b in remaining[i+1:])
        # Counterfactual next move if the effective shape persists. This is
        # hand structure, not a prediction of an unseen opponent action.
        target_shape=(max(rules['shapes'],key=lambda s:(shapes[s],-rules['shapes'].index(s)))
                      if c['rank']==rules['wild_rank'] else c['shape'])
        followups=sum(x['rank']==rules['wild_rank'] or x['rank']==c['rank'] or x['shape']==target_shape
                      for x in remaining)
        next_count=state.get('next_opponent_visible_card_count')
        targeted_block=(next_count is not None and next_count<=2 and
                        c['rank'] in rules.get('blocking_ranks',[]) and
                        rules.get('blocking_target')=='next_player')
        rows.append({'card_index':c['index'],'remaining_points':sum(points[f"{x['rank']}:{x['shape']}"] for x in remaining),
                     'visible_connections':connections,'largest_shape_group':max(shapes.values(),default=0),
                     'specials_retained':sum(x['rank'] in rules.get('special_ranks',[]) for x in remaining),
                     'wins_by_empty_hand':not remaining,
                     'counterfactual_followups':followups,'target_shape':target_shape,
                     'verified_next_player_block':targeted_block,
                     'public_draw_observations':state.get('public_draw_observations',[]),
                     'hypothesis_only':True})
    rows.sort(key=lambda x:(not x['wins_by_empty_hand'],not x['verified_next_player_block'],
                           x['remaining_points'],-x['counterfactual_followups'],
                           -x['visible_connections'],x['card_index']))
    return {'status':'shadow_only','candidates':rows,'note':'Descriptive features, not trained win probabilities; never uses hidden cards.'}
