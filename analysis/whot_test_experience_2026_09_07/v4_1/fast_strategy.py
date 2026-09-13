"""Deterministic visible-hand heuristic; legality stays in the rules/UI gate."""
from collections import Counter

ARMS=('first_legal_play','fast_connectivity_v1','fast_connectivity_v1_1')

def choose(hand,candidates,arm):
    if arm not in ARMS:raise ValueError('unknown_strategy')
    if not candidates:return None,['no_legal_candidate']
    if any(not any(c is h for h in hand) for c in candidates):raise ValueError('candidate_not_in_visible_hand')
    if arm=='first_legal_play':return candidates[0],['first_verified_legal']
    normal=[c for c in candidates if c['rank']!=20]
    pool=normal or candidates
    shapes=Counter(c['shape'] for c in hand)
    ranks=Counter(c['rank'] for c in hand)
    pairs=Counter((c['rank'],c['shape']) for c in hand)
    def connections(c):return shapes[c['shape']]+ranks[c['rank']]-pairs[(c['rank'],c['shape'])]-1
    if arm=='fast_connectivity_v1':
        chosen=max(pool,key=connections)  # max retains original order for ties.
        return chosen,['preserve_wild_if_normal_available','maximize_visible_followups',f'followups_{connections(chosen)}']
    chosen=max(pool,key=lambda c:(connections(c),-c['rank'],-hand.index(c)))
    return chosen,['preserve_wild_if_normal_available','maximize_visible_followups','lower_rank_proxy_tiebreak',f'followups_{connections(chosen)}']
