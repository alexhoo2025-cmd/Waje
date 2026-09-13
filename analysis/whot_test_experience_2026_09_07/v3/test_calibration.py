import unittest

from calibrate_live import SHAPE_POINTS, candidate


def card(rank, shape, confidence=1.0, point=None):
    return {
        "rank": rank,
        "shape": shape,
        "confidence": confidence,
        "point": point or [0.45, 0.87],
        "box": [0.4, 0.77, 0.02, 0.03],
    }


def regions(hand, table, turn="ZAMU YAKO", autoplay="Dau: 1"):
    return {
        "turn": {"text": [{"value": turn}]},
        "autoplay": {"text": [{"value": autoplay}]},
        "hand": {"cards": hand},
        "table": {"cards": [table]},
        "stake": {"text": [{"value": "Dau: 1"}]},
    }


class CalibrationDecisionTests(unittest.TestCase):
    def test_normal_overlay_does_not_hide_action(self):
        r = regions(
            [card(7, "circle", point=[0.38, 0.87]), card(4, "square")],
            card(7, "triangle"),
            autoplay="Cheza kadi kiotomatiki. Gusa skrini ili kuendelea na mchezo",
        )
        action = candidate(r)
        self.assertEqual(action["action"], "play")
        self.assertEqual(action["chosen"]["rank"], 7)

    def test_whot_selector_uses_majority_shape(self):
        r = regions(
            [card(4, "circle"), card(7, "circle"), card(12, "cross")],
            card(20, "wild"),
        )
        action = candidate(r, shape_ready=True)
        self.assertEqual(action["action"], "select_shape")
        self.assertEqual(action["target_shape"], "circle")
        self.assertEqual(action["point"], SHAPE_POINTS["circle"])

    def test_whot_without_selector_stops(self):
        r = regions([card(4, "circle")], card(20, "wild"))
        self.assertEqual(candidate(r)["reason"], "special_state_requires_calibration")

    def test_unknown_card_is_rejected(self):
        r = regions([card(4, "unknown")], card(7, "star"))
        self.assertEqual(candidate(r)["reason"], "card_recognition_unresolved")


if __name__ == "__main__":
    unittest.main()
