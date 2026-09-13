import unittest
from policy import PendingAction

class IdentityTests(unittest.TestCase):
    def fixtures(self):
        card={'rank':1,'shape':'circle'}
        return ({'state_seq':3,'visible_hand':[card]},
                {'state_seq':3,'action':'play','chosen_index':0,
                 'chosen_card':card,'expires_at_ms':1000})

    def test_mismatched_decision_rejected(self):
        s,d=self.fixtures();d['state_seq']=2
        self.assertFalse(PendingAction().submit('a',s,d,100))

    def test_invalid_expiry_rejected(self):
        for expiry in (None,float('nan'),float('inf'),True):
            s,d=self.fixtures();d['expires_at_ms']=expiry
            self.assertFalse(PendingAction().submit('a',s,d,100))

    def test_snapshot_is_immutable(self):
        s,d=self.fixtures();p=PendingAction()
        self.assertTrue(p.submit('a',s,d,100))
        s['visible_hand'].clear();d['chosen_card']['rank']=2
        self.assertEqual(p.pending[1]['visible_hand'][0]['rank'],1)
        self.assertEqual(p.pending[2]['chosen_card']['rank'],1)

    def test_out_of_order_frame_ignored(self):
        s,d=self.fixtures();p=PendingAction();p.submit('a',s,d,100)
        self.assertIsNone(p.confirm({'state_seq':2}))
        self.assertIsNotNone(p.pending)

if __name__=='__main__':unittest.main()
