import copy
import json
import tempfile
import time
import unittest
from pathlib import Path
from controller import Controller,Native,Vision,select_window
from lab import eligibility,decide,ARMS,ROOT,Store,gate
import test_lab
from accounting import reconcile,aggregate,can_enter
from shadow import rank_candidates
from migrate import migrate


class SafetyTests(unittest.TestCase):
    def setUp(self):self.f=test_lab.LabTests()

    def test_observer_has_no_click_capability(self):
        n=Native.__new__(Native);n.allow_input=False
        for op in ('click','page_click','tab_click','activate_process'):
            with self.subTest(op=op),self.assertRaises(PermissionError):n.call(op=op)

    def test_calibration_uses_same_entrypoint(self):
        import calibrate_live,controller
        self.assertIs(calibrate_live.main,controller.main)

    def test_origin_is_profile_specific(self):
        base=dict(browser_surface='ordinary_chrome',client_game_id='9006',
                  foreground=True,window_verified=True)
        profile={'client_game_id':'9006','origin':'https://test-h5.wajetan.com',
                 'route':'/game/9006-wajewhot'}
        self.assertEqual(gate(dict(base,url='https://test-h5.wajetan.com/game/9006-wajewhot'),profile),[])
        self.assertIn('wrong_origin',gate(dict(base,url='https://test-h5.wajew.com/game/9006-wajewhot'),profile))

    def test_window_selection_waits_for_focus(self):
        class FakeNative:
            def __init__(self): self.calls=0
            def call(self,**request):
                self.calls+=1
                focused=None if self.calls==1 else 22
                return {'foreground_chrome':self.calls>1,'focused_window_id':focused,
                        'windows':[{'id':11,'bounds':{'Height':800}},
                                   {'id':22,'bounds':{'Height':900}}]}
        native=FakeNative();status,window=select_window(native,timeout_s=1)
        self.assertEqual(window['id'],22);self.assertGreaterEqual(native.calls,2)

    def test_control_unknown_and_auto_are_not_playable(self):
        for mode in (True,None):
            s=dict(self.f.state(),autoplay=mode)
            self.assertNotEqual(decide(s,self.f.rules(),ARMS[0],1100)['action'],'play')

    def test_legacy_stop_and_intervention_cannot_qualify(self):
        for quality in ('mixed_auto_play','controller_stopped_unqualified','uncontrolled_after_local_loop_stop','uncertified_manual_intervention'):
            self.assertFalse(eligibility(self.f.meta(),dict(self.f.settlement(),quality=quality),self.f.valid_events())['eligible'])
        self.assertFalse(eligibility(self.f.meta(),self.f.settlement(),self.f.valid_events()+[{'type':'stop','reason':'mixed_auto_play'}])['eligible'])

    def test_submitted_without_confirmation_cannot_qualify(self):
        e=self.f.valid_events()+[{'type':'action_submitted','decision_id':'d2'}]
        self.assertFalse(eligibility(self.f.meta(),self.f.settlement(),e)['eligible'])

    def test_coverage_requires_independent_evidence(self):
        s=self.f.settlement();s.pop('coverage_review')
        self.assertFalse(eligibility(self.f.meta(),s,self.f.valid_events())['eligible'])

    def test_terminal_title_is_not_end_reason(self):
        self.assertFalse(eligibility(self.f.meta(),dict(self.f.settlement(),end_reason='settlement_visible'),self.f.valid_events())['eligible'])

    def runner(self,hand=None,action='play'):
        c=Controller.__new__(Controller);c.poisoned=False;c.events=[]
        c.emit=lambda kind,**kw:c.events.append(dict(type=kind,**kw))
        t=time.monotonic_ns()/1e6;c.turn_start=t-100
        hand=hand if hand is not None else [{'rank':3,'shape':'circle'},{'rank':4,'shape':'circle'}]
        c.pending={'state':{'state_seq':1,'visible_hand':hand},
                   'decision':{'action':action,'chosen_card':dict(hand[0],index=0),'target_shape':'circle'},
                   'clicked_at':t,'decision_id':'d','turn_id':'t'}
        return c

    def test_confirm_on_opponent_turn(self):
        c=self.runner();c.confirm({'state_seq':2,'capture_confidence':1,'autoplay':False,'phase':'opponent_turn',
            'visible_hand':[{'rank':4,'shape':'circle'}],'table_card':{'rank':3,'shape':'circle'}})
        self.assertIs(c.events[-1]['accepted'],True);self.assertIsNone(c.pending)

    def test_selected_animation_is_not_acceptance(self):
        c=self.runner();c.confirm({'state_seq':2,'capture_confidence':1,'autoplay':False,
            'visible_hand':c.pending['state']['visible_hand'],'table_card':{'rank':3,'shape':'circle'}})
        self.assertIsNotNone(c.pending);self.assertEqual(c.events,[])

    def test_last_card_terminal_ack_before_return(self):
        c=self.runner(hand=[{'rank':3,'shape':'circle'}]);c.observe=lambda:{'phase':'settlement','state_seq':2,'autoplay':False,
            'capture_confidence':0,'settlement':{'visible':True,'result':'win','end_reason':'hand_empty','player_remaining_cards':0}}
        result=c.run(.1)
        self.assertIs(c.events[0]['accepted'],True);self.assertEqual(result['status'],'settlement_observed')

    def test_missing_terminal_details_not_accepted(self):
        c=self.runner(hand=[{'rank':3,'shape':'circle'}]);c.confirm({'phase':'settlement','state_seq':2,'autoplay':False,
            'capture_confidence':0,'settlement':{'visible':True,'result':'win','end_reason':'hand_empty'}})
        self.assertIsNotNone(c.pending)

    def test_timeout_is_unknown_never_success(self):
        c=self.runner();c.pending['clicked_at']-=1600
        c.confirm({'state_seq':1,'capture_confidence':1,'autoplay':False})
        self.assertTrue(c.poisoned);self.assertIsNone(c.events[0]['accepted'])

    def test_shape_selection_confirmation(self):
        c=self.runner(action='select_shape');c.confirm({'state_seq':2,'capture_confidence':1,'autoplay':False,
            'effective_shape':'circle','pending_effect':'none'})
        self.assertTrue(c.events[-1]['accepted'])

    def test_draw_must_preserve_old_cards(self):
        c=self.runner(action='draw');c.confirm({'state_seq':2,'capture_confidence':1,'autoplay':False,
            'visible_hand':[{'rank':8,'shape':'star'}]*3})
        self.assertIsNotNone(c.pending)

    def test_vision_keeps_cards_on_opponent_turn(self):
        p={'client_game_id':'6001','vision':{'version':'test','hand_layouts':{'1':[{'rank_region':'r0','shape_region':'s0','point':[.5,.8]}]},'templates':{}}}
        values={'phase':'opponent_turn','action_owner':'opponent','autoplay':'off','pending_effect':'none',
                'table_shape':'circle','effective_shape':'circle','s0':'circle'}
        frame={'regions':{}}
        for key,val in values.items():
            p['vision']['templates'][key]={val:[1,0]};frame['regions'][key]={'feature':[1,0]}
        for key,val in {'hand_count':'1','countdown':'3','table_rank':'4','opponent_count':'2','r0':'3'}.items():
            frame['regions'][key]={'text':[{'value':val,'confidence':1}]}
        state=Vision(p).parse(frame,1000,{'foreground':True,'window_verified':True})
        self.assertEqual(state['visible_hand'],[{'rank':3,'shape':'circle'}])

    def ledger(self,stake=1,returned=1.8):
        return dict(stake=stake,gross_return=returned,fee=0,bonus=0,adjustment=0,balance_before=10,
                    balance_after_debit=10-stake,balance_after=10-stake+returned,
                    semantics_status='certified',asset_unit='test_chip',fee_timing='settlement')

    def test_rtp_uses_sums(self):
        a=self.ledger(1,2);b=self.ledger(9,0)
        self.assertEqual(aggregate([a,b])['rtp'],'0.2')

    def test_incomplete_or_unbalanced_ledger_no_rtp(self):
        a=self.ledger();a['balance_after']=20
        self.assertIsNone(aggregate([a])['rtp'])
        a=self.ledger();a.pop('gross_return');self.assertIsNone(aggregate([a])['rtp'])

    def test_dau1_no_arbitrary_200_balance_floor(self):
        self.assertTrue(can_enter(2,1));self.assertFalse(can_enter(.5,1));self.assertFalse(can_enter(2,None))

    def test_high_point_includes_wild(self):
        s=self.f.state();s['visible_hand']=[{'rank':4,'shape':'circle'},{'rank':20,'shape':'wild'}]
        self.assertEqual(decide(s,self.f.rules(),ARMS[1],1100)['chosen_card']['rank'],20)
        self.assertEqual(decide(s,self.f.rules(),ARMS[2],1100)['chosen_card']['rank'],4)

    def test_shadow_does_not_change_state_or_arm(self):
        s=self.f.state();before=copy.deepcopy(s);r=rank_candidates(s,self.f.rules(),1100)
        self.assertEqual(s,before);self.assertEqual(r['status'],'shadow_only')

    def test_unverified_profiles_cannot_be_used(self):
        from certification import require_profile
        for p in json.loads((ROOT/'profiles.json').read_text()).values():
            with self.assertRaises(ValueError):require_profile(p,Path('/tmp/whot-native-v3_1'))

    def test_migration_is_idempotent_and_does_not_infer_visibility(self):
        with tempfile.TemporaryDirectory(prefix='whot31-test-') as d:
            src=Path(d)/'source.sqlite3';s=Store(src)
            s.c.execute('insert into matches values(?,?,?,?,?,?,?,?,?,?)',('old','6001','calibration','first_legal_play','a','b',
                json.dumps(self.f.meta()),json.dumps({'result':'win','stake':1,'end_reason':'settlement_visible'}),'{}','legacy'));s.c.commit();s.c.close()
            dst=Path(d)/'derived.sqlite3';a=migrate(src,dst);b=migrate(src,dst)
            self.assertEqual(a['counts']['inserted'],1);self.assertEqual(b['counts']['skipped'],1)
            out=Store(dst,readonly=True);row=out.c.execute('select * from matches').fetchone()
            self.assertIsNone(json.loads(row['settlement']).get('visible'));self.assertEqual(row['arm'],'unknown')
            self.assertEqual(json.loads(row['settlement'])['end_reason'],'unknown');out.c.close()


if __name__=='__main__':unittest.main()
