#!/usr/bin/env python3
"""Validate the local KYC aggregate report before Feishu publication."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image


OUT = Path(__file__).resolve().parent
ARCHIVE = OUT.parents[1] / "knowledge" / "02-数据" / "Waje-KYC人脸与羊毛风险综合分析-近30天与用户关联-2026-08-27.md"
CHARTS = [
    "01_KYC项目节点后的状态变化.png",
    "02_首充用户七日提充结构.png",
    "03_首充用户提现速度.png",
    "04_首充用户游戏参与.png",
    "05_分阶段首充提充比.png",
]


def fail(message: str) -> None:
    print(json.dumps({"status": "failed", "reason": message}, ensure_ascii=False))
    raise SystemExit(2)


def main() -> None:
    snapshot_path = OUT / "source_snapshot.json"
    report_path = OUT / "report.md"
    if not snapshot_path.exists() or not report_path.exists() or not ARCHIVE.exists():
        fail("missing_report_or_snapshot")
    data = json.loads(snapshot_path.read_text("utf-8"))
    face = data["face_phases"]
    groups = data["first_pay_user_link"]
    if sum(row["users"] for row in face) != 47197:
        fail("face_phase_total_mismatch")
    if sum(row["success"] for row in face) != 24062:
        fail("face_success_total_mismatch")
    if sum(row["users"] for row in groups) != 20721:
        fail("first_pay_group_total_mismatch")
    if not (groups[1]["tc7"] > 1 and groups[1]["game_rate"] > 0.9):
        fail("headline_relationship_not_preserved")
    text = report_path.read_text("utf-8")
    for required in [
        "137%",
        "92.1%",
        "7月27日23:20",
        "7日提现÷现金充值",
        "不能直接归因",
        "企业 BigQuery MCP",
    ]:
        if required not in text:
            fail(f"missing_required_report_content:{required}")
    for forbidden in ["user_id", "gid", "account_number", "BVN号码", "NIN号码", "IP地址"]:
        if forbidden in text:
            fail(f"sensitive_field_leak_in_report:{forbidden}")
    if ARCHIVE.read_text("utf-8") != text:
        fail("archive_not_identical_to_report")
    sizes = {}
    for name in CHARTS:
        path = OUT / name
        if not path.exists() or path.stat().st_size < 10_000:
            fail(f"chart_missing_or_empty:{name}")
        with Image.open(path) as image:
            if image.width < 1200 or image.height < 900:
                fail(f"chart_dimensions_too_small:{name}")
            sizes[name] = [image.width, image.height]
    print(
        json.dumps(
            {
                "status": "passed",
                "report": str(report_path),
                "archive": str(ARCHIVE),
                "charts": sizes,
                "user_link_status": data["source_status"]["metabase_user_link"],
                "bigquery_status": data["source_status"]["bigquery_mcp"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
