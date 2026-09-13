import unittest
from resident_calibration import accumulate_pending_turn,transition_ready

class PendingTurnTests(unittest.TestCase):
    def test_preserves_two_frames_before_acceptance(self):
        pending={}
        self.assertEqual(accumulate_pending_turn(pending,False),1)
        self.assertEqual(accumulate_pending_turn(pending,False),2)
        self.assertEqual(accumulate_pending_turn(pending,True),2)
        wait=dict(away_frames=pending['observed_away_frames'],effect_seen=False,clear_frames=0)
        self.assertFalse(transition_ready(wait,True,(),2))
        self.assertTrue(transition_ready(wait,True,(),3))
    def test_owner_only_does_not_invent_transition(self):
        pending={}
        for _ in range(4):accumulate_pending_turn(pending,True)
        wait=dict(away_frames=pending['observed_away_frames'],effect_seen=False,clear_frames=0)
        for _ in range(4):self.assertFalse(transition_ready(wait,True,(),4))

if __name__=='__main__':unittest.main()
