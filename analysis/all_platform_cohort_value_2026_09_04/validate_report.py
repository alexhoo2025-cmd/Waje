#!/usr/bin/env python3
"""Validate refreshed cohort-report data, calculations, and portable artifact bounds."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ANALYSIS = Path(__file__).resolve().parent
RESULTS = ANALYSIS / "results"
PAYMENT = ANALYSIS / "payment_segmentation"
SUMMARY = ANALYSIS / "analysis_summary.json"
ARTIFACT = ANALYSIS / "artifact.json"
HTML = ROOT / "output/html/Waje-全平台用户生命周期与付费价值分析-H5自然新增重点-2026-09-04.html"
REPORT = ANALYSIS / "validation_report.json"
REPORT_MD = ANALYSIS / "validation_report.md"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def unique(rows: list[dict[str, Any]], fields: list[str]) -> bool:
    values = [tuple(row.get(field) for field in fields) for row in rows]
    return len(values) == len(set(values))


def main() -> int:
    findings: list[dict[str, Any]] = []
    failures: list[str] = []
    freshness = load(RESULTS / "01_source_freshness.json")["aggregate_rows"]
    expected_sources = {"ares_lifecycle", "track_ltv", "registration_profile", "daily_active", "success_orders"}
    latest = {row["source_name"]: row["latest_seen_date"] for row in freshness}
    freshness_ok = set(latest) == expected_sources and all(value == "2026-09-04" for value in latest.values())
    findings.append({"check": "服务器来源完整日期", "status": "passed" if freshness_ok else "failed", "evidence": latest})
    if not freshness_ok:
        failures.append("Core source freshness is incomplete or mismatched.")

    h5_daily = load(RESULTS / "03_h5_natural_daily_retention.json")["aggregate_rows"]
    h5_daily_ok = len(h5_daily) == 92 and unique(h5_daily, ["cohort_date"])
    findings.append({"check": "严格H5日cohort唯一性", "status": "passed" if h5_daily_ok else "failed", "evidence": {"row_count": len(h5_daily), "unique_cohort_dates": len({row['cohort_date'] for row in h5_daily})}})
    if not h5_daily_ok:
        failures.append("H5 daily cohort results are not one row per cohort date.")

    platform_daily = load(RESULTS / "04_platform_daily_retention.json")["aggregate_rows"]
    platform_ok = len(platform_daily) == 368 and unique(platform_daily, ["cohort_date", "platform"])
    findings.append({"check": "平台日cohort唯一性", "status": "passed" if platform_ok else "failed", "evidence": {"row_count": len(platform_daily), "unique_keys": len({(row['cohort_date'], row['platform']) for row in platform_daily})}})
    if not platform_ok:
        failures.append("Platform daily cohort results contain duplicates or missing expected groups.")

    payment_files = [
        "05a_h5_natural_payment_2026_06.json",
        "05b1_h5_natural_payment_2026_07_01_15.json",
        "05b2_h5_natural_payment_2026_07_16_31.json",
        "05c1_h5_natural_payment_2026_08_01_15.json",
        "05c2_h5_natural_payment_2026_08_16_31.json",
    ]
    payment_daily = [row for filename in payment_files for row in load(RESULTS / filename)["aggregate_rows"]]
    payment_ok = len(payment_daily) == 92 and unique(payment_daily, ["cohort_date"])
    findings.append({"check": "H5成功支付cohort覆盖", "status": "passed" if payment_ok else "failed", "evidence": {"row_count": len(payment_daily), "unique_cohort_dates": len({row['cohort_date'] for row in payment_daily})}})
    if not payment_ok:
        failures.append("H5 payment cohort windows do not combine to one row per June-August date.")

    summary = load(SUMMARY)
    h5_aug = next(row for row in summary["h5_strict_natural_payment_monthly"] if row["cohort_month"] == "2026-08")
    direct_aug = [row for row in payment_daily if row["cohort_date"].startswith("2026-08") and row.get("day_14_payment_rate") is not None]
    denominator = sum(int(row["cohort_users"]) for row in direct_aug)
    numerator = sum(float(row["day_14_payment_rate"]) * int(row["cohort_users"]) for row in direct_aug)
    recomputed = numerator / denominator if denominator else None
    payment_weighted_ok = recomputed is not None and abs(recomputed - float(h5_aug["day_14_payment_rate"])) < 1e-12
    findings.append({"check": "8月第14日付费率加权复算", "status": "passed" if payment_weighted_ok else "failed", "evidence": {"recomputed": recomputed, "summary": h5_aug["day_14_payment_rate"], "mature_users": denominator}})
    if not payment_weighted_ok:
        failures.append("August payment rate is not a user-weighted aggregation.")

    segment_june = load(PAYMENT / "06a_payment_segment_2026_06.json")["aggregate_rows"]
    segment_july = load(PAYMENT / "06b_payment_segment_2026_07.json")["aggregate_rows"]
    segment_ok = unique(segment_june, ["platform", "first_package_name", "download_channel"]) and unique(segment_july, ["platform", "first_package_name", "download_channel"])
    findings.append({"check": "完整月度分包阶段键唯一性", "status": "passed" if segment_ok else "failed", "evidence": {"june_rows": len(segment_june), "july_rows": len(segment_july)}})
    if not segment_ok:
        failures.append("Payment segmentation contains duplicate package keys.")

    artifact = load(ARTIFACT)
    manifest = artifact["manifest"]
    artifact_ok = artifact["surface"] == "report" and manifest["title"] and len(manifest["charts"]) == 3 and len(manifest["sources"]) == 5 and artifact["snapshot"]["status"] == "partial"
    findings.append({"check": "报告artifact合同", "status": "passed" if artifact_ok else "failed", "evidence": {"charts": len(manifest["charts"]), "tables": len(manifest["tables"]), "sources": len(manifest["sources"]), "snapshot_status": artifact["snapshot"]["status"]}})
    if not artifact_ok:
        failures.append("Artifact contract is incomplete.")

    scope_ok = not re.search(r"phoenix|phenix|firebase|h5phx", json.dumps(artifact), re.I)
    findings.append({"check": "专题范围清理", "status": "passed" if scope_ok else "failed"})
    if not scope_ok:
        failures.append("Out-of-scope content remains in the delivered payload.")
    prose = "\n".join(block.get("body", "") for block in manifest["blocks"])
    language_ok = "执行摘要" in prose and not re.search(r"Executive Summary|\bcohort\b|\bsession\b", prose, re.I)
    findings.append({"check": "正文中文化", "status": "passed" if language_ok else "failed"})
    if not language_ok:
        failures.append("Unnecessary English remains in the report body.")
    ltv_ok = all(value in prose for value in ("1707.45", "1607.46", "99.99", "-5.9%", "2421.79", "2190.15", "231.63", "-9.6%"))
    findings.append({"check": "LTV绝对下降额与相对降幅", "status": "passed" if ltv_ok else "failed"})
    if not ltv_ok:
        failures.append("Required LTV comparison values are missing.")

    html = HTML.read_text(encoding="utf-8") if HTML.exists() else ""
    html_ok = bool(html) and "<html" in html.lower() and not re.search(r"https?://", html, flags=re.I)
    findings.append({"check": "HTML自包含性", "status": "passed" if html_ok else "failed", "evidence": {"exists": HTML.exists(), "bytes": len(html), "external_http_reference": bool(re.search(r"https?://", html, flags=re.I))}})
    if not html_ok:
        failures.append("HTML is missing or has an external HTTP(S) dependency.")

    browser = load(ANALYSIS / "browser_verification.json")
    browser_ok = browser.get("ok") is True and browser.get("viewports") == [1440, 390] and browser.get("sourceDialog") == "passed"
    findings.append({"check": "桌面与窄屏显示及来源交互", "status": "passed" if browser_ok else "failed", "evidence": browser})
    if not browser_ok:
        failures.append("Rendered report verification did not pass.")

    report = {
        "overall_assessment": "share_with_caveats" if not failures else "needs_revision",
        "source_cutoff": {"server_aggregate": "2026-09-04"},
        "findings": findings,
        "caveats": [
            "8月完整月度首充/老付费/复充已可用；新增注册付费仅有不相加的半月去重窗口。",
            "Dn Day按第N个自然日解释；未成熟窗口为N/A。",
        ],
        "failures": failures,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown = "# 分析与交付验证回执\n\n"
    markdown += f"**总体评估：{'可分享（附重要边界）' if not failures else '需要修订'}**\n\n"
    markdown += "## 已通过检查\n\n"
    for item in findings:
        markdown += f"- {'✅' if item['status'] == 'passed' else '❌'} {item['check']}：`{item['status']}`\n"
    markdown += "\n## 必须保留的边界\n\n"
    for caveat in report["caveats"]:
        markdown += f"- {caveat}\n"
    REPORT_MD.write_text(markdown, encoding="utf-8")
    print(json.dumps({"assessment": report["overall_assessment"], "failure_count": len(failures), "report": str(REPORT.relative_to(ROOT))}, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
