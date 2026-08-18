from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from release_experience import build_comparison  # noqa: E402
from run_release_experience_watch import run_watch  # noqa: E402


class ReleaseExperienceTests(unittest.TestCase):
    def test_comparison_reports_changed_facts_without_identifier_fields(self):
        baseline = {
            "release_context": {"release_id": "base", "version": "1.0"},
            "observations": [{"id": "whot", "facts": {"minimum_bet_ngn": 1, "user_id": "private"}}],
        }
        candidate = {
            "release_context": {"release_id": "next", "version": "1.1"},
            "observations": [{"id": "whot", "facts": {"minimum_bet_ngn": 2, "user_id": "other-private"}}],
        }
        comparison = build_comparison(baseline, candidate)
        self.assertEqual(comparison["summary"]["changed_facts"], 1)
        self.assertEqual(comparison["changed_facts"][0]["field"], "minimum_bet_ngn")

    def test_watch_uses_release_manifest_not_config_revision_as_release_proof(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "incoming").mkdir()
            (root / "processed").mkdir()
            (root / "out").mkdir()
            (root / "knowledge").mkdir()
            config_index = root / "config-index.json"
            config_index.write_text(json.dumps({"revision": 12, "content_hash": "abc"}), encoding="utf-8")
            baseline = root / "baseline.json"
            baseline.write_text(json.dumps({"release_id": "base", "experience_report_path": "baseline.md"}), encoding="utf-8")
            config = {
                "release_manifest_dir": str(root / "incoming"),
                "configuration_index_path": str(config_index),
                "baseline_manifest_path": str(baseline),
                "state_path": str(root / "processed" / "state.json"),
                "output_dir": str(root / "out"),
                "knowledge_dir": str(root / "knowledge"),
                "release_manifest_required_fields": ["release_id", "version", "status", "released_at", "source", "surfaces"],
                "policy": {"release_confirmation": "manifest", "experience_scope": "test", "abuse_testing": "safe"},
            }
            config_path = root / "watch.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            first = run_watch(config_path, "2026-08-14")
            self.assertEqual(first["status"], "initialized")

            config_index.write_text(json.dumps({"revision": 13, "content_hash": "def"}), encoding="utf-8")
            changed = run_watch(config_path, "2026-08-15")
            self.assertEqual(changed["status"], "config_changed_needs_release_manifest")

            manifest = {
                "release_id": "h5-2.18.0",
                "version": "2.18.0",
                "status": "released",
                "released_at": "2026-08-15T10:00:00+08:00",
                "source": "release-manifest",
                "surfaces": ["H5"],
            }
            (root / "incoming" / "h5-2.18.0.json").write_text(json.dumps(manifest), encoding="utf-8")
            detected = run_watch(config_path, "2026-08-15")
            self.assertEqual(detected["status"], "release_detected")
            self.assertEqual(len(detected["created_tasks"]), 1)


if __name__ == "__main__":
    unittest.main()
