import unittest
from observer_contract import normalize_card,action_readiness

class ObserverTests(unittest.TestCase):
    def test_rank_confidence_is_not_card_confidence(self):
        c=normalize_card({'rank':11,'shape':'unknown','rank_score':.999,'confidence':0,'shape_score':None})
        result=action_readiness([c],'/game/6001-whot',30,{'status':'passed'})
        self.assertFalse(result['ready']);self.assertIn('shape_unknown',result['reasons'])
    def test_settlement_without_hand_is_not_vision_accuracy_failure(self):
        self.assertEqual(action_readiness([], '/game/6001-whot',20,{'status':'passed'})['reasons'],['no_hand_observed'])
    def test_expired_frame_cannot_be_used(self):
        c={'rank':5,'shape':'circle','confidence':.999}
        self.assertFalse(action_readiness([c],'/game/6001-whot',1000,{'status':'passed'})['ready'])

if __name__=='__main__':unittest.main()
