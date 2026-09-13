import json
import tempfile
import unittest
from pathlib import Path

from legacy6001 import (
    ARMS,
    GAME,
    ROUTE,
    Store,
    build_schedule,
    choose_decision,
    confirm_action,
    report,
    safe_route,
)


class Legacy6001Tests(unittest.TestCase):
    def test_schedule_is_exact_and_reproducible(self):
        a, b = build_schedule(6001), build_schedule(6001)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 100)
        self.assertEqual({x["strategy_arm"] for x in a}, set(ARMS))
        self.assertEqual({k: sum(x["strategy_arm"] == k for x in a) for k in ARMS},
                         {ARMS[0]: 34, ARMS[1]: 33, ARMS[2]: 33})
        self.assertEqual({bet: sum(x["bet_display"] == bet for x in a)
                          for bet in (1, 100, 200, 1000, 5000)},
                         {1: 20, 100: 20, 200: 20, 1000: 25, 5000: 15})
        self.assertEqual({n: sum(x["requested_players"] == n for x in a)
                          for n in (2, 3, 4)}, {2: 60, 3: 20, 4: 20})

    def test_route_gate_rejects_query_and_wrong_host(self):
        self.assertTrue(safe_route("https://test-h5.wajetan.com/game/6001-whot"))
        self.assertFalse(safe_route("https://test-h5.wajetan.com/game/6001-whot?gid=1"))
        self.assertFalse(safe_route("https://test-h5.wajew.com/game/6001-whot"))
        self.assertFalse(safe_route("http://test-h5.wajetan.com/game/6001-whot"))

    def state(self, **overrides):
        base = dict(client_game_id=GAME, route=ROUTE, phase="player_turn",
                    action_owner="self", autoplay=False, pending_effect="none",
                    table_card={"rank": 3, "shape": "circle"}, effective_shape="circle",
                    visible_hand=[{"rank": 14, "shape": "square"},
                                  {"rank": 3, "shape": "circle"},
                                  {"rank": 20, "shape": "whot"}],
                    state_seq="s1", deadline_ms=999999, capture_confidence=.99)
        base.update(overrides)
        return base

    def test_strategies_and_special_state_are_deterministic(self):
        rules = {"shapes": ["circle", "square", "triangle", "star", "cross"],
                 "points": {"3": 3, "14": 14, "20": 20}}
        self.assertEqual(choose_decision(self.state(), ARMS[0], rules)["chosen_card"]["rank"], 3)
        self.assertEqual(choose_decision(self.state(), ARMS[1], rules)["chosen_card"]["rank"], 20)
        self.assertEqual(choose_decision(self.state(), ARMS[2], rules)["chosen_card"]["rank"], 3)
        special = self.state(pending_effect="whot_shape_selection")
        self.assertEqual(choose_decision(special, ARMS[2], rules)["action"], "select_shape")
        self.assertEqual(choose_decision(self.state(autoplay=True), ARMS[0], rules)["action"], "stop")

    def test_confirmation_rejects_same_frame_and_checks_hand_table(self):
        before = self.state()
        decision = {"action": "play", "chosen_card": {"rank": 3, "shape": "circle"}}
        self.assertIsNone(confirm_action(before, before, decision)["accepted"])
        after = self.state(state_seq="s2", visible_hand=[{"rank": 14, "shape": "square"},
                                                            {"rank": 20, "shape": "whot"}],
                           table_card={"rank": 3, "shape": "circle"})
        self.assertTrue(confirm_action(before, after, decision)["accepted"])
        wrong = self.state(state_seq="s3", visible_hand=after["visible_hand"],
                           table_card={"rank": 8, "shape": "circle"})
        self.assertFalse(confirm_action(before, wrong, decision)["accepted"])

    def test_store_is_idempotent_and_formal_qualification_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "legacy.sqlite3"
            store = Store(db)
            run_id = store.create_run(seed=6001)
            attempt_id = store.add_attempt(run_id, requested_players=2, bet=1,
                                           source="attempt-1")
            same = store.add_attempt(run_id, requested_players=2, bet=1,
                                     source="attempt-1")
            self.assertEqual(attempt_id, same)
            match_id = store.add_match(attempt_id, strategy_arm=ARMS[0], source="match-1")
            result = store.settle(match_id, result="win", end_reason="hand_empty",
                                   player_points=0, opponent_points=20, player_cards=0,
                                   opponent_cards=3, autoplay_observed=False,
                                   page_stake=1, page_return=1.8,
                                   return_assumption="gross_return_assumed")
            self.assertFalse(result["qualified"])
            self.assertIn("turn_evidence_missing", result["exclusion_reason"])
            control = store.conn.execute(
                "SELECT control_source FROM matches WHERE match_id=?", (match_id,)
            ).fetchone()[0]
            self.assertEqual(control, "unknown")
            auto_match = store.add_match(attempt_id, strategy_arm=ARMS[1], source="match-auto-1")
            store.settle(auto_match, result="loss", end_reason="autoplay_end",
                         player_points=10, opponent_points=0, player_cards=2,
                         opponent_cards=0, autoplay_observed=True, manual_intervention=False,
                         page_stake=1, page_return=0)
            auto_control = store.conn.execute(
                "SELECT control_source FROM matches WHERE match_id=?", (auto_match,)
            ).fetchone()[0]
            self.assertEqual(auto_control, "autoplay")
            store.close()
            self.assertEqual(report(db, assume_gross=True)["status"], "provisional")

    def test_sensitive_payload_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "legacy.sqlite3")
            run_id = store.create_run()
            with self.assertRaises(ValueError):
                store.add_attempt(run_id, requested_players=2, bet=1,
                                  source="bad", opponent_name="redacted")
            store.close()


if __name__ == "__main__":
    unittest.main()
