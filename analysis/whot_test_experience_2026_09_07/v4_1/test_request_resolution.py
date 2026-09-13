import unittest
from resident_calibration import transition_ready

class RequestResolutionTests(unittest.TestCase):
    def state(self,satisfied):return dict(away_frames=0,effect_seen=False,clear_frames=0,request_satisfied=satisfied,request_overlay_seen=False)
    def test_confirmed_request_must_finish_animation(self):
        w=self.state(True)
        self.assertFalse(transition_ready(w,True,('MATCH SYMBOL',),3))
        self.assertFalse(transition_ready(w,True,(),3))
        self.assertTrue(transition_ready(w,True,(),3))
    def test_arbitrary_overlay_does_not_grant_turn(self):
        w=self.state(False)
        transition_ready(w,True,('MATCH SYMBOL',),3)
        for _ in range(5):self.assertFalse(transition_ready(w,True,(),5))
    def test_no_owner_or_no_observed_overlay(self):
        w=self.state(True)
        for _ in range(5):self.assertFalse(transition_ready(w,True,(),5))
        w['request_overlay_seen']=True
        self.assertFalse(transition_ready(w,False,(),5))

if __name__=='__main__':unittest.main()
