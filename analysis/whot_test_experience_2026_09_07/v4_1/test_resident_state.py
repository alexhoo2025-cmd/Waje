import unittest
from resident_calibration import signature_for,effects

class StateTests(unittest.TestCase):
    def test_numeric_ocr_does_not_reset_stability(self):
        h=[{'rank':14,'shape':'square'}];t=[{'rank':10,'shape':'square'}]
        self.assertEqual(signature_for(h,t,True,'10 01'),signature_for(h,t,True,'01 10'))
    def test_effects_do_change_stability(self):
        self.assertNotEqual(signature_for([],[],True,''),signature_for([],[],True,'PICK 2'))
        self.assertEqual(effects('HOLD ON'),('HOLD ON',))
    def test_card_or_owner_changes_are_distinct(self):
        self.assertNotEqual(signature_for([],[],True,''),signature_for([],[],False,''))
        self.assertNotEqual(signature_for([{'rank':1,'shape':'circle'}],[],True,''),signature_for([{'rank':1,'shape':'star'}],[],True,''))

if __name__=='__main__':unittest.main()
