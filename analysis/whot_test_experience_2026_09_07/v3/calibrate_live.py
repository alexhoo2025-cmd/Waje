"""Bounded, DAU-1-only visual calibration; never counts as formal samples.

Reads masked pixel ROIs. A conservative observed-rule policy can be exercised
with --play after reviewing the first frame. All predictions remain unverified
until the holdout replay and controlled pilots pass.
"""
import argparse
import re
import json
import time
import uuid
from pathlib import Path
from controller import Native
from lab import ROOT, digest, now

REGIONS={
    'title':[.38,.07,.24,.15],
    'rewards':[.43,.30,.065,.24],
    'points':[.545,.30,.05,.24],
    'turn':[.37,.62,.27,.105],
    'autoplay':[.35,.47,.32,.14],
    'hand':[.23,.745,.57,.25],
    'table':[.558,.375,.091,.245],
    'stake':[.435,.465,.125,.075],
    'opponent_count':[.44,.05,.029,.066]
}


def texts(region):return ' '.join(t['value'] for t in region.get('text',[])).upper()


def compact(frame):
    return dict(native_ms=frame['native_ms'],width=frame['width'],height=frame['height'],
                regions={k:{n:x for n,x in v.items() if n!='feature'} for k,v in frame['regions'].items()})


def redact_title(frame):
    region=frame['regions'].get('title',{})
    region['text']=[x for x in region.get('text',[]) if x['value'].strip().upper() in ('USHINDI','SHINDWA','WHOT')]
    region['numbers']=[]


SHAPE_POINTS={
    # Normalized to the Cocos canvas (the browser toolbar is excluded). These
    # are calibration points captured from the visible five-segment WHOT
    # selector; they are never used unless a preceding WHOT play opened it.
    'circle':[.27,.38], 'cross':[.36,.38], 'square':[.23,.54],
    'triangle':[.39,.54], 'star':[.31,.65]
}


def choose_shape(hand):
    counts={k:0 for k in SHAPE_POINTS}
    for c in hand:
        if c.get('shape') in counts:counts[c['shape']]+=1
    return max(counts,key=lambda s:(counts[s],-list(SHAPE_POINTS).index(s)))


def candidate(regions,shape_ready=False):
    if 'ZAMU YAKO' not in texts(regions.get('turn',{})):return None
    # The run loop classifies the visible automatic-play overlay only after it
    # has attempted to derive a complete manual action. This prevents the
    # 6001 instructional overlay from masking a valid turn at startup.
    hand=regions.get('hand',{}).get('cards',[]);table=regions.get('table',{}).get('cards',[])
    if len(table)!=1 or not hand or any(c['shape']=='unknown' for c in hand+table):
        return {'action':'stop','reason':'card_recognition_unresolved'}
    if any(c['confidence']<.98 for c in hand+table):return {'action':'stop','reason':'rank_confidence'}
    top=table[0]
    if top['rank']==2:return {'action':'stop','reason':'special_state_requires_calibration'}
    if top['rank']==20:
        if not shape_ready:return {'action':'stop','reason':'special_state_requires_calibration'}
        target=choose_shape(hand)
        return {'action':'select_shape','target_shape':target,'point':SHAPE_POINTS[target],
                'reason':'visible_whot_selector_majority_shape'}
    legal=[c for c in hand if c['rank']==20 or c['rank']==top['rank'] or c['shape']==top['shape']]
    if not legal:
        return {'action':'draw','point':[.396,.47],'reason':'observed_matching_rule_no_legal_card'}
    return {'action':'play','point':legal[0]['point'],'chosen':legal[0],
            'reason':'first_observed_legal_card','legal_count':len(legal)}


def run(native,outdir,seconds,play,auto_dau1=False):
    windows=[w for w in native.call(op='status')['windows'] if w['bounds']['Height']>300]
    if len(windows)!=1:raise ValueError('ambiguous_window')
    w=windows[0];info=native.call(op='inspect',pid=w['pid'])
    if info['origin']!='https://test-h5.wajew.com' or info['path']!='/game/6001-whot' or info['standalone']:
        raise ValueError('wrong_game_route')
    # The terminal/agent can briefly steal focus between the route check and
    # the first frame. Re-activate the already verified Chrome process once;
    # never switch tabs or navigate here.
    if not info['foreground']:
        for _ in range(3):
            native.call(op='activate_process',pid=w['pid'])
            time.sleep(.20)
            info=native.call(op='inspect',pid=w['pid'])
            if info['foreground']:break
    if not info['foreground']:raise ValueError('bound_chrome_not_foreground')
    canvas=info['content_bounds']
    end=time.monotonic()+seconds;count=0;last=None;pending_fp=None;pending_at=0;pending_change_frames=0;observed_stake=False;uncertain=0;wild_pending=False;room_selected=not auto_dau1
    outdir.mkdir(parents=True,exist_ok=False)
    with (outdir/'observations.jsonl').open('x') as log:
        def record(row):
            log.write(json.dumps(dict(observed_at=now(),**row),ensure_ascii=False)+'\n');log.flush()
        record({'type':'start','calibration_only':True,'play_enabled':play,'game':'6001','canvas':canvas})
        while time.monotonic()<end:
            t=time.monotonic();info=native.call(op='inspect',pid=w['pid'])
            next_canvas=info.get('content_bounds')
            # A tab focus/toolbar transition can change only the web viewport
            # height. Re-anchor normalized ROIs once when the same verified
            # Chrome window and route remain in place; stop on a real window or
            # horizontal surface change so coordinates can never drift.
            if next_canvas and canvas:
                try:
                    dx=abs(float(next_canvas[0])-float(canvas[0]));dy=abs(float(next_canvas[1])-float(canvas[1]))
                    dw=abs(float(next_canvas[2])-float(canvas[2]))/max(float(canvas[2]),1.0)
                    dh=abs(float(next_canvas[3])-float(canvas[3]))/max(float(canvas[3]),1.0)
                except (TypeError,ValueError,IndexError):
                    dx=dy=dw=dh=999.0
                if dx>8 or dy>8 or dw>0.03 or dh>0.18:
                    record({'type':'stop','reason':'surface_changed'});break
                if next_canvas!=canvas:
                    record({'type':'surface_reanchored','from':canvas,'to':next_canvas})
                    canvas=next_canvas
            if not info['foreground'] or info['path']!='/game/6001-whot':
                record({'type':'stop','reason':'surface_changed'});break
            f=native.call(op='capture',window_id=w['id'],bounds=w['bounds'],screen_rect=canvas,crop=[0,0,1,1],regions=REGIONS)
            redact_title(f)
            c=compact(f);regions=f['regions'];semantic=digest(c['regions'])
            fingerprint=digest({'hand':[(x['rank'],x['shape']) for x in regions['hand'].get('cards',[])],
                                'table':[(x['rank'],x['shape']) for x in regions['table'].get('cards',[])]})
            if semantic!=last:
                record({'type':'frame','frame':c});count+=1;last=semantic
                print(json.dumps({'frame':count,'ms':f['native_ms'],'turn':texts(regions['turn']),
                    'cards':[(x['rank'],x['shape']) for x in regions['hand'].get('cards',[])],
                    'table':[(x['rank'],x['shape']) for x in regions['table'].get('cards',[])],
                    'title':texts(regions['title'])}),flush=True)
            if 'SHINDWA' in texts(regions['title']) or 'USHINDI' in texts(regions['title']):
                record({'type':'settlement_observed','values':regions['rewards']['text'],'points':regions['points']['text']});break
            if auto_dau1 and not room_selected:
                # The 6001 room picker is a stable, visible Cocos surface. A
                # lobby frame has the WHOT title but no hand/table cards; click
                # only the normalized DAU-1 button once, then verify the next
                # frames contain a deal before any strategy action.
                if 'WHOT' in texts(regions.get('title',{})) and not regions.get('hand',{}).get('cards') and not regions.get('table',{}).get('cards'):
                    info=native.call(op='inspect',pid=w['pid']);current_canvas=info.get('content_bounds') or canvas
                    if info.get('foreground') and info.get('path')=='/game/6001-whot':
                        point=[current_canvas[0]+.273*current_canvas[2],current_canvas[1]+.389*current_canvas[3]]
                        native.call(op='click',window_id=w['id'],bounds=w['bounds'],point=point,canvas_screen=current_canvas)
                        record({'type':'dau1_lobby_click','point_norm':[.273,.389],'reason':'verified_6001_room_picker'})
                        room_selected=True;canvas=current_canvas;continue
            if auto_dau1 and room_selected and (regions.get('hand',{}).get('cards') or regions.get('table',{}).get('cards')):
                record({'type':'deal_observed_after_dau1','hand_count':len(regions.get('hand',{}).get('cards',[])),
                        'table_count':len(regions.get('table',{}).get('cards',[]))})
            # A card animation can briefly expose an intermediate hand. Hold
            # one pending action until two consecutive frames show a changed
            # state; this prevents duplicate clicks and keeps each click
            # one-to-one with a visible state transition.
            if pending_fp is not None:
                if fingerprint != pending_fp:
                    pending_change_frames += 1
                    if pending_change_frames >= 2:
                        record({'type':'action_state_changed','from_fingerprint':pending_fp,
                                'to_fingerprint':fingerprint,'confirmation_frames':pending_change_frames})
                        pending_fp=None;pending_at=0;pending_change_frames=0
                else:
                    pending_change_frames=0
                    if time.monotonic()-pending_at>1.5:
                        record({'type':'stop','reason':'action_unconfirmed'});break
                if pending_fp is not None:
                    last=semantic
                    time.sleep(max(0,.125-(time.monotonic()-t)))
                    continue
            stake_text=texts(regions['stake']).replace(' ','')
            if re.fullmatch(r'(DAU|AU|U):?1',stake_text):observed_stake=True
            table_cards=regions.get('table',{}).get('cards',[])
            # The selector is rendered on top of the same instructional text
            # (“Cheza kadi kiotomatiki”). A just-played WHOT waiting for a
            # target shape remains a valid manual action window.
            selector_visible=wild_pending and len(table_cards)==1 and table_cards[0].get('rank')==20
            action=candidate(regions,shape_ready=wild_pending)
            # If the game reports the automatic-play overlay but we also have a
            # complete, confident, actionable hand, try the action first. This
            # is the only way to beat the five-second handoff window; an
            # overlay without a valid action is still rejected as mixed play.
            if 'KIOTOMATIKI' in texts(regions['autoplay']) and not selector_visible and not (action and action.get('action') in ('play','draw')):
                record({'type':'stop','reason':'mixed_auto_play'});break
            if play and action:
                if action['action']=='stop':
                    uncertain+=1
                    if uncertain<2 and action['reason']=='card_recognition_unresolved':
                        record({'type':'rescan','reason':action['reason']});continue
                    if action['reason']=='card_recognition_unresolved':
                        evidence=native.call(op='capture',window_id=w['id'],bounds=w['bounds'],screen_rect=canvas,crop=[0,0,1,1],
                            regions={'hand':REGIONS['hand'],'table':REGIONS['table']},
                            save_prefix=str(ROOT/'captures'/('unresolved-'+uuid.uuid4().hex)))
                        record({'type':'unresolved_card_evidence','frame':compact(evidence)})
                    record({'type':'stop',**action});break
                uncertain=0
                if not observed_stake:record({'type':'stop','reason':'dau_1_not_verified'});break
                if time.monotonic()-t>.75:
                    record({'type':'stale_frame_rejected'});continue
                info=native.call(op='inspect',pid=w['pid'])
                current_canvas=info.get('content_bounds')
                if not info['foreground'] or info['path']!='/game/6001-whot' or not current_canvas:break
                try:
                    dx=abs(float(current_canvas[0])-float(canvas[0]));dy=abs(float(current_canvas[1])-float(canvas[1]))
                    dw=abs(float(current_canvas[2])-float(canvas[2]))/max(float(canvas[2]),1.0)
                    dh=abs(float(current_canvas[3])-float(canvas[3]))/max(float(canvas[3]),1.0)
                except (TypeError,ValueError,IndexError):
                    dx=dy=dw=dh=999.0
                if dx>8 or dy>8 or dw>0.03 or dh>0.18:break
                if current_canvas!=canvas:canvas=current_canvas
                point=[canvas[0]+action['point'][0]*canvas[2],canvas[1]+action['point'][1]*canvas[3]]
                native.call(op='click',window_id=w['id'],bounds=w['bounds'],point=point,canvas_screen=canvas)
                record({'type':'action_submitted','action':action,'observation_to_submit_ms':(time.monotonic()-t)*1000,
                        'accepted':None,'quality':'uncertified_calibration'})
                if action['action']=='select_shape':wild_pending=False
                elif action['action']=='play' and action.get('chosen',{}).get('rank')==20:wild_pending=True
                pending_fp=fingerprint;pending_at=time.monotonic();pending_change_frames=0
            time.sleep(max(0,.125-(time.monotonic()-t)))
        record({'type':'end','distinct_observation_records':count,'formal_samples_added':0})


def main():
    p=argparse.ArgumentParser();p.add_argument('--seconds',type=int,default=20);p.add_argument('--play',action='store_true')
    p.add_argument('--auto-dau1',action='store_true',help='click the verified 6001 lobby DAU-1 button once')
    p.add_argument('--output',type=Path,default=ROOT/'calibration_runs'/str(uuid.uuid4()));a=p.parse_args()
    n=Native('/tmp/whot-native-v3')
    try:run(n,a.output,a.seconds,a.play,a.auto_dau1)
    finally:n.close()


if __name__=='__main__':main()
