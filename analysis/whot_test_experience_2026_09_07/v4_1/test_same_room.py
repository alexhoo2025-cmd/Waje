import unittest
from same_room import verified_target

class SameRoomTests(unittest.TestCase):
    def fixture(self):return {'title':{'text':[{'value':'VICTORY'}]},'bet':{'text':[{'value':'Bet: 1000'}]},'again':{'text':[{'value':'Play again 4','box':[.56,.81,.14,.05]}]}}
    def test_exact_button(self):
        x,y=verified_target(self.fixture(),1000)
        self.assertAlmostEqual(x,.63);self.assertAlmostEqual(y,.835)
    def test_never_upgrade(self):
        r=self.fixture();r['again']['text'][0]['value']='Win more'
        with self.assertRaises(ValueError):verified_target(r,1000)
    def test_wrong_bet_or_no_settlement(self):
        with self.assertRaises(ValueError):verified_target(self.fixture(),1)
        r=self.fixture();r['title']['text']=[]
        with self.assertRaises(ValueError):verified_target(r,1000)
    def test_ambiguous_buttons(self):
        r=self.fixture();r['again']['text']*=2
        with self.assertRaises(ValueError):verified_target(r,1000)

if __name__=='__main__':unittest.main()
