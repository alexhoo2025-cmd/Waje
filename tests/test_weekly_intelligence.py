from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT / "scripts/build_weekly_intelligence_html.py"


class WeeklyIntelligenceTests(unittest.TestCase):
    def test_builds_ready_canonical_artifact_and_portable_html(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            start = date(2026, 8, 3)
            for offset in range(7):
                day = start + timedelta(days=offset)
                day_text = day.isoformat()
                output_dir = root / "data/outputs" / day_text
                processed_dir = root / "data/processed" / day_text
                output_dir.mkdir(parents=True)
                processed_dir.mkdir(parents=True)
                (output_dir / "quality.json").write_text(json.dumps({
                    "status": "ready",
                    "source_health": {"total": 2, "ok": 2, "failed": 0, "success_rate": 1.0, "failed_sources": []},
                    "content_health": {"unique_item_count": 1, "duplicate_count": 0, "stale_item_count": 0},
                    "analysis_health": {"manual_review_count": 0},
                }), encoding="utf-8")
                (processed_dir / "normalized-items.json").write_text(json.dumps({
                    "raw_item_count": 1, "unique_item_count": 1, "duplicate_count": 0, "stale_item_count": 0, "items": []
                }), encoding="utf-8")
                (output_dir / "analysis.json").write_text(json.dumps({"items": [{
                    "importance": 1,
                    "entity_id": "market",
                    "title": f"公开来源样例 {day_text}",
                    "source_type": "news_rss",
                    "freshness": "current",
                    "priority_reason": "测试用公开来源信号",
                    "topic": "product_update",
                    "url": "https://news.google.com/",
                }]}), encoding="utf-8")

            env = os.environ.copy()
            env["WAJE_ANALYST_ROOT"] = str(root)
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--date", "2026-08-10"],
                cwd=PROJECT,
                env=env,
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn("weekly HTML report", result.stdout)
            artifact_path = root / "data/outputs/weekly/2026-08-10/artifact.json"
            receipt_path = root / "data/outputs/weekly/2026-08-10/delivery-receipt.json"
            html_path = root / "knowledge/03-竞品/周报/2026-08-10-Waje竞品情报周报.html"
            preview_path = root / "output/html/Waje-weekly-report.html"
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(artifact["surface"], "report")
            self.assertEqual(artifact["snapshot"]["status"], "partial")
            self.assertEqual(len(artifact["manifest"]["charts"]), 1)
            self.assertEqual(len(artifact["manifest"]["tables"]), 5)
            self.assertEqual(receipt["summary"]["public_source_days"], 7)
            self.assertEqual(receipt["summary"]["internal_complete_days"], 0)
            self.assertEqual(receipt["delivery"]["validation"], "passed")
            self.assertEqual(receipt["delivery"]["package"], "passed")
            self.assertEqual(receipt["delivery"]["counts"]["html"], 0)
            self.assertEqual(receipt["preview_html"], "output/html/Waje-weekly-report.html")
            self.assertTrue(html_path.exists())
            self.assertTrue(preview_path.exists())
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("Waje 产品经营与竞品追踪周报", html)
            self.assertIn("核心经营指标的数据接入状态", html)
            self.assertIn("下周产品、商业化与数据行动清单", html)
            self.assertNotIn("WECHAT_ARTICLE_API_TOKEN", html)
            self.assertEqual(preview_path.read_bytes(), html_path.read_bytes())


if __name__ == "__main__":
    unittest.main()
