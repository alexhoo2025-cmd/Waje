import unittest
from policy import decide,PendingAction,ARMS

class Tests(unittest.TestCase):
    def state(self):
        return dict(route='/game/6001-whot',client_game_id='6001',binding_verified=True,autoplay=False,
          action_owner='self',captured_at_ms=1000,deadline_ms=9000,cards_verified=True,pending_effect='none',
          visible_hand=[{'rank':8,'shape':'star'},{'rank':13,'shape':'cross'}],table_card={'rank':8,'shape':'cross'},state_seq=1)
    def test_expired_unknown_and_binding(self):
        for key,val in [('deadline_ms',1000),('autoplay',None),('binding_verified',False),('visible_hand',[{}]),('table_card',{}),('pending_effect','arbitrary_click')]:
            s=self.state();s[key]=val
            self.assertEqual(decide(s,{},ARMS[0],1100)['action'],'wait',key)
    def test_star_penalty(self):
        rules={'points_verified':True,'penalty_points':{'8:star':16,'13:cross':13}}
        self.assertEqual(decide(self.state(),rules,ARMS[1],1100)['chosen_index'],0)
    def test_duplicate_frame_and_wrong_card(self):
        s=self.state();d=decide(s,{},ARMS[0],1100);p=PendingAction()
        self.assertTrue(p.submit('a',s,d,1200));self.assertFalse(p.submit('b',s,d,1200))
        self.assertIsNone(p.confirm(s))
        after=dict(s,state_seq=2,visible_hand=[s['visible_hand'][0]],table_card=s['visible_hand'][1])
        self.assertIsNone(p.confirm(after)['accepted'])
        after.update(visible_hand=[s['visible_hand'][1]],table_card=s['visible_hand'][0])
        self.assertTrue(p.confirm(after)['accepted'])
    def test_old_two_does_not_force_draw(self):
        s=self.state();s.update(table_card={'rank':2,'shape':'star'})
        self.assertEqual(decide(s,{},ARMS[0],1100)['action'],'play')

if __name__=='__main__':unittest.main()
