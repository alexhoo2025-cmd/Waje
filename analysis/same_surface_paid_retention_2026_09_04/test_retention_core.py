import unittest
from datetime import date
from retention_core import classify,runtime_surface,target_day,subplatform_state,weighted_rate,STATES

class ContractTests(unittest.TestCase):
    def test_mature_14(self):self.assertEqual(target_day('2026-08-20',14),date(2026,9,2))
    def test_mature_30(self):self.assertEqual(target_day('2026-08-01',30),date(2026,8,30))
    def test_mature_90(self):self.assertEqual(target_day('2026-06-01',90),date(2026,8,29))
    def test_immature(self):self.assertEqual(classify('APP',{'APP'},mature=False),'immature')
    def test_cross_surface(self):self.assertEqual(classify('H5',{'APP'}),'only_other')
    def test_both(self):self.assertEqual(classify('H5',{'APP','H5'}),'same_and_other')
    def test_unknown_and_other(self):self.assertEqual(classify('H5',{'APP'},unknown_event=True),'unknown_return_surface')
    def test_unknown_does_not_erase_same(self):self.assertEqual(classify('H5',{'H5'},unknown_event=True),'same_only')
    def test_account_only(self):self.assertEqual(classify('APP',set(),account_active=True),'unknown_return_surface')
    def test_missing_anchor(self):self.assertEqual(classify(None,{'APP'}),'unknown_anchor')
    def test_no_activity(self):self.assertEqual(classify('APP',set()),'no_observed_return')
    def test_app_rollup(self):
        self.assertEqual(classify('APP',{runtime_surface(client_type=2)}),'same_only')
        self.assertEqual(subplatform_state(1,{2}),'only_other')
    def test_native_webview(self):self.assertEqual(runtime_surface(client_type=3,display_mode='browser',host_app=True),'APP')
    def test_web_unknown(self):self.assertIsNone(runtime_surface(client_type=3))
    def test_pwa(self):self.assertEqual(runtime_surface(client_type=3,display_mode='standalone'),'PWA')
    def test_fullscreen_not_install_proof(self):self.assertIsNone(runtime_surface(client_type=3,display_mode='fullscreen'))
    def test_h5(self):self.assertEqual(runtime_surface(client_type=3,display_mode='browser'),'H5')
    def test_weighting(self):self.assertAlmostEqual(weighted_rate([{'same_surface_users':1,'mature_users':2},{'same_surface_users':1,'mature_users':8}]),.2)
    def test_no_zero_fill(self):self.assertIsNone(weighted_rate([{'same_surface_users':0,'mature_users':0}]))
    def test_states_partition(self):
        states=[classify('H5',s,unknown_event=u,account_active=a) for s,u,a in [({'H5'},False,True),({'H5','APP'},False,True),({'APP'},False,True),(set(),False,False),(set(),False,True)]]
        self.assertEqual(set(states),set(STATES))

if __name__=='__main__':unittest.main()
