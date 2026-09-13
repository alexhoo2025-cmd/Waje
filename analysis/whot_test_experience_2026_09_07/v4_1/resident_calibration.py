"""Experimental BET1 visible-pixel calibration, one session, no automatic lobby clicks.

Stops on autoplay, unknown confirmation, changed binding or budget expiry.
No model calls or report generation in the action loop. Native input requires --execute.
"""
import argparse,json,time,uuid,hashlib,re
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
from native_session import Session
from start_low_room import start_in_session
from same_room import submit as submit_same_room
from fast_strategy import choose as choose_strategy,ARMS as FAST_ARMS
from start_existing_bet import start1000,start2000,start5000

ROOT=Path(__file__).resolve().parent
PICKER_REGIONS={'pick_cross':[.32532,.32664,.0648,.104],
                'pick_triangle':[.348,.4868,.0756,.104],
                'pick_star':[.27024,.5856,.0756,.1118]}
def picker_verified(regions):
    return all(regions.get('pick_'+shape,{}).get('shape')==shape for shape in ('cross','triangle','star'))
def picker_target(hand):
    # Calibration supports three independently visible targets; no guessed
    # circle/square coordinates. This is not a certified strategy experiment.
    counts=Counter(c['shape'] for c in hand)
    return max(('cross','triangle','star'),key=lambda shape:counts[shape])
REGIONS={'hand':[.22,.775,.58,.22],'table':[.575,.39,.10,.22],
         'turn':[.33,.635,.36,.065],'effect':[.28,.22,.40,.40],
         'title':[.30,.08,.4,.15],'bet':[.43,.475,.14,.06],'indicator':[.56,.436,.072,.108],'raised':[.22,.735,.58,.23],'round':[.10,.34,.14,.10],'draw_prompt':[.325,.255,.105,.115]}
def text(region):return ' '.join(' '.join(t['value'] for t in region.get('text',[])).split()).upper()
def round_hash(region):
    value=text(region)
    return hashlib.sha256(value.encode()).hexdigest() if re.fullmatch(r'\d{6}',value) else None
def valid_numeric(value,signed=False):
    prefix=r'[+\-]' if signed else r'[+\-]?'
    return re.fullmatch(prefix+r'(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?',value.strip()) is not None

def settlement_outcome(title,effect,regions):
    """Classify the player's result even when the wide Canvas title OCR is weak."""
    if 'VICTORY' in title:return 'win'
    if 'DEFEAT' in title or 'LOSE' in title:return 'loss'
    signed=[v['value'].strip() for v in regions.get('effect',{}).get('text',[]) if valid_numeric(v.get('value',''),signed=True)]
    if signed:
        return 'win' if signed[0].startswith('+') else 'loss'
    return 'unknown'

def observe_settlement(s,w,binding,emit,expected_round=None,seconds=150,expected_bet=1,fast=False):
    """Read-only tail; does not recover control or submit input."""
    end=time.monotonic()+seconds
    previous=None;stable=0;terminal_started=None
    regions={'title':[.30,.08,.4,.17],'bet':[.43,.475,.14,.06],
             'returns':[.40,.30,.13,.30],'points':[.55,.30,.06,.30],
             'round':[.10,.34,.14,.10]}
    while time.monotonic()<end:
        b=s.call('inspect',pid=w['pid'],window_id=w['id'])
        if b.get('origin')!=binding['origin'] or b.get('path')!=binding['path'] or b.get('content_bounds')!=binding['content_bounds']:
            emit('settlement_tail_stopped',reason='binding_changed');return
        f=s.call('capture',window_id=w['id'],bounds=w['bounds'],screen_rect=binding['content_bounds'],crop=[0,0,1,1],allow_background_capture=True,regions=regions)
        r=f['regions'];bet=re.fullmatch(r'BET\s*:?\s*(\d+)',text(r['bet']))
        if bet and int(bet[1])!=expected_bet:emit('settlement_tail_stopped',reason='unexpected_bet',observed_bet=int(bet[1]));return
        current_round=round_hash(r['round'])
        if expected_round and current_round and current_round!=expected_round:
            emit('settlement_tail_stopped',reason='different_round');return
        title=text(r['title'])
        if any(label in title for label in ('VICTORY','LOSE','DEFEAT')):
            values={name:[{'value':v['value'],'box':v.get('box')} for v in r[name].get('text',[]) if valid_numeric(v['value'],signed=name=='returns')] for name in ('returns','points')}
            signature=json.dumps([title,[[v['value'] for v in values[name]] for name in ('returns','points')]])
            stable=stable+1 if signature==previous else 1;previous=signature
            if terminal_started is None:terminal_started=time.monotonic()
            complete=len(values['returns'])==2
            if fast or (stable>=2 and complete) or time.monotonic()-terminal_started>=5:
                emit('settlement_capture',result='win' if 'VICTORY' in title else 'loss',numeric_evidence=values,public_round_hash=expected_round,read_only=True,numeric_status='complete' if complete and stable>=2 else 'partial',stable_frames=stable);return
        time.sleep(.4)
    emit('settlement_tail_stopped',reason='deadline')
def pair(c):return c['rank'],c['shape']
def client_enabled(c):return c.get('ink_red',0)>=210
def draw_delta_accepted(before,after,expected):
    delta=sum(after.values())-sum(before.values())
    return not(before-after) and (delta==expected if expected is not None else delta in (1,2))
def trusted(c):
    return c.get('rank') in list(range(1,15))+[20] and c.get('shape') in ('circle','square','triangle','star','cross','wild') and c.get('rank_score',0)>=.82 and (c.get('rank')==20 or c.get('shape_evidence',{}).get('marker_consistent') is True)

def effects(raw):
    # Numeric OCR on the table is not a new action state. Only rule-state labels
    # belong in the stable-state fingerprint; retain the detected labels in logs.
    return tuple(k for k in ('PICK','MATCH SYMBOL','SUSPENSION','HOLD ON','LAST CARD','GENERAL MARKET') if k in raw)

def forced_draw_count(raw):
    return 2 if re.search(r'\bPICK\s+2\b',raw) and effects(raw)==('PICK',) else None

def signature_for(hand,table,owner,effect):
    return json.dumps([[(c.get('rank'),c.get('shape')) for c in hand],[(c.get('rank'),c.get('shape')) for c in table],owner,effects(effect)],sort_keys=True)

def selected_ready(pending,hand,raised,table,owner,effective=None):
    table_matches=len(table)==1 and trusted(table[0]) and pair(table[0])==pending.get('table_before')
    requested=pending.get('effective_before')
    overlay_matches=requested in ('circle','square','triangle','cross','star') and effective==requested
    if not (pending['action']=='play' and not pending.get('committed') and owner and len(raised)==1 and trusted(raised[0]) and pair(raised[0])==pending['chosen'] and (table_matches or overlay_matches)):return False
    expected=Counter(pending['hand']);expected.subtract([pending['chosen']])
    return +expected==Counter(pair(c) for c in hand) and all(trusted(c) for c in hand)

def selected_hand_complete(region,raised):
    """Only discount one bright symbol contained in a verified raised card.

    Ordinary action readiness remains strict. The caller separately requires an
    exact remaining-hand multiset and the selected card's original identity.
    Coordinates refer to the calibrated full canvas, not a cropped image.
    """
    cards=region.get('cards',[]);numbers=region.get('numbers',[])
    if region.get('number_group_count')==len(cards):return True
    if len(raised)!=1 or not trusted(raised[0]):return False
    box=raised[0].get('box')
    if not box or len(box)!=4:return False
    unknown=[n for n in numbers if n.get('rank') is None]
    if len(numbers)!=len(cards)+1 or len(unknown)!=1:return False
    n=unknown[0];b=n.get('box')
    return bool(b and len(b)==4 and n.get('ink_red',0)>=210
                and box[0]-.005<=b[0] and b[0]+b[2]<=box[0]+.095
                and b[1]>=box[1]+box[3] and b[1]+b[3]<=box[1]+.14)

def wait_for_occluded_confirmation(pending,hand,hand_complete,table_complete,elapsed_ms):
    """Bounded read-only grace after a committed card visibly left the hand.

    This is not acceptance and never authorizes another click. Unknown table
    pixels during effect animation must resolve before the action is accepted.
    """
    if not(pending.get('committed') and pending['action']=='play' and
           hand_complete and not table_complete and elapsed_ms<5000 and
           all(trusted(c) for c in hand)):return False
    expected=Counter(pending['hand']);expected.subtract([pending['chosen']])
    return +expected==Counter(pair(c) for c in hand)

def play_hand_delta_with_raised_accepted(pending,hand,raised,hand_complete):
    """Accept a play while the centre-card animation still covers the table.

    On the old Canvas client the selected card can leave the hand before the
    table card is repainted.  The previous confirmer required a changed table
    card and therefore turned an already accepted play into an unknown result.
    An exact one-card multiset delta plus a trusted raised copy of that same
    card is sufficient evidence that the submitted play was accepted; it
    never authorizes another click.
    """
    if not (pending.get('action') == 'play'
            and hand_complete and all(trusted(c) for c in hand)
            and len(raised) == 1 and trusted(raised[0])):
        return False
    chosen = pending.get('chosen')
    if not chosen or pair(raised[0]) != tuple(chosen):
        return False
    expected = Counter(pending.get('hand', []))
    expected.subtract([tuple(chosen)])
    return +expected == Counter(pair(c) for c in hand)

def transition_ready(wait,owner,flags,stable):
    if not owner:wait['away_frames']+=1
    if flags:
        wait['effect_seen']|=any(x in ('HOLD ON','SUSPENSION','GENERAL MARKET') for x in flags)
        if wait.get('request_satisfied') and 'MATCH SYMBOL' in flags:wait['request_overlay_seen']=True
        wait['clear_frames']=0
    else:wait['clear_frames']+=1
    request_resolved=wait.get('request_satisfied') and wait.get('request_overlay_seen')
    return owner and stable>=2 and wait['clear_frames']>=2 and (wait['away_frames']>=2 or wait['effect_seen'] or request_resolved)

def accumulate_pending_turn(pending,owner):
    # Turn changes can occur before the final hand animation confirms a draw.
    # Preserve those observed frames rather than resetting to only the last one.
    pending['observed_away_frames']=pending.get('observed_away_frames',0)+(0 if owner else 1)
    return pending['observed_away_frames']

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');ap.add_argument('--quiet',action='store_true');ap.add_argument('--probe-wild',action='store_true');ap.add_argument('--start-bet1',action='store_true');ap.add_argument('--recover-existing',action='store_true');ap.add_argument('--seconds',type=int,default=120)
    ap.add_argument('--expected-bet',type=int,choices=(1,100,200,500,1000,2000,5000),default=1)
    ap.add_argument('--continuous',action='store_true');ap.add_argument('--max-settlements',type=int,default=3)
    ap.add_argument('--match-timeout',type=int,default=45)
    ap.add_argument('--strategy',choices=FAST_ARMS,default='first_legal_play')
    ap.add_argument('--recover-autoplay',action='store_true')
    ap.add_argument('--start-bet1000',action='store_true')
    ap.add_argument('--start-bet2000',action='store_true')
    ap.add_argument('--start-bet5000',action='store_true')
    args=ap.parse_args()
    if args.start_bet1 and args.expected_bet!=1:ap.error('start-bet1 requires expected-bet 1')
    if args.start_bet1000 and (not args.execute or args.expected_bet!=1000 or args.start_bet1 or args.start_bet2000 or args.recover_existing):ap.error('invalid BET1000 entry configuration')
    if args.start_bet2000 and (not args.execute or args.expected_bet!=2000 or args.start_bet1 or args.start_bet1000 or args.start_bet5000 or args.recover_existing):ap.error('invalid BET2000 entry configuration')
    if args.start_bet5000 and (not args.execute or args.expected_bet!=5000 or args.start_bet1 or args.start_bet1000 or args.start_bet2000 or args.recover_existing):ap.error('invalid BET5000 entry configuration')
    if not 1<=args.max_settlements<=10:ap.error('max-settlements must be 1..10')
    if not 5<=args.match_timeout<=300:ap.error('match-timeout must be 5..300 seconds')
    if args.start_bet1 and (not args.execute or args.recover_existing):ap.error('start-bet1 requires execute and cannot combine with recovery')
    sid='native-'+uuid.uuid4().hex[:10];log=ROOT/(sid+'.jsonl');s=Session(args.execute)
    pending=None;last_signature=None;stable=0;used=set();seen_game=False;turn_start=None;previous_owner=False;actions=0;recovered=False;bet_verified=False;focus_recoveries=0;await_turn=None;picker_probe_until=None;observed_round=None
    match_seq=1;settlements=0;settlement_latched=False;joining_existing=True
    recovery_pending=None;recovery_clear_frames=0
    initial_entry_registered=False;matching_started_at=None
    bet_mismatch_frames=0
    with log.open('x') as output:
        def emit(kind,**fields):
            output.write(json.dumps(dict(kind=kind,session_id=sid,match_seq=match_seq,expected_bet=args.expected_bet,strategy_version=args.strategy,at=datetime.now(timezone.utc).isoformat(),monotonic_ms=time.monotonic()*1000,**fields))+'\n');output.flush()
        try:
            status=s.call('status');ws=[w for w in status['windows'] if w['bounds']['Height']>300]
            matches=[]
            for candidate in ws:
                try:observed=s.call('inspect',pid=candidate['pid'],window_id=candidate['id'])
                except RuntimeError:continue
                if observed.get('origin')=='https://test-h5.wajetan.com' and observed.get('path')=='/game/6001-whot':matches.append((candidate,observed))
            if len(matches)!=1:raise RuntimeError('test_window_not_unique')
            w,binding=matches[0]
            aspect=binding['content_bounds'][2]/binding['content_bounds'][3]
            # Chrome may expose a wider, non-fullscreen viewport on a second
            # display. The Cocos layout uses normalized coordinates, so retain
            # the safe aspect band while recording the actual value.
            if not 1.55<=aspect<=2.0:raise RuntimeError('uncalibrated_aspect')
            def check(b):
                return b.get('origin')=='https://test-h5.wajetan.com' and b.get('path')=='/game/6001-whot' and not b.get('standalone') and b.get('content_bounds')==binding.get('content_bounds')
            if not check(binding):raise RuntimeError('wrong_route')
            if args.execute:
                s.call('focus_test_window',pid=w['pid'],window_id=w['id'])
                stable_since=time.monotonic();preflight_end=stable_since+6
                while time.monotonic()<preflight_end:
                    status=s.call('status')
                    current_window=next((item for item in status['windows'] if item['id']==w['id']),None)
                    if current_window is None:raise RuntimeError('preflight_window_missing')
                    current_binding=s.call('inspect',pid=w['pid'],window_id=w['id'])
                    if current_binding.get('origin')!='https://test-h5.wajetan.com' or current_binding.get('path')!='/game/6001-whot' or current_binding.get('standalone'):raise RuntimeError('preflight_scope_changed')
                    if current_window['bounds']!=w['bounds'] or current_binding.get('content_bounds')!=binding.get('content_bounds'):
                        emit('preflight_geometry_changed',old_bounds=w['bounds'],new_bounds=current_window['bounds'])
                        w=current_window;binding=current_binding;stable_since=time.monotonic()
                    if time.monotonic()-stable_since>=1.2:break
                    time.sleep(.1)
                else:raise RuntimeError('preflight_geometry_unstable')
                aspect=binding['content_bounds'][2]/binding['content_bounds'][3]
                if not 1.55<=aspect<=2.0:raise RuntimeError('uncalibrated_aspect_after_focus')
            emit('start',input_enabled=args.execute,vision_regions=REGIONS,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),binary_sha256=hashlib.sha256((ROOT/'native_fast').read_bytes()).hexdigest())
            stop=time.monotonic()+min(args.seconds,1800 if args.continuous else 300)
            warm=False;frame_no=0
            while time.monotonic()<stop:
                b=s.call('inspect',pid=w['pid'],window_id=w['id'])
                if not check(b):raise RuntimeError('binding_changed')
                started=time.monotonic()*1000
                regions=dict(REGIONS)
                if args.probe_wild and (picker_probe_until is not None or (pending and pending['action']=='choose_shape')):
                    regions['picker']=[.24,.18,.54,.52]
                    regions.update(PICKER_REGIONS)
                material={}
                if frame_no%2==0:
                    material=dict(save_prefix=str(ROOT.parent/'v3_1'/'captures'/f'{sid}-{frame_no:05d}'),save_regions=['hand','table','turn','effect','raised']+(['picker'] if args.probe_wild else []))
                f=s.call('capture',window_id=w['id'],bounds=w['bounds'],screen_rect=binding['content_bounds'],crop=[0,0,1,1],allow_background_capture=True,regions=regions,**material)
                frame_no+=1
                received=time.monotonic()*1000;r=f['regions'];elapsed=received-started
                frame_round=round_hash(r.get('round',{}))
                if observed_round and frame_round and frame_round!=observed_round and not settlement_latched:raise RuntimeError('different_round')
                if frame_round:observed_round=frame_round
                title=text(r['title']);turn=text(r['turn']);effect=text(r['effect']);bet=text(r['bet'])
                forced=forced_draw_count(effect)
                draw_prompt=r.get('draw_prompt',{}).get('verified') is True
                hand=r['hand'].get('cards',[]);table=r['table'].get('cards',[])
                raised=r.get('raised',{}).get('cards',[])
                hand_complete=r['hand'].get('number_group_count')==len(hand)
                table_complete=r['table'].get('number_group_count')==len(table)
                raised_complete=r.get('raised',{}).get('number_group_count')==len(raised)
                owner='YOUR TURN' in turn
                auto='AUTOMATICALLY' in effect or 'TOUCH THE SCREEN' in effect
                # On the wide Chrome layout the large result banner can be
                # missed by OCR, while the result rows remain visible in the
                # effect ROI. Require the full settlement header before using
                # that fallback so ordinary play is not misclassified.
                settlement_header=all(marker in effect for marker in ('BALANCE','POINTS','CARDS LEFT'))
                terminal='VICTORY' in title or 'DEFEAT' in title or 'LOSE' in title or settlement_header
                indicator=r.get('indicator',{}).get('shape_evidence',{})
                effective=indicator.get('shape') if 'MATCH SYMBOL' in effects(effect) else None
                overlay_verified=effective in ('triangle','circle','square','cross','star')
                signature=signature_for(hand,table,owner,effect)+str(effective)
                stable=stable+1 if signature==last_signature else 1;last_signature=signature
                if owner and not previous_owner:turn_start=started
                previous_owner=owner
                emit('frame',capture_seq=f.get('capture_seq'),capture_ms=elapsed,frame_age_ms=f.get('frame_age_ms'),owner=owner,autoplay=auto,terminal=terminal,
                     hand=[{'rank':c.get('rank'),'shape':c.get('shape'),'rank_similarity':c.get('rank_score'),'ink_red':c.get('ink_red'),'client_enabled':client_enabled(c),'point':c.get('point')} for c in hand],
                     table=[{'rank':c.get('rank'),'shape':c.get('shape'),'rank_similarity':c.get('rank_score'),'marker_votes':c.get('shape_evidence',{}).get('marker_votes'),'trusted':trusted(c)} for c in table],
                     stable_frames=stable,hand_trusted=[trusted(c) for c in hand],hand_complete=hand_complete,table_complete=table_complete,effect_flags=effects(effect),effective_shape=effective,draw_prompt=draw_prompt,raised=[{'rank':c.get('rank'),'shape':c.get('shape'),'trusted':trusted(c)} for c in raised],material_prefix=material.get('save_prefix'))
                if not warm:
                    warm=True
                    if args.start_bet1 or args.start_bet1000 or args.start_bet2000 or args.start_bet5000:
                        receipt=start1000(s,w,binding) if args.start_bet1000 else (start2000(s,w,binding) if args.start_bet2000 else (start5000(s,w,binding) if args.start_bet5000 else start_in_session(s,w,binding)))
                        emit('entry_submitted',receipt=receipt)
                        matching_started_at=time.monotonic()
                        joining_existing=False
                        if not args.quiet:print(json.dumps({'status':'entry_submitted','log':str(log),'input_enabled':args.execute}),flush=True)
                        continue
                    if not args.quiet:print(json.dumps({'status':'ready','log':str(log),'input_enabled':args.execute}),flush=True)
                immediate_bet=re.fullmatch(r'BET\s*:?\s*(\d+)',bet)
                if immediate_bet and int(immediate_bet[1])!=args.expected_bet:
                    bet_mismatch_frames+=1
                    emit('bet_observation_mismatch',observed_bet=int(immediate_bet[1]),consecutive_frames=bet_mismatch_frames)
                    # OCR can expose a truncated digit during settlement/entry
                    # animation. Stop only after stable contradictory frames.
                    if bet_mismatch_frames >= (3 if bet_verified else 2):
                        emit('scope_violation',observed_bet=int(immediate_bet[1]),stable_frames=bet_mismatch_frames);raise RuntimeError('unexpected_bet')
                elif immediate_bet and int(immediate_bet[1])==args.expected_bet:
                    bet_mismatch_frames=0
                if auto:
                    if args.execute and args.recover_autoplay:
                        if recovery_pending is not None:
                            if received-recovery_pending>3000:raise RuntimeError('autoplay_recovery_unconfirmed')
                            continue
                        if pending:
                            emit('action_terminal',action_id=pending['id'],accepted=None,reason='autoplay_interruption');pending=None
                        # Dismissing the explicitly visible autoplay overlay is
                        # not an entry/BET action. Gameplay still requires BET verification.
                        if not(b.get('foreground') and b.get('window_focused')):
                            s.call('focus_test_window',pid=w['pid'],window_id=w['id'])
                            stable=0;continue
                        cb=binding['content_bounds']
                        emit('autoplay_recovery_intent',control_source='mixed_auto_play')
                        ack=s.call('click_recovery',window_id=w['id'],bounds=w['bounds'],point=[cb[0]+.5*cb[2],cb[1]+.49*cb[3]],canvas_screen=cb,expected_origin=binding['origin'],expected_path=binding['path'])
                        recovery_pending=ack['clicked_at_ms'];recovery_clear_frames=0;recovered=True
                        emit('autoplay_recovery_submitted',control_source='mixed_auto_play',ack=ack)
                        continue
                    if args.continuous and joining_existing and actions==0:
                        # Observe the already-running user/auto match until its
                        # settlement; join only after a verified new-round boundary.
                        emit('existing_autoplay_observation',controlled_sample=False)
                        continue
                    if args.execute and args.recover_existing and not recovered and not pending:
                        if not bet_verified and not (immediate_bet and int(immediate_bet[1])==args.expected_bet):raise RuntimeError('recovery_bet_unverified')
                        cb=binding['content_bounds']
                        emit('autoplay_recovery_submitted',control_source='mixed_auto_play')
                        s.call('click',window_id=w['id'],bounds=w['bounds'],point=[cb[0]+.5*cb[2],cb[1]+.49*cb[3]],canvas_screen=cb,expected_origin=binding['origin'],expected_path=binding['path'],expected_capture_seq=f['capture_seq'])
                        recovered=True;previous_owner=False;stable=0
                        continue
                    raise RuntimeError('autoplay_stop')
                if recovery_pending is not None:
                    recovery_clear_frames+=1
                    if recovery_clear_frames<2:continue
                    emit('autoplay_recovery_confirmed',confirmation_ms=received-recovery_pending,control_source='mixed_auto_play')
                    recovery_pending=None;used.clear();await_turn=None;picker_probe_until=None
                    previous_owner=False;turn_start=None;stable=0
                    continue
                if terminal:
                    if args.continuous and settlement_latched:continue
                    if seen_game or args.recover_existing or args.continuous:
                        if pending:
                            emit('action_terminal',action_id=pending['id'],accepted=None,reason='settlement_before_confirmation')
                            pending=None
                        emit('settlement_seen',result=settlement_outcome(title,effect,r))
                        observe_settlement(s,w,binding,emit,observed_round,seconds=1.5 if args.continuous else 15,expected_bet=args.expected_bet,fast=args.continuous)
                        settlements+=1 if not args.continuous or not joining_existing else 0
                        if not args.continuous or settlements>=args.max_settlements:break
                        if args.execute:
                            try:submit_same_room(s,w,binding,args.expected_bet,emit)
                            except (ValueError,RuntimeError) as continuation_error:
                                emit('same_room_continuation_not_submitted',reason=str(continuation_error))
                        settlement_latched=True;seen_game=False;stable=0;last_signature=None
                        emit('await_automatic_next_round',no_navigation=True)
                        continue
                    continue
                if matching_started_at is not None and not seen_game and not hand and not table and not terminal and time.monotonic()-matching_started_at>=args.match_timeout:
                    emit('matching_timeout',timeout_seconds=args.match_timeout,observed_bet=int(immediate_bet[1]) if immediate_bet else None)
                    raise RuntimeError('matching_timeout')
                if settlement_latched:
                    if not(hand and table and hand_complete and table_complete and stable>=2 and immediate_bet and int(immediate_bet[1])==args.expected_bet):continue
                    match_seq+=1;settlement_latched=False;joining_existing=False
                    pending=None;used.clear();await_turn=None;picker_probe_until=None;observed_round=frame_round
                    recovered=False;bet_verified=True;turn_start=started if owner else None;previous_owner=owner;stable=0
                    emit('new_round_observed',entry_source='play_again_or_automatic_countdown',observed_bet=int(immediate_bet[1]),controlled_sample=False)
                    continue
                if hand and table:
                    if not initial_entry_registered and (args.start_bet1 or args.start_bet1000 or args.start_bet2000 or args.start_bet5000) and match_seq==1 and immediate_bet and int(immediate_bet[1])==args.expected_bet:
                        emit('new_round_observed',entry_source='verified_lobby_entry',observed_bet=int(immediate_bet[1]),controlled_sample=False)
                        initial_entry_registered=True
                    seen_game=True
                if picker_probe_until is not None:
                    if owner and stable>=2 and hand_complete and all(trusted(c) for c in hand) and picker_verified(r):
                        target=picker_target(hand);roi=PICKER_REGIONS['pick_'+target]
                        point=[roi[0]+roi[2]/2,roi[1]+roi[3]/2];cb=binding['content_bounds'];aid=uuid.uuid4().hex
                        emit('shape_choice_intent',action_id=aid,target_shape=target,method='visible_three_target_calibration')
                        ack=s.call('click',window_id=w['id'],bounds=w['bounds'],point=[cb[0]+point[0]*cb[2],cb[1]+point[1]*cb[3]],canvas_screen=cb,expected_origin=binding['origin'],expected_path=binding['path'],expected_capture_seq=f['capture_seq'])
                        pending=dict(id=aid,action='choose_shape',target_shape=target,at=ack['clicked_at_ms'],hand=[pair(c) for c in hand],chosen=None)
                        emit('action_submitted',action_id=aid,decision={'action':'choose_shape','target_shape':target})
                        actions+=1;picker_probe_until=None;await_turn=None
                    elif received>=picker_probe_until:raise RuntimeError('wild_picker_calibration_required')
                    continue
                shown_bet=re.fullmatch(r'BET\s*:?\s*(\d+)',bet)
                if seen_game and shown_bet:
                    if int(shown_bet[1])!=args.expected_bet:
                        emit('bet_observation_mismatch',observed_bet=int(shown_bet[1]),consecutive_frames=bet_mismatch_frames,source='shown_bet_gate')
                        # immediate_bet gate above owns the stable-frame stop;
                        # do not let this duplicate OCR check stop on one crop.
                    bet_verified=True
                if pending:
                    accumulate_pending_turn(pending,owner)
                    accepted=False
                    confirmation_mode=None
                    if pending['action']=='choose_shape':
                        accepted=overlay_verified and effective==pending['target_shape'] and not picker_verified(r)
                    if hand_complete and all(trusted(c) for c in hand):
                        old=Counter(pending['hand']);new=Counter(pair(c) for c in hand)
                        if pending['action']=='play' and table_complete and len(table)==1 and trusted(table[0]):
                            old.subtract([pending['chosen']]);accepted=+old==new and pair(table[0])==pending['chosen']
                        animation_hand_complete = (hand_complete
                                                   or selected_hand_complete(r['hand'], raised)
                                                   or (pending['action']=='play'
                                                       and len(hand)==len(pending['hand'])-1))
                        if (not accepted and pending['action']=='play'
                                and play_hand_delta_with_raised_accepted(pending,hand,raised,animation_hand_complete)):
                            accepted=True
                            confirmation_mode='hand_delta_with_raised'
                        elif pending['action']=='draw':accepted=draw_delta_accepted(old,new,pending.get('expected_draw_count',1))
                    if accepted:
                        wild_played=pending['action']=='play' and pending['chosen'][0]==20
                        request_satisfied=pending['action']=='play' and pending.get('effective_before') in ('circle','square','triangle','cross','star') and pending['chosen'][0]!=20
                        await_turn={'started':received,'away_frames':pending.get('observed_away_frames',0),'effect_seen':any(x in ('HOLD ON','SUSPENSION','GENERAL MARKET') for x in effects(effect)),'clear_frames':0,
                                    'request_satisfied':request_satisfied,'request_overlay_seen':request_satisfied and 'MATCH SYMBOL' in effects(effect)}
                        emit('action_terminal',action_id=pending['id'],accepted=True,confirmation_ms=received-pending['at'],observed_draw_count=len(hand)-len(pending['hand']) if pending['action']=='draw' else None,confirmation_mode=confirmation_mode or 'table_and_hand');pending=None;turn_start=started;stable=0
                        if wild_played and args.probe_wild:
                            picker_probe_until=received+3000
                            emit('wild_picker_observation_started',input_suspended=True)
                    elif selected_hand_complete(r['hand'],raised) and (table_complete or overlay_verified) and raised_complete and selected_ready(pending,hand,raised,table,owner,effective) and turn_start is not None and received-turn_start<5000:
                        expected=Counter(pending['hand']);expected.subtract([pending['chosen']])
                        if +expected==Counter(pair(c) for c in hand) and all(trusted(c) for c in hand):
                            pending['selected_frames']=pending.get('selected_frames',0)+1
                            if pending['selected_frames']>=2:
                                cb=binding['content_bounds'];point=pending['point']
                                emit('selection_confirmed',action_id=pending['id'],chosen=pending['chosen'])
                                try:
                                    ack=s.call('click',window_id=w['id'],bounds=w['bounds'],point=[cb[0]+point[0]*cb[2],cb[1]+point[1]*cb[3]],canvas_screen=cb,expected_origin=binding['origin'],expected_path=binding['path'],expected_capture_seq=f['capture_seq'])
                                except RuntimeError as error:
                                    if 'witness_changed' in str(error) or 'witness_expired' in str(error):
                                        pending['selected_frames']=0;emit('commit_rejected',action_id=pending['id'],reason=str(error));continue
                                    if 'chrome_not_foreground' in str(error) and focus_recoveries<100:
                                        focus_recoveries+=1
                                        emit('focus_recovery',action_id=pending['id'],stage='selected_card_commit',recovery_count=focus_recoveries)
                                        s.call('focus_test_window',pid=w['pid'],window_id=w['id'])
                                        pending['selected_frames']=0;stable=0
                                        # Preserve the original deadline and require a fresh
                                        # selected-card observation before another submission.
                                        continue
                                    raise
                                pending['committed']=True;pending['at']=ack['clicked_at_ms'];actions+=1
                                emit('commit_submitted',action_id=pending['id'],turn_observed_to_commit_ms=ack['clicked_at_ms']-turn_start)
                    elif wait_for_occluded_confirmation(pending,hand,hand_complete,table_complete,received-pending['at']):
                        if not pending.get('animation_wait_logged'):
                            emit('confirmation_animation_wait',action_id=pending['id'],accepted=None,max_wait_ms=5000)
                            pending['animation_wait_logged']=True
                    elif received-pending['at']>1800:
                        emit('action_terminal',action_id=pending['id'],accepted=None,reason='confirmation_timeout');pending=None;raise RuntimeError('confirmation_stop')
                    continue
                if await_turn:
                    transition_flags=tuple(x for x in effects(effect) if not((x=='MATCH SYMBOL' and overlay_verified and not await_turn.get('request_satisfied')) or (x=='PICK' and forced==2)))
                    if transition_ready(await_turn,owner,transition_flags,stable):
                        emit('turn_transition_confirmed',away_frames=await_turn['away_frames'],effect_seen=await_turn['effect_seen']);await_turn=None;turn_start=started;stable=0
                    elif received-await_turn['started']>20000:raise RuntimeError('turn_transition_unverified')
                    continue
                table_ready=(table_complete and len(table)==1 and trusted(table[0])) or overlay_verified or forced==2
                if not(owner and stable>=2 and hand and hand_complete and table_ready and all(trusted(c) for c in hand)):
                    if owner:emit('decision_rejected',reason='state_readiness',stable_frames=stable,hand_trusted=[trusted(c) for c in hand],table_trusted=[trusted(c) for c in table])
                    continue
                if not bet_verified:
                    emit('decision_rejected',reason='bet_unverified',bet_text=bet);continue
                if any(e!='MATCH SYMBOL' and not(e=='PICK' and forced==2) for e in effects(effect)) or ('MATCH SYMBOL' in effects(effect) and not overlay_verified):
                    emit('decision_rejected',reason='special_window_requires_calibration');continue
                if forced is None and not overlay_verified and table[0]['rank']==20:continue
                if signature in used:continue
                candidates=[] if forced else [c for c in hand if c['rank']==20 or (not overlay_verified and c['rank']==table[0]['rank']) or c['shape']==(effective if overlay_verified else table[0]['shape'])]
                candidates=[c for c in candidates if client_enabled(c)]
                policy_started=time.perf_counter()
                chosen,reason_codes=choose_strategy(hand,candidates,args.strategy)
                policy_compute_ms=(time.perf_counter()-policy_started)*1000
                if chosen is not None:candidates=[chosen]+[c for c in candidates if c is not chosen]
                if not candidates and not(forced or draw_prompt):
                    emit('decision_rejected',reason='client_affordance_unverified');continue
                # Wild selection needs its own calibrated modal; do not submit it yet.
                if candidates and candidates[0]['rank']==20 and not args.probe_wild:
                    emit('decision_rejected',reason='wild_picker_not_calibrated');continue
                point=candidates[0]['point'] if candidates else [.394,.46]
                action='play' if candidates else 'draw'
                if received-started+f.get('frame_age_ms',500)>1800:
                    emit('decision_rejected',reason='capture_expired',capture_ms=received-started,frame_age_ms=f.get('frame_age_ms'));continue
                if turn_start is None or received-turn_start>5000:
                    emit('decision_rejected',reason='turn_deadline');continue
                decision=dict(action=action,chosen=pair(candidates[0]) if candidates else None,point=point,expected_draw_count=forced if action=='draw' else None)
                emit('decision',decision=decision,arm=args.strategy,reason_codes=reason_codes,policy_compute_ms=policy_compute_ms,observed_turn_age_ms=received-turn_start)
                if not args.execute:used.add(signature);continue
                current=s.call('inspect',pid=w['pid'],window_id=w['id'])
                now=time.monotonic()*1000
                focused=current.get('foreground') and current.get('window_focused')
                recoverable_focus=focus_recoveries<100
                if check(current) and not focused and recoverable_focus:
                    focus_recoveries+=1
                    emit('focus_recovery',discarded_decision=decision,recovery_count=focus_recoveries)
                    s.call('focus_test_window',pid=w['pid'],window_id=w['id'])
                    stable=0
                    continue
                if not check(current) or not focused or now-started+f.get('frame_age_ms',500)>1800:
                    emit('decision_rejected',reason='input_gate',binding_valid=check(current),foreground=current.get('foreground'),window_focused=current.get('window_focused'),foreground_app_bundle=current.get('foreground_app_bundle'),age_ms=now-started+f.get('frame_age_ms',500));continue
                cb=binding['content_bounds'];xy=[cb[0]+point[0]*cb[2],cb[1]+point[1]*cb[3]]
                aid=uuid.uuid4().hex;used.add(signature)
                pending=dict(id=aid,hand=[pair(c) for c in hand],chosen=decision['chosen'],action=action,at=now,point=point,table_before=pair(table[0]) if len(table)==1 else None,effective_before=effective if overlay_verified else None,expected_draw_count=decision['expected_draw_count'])
                emit('action_intent',action_id=aid,decision=decision)
                try:
                    acknowledgement=s.call('click',window_id=w['id'],bounds=w['bounds'],point=xy,canvas_screen=cb,expected_origin=binding['origin'],expected_path=binding['path'],expected_capture_seq=f['capture_seq'])
                except RuntimeError as error:
                    if 'witness_changed' in str(error) or 'witness_expired' in str(error):
                        emit('action_rejected',action_id=aid,reason=str(error));pending=None;used.remove(signature);continue
                    raise
                pending['at']=acknowledgement['clicked_at_ms']
                emit('action_submitted',action_id=aid,decision=decision,turn_observed_to_submit_ms=acknowledgement['clicked_at_ms']-turn_start,fresh_frame_age_ms=acknowledgement['fresh_frame_age_ms'])
                actions+=1
            else:emit('budget_end')
        except Exception as e:
            emit('stopped',reason=str(e));print(json.dumps({'status':'input_stopped','reason':str(e),'log':str(log)}),flush=True)
            if (str(e) in ('autoplay_stop','confirmation_stop','effect_resolution_unverified','turn_transition_unverified','wild_picker_calibration_required') or 'chrome_not_foreground' in str(e)) and seen_game:
                try:observe_settlement(s,w,binding,emit,observed_round,expected_bet=args.expected_bet)
                except Exception as tail_error:emit('settlement_tail_stopped',reason=str(tail_error))
        finally:
            if pending:emit('action_terminal',action_id=pending['id'],accepted=None,reason='session_end')
            emit('closed',submitted_actions=actions);s.close()
    print(json.dumps({'status':'closed','log':str(log),'submitted_actions':actions}),flush=True)

if __name__=='__main__':main()
