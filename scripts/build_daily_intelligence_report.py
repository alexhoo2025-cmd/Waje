#!/usr/bin/env python3
"""Render a source-linked daily intelligence note."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from render_analysis_report_html import render_markdown_file


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    args = parser.parse_args()
    source = ROOT / "data/outputs" / args.date / "analysis.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    quality_path = ROOT / "data/outputs" / args.date / "quality.json"
    quality = json.loads(quality_path.read_text(encoding="utf-8")) if quality_path.exists() else {}
    target_dir = ROOT / "knowledge/03-竞品/日报"
    target_dir.mkdir(parents=True, exist_ok=True)
    source_health = quality.get("source_health", {})
    content_health = quality.get("content_health", {})
    lines = ["---", "type: daily-intelligence", "domain: competitor", "status: generated", f"updated: {args.date}", "tags: [daily-intelligence, competitor, market]", "---", "", f"# Waje 产品与竞品每日情报｜{args.date}", "", f"采集条目：{len(data['items'])}。本日报只做公开信息的初筛，重要结论需人工复核。", "", "## 数据质量摘要", "", f"- 来源成功率：{source_health.get('ok', 0)}/{source_health.get('total', 0)}（{source_health.get('success_rate', 0):.1%}）。", f"- 去重后条目：{content_health.get('unique_item_count', len(data['items']))}；过滤旧新闻：{content_health.get('stale_item_count', 0)} 条。", f"- 质量状态：`{quality.get('status', 'unknown')}`。", ""]
    for failed in source_health.get("failed_sources", []):
        lines.append(f"- 失败来源：`{failed.get('source_id', '')}` — {failed.get('error', '待确认')}。")
    if source_health.get("failed_sources"): lines.append("")
    for priority in (3, 2, 1):
        group = [item for item in data["items"] if item["importance"] == priority]
        if not group: continue
        lines += [f"## {group[0]['triage']}", ""]
        for item in group:
            title = item.get("title") or item["source_id"]
            summary = item.get("summary") or "（未提取到正文摘要）"
            lines += [f"### [{title}]({item.get('url', '')})", "", f"- 实体：`{item.get('entity_id', '')}`", f"- 主题：`{item.get('topic', '')}`", f"- 抓取时间：{item.get('fetched_at', '')}", f"- 摘要：{summary}", ""]
    target = target_dir / f"{args.date}-Waje产品与竞品情报.md"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    html_target = render_markdown_file(target)
    print(f"report={target}")
    print(f"html_report={html_target}")


if __name__ == "__main__":
    main()
