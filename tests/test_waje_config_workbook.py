from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from waje_config_workbook import make_diff, normalize_sheet_entries, redact_text, status_for_sheet  # noqa: E402


def payload(csv_text: str) -> dict:
    return {
        "annotated_csv": csv_text,
        "col_indices": ["A", "B", "C"],
        "actual_range": "A1:C3",
        "has_more": False,
        "warning_message": "",
    }


class WajeConfigWorkbookTests(unittest.TestCase):
    def test_hidden_and_obsolete_sheets_are_not_current_candidates(self):
        self.assertEqual(status_for_sheet("新包充值体系（老表作废）", True)[0], "obsolete")
        self.assertEqual(status_for_sheet("弹窗队列(老版)", True)[0], "historical_reference")
        self.assertEqual(status_for_sheet("游戏顺序", False)[0], "current_candidate")

    def test_normalization_retains_cells_but_redacts_sensitive_text(self):
        sheet = {"source_revision": 17221, "sheet_id": "sheet-1", "sheet_name": "7日任务", "is_hidden": False, "index": 1}
        entries, metadata = normalize_sheet_entries(
            sheet,
            payload(
                "[row=1] 配置路径,字段,正式配置\n"
                "[row=2] PSG.Config,token,token=secret-value\n"
                "[row=3] PSG.Config,奖励,\"{\"\"amount\"\":100,\"\"mail\"\":\"\"test@example.com\"\"}\"\n"
            ),
            {"merged_cells": []},
        )
        self.assertGreaterEqual(metadata["entry_count"], 3)
        values = "\n".join(str(item["normalized_value"]) for item in entries)
        self.assertNotIn("secret-value", values)
        self.assertNotIn("test@example.com", values)
        self.assertTrue(any(item["source_range"] == "C3" and "amount" in item["key_path"] for item in entries))

    def test_cell_level_diff_reports_added_modified_and_removed(self):
        base = {
            "revision": 1,
            "entries": [
                {"sheet_id": "s", "sheet_name": "游戏", "source_range": "A1", "key_path": "a", "content_hash": "one", "normalized_value": 1, "category": "游戏与场次经济"},
                {"sheet_id": "s", "sheet_name": "游戏", "source_range": "B1", "key_path": "b", "content_hash": "two", "normalized_value": 2, "category": "游戏与场次经济"},
            ],
        }
        current = {
            "revision": 2,
            "entries": [
                {"sheet_id": "s", "sheet_name": "游戏", "source_range": "A1", "key_path": "a", "content_hash": "changed", "normalized_value": 3, "category": "游戏与场次经济"},
                {"sheet_id": "s", "sheet_name": "游戏", "source_range": "C1", "key_path": "c", "content_hash": "three", "normalized_value": 4, "category": "游戏与场次经济"},
            ],
        }
        diff = make_diff(base, current)
        self.assertEqual(diff["summary"], {"added": 1, "modified": 1, "removed": 1})

    def test_redaction_removes_urls_emails_and_bearer_tokens(self):
        text = redact_text("Bearer abc.def password=abc https://example.com/a test@example.com")
        self.assertNotIn("abc.def", text)
        self.assertNotIn("example.com", text)
        self.assertNotIn("test@example.com", text)


if __name__ == "__main__":
    unittest.main()
