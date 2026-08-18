#!/usr/bin/env python3
"""Extract project-relevant, redacted Lark messages into the knowledge base."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from collections import defaultdict
from pathlib import Path

from lark_common import project_root, write_json


def load_config(root: Path) -> dict:
    path = root / "config/lark_sources.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def classify(text: str, keywords: dict) -> tuple[list[str], int]:
    matched: list[str] = []
    for category, terms in keywords.items():
        if any(term.lower() in text.lower() for term in terms):
            matched.append(category)
    return matched, len(matched)


def infer_type(text: str) -> str:
    if re.search(r"异常|失败|丢失|重复|延迟|阻塞|修复|回归|事故", text):
        return "问题/异常"
    if re.search(r"需要|需求|开发|实现|增加|支持|优化", text):
        return "需求/方案"
    if re.search(r"结论|决定|确认|口径|统一|以后|改为", text):
        return "决策/口径"
    if re.search(r"指标|数据|报表|看板|SQL|BQ|MySQL|RTP|GAMEEND", text, re.I):
        return "数据/指标"
    if re.search(r"跟进|负责人|截止|排期|验收", text):
        return "任务/协同"
    return "待确认"


def read_messages(root: Path, day: str) -> list[dict]:
    directory = root / "data/raw/lark" / day / "messages"
    records = []
    for path in sorted(directory.glob("*.json")) if directory.exists() else []:
        records.append(json.loads(path.read_text(encoding="utf-8")))
    return records


def build_note(root: Path, day: str, records: list[dict], config: dict) -> Path:
    keywords = config.get("project_keywords", {})
    relevant: list[dict] = []
    review: list[dict] = []
    for record in records:
        text = str(record.get("text", "")).strip()
        categories, score = classify(text, keywords)
        if score == 0:
            continue
        item = dict(record)
        item["categories"] = categories
        item["type"] = infer_type(text)
        item["confidence"] = "high" if score >= 2 else "review"
        if score >= 2:
            relevant.append(item)
        else:
            review.append(item)

    out_dir = root / str(config.get("knowledge", {}).get("output_dir", "knowledge/05-协同沟通"))
    out_dir.mkdir(parents=True, exist_ok=True)
    review_dir = root / str(config.get("knowledge", {}).get("review_dir", "data/outputs/lark"))
    review_dir.mkdir(parents=True, exist_ok=True)
    write_json(review_dir / day / "review-queue.json", {"schema_version": 1, "date": day, "items": review, "outbound_actions": 0})

    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in relevant:
        grouped[item["type"]].append(item)
    lines = [
        "---",
        "type: communication-derived",
        "domain: project-operations",
        "status: extracted",
        f"updated: {day}",
        "owner: analyst",
        "tags: [lark, project-communication, silent-ingestion]",
        "---",
        "",
        f"# Lark 项目沟通提炼｜{day}",
        "",
        "本文件由 Lark 只读、静默采集流程生成，只保留项目相关且已脱敏的消息片段；不会向 Lark 发送或回复任何消息。低置信度内容进入本地复核队列。",
        "",
        f"- 采集消息：{len(records)} 条。",
        f"- 提取项目相关：{len(relevant)} 条。",
        f"- 待人工复核：{len(review)} 条。",
        "- 出站操作：0。",
        "",
    ]
    if not relevant:
        lines.extend(["## 当前结果", "", "本次没有达到项目相关阈值的消息；未生成业务结论。", ""])
    for category in ("需求/方案", "问题/异常", "决策/口径", "数据/指标", "任务/协同", "待确认"):
        items = grouped.get(category, [])
        if not items:
            continue
        lines.extend([f"## {category}", "", "| 时间 | 会话 | 摘要 | 标签 | 来源消息 |"])
        lines.append("|---|---|---|---|---|")
        for item in items:
            summary = str(item.get("text", "")).replace("\n", " ").replace("|", "｜")
            lines.append(f"| {item.get('created_at','')} | {item.get('chat_name','') or item.get('chat_id','')} | {summary} | {', '.join(item.get('categories', []))} | `{item.get('message_id','')}` |")
        lines.append("")
    lines.extend(["## 待确认", "", "- 规则提取只用于初筛；需求优先级、负责人、截止时间和业务结论需要人工确认。", "- 原始消息不在本知识条目中保存；如需追溯，使用消息 ID 在 Lark 中人工查看。", ""])
    path = out_dir / f"{day}-Lark项目沟通提炼.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=dt.datetime.now().astimezone().date().isoformat())
    args = parser.parse_args()
    root = project_root()
    config = load_config(root)
    records = read_messages(root, args.date)
    path = build_note(root, args.date, records, config)
    print(f"lark parsing: {len(records)} messages; output={path.relative_to(root)}; outbound_actions=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
