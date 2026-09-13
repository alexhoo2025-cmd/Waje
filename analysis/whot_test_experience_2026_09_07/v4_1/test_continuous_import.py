import unittest
from record_continuous_session import eligible_groups

class ContinuousTests(unittest.TestCase):
    def test_existing_terminal_not_a_new_match(self):
        self.assertEqual(eligible_groups([{'kind':'settlement_capture','match_seq':1},{'kind':'closed','match_seq':1}]),[])
    def test_requires_closed_and_unique_boundary(self):
        with self.assertRaises(ValueError):eligible_groups([{'kind':'new_round_observed','match_seq':2}])
        events=[{'kind':k,'match_seq':2} for k in ('new_round_observed','settlement_capture','closed')]
        self.assertEqual(len(eligible_groups(events)),1)
        with self.assertRaises(ValueError):eligible_groups([events[0]]+events)
    def test_scope_violation_excluded(self):
        events=[{'kind':k,'match_seq':2} for k in ('new_round_observed','scope_violation','settlement_capture','closed')]
        self.assertEqual(eligible_groups(events),[])

if __name__=='__main__':unittest.main()
