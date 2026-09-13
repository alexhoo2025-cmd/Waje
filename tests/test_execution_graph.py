from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.execution_graph import build_execution_graph, latest_events, record_and_refresh


class ExecutionGraphTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "config").mkdir()
        (self.root / "scripts").mkdir()
        (self.root / "tools").mkdir()
        (self.root / "data/outputs/weekly/2026-09-10").mkdir(parents=True)
        (self.root / "analysis/receipted-report").mkdir(parents=True)
        (self.root / ".venv/lib").mkdir(parents=True)
        (self.root / ".venv/lib/noise.py").write_text("import irrelevant\n", encoding="utf-8")
        (self.root / "config/execution_graph.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "report_job_ids": ["weekly_report"],
                    "manual_workflows": ["manual-flow"],
                    "ad_hoc_inclusion": {
                        "root": "analysis",
                        "required_markers": ["artifact.json", "receipt.json", "last-approved-version.json"],
                    },
                    "declared_schedules": [
                        {
                            "automation_id": "audit",
                            "expected_rrule": "FREQ=WEEKLY;BYDAY=FR;BYHOUR=17;BYMINUTE=0",
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (self.root / "jobs").mkdir()
        (self.root / "jobs/manifest.json").write_text(
            json.dumps(
                {
                    "name": "fixture",
                    "timezone": "Asia/Hong_Kong",
                    "stages": [
                        {
                            "id": "weekly_report",
                            "automation_id": "audit",
                            "schedule": "每周五 17:00",
                            "script": "scripts/report.py",
                            "input": "config/report.json + authorized Lark Sheets",
                            "output": "data/outputs/weekly/YYYY-MM-DD/report.md + data/outputs/weekly/YYYY-MM-DD/run-log.json",
                        },
                        {
                            "id": "manual_browser_workbooks",
                            "status": "manual_only",
                            "workflow": ["manual-flow"],
                            "reason": "visible browser and approval required",
                        },
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (self.root / "config/report.json").write_text("{}\n", encoding="utf-8")
        (self.root / "scripts/helper.py").write_text("VALUE = 1\n", encoding="utf-8")
        (self.root / "scripts/report.py").write_text(
            "from helper import VALUE\nimport subprocess\nsubprocess.run(['python3', 'scripts/helper.py'])\n",
            encoding="utf-8",
        )
        (self.root / "data/outputs/weekly/2026-09-10/run-log.json").write_text(
            json.dumps({"job_id": "weekly_report", "status": "partial", "finished_at": "2026-09-10T10:00:00+08:00"}),
            encoding="utf-8",
        )
        (self.root / "analysis/receipted-report/receipt.json").write_text(
            json.dumps({"status": "ok", "finished_at": "2026-09-10T10:00:00+08:00"}),
            encoding="utf-8",
        )
        (self.root / "data/outputs/weekly/2026-09-10/artifact.json").write_text("{}\n", encoding="utf-8")
        (self.root / "data/outputs/weekly/2026-09-10/delivery-receipt.json").write_text(
            json.dumps(
                {
                    "status": "ok",
                    "finished_at": "2026-09-10T10:00:00+08:00",
                    "artifact": "data/outputs/weekly/2026-09-10/artifact.json",
                }
            ),
            encoding="utf-8",
        )
        (self.root / "analysis/receipted-report/last-approved-version.json").write_text(
            json.dumps({"status": "ok", "revision": "r1"}),
            encoding="utf-8",
        )
        self.automations = self.root / "automations/audit"
        self.automations.mkdir(parents=True)
        (self.automations / "automation.toml").write_text(
            'id = "audit"\nname = "Audit"\nstatus = "ACTIVE"\nrrule = "FREQ=WEEKLY;BYHOUR=17;BYMINUTE=15;BYDAY=FR"\n',
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_builds_core_graph_without_vendor_noise(self) -> None:
        graph = build_execution_graph(self.root, automations_root=self.root / "automations", reason="test")
        ids = {node["id"] for node in graph["nodes"]}
        edge_types = {edge["type"] for edge in graph["edges"]}
        self.assertIn("job:weekly_report", ids)
        self.assertIn("script:scripts/report.py", ids)
        self.assertIn("config:config/report.json", ids)
        self.assertIn("manual:manual-flow", ids)
        self.assertTrue(any(node["kind"] == "source" and node.get("redacted") for node in graph["nodes"]))
        self.assertFalse(any(".venv/" in node_id for node_id in ids))
        self.assertIn("executes", edge_types)
        self.assertIn("reads", edge_types)
        self.assertIn("writes", edge_types)
        self.assertTrue(any(node["kind"] == "quality_check" for node in graph["nodes"]))
        self.assertTrue(any(node["kind"] == "approved_version" for node in graph["nodes"]))
        persisted = json.loads((self.root / "knowledge/_generated/execution-graph.json").read_text(encoding="utf-8"))
        self.assertTrue(persisted["refresh_receipt"].endswith("refresh-receipt.json"))
        self.assertIn("declared_vs_observed_mismatch", {item["code"] for item in graph["diagnostics"]})
        dashboard = (self.root / "knowledge/_generated/执行图看板.md").read_text(encoding="utf-8")
        self.assertIn("核心执行链", dashboard)
        self.assertNotIn(".venv", dashboard)

    def test_receipts_and_receipted_ad_hoc_reports_are_linked(self) -> None:
        graph = build_execution_graph(self.root, automations_root=self.root / "automations")
        report = next(node for node in graph["nodes"] if node["id"] == "job:weekly_report")
        self.assertEqual(report["receipt_status"], "partial")
        self.assertTrue(any(node["id"].startswith("report:analysis/receipted-report") for node in graph["nodes"]))

    def test_event_recording_is_idempotent_and_updates_observed_status(self) -> None:
        first = record_and_refresh(
            self.root,
            job_id="weekly_report",
            run_id="run-1",
            phase="started",
            status="started",
            artifact_paths=["data/outputs/weekly/2026-09-10/report.md"],
            automations_root=self.root / "automations",
        )
        second = record_and_refresh(
            self.root,
            job_id="weekly_report",
            run_id="run-1",
            phase="finished",
            status="ok",
            receipt_paths=["data/outputs/weekly/2026-09-10/run-log.json"],
            automations_root=self.root / "automations",
        )
        self.assertNotEqual(first["event_key"], second["event_key"])
        record_and_refresh(
            self.root,
            job_id="weekly_report",
            run_id="run-1",
            phase="finished",
            status="ok",
            receipt_paths=["data/outputs/weekly/2026-09-10/run-log.json"],
            automations_root=self.root / "automations",
        )
        latest = latest_events(self.root)["weekly_report"]
        self.assertEqual(latest["status"], "ok")
        graph = json.loads((self.root / "knowledge/_generated/execution-graph.json").read_text(encoding="utf-8"))
        node = next(item for item in graph["nodes"] if item["id"] == "job:weekly_report")
        self.assertEqual(node["observed_status"], "ok")

    def test_legacy_builder_also_refreshes_execution_graph(self) -> None:
        output = self.root / "graph-output"
        command = [
            sys.executable,
            str(Path(__file__).resolve().parents[1] / "tools/build_graph.py"),
            "--root",
            str(self.root),
            "--out",
            str(output),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue((output / "code-graph.json").exists())
        self.assertTrue((self.root / "knowledge/_generated/execution-graph.json").exists())


if __name__ == "__main__":
    unittest.main()
