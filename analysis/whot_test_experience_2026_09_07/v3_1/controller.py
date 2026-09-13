"""Persistent visible-window adapter, OCR/template parser and acknowledged action loop.

Profiles start uncalibrated. `probe` is non-clicking. `run` requires a calibrated
profile and never starts or requeues matches by guessing lobby coordinates.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
import selectors
import uuid
from collections import Counter
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse
from lab import ROOT, VERSION, ARMS, Store, decide, digest, gate


class Native:
    def __init__(self, binary, allow_input=False):
        self.allow_input=allow_input
        self.p=subprocess.Popen([str(binary)]+(['--allow-input'] if allow_input else []),stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)
        self.selector=selectors.DefaultSelector();self.selector.register(self.p.stdout,selectors.EVENT_READ)

    def call(self, **request):
        if request.get('op') not in {'status','inspect','capture','analyze','glyphs','shape'} and not self.allow_input:
            raise PermissionError('input_capability_denied')
        request['request_id']=uuid.uuid4().hex
        self.p.stdin.write(json.dumps(request)+'\n');self.p.stdin.flush()
        if not self.selector.select(8 if request.get('op')=='capture' else 3):
            self.p.kill()
            raise RuntimeError('native_timeout')
        result=json.loads(self.p.stdout.readline())
        if result.get('status')!='ok':raise RuntimeError(result.get('reason','native_error'))
        if result.get('request_id') != request['request_id']:raise RuntimeError('native_response_mismatch')
        return result

    def close(self):
        self.p.stdin.close()
        try:self.p.wait(timeout=2)
        except subprocess.TimeoutExpired:self.p.kill()
        self.selector.close()


def bound_context(native,profile,window):
    status=native.call(op='status')
    inspected=native.call(op='inspect',pid=window['pid'])
    focused_id=status.get('focused_window_id')
    return dict(url=inspected['origin']+inspected['path']+('?ux_mode=standalone' if inspected['standalone'] else ''),
                client_game_id=profile['client_game_id'],browser_surface='ordinary_chrome',
                foreground=inspected['foreground'],
                window_verified=any(w==window for w in status['windows']) and focused_id==window.get('id'),
                content_bounds=inspected.get('content_bounds'))


def select_window(native, timeout_s=15):
    """Wait for a single foreground, accessibility-focused Chrome window.

    Starting the worker from a terminal can temporarily make Chrome lose
    focus.  Waiting here keeps that startup race outside the game clock while
    still failing closed when focus never returns or multiple windows are
    indistinguishable.
    """
    deadline=time.monotonic()+timeout_s;last=None
    while True:
        status=native.call(op='status');last=status
        focused_id=status.get('focused_window_id')
        visible=[w for w in status.get('windows',[]) if w['bounds']['Height']>300]
        matches=[w for w in visible if w.get('id')==focused_id] if isinstance(focused_id,int) else []
        if status.get('foreground_chrome') is True and len(matches)==1:
            return status,matches[0]
        if time.monotonic()>=deadline:
            raise ValueError('window_not_focused_or_ambiguous')
        time.sleep(.25)


def top_text(region):
    texts=region.get('text',[])
    if len(texts)!=1:return None,0
    return texts[0]['value'].strip(),texts[0]['confidence']


def template_label(feature, templates):
    scores=[]
    for label,reference in templates.items():
        if not feature or len(reference)!=len(feature):continue
        distance=sum((a-b)**2 for a,b in zip(feature,reference))/len(feature)
        scores.append((distance,label))
    scores.sort()
    if not scores or scores[0][0]>.04 or (len(scores)>1 and scores[1][0]-scores[0][0]<.08):
        return None,0
    # Similarity score, not calibrated probability. Replay validation is required.
    return scores[0][1],max(0,1-scores[0][0]/2)


class Vision:
    def __init__(self, profile):
        self.profile=profile;self.seq=0;self.last=None

    def parse(self, frame, captured, context):
        v=self.profile['vision']; r=frame['regions']; confidence=[]
        def text(name):
            value,conf=top_text(r.get(name,{}));confidence.append(conf);return value
        def integer(name):
            value=text(name)
            return int(value) if value and re.fullmatch(r'\d+',value) else None
        def label(name):
            value,conf=template_label(r.get(name,{}).get('feature',[]),v.get('templates',{}).get(name,{}))
            confidence.append(conf);return value
        phase=label('phase')
        owner=label('action_owner')
        autoplay=label('autoplay')
        pending=label('pending_effect')
        state=dict(client_game_id=self.profile['client_game_id'],phase=phase or 'unknown',
                   foreground=context['foreground'],window_verified=context['window_verified'],
                   action_owner=owner,pending_effect=pending or 'unknown',autoplay=(None if autoplay is None else autoplay=='on'),
                   captured_at_ms=captured,available_actions=[],visible_hand=None,table_card=None)
        if phase in ('player_turn','opponent_turn','special_resolution','settlement'):
            count=integer('hand_count');seconds=integer('countdown')
            state['deadline_ms']=captured+seconds*1000 if seconds is not None else None
            state['table_card']={'rank':integer('table_rank'),'shape':label('table_shape')}
            state['effective_shape']=label('effective_shape')
            opponent=integer('opponent_count')
            state['opponent_visible_card_counts']=[opponent] if opponent is not None else []
            layouts=v.get('hand_layouts',{})
            layout=layouts.get(str(count))
            if layout:
                state['visible_hand']=[{'rank':integer(x['rank_region']),'shape':label(x['shape_region'])} for x in layout]
                state['card_points']=[x['point'] for x in layout]
            if pending in v.get('action_points',{}):state['available_actions']=[pending]
        state['settlement']=None
        # Terminal fields have their own explicit parser contract; no inference from title alone.
        if phase=='settlement' and v.get('settlement_fields'):
            result={}
            for key,spec in v['settlement_fields'].items():
                raw,conf=top_text(r.get(spec['region'],{}))
                if raw is None or conf<v.get('ocr_threshold',.98):continue
                if spec.get('type')=='enum':
                    if raw in spec.get('values',{}):result[key]=spec['values'][raw]
                elif spec.get('type')=='number' and re.fullmatch(r'-?\\d+(?:\\.\\d+)?',raw):
                    result[key]=float(raw)
            result['visible']=result.get('result') in ('win','loss','draw') and result.get('end_reason') in ('hand_empty','opponent_hand_empty','deck_exhausted','tie_break')
            state['settlement']=result
        state['capture_confidence']=min(confidence) if confidence else 0
        # Countdown ticks don't create new action opportunities.
        semantic={k:state.get(k) for k in ('phase','action_owner','pending_effect','autoplay','visible_hand','table_card','effective_shape','opponent_visible_card_counts')}
        fingerprint=digest(semantic)
        if fingerprint!=self.last:self.seq+=1;self.last=fingerprint
        state.update(state_seq=self.seq,frame_hash=fingerprint,vision_profile_version=v['version'])
        return state


class Controller:
    def __init__(self,native,profile,store,match_id,window):
        self.native,self.profile,self.store,self.match_id,self.window=native,profile,store,match_id,window
        self.vision=Vision(profile);self.pending=None;self.used=set();self.last_capture=None
        self.event_seq=store.c.execute('select coalesce(max(seq),0) from events where match_id=?',(match_id,)).fetchone()[0]
        self.opened=set();self.poisoned=False;self.previous_state=None;self.last_wait_at=None
        row=store.c.execute('select meta,arm from matches where id=?',(match_id,)).fetchone()
        if not row:raise ValueError('match_not_started')
        self.arm=row['arm'];self.turn_id=None;self.turn_start=None;self.last_phase=None

    def emit(self,kind,**fields):
        self.event_seq+=1;self.store.append(self.match_id,self.event_seq,{'type':kind,**fields})

    def observe(self):
        start=time.monotonic_ns()/1e6
        context=bound_context(self.native,self.profile,self.window)
        reasons=gate(context,self.profile)
        if reasons:raise RuntimeError('browser_gate:'+','.join(reasons))
        if not context['content_bounds']:raise RuntimeError('content_bounds_unavailable')
        frame=self.native.call(op='capture',window_id=self.window['id'],bounds=self.window['bounds'],
                               screen_rect=context['content_bounds'],crop=[0,0,1,1],regions=self.profile['vision']['regions'])
        captured=time.monotonic_ns()/1e6-float(frame.get('frame_age_ms',0))
        state=self.vision.parse(frame,captured,context)
        state['content_bounds']=context['content_bounds']
        state['capture_pipeline_ms']=time.monotonic_ns()/1e6-start
        if self.last_capture is not None and start-self.last_capture>(1050 if self.last_phase=='waiting' else 550):
            self.emit('capture_gap',gap_ms=start-self.last_capture)
        self.last_capture=start
        self.emit('capture_heartbeat',at_ms=start,capture_seq=frame.get('capture_seq'),phase=state['phase'])
        return state

    def execute_and_confirm(self,state,decision):
        """Physical input is never mistaken for an accepted in-game action."""
        if self.pending or self.poisoned:return False
        at=time.monotonic_ns()/1e6
        if state['state_seq'] in self.used or at-state['captured_at_ms']>750 or at>=decision['expires_at_ms']-300:
            return False
        action=decision['action'];points=self.profile['vision']['action_points']
        if action=='play':
            index=decision['chosen_card']['index'];point=state.get('card_points',[])[index]
        elif action=='select_shape':point=points.get('shape_'+decision['target_shape'])
        else:point=points.get(action)
        if not point:raise RuntimeError('action_coordinate_not_calibrated')
        context=bound_context(self.native,self.profile,self.window)
        if gate(context,self.profile) or context['content_bounds']!=state['content_bounds']:raise RuntimeError('window_changed_before_click')
        # Re-check expiry after the OS/browser checks, which are part of latency.
        click_at=time.monotonic_ns()/1e6
        if click_at-state['captured_at_ms']>750 or click_at>=decision['expires_at_ms']-300:return False
        b=self.window['bounds'];canvas=context['content_bounds']
        xy=[canvas[0]+point[0]*canvas[2],canvas[1]+point[1]*canvas[3]]
        id_=digest([self.match_id,state['state_seq'],decision])
        self.emit('decision',decision_id=id_,turn_id=self.turn_id,state=state,decision=decision)
        self.used.add(state['state_seq'])
        self.pending=dict(state=state,decision=decision,decision_id=id_,clicked_at=click_at,turn_id=self.turn_id)
        self.emit('action_submitted',decision_id=id_,turn_id=self.turn_id,at_ms=click_at)
        try:
            self.native.call(op='click',window_id=self.window['id'],bounds=b,point=xy,
                             canvas_screen=canvas,expected_origin=self.profile['origin'],
                             expected_path=self.profile['route'])
            self.pending['clicked_at']=time.monotonic_ns()/1e6
        except Exception:
            self.poisoned=True
            self.emit('action_unknown',decision_id=id_,reason='native_response_missing')
            raise
        return True

    def confirm(self,state):
        p=self.pending
        if not p:return
        old=p['state'];decision=p['decision'];accepted=False
        trusted=state.get('capture_confidence',0)>=.98 and state.get('autoplay') is False
        bag=lambda hand:Counter((c['rank'],c['shape']) for c in hand)
        if trusted and state['state_seq']!=old['state_seq']:
            if decision['action']=='play' and state.get('visible_hand') is not None:
                chosen=decision['chosen_card'];before=list(old['visible_hand']);before.pop(chosen['index'])
                accepted=(bag(state['visible_hand'])==bag(before) and
                          state.get('table_card')=={'rank':chosen['rank'],'shape':chosen['shape']})
            elif decision['action']=='draw' and state.get('visible_hand') is not None:
                before=bag(old.get('visible_hand') or []);after=bag(state['visible_hand'])
                expected=decision.get('expected_draw_count',1)
                accepted=(not before-after and sum(after.values())-sum(before.values())==expected)
            elif decision['action']=='select_shape':
                accepted=state.get('effective_shape')==decision['target_shape'] and state.get('pending_effect')=='none'
            elif decision['action'] in ('declare_last_card','catch_last_card'):
                accepted=(state.get('confirmed_action_id')==p['decision_id'])
        terminal=state.get('settlement') or {}
        if (state.get('autoplay') is False and decision['action']=='play' and
            len(old.get('visible_hand') or [])==1 and terminal.get('visible') is True and
            terminal.get('end_reason')=='hand_empty' and terminal.get('player_remaining_cards')==0):
            accepted=True
        elapsed=time.monotonic_ns()/1e6-p['clicked_at']
        if accepted or elapsed>1500 or self.poisoned:
            latency=p['clicked_at']-self.turn_start if self.turn_start is not None else None
            self.emit('action_confirmed',decision_id=p['decision_id'],turn_id=p['turn_id'],
                      accepted=True if accepted and not self.poisoned else None,
                      legal=True if not self.poisoned else None,timeout=False if accepted and not self.poisoned else None,
                      timing_source='monotonic_observed',click_latency_ms=latency,confirmation_ms=elapsed,
                      context_complete=latency is not None and not self.poisoned)
            self.pending=None
            if not accepted or self.poisoned:
                self.poisoned=True;self.emit('action_unknown',reason='acceptance_not_proven')

    def run(self,seconds):
        end=time.monotonic()+seconds;unresolved=0
        while time.monotonic()<end:
            tick=time.monotonic();state=self.observe()
            if state.get('autoplay') is True:
                if not self.poisoned:self.emit('autoplay')
                self.poisoned=True
            # Confirmation is evaluated BEFORE terminal return, including the last card.
            self.confirm(state)
            if state['phase']=='settlement':
                self.emit('settlement_visible',state_seq=state['state_seq'])
                settlement=state.get('settlement') or {'visible':False,'result':'unknown','end_reason':'unknown'}
                if self.poisoned:settlement=dict(settlement,quality='mixed_or_unverified_control')
                return dict(status='settlement_observed',settlement=settlement)
            actionable=state['phase'] in ('player_turn','special_resolution') and state.get('action_owner')=='self'
            if not actionable:self.last_wait_at=state['captured_at_ms']
            if actionable and state['state_seq'] not in self.opened and self.pending is None:
                self.opened.add(state['state_seq']);self.turn_id=f"{self.match_id}:{state['state_seq']}"
                # Upper bound from last observed non-actionable frame; unknown if first attached mid-turn.
                self.turn_start=self.last_wait_at
                self.emit('turn_open',turn_id=self.turn_id,at_ms=state['captured_at_ms'],onset_lower_ms=self.turn_start)
            self.last_phase='actionable' if actionable else 'waiting'
            if not self.poisoned and self.pending is None:
                decision=decide(state,self.profile['rules'],self.arm)
                if decision['action'] in ('stop','rescan'):
                    unresolved+=1
                    if unresolved>=2:
                        self.poisoned=True;self.emit('unresolved_state',reason=decision['reason'])
                else:unresolved=0
                if decision['action'] in ('play','draw','select_shape','declare_last_card','catch_last_card'):
                    self.execute_and_confirm(state,decision)
            self.previous_state=state
            time.sleep(max(0,(1/8 if actionable else 1/2)-(time.monotonic()-tick)))
        if self.pending:self.emit('action_unknown',decision_id=self.pending['decision_id'],reason='run_ended')
        self.emit('capture_gap',reason='bounded_run_ended')
        return dict(status='bounded_run_ended')


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['probe','dry-run','run']);p.add_argument('--game',choices=['6001','9006'],required=True)
    p.add_argument('--native',type=Path,default=Path('/tmp/whot-native-v3_1'));p.add_argument('--profile',type=Path,default=ROOT/'profiles.json')
    p.add_argument('--db',type=Path,default=ROOT/'samples.sqlite3');p.add_argument('--match');p.add_argument('--seconds',type=int,default=30)
    a=p.parse_args();profile=json.loads(a.profile.read_text())[a.game];worker=Native(a.native,allow_input=a.command=='run')
    try:
        status,window=select_window(worker)
        # Multiple on-screen Chrome windows are normal (for example a second
        # work profile).  Bind only the accessibility-focused one; if the
        # native probe cannot identify it, fail closed instead of clicking a
        # stale or unrelated window.
        inspected=worker.call(op='inspect',pid=window['pid'])
        print(json.dumps({'native':status,'origin':inspected['origin'],'path':inspected['path'],
                          'bound_foreground':inspected['foreground'],
                          'rules':profile['rules']['status'],'vision':profile['vision']['status']},ensure_ascii=False),flush=True)
        if a.command in ('probe','dry-run'):return
        if not a.match:raise ValueError('match_required')
        if profile['rules']['status']!='verified' or profile['vision']['status']!='calibrated':
            raise ValueError('profile_not_calibrated')
        from certification import require_profile
        require_profile(profile, a.native)
        store=Store(a.db);runner=Controller(worker,profile,store,a.match,window)
        try:result=runner.run(a.seconds)
        except Exception as e:
            runner.emit('unresolved_state',reason=str(e));raise
        if isinstance(result,dict) and result.get('settlement'):store.finish(a.match,result['settlement'])
        print(json.dumps({'status':result}),flush=True)
    finally:worker.close()


if __name__=='__main__':main()
