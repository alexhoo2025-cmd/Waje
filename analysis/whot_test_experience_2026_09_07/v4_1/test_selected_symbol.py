import unittest
from resident_calibration import selected_hand_complete

class RaisedSymbolTests(unittest.TestCase):
    def setUp(self):
        self.raised=[dict(rank=11,shape='triangle',rank_score=.99,
                          shape_evidence={'marker_consistent':True},box=[.56,.74,.02,.035])]
        self.symbol=dict(rank=None,ink_red=235,box=[.588,.793,.025,.035])
        self.region=dict(cards=[{}]*4,number_group_count=5,
                         numbers=[dict(rank=x) for x in (13,2,3,14)]+[self.symbol])
    def test_symbol_inside_selected_card(self):
        self.assertTrue(selected_hand_complete(self.region,self.raised))
    def test_unrelated_unknown_stays_rejected(self):
        self.symbol['box']=[.4,.793,.025,.035]
        self.assertFalse(selected_hand_complete(self.region,self.raised))
    def test_unknown_rank_not_symbol(self):
        self.symbol['box']=[.57,.741,.025,.035]
        self.assertFalse(selected_hand_complete(self.region,self.raised))
    def test_dim_or_multiple_unknowns_rejected(self):
        self.symbol['ink_red']=93
        self.assertFalse(selected_hand_complete(self.region,self.raised))
        self.symbol['ink_red']=235
        self.region['numbers'].append(dict(self.symbol))
        self.assertFalse(selected_hand_complete(self.region,self.raised))
    def test_no_verified_raised_card(self):
        self.assertFalse(selected_hand_complete(self.region,[]))

if __name__=='__main__':unittest.main()
