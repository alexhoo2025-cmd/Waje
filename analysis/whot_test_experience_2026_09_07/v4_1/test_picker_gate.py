import unittest
from resident_calibration import picker_verified,picker_target

class PickerTests(unittest.TestCase):
    def test_all_three_shapes_required(self):
        r={'pick_'+x:{'shape':x} for x in ('cross','triangle','star')}
        self.assertTrue(picker_verified(r))
        for key in r:
            self.assertFalse(picker_verified(dict(r,**{key:{'shape':'unknown'}})))
        self.assertFalse(picker_verified({}))
    def test_visible_hand_only_fixed_tie(self):
        self.assertEqual(picker_target([{'shape':'star'},{'shape':'star'},{'shape':'cross'}]),'star')
        self.assertEqual(picker_target([{'shape':'cross'},{'shape':'triangle'}]),'cross')
        self.assertEqual(picker_target([{'shape':'square'}]),'cross')

if __name__=='__main__':unittest.main()
