import unittest
from fast_strategy import choose

def c(rank,shape):return dict(rank=rank,shape=shape)
class FastStrategyTests(unittest.TestCase):
    def test_baseline_and_no_candidate(self):
        h=[c(2,'circle'),c(5,'square')]
        self.assertIs(choose(h,h,'first_legal_play')[0],h[0])
        self.assertIsNone(choose(h,[],'fast_connectivity_v1')[0])
    def test_preserve_wild_and_connectivity(self):
        h=[c(20,'wild'),c(2,'circle'),c(2,'square'),c(5,'square'),c(7,'square')]
        self.assertIs(choose(h,h[:3],'fast_connectivity_v1')[0],h[2])
    def test_v11_lower_rank_only_breaks_connectivity_tie(self):
        h=[c(14,'circle'),c(2,'square')]
        self.assertIs(choose(h,h,'fast_connectivity_v1_1')[0],h[1])
    def test_only_wild_remains_legal(self):
        h=[c(20,'wild'),c(4,'star')]
        self.assertIs(choose(h,h[:1],'fast_connectivity_v1')[0],h[0])
    def test_cannot_choose_non_candidate_or_hidden_card(self):
        h=[c(3,'circle'),c(7,'triangle')]
        self.assertIs(choose(h,h[1:],'fast_connectivity_v1')[0],h[1])
        with self.assertRaises(ValueError):choose(h,[c(3,'circle')],'fast_connectivity_v1')
    def test_fixed_tie_and_no_mutation(self):
        h=[c(3,'circle'),c(7,'triangle')];before=[dict(x) for x in h]
        self.assertIs(choose(h,h,'fast_connectivity_v1')[0],h[0]);self.assertEqual(h,before)

if __name__=='__main__':unittest.main()
