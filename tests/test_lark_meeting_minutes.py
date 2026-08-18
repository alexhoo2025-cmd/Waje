from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import run_lark_meeting_minutes_pipeline as pipeline  # noqa: E402


class MeetingMinutesPipelineTests(unittest.TestCase):
    def test_extracts_linked_transcript_without_returning_source_doc(self) -> None:
        source = "https://ksg964l11fam.sg.larksuite.com/docx/ZB6OdypGjoCyvdxbRXPlhzfIgaf"
        content = (
            "原始文字记录："
            "https://ksg964l11fam.sg.larksuite.com/docx/FjiSdjZwwo4ic3x4vVelUsTEgZd"
        )
        self.assertEqual(
            pipeline.extract_transcript_url(content, source),
            "https://ksg964l11fam.sg.larksuite.com/docx/FjiSdjZwwo4ic3x4vVelUsTEgZd",
        )

    def test_transcript_is_summarized_to_safe_task_records(self) -> None:
        content = (
            '<cite user-name="Robin"></cite>09:45:00 '
            "H5/PWA 设备性能数据打通，生命周期报表迁移到起源。\n"
            '<cite user-name="Max"></cite>09:57:00 '
            "H5 可能本周发版，请检查配置。"
        )
        records = pipeline.parse_transcript(content)
        tasks = pipeline.build_tasks(records)
        self.assertEqual(len(records), 2)
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0]["priority"], "P0")
        self.assertEqual(tasks[1]["status"], "待确认")
        self.assertNotIn("<cite", tasks[0]["summary"])

    def test_smart_minutes_todos_keep_display_name_but_drop_user_id(self) -> None:
        content = (
            "# 待办\n\n"
            '- [ ] 配置H5发版内容：检查配置 <cite type="user" '
            'user-id="ou_sensitive" user-name="Vito"></cite>\n\n'
            '<readonly-block type="isv"></readonly-block>'
        )
        todos = pipeline.extract_smart_todos(content)
        self.assertEqual(todos, [{"owner": "Vito", "summary": "配置H5发版内容：检查配置"}])
        self.assertNotIn("ou_sensitive", str(todos))

    def test_build_note_does_not_store_open_id_or_full_transcript(self) -> None:
        documents = [{
            "title": "智能纪要：测试 2026年8月17日",
            "source_url": "https://ksg964l11fam.sg.larksuite.com/docx/ZB6OdypGjoCyvdxbRXPlhzfIgaf",
            "transcript_url": "https://ksg964l11fam.sg.larksuite.com/docx/FjiSdjZwwo4ic3x4vVelUsTEgZd",
            "document_token": "ZB6OdypGjoCyvdxbRXPlhzfIgaf",
            "owner_name": "Max",
            "revision_id": 17,
        }]
        tasks = [{
            "speaker": "Robin",
            "timestamp": "09:45:00",
            "summary": "H5/PWA 设备性能数据打通。",
            "categories": ["H5与性能"],
            "priority": "P0",
            "status": "进行中",
            "data_action": "核验性能链路",
            "acceptance": "可按版本和设备下钻",
        }]
        note = pipeline.build_note("2026-08-17", documents, tasks, "2026-08-17T10:15:00+08:00")
        self.assertIn("transcript_verified", note)
        self.assertIn("出站操作：`0`", note)
        self.assertNotIn("ou_1da16d47a973d6aa203ae8ab7b2870bb", note)
        self.assertIn("不保存完整逐字稿", note)


if __name__ == "__main__":
    unittest.main()
