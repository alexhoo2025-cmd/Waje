import unittest
from resident_calibration import selected_ready,play_hand_delta_with_raised_accepted

def card(rank,shape):return dict(rank=rank,shape=shape,rank_score=.99,shape_evidence={'marker_consistent':True})
class SelectedTests(unittest.TestCase):
    def setUp(self):
        self.p=dict(action='play',hand=[(3,'circle'),(10,'square')],chosen=(3,'circle'),table_before=(4,'circle'))
        self.h=[card(10,'square')];self.r=[card(3,'circle')];self.t=[card(4,'circle')]
    def test_confirmed_selection(self):self.assertTrue(selected_ready(self.p,self.h,self.r,self.t,True))

    def test_hand_delta_with_raised_confirms_old_canvas_animation(self):
        pending=dict(self.p,committed=True)
        self.assertTrue(play_hand_delta_with_raised_accepted(pending,self.h,self.r,True))

    def test_hand_delta_without_raised_is_not_confirmation(self):
        pending=dict(self.p,committed=True)
        self.assertFalse(play_hand_delta_with_raised_accepted(pending,self.h,[],True))
    def test_raised_without_removal_is_not_ready(self):self.assertFalse(selected_ready(self.p,self.h+self.r,self.r,self.t,True))
    def test_other_turn_or_other_card(self):
        self.assertFalse(selected_ready(self.p,self.h,self.r,self.t,False))
        self.assertFalse(selected_ready(self.p,self.h,[card(3,'cross')],self.t,True))
    def test_no_repeat_commit_or_changed_table(self):
        self.assertFalse(selected_ready(dict(self.p,committed=True),self.h,self.r,self.t,True))
        self.assertFalse(selected_ready(self.p,self.h,self.r,[card(3,'circle')],True))
    def test_verified_requested_shape_can_replace_table(self):
        p=dict(self.p,table_before=None,effective_before='circle')
        self.assertTrue(selected_ready(p,self.h,self.r,[],True,'circle'))
        self.assertFalse(selected_ready(p,self.h,self.r,[],True,'star'))
        self.assertFalse(selected_ready(p,self.h,self.r,[],True,None))
        self.assertFalse(selected_ready(dict(p,effective_before=None),self.h,self.r,[],True,None))

if __name__=='__main__':unittest.main()
