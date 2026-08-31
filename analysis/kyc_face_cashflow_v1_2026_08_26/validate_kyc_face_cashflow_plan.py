#!/usr/bin/env python3
"""Validate the aggregate-only KYC face cashflow design artifacts."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[1]
KNOWLEDGE = WORKSPACE / "knowledge/02-数据/Waje-KYC人脸用户提充比与疑似刷子整体分析方案-V1-2026-08-26.md"


def main() -> None:
    collection = json.loads((ROOT / "data_collection_contract.json").read_text(encoding="utf-8"))
    dashboard = json.loads((ROOT / "risk_kyc_dashboard_contract.json").read_text(encoding="utf-8"))
    delivery = json.loads((ROOT / "feishu_delivery_receipt.json").read_text(encoding="utf-8"))
    text = KNOWLEDGE.read_text(encoding="utf-8")
    errors: list[str] = []
    required_metrics = {"face_cohort_tc_d30", "first_recharge_tc_d7", "user_tc_distribution", "cashflow_link_coverage"}
    actual_metrics = {item["id"] for item in collection.get("metrics", [])}
    if not required_metrics.issubset(actual_metrics):
        errors.append("missing_required_metrics")
    if collection.get("decision_boundary") != "仅聚合整体分析，不生成名单、不自动标记、不限制提现。":
        errors.append("decision_boundary_changed")
    if dashboard.get("access", {}).get("no_export") is not True:
        errors.append("export_not_disabled")
    if dashboard.get("access", {}).get("small_group_suppression", {}).get("min_recharge_users") != 20:
        errors.append("small_group_rule_missing")
    if len(dashboard.get("pages", [])) != 4:
        errors.append("dashboard_pages")
    for phrase in ["不输出用户名单", "成功打款提现金额", "首次成功现金充值", "不构成刷子事实", "关联率≥99%"]:
        if phrase not in text:
            errors.append(f"missing_text:{phrase}")
    for path in [ROOT / "report.md", ROOT / "feishu_release.xml", ROOT / "run_receipt.json", ROOT / "feishu_delivery_receipt.json", KNOWLEDGE]:
        if not path.exists() or path.stat().st_size == 0:
            errors.append(f"missing_artifact:{path.name}")
    if delivery.get("readback", {}).get("status") != "passed":
        errors.append("feishu_readback_not_passed")
    if delivery.get("dashboard", {}).get("status") != "blocked":
        errors.append("dashboard_status_not_explicit")
    result = {"status": "passed" if not errors else "failed", "errors": errors, "metrics": len(actual_metrics), "dashboard_pages": len(dashboard.get("pages", [])), "remote_dashboard_status": delivery.get("dashboard", {}).get("status"), "feishu_url": delivery.get("document", {}).get("url")}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
