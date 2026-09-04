#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
REPORT = PROJECT / "knowledge/01-产品/Waje-H5轻量化游戏上线后留存与活跃度效果分析-V4-2026-08-21.md"
SUMMARY = json.loads((ROOT / "analysis_summary.json").read_text("utf-8"))
receipt_path = ROOT / "final_feishu_readback.json"
if not receipt_path.exists():
    receipt_path = ROOT / "browser_comment_update_receipt.json"
if not receipt_path.exists():
    receipt_path = ROOT / "feishu_reorg_receipt.json"
RECEIPT = json.loads(receipt_path.read_text("utf-8"))
text = REPORT.read_text("utf-8")

checks: list[dict[str, object]] = []


def check(name: str, ok: bool, evidence: object) -> None:
    checks.append({"name": name, "ok": bool(ok), "evidence": evidence})


check("ga4_window", "2026-08-21—2026-08-27" in text and SUMMARY["ga4"]["window"] == ["2026-08-21", "2026-08-27"], SUMMARY["ga4"]["window"])
check("source_cutoffs", "new_user_retention_cutoff: 2026-08-29" in text and "新增留存最新完整日：2026年8月29日" in text, {"ga4": "2026-08-27", "retention": "2026-08-29"})
check("latest_ga4_totals", "1,140,489" in text and "7,513" in text, {"events": SUMMARY["ga4"]["event_rows"], "first_visitors": SUMMARY["ga4"]["first_visitors"]})
check("five_games", all(name in text for name in ["Limbo", "Keno", "Color Dice", "Hilo", "Plinko"]), [r["game"] for r in SUMMARY["games"]])
check("expanded_quality_comment", "PWA在新增扩大97.6%的同时D7下降3.1个百分点" in text, "PWA volume and retention separated")
check("first_pay_comment", all(v in text for v in ["首充日记为T0", "90.2%", "98.9%", "35.3%"]), "first-pay day and paid/unpaid comparison included")
check("maturity", "D7尚未成熟" in text and "| N/A |" in text, "immature kept as N/A")
check("funnel_boundary", all(v in text for v in ["GAME_LOAD", "GAME_READY", "BET_READY", "GAMEEND异常率约6.13%"]), "blocked stages preserved")
check("source_delay", all(v in text for v in ["8月30日尚未形成完整日数据", "不补零", "GA4游戏页面行为仍只到8月27日"]), "different source cutoffs disclosed")
check("d15_added", all(v in text for v in ["D1 / D3 / D7 / D15", "D15截至8月14日", "源表没有D14留存字段"]), "D15 added without inventing D14")
check("top9_added", all(v in text for v in ["产品Top Games九款：轻量化4款与非轻量化5款对照", "Whot / 6001", "Limbo / 9008", "Keno / 9010", "Tower / 9013", "Bottle spin / 2003"]), "product-defined Top Games included")
check("technical_mapping", all(v in text for v in ["Limbo / 9008", "Keno / 9010", "Limbo覆盖最大", "Keno的D1应用回访最高"]), "technical GameId mapping applied")
check("paid_unpaid_before_after", all(v in text for v in ["95.9%", "94.5%", "96.5%", "95.4%", "40.7%", "42.1%", "下降 **1.1个百分点**"]), "paid and unpaid comparison added")
check("no_stale_ga4", not any(v in text for v in ["1,149,317", "7,056名首次访问"]), "old 8/20-26 totals absent")
check("feishu_revision", f"lark_revision: {RECEIPT['revision_id']}" in text, RECEIPT["revision_id"])

image_paths = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
missing = []
for rel in image_paths:
    path = (REPORT.parent / rel).resolve()
    if not path.exists() or path.stat().st_size == 0:
        missing.append(str(path))
check("images_exist", not missing and len(image_paths) >= 6, {"count": len(image_paths), "missing": missing})

outline = "\n".join(
    re.sub(r"<[^>]+>", "", heading)
    for heading in re.findall(r"<h[1-6]\b[^>]*>([\s\S]*?)</h[1-6]>", RECEIPT["content"])
)
expected = [
    "历史留存结构", "上线前后效果", "留存衰减", "发布节点观察", "近期新增留存",
    "新增首充与新增未付费：两段注册批次对比", "近期五款游戏", "产品Top Games九款：轻量化4款与非轻量化5款对照",
    "游戏深度", "首充用户专项", "完整漏斗", "设备与体验", "结论与后续计划", "附录",
]
positions = [outline.find(name) for name in expected]
check("feishu_outline_order", all(p >= 0 for p in positions) and positions == sorted(positions), positions)

payload = {
    "status": "passed" if all(row["ok"] for row in checks) else "failed",
    "checks": checks,
    "report": str(REPORT),
    "feishu_revision": RECEIPT["revision_id"],
}
(ROOT / "validation_report.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "checks": len(checks), "failed": [r["name"] for r in checks if not r["ok"]]}, ensure_ascii=False))
raise SystemExit(0 if payload["status"] == "passed" else 1)
