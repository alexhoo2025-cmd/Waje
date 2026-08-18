from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.render_analysis_report_html import render_markdown_file


class RenderAnalysisReportHtmlTest(unittest.TestCase):
    def test_renders_headings_table_and_escapes_script(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "report.md"
            source.write_text(
                "---\nupdated: 2026-08-14\n---\n\n# 标题\n\n> 证据边界\n\n| 指标 | 值 |\n|---|---:|\n| A | 1 |\n\n<script>alert(1)</script>\n",
                encoding="utf-8",
            )
            target = render_markdown_file(source)
            result = target.read_text(encoding="utf-8")
            self.assertIn('<h1 id="section-1">标题</h1>', result)
            self.assertIn("<table>", result)
            self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", result)
            self.assertNotIn("<script>alert(1)</script>", result)


if __name__ == "__main__":
    unittest.main()
