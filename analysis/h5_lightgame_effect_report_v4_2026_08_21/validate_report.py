#!/usr/bin/env python3
"""Validate scope, evidence, and prohibited commercial terms for report V4."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "knowledge/01-产品/Waje-H5轻量化游戏上线后留存与活跃度效果分析-V4-2026-08-21.md"
DATA = Path(__file__).resolve().parent / "report_data.json"
MANIFEST = Path(__file__).resolve().parent / "chart_manifest.json"

REQUIRED = [
    "核心结论",
    "四渠道新增与留存对比",
    "轻量化上线前后",
    "D15变化",
    "留存路径",
    "发布节点观察",
    "活跃与游戏参与",
    "GA4页面活跃快照",
    "游戏游玩与下注数据",
    "技术与数据问题",
    "附录：统计范围与来源",
]
FORBIDDEN = ["付费", "首充", "复充", "C-T", "ARPU", "ARPPU", "TX", "ROI", "ROAS", "LTV"]


def main() -> None:
    text = REPORT.read_text(encoding="utf-8")
    data = json.loads(DATA.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    missing = [x for x in REQUIRED if x not in text]
    hits = [
        term
        for term in FORBIDDEN
        if (term in text if any("\u4e00" <= char <= "\u9fff" for char in term) else re.search(rf"\\b{re.escape(term)}\\b", text, flags=re.IGNORECASE))
    ]
    missing_charts = []
    for chart in manifest["charts"]:
        target = (Path(__file__).resolve().parent / chart["path"]).resolve()
        if not target.exists() or target.stat().st_size == 0:
            missing_charts.append(str(target))
    result = {
        "status": "passed" if not missing and not hits and not missing_charts else "failed",
        "required_sections_missing": missing,
        "forbidden_term_hits": hits,
        "missing_or_empty_charts": missing_charts,
        "channel_count": len(data["channels"]),
        "phase_count": len(data["phases"]),
        "window": data["window"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
