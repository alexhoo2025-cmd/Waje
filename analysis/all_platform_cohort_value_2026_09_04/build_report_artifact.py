#!/usr/bin/env python3
"""Build the canonical portable-report artifact from refreshed aggregate results."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any
from finalize_topic import finalize_topic


ROOT = Path(__file__).resolve().parents[2]
ANALYSIS = Path(__file__).resolve().parent
SUMMARY_PATH = ANALYSIS / "analysis_summary.json"
ARTIFACT_PATH = ANALYSIS / "artifact.json"
CHART_MAP_PATH = ANALYSIS / "chart_map.json"
KNOWLEDGE_PATH = ROOT / "knowledge/02-数据/Waje-全平台用户生命周期与付费价值分析-H5自然新增重点-2026-09-04.md"


def pct(value: float | None, digits: int = 2) -> str:
    return "N/A" if value is None else f"{value * 100:.{digits}f}%"


def pp(new: float | None, old: float | None) -> str:
    if new is None or old is None:
        return "暂不可用"
    return f"{(new - old) * 100:+.2f} 个百分点"


def compact(value: float | int | None, digits: int = 1) -> str:
    if value is None:
        return "N/A"
    number = float(value)
    if abs(number) >= 1_000_000_000:
        return f"{number / 1_000_000_000:.{digits}f}B"
    if abs(number) >= 1_000_000:
        return f"{number / 1_000_000:.{digits}f}M"
    if abs(number) >= 1_000:
        return f"{number / 1_000:.{digits}f}k"
    return f"{number:.{digits}f}"


def source(
    identifier: str,
    label: str,
    paths: list[str],
    tables: list[str],
    filters: list[str],
    definitions: list[str],
    description: str,
) -> dict[str, Any]:
    sql_files = [path for path in paths if path.endswith(".sql")]
    if not sql_files:
        raise RuntimeError(f"{identifier} has no SQL provenance file")
    sql_text = "\n\n".join(
        f"-- Executed statement source: {path}\n" + (ROOT / path).read_text(encoding="utf-8").strip()
        for path in sql_files
    )
    return {
        "id": identifier,
        "label": label,
        "path": paths[0],
        "query": {
            "engine": "Google Cloud BigQuery (read-only aggregate queries)",
            "language": "SQL",
            "description": description,
            "sql": sql_text,
            "tables_used": tables,
            "filters": filters,
            "metric_definitions": definitions,
            "status": "actual_aggregate",
        },
        "related_paths": paths[1:],
    }


def data_rows(summary: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = summary.get(key)
    if not isinstance(value, list):
        raise RuntimeError(f"Expected list for {key}")
    return value


def lookup(rows: list[dict[str, Any]], month: str) -> dict[str, Any]:
    item = next((row for row in rows if row["cohort_month"] == month), None)
    if item is None:
        raise RuntimeError(f"Missing month {month}")
    return item


def make_long_h5_retention(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        for day in [*range(2, 15), 30, 60, 90]:
            metric = f"day_{day}_retention"
            rate = row.get(metric)
            if rate is not None:
                result.append(
                    {
                        "cohort_month": row["cohort_month"],
                        "lifecycle_day": f"第{day}日",
                        "day_number": day,
                        "retention_rate": rate,
                        "mature_cohort_users": row.get(f"{metric}_mature_users"),
                    }
                )
    return result


def make_long_ltv(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        for day in [*range(1, 15), 30, 60, 90]:
            value = row.get(f"ltv_{day}")
            if value is not None:
                result.append(
                    {
                        "cohort_month": row["cohort_month"],
                        "lifecycle_day": f"第{day}日",
                        "day_number": day,
                        "ltv": value,
                        "new_users": row["new_users"],
                    }
                )
    return result


def make_payment_horizon(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        for day in [1, 7, 14]:
            rate = row.get(f"day_{day}_payment_rate")
            arpu = row.get(f"day_{day}_arpu")
            if rate is not None:
                result.append(
                    {
                        "cohort_month": row["cohort_month"],
                        "lifecycle_day": f"第{day}日",
                        "day_number": day,
                        "payment_rate": rate,
                        "arpu": arpu,
                        "mature_cohort_users": row.get(f"day_{day}_payment_rate_mature_users"),
                    }
                )
    return result


def main() -> int:
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    lifecycle = data_rows(summary, "h5_lifecycle_source_monthly")
    h5_retention = data_rows(summary, "h5_strict_natural_retention_monthly")
    platform_retention = [
        row for row in data_rows(summary, "platform_retention_monthly")
        if row["platform"] in {"H5", "Android", "iOS"}
    ]
    h5_payment = data_rows(summary, "h5_strict_natural_payment_monthly")
    payment_segments = data_rows(summary, "payment_segmentation_monthly")
    payment_august = data_rows(summary, "payment_segmentation_august_windows")
    payment_august_full = summary["payment_segmentation_august_full"]
    firebase_rows = data_rows(summary, "phenix_firebase_retention_daily")
    firebase_summary = summary["phenix_firebase_summary"]
    firebase_inventory = data_rows(summary, "phenix_firebase_event_inventory")

    june_retention = lookup(h5_retention, "2026-06")
    july_retention = lookup(h5_retention, "2026-07")
    august_retention = lookup(h5_retention, "2026-08")
    june_lifecycle = lookup(lifecycle, "2026-06")
    july_lifecycle = lookup(lifecycle, "2026-07")
    august_lifecycle = lookup(lifecycle, "2026-08")
    june_payment = lookup(h5_payment, "2026-06")
    july_payment = lookup(h5_payment, "2026-07")
    august_payment = lookup(h5_payment, "2026-08")

    h5_segment_rows = [
        row for row in payment_segments
        if row["platform"] == "H5" and row["first_package_name"] == "com.wajegame.web" and row["download_channel"] == "PAWAJEBETH5"
    ]
    h5_segment_june = next(row for row in h5_segment_rows if row["period"] == "2026-06")
    h5_segment_july = next(row for row in h5_segment_rows if row["period"] == "2026-07")
    h5_august_windows = [
        row for row in payment_august
        if row["platform"] == "H5" and row["first_package_name"] == "com.wajegame.web" and row["download_channel"] == "PAWAJEBETH5"
    ]
    app_payment_segments_map: dict[tuple[str, str], dict[str, Any]] = {}
    additive_fields = [
        "unique_paying_users", "unique_new_registered_payers", "unique_first_payers",
        "unique_old_payers_at_period_start", "unique_repeat_payers_after_first_payment",
        "pay_amount", "first_payment_amount", "repeat_payment_amount",
    ]
    for row in payment_segments:
        key = (row["period"], row["platform"])
        target = app_payment_segments_map.setdefault(
            key,
            {"period": row["period"], "platform": row["platform"], **{field: 0 for field in additive_fields}},
        )
        for field in additive_fields:
            target[field] += row.get(field) or 0
    app_payment_segments = []
    for row in app_payment_segments_map.values():
        row["payer_arppu"] = row["pay_amount"] / row["unique_paying_users"] if row["unique_paying_users"] else None
        row["repeat_payer_arppu"] = row["repeat_payment_amount"] / row["unique_repeat_payers_after_first_payment"] if row["unique_repeat_payers_after_first_payment"] else None
        app_payment_segments.append(row)
    app_payment_segments.sort(key=lambda row: (row["period"], row["platform"]))

    platform_d2 = [
        {
            "cohort_month": row["cohort_month"],
            "platform": row["platform"],
            "day_2_retention": row["day_2_retention"],
            "day_7_retention": row["day_7_retention"],
            "day_14_retention": row["day_14_retention"],
            "cohort_users": row["cohort_users"],
        }
        for row in platform_retention
    ]
    h5_retention_curve = make_long_h5_retention(h5_retention)
    h5_ltv_curve = make_long_ltv(lifecycle)
    h5_payment_curve = make_payment_horizon(h5_payment)
    firebase_curve = []
    for row in firebase_rows:
        for day, prefix in [(2, "day_2"), (4, "day_4")]:
            if row.get(f"{prefix}_any_event_users") is not None:
                firebase_curve.append(
                    {
                        "cohort_date": row["cohort_date"],
                        "lifecycle_day": f"第{day}日",
                        "metric": "任意事件回访",
                        "retention_rate": row[f"{prefix}_any_event_users"] / row["cohort_users"],
                        "cohort_users": row["cohort_users"],
                    }
                )
                firebase_curve.append(
                    {
                        "cohort_date": row["cohort_date"],
                        "lifecycle_day": f"第{day}日",
                        "metric": "会话开始回访",
                        "retention_rate": row[f"{prefix}_session_start_users"] / row["cohort_users"],
                        "cohort_users": row["cohort_users"],
                    }
                )

    headline = [{
        "h5_aug_day14_retention": august_retention["day_14_retention"],
        "h5_aug_day14_payment_rate": august_payment["day_14_payment_rate"],
        "h5_aug_ltv14": august_lifecycle["ltv_14"],
        "phenix_day2_observed_retention": firebase_summary["day_2_session_start_users_rate"],
    }]

    sources = [
        source(
            "h5-lifecycle-source", "H5 自然新增生命周期聚合",
            ["analysis/all_platform_cohort_value_2026_09_04/results/02_h5_natural_lifecycle_value.json", "analysis/all_platform_cohort_value_2026_09_04/sql/02_h5_natural_lifecycle_value.sql"],
            ["wajenigeria.ares_hfyl.user_activety_indicators_downloadchannel"],
            ["2026-06-01—2026-08-31 cohort", "channel=PAWAJEBETH5", "sub_channel=PAWAJEBETH501", "数据截止：2026-09-04"],
            ["留存率＝成熟 cohort 的留存人数汇总 ÷ 新增人数汇总。", "LTV＝成熟 cohort 的累计 LTV 汇总 ÷ 新增人数汇总。"],
            "H5 自然新增的联运生命周期聚合，用于 LTV 与来源口径留存趋势。",
        ),
        source(
            "h5-strict-retention", "严格 H5 自然注册 cohort 留存",
            ["analysis/all_platform_cohort_value_2026_09_04/results/03_h5_natural_daily_retention.json", "analysis/all_platform_cohort_value_2026_09_04/sql/03_h5_natural_daily_retention.sql"],
            ["wajenigeria.origin_hfyl.user_events", "wajenigeria.origin_hfyl.realtime_edw_user_version_daily"],
            ["Web first package", "download/first channel/subchannel 均为 PAWAJEBETH5", "2026-06—2026-08 注册 cohort", "数据截止：2026-09-04"],
            ["第 N 日留存＝第 N 个自然日存在任意 Waje 日活记录的 cohort 用户 ÷ cohort 用户。", "只纳入已有日活源日期的 cohort，不以缺失日期补零。"],
            "严格映射的 H5 自然注册 cohort，用于用户留存主结论。",
        ),
        source(
            "platform-retention", "APP 与 H5 首平台注册 cohort 留存",
            ["analysis/all_platform_cohort_value_2026_09_04/results/04_platform_daily_retention.json", "analysis/all_platform_cohort_value_2026_09_04/sql/04_platform_daily_retention.sql"],
            ["wajenigeria.origin_hfyl.user_events", "wajenigeria.origin_hfyl.realtime_edw_user_version_daily"],
            ["2026-06—2026-08 注册 cohort", "first_client_type 归为 H5/Android/iOS", "数据截止：2026-09-04"],
            ["平台留存＝首平台注册 cohort 在指定自然日有日活记录的用户 ÷ cohort 用户。"],
            "全平台首平台 cohort，用于 H5 与 APP 的对照。",
        ),
        source(
            "h5-payment-cohort", "严格 H5 自然 cohort 成功支付率与 ARPU",
            ["analysis/all_platform_cohort_value_2026_09_04/results/05a_h5_natural_payment_2026_06.json", "analysis/all_platform_cohort_value_2026_09_04/results/05b1_h5_natural_payment_2026_07_01_15.json", "analysis/all_platform_cohort_value_2026_09_04/results/05b2_h5_natural_payment_2026_07_16_31.json", "analysis/all_platform_cohort_value_2026_09_04/results/05c1_h5_natural_payment_2026_08_01_15.json", "analysis/all_platform_cohort_value_2026_09_04/results/05c2_h5_natural_payment_2026_08_16_31.json", "analysis/all_platform_cohort_value_2026_09_04/sql/05a_h5_natural_payment_2026_06.sql", "analysis/all_platform_cohort_value_2026_09_04/sql/05b1_h5_natural_payment_2026_07_01_15.sql", "analysis/all_platform_cohort_value_2026_09_04/sql/05b2_h5_natural_payment_2026_07_16_31.sql", "analysis/all_platform_cohort_value_2026_09_04/sql/05c1_h5_natural_payment_2026_08_01_15.sql", "analysis/all_platform_cohort_value_2026_09_04/sql/05c2_h5_natural_payment_2026_08_16_31.sql"],
            ["wajenigeria.origin_hfyl.user_events", "wajenigeria.origin_hfyl.view_event_pay"],
            ["严格 H5 自然注册 cohort", "success event=order_success", "按 payment date × user × order 去重", "数据截止：2026-09-04"],
            ["累计付费率＝指定生命周期内有至少一笔去重成功订单的 cohort 用户 ÷ cohort 用户。", "ARPU＝指定生命周期内去重成功订单金额 ÷ cohort 用户。"],
            "五个分段查询合并的严格 H5 自然 cohort 支付行为；各月先汇总分子和分母后计算。",
        ),
        source(
            "payment-segmentation", "分包付费阶段分层",
            ["analysis/all_platform_cohort_value_2026_09_04/payment_segmentation/06a_payment_segment_2026_06.json", "analysis/all_platform_cohort_value_2026_09_04/payment_segmentation/06b_payment_segment_2026_07.json", "analysis/all_platform_cohort_value_2026_09_04/payment_segmentation/06c1_payment_segment_2026_08_01_15.json", "analysis/all_platform_cohort_value_2026_09_04/payment_segmentation/06c2_payment_segment_2026_08_16_31.json", "analysis/all_platform_cohort_value_2026_09_04/payment_segmentation/06e_h5_payment_stage_2026_08_full.json", "analysis/all_platform_cohort_value_2026_09_04/sql/06a_payment_segment_2026_06.sql", "analysis/all_platform_cohort_value_2026_09_04/sql/06b_payment_segment_2026_07.sql", "analysis/all_platform_cohort_value_2026_09_04/sql/06c1_payment_segment_2026_08_01_15.sql", "analysis/all_platform_cohort_value_2026_09_04/sql/06c2_payment_segment_2026_08_16_31.sql", "analysis/all_platform_cohort_value_2026_09_04/sql/06e_h5_payment_stage_2026_08_full.sql"],
            ["wajenigeria.origin_hfyl.view_event_pay", "wajenigeria.origin_hfyl.user_info_all"],
            ["success event=order_success", "按 payment date × user × order 去重", "first package / download channel 分包", "数据截止：2026-09-04"],
            ["当月首充＝存在订单发生在历史首付日。", "期初老付费＝历史首付日在窗口起点之前且窗口内付费。", "期内复充＝存在订单发生在历史首付日之后。"],
            "用户画像可关联首付日期的分包阶段拆分；8 月首充/老付费/复充为完整月度，新增注册付费保留半月窗口。",
        ),
        source(
            "phenix-firebase", "Phoenix Firebase 客户端 cohort 诊断",
            ["analysis/all_platform_cohort_value_2026_09_04/firebase_diagnosis/07a_phenix_firebase_retention_diagnosis.json", "analysis/all_platform_cohort_value_2026_09_04/firebase_diagnosis/07b_phenix_firebase_event_inventory.json", "analysis/all_platform_cohort_value_2026_09_04/sql/07a_phenix_firebase_retention_diagnosis.sql", "analysis/all_platform_cohort_value_2026_09_04/sql/07b_phenix_firebase_event_inventory.sql"],
            ["wajenigeria.analytics_517134955.events_*"],
            ["首访 URL 含 p=h5phx", "完整日：2026-08-28—2026-09-02", "仅客户端事件"],
            ["Phoenix 观察留存＝同一 GA4 pseudonymous ID 在指定自然日出现客户端事件 ÷ 带标记的首访 ID。", "Firebase 未发现成功付费事件，不用于成功付费率或财务结论。"],
            "Phoenix H5 前端客户端诊断：可验证回访事件是否缺失，不能替代服务端账号留存和成功支付。",
        ),
    ]

    manifest = {
        "version": 1,
        "surface": "report",
        "title": "Waje 全平台用户生命周期与付费价值分析｜H5 自然新增重点",
        "description": "H5 自然新增为主线、APP 为对照；覆盖留存、LTV、成功支付率、ARPU、分包付费阶段与 Phoenix Firebase 客户端诊断。",
        "generatedAt": "2026-09-04T12:00:00+08:00",
        "sources": sources,
        "accessIssues": [
            "8 月分包首充/老付费/复充有完整月度去重值；新增注册付费仅有两个不相加的半月去重窗口。",
            "Phoenix Firebase 完整表截至 2026-09-02，且没有成功付费事件；支付率以服务端 order_success 为准。",
            "D60/D90 仅展示已达到观察日的 cohort；未成熟结果为 N/A。",
        ],
        "statusDefinitions": {
            "actual": "已执行的 BigQuery 只读聚合结果。",
            "partial": "有决策价值，但某些生命周期窗口、来源或去重范围尚未完整。",
            "N/A": "未成熟、来源没有该字段，或无法安全对齐口径；不表示零。",
        },
        "cards": [
            {"id": "h5-aug-d14-retention", "dataset": "headline", "sourceId": "h5-strict-retention", "description": "8 月严格 H5 自然 cohort 的已成熟第 14 日留存。", "metrics": [{"label": "8 月第14日留存", "field": "h5_aug_day14_retention", "format": "percent"}]},
            {"id": "h5-aug-d14-payment", "dataset": "headline", "sourceId": "h5-payment-cohort", "description": "8 月严格 H5 自然 cohort 的已成熟第 14 日累计成功支付率。", "metrics": [{"label": "8 月第14日付费率", "field": "h5_aug_day14_payment_rate", "format": "percent"}]},
            {"id": "h5-aug-ltv14", "dataset": "headline", "sourceId": "h5-lifecycle-source", "description": "8 月 H5 自然新增在联运生命周期来源中的第 14 日累计 LTV。", "metrics": [{"label": "8 月第14日 LTV", "field": "h5_aug_ltv14", "format": "number"}]},
            {"id": "phenix-day2", "dataset": "headline", "sourceId": "phenix-firebase", "description": "Phoenix 标记首访 cohort 的第 2 日会话开始回访观察值。", "metrics": [{"label": "Phoenix 第2日观察留存", "field": "phenix_day2_observed_retention", "format": "percent"}]},
        ],
        "charts": [
            {"id": "h5-retention-curve", "title": "严格 H5 自然新增留存曲线", "subtitle": "6—8 月注册 cohort；按新增用户加权，只显示已成熟的第 N 个自然日。", "type": "line", "dataset": "h5_retention_curve", "sourceId": "h5-strict-retention", "layout": "full", "encodings": {"x": {"field": "day_number", "type": "quantitative", "label": "第 N 个自然日"}, "y": {"field": "retention_rate", "type": "quantitative", "format": "percent", "label": "留存率"}, "color": {"field": "cohort_month", "type": "nominal", "label": "注册月"}, "tooltip": [{"field": "cohort_month", "type": "nominal"}, {"field": "lifecycle_day", "type": "nominal"}, {"field": "retention_rate", "type": "quantitative", "format": "percent"}, {"field": "mature_cohort_users", "type": "quantitative", "format": "number"}]}},
            {"id": "h5-ltv-curve", "title": "H5 自然新增累计 LTV", "subtitle": "联运生命周期来源；6—8 月 cohort，按新增用户加权。", "type": "line", "dataset": "h5_ltv_curve", "sourceId": "h5-lifecycle-source", "layout": "full", "encodings": {"x": {"field": "day_number", "type": "quantitative", "label": "第 N 个自然日"}, "y": {"field": "ltv", "type": "quantitative", "format": "number", "label": "累计 LTV"}, "color": {"field": "cohort_month", "type": "nominal", "label": "注册月"}, "tooltip": [{"field": "cohort_month", "type": "nominal"}, {"field": "lifecycle_day", "type": "nominal"}, {"field": "ltv", "type": "quantitative", "format": "number"}, {"field": "new_users", "type": "quantitative", "format": "number"}]}},
            {"id": "platform-day2", "title": "各平台第2日留存对照", "subtitle": "6—8 月首平台注册 cohort；每个月独立按 cohort 用户加权。", "type": "bar", "dataset": "platform_retention_monthly", "sourceId": "platform-retention", "layout": "full", "encodings": {"x": {"field": "cohort_month", "type": "nominal", "label": "注册月"}, "y": {"field": "day_2_retention", "type": "quantitative", "format": "percent", "label": "第2日留存"}, "color": {"field": "platform", "type": "nominal", "label": "首平台"}, "tooltip": [{"field": "cohort_month", "type": "nominal"}, {"field": "platform", "type": "nominal"}, {"field": "day_2_retention", "type": "quantitative", "format": "percent"}, {"field": "day_7_retention", "type": "quantitative", "format": "percent"}, {"field": "day_14_retention", "type": "quantitative", "format": "percent"}, {"field": "cohort_users", "type": "quantitative", "format": "number"}]}},
            {"id": "h5-payment-rate", "title": "严格 H5 自然 cohort 累计付费率", "subtitle": "成功订单口径；按注册 cohort 用户加权的第 1/7/14 日累计值。", "type": "bar", "dataset": "h5_payment_curve", "sourceId": "h5-payment-cohort", "layout": "full", "encodings": {"x": {"field": "lifecycle_day", "type": "nominal", "label": "生命周期"}, "y": {"field": "payment_rate", "type": "quantitative", "format": "percent", "label": "累计付费率"}, "color": {"field": "cohort_month", "type": "nominal", "label": "注册月"}, "tooltip": [{"field": "cohort_month", "type": "nominal"}, {"field": "lifecycle_day", "type": "nominal"}, {"field": "payment_rate", "type": "quantitative", "format": "percent"}, {"field": "arpu", "type": "quantitative", "format": "number"}, {"field": "mature_cohort_users", "type": "quantitative", "format": "number"}]}},
            {"id": "phenix-retention", "title": "Phoenix Firebase 客户端回访观察", "subtitle": "带 p=h5phx 标记的首访 cohort；完整日截至 9 月 2 日。", "type": "bar", "dataset": "phenix_retention_curve", "sourceId": "phenix-firebase", "layout": "full", "encodings": {"x": {"field": "lifecycle_day", "type": "nominal", "label": "生命周期"}, "y": {"field": "retention_rate", "type": "quantitative", "format": "percent", "label": "观察留存"}, "color": {"field": "metric", "type": "nominal", "label": "客户端信号"}, "tooltip": [{"field": "cohort_date", "type": "temporal"}, {"field": "lifecycle_day", "type": "nominal"}, {"field": "metric", "type": "nominal"}, {"field": "retention_rate", "type": "quantitative", "format": "percent"}, {"field": "cohort_users", "type": "quantitative", "format": "number"}]}},
        ],
        "tables": [
            {"id": "h5-retention-day2-8", "title": "严格 H5 自然新增：第2—8日留存", "subtitle": "按注册月汇总；每列仅纳入已成熟 cohort。", "dataset": "h5_retention_monthly", "sourceId": "h5-strict-retention", "layout": "full", "density": "spacious", "defaultSort": {"field": "cohort_month", "direction": "asc"}, "columns": [{"field": "cohort_month", "label": "注册月", "type": "text"}, {"field": "cohort_users", "label": "新增用户", "type": "number", "format": "number"}, *[{"field": f"day_{d}_retention", "label": f"第{d}日", "type": "number", "format": "percent"} for d in range(2, 9)]]},
            {"id": "h5-retention-day9-14", "title": "严格 H5 自然新增：第9—14日留存", "subtitle": "按注册月汇总；每列仅纳入已成熟 cohort。", "dataset": "h5_retention_monthly", "sourceId": "h5-strict-retention", "layout": "full", "density": "spacious", "defaultSort": {"field": "cohort_month", "direction": "asc"}, "columns": [{"field": "cohort_month", "label": "注册月", "type": "text"}, {"field": "cohort_users", "label": "新增用户", "type": "number", "format": "number"}, *[{"field": f"day_{d}_retention", "label": f"第{d}日", "type": "number", "format": "percent"} for d in range(9, 15)]]},
            {"id": "h5-retention-long", "title": "严格 H5 自然新增：长周期留存", "subtitle": "第30/60/90日；未成熟 cohort 为 N/A。", "dataset": "h5_retention_monthly", "sourceId": "h5-strict-retention", "layout": "full", "density": "spacious", "defaultSort": {"field": "cohort_month", "direction": "asc"}, "columns": [{"field": "cohort_month", "label": "注册月", "type": "text"}, {"field": "cohort_users", "label": "新增用户", "type": "number", "format": "number"}, *[{"field": f"day_{d}_retention", "label": f"第{d}日", "type": "number", "format": "percent"} for d in [30, 60, 90]]]},
            {"id": "h5-lifecycle-retention", "title": "H5 自然新增：联运生命周期留存", "subtitle": "联运生命周期来源；按注册月对照。", "dataset": "h5_lifecycle_source_monthly", "sourceId": "h5-lifecycle-source", "layout": "full", "density": "spacious", "defaultSort": {"field": "cohort_month", "direction": "asc"}, "columns": [{"field": "cohort_month", "label": "注册月", "type": "text"}, {"field": "new_users", "label": "新增", "type": "number", "format": "number"}, *[{"field": f"day_{d}_retention", "label": f"第{d}日留存", "type": "number", "format": "percent"} for d in [2, 3, 7, 14, 30, 60]]]},
            {"id": "h5-lifecycle-ltv", "title": "H5 自然新增：联运累计 LTV", "subtitle": "第1/7/14/30/60/90日；未成熟值为 N/A。", "dataset": "h5_lifecycle_source_monthly", "sourceId": "h5-lifecycle-source", "layout": "full", "density": "spacious", "defaultSort": {"field": "cohort_month", "direction": "asc"}, "columns": [{"field": "cohort_month", "label": "注册月", "type": "text"}, {"field": "new_users", "label": "新增", "type": "number", "format": "number"}, *[{"field": f"ltv_{d}", "label": f"LTV{d}", "type": "number", "format": "number"} for d in [1, 7, 14, 30, 60, 90]]]},
            {"id": "platform-retention-table", "title": "APP 与 H5 留存对照", "subtitle": "首平台注册 cohort；H5、Android、iOS 分别展示。", "dataset": "platform_retention_monthly", "sourceId": "platform-retention", "layout": "full", "density": "spacious", "defaultSort": {"field": "cohort_month", "direction": "asc"}, "columns": [{"field": "cohort_month", "label": "注册月", "type": "text"}, {"field": "platform", "label": "首平台", "type": "text"}, {"field": "cohort_users", "label": "新增", "type": "number", "format": "number"}, *[{"field": f"day_{d}_retention", "label": f"第{d}日", "type": "number", "format": "percent"} for d in [2, 3, 7, 14, 30, 60, 90]]]},
            {"id": "app-payment-segments", "title": "APP 与 H5：首平台付费阶段概览", "subtitle": "6—7 月完整月度；仅限可关联历史首付画像的用户。", "dataset": "app_payment_segments", "sourceId": "payment-segmentation", "layout": "full", "density": "spacious", "defaultSort": {"field": "period", "direction": "asc"}, "columns": [{"field": "period", "label": "窗口", "type": "text"}, {"field": "platform", "label": "首平台", "type": "text"}, {"field": "unique_paying_users", "label": "付费用户", "type": "number", "format": "number"}, {"field": "unique_new_registered_payers", "label": "新增付费", "type": "number", "format": "number"}, {"field": "unique_first_payers", "label": "首充付费", "type": "number", "format": "number"}, {"field": "unique_old_payers_at_period_start", "label": "期初老付费", "type": "number", "format": "number"}, {"field": "payer_arppu", "label": "付费 ARPPU", "type": "number", "format": "number"}]},
            {"id": "h5-payment-monthly", "title": "严格 H5 自然新增：付费率与 ARPU", "subtitle": "成功订单口径；第 1/7/14 日累计支付结果。", "dataset": "h5_payment_monthly", "sourceId": "h5-payment-cohort", "layout": "full", "density": "spacious", "defaultSort": {"field": "cohort_month", "direction": "asc"}, "columns": [{"field": "cohort_month", "label": "注册月", "type": "text"}, {"field": "cohort_users", "label": "新增", "type": "number", "format": "number"}, *sum(([{"field": f"day_{d}_payment_rate", "label": f"第{d}日付费率", "type": "number", "format": "percent"}, {"field": f"day_{d}_arpu", "label": f"第{d}日 ARPU", "type": "number", "format": "number"}] for d in [1, 7, 14]), [])]},
            {"id": "h5-payment-segments", "title": "H5 PAWAJEBETH5 分包付费阶段", "subtitle": "6—8 月完整月度的首充/老付费/复充；8 月新增付费显示 N/A。", "dataset": "h5_payment_segments", "sourceId": "payment-segmentation", "layout": "full", "density": "spacious", "defaultSort": {"field": "period", "direction": "asc"}, "columns": [{"field": "period", "label": "窗口", "type": "text"}, {"field": "unique_paying_users", "label": "付费用户", "type": "number", "format": "number"}, {"field": "unique_new_registered_payers", "label": "新增付费", "type": "number", "format": "number"}, {"field": "unique_first_payers", "label": "首充付费", "type": "number", "format": "number"}, {"field": "old_payers", "label": "期初老付费", "type": "number", "format": "number"}, {"field": "unique_repeat_payers_after_first_payment", "label": "期内复充", "type": "number", "format": "number"}, {"field": "pay_amount", "label": "成功支付额", "type": "number", "format": "number"}, {"field": "payer_arppu", "label": "付费 ARPPU", "type": "number", "format": "number"}, {"field": "repeat_payer_arppu", "label": "复充 ARPPU", "type": "number", "format": "number"}]},
            {"id": "h5-august-new-windows", "title": "H5 PAWAJEBETH5：8月新增付费半月窗口", "subtitle": "每个半月内独立去重；两行不可相加为整月人数。", "dataset": "h5_payment_august_new_windows", "sourceId": "payment-segmentation", "layout": "full", "density": "spacious", "defaultSort": {"field": "period", "direction": "asc"}, "columns": [{"field": "period", "label": "窗口", "type": "text"}, {"field": "unique_new_registered_payers", "label": "新增付费", "type": "number", "format": "number"}, {"field": "unique_paying_users", "label": "窗口付费用户", "type": "number", "format": "number"}, {"field": "unique_first_payers", "label": "窗口首充", "type": "number", "format": "number"}]},
            {"id": "phenix-firebase-table", "title": "Phoenix Firebase 诊断明细", "subtitle": "同一客户端匿名 ID 的回访观察；不是服务端账号留存。", "dataset": "phenix_retention_daily", "sourceId": "phenix-firebase", "layout": "full", "density": "spacious", "defaultSort": {"field": "cohort_date", "direction": "asc"}, "columns": [{"field": "cohort_date", "label": "首访日期", "type": "text"}, {"field": "cohort_users", "label": "首访 ID", "type": "number", "format": "number"}, {"field": "day_2_any_event_users", "label": "第2日任意事件", "type": "number", "format": "number"}, {"field": "day_2_session_start_users", "label": "第2日会话开始", "type": "number", "format": "number"}, {"field": "day_2_page_view_users", "label": "第2日页面浏览", "type": "number", "format": "number"}, {"field": "day_4_any_event_users", "label": "第4日任意事件", "type": "number", "format": "number"}, {"field": "day_4_session_start_users", "label": "第4日会话开始", "type": "number", "format": "number"}]},
            {"id": "source-freshness", "title": "数据源最新完整日期", "subtitle": "本报告主要服务器侧来源均已覆盖至 9 月 4 日。", "dataset": "source_freshness", "sourceId": "platform-retention", "layout": "full", "density": "spacious", "defaultSort": {"field": "source_name", "direction": "asc"}, "columns": [{"field": "source_name", "label": "来源", "type": "text"}, {"field": "latest_seen_date", "label": "最新日期", "type": "text"}, {"field": "distinct_date_count", "label": "近期连续日期数", "type": "number", "format": "number"}]},
        ],
        "blocks": [
            {"id": "title", "type": "markdown", "body": "# Waje 全平台用户生命周期与付费价值分析｜H5 自然新增重点"},
            {"id": "summary", "type": "markdown", "body": f"## Executive Summary\n\n**H5 自然新增的留存没有在 8 月继续恶化。** 严格 H5 自然 cohort 的第 2 日留存从 7 月的 {pct(july_retention['day_2_retention'])} 升至 8 月的 {pct(august_retention['day_2_retention'])}（{pp(august_retention['day_2_retention'], july_retention['day_2_retention'])}）；第 14 日也从 {pct(july_retention['day_14_retention'])} 升至 {pct(august_retention['day_14_retention'])}。但全量 H5 首平台 cohort 的第 2 日留存从 5.14% 降至 4.65%，需把问题优先放在其他 H5 包/渠道结构，而不是直接归因自然新增留存。\n\n**8 月的主要矛盾在早期支付覆盖，而不是单纯留存。** 严格 H5 自然 cohort 第 14 日成功支付率从 7 月的 {pct(july_payment['day_14_payment_rate'])} 降至 8 月的 {pct(august_payment['day_14_payment_rate'])}（{pp(august_payment['day_14_payment_rate'], july_payment['day_14_payment_rate'])}），但第 14 日 ARPU 从 {compact(july_payment['day_14_arpu'])} 升至 {compact(august_payment['day_14_arpu'])}。这表示更少的新用户进入支付，但留下/支付的人贡献更高；需优先检查首充触发与支付完成漏斗。\n\n**H5 生命周期价值在 8 月继续走弱。** 联运来源的第 14 日 LTV 由 7 月 {compact(july_lifecycle['ltv_14'])} 降至 8 月 {compact(august_lifecycle['ltv_14'])}（约 {(august_lifecycle['ltv_14']/july_lifecycle['ltv_14']-1)*100:.1f}%）；第 30 日 LTV 亦由 {compact(july_lifecycle['ltv_30'])} 降至 {compact(august_lifecycle['ltv_30'])}。\n\n**Phoenix 的 Firebase 观察留存很低，但当前没有“页面加载或 session 事件缺失”的直接证据。** 成熟 cohort 的第 2 日任意事件回访为 {pct(firebase_summary['day_2_any_event_users_rate'])}，会话开始回访为 {pct(firebase_summary['day_2_session_start_users_rate'])}，两者几乎一致；首访当日页面浏览和会话开始均覆盖 cohort。现有 Firebase 事件中没有成功付费事件，因此不能用它计算付费率。"},
            {"id": "headline", "type": "metric-strip", "cardIds": ["h5-aug-d14-retention", "h5-aug-d14-payment", "h5-aug-ltv14", "phenix-day2"]},
            {"id": "definitions", "type": "markdown", "body": "## 口径先对齐：第 N 日、严格 H5 自然 cohort 与支付分层\n\n**第 N 日是第 N 个自然日。** 例如第 2 日是注册/首访后次日，第 3 日是第 3 个自然日；未达到观察日的 cohort 显示 N/A。\n\n**严格 H5 自然 cohort** 同时要求 Web 首包与 PAWAJEBETH5 的下载、首渠道和首子渠道匹配。留存是任意 Waje 日活回访，不等同于回到同一游戏。支付仅计去重的成功订单。\n\n**新增付费、首充付费、老付费与复充不是可加总的人群。** 新增付费是注册月内付费；首充是历史首付发生在窗口内；老付费是窗口起点前已首充且窗口内仍付费；复充是窗口内有首付日之后的订单。"},
            {"id": "h5-retention-finding", "type": "markdown", "body": f"## H5 自然新增：第 2—14 日留存稳定，转折点不在回访\n\n7 月到 8 月，严格 H5 自然 cohort 的第 2 日留存 {pct(july_retention['day_2_retention'])} → {pct(august_retention['day_2_retention'])}，第 7 日 {pct(july_retention['day_7_retention'])} → {pct(august_retention['day_7_retention'])}，第 14 日 {pct(july_retention['day_14_retention'])} → {pct(august_retention['day_14_retention'])}。第 7 日仅小幅波动，而第 14 日仍改善。**H5 自然新增的留存曲线不是当前首要下滑点；应将资源优先投入支付转化与其他 H5 入口的拆解。**", "sourceId": "h5-strict-retention"},
            {"id": "h5-retention-chart", "type": "chart", "chartId": "h5-retention-curve"},
            {"id": "h5-retention-table-short", "type": "table", "tableId": "h5-retention-day2-8"},
            {"id": "h5-retention-table-late", "type": "table", "tableId": "h5-retention-day9-14"},
            {"id": "h5-retention-table-long", "type": "table", "tableId": "h5-retention-long"},
            {"id": "ltv-finding", "type": "markdown", "body": f"## 价值曲线下移：8 月第 1—30 日 LTV 均低于 7 月\n\n8 月的第 1 日 LTV 为 {compact(august_lifecycle['ltv_1'])}，低于 7 月的 {compact(july_lifecycle['ltv_1'])}；第 7 日为 {compact(august_lifecycle['ltv_7'])}，低于 {compact(july_lifecycle['ltv_7'])}；第 14 日为 {compact(august_lifecycle['ltv_14'])}，低于 {compact(july_lifecycle['ltv_14'])}。**价值差距从首日即出现，重点核查首充触达、支付完成与早期复充，而不是等待第 30 日才处理。**", "sourceId": "h5-lifecycle-source"},
            {"id": "ltv-chart", "type": "chart", "chartId": "h5-ltv-curve"},
            {"id": "ltv-retention-table", "type": "table", "tableId": "h5-lifecycle-retention"},
            {"id": "ltv-table", "type": "table", "tableId": "h5-lifecycle-ltv"},
            {"id": "platform-finding", "type": "markdown", "body": "## APP 与 H5：8 月首平台 cohort 均走弱，Android 量级最大\n\n7 月到 8 月，Android 第 2 日留存由 22.44% 降至 19.44%，H5 由 5.14% 降至 4.65%，iOS 由 38.69% 降至 38.00%。Android 8 月 cohort 规模约 518k，显著大于 H5 和 iOS，因此全产品留存波动不能仅以 H5 解释。**应先按包名、入口和新老渠道拆 Android 的下降，再回看全产品口径。**", "sourceId": "platform-retention"},
            {"id": "platform-chart", "type": "chart", "chartId": "platform-day2"},
            {"id": "platform-table", "type": "table", "tableId": "platform-retention-table"},
            {"id": "app-payment-segment-table", "type": "table", "tableId": "app-payment-segments"},
            {"id": "payment-finding", "type": "markdown", "body": f"## 支付覆盖下降、单用户价值上升：先诊断首充漏斗\n\n严格 H5 自然 cohort 的第 1/7/14 日成功支付率在 8 月均低于 7 月：第 1 日 {pct(july_payment['day_1_payment_rate'])} → {pct(august_payment['day_1_payment_rate'])}，第 7 日 {pct(july_payment['day_7_payment_rate'])} → {pct(august_payment['day_7_payment_rate'])}，第 14 日 {pct(july_payment['day_14_payment_rate'])} → {pct(august_payment['day_14_payment_rate'])}。与此同时，第 14 日 ARPU {compact(july_payment['day_14_arpu'])} → {compact(august_payment['day_14_arpu'])}。**先看支付页到订单成功的完成率、失败/取消原因和首充金额档位；不能仅用 ARPU 上升判断变现改善。**", "sourceId": "h5-payment-cohort"},
            {"id": "payment-chart", "type": "chart", "chartId": "h5-payment-rate"},
            {"id": "payment-table", "type": "table", "tableId": "h5-payment-monthly"},
            {"id": "payment-segment-finding", "type": "markdown", "body": f"## 分包付费阶段：8 月首充与老付费均可完整月度核对\n\nH5 PAWAJEBETH5 的完整月度、可关联首付画像中，付费用户从 6 月 {compact(h5_segment_june['unique_paying_users'], 0)} 增至 7 月 {compact(h5_segment_july['unique_paying_users'], 0)}；首充用户由 {compact(h5_segment_june['unique_first_payers'], 0)} 增至 {compact(h5_segment_july['unique_first_payers'], 0)}，但付费 ARPPU 从 {compact(h5_segment_june['payer_arppu'])} 降至 {compact(h5_segment_july['payer_arppu'])}。8 月完整月度有 {compact(payment_august_full['unique_paying_users'], 0)} 名付费用户、{compact(payment_august_full['unique_first_payers'], 0)} 名首充、{compact(payment_august_full['unique_old_payers_at_month_start'], 0)} 名期初老付费和 {compact(payment_august_full['unique_repeat_payers_after_first_payment'], 0)} 名期内复充，付费 ARPPU 为 {compact(payment_august_full['payer_arppu'])}。新增注册付费只保留独立半月窗口，**不得相加为 8 月去重总数。**", "sourceId": "payment-segmentation"},
            {"id": "payment-segment-table", "type": "table", "tableId": "h5-payment-segments"},
            {"id": "payment-segment-new-window-table", "type": "table", "tableId": "h5-august-new-windows"},
            {"id": "phenix-finding", "type": "markdown", "body": f"## Phoenix：客户端回访极低，但不像单纯页面加载漏报\n\nPhoenix 标记首访 cohort 的第 2 日任意事件回访为 {firebase_summary['day_2_any_event_users']}/{firebase_summary['day_2_mature_cohort_users']}（{pct(firebase_summary['day_2_any_event_users_rate'])}），会话开始回访为 {firebase_summary['day_2_session_start_users']}/{firebase_summary['day_2_mature_cohort_users']}（{pct(firebase_summary['day_2_session_start_users_rate'])}）；第 4 日任意事件回访为 {firebase_summary['day_4_any_event_users']}/{firebase_summary['day_4_mature_cohort_users']}（{pct(firebase_summary['day_4_any_event_users_rate'])}）。任意事件、会话开始和页面浏览的回访量几乎相同，说明当前看不到“页面有回访但 session_start 没有上报”的明显缺口。**下一步应验证 H5 匿名 ID 是否跨日重置，并将前端首访与服务端账号/登录会话关联。**", "sourceId": "phenix-firebase"},
            {"id": "phenix-chart", "type": "chart", "chartId": "phenix-retention"},
            {"id": "phenix-table", "type": "table", "tableId": "phenix-firebase-table"},
            {"id": "recommended-next", "type": "markdown", "body": "## Recommended next steps\n\n1. **P0：首充漏斗复核。** 按 H5 包名/入口输出支付页到成功订单的到达、发起、成功、失败/取消，以及金额档位；以服务端成功订单为唯一支付真相。\n2. **P0：全量 H5 下滑拆解。** 将 H5 按包名、首渠道、入口页和新/老用户分开，量化 7 月→8 月第 2 日留存下降来自哪一组；不要用严格自然 cohort 代替全量 H5。\n3. **P0：Phoenix 身份连续性验证。** 增加前端 `loaded/ready`、登录/账号关联和匿名 ID 变更的聚合监控；验证跨日回访是否因存储重置而被切为新 ID。\n4. **P1：补齐 8 月完整月度分包老付费去重视图。** 建立预聚合的“月 × 包 × 首付阶段”视图，避免每次跨月唯一去重超过单条查询成本上限。"},
            {"id": "questions", "type": "markdown", "body": "## Further Questions\n\n- 8 月全量 H5 的下降由哪些具体包名、入口页和首渠道贡献？\n- 8 月首充成功率下降是支付失败、金额档位、活动变化，还是流量结构变化？\n- Phoenix 是否在跨日时重置 Firebase 匿名 ID；服务端账号回访率是否同样低？"},
            {"id": "caveats", "type": "markdown", "body": "## Caveats and Assumptions\n\n- H5 联运生命周期来源、严格 H5 cohort 与全量 H5 首平台 cohort 的分母不同，只比较各自趋势，不把绝对数直接互相替代。\n- 当前 LTV 来源没有已验证的首平台映射，因此报告不把渠道字段强行转换为 Android/iOS/H5 的平台 LTV；APP 以留存与付费阶段进行对照。\n- 8 月第 60/90 日等未成熟窗口为 N/A，不以 0% 补齐。\n- Phoenix Firebase 仅反映客户端匿名 ID 行为，完整日截至 9 月 2 日；它不能替代服务端账号留存或成功付费。\n- 所有结果均为聚合数据；不展示或保存用户、订单、设备、URL、支付参考号或凭据。"},
            {"id": "freshness", "type": "table", "tableId": "source-freshness"},
        ],
    }

    table_splits: dict[str, list[tuple[str, str, list[str]]]] = {
        "h5-retention-day2-8": [
            ("h5-retention-day2-5", "严格 H5 自然新增：第2—5日留存", ["cohort_month", "cohort_users", "day_2_retention", "day_3_retention", "day_4_retention", "day_5_retention"]),
            ("h5-retention-day6-8", "严格 H5 自然新增：第6—8日留存", ["cohort_month", "cohort_users", "day_6_retention", "day_7_retention", "day_8_retention"]),
        ],
        "h5-retention-day9-14": [
            ("h5-retention-day9-11", "严格 H5 自然新增：第9—11日留存", ["cohort_month", "cohort_users", "day_9_retention", "day_10_retention", "day_11_retention"]),
            ("h5-retention-day12-14", "严格 H5 自然新增：第12—14日留存", ["cohort_month", "cohort_users", "day_12_retention", "day_13_retention", "day_14_retention"]),
        ],
        "h5-lifecycle-retention": [
            ("h5-lifecycle-retention-short", "H5 自然新增：联运第2—14日留存", ["cohort_month", "new_users", "day_2_retention", "day_3_retention", "day_7_retention", "day_14_retention"]),
            ("h5-lifecycle-retention-long", "H5 自然新增：联运第30/60日留存", ["cohort_month", "new_users", "day_30_retention", "day_60_retention"]),
        ],
        "h5-lifecycle-ltv": [
            ("h5-lifecycle-ltv-short", "H5 自然新增：联运 LTV1/7/14", ["cohort_month", "new_users", "ltv_1", "ltv_7", "ltv_14"]),
            ("h5-lifecycle-ltv-long", "H5 自然新增：联运 LTV30/60/90", ["cohort_month", "new_users", "ltv_30", "ltv_60", "ltv_90"]),
        ],
        "platform-retention-table": [
            ("platform-retention-short", "APP 与 H5：第2—14日留存", ["cohort_month", "platform", "cohort_users", "day_2_retention", "day_3_retention", "day_7_retention", "day_14_retention"]),
            ("platform-retention-long", "APP 与 H5：第30/60/90日留存", ["cohort_month", "platform", "cohort_users", "day_30_retention", "day_60_retention", "day_90_retention"]),
        ],
        "h5-payment-monthly": [
            ("h5-payment-rate-table", "严格 H5 自然新增：第1/7/14日付费率", ["cohort_month", "cohort_users", "day_1_payment_rate", "day_7_payment_rate", "day_14_payment_rate"]),
            ("h5-payment-arpu-table", "严格 H5 自然新增：第1/7/14日 ARPU", ["cohort_month", "cohort_users", "day_1_arpu", "day_7_arpu", "day_14_arpu"]),
        ],
        "h5-payment-segments": [
            ("h5-payment-segments-users", "H5 PAWAJEBETH5：付费用户阶段", ["period", "unique_paying_users", "unique_new_registered_payers", "unique_first_payers", "old_payers", "unique_repeat_payers_after_first_payment"]),
            ("h5-payment-segments-value", "H5 PAWAJEBETH5：支付额与 ARPPU", ["period", "pay_amount", "payer_arppu", "repeat_payer_arppu"]),
        ],
        "phenix-firebase-table": [
            ("phenix-firebase-day2", "Phoenix Firebase：第2日诊断", ["cohort_date", "cohort_users", "day_2_any_event_users", "day_2_session_start_users", "day_2_page_view_users"]),
            ("phenix-firebase-day4", "Phoenix Firebase：第4日诊断", ["cohort_date", "cohort_users", "day_4_any_event_users", "day_4_session_start_users"]),
        ],
    }
    table_blocks: dict[str, list[str]] = {}
    rewritten_tables: list[dict[str, Any]] = []
    for table in manifest["tables"]:
        plans = table_splits.get(table["id"])
        if not plans:
            rewritten_tables.append(table)
            continue
        columns_by_field = {column["field"]: column for column in table["columns"]}
        table_blocks[table["id"]] = []
        for clone_id, clone_title, fields in plans:
            clone = {**table, "id": clone_id, "title": clone_title, "columns": [columns_by_field[field] for field in fields]}
            rewritten_tables.append(clone)
            table_blocks[table["id"]].append(clone_id)
    manifest["tables"] = rewritten_tables
    rewritten_blocks: list[dict[str, Any]] = []
    for block in manifest["blocks"]:
        if block.get("type") == "table" and block.get("tableId") in table_blocks:
            for index, table_id in enumerate(table_blocks[block["tableId"]], start=1):
                rewritten_blocks.append({"id": f"{block['id']}-{index}", "type": "table", "tableId": table_id})
        else:
            rewritten_blocks.append(block)
    manifest["blocks"] = rewritten_blocks

    h5_payment_segments = []
    for row in h5_segment_rows:
        h5_payment_segments.append({
            **row,
            "old_payers": row.get("unique_old_payers_at_period_start") or row.get("unique_old_payers_at_month_start"),
        })
    h5_payment_segments.append({
        "period": "2026-08",
        "unique_paying_users": payment_august_full["unique_paying_users"],
        "unique_new_registered_payers": None,
        "unique_first_payers": payment_august_full["unique_first_payers"],
        "old_payers": payment_august_full["unique_old_payers_at_month_start"],
        "unique_repeat_payers_after_first_payment": payment_august_full["unique_repeat_payers_after_first_payment"],
        "pay_amount": payment_august_full["pay_amount"],
        "payer_arppu": payment_august_full["payer_arppu"],
        "repeat_payer_arppu": None,
    })
    snapshot = {
        "version": 1,
        "generatedAt": "2026-09-04T12:00:00+08:00",
        "status": "partial",
        "datasets": {
            "headline": headline,
            "h5_retention_curve": h5_retention_curve,
            "h5_retention_monthly": h5_retention,
            "h5_ltv_curve": h5_ltv_curve,
            "h5_lifecycle_source_monthly": lifecycle,
            "platform_retention_monthly": platform_d2,
            "app_payment_segments": app_payment_segments,
            "h5_payment_curve": h5_payment_curve,
            "h5_payment_monthly": h5_payment,
            "h5_payment_segments": h5_payment_segments,
            "h5_payment_august_new_windows": h5_august_windows,
            "phenix_retention_curve": firebase_curve,
            "phenix_retention_daily": firebase_rows,
            "phenix_event_inventory": firebase_inventory,
            "source_freshness": summary["source_freshness"],
        },
    }
    # Executive presentation layer: retain the complete reviewed snapshot above,
    # but reduce the reader-facing report to decision evidence rather than a
    # stitched audit workbook.
    snapshot["datasets"]["h5_retention_short_curve"] = [
        row for row in h5_retention_curve if int(row["day_number"]) <= 14
    ]
    snapshot["datasets"]["h5_ltv_short_curve"] = [
        row for row in h5_ltv_curve if int(row["day_number"]) <= 14
    ]

    manifest["title"] = "Waje 增长质量诊断｜H5 自然新增重点"
    manifest["description"] = "面向业务负责人的增长质量诊断：先看 H5 自然新增的留存、支付覆盖与 LTV，再看 APP 对照与 Phoenix 客户端边界。"
    manifest["charts"] = [
        {
            "id": "h5-retention-short",
            "title": "严格 H5 自然新增：第2—14日留存",
            "subtitle": "6—8 月注册 cohort；按新增用户加权，只显示已成熟观察日。",
            "type": "line",
            "dataset": "h5_retention_short_curve",
            "sourceId": "h5-strict-retention",
            "layout": "full",
            "encodings": {
                "x": {"field": "day_number", "type": "quantitative", "label": "第 N 个自然日"},
                "y": {"field": "retention_rate", "type": "quantitative", "format": "percent", "label": "留存率"},
                "color": {"field": "cohort_month", "type": "nominal", "label": "注册月"},
                "tooltip": [
                    {"field": "cohort_month", "type": "nominal"},
                    {"field": "lifecycle_day", "type": "nominal"},
                    {"field": "retention_rate", "type": "quantitative", "format": "percent"},
                    {"field": "mature_cohort_users", "type": "quantitative", "format": "number"},
                ],
            },
        },
        {
            "id": "h5-ltv-short",
            "title": "H5 自然新增：第1—14日累计 LTV",
            "subtitle": "联运生命周期来源；6—8 月 cohort，按新增用户加权。",
            "type": "line",
            "dataset": "h5_ltv_short_curve",
            "sourceId": "h5-lifecycle-source",
            "layout": "full",
            "encodings": {
                "x": {"field": "day_number", "type": "quantitative", "label": "第 N 个自然日"},
                "y": {"field": "ltv", "type": "quantitative", "format": "number", "label": "累计 LTV"},
                "color": {"field": "cohort_month", "type": "nominal", "label": "注册月"},
                "tooltip": [
                    {"field": "cohort_month", "type": "nominal"},
                    {"field": "lifecycle_day", "type": "nominal"},
                    {"field": "ltv", "type": "quantitative", "format": "number"},
                    {"field": "new_users", "type": "quantitative", "format": "number"},
                ],
            },
        },
        {
            "id": "h5-payment-rate-clean",
            "title": "严格 H5 自然新增：累计成功支付率",
            "subtitle": "第1/7/14日；仅计去重后的成功订单。",
            "type": "bar",
            "dataset": "h5_payment_curve",
            "sourceId": "h5-payment-cohort",
            "layout": "full",
            "encodings": {
                "x": {"field": "lifecycle_day", "type": "nominal", "label": "生命周期"},
                "y": {"field": "payment_rate", "type": "quantitative", "format": "percent", "label": "累计付费率"},
                "color": {"field": "cohort_month", "type": "nominal", "label": "注册月"},
                "tooltip": [
                    {"field": "cohort_month", "type": "nominal"},
                    {"field": "lifecycle_day", "type": "nominal"},
                    {"field": "payment_rate", "type": "quantitative", "format": "percent"},
                    {"field": "arpu", "type": "quantitative", "format": "number"},
                    {"field": "mature_cohort_users", "type": "quantitative", "format": "number"},
                ],
            },
        },
    ]
    manifest["tables"] = [
        {
            "id": "h5-lifecycle-key",
            "title": "H5 自然新增：留存与价值关键读数",
            "subtitle": "联运生命周期来源；以第14日和第30日价值为核心比较。",
            "dataset": "h5_lifecycle_source_monthly",
            "sourceId": "h5-lifecycle-source",
            "layout": "full",
            "density": "spacious",
            "defaultSort": {"field": "cohort_month", "direction": "asc"},
            "columns": [
                {"field": "cohort_month", "label": "注册月", "type": "text"},
                {"field": "new_users", "label": "新增", "type": "number", "format": "number"},
                {"field": "day_2_retention", "label": "第2日留存", "type": "number", "format": "percent"},
                {"field": "day_7_retention", "label": "第7日留存", "type": "number", "format": "percent"},
                {"field": "day_14_retention", "label": "第14日留存", "type": "number", "format": "percent"},
                {"field": "ltv_14", "label": "LTV14", "type": "number", "format": "number"},
                {"field": "ltv_30", "label": "LTV30", "type": "number", "format": "number"},
            ],
        },
        {
            "id": "h5-payment-key",
            "title": "严格 H5 自然新增：支付覆盖与 ARPU",
            "subtitle": "成功订单口径；各列按成熟注册批次用户加权。",
            "dataset": "h5_payment_monthly",
            "sourceId": "h5-payment-cohort",
            "layout": "full",
            "density": "spacious",
            "defaultSort": {"field": "cohort_month", "direction": "asc"},
            "columns": [
                {"field": "cohort_month", "label": "注册月", "type": "text"},
                {"field": "day_1_payment_rate", "label": "第1日付费率", "type": "number", "format": "percent"},
                {"field": "day_7_payment_rate", "label": "第7日付费率", "type": "number", "format": "percent"},
                {"field": "day_14_payment_rate", "label": "第14日付费率", "type": "number", "format": "percent"},
                {"field": "day_14_arpu", "label": "第14日 ARPU", "type": "number", "format": "number"},
            ],
        },
        {
            "id": "platform-retention-key",
            "title": "APP 与 H5：首平台注册批次对照",
            "subtitle": "展示第2/7/14日留存；Android、H5、iOS 并列。",
            "dataset": "platform_retention_monthly",
            "sourceId": "platform-retention",
            "layout": "full",
            "density": "spacious",
            "defaultSort": {"field": "cohort_month", "direction": "asc"},
            "columns": [
                {"field": "cohort_month", "label": "注册月", "type": "text"},
                {"field": "platform", "label": "首平台", "type": "text"},
                {"field": "cohort_users", "label": "新增", "type": "number", "format": "number"},
                {"field": "day_2_retention", "label": "第2日", "type": "number", "format": "percent"},
                {"field": "day_7_retention", "label": "第7日", "type": "number", "format": "percent"},
                {"field": "day_14_retention", "label": "第14日", "type": "number", "format": "percent"},
            ],
        },
        {
            "id": "h5-payment-stage-key",
            "title": "H5 PAWAJEBETH5：付费阶段",
            "subtitle": "首付画像可关联用户；8月新增注册付费暂不可用，半月窗口在来源中保留。",
            "dataset": "h5_payment_segments",
            "sourceId": "payment-segmentation",
            "layout": "full",
            "density": "spacious",
            "defaultSort": {"field": "period", "direction": "asc"},
            "columns": [
                {"field": "period", "label": "窗口", "type": "text"},
                {"field": "unique_paying_users", "label": "付费用户", "type": "number", "format": "number"},
                {"field": "unique_first_payers", "label": "首充", "type": "number", "format": "number"},
                {"field": "old_payers", "label": "期初老付费", "type": "number", "format": "number"},
                {"field": "unique_repeat_payers_after_first_payment", "label": "期内复充", "type": "number", "format": "number"},
                {"field": "payer_arppu", "label": "付费 ARPPU", "type": "number", "format": "number"},
            ],
        },
        {
            "id": "phenix-key",
            "title": "Phoenix：客户端回访观察",
            "subtitle": "带 p=h5phx 标记的首访批次；只用于前端行为诊断。",
            "dataset": "phenix_retention_daily",
            "sourceId": "phenix-firebase",
            "layout": "full",
            "density": "spacious",
            "defaultSort": {"field": "cohort_date", "direction": "asc"},
            "columns": [
                {"field": "cohort_date", "label": "首访日", "type": "text"},
                {"field": "cohort_users", "label": "首访 ID", "type": "number", "format": "number"},
                {"field": "day_2_any_event_users", "label": "第2日任意事件", "type": "number", "format": "number"},
                {"field": "day_2_session_start_users", "label": "第2日会话", "type": "number", "format": "number"},
                {"field": "day_4_any_event_users", "label": "第4日任意事件", "type": "number", "format": "number"},
            ],
        },
    ]
    manifest["blocks"] = [
        {"id": "title", "type": "markdown", "body": "# Waje 增长质量诊断｜H5 自然新增重点"},
        {"id": "summary", "type": "markdown", "body": f"## 执行摘要\n\n**H5 自然新增留存稳定，问题不在回访本身。** 8 月严格 H5 自然新增注册批次的第 2 日留存为 {pct(august_retention['day_2_retention'])}、第 14 日为 {pct(august_retention['day_14_retention'])}，均略高于 7 月；但全量 H5 首平台新增批次的第 2 日从 5.14% 降至 4.65%。\n\n**8 月首先要解决的是支付覆盖下降。** 第 14 日成功支付率从 {pct(july_payment['day_14_payment_rate'])} 降至 {pct(august_payment['day_14_payment_rate'])}，同时第 14 日 ARPU 从 {compact(july_payment['day_14_arpu'])} 升至 {compact(august_payment['day_14_arpu'])}。\n\n**H5 生命周期价值继续下移。** 第 14 日 LTV 从 {july_lifecycle['ltv_14']:.2f} 降至 {august_lifecycle['ltv_14']:.2f}，减少 {july_lifecycle['ltv_14'] - august_lifecycle['ltv_14']:.2f}（{(august_lifecycle['ltv_14'] / july_lifecycle['ltv_14'] - 1) * 100:.1f}%）；第 30 日 LTV 从 {july_lifecycle['ltv_30']:.2f} 降至 {august_lifecycle['ltv_30']:.2f}，减少 {july_lifecycle['ltv_30'] - august_lifecycle['ltv_30']:.2f}（{(august_lifecycle['ltv_30'] / july_lifecycle['ltv_30'] - 1) * 100:.1f}%）。\n\n**Phoenix 的低观察留存不是单纯页面上报缺失。** 第 2 日任意事件回访与会话开始回访均约 {pct(firebase_summary['day_2_any_event_users_rate'])}；下一步应验证匿名 ID 跨日连续性，并连接到服务端账号回访。"},
        {"id": "headline", "type": "metric-strip", "cardIds": ["h5-aug-d14-retention", "h5-aug-d14-payment", "h5-aug-ltv14", "phenix-day2"]},
        {"id": "priority", "type": "markdown", "body": "## 现在先做什么\n\n1. **首充漏斗：** 按 H5 包名和入口核查支付页到成功订单的到达、发起、失败/取消与金额档位。\n2. **全量 H5 拆解：** 按包名、入口与首渠道找到 7 月到 8 月第 2 日留存下降的具体组。\n3. **Phoenix 身份连续性：** 监控匿名 ID 变化，并与服务端账号/登录会话做聚合关联。"},
        {"id": "retention-story", "type": "markdown", "body": f"## H5 自然新增：第2—14日留存没有继续恶化\n\n8 月第 2 日留存较 7 月提升 {pp(august_retention['day_2_retention'], july_retention['day_2_retention'])}，第 14 日提升 {pp(august_retention['day_14_retention'], july_retention['day_14_retention'])}。**这意味着自然新增回访不是当前首要劣化点，排查应从其他 H5 流量结构和支付转化开始。**", "sourceId": "h5-strict-retention"},
        {"id": "retention-chart", "type": "chart", "chartId": "h5-retention-short"},
        {"id": "ltv-payment-story", "type": "markdown", "body": f"## 价值从首日开始走弱，支付覆盖是关键断点\n\n8 月第 14 日 LTV 为 {compact(august_lifecycle['ltv_14'])}，低于 7 月的 {compact(july_lifecycle['ltv_14'])}；同时第 14 日付费率下降 {pp(august_payment['day_14_payment_rate'], july_payment['day_14_payment_rate'])}。**优先验证首充触发、支付完成与早期复充，不要用 ARPU 上升误判整体变现改善。**", "sourceId": "h5-lifecycle-source"},
        {"id": "ltv-chart", "type": "chart", "chartId": "h5-ltv-short"},
        {"id": "payment-chart", "type": "chart", "chartId": "h5-payment-rate-clean"},
        {"id": "h5-lifecycle-table", "type": "table", "tableId": "h5-lifecycle-key"},
        {"id": "h5-payment-table", "type": "table", "tableId": "h5-payment-key"},
        {"id": "platform-story", "type": "markdown", "body": "## APP 端也在走弱，Android 是更大的量级变量\n\n7 月到 8 月，Android 第 2 日留存从 22.44% 降至 19.44%，H5 从 5.14% 降至 4.65%，iOS 从 38.69% 降至 38.00%。Android 的 8 月 cohort 规模约 518k，远高于 H5 与 iOS；**全产品问题不能只围绕 H5 解释。**", "sourceId": "platform-retention"},
        {"id": "platform-table", "type": "table", "tableId": "platform-retention-key"},
        {"id": "stage-story", "type": "markdown", "body": f"## H5 PAWAJEBETH5：8 月仍由首充与复充共同支撑\n\n8 月完整月度可关联首付画像中，有 {compact(payment_august_full['unique_first_payers'], 0)} 名首充、{compact(payment_august_full['unique_old_payers_at_month_start'], 0)} 名期初老付费与 {compact(payment_august_full['unique_repeat_payers_after_first_payment'], 0)} 名期内复充。**新增注册付费仍只适合按半月观察，不能把两个半月人数相加。**", "sourceId": "payment-segmentation"},
        {"id": "stage-table", "type": "table", "tableId": "h5-payment-stage-key"},
        {"id": "phenix-story", "type": "markdown", "body": f"## Phoenix：先确认身份连续性，再判断真实流失\n\n成熟 Phoenix cohort 的第 2 日任意事件回访为 {firebase_summary['day_2_any_event_users']}/{firebase_summary['day_2_mature_cohort_users']}，与会话开始回访几乎相同。现有事件没有成功付费信号；**这份数据适合定位前端回访与身份连续性，不适合给出支付或财务结论。**", "sourceId": "phenix-firebase"},
        {"id": "phenix-table", "type": "table", "tableId": "phenix-key"},
        {"id": "caveats", "type": "markdown", "body": "## 数据边界\n\n- 严格 H5 自然新增注册批次、联运生命周期来源与全量 H5 首平台新增批次的分母不同，只比较各自趋势。\n- 第 N 日表示第 N 个自然日；未成熟窗口显示“暂不可用”。\n- APP LTV 暂无经验证的首平台映射，因此不强行给出 Android/iOS/H5 LTV。\n- Phoenix 完整客户端数据截至 9 月 2 日，且不含成功付费事件。"},
    ]

    # Apply the reference report's visual language through native artifact
    # features: fixed cohort colors, clear section numbering, compact source
    # captions, value labels, and only true movement fields highlighted.
    cohort_fields = [("2026-06", "jun", "blue"), ("2026-07", "jul", "green"), ("2026-08", "aug", "yellow")]

    def pivot_by_day(rows: list[dict[str, Any]], value_field: str) -> list[dict[str, Any]]:
        grouped: dict[int, dict[str, Any]] = {}
        lookup = {month: field for month, field, _color in cohort_fields}
        for row in rows:
            day = int(row["day_number"])
            item = grouped.setdefault(day, {"day_number": day, "lifecycle_day": f"第{day}日"})
            field = lookup.get(row.get("cohort_month"))
            if field:
                item[field] = row.get(value_field)
        return [grouped[key] for key in sorted(grouped)]

    snapshot["datasets"]["h5_retention_reference"] = pivot_by_day(snapshot["datasets"]["h5_retention_short_curve"], "retention_rate")
    snapshot["datasets"]["h5_ltv_reference"] = pivot_by_day(snapshot["datasets"]["h5_ltv_short_curve"], "ltv")
    snapshot["datasets"]["h5_payment_reference"] = pivot_by_day(snapshot["datasets"]["h5_payment_curve"], "payment_rate")

    lifecycle_key_visual = []
    previous_ltv14: float | None = None
    for row in lifecycle:
        item = dict(row)
        item["ltv14_mom_change"] = None if previous_ltv14 in {None, 0} else row["ltv_14"] / previous_ltv14 - 1
        lifecycle_key_visual.append(item)
        previous_ltv14 = row["ltv_14"]
    snapshot["datasets"]["h5_lifecycle_key_visual"] = lifecycle_key_visual

    payment_key_visual = []
    previous_d14_rate: float | None = None
    for row in h5_payment:
        item = dict(row)
        item["day14_pp_change"] = "—" if previous_d14_rate is None else f"{(row['day_14_payment_rate'] - previous_d14_rate) * 100:+.2f}pp"
        payment_key_visual.append(item)
        previous_d14_rate = row["day_14_payment_rate"]
    snapshot["datasets"]["h5_payment_key_visual"] = payment_key_visual

    manifest["charts"] = [
        {
            "id": "h5-retention-reference",
            "title": "严格 H5 自然新增：第2—14日留存",
            "subtitle": "6—8 月注册批次；仅纳入达到对应观察日的新增用户。",
            "type": "line",
            "dataset": "h5_retention_short_curve",
            "sourceId": "h5-strict-retention",
            "layout": "full",
            "encodings": {"x": {"field": "day_number", "type": "quantitative", "label": "第 N 个自然日"}, "y": {"field": "retention_rate", "type": "quantitative", "format": "percent", "label": "留存率"}, "color": {"field": "cohort_month", "type": "nominal", "label": "注册月"}},
            "valueFormat": "percent",
            "palette": {"kind": "sequential", "name": "reference-blue-scale"},
            "labels": {"values": "endpoints"},
            "legend": {"position": "bottom", "sort": "spec"},
            "settings": {"showPoints": "always"},
        },
        {
            "id": "h5-ltv-reference",
            "title": "H5 自然新增：第1—14日累计 LTV",
            "subtitle": "联运生命周期来源；6—8 月注册批次，按新增用户加权。",
            "type": "line",
            "dataset": "h5_ltv_short_curve",
            "sourceId": "h5-lifecycle-source",
            "layout": "full",
            "encodings": {"x": {"field": "day_number", "type": "quantitative", "label": "第 N 个自然日"}, "y": {"field": "ltv", "type": "quantitative", "format": "number", "label": "累计 LTV"}, "color": {"field": "cohort_month", "type": "nominal", "label": "注册月"}},
            "valueFormat": "number",
            "palette": {"kind": "sequential", "name": "reference-blue-scale"},
            "labels": {"values": "endpoints"},
            "legend": {"position": "bottom", "sort": "spec"},
            "settings": {"showPoints": "always"},
        },
        {
            "id": "h5-payment-reference",
            "title": "严格 H5 自然新增：累计成功支付率",
            "subtitle": "第1/7/14日；只计去重后的成功订单。",
            "type": "bar",
            "dataset": "h5_payment_curve",
            "sourceId": "h5-payment-cohort",
            "layout": "full",
            "encodings": {"x": {"field": "lifecycle_day", "type": "nominal", "label": "生命周期"}, "y": {"field": "payment_rate", "type": "quantitative", "format": "percent", "label": "累计付费率"}, "color": {"field": "cohort_month", "type": "nominal", "label": "注册月"}},
            "valueFormat": "percent",
            "palette": {"kind": "sequential", "name": "reference-blue-scale"},
            "labels": {"values": "all"},
            "legend": {"position": "bottom", "sort": "spec"},
            "settings": {"groupMode": "grouped", "showValues": True, "sort": "none"},
        },
    ]

    table_by_id = {table["id"]: table for table in manifest["tables"]}
    table_by_id["h5-lifecycle-key"].update({
        "dataset": "h5_lifecycle_key_visual",
        "columns": [
            {"field": "cohort_month", "label": "注册月", "type": "text"},
            {"field": "new_users", "label": "新增", "type": "number", "format": "number"},
            {"field": "day_2_retention", "label": "第2日留存", "type": "number", "format": "percent"},
            {"field": "day_7_retention", "label": "第7日留存", "type": "number", "format": "percent"},
            {"field": "day_14_retention", "label": "第14日留存", "type": "number", "format": "percent"},
            {"field": "ltv_14", "label": "LTV14", "type": "number", "format": "number"},
            {"field": "ltv14_mom_change", "label": "LTV14 环比", "type": "number", "format": "percent", "movement": True},
        ],
    })
    table_by_id["h5-payment-key"].update({
        "dataset": "h5_payment_key_visual",
        "columns": [
            {"field": "cohort_month", "label": "注册月", "type": "text"},
            {"field": "day_1_payment_rate", "label": "第1日付费率", "type": "number", "format": "percent"},
            {"field": "day_7_payment_rate", "label": "第7日付费率", "type": "number", "format": "percent"},
            {"field": "day_14_payment_rate", "label": "第14日付费率", "type": "number", "format": "percent"},
            {"field": "day14_pp_change", "label": "第14日变化", "type": "text", "movement": True},
            {"field": "day_14_arpu", "label": "第14日 ARPU", "type": "number", "format": "number"},
        ],
    })

    revised_blocks: list[dict[str, Any]] = []
    heading_bodies = {
        "priority": "## 01｜现在先做什么\n\n1. **首充漏斗：** 按 H5 包名和入口核查支付页到成功订单的到达、发起、失败/取消与金额档位。\n2. **全量 H5 拆解：** 按包名、入口与首渠道找到 7 月到 8 月第 2 日留存下降的具体组。\n3. **Phoenix 身份连续性：** 监控匿名 ID 变化，并与服务端账号/登录会话做聚合关联。",
        "retention-story": f"## 02｜H5 自然新增：第2—14日留存没有继续恶化\n\n8 月第 2 日留存较 7 月提升 {pp(august_retention['day_2_retention'], july_retention['day_2_retention'])}，第 14 日提升 {pp(august_retention['day_14_retention'], july_retention['day_14_retention'])}。**自然新增回访不是当前首要劣化点；应优先检查其他 H5 流量结构和支付转化。**",
        "ltv-payment-story": f"## 03｜价值从首日开始走弱，支付覆盖是关键断点\n\n8 月第 14 日 LTV 为 {compact(august_lifecycle['ltv_14'])}，低于 7 月的 {compact(july_lifecycle['ltv_14'])}；第 14 日付费率下降 {pp(august_payment['day_14_payment_rate'], july_payment['day_14_payment_rate'])}。**优先验证首充触发、支付完成与早期复充，不要用 ARPU 上升误判整体改善。**",
        "platform-story": "## 04｜APP 端也在走弱，Android 是更大的量级变量\n\n7 月到 8 月，Android 第 2 日留存从 22.44% 降至 19.44%，H5 从 5.14% 降至 4.65%，iOS 从 38.69% 降至 38.00%。Android 的 8 月新增批次规模约 518k，远高于 H5 与 iOS；**全产品问题不能只围绕 H5 解释。**",
        "stage-story": f"## 05｜H5 PAWAJEBETH5：首充与复充共同支撑\n\n8 月完整月度可关联首付画像中，有 {compact(payment_august_full['unique_first_payers'], 0)} 名首充、{compact(payment_august_full['unique_old_payers_at_month_start'], 0)} 名期初老付费与 {compact(payment_august_full['unique_repeat_payers_after_first_payment'], 0)} 名期内复充。**新增注册付费仍只适合按半月观察，不能把两个半月人数相加。**",
        "phenix-story": f"## 06｜Phoenix：先确认身份连续性，再判断真实流失\n\n成熟 Phoenix 首访批次的第 2 日任意事件回访为 {firebase_summary['day_2_any_event_users']}/{firebase_summary['day_2_mature_cohort_users']}，与会话开始回访几乎相同。现有事件没有成功付费信号；**这份数据适合定位前端回访与身份连续性，不适合给出支付或财务结论。**",
    }
    source_captions = {
        "retention-chart": ("retention-source", "来源：起源用户画像与日活聚合｜严格 H5 自然注册批次｜截至 9 月 4 日", "h5-strict-retention"),
        "ltv-chart": ("ltv-source", "来源：联运生命周期聚合｜H5 自然新增注册批次｜截至 9 月 4 日", "h5-lifecycle-source"),
        "payment-chart": ("payment-source", "来源：去重成功订单｜严格 H5 自然注册批次｜截至 9 月 4 日", "h5-payment-cohort"),
    }
    chart_ids = {"retention-chart": "h5-retention-reference", "ltv-chart": "h5-ltv-reference", "payment-chart": "h5-payment-reference"}
    for block in manifest["blocks"]:
        if block["id"] in heading_bodies:
            block = {**block, "body": heading_bodies[block["id"]]}
        if block["id"] in chart_ids:
            block = {**block, "chartId": chart_ids[block["id"]]}
        revised_blocks.append(block)
        caption = source_captions.get(block["id"])
        if caption:
            caption_id, body, source_id = caption
            revised_blocks.append({"id": caption_id, "type": "markdown", "body": body, "sourceId": source_id})
    manifest["blocks"] = revised_blocks
    finalize_topic(manifest, snapshot, lifecycle)
    artifact = {"surface": "report", "manifest": manifest, "snapshot": snapshot}
    ARTIFACT_PATH.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    chart_map = [
        {"section": "H5 留存", "chart": "h5-retention-reference", "type": "line", "fields": "第2—14日 × 注册月 × 留存率", "takeaway": "严格 H5 自然 cohort 的 7—8 月留存稳定。", "palette": "渐进蓝色月度对照"},
        {"section": "H5 LTV", "chart": "h5-ltv-reference", "type": "line", "fields": "第1—14日 × 注册月 × 累计LTV", "takeaway": "8 月价值曲线低于 7 月。", "palette": "渐进蓝色月度对照"},
        {"section": "支付覆盖", "chart": "h5-payment-reference", "type": "grouped bar", "fields": "第1/7/14日 × 注册月 × 成功支付率", "takeaway": "8 月支付覆盖低于 7 月。", "palette": "渐进蓝色月度对照"},
    ]
    CHART_MAP_PATH.write_text(json.dumps(chart_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    knowledge = f"""# Waje 全平台用户生命周期与付费价值分析｜H5 自然新增重点（截至 2026-09-04）

## 结论

- 严格 H5 自然新增 cohort 在 8 月的第 2 日和第 14 日留存均略高于 7 月；全量 H5 首平台 cohort 则下行，不能将全量问题直接归因到自然新增留存。
- 8 月严格 H5 自然 cohort 的第 14 日成功支付率为 {pct(august_payment['day_14_payment_rate'])}，低于 7 月的 {pct(july_payment['day_14_payment_rate'])}；第 14 日 ARPU 则由 {compact(july_payment['day_14_arpu'])} 升至 {compact(august_payment['day_14_arpu'])}。优先核查首充转化与支付成功漏斗。
- H5 生命周期来源的第 14 日 LTV：6 月 {compact(june_lifecycle['ltv_14'])}、7 月 {compact(july_lifecycle['ltv_14'])}、8 月 {compact(august_lifecycle['ltv_14'])}，8 月进一步下滑。
- Phoenix Firebase 标记首访 cohort 的第 2 日任意事件回访为 {pct(firebase_summary['day_2_any_event_users_rate'])}，会话开始回访为 {pct(firebase_summary['day_2_session_start_users_rate'])}；当前无成功付费事件，不能由 Firebase 计算成功付费率。

## 口径

- 第 N 日 = 第 N 个自然日；第 2 日是 cohort 次日。
- 严格 H5 自然 cohort：Web 首包且下载/首渠道/首子渠道均为 PAWAJEBETH5。
- 成功支付：`order_success`，按支付日 × 用户 × 订单号去重。
- 所有输出仅保留聚合数据；未成熟 cohort 显示 N/A。

## 工件

- 主报告：`output/html/Waje-全平台用户生命周期与付费价值分析-H5自然新增重点-2026-09-04.html`
- SQL、聚合结果与回执：`analysis/all_platform_cohort_value_2026_09_04/`
"""
    knowledge = "\n\n".join(block["body"] for block in manifest["blocks"] if block.get("type") == "markdown") + "\n"
    KNOWLEDGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_PATH.write_text(knowledge, encoding="utf-8")
    print(json.dumps({"artifact": str(ARTIFACT_PATH.relative_to(ROOT)), "chart_count": len(chart_map), "knowledge": str(KNOWLEDGE_PATH.relative_to(ROOT))}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
