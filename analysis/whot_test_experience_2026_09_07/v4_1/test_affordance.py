import unittest
from collections import Counter
from resident_calibration import client_enabled,draw_delta_accepted

class AffordanceTests(unittest.TestCase):
    def test_disabled_and_unknown_not_enabled(self):
        for c in ({},{'ink_red':93.6},{'ink_red':185.9}):self.assertFalse(client_enabled(c))
        self.assertTrue(client_enabled({'ink_red':231.5}))
    def test_unknown_count_is_observed_not_invented(self):
        old=Counter({(3,'square'):1})
        self.assertTrue(draw_delta_accepted(old,old+Counter({(4,'circle'):2}),None))
        self.assertFalse(draw_delta_accepted(old,old,None))
        self.assertFalse(draw_delta_accepted(old,Counter({(4,'circle'):2}),None))
    def test_explicit_two_requires_two(self):
        old=Counter({(3,'square'):1})
        self.assertFalse(draw_delta_accepted(old,old+Counter({(4,'circle'):1}),2))

if __name__=='__main__':unittest.main()
