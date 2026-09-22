from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts/create_thread_checkpoint.py"
TEMPLATE = PROJECT_ROOT / "analysis/thread_handoffs/TEMPLATE.md"


class CheckpointScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "analysis/thread_handoffs").mkdir(parents=True)
        (self.root / "analysis/thread_handoffs/TEMPLATE.md").write_text(
            TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8"
        )
        self.scope = self.root / "analysis/demo"
        self.scope.mkdir(parents=True)
        (self.scope / "run-receipt.json").write_text(
            json.dumps(
                {
                    "status": "ok",
                    "run_at": "2026-09-22T09:00:00+08:00",
                    "window": {"start": "2026-09-21", "end": "2026-09-22", "timezone": "Asia/Hong_Kong"},
                }
            ),
            encoding="utf-8",
        )
        (self.scope / "report.md").write_text("# Demo\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        (self.root / "tracked.txt").write_text("changed\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_script(self, *extra: str) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(self.root),
            "--task",
            "测试任务",
            "--slug",
            "demo",
            "--objective",
            "验证检查点生成",
            "--scope",
            "analysis/demo",
            "--next",
            "继续验证",
            *extra,
        ]
        return subprocess.run(command, text=True, capture_output=True, check=False)

    def test_creates_checkpoint_and_archives_previous_version(self) -> None:
        first = self.run_script()
        self.assertEqual(first.returncode, 0, first.stderr)
        output = self.root / "analysis/thread_handoffs/demo/CURRENT.md"
        text = output.read_text(encoding="utf-8")
        self.assertIn("验证检查点生成", text)
        self.assertIn("analysis/demo/run-receipt.json", text)
        self.assertIn("analysis/demo/report.md", text)
        self.assertIn("继续验证", text)

        second = self.run_script("--decision", "第二次生成")
        self.assertEqual(second.returncode, 0, second.stderr)
        history = list((output.parent / "history").glob("CURRENT-*.md"))
        self.assertEqual(len(history), 1)
        self.assertIn("第二次生成", output.read_text(encoding="utf-8"))

    def test_rejects_path_outside_project(self) -> None:
        result = self.run_script("--artifact", "/etc/hosts")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside project root", result.stderr)


if __name__ == "__main__":
    unittest.main()
