#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
REPORT = PROJECT / "knowledge/01-产品/Waje-H5轻量化游戏上线后留存与活跃度效果分析-V4-2026-08-21.md"
SUMMARY = json.loads((ROOT / "analysis_summary.json").read_text("utf-8"))
QUALITY = json.loads((ROOT / "quality_matrix.json").read_text("utf-8"))
text = REPORT.read_text("utf-8")

checks = []


def check(name: str, passed: bool, detail=None):
    checks.append({"check": name, "pass": bool(passed), "detail": detail})


check("report_exists", REPORT.exists() and REPORT.stat().st_size > 5000, REPORT.stat().st_size)
check("joint_cutoff", "2026-08-26" in text, SUMMARY["joint_cutoff"])
check("ga4_total", "1,149,317" in text, SUMMARY["ga4"]["event_rows"])
check("five_games", all(name in text for name in ["Limbo", "Keno", "Color Dice", "Hilo", "Plinko"]))
check("blocked_stages", all(name in text for name in ["GAME_LOAD", "GAME_READY", "BET_READY", "blocked"]))
check("d7_na", "D7为N/A" in text or "| N/A |" in text)
check("payment_segment_only", "只作为用户结构分群" in text)
check("firebase_boundary", "未关联Google Analytics数据流" in text and "Firebase Performance没有H5 Web数据" in text)
check("no_false_load_claim", "page_view写成加载成功" not in text)
check("quality_rows", len(QUALITY) >= 8, len(QUALITY))

for name in [
    "01_轻量化游戏发布与分析节点.png",
    "02_新访客游戏页面触达.png",
    "03_游戏页新访客D1D3回访.png",
    "04_首充用户游戏深度横向比较.png",
    "05_新增用户全链路数据可用性.png",
]:
    path = ROOT / "charts" / name
    check(f"chart:{name}", path.exists() and path.stat().st_size > 10000, path.stat().st_size if path.exists() else 0)

status = "passed" if all(c["pass"] for c in checks) else "failed"
receipt = {
    "status": status,
    "report": str(REPORT.relative_to(PROJECT)),
    "joint_cutoff": SUMMARY["joint_cutoff"],
    "checks": checks,
    "feishu_sync": (
        "completed_revision_131"
        if (ROOT / "feishu_publish_receipt.json").exists()
        else "pending_lark_api"
    ),
}
(ROOT / "validation_report.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"status": status, "checks": len(checks)}, ensure_ascii=False))
raise SystemExit(0 if status == "passed" else 1)
