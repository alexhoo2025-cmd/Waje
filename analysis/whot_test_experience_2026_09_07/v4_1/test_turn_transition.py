import unittest
from resident_calibration import transition_ready

class TransitionTests(unittest.TestCase):
    def state(self):return dict(away_frames=0,effect_seen=False,clear_frames=0)
    def test_lingering_own_turn_is_not_new_turn(self):
        w=self.state()
        for _ in range(10):self.assertFalse(transition_ready(w,True,(),4))
    def test_requires_observed_handoff(self):
        w=self.state()
        self.assertFalse(transition_ready(w,False,(),1))
        self.assertFalse(transition_ready(w,True,(),2))
        self.assertFalse(transition_ready(w,False,(),1))
        self.assertTrue(transition_ready(w,True,(),2))
    def test_effect_must_clear(self):
        w=self.state()
        self.assertFalse(transition_ready(w,True,('HOLD ON',),3))
        self.assertFalse(transition_ready(w,True,(),2))
        self.assertTrue(transition_ready(w,True,(),3))
    def test_match_symbol_is_not_an_extra_turn_grant(self):
        w=self.state()
        self.assertFalse(transition_ready(w,True,('MATCH SYMBOL',),3))
        self.assertFalse(transition_ready(w,True,(),3))
        self.assertFalse(transition_ready(w,True,(),3))
    def test_verified_constraint_after_handoff_can_continue(self):
        w=self.state();w['away_frames']=2
        self.assertFalse(transition_ready(w,True,(),2))
        self.assertTrue(transition_ready(w,True,(),3))

if __name__=='__main__':unittest.main()
