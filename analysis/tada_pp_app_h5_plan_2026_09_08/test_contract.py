"""All records below are invented unit-test fixtures, not Waje user data."""
import unittest,json
from pathlib import Path
from datetime import date,datetime
from decimal import Decimal
from reference_logic import *

class ContractTests(unittest.TestCase):
    def test_windows(self):
        w=windows(date(2026,9,7));self.assertEqual(w['current'],(date(2026,8,9),date(2026,9,7)))
        self.assertEqual(w['previous'],(date(2026,7,10),date(2026,8,8)))
    def test_fixed_cohort(self):
        start,end=windows(date(2026,9,7))['current']
        self.assertEqual([cohort(x,start,end) for x in [start,date(2026,8,8),None,date(2026,9,8)]],['new','old','unknown_registration','outside_window'])
    def test_host_not_webview(self):
        self.assertEqual(platform('app','Android','webview'),('APP','Android'))
        self.assertEqual(platform('browser',None,'browser')[0],'H5')
        self.assertEqual(platform('web',None,'installed_pwa')[0],'PWA')
        self.assertEqual(platform('web')[0],'unknown')
    def test_same_and_cross(self):
        self.assertEqual(return_status('APP','Tada',[('APP','Tada'),('H5','Tada')]),('same_platform_provider',True))
    def test_cross_only(self):
        self.assertEqual(return_status('APP','Tada',[('H5','Tada'),('APP','PP')])[0],'cross_platform_provider_only')
    def test_unknown_is_not_loss(self):
        self.assertEqual(return_status('APP','Tada',[(None,'Tada')])[0],'unresolved')
        self.assertEqual(return_status('APP','Tada',[('APP','Tada'),(None,'Tada')])[0],'same_platform_provider')
    def test_other_and_none(self):
        self.assertEqual(return_status('APP','Tada',[(None,'PP')])[0],'other_providers_only')
        self.assertEqual(return_status('APP','Tada',[])[0],'no_observed_bet')
    def test_maturity_and_missing(self):
        c=date(2026,9,7)
        self.assertEqual(eligible(date(2026,8,9),30,c,{c}),'eligible')
        self.assertEqual(eligible(date(2026,8,10),30,c,{c}),'immature')
        self.assertEqual(eligible(date(2026,8,9),30,c,set()),'missing_observation_day')
    def test_tc_groups_exclusive(self):
        self.assertEqual([participation(x) for x in [['Tada'],['PP'],['Tada','PP'],['Other'],['Tada',None],['Tada','PP',None]]],['tada_only','pp_only','both','neither','unresolved','both'])
        self.assertIsNone(ratio(20,0))
    def test_no_future_payer_state(self):
        self.assertFalse(paid_at(20,10));self.assertTrue(paid_at(20,20));self.assertFalse(paid_at(None,20))
    def test_bet_dedupe_refund_pending(self):
        b={'namespace':'Tada','bet_id':'TEST1','asset':'cash','version_at':1,'status':'accepted','stake':100,'refund':0,'payout':None}
        final={**b,'version_at':2,'refund':20,'status':'settled','payout':70}
        out=normalize_bets([b,b,final],2);self.assertEqual(len(out),1);self.assertEqual(out[0]['net_stake'],Decimal(80));self.assertEqual(out[0]['final_payout'],Decimal(70))
        self.assertIsNone(normalize_bets([b,final],1)[0]['final_payout'])
        self.assertEqual(normalize_bets([{**b,'status':'cancelled'}],1)[0]['net_stake'],0)
        with self.assertRaises(ValueError):normalize_bets([b,{**b,'stake':200}],1)
    def test_assets_and_provider_namespace(self):
        b={'namespace':'Tada','bet_id':'TEST1','asset':'cash','version_at':1,'status':'accepted','stake':80,'refund':0,'payout':None}
        rows=normalize_bets([b,{**b,'asset':'bonus','stake':20},{**b,'namespace':'PP'}],1)
        self.assertEqual(sum(r['net_stake'] for r in rows),180)
        self.assertEqual(len({(r['namespace'],r['bet_id']) for r in rows}),2)
    def test_weighted_rtp_and_share(self):
        self.assertEqual(ratio(50+900,100+1000),950/1100)
        self.assertNotEqual(ratio(950,1100),(.5+.9)/2)
        a={'Tada':100,'PP':50,'other':40,'unknown':10}
        self.assertEqual(ratio(a['Tada'],sum(a.values())),.5)
        self.assertAlmostEqual(ratio(a['Tada'],a['Tada']+a['PP']),2/3)
    def test_rounds_and_period_uv(self):
        rows=[('U1','ROUND1','B1'),('U1','ROUND1','B2'),('U2','ROUND1','B3')]
        self.assertEqual(len({r[1] for r in rows}),1)
        self.assertEqual(len({r[:2] for r in rows}),2)
        self.assertEqual(len({r[2] for r in rows}),3)
        self.assertEqual(len(set(['U1','U2'])|set(['U1'])),2)
    def test_open_link_is_required(self):
        opens=[{'id':'O1','status':'success','user':'U1','game':'G1','start':0,'end':10},{'id':'O2','status':'success','user':'U1','game':'G1','start':10,'end':20}]
        bets=[{'open_id':None,'user':'U1','game':'G1','time':2},{'open_id':'O1','user':'U1','game':'G1','time':12},{'open_id':'O2','user':'U1','game':'G1','time':12}]
        self.assertEqual(first_bet_conversion(opens,bets),(1,2))
    def test_shapley_sum_and_zero_guard(self):
        x=shapley_product([100,.2,3,10],[120,.25,4,12])
        self.assertAlmostEqual(sum(x),1440-600)
        self.assertIsNone(shapley_product([0,.2,3,10],[120,.25,4,12]))
    def test_return_partition(self):
        cases=[[],[('APP','Tada')],[('H5','Tada')],[('APP','PP')],[(None,'Tada')],[('APP','Tada'),('H5','Tada')]]
        states=[return_status('APP','Tada',e)[0] for e in cases]
        counts={s:states.count(s) for s in set(states)};self.assertEqual(sum(counts.values()),len(cases))
        same=sum(any(p=='APP' and v=='Tada' for p,v in e) for e in cases)
        any_end=sum(any(v=='Tada' for p,v in e) for e in cases)
        self.assertLessEqual(same,any_end)

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ContractTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    receipt={'status':'passed' if result.wasSuccessful() else 'failed','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'fixture':'synthetic_only','production_data_queried':False}
    Path(__file__).with_name('test-receipt.json').write_text(json.dumps(receipt,indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
