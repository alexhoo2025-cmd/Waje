from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import whot_lab_v2 as lab


class WhotLabV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db = self.root / "test.sqlite3"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_current_sources_migrate_to_expected_baseline(self) -> None:
        connection = lab.init_db(self.db)
        first = lab.migrate_sources(connection, lab.DEFAULT_RECEIPTS, lab.DEFAULT_MANUAL)
        self.assertEqual(first.as_dict(), {
            "read": 24,
            "inserted": 24,
            "updated": 0,
            "skipped": 0,
            "rejected": 0,
        })
        counts = connection.execute(
            """
            SELECT COUNT(*),SUM(result IN ('win','loss','draw')),
                   SUM(result='win'),SUM(result='loss'),SUM(result='unknown')
            FROM matches
            """
        ).fetchone()
        self.assertEqual(tuple(counts), (24, 23, 15, 8, 1))
        turns = connection.execute(
            "SELECT COUNT(*),SUM(actor_type IN ('bot','auto_play')) FROM turns"
        ).fetchone()
        self.assertEqual(tuple(turns), (19, 9))
        mislabeled = connection.execute(
            """
            SELECT COUNT(*) FROM matches
            WHERE (run_id LIKE '%normal-player%' OR run_id LIKE '%restart-normal%')
              AND strategy_arm <> 'baseline_unknown'
            """
        ).fetchone()[0]
        self.assertEqual(mislabeled, 0)
        second = lab.migrate_sources(connection, lab.DEFAULT_RECEIPTS, lab.DEFAULT_MANUAL)
        self.assertEqual(second.inserted, 0)
        self.assertEqual(second.skipped, 24)
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM matches").fetchone()[0], 24)
        connection.close()

    def test_schedule_is_balanced_and_matches_plan(self) -> None:
        schedule = lab.generate_schedule(77)
        counts = {
            arm: sum(row["strategy_arm"] == arm for row in schedule)
            for arm in lab.ALLOWED_STRATEGIES[1:]
        }
        self.assertEqual(counts, {
            "first_legal_play": 26,
            "reduce_high_point_cards": 26,
            "retain_special_or_wild_cards_until_needed": 25,
        })
        self.assertEqual([row["ordinal"] for row in schedule], list(range(1, 78)))

    def test_rule_engine_requires_turn_and_confidence(self) -> None:
        state = {
            "capture_confidence": 0.5,
            "rescan_count": 0,
            "is_player_turn": True,
            "pending_effect": "none",
            "table_card": {"rank": 3, "shape": "triangle"},
            "visible_hand": [{"rank": 12, "shape": "triangle"}],
        }
        self.assertEqual(lab.recommend_action(state, "first_legal_play")["action"], "rescan")
        state["rescan_count"] = 1
        self.assertEqual(lab.recommend_action(state, "first_legal_play")["action"], "unresolved_turn")
        state["capture_confidence"] = 0.95
        state["is_player_turn"] = False
        self.assertEqual(lab.recommend_action(state, "first_legal_play")["action"], "wait")

    def test_rule_engine_handles_special_states_and_strategies(self) -> None:
        base = {
            "capture_confidence": 0.95,
            "rescan_count": 0,
            "is_player_turn": True,
            "pending_effect": "pick_two",
            "table_card": {"rank": 2, "shape": "circle"},
            "visible_hand": [{"rank": 12, "shape": "triangle"}],
        }
        decision = lab.recommend_action(base, "first_legal_play")
        self.assertEqual((decision["action"], decision["draw_count"]), ("draw", 2))

        base["pending_effect"] = "none"
        base["table_card"] = {"rank": 3, "shape": "triangle"}
        base["visible_hand"] = [
            {"rank": 20, "shape": "wild"},
            {"rank": 4, "shape": "circle"},
            {"rank": 12, "shape": "triangle"},
        ]
        first = lab.recommend_action(base, "first_legal_play")
        high = lab.recommend_action(base, "reduce_high_point_cards")
        retain = lab.recommend_action(base, "retain_special_or_wild_cards_until_needed")
        self.assertEqual(first["chosen_card"]["rank"], 20)
        self.assertEqual(high["chosen_card"]["rank"], 12)
        self.assertEqual(retain["chosen_card"]["rank"], 12)
        self.assertEqual(first["target_shape"], "circle")

    def test_report_and_quality_are_read_only(self) -> None:
        connection = lab.init_db(self.db)
        lab.migrate_sources(connection, lab.DEFAULT_RECEIPTS, lab.DEFAULT_MANUAL)
        lab.persist_schedule(connection, lab.generate_schedule(77))
        lab.recompute_evaluations(connection)
        connection.close()
        before = hashlib.sha256(self.db.read_bytes()).hexdigest()
        readonly = lab.open_readonly(self.db)
        report = lab.read_report(readonly)
        quality = lab.quality_summary(readonly)
        readonly.close()
        after = hashlib.sha256(self.db.read_bytes()).hexdigest()
        self.assertEqual(before, after)
        self.assertEqual(report["quality"]["matches"]["completed"], 23)
        self.assertEqual(report["policy_selection"]["selected_strategy"], None)
        self.assertEqual(quality["matches"]["eligible_controlled"], 0)

    def test_sensitive_fields_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "sensitive_field_rejected"):
            lab.reject_sensitive_fields({"cookie": "secret"})
        with self.assertRaisesRegex(ValueError, "sensitive_field_rejected"):
            lab.reject_sensitive_fields({"turn": {"hidden_cards": [1, 2]}})

    def test_browser_gate_blocks_pwa_search_and_other_games(self) -> None:
        allowed = lab.validate_browser_gate({
            "browser_surface": "external_chrome",
            "current_url": "https://test-h5.wajew.com/game/6001-whot",
            "entry_method": "site_home_card_6001",
        })
        self.assertTrue(allowed["allowed"])
        for state in (
            {
                "browser_surface": "pwa",
                "current_url": "https://test-h5.wajew.com/game/6001-whot",
                "entry_method": "site_home_card_6001",
            },
            {
                "browser_surface": "external_chrome",
                "current_url": "https://www.google.com/search?q=whot",
                "entry_method": "external_search",
            },
            {
                "browser_surface": "external_chrome",
                "current_url": "https://test-h5.wajew.com/game/2002-wajespin",
                "entry_method": "site_home_card_6001",
            },
        ):
            self.assertFalse(lab.validate_browser_gate(state)["allowed"])

    def test_record_live_is_idempotent_and_accepts_full_controlled_context(self) -> None:
        payload = {
            "run": {
                "run_id": "whot-test-20260907T120000Z-controlled-v2",
                "environment": "test_h5",
                "status": "in_progress",
                "round_target": 100,
            },
            "match": {
                "round_no": 1,
                "observed_at": "2026-09-07T12:00:00+00:00",
                "strategy_arm": "first_legal_play",
                "room_stake_displayed_units": 1,
                "result": "win",
                "end_reason": "hand_empty",
                "settlement_visible": True,
                "settlement_displayed_units": 1.8,
                "turns": [
                    {
                        "event_seq": 1,
                        "actor_type": "human",
                        "is_player_turn": True,
                        "pending_effect": "none",
                        "table_rank": 3,
                        "table_shape": "triangle",
                        "hand_count_before": 2,
                        "legal_card_count": 1,
                        "action": "play",
                        "chosen_rank": 12,
                        "chosen_shape": "triangle",
                        "decision_ms": 900,
                        "policy_compute_ms": 1,
                        "action_accepted": True,
                        "timeout_flag": False,
                        "capture_confidence": 0.95,
                        "opponent_visible_card_counts": [4],
                    }
                ],
            },
        }
        source = self.root / "match.json"
        source.write_text(json.dumps(payload), encoding="utf-8")
        connection = lab.init_db(self.db)
        first = lab.record_live_observation(connection, source)
        second = lab.record_live_observation(connection, source)
        self.assertEqual((first.inserted, first.rejected), (1, 0))
        self.assertEqual((second.skipped, second.rejected), (1, 0))
        match = connection.execute(
            "SELECT eligibility_status,turn_capture_coverage FROM matches"
        ).fetchone()
        self.assertEqual(match["eligibility_status"], "eligible_controlled")
        self.assertEqual(match["turn_capture_coverage"], 1.0)
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM source_lineage").fetchone()[0], 1)
        connection.close()

    def test_completed_strategy_is_not_selectable_without_quality_gates(self) -> None:
        connection = lab.init_db(self.db)
        lab.migrate_sources(connection, lab.DEFAULT_RECEIPTS, lab.DEFAULT_MANUAL)
        lab.recompute_evaluations(connection)
        selectable = connection.execute(
            "SELECT COUNT(*) FROM strategy_evaluations WHERE eligible_for_selection=1"
        ).fetchone()[0]
        self.assertEqual(selectable, 0)
        connection.close()


if __name__ == "__main__":
    unittest.main()
