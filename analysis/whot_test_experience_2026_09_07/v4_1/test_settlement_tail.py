import unittest
from resident_calibration import observe_settlement,valid_numeric

class TailTests(unittest.TestCase):
    def run_tail(self,bet='Bet: 1',round_value='123456',expected=None):
        events=[];calls=[]
        binding={'origin':'https://test-h5.wajetan.com','path':'/game/6001-whot','content_bounds':[0,0,1470,865]}
        class Fake:
            def call(self,op,**kw):
                calls.append(op)
                if op=='inspect':return binding
                if op=='capture':
                    assert 'balance' not in kw['regions']
                    return {'regions':{'title':{'text':[{'value':'VICTORY'}]},'bet':{'text':[{'value':bet}]},'round':{'text':[{'value':round_value}]},'returns':{'text':[{'value':'+1.8'},{'value':'-1'},{'value':'not numeric'}]},'points':{'text':[{'value':'0'}]}}}
                raise AssertionError('unexpected input operation')
        observe_settlement(Fake(),{'pid':1,'id':2,'bounds':{}},binding,lambda kind,**kw:events.append(dict(kind=kind,**kw)),expected,seconds=1)
        return calls,events
    def test_readonly_and_numeric_output(self):
        calls,events=self.run_tail()
        self.assertEqual(calls,['inspect','capture','inspect','capture'])
        self.assertEqual(events[0]['kind'],'settlement_capture')
        self.assertEqual(len(events[0]['numeric_evidence']['returns']),2)
    def test_incomplete_numeric_rejected(self):
        for value in ('+1.','1,','12,34','NaN',''):
            self.assertFalse(valid_numeric(value))
        self.assertTrue(valid_numeric('+1.8',True))
        self.assertFalse(valid_numeric('8',True))
    def test_high_bet_not_attributed(self):
        _,events=self.run_tail('Bet: 50000')
        self.assertEqual(events[0]['reason'],'unexpected_bet')
    def test_different_round_not_attributed(self):
        _,events=self.run_tail(expected='another-round-hash')
        self.assertEqual(events[0]['reason'],'different_round')

if __name__=='__main__':unittest.main()
