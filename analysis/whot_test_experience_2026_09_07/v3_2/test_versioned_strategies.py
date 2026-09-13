import unittest

from versioned_strategies import ARMS, LEGACY_6001, NEW_9006, confirm, decide, flow


class VersionedStrategyTests(unittest.TestCase):
    def base(self, version):
        spec = LEGACY_6001 if version == "6001" else NEW_9006
        return dict(client_game_id=version, route=spec.route, phase="player_turn",
                    is_player_turn=True, action_owner="self", autoplay=False,
                    pending_effect="none", table_card={"rank": 3, "shape": "circle"},
                    effective_shape="circle", capture_confidence=.99, state_seq="a",
                    visible_hand=[{"rank": 1, "shape": "square", "enabled": True},
                                  {"rank": 3, "shape": "circle", "enabled": True},
                                  {"rank": 20, "shape": "whot", "enabled": True}])

    def test_6001_is_single_click_and_rejects_new_two_step_action(self):
        s = self.base("6001")
        d = decide("6001", s, ARMS[0])
        self.assertEqual(d["action"], "play")
        self.assertEqual(d["input_steps"], 1)
        self.assertNotEqual(d["action"], "select_card")

    def test_9006_is_two_step(self):
        s = self.base("9006")
        d1 = decide("9006", s, ARMS[0])
        self.assertEqual(d1["action"], "select_card")
        self.assertEqual(d1["input_steps"], 1)
        s2 = dict(s, state_seq="b", selected_card=d1["chosen_card"],
                  visible_hand=[dict(d1["chosen_card"], selected=True),
                                {"rank": 20, "shape": "whot", "enabled": True}])
        d2 = decide("9006", s2, ARMS[0])
        self.assertEqual(d2["action"], "play_selected")

    def test_special_shape_rules_are_version_specific_but_pure(self):
        for version in ("6001", "9006"):
            s = dict(self.base(version), pending_effect="whot_shape_selection",
                     visible_hand=[{"rank": 1, "shape": "triangle"},
                                   {"rank": 2, "shape": "triangle"},
                                   {"rank": 3, "shape": "circle"}])
            d = decide(version, s, ARMS[2])
            self.assertEqual(d["action"], "select_shape")
            self.assertEqual(d["target_shape"], "triangle")

    def test_6001_unverified_special_rank_fails_closed(self):
        s = dict(self.base("6001"), table_card={"rank": 2, "shape": "circle"})
        self.assertEqual(decide("6001", s, ARMS[0])["action"], "stop")

    def test_confirm_protocols_differ(self):
        before = self.base("6001")
        after = dict(before, state_seq="b", visible_hand=[{"rank": 1, "shape": "square"},
                                                           {"rank": 20, "shape": "whot"}],
                     table_card={"rank": 3, "shape": "circle"})
        d = {"action": "play", "chosen_card": {"rank": 3, "shape": "circle"}}
        self.assertTrue(confirm("6001", before, after, d)["accepted"])
        before2 = self.base("9006")
        selected = dict(before2, state_seq="b", selected_card={"rank": 3, "shape": "circle"})
        self.assertTrue(confirm("9006", before2, selected,
                                {"action": "select_card", "chosen_card": {"rank": 3, "shape": "circle"}})["accepted"])

    def test_flows_are_not_shared(self):
        self.assertNotEqual(flow("6001"), flow("9006"))
        self.assertIn("SINGLE_CLICK", flow("6001"))
        self.assertIn("SELECT_CARD", flow("9006"))


if __name__ == "__main__":
    unittest.main()
