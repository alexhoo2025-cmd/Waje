from __future__ import annotations

import json
import http.server
import os
import socketserver
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
FIXTURE = PROJECT / "tests/fixtures/wechat/sample-export.json"


class WechatPipelineTests(unittest.TestCase):
    def run_script(self, script: str, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["WAJE_ANALYST_ROOT"] = str(root)
        env.pop("WECHAT_ARTICLE_API_BASE", None)
        env.pop("WECHAT_ARTICLE_API_TOKEN", None)
        return subprocess.run([sys.executable, str(PROJECT / "scripts" / script), *args], cwd=PROJECT, env=env, text=True, capture_output=True, check=True)

    def prepare_root(self, root: Path) -> None:
        (root / "config").mkdir(parents=True)
        (root / "config/wechat_sources.json").write_text((PROJECT / "config/wechat_sources.json").read_text(encoding="utf-8"), encoding="utf-8")

    def test_authorized_export_parse_and_weekly_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.prepare_root(root)
            self.run_script("collect_wechat_articles.py", root, "--date", "2026-08-07", "--source-dir", str(FIXTURE.parent))
            manifest = sorted((root / "data/raw/wechat/2026-08-07").glob("manifest-*.json"))[-1]
            manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(manifest_payload["status"], "ok")
            self.assertEqual(len(manifest_payload["articles"]), 2)
            self.run_script("parse_wechat_article.py", root, "--date", "2026-08-07")
            parsed = json.loads((root / "data/processed/wechat/2026-08-07/articles.json").read_text(encoding="utf-8"))
            self.assertEqual(parsed["article_count"], 2)
            first = parsed["articles"][0]
            self.assertTrue(first["structure"]["tables"])
            self.assertEqual(first["structure"]["images"][0]["chart_type"], "折线图")
            self.assertIn("留存", first["analysis"]["metrics"])
            self.assertEqual(len(list((root / "knowledge/03-竞品/公众号").glob("*.md"))), 2)
            self.run_script("build_wechat_weekly_report.py", root, "--date", "2026-08-07")
            report = root / "knowledge/03-竞品/周报/2026-08-07-博彩社交游戏公众号周报.md"
            self.assertTrue(report.exists())
            report_text = report.read_text(encoding="utf-8")
            self.assertIn("本周新增文章", report_text)
            self.assertIn("Waje", report_text)

    def test_missing_api_degrades_without_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.prepare_root(root)
            env = os.environ.copy()
            env["WAJE_ANALYST_ROOT"] = str(root)
            env["WECHAT_ARTICLE_API_TOKEN"] = "do-not-write-this-token"
            env.pop("WECHAT_ARTICLE_API_BASE", None)
            result = subprocess.run([sys.executable, str(PROJECT / "scripts/collect_wechat_articles.py"), "--date", "2026-08-07"], cwd=PROJECT, env=env, text=True, capture_output=True, check=True)
            self.assertNotIn("do-not-write-this-token", result.stdout)
            manifest = sorted((root / "data/raw/wechat/2026-08-07").glob("manifest-*.json"))[-1]
            manifest_text = manifest.read_text(encoding="utf-8")
            self.assertNotIn("do-not-write-this-token", manifest_text)
            self.assertIn("no_authorized_export_found", manifest_text)

    def test_authorized_api_pagination_and_detail(self) -> None:
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802 - stdlib HTTPServer callback name
                if self.path.startswith("/articles?") and "cursor=next" in self.path:
                    body = {"items": []}
                elif self.path.startswith("/articles?"):
                    body = {"items": [{"id": "api-001"}], "next_cursor": "next"}
                elif self.path == "/articles/api-001":
                    body = {"article_id": "api-001", "title": "API 文章", "html": "<h1>API 文章</h1><p>RTP and retention</p>"}
                else:
                    self.send_response(404)
                    self.end_headers()
                    return
                payload = json.dumps(body).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *_args):
                return

        server = socketserver.TCPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                self.prepare_root(root)
                env = os.environ.copy()
                env["WAJE_ANALYST_ROOT"] = str(root)
                env["WECHAT_ARTICLE_API_BASE"] = f"http://127.0.0.1:{server.server_address[1]}"
                env["WECHAT_ARTICLE_API_TOKEN"] = "api-token-must-not-be-written"
                result = subprocess.run([sys.executable, str(PROJECT / "scripts/collect_wechat_articles.py"), "--date", "2026-08-07"], cwd=PROJECT, env=env, text=True, capture_output=True, check=True)
                self.assertNotIn("api-token-must-not-be-written", result.stdout)
                manifest = sorted((root / "data/raw/wechat/2026-08-07").glob("manifest-*.json"))[-1]
                payload = json.loads(manifest.read_text(encoding="utf-8"))
                self.assertEqual(payload["status"], "ok")
                self.assertEqual(payload["articles"][0]["source_access_status"], "authorized_api")
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
