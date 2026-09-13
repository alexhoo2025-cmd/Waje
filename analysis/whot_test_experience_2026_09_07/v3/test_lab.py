import copy
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
import lab


class LabTests(unittest.TestCase):
    def rules(self):
        return dict(client_game_id='6001',status='verified',ruleset_version='test',wild_rank=20,
                    shapes=['circle','star'],valid_cards=['3:circle','4:circle','5:star','20:wild'],
                    points={'3:circle':3,'4:circle':4,'5:star':10,'20:wild':20},special_ranks=[20],
                    blocking_ranks=[],effects={'pick_two':{'resolution':'manual','action':'draw'}})

    def state(self):
        return dict(client_game_id='6001',state_seq=4,foreground=True,window_verified=True,
                    captured_at_ms=1000,deadline_ms=5000,capture_confidence=.99,phase='player_turn',
                    action_owner='self',pending_effect='none',table_card={'rank':3,'shape':'circle'},
                    effective_shape='circle',visible_hand=[{'rank':4,'shape':'circle'}],
                    opponent_visible_card_counts=[4])

    def test_actor_deadline_staleness_and_legal_choice(self):
        s=self.state(); r=self.rules()
        self.assertEqual(lab.decide(s,r,lab.ARMS[0],1100)['action'],'play')
        for changes in ({'deadline_ms':1100},{'captured_at_ms':0},{'autoplay':True},{'foreground':False}):
            self.assertNotEqual(lab.decide(dict(s,**changes),r,lab.ARMS[0],1100)['action'],'play')
        s.update(action_owner='opponent',pending_effect='pick_two',available_actions=['pick_two'])
        self.assertEqual(lab.decide(s,r,lab.ARMS[0],1100)['action'],'wait')
        s['action_owner']='self'
        self.assertEqual(lab.decide(s,r,lab.ARMS[0],1100)['action'],'draw')

    def test_wild_shape_and_scoring(self):
        s=self.state(); s.update(table_card={'rank':20,'shape':'wild'},effective_shape='star',
                                 visible_hand=[{'rank':4,'shape':'circle'},{'rank':5,'shape':'star'}])
        self.assertEqual(lab.decide(s,self.rules(),lab.ARMS[1],1100)['chosen_card']['rank'],5)
        s['effective_shape']=None
        self.assertEqual(lab.decide(s,self.rules(),lab.ARMS[0],1100)['action'],'stop')

    def test_scope_does_not_trust_surface_string_alone(self):
        p={'client_game_id':'6001','route':'/game/6001-whot'}
        c=dict(client_game_id='6001',url='https://test-h5.wajew.com/game/6001-whot',
               browser_surface='ordinary_chrome',foreground=True,window_verified=True)
        self.assertEqual(lab.gate(c,p),[])
        for url in ('http://test-h5.wajew.com/game/6001-whot',
                    c['url']+'?ux_mode=standalone','https://test-h5.wajew.com/game/9006-whot'):
            self.assertTrue(lab.gate(dict(c,url=url),p))

    def valid_events(self):
        return [{'type':'match_start'}, {'type':'turn_open','turn_id':'t1'},
                {'type':'decision','decision_id':'d1'},
                dict(type='action_confirmed',turn_id='t1',decision_id='d1',accepted=True,legal=True,
                     timeout=False,timing_source='monotonic_observed',click_latency_ms=100,
                     context_complete=True)]

    def meta(self):
        return dict(client_game_id='6001',phase='calibration',strategy_arm=lab.ARMS[0],
                    ruleset_version='test',game_build='test',vision_profile_version='test',
                    controller_version=lab.VERSION,room_id='low',stake=1,actual_player_count=2)

    def settlement(self):
        return dict(visible=True,result='win',end_reason='hand_empty',observed_turn_opportunities=1,
                    continuous_capture_verified=True)

    def test_missing_turns_failed_actions_and_false_timing_are_not_qualified(self):
        m,s,e=self.meta(),self.settlement(),self.valid_events()
        self.assertTrue(lab.eligibility(m,s,e)['eligible'])
        for field,value in [('accepted',False),('timeout',True),('click_latency_ms',9000),
                            ('timing_source','manual_estimate'),('decision_id','missing')]:
            bad=copy.deepcopy(e);bad[-1][field]=value
            self.assertFalse(lab.eligibility(m,s,bad)['eligible'])
        self.assertFalse(lab.eligibility(m,dict(s,observed_turn_opportunities=8),e)['eligible'])
        self.assertFalse(lab.eligibility(m,dict(s,continuous_capture_verified=False),e)['eligible'])
        self.assertFalse(lab.eligibility(m,s,e+[{'type':'autoplay'}])['eligible'])

    def test_schedule_recovery_and_atomic_settlement(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'t.db'; store=lab.Store(path); store.init_schedule(); store.init_schedule()
            self.assertEqual(store.c.execute('select count(*) from slots').fetchone()[0],200)
            for g in lab.GAMES:
                self.assertEqual(sorted(r[0] for r in store.c.execute('select count(*) from slots where game=? group by arm',(g,))),[33,33,34])
            with self.assertRaisesRegex(ValueError,'calibration_not_passed'):
                store.begin(dict(self.meta(),phase='formal'))
            id_=store.begin(self.meta())
            with self.assertRaisesRegex(ValueError,'unfinished'):
                store.begin(self.meta())
            for i,e in enumerate(self.valid_events()[1:],2):store.append(id_,i,e)
            store.append(id_,4,self.valid_events()[-1])
            self.assertEqual(store.c.execute('select count(*) from events').fetchone()[0],4)
            q=store.finish(id_,self.settlement()); self.assertTrue(q['eligible'])
            self.assertEqual(store.finish(id_,self.settlement()),q)
            with self.assertRaisesRegex(ValueError,'settlement_conflict'):
                store.finish(id_,dict(self.settlement(),result='loss'))
            self.assertEqual(store.progress()['games']['6001']['qualified'],0)
            store.c.close()
            readonly=lab.Store(path,readonly=True)
            self.assertEqual(readonly.progress()['games']['6001']['qualified'],0)

    def test_secrets_and_nonfinite_values_rejected(self):
        for value in ({'turn':{'hidden_cards':[1]}},{'token':'x'},{'time':float('nan')}):
            with self.assertRaises(ValueError):lab.validate_payload(value)


if __name__=='__main__':unittest.main()
