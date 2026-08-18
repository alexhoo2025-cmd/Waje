from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]


class LarkPipelineTests(unittest.TestCase):
    def run_script(self, script: str, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["WAJE_ANALYST_ROOT"] = str(root)
        env.pop("LARK_API_BASE", None)
        env.pop("LARK_API_TOKEN", None)
        return subprocess.run([sys.executable, str(PROJECT / "scripts" / script), *args], cwd=PROJECT, env=env, text=True, capture_output=True, check=True)

    def prepare_root(self, root: Path) -> None:
        (root / "config").mkdir(parents=True)
        (root / "config/lark_sources.json").write_text((PROJECT / "config/lark_sources.json").read_text(encoding="utf-8"), encoding="utf-8")

    def test_export_is_filtered_redacted_and_written_silently(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.prepare_root(root)
            source = root / "incoming"
            source.mkdir()
            (source / "messages.json").write_text(json.dumps({"items": [
                {"id": "m-1", "chat_id": "chat-1", "chat_name": "数据报表", "create_time": "2026-08-11T09:00:00+08:00", "sender_id": "u-1", "text": "GAMEEND 异常，需要补充版本和字段口径 password=hidden"},
                {"id": "m-2", "chat_id": "chat-2", "chat_name": "闲聊", "create_time": "2026-08-11T09:01:00+08:00", "sender_id": "u-2", "text": "午饭吃什么"}
            ]}, ensure_ascii=False), encoding="utf-8")
            collect = self.run_script("collect_lark_messages.py", root, "--date", "2026-08-11", "--source-dir", str(source))
            self.assertIn("outbound_actions=0", collect.stdout)
            message_files = list((root / "data/raw/lark/2026-08-11/messages").glob("*.json"))
            self.assertEqual(len(message_files), 2)
            message_text = "\n".join(path.read_text(encoding="utf-8") for path in message_files)
            self.assertNotIn("hidden", message_text)
            self.assertNotIn("password=hidden", message_text)
            self.run_script("parse_lark_messages.py", root, "--date", "2026-08-11")
            note = root / "knowledge/05-协同沟通/2026-08-11-Lark项目沟通提炼.md"
            self.assertTrue(note.exists())
            note_text = note.read_text(encoding="utf-8")
            self.assertIn("GAMEEND", note_text)
            self.assertIn("出站操作：0", note_text)

    def test_no_export_degrades_without_outbound_action(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.prepare_root(root)
            result = self.run_script("collect_lark_messages.py", root, "--date", "2026-08-11")
            self.assertIn("status=degraded", result.stdout)
            self.assertIn("outbound_actions=0", result.stdout)


if __name__ == "__main__":
    unittest.main()
