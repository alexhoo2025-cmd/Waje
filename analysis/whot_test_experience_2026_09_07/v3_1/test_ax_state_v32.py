import unittest
from ax_state_v32 import parse_full, eligible_observation


class AXRegression(unittest.TestCase):
    def test_full_hand_nested_and_draw_without_description(self):
        s = '''0 AXWebArea
  1 container Whot table
    2 checkbox (disabled) Description: 3 star, Value: 0
    3 text YOUR TURN
  4 container Turn time remaining
    5 text 9
  6 button Draw from deck, 29 cards remaining
  7 container Your hand
    8 container
      9 checkbox Description: 3 triangle, Value: 0
      10 checkbox (disabled) Description: 7 square, Value: 0
  11 checkbox Description: 20 whot, Value: 0'''
        p = parse_full(s)
        self.assertEqual([x['rank'] for x in p['hand']], [3, 7])
        self.assertEqual(p['draw']['index'], 6)
        self.assertTrue(p['hand'][0]['enabled'])
        self.assertEqual(p['seconds'], 9)

    def test_diff_rejected(self):
        for text in ('There has been no change in the accessibility tree.',
                     'The following is a diff from the previous accessibility tree'):
            self.assertEqual(parse_full(text)['status'], 'reject')

    def test_user_threshold(self):
        for count, expected in ((0, True), (3, True), (4, False), (None, False)):
            self.assertEqual(eligible_observation(settled=True, autoplay_entries=count,
                             continuous_count_verified=True)['eligible'], expected)
        self.assertFalse(eligible_observation(settled=True, autoplay_entries=1,
                         continuous_count_verified=False)['eligible'])


if __name__ == '__main__':
    unittest.main()
