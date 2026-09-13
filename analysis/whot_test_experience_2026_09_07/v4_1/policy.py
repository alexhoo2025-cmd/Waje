"""6001 visible-state policy. No browser input or hidden-state access."""
from collections import Counter
from copy import deepcopy
import math

SHAPES={'circle','square','triangle','star','cross'}
ARMS=('first_legal_play','reduce_high_point_cards','retain_special_or_wild_cards_until_needed')

def valid(card):
    return isinstance(card,dict) and type(card.get('rank')) is int and (
        card['rank']==20 and card.get('shape') in ('whot','wild') or
        1<=card['rank']<=14 and card.get('shape') in SHAPES)

def decide(state,rules,arm,now_ms):
    def stop(reason): return {'action':'wait','reason':reason,'policy_version':'6001-v4.1'}
    if arm not in ARMS: return stop('unknown_arm')
    if state.get('route')!='/game/6001-whot' or str(state.get('client_game_id'))!='6001': return stop('wrong_game')
    if state.get('binding_verified') is not True: return stop('binding_unverified')
    if state.get('autoplay') is not False: return stop('control_unknown_or_auto')
    if state.get('action_owner')!='self': return stop('not_self_turn')
    timing=[state.get('captured_at_ms'),state.get('deadline_ms'),now_ms]
    if any(not isinstance(x,(int,float)) or not math.isfinite(x) for x in timing): return stop('timing_unknown')
    if not 0<=now_ms-timing[0]<=750 or now_ms+300>=timing[1]: return stop('expired')
    hand=state.get('visible_hand')
    if not isinstance(hand,list) or not hand or not all(valid(c) for c in hand): return stop('hand_unknown')
    if state.get('cards_verified') is not True: return stop('recognition_unverified')
    pending=state.get('pending_effect')
    if pending not in ('none','whot_shape_selection','draw_required','declare_last_card','catch_last_card'): return stop('unknown_effect')
    if pending!='none':
        if state.get('effect_window_verified') is not True or pending not in rules.get('verified_effects',[]): return stop('effect_unverified')
        out={'action':pending}
        if pending=='whot_shape_selection':
            counts=Counter(c['shape'] for c in hand if c['shape'] in SHAPES)
            out={'action':'select_shape','target_shape':max(sorted(SHAPES),key=lambda s:counts[s])}
    else:
        table=state.get('table_card')
        if not valid(table): return stop('table_unknown')
        shape=state.get('effective_shape') or table['shape']
        if table['rank']==20 and shape not in SHAPES:return stop('effective_shape_unknown')
        candidates=[i for i,c in enumerate(hand) if c['rank']==20 or c['rank']==table['rank'] or c['shape']==shape]
        if not candidates: out={'action':'draw','candidates':[]}
        else:
            chosen=candidates[0]
            if arm==ARMS[1]:
                points=rules.get('penalty_points',{})
                if rules.get('points_verified') is not True or any(f"{hand[i]['rank']}:{hand[i]['shape']}" not in points for i in candidates):return stop('points_unverified')
                chosen=max(candidates,key=lambda i:(points[f"{hand[i]['rank']}:{hand[i]['shape']}"],-i))
            if arm==ARMS[2]:
                special=set(rules.get('special_ranks',[]))|{20}
                normal=[i for i in candidates if hand[i]['rank'] not in special]
                blockers=[i for i in candidates if hand[i]['rank'] in rules.get('verified_blocking_ranks',[])]
                counts=state.get('opponent_visible_card_counts') or []
                urgent=any(type(n) is int and 1<=n<=2 for n in counts)
                chosen=(blockers if urgent and blockers else normal or candidates)[0]
            out={'action':'play','chosen_index':chosen,'chosen_card':hand[chosen],'candidates':candidates}
    out.update(policy_version='6001-v4.1',strategy_arm=arm,state_seq=state.get('state_seq'),expires_at_ms=timing[1]-300)
    return out

class PendingAction:
    def __init__(self):self.pending=None;self.used=set()
    def submit(self,action_id,state,decision,now_ms):
        seq=state.get('state_seq')
        if self.pending or type(seq) is not int or seq in self.used or decision.get('action')=='wait':return False
        if not action_id or decision.get('state_seq')!=seq:return False
        expiry=decision.get('expires_at_ms')
        if any(type(x) not in (int,float) or not math.isfinite(x) for x in (now_ms,expiry)):return False
        if now_ms>=expiry:return False
        self.pending=(action_id,deepcopy(state),deepcopy(decision));self.used.add(seq);return True
    def confirm(self,after):
        if self.pending is None:return None
        aid,before,d=self.pending
        seq=after.get('state_seq')
        if type(seq) is not int or seq<=before.get('state_seq'):return None
        if after.get('autoplay') is not False or after.get('cards_verified') is not True:return {'action_id':aid,'accepted':None}
        bag=lambda h:Counter((c['rank'],c['shape']) for c in h)
        old=before['visible_hand'];new=after.get('visible_hand')
        accepted=None
        if isinstance(new,list) and all(valid(c) for c in new):
            if d['action']=='play':
                expected=list(old);expected.pop(d['chosen_index'])
                accepted=bag(expected)==bag(new) and after.get('table_card')==d['chosen_card']
            elif d['action']=='draw': accepted=not (bag(old)-bag(new)) and len(new)==len(old)+1
        if d['action']=='select_shape':accepted=after.get('effective_shape')==d['target_shape'] and after.get('pending_effect')=='none'
        if accepted:self.pending=None
        return {'action_id':aid,'accepted':True if accepted else None}
    def unresolved(self):
        if not self.pending:return None
        aid=self.pending[0];self.pending=None
        return {'action_id':aid,'accepted':None,'reason':'confirmation_unresolved'}
