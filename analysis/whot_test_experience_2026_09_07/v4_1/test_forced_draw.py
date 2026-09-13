import unittest
from resident_calibration import forced_draw_count

class ForcedDrawTests(unittest.TestCase):
    def test_explicit_pick_two(self):self.assertEqual(forced_draw_count('PICK 2'),2)
    def test_plain_two_is_not_instruction(self):self.assertIsNone(forced_draw_count('2'))
    def test_other_counts_and_conflicts_reject(self):
        for value in ('PICK 20','PICK 4','PICK','PICK 2 MATCH SYMBOL','PICK 2 HOLD ON'):
            self.assertIsNone(forced_draw_count(value))

if __name__=='__main__':unittest.main()
