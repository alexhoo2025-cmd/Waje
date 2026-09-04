#!/usr/bin/env python3
"""Validate the Dn Day full-document correction before handoff."""
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
FEISHU = ROOT / "full_document_optimization_receipt_2026_09_01.json"
AUDIT = ROOT / "full_document_audit_2026_09_01.md"
REPORT = PROJECT / "knowledge/01-产品/Waje-H5轻量化游戏新增用户行为与留存影响分析-DnDay-2026-09-01.md"
STANDARD = PROJECT / "knowledge/02-数据/Waje-留存口径与DnDay命名规范-2026-09-01.md"

payload = json.loads(FEISHU.read_text(encoding="utf-8"))
xml = payload["content"]
report = REPORT.read_text(encoding="utf-8")
checks: list[dict[str, object]] = []


def check(name: str, ok: bool, evidence: object) -> None:
    checks.append({"name": name, "ok": bool(ok), "evidence": evidence})


check("source_contract", all(v in xml for v in ["数据来源与 Dn Day 口径", "GA4 BigQuery（外部平台）", "Firebase Web 配置（外部平台）", "外部生产 Metabase"]), "five-source contract")
check("dn_day_rule", all(v in xml for v in ["D1 Day为注册/首次访问当天", "D2 Day为次日", "D3 Day为第3个自然日"]), "Dn Day definition")
xml_flat = "".join(re.sub(r"<[^>]+>", "", xml).split())
check("chart_table_mapping", all(v in xml_flat for v in ["Limbo9008647", "Keno9010270", "Limbo页面触达高于Keno"]), "Limbo=9008, Keno=9010")
check("ga4_d3_boundary", all(v in xml for v in ["D4 Day", "标准D3 Day待重算", "D2 Day应用回访"]), "legacy GA4 D0+3 isolated")
check("funnel_boundary", all(v in xml for v in ["GAME_LOAD / GAME_READY / BET_READY", "完整漏斗blocked", "D2 Day / D4 Day应用回访"]), "blocked events not treated as zero")
check("firebase_boundary", "Firebase在本报告中只用于接入状态核验，不作为页面触达、留存、下注或结算数据来源" in xml, "configuration only")
check("local_report", all(v in report for v in ["D2 Day", "D4 Day", "GA4 BigQuery", "Firebase Web 配置"]), str(REPORT))
check("standard_exists", "Dn Day = cohort_date + (n - 1) 个自然日" in STANDARD.read_text(encoding="utf-8"), str(STANDARD))
check("audit_exists", AUDIT.exists() and AUDIT.stat().st_size > 0, str(AUDIT))

images = [
    "01_起源四渠道DnDay留存对比.png",
    "02_起源上线前后DnDay留存变化.png",
    "03_起源同批注册DnDay留存曲线.png",
    "04_起源DnDay留存衰减.png",
    "05_起源轻量化节点D3Day留存.png",
    "02_新访客游戏页面触达_DnDay修正.png",
    "03_游戏页新访客D2D4回访.png",
    "07_产品TopGames九款_D2D4回访.png",
]
missing = [name for name in images if not (ROOT / "charts" / name).exists() or (ROOT / "charts" / name).stat().st_size == 0]
check("charts_exist", not missing, missing)

result = {
    "status": "passed" if all(c["ok"] for c in checks) else "failed",
    "revision_id": payload["revision_id"],
    "checks": checks,
}
(ROOT / "full_document_validation_2026_09_01.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"status": result["status"], "revision_id": result["revision_id"], "failed": [c["name"] for c in checks if not c["ok"]]}, ensure_ascii=False))
raise SystemExit(0 if result["status"] == "passed" else 1)
