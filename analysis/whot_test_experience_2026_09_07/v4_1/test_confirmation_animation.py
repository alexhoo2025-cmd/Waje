import unittest
from resident_calibration import wait_for_occluded_confirmation

class AnimationTests(unittest.TestCase):
    def setUp(self):
        self.pending=dict(committed=True,action='play',hand=[(14,'cross'),(13,'square')],chosen=(14,'cross'))
        self.hand=[dict(rank=13,shape='square',rank_score=.99,shape_evidence={'marker_consistent':True})]
    def test_only_readonly_grace_for_removed_card(self):
        self.assertTrue(wait_for_occluded_confirmation(self.pending,self.hand,True,False,2000))
    def test_finite_deadline(self):
        self.assertFalse(wait_for_occluded_confirmation(self.pending,self.hand,True,False,5000))
    def test_uncommitted_or_untrusted_is_not_grace(self):
        self.assertFalse(wait_for_occluded_confirmation(dict(self.pending,committed=False),self.hand,True,False,2000))
        self.assertFalse(wait_for_occluded_confirmation(self.pending,self.hand,False,False,2000))
        self.hand[0]['shape']='unknown'
        self.assertFalse(wait_for_occluded_confirmation(self.pending,self.hand,True,False,2000))
    def test_changed_hand_or_visible_table(self):
        self.assertFalse(wait_for_occluded_confirmation(self.pending,[],True,False,2000))
        self.assertFalse(wait_for_occluded_confirmation(self.pending,self.hand,True,True,2000))

if __name__=='__main__':unittest.main()
