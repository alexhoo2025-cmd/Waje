import unittest
from record_resident_settlement import own_result_display

class SettlementRowTests(unittest.TestCase):
    def item(self,value,y=.335):return {'value':value,'box':[.433,y,.045,.035]}
    def test_opponent_only_not_misattributed(self):
        self.assertIsNone(own_result_display({'returns':[self.item('-1',.449)]}))
    def test_unordered_rows(self):
        r=own_result_display({'returns':[self.item('-1',.449),self.item('+1.8')]})
        self.assertEqual(r['value'],1.8)
        self.assertEqual(r['semantics'],'unverified_gross_vs_net')
    def test_loss_and_ambiguous(self):
        self.assertEqual(own_result_display({'returns':[self.item('-1') ]})['value'],-1)
        self.assertIsNone(own_result_display({'returns':[self.item('-1'),self.item('+1.8')]}))
    def test_missing_box_and_partial(self):
        self.assertIsNone(own_result_display({'returns':[{'value':'+1.8'}]}))
        self.assertIsNone(own_result_display({'returns':[self.item('+1.')]}))
    def test_wider_negative_amount_preserves_sign(self):
        r=own_result_display({'returns':[{'value':'-1000','box':[.412,.335,.08,.035]}]})
        self.assertEqual(r['raw'],'-1000');self.assertEqual(r['value'],-1000)

if __name__=='__main__':unittest.main()
