from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import build_weekly_intelligence_report as weekly_report  # noqa: E402
import run_weekly_intelligence_pipeline as weekly_pipeline  # noqa: E402


class WeeklyIntelligencePipelineTests(unittest.TestCase):
    def test_week_window_is_previous_friday_to_thursday(self) -> None:
        start, end = weekly_pipeline.week_window(date(2026, 8, 21))
        self.assertEqual(start.isoformat(), "2026-08-14")
        self.assertEqual(end.isoformat(), "2026-08-20")
        self.assertEqual(weekly_pipeline.batch_id(date(2026, 8, 21), start, end), "waje-weekly-2026-08-14-2026-08-20-2026-08-21")

    def test_weekly_report_uses_batch_outputs_without_daily_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            processed = root / "data/processed/weekly/2026-08-21"
            output = root / "data/outputs/weekly/2026-08-21"
            processed.mkdir(parents=True)
            output.mkdir(parents=True)
            (processed / "normalized-items.json").write_text(json.dumps({"raw_item_count": 2, "unique_item_count": 1, "duplicate_count": 1, "items": []}), encoding="utf-8")
            (output / "analysis.json").write_text(json.dumps({"items": [{
                "importance": 2,
                "entity_id": "waje",
                "topic": "promotion",
                "title": "公开奖励机制样例",
                "priority_reason": "product_or_commercial_signal",
                "summary": "用于测试的公开信号",
                "source_type": "official_site",
                "url": "https://example.com/source"
            }]}), encoding="utf-8")
            (output / "quality.json").write_text(json.dumps({"status": "ready", "source_health": {"ok": 1, "total": 1}}), encoding="utf-8")
            (output / "source-verification.json").write_text(json.dumps({"status": "pending_manual_review", "items": []}), encoding="utf-8")
            report_path, receipt = weekly_report.build_report(root, date(2026, 8, 21))
            self.assertTrue(report_path.exists())
            self.assertTrue((root / "knowledge/03-竞品/周报/2026-08-21-Waje产品与竞品情报周报.html").exists())
            self.assertFalse((root / "knowledge/03-竞品/日报/2026-08-21-Waje产品与竞品情报.md").exists())
            self.assertEqual(receipt["item_count"], 1)

    def test_normalization_is_idempotent_for_same_item_url(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw = root / "data/raw/weekly/2026-08-21"
            processed = root / "data/processed/weekly/2026-08-21"
            raw.mkdir(parents=True)
            html_path = raw / "waje_1_hash.html"
            html_path.write_text("<html><title>Waje</title><body>promotion bonus</body></html>", encoding="utf-8")
            (raw / "manifest.json").write_text(json.dumps({"items": [{"status": "ok", "source_id": "waje_1", "entity_id": "waje", "source_type": "official_site", "url": "https://example.com", "fetched_at": "2026-08-21T15:00:00+08:00", "sha256": "hash", "path": "data/raw/weekly/2026-08-21/waje_1_hash.html"}]}), encoding="utf-8")
            first = weekly_pipeline.normalize_weekly(date(2026, 8, 21), raw, processed)
            second = weekly_pipeline.normalize_weekly(date(2026, 8, 21), raw, processed)
            self.assertEqual(first["unique_item_count"], 1)
            self.assertEqual(first["unique_item_count"], second["unique_item_count"])


if __name__ == "__main__":
    unittest.main()
