#!/usr/bin/env python3
"""Build the canonical HTML design artifact for Waje's three-platform BI plan."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
LIVE_ROOT = ROOT.parent / "android_bq_api_client_2026_08_27"
VALIDATION_ROOT = ROOT.parent / "android_bq_api_validation_2026_08_27"
SQL_ROOT = ROOT / "sql"
FULL_RECEIPT = LIVE_ROOT / "full-validation-receipt.json"
ANALYTICS_RECEIPT = LIVE_ROOT / "supplemental-coverage-receipt.json"
CONTRACT = ROOT / "data-contract.json"
DASHBOARD = ROOT / "metabase-dashboard-contract.json"
OUT_ARTIFACT = ROOT / "artifact.json"
OUT_DATA = ROOT / "report-data.json"
OUT_CHART_MAP = ROOT / "chart-map.json"


LABELS = {
    "android_main": "Android 主包",
    "android_transsion_old": "Android 传音老包",
    "android_transsion_new": "Android 传音新包",
    "ios_existing": "iOS",
    "h5": "H5/PWA",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def receipt_rows(receipt: dict[str, Any], query_id: str) -> list[dict[str, Any]]:
    for item in receipt.get("queries", []):
        if item.get("id") == query_id:
            return list((item.get("execution") or {}).get("aggregate_rows") or [])
    return []


def make_source(
    source_id: str,
    label: str,
    path: str,
    description: str,
    *,
    sql_file: Path | None = None,
    tables: list[str] | None = None,
    filters: list[str] | None = None,
    definitions: list[str] | None = None,
) -> dict[str, Any]:
    query: dict[str, Any] = {
        "engine": "BigQuery" if sql_file else "Local JSON contract",
        "language": "SQL" if sql_file else "JSON",
        "description": description,
    }
    if sql_file:
        query.update(
            {
                "sql": sql_file.read_text(encoding="utf-8").strip(),
                "tables_used": tables or [],
                "filters": filters or [],
                "metric_definitions": definitions or [],
                "execution": "database-side aggregation; report downloads aggregate rows only",
            }
        )
    return {"id": source_id, "label": label, "path": path, "query": query}


def sqlite_values_sql(columns: list[str], rows: list[list[Any]], table_name: str) -> str:
    """Create an auditable local snapshot query for non-business design tables."""
    def literal(value: Any) -> str:
        if value is None:
            return "NULL"
        if isinstance(value, bool):
            return "1" if value else "0"
        if isinstance(value, (int, float)):
            return str(value)
        return "'" + str(value).replace("'", "''") + "'"

    values = ", ".join("(" + ", ".join(literal(value) for value in row) + ")" for row in rows)
    names = ", ".join(columns)
    return f"WITH {table_name}({names}) AS (VALUES {values}) SELECT {names} FROM {table_name};"


def build_report_data() -> dict[str, Any]:
    full = read_json(FULL_RECEIPT)
    analytics = read_json(ANALYTICS_RECEIPT)
    contract = read_json(CONTRACT)
    dashboard = read_json(DASHBOARD)

    coverage = receipt_rows(full, "01_performance_daily_coverage")
    metrics = receipt_rows(full, "02_performance_metric_aggregates")
    devices = receipt_rows(full, "03_device_os_mix")
    network = receipt_rows(full, "04_network_quality")
    sessions = receipt_rows(full, "05_sessions_reconciliation")
    formulas = receipt_rows(full, "07_formula_reconciliation")
    analytics_coverage = list((analytics.get("execution") or {}).get("aggregate_rows") or [])

    latest_date = max((row.get("metric_date_lagos") for row in metrics), default=None)
    latest_metrics = [row for row in metrics if row.get("metric_date_lagos") == latest_date]
    total_network_responses = sum(int(row.get("network_response_count") or 0) for row in metrics)
    total_network_success = sum(int(row.get("network_success_count") or 0) for row in metrics)

    package_totals = []
    for endpoint in ("android_main", "android_transsion_old", "android_transsion_new"):
        cov = [row for row in coverage if row.get("endpoint") == endpoint]
        met = [row for row in metrics if row.get("endpoint") == endpoint]
        latest = next((row for row in latest_metrics if row.get("endpoint") == endpoint), None)
        responses = sum(int(row.get("network_response_count") or 0) for row in met)
        successes = sum(int(row.get("network_success_count") or 0) for row in met)
        package_totals.append(
            {
                "endpoint": endpoint,
                "label": LABELS[endpoint],
                "app_package": cov[0].get("app_package") if cov else None,
                "performance_record_count": sum(int(row.get("performance_record_count") or 0) for row in cov),
                "covered_days": len({row.get("metric_date_lagos") for row in cov}),
                "weighted_network_success_rate": round(successes / responses, 6) if responses else None,
                "latest_duration_p90_ms": round(float(latest["duration_p90_ms"]), 3) if latest and latest.get("duration_p90_ms") is not None else None,
                "latest_network_p90_ms": round(float(latest["network_p90_ms"]), 3) if latest and latest.get("network_p90_ms") is not None else None,
                "latest_slow_frame_ratio": round(float(latest["slow_frame_ratio_trace_mean"]), 6) if latest and latest.get("slow_frame_ratio_trace_mean") is not None else None,
                "latest_frozen_frame_ratio": round(float(latest["frozen_frame_ratio_trace_mean"]), 6) if latest and latest.get("frozen_frame_ratio_trace_mean") is not None else None,
            }
        )

    # Keep the table report-friendly: one row per date and package, all already aggregated.
    daily_coverage = [
        {
            "date": row.get("metric_date_lagos"),
            "endpoint": row.get("endpoint"),
            "label": LABELS.get(row.get("endpoint"), row.get("endpoint")),
            "performance_records": int(row.get("performance_record_count") or 0),
            "duration_traces": int(row.get("duration_trace_count") or 0),
            "screen_traces": int(row.get("screen_trace_count") or 0),
            "network_requests": int(row.get("network_request_count") or 0),
            "versions": int(row.get("app_version_count") or 0),
            "coverage_status": row.get("coverage_status"),
        }
        for row in sorted(coverage, key=lambda item: (item.get("metric_date_lagos"), item.get("endpoint")))
    ]

    latest_network = [
        {
            "endpoint": row.get("endpoint"),
            "label": LABELS.get(row.get("endpoint"), row.get("endpoint")),
            "network_p90_ms": round(float(row["network_p90_ms"]), 3) if row.get("network_p90_ms") is not None else None,
            "network_sample_count": int(row.get("network_sample_count") or 0),
        }
        for row in sorted(latest_metrics, key=lambda item: item.get("endpoint"))
        if row.get("network_p90_ms") is not None
    ]

    latest_duration = [
        {
            "endpoint": row.get("endpoint"),
            "label": LABELS.get(row.get("endpoint"), row.get("endpoint")),
            "duration_p90_ms": round(float(row["duration_p90_ms"]), 3) if row.get("duration_p90_ms") is not None else None,
            "duration_sample_count": int(row.get("duration_sample_count") or 0),
        }
        for row in sorted(latest_metrics, key=lambda item: item.get("endpoint"))
        if row.get("duration_p90_ms") is not None
    ]

    # Aggregate the already-filtered top device groups; no raw events are downloaded.
    device_agg: dict[tuple[str, str, str], int] = {}
    for row in devices:
        key = (str(row.get("endpoint")), str(row.get("device_name")), str(row.get("os_version")))
        device_agg[key] = device_agg.get(key, 0) + int(row.get("performance_record_count") or 0)
    device_top = []
    for endpoint in ("android_main", "android_transsion_old", "android_transsion_new"):
        top = sorted(
            ((device, os_version, count) for (ep, device, os_version), count in device_agg.items() if ep == endpoint),
            key=lambda item: -item[2],
        )[:8]
        device_top.extend(
            {"endpoint": endpoint, "label": LABELS[endpoint], "rank": index, "device_name": device, "display_label": f"{LABELS[endpoint]} · {device}", "os_version": os_version, "performance_records": count}
            for index, (device, os_version, count) in enumerate(top, 1)
        )

    formula_quality = []
    session_quality = []
    for endpoint in ("android_main", "android_transsion_old", "android_transsion_new"):
        f_rows = [row for row in formulas if row.get("endpoint") == endpoint]
        s_rows = [row for row in sessions if row.get("endpoint") == endpoint]
        formula_quality.append(
            {
                "endpoint": endpoint,
                "label": LABELS[endpoint],
                "checked_days": len(f_rows),
                "additive_mismatch_days": sum(int(row.get("additive_reconciliation_delta") or 0) != 0 for row in f_rows),
                "negative_duration_values": sum(int(row.get("negative_duration_count") or 0) for row in f_rows),
                "negative_network_latency_values": sum(int(row.get("negative_network_latency_count") or 0) for row in f_rows),
                "invalid_frame_ratio_values": sum(int(row.get("invalid_frame_ratio_count") or 0) for row in f_rows),
                "status": "passed" if all(row.get("quality_status") == "basic_formula_checks_pass" for row in f_rows) else "warning",
            }
        )
        session_quality.append(
            {
                "endpoint": endpoint,
                "label": LABELS[endpoint],
                "checked_days": len(s_rows),
                "daily_distinct_sessions_sum": sum(int(row.get("distinct_session_count") or 0) for row in s_rows),
                "performance_flag_share_min": min((row.get("performance_flag_share") or 0) for row in s_rows) if s_rows else None,
                "performance_flag_share_max": max((row.get("performance_flag_share") or 0) for row in s_rows) if s_rows else None,
                "crashlytics_flag_share_min": min((row.get("crashlytics_flag_share") or 0) for row in s_rows) if s_rows else None,
                "crashlytics_flag_share_max": max((row.get("crashlytics_flag_share") or 0) for row in s_rows) if s_rows else None,
                "status": "warning_performance_flag_conflict" if any(row.get("quality_status") == "quality_warning_check_performance_table" for row in s_rows) else "observed",
            }
        )

    source_coverage = [
        {"source": "Android Performance", "covered_days": 7, "status": "provisional"},
        {"source": "Android Analytics", "covered_days": len({row.get("metric_date_lagos") for row in analytics_coverage}), "status": "immature"},
        {"source": "iOS Analytics", "covered_days": 5, "status": "immature"},
        {"source": "iOS Performance", "covered_days": 6, "status": "immature"},
        {"source": "H5 Analytics", "covered_days": 8, "status": "behavior_only"},
    ]
    quality_state_counts = [
        {"status": state, "source_count": sum(item["status"] == state for item in source_coverage)}
        for state in ("provisional", "immature", "behavior_only")
    ]
    latest_package_metrics = [
        {
            "endpoint": row.get("endpoint"),
            "label": LABELS.get(row.get("endpoint"), row.get("endpoint")),
            "duration_p90_ms": row.get("duration_p90_ms"),
            "network_p90_ms": row.get("network_p90_ms"),
            "network_success_rate": row.get("network_success_rate"),
            "slow_frame_ratio": row.get("slow_frame_ratio_trace_mean"),
            "frozen_frame_ratio": row.get("frozen_frame_ratio_trace_mean"),
            "duration_sample_count": row.get("duration_sample_count"),
            "network_sample_count": row.get("network_sample_count"),
        }
        for row in sorted(latest_metrics, key=lambda item: item.get("endpoint"))
    ]
    daily_network_success = [
        {
            "date": row.get("metric_date_lagos"),
            "label": LABELS.get(row.get("endpoint"), row.get("endpoint")),
            "network_success_rate": row.get("network_success_rate"),
            "network_sample_count": row.get("network_sample_count"),
        }
        for row in sorted(metrics, key=lambda item: (item.get("metric_date_lagos"), item.get("endpoint")))
    ]
    metric_catalog = []
    for metric in contract["metrics"]:
        metric_catalog.append(
            {
                "id": metric["id"],
                "label": metric["label"],
                "definition": metric["definition"],
                "grain": metric["grain"],
                "unit": metric["unit"],
                "source": metric["source"],
                "denominator": metric.get("denominator", "not applicable"),
                "eligibility": metric.get("eligibility", "not applicable"),
                "status": metric["status"],
            }
        )

    page_rows = []
    for page in dashboard["pages"]:
        page_rows.append(
            {
                "page_id": page["id"],
                "page_name": page["name"],
                "role": page["role"],
                "questions": "；".join(page["questions"]),
                "hero_cards": "、".join(page["hero_cards"]),
                "charts": "、".join(page["charts"]),
                "tables": "、".join(page["tables"]),
            }
        )

    sql_files = []
    for path in sorted(SQL_ROOT.glob("*.sql")):
        sql_files.append(
            {
                "file": path.name,
                "execution_mode": "admin_write" if path.name in {"00_create_mart_dataset.sql", "10_metabase_readonly_views.sql"} else "scheduled_or_readonly",
                "status": "design_ready_not_executed",
            }
        )

    return {
        "scope": {
            "project_id": "wajenigeria",
            "location": "europe-west4",
            "timezone": "Africa/Lagos",
            "window": "2026-08-20 through 2026-08-26",
            "latest_complete_day": latest_date,
        },
        "summary": {
            "performance_records": sum(int(row.get("performance_record_count") or 0) for row in coverage),
            "coverage_pairs": len(coverage),
            "expected_coverage_pairs": 21,
            "weighted_network_success_rate": round(total_network_success / total_network_responses, 6) if total_network_responses else None,
            "duration_p90_eligible_pairs": sum(row.get("duration_p90_ms") is not None for row in metrics),
            "network_p90_eligible_pairs": sum(row.get("network_p90_ms") is not None for row in metrics),
            "analytics_covered_days": len({row.get("metric_date_lagos") for row in analytics_coverage}),
            "dry_run_gib": full.get("dry_run", {}).get("total_bytes_processed_gib"),
        },
        "package_totals": package_totals,
        "latest_network": latest_network,
        "latest_duration": latest_duration,
        "daily_coverage": daily_coverage,
        "device_top": device_top,
        "device_top_global": sorted(device_top, key=lambda row: -row["performance_records"])[:8],
        "latest_package_metrics": latest_package_metrics,
        "daily_network_success": daily_network_success,
        "quality_state_counts": quality_state_counts,
        "formula_quality": formula_quality,
        "session_quality": session_quality,
        "analytics_coverage": analytics_coverage,
        "source_coverage": source_coverage,
        "metric_catalog": metric_catalog,
        "dashboard_pages": page_rows,
        "report_catalog": [
            {
                "id": report["id"],
                "name": report["name"],
                "window": report["window"],
                "sections": "、".join(report["sections"]),
            }
            for report in dashboard["reports"]
        ],
        "sql_catalog": sql_files,
    }


def build_artifact(data: dict[str, Any]) -> dict[str, Any]:
    source_perf = make_source(
        "performance_coverage",
        "BigQuery Android Performance 每日覆盖",
        "analysis/android_bq_api_validation_2026_08_27/sql/01_performance_daily_coverage.sql",
        "按日期和三个 Android 包体汇总 Performance 记录、事件类型和版本覆盖。",
        sql_file=VALIDATION_ROOT / "01_performance_daily_coverage.sql" if (VALIDATION_ROOT / "01_performance_daily_coverage.sql").exists() else VALIDATION_ROOT / "sql/01_performance_daily_coverage.sql",
        tables=["wajenigeria.waje_ng_firebase_android_performance.<package_table>"],
        filters=["2026-08-20 至 2026-08-26", "Africa/Lagos"],
        definitions=["记录数是 Performance 事件记录数，不是用户数。"],
    )
    source_metrics = make_source(
        "performance_metrics",
        "BigQuery Android Performance 指标聚合",
        "analysis/android_bq_api_validation_2026_08_27/sql/02_performance_metric_aggregates.sql",
        "在线计算 DURATION_TRACE P90、NETWORK_REQUEST P90、网络成功率和帧比例。",
        sql_file=VALIDATION_ROOT / "sql/02_performance_metric_aggregates.sql",
        tables=["wajenigeria.waje_ng_firebase_android_performance.<package_table>"],
        filters=["2026-08-20 至 2026-08-26", "P90 有效样本至少 500"],
        definitions=["不平均日级 P90；样本不足返回 NULL。", "网络成功率 = 200–399 / 有响应码请求。"],
    )
    source_devices = make_source(
        "device_mix",
        "BigQuery Android 设备/系统聚合",
        "analysis/android_bq_api_validation_2026_08_27/sql/03_device_os_mix.sql",
        "按设备型号和系统版本聚合高样本组合。",
        sql_file=VALIDATION_ROOT / "sql/03_device_os_mix.sql",
        tables=["wajenigeria.waje_ng_firebase_android_performance.<package_table>"],
        filters=["聚合组至少 10 条记录", "每包每日最多 50 组"],
        definitions=["设备名称为聚合维度，不代表独立设备数。"],
    )
    source_network = make_source(
        "network_quality",
        "BigQuery Android 网络质量聚合",
        "analysis/android_bq_api_validation_2026_08_27/sql/04_network_quality.sql",
        "按版本汇总网络响应码、P90 和成功率。",
        sql_file=VALIDATION_ROOT / "sql/04_network_quality.sql",
        tables=["wajenigeria.waje_ng_firebase_android_performance.<package_table>"],
        filters=["只统计 NETWORK_REQUEST", "P90 样本至少 500"],
        definitions=["不返回 URL、请求名称、请求正文或响应正文。"],
    )
    source_sessions = make_source(
        "sessions_quality",
        "BigQuery Android Sessions 质量聚合",
        "analysis/android_bq_api_validation_2026_08_27/sql/05_sessions_reconciliation.sql",
        "按日和包体聚合日唯一会话及采集标记。",
        sql_file=VALIDATION_ROOT / "sql/05_sessions_reconciliation.sql",
        tables=["wajenigeria.waje_ng_firebase_android_sessions.<package_table>"],
        filters=["2026-08-20 至 2026-08-26"],
        definitions=["session_id 只在 COUNT(DISTINCT) 内使用，不返回明细。"],
    )
    source_analytics = make_source(
        "analytics_coverage",
        "BigQuery Android Analytics 包体覆盖",
        "analysis/android_bq_api_client_2026_08_27/sql/03_android_analytics_coverage.sql",
        "单独按日期×包体聚合 Analytics 覆盖，避免长尾结果被 LIMIT 截断。",
        sql_file=LIVE_ROOT / "sql/03_android_analytics_coverage.sql",
        tables=["wajenigeria.waje_ng_firebase_android.events_*"],
        filters=["2026-08-20 至 2026-08-26", "platform = ANDROID"],
        definitions=["事件数为事件记录数，不是用户数。"],
    )
    source_formula = make_source(
        "formula_quality",
        "BigQuery Android Performance 公式和值域检查",
        "analysis/android_bq_api_validation_2026_08_27/sql/07_formula_reconciliation.sql",
        "检查事件类型分项可加总性、负时长、负网络延迟和非法帧比例。",
        sql_file=VALIDATION_ROOT / "sql/07_formula_reconciliation.sql",
        tables=["wajenigeria.waje_ng_firebase_android_performance.<package_table>"],
        filters=["2026-08-20 至 2026-08-26"],
        definitions=["只输出质量计数，不删除或修正源数据。"],
    )
    metric_rows = [[
        row["id"], row["label"], row["definition"], row["grain"], row["unit"],
        row["source"], row["denominator"], row["eligibility"], row["status"]
    ] for row in data["metric_catalog"]]
    metric_catalog_sql = sqlite_values_sql(
        ["id", "label", "definition", "grain", "unit", "source", "denominator", "eligibility", "status"],
        metric_rows,
        "metric_catalog",
    )
    source_metric_catalog = {
        "id": "metric_catalog_source",
        "label": "Waje 三端指标合同快照",
        "path": "analysis/metabase_waje_three_platform_dashboard_design_2026_08_27/data-contract.json",
        "query": {"engine": "SQLite (contract snapshot)", "language": "SQL", "description": "从指标合同快照生成可读指标目录。", "sql": metric_catalog_sql, "tables_used": ["data-contract.json"], "filters": ["指标合同快照"], "metric_definitions": ["仅为设计元数据，不读取业务数据。"]},
    }
    dashboard_rows = [[row["page_id"], row["page_name"], row["role"], row["questions"], row["hero_cards"], row["charts"], row["tables"]] for row in data["dashboard_pages"]]
    dashboard_catalog_sql = sqlite_values_sql(["page_id", "page_name", "role", "questions", "hero_cards", "charts", "tables"], dashboard_rows, "dashboard_pages")
    source_dashboard = {
        "id": "dashboard_contract_source",
        "label": "Metabase 四页 Dashboard 合同快照",
        "path": "analysis/metabase_waje_three_platform_dashboard_design_2026_08_27/metabase-dashboard-contract.json",
        "query": {"engine": "SQLite (contract snapshot)", "language": "SQL", "description": "从 Dashboard 合同生成四页页面目录。", "sql": dashboard_catalog_sql, "tables_used": ["metabase-dashboard-contract.json"], "filters": ["四页 Dashboard 设计"], "metric_definitions": ["仅为设计元数据，不读取业务数据。"]},
    }
    sql_rows = [[row["file"], row["execution_mode"], row["status"]] for row in data["sql_catalog"]]
    sql_catalog_sql = sqlite_values_sql(["file", "execution_mode", "status"], sql_rows, "sql_catalog")
    source_sql_catalog = {
        "id": "sql_catalog_source",
        "label": "BigQuery 与 Metabase SQL 目录快照",
        "path": "analysis/metabase_waje_three_platform_dashboard_design_2026_08_27/sql/",
        "query": {"engine": "SQLite (design file catalog)", "language": "SQL", "description": "从设计目录生成 SQL 文件清单。", "sql": sql_catalog_sql, "tables_used": ["sql/ directory"], "filters": ["管理员脚本与只读查询脚本"], "metric_definitions": ["仅为脚本目录，不执行 SQL。"]},
    }
    report_rows = [[row["id"], row["name"], row["window"], "、".join(row["sections"])] for row in read_json(DASHBOARD)["reports"]]
    report_catalog_sql = sqlite_values_sql(["id", "name", "window", "sections"], report_rows, "report_catalog")
    source_report_catalog = {
        "id": "report_catalog_source",
        "label": "日报、周报和专项报告合同快照",
        "path": "analysis/metabase_waje_three_platform_dashboard_design_2026_08_27/metabase-dashboard-contract.json",
        "query": {"engine": "SQLite (contract snapshot)", "language": "SQL", "description": "从报表合同生成日报、周报和版本专项报告目录。", "sql": report_catalog_sql, "tables_used": ["metabase-dashboard-contract.json"], "filters": ["报表合同快照"], "metric_definitions": ["仅为设计元数据，不读取业务数据。"]},
    }
    source_contract = {
        "id": "design_contract",
        "label": "Waje 三端数据与指标合同",
        "path": "analysis/metabase_waje_three_platform_dashboard_design_2026_08_27/data-contract.json",
        "query": {"engine": "Local JSON contract", "language": "JSON", "description": "定义源表、字段、指标、状态、告警和隐私边界。"},
    }
    source_baseline = {
        "id": "current_baseline",
        "label": "BigQuery API 安卓聚合实测基线",
        "path": "analysis/android_bq_api_client_2026_08_27/report-data.json",
        "query": {
            "engine": "SQLite (report snapshot aggregation)",
            "language": "SQL",
            "description": "由已执行的聚合 SQL 回执二次汇总而成；不包含原始事件。",
            "sql": "WITH source_coverage(source, covered_days, status) AS (VALUES ('Android Performance', 7, 'provisional'), ('Android Analytics', 1, 'immature'), ('iOS Analytics', 5, 'immature'), ('iOS Performance', 6, 'immature'), ('H5 Analytics', 8, 'behavior_only')) SELECT source, covered_days, status FROM source_coverage;",
            "tables_used": ["analysis/android_bq_api_client_2026_08_27/report-data.json"],
            "filters": ["当前实测基线", "仅汇总覆盖天数"],
            "metric_definitions": ["覆盖天数是来源快照中的已观察数据日数，不是业务活跃天数。"],
        },
    }
    sources = [source_perf, source_metrics, source_devices, source_network, source_sessions, source_analytics, source_formula, source_contract, source_dashboard, source_metric_catalog, source_sql_catalog, source_report_catalog, source_baseline]
    summary = data["summary"]

    def pct(value: float | None) -> str:
        return "N/A" if value is None else f"{value * 100:.2f}%"

    manifest = {
        "version": 1,
        "surface": "report",
        "title": "Waje 三端设备与性能看板、报表及 BigQuery 聚合设计",
        "description": "以 Metabase 为目标展示层、以 BigQuery 在线聚合为计算层的三端设备与性能数据体系设计文档。",
        "generatedAt": dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(timespec="seconds"),
        "sources": sources,
        "accessIssues": [
            "当前 HTML 是设计与配置草案，不创建或修改远端 Metabase 对象。",
            "Android Performance 当前已有 7 日基线；Android Analytics 仅有 1 个有效日，iOS/H5 按现有资料保持 provisional/数据缺口状态。",
            "服务端核心漏斗授权聚合视图尚未登记，相关卡片必须显示 blocked。",
        ],
        "statusDefinitions": {
            "certified": "定义、来源、完整性、新鲜度和勾稽均通过。",
            "provisional": "可做聚合观察，但仍有来源或语义限制。",
            "immature": "数据日数或样本不足，暂不用于趋势结论。",
            "delayed": "数据截止时间落后当前检查时间超过 45 分钟。",
            "data_gap": "目标信号未入库，不解释为 0。",
            "blocked": "权限、对象白名单或源事实不足。",
        },
        "cards": [
            {"id": "performance_records", "dataset": "summary", "sourceId": "performance_coverage", "metrics": [{"label": "7日 Performance 记录", "field": "performance_records", "format": "number"}]},
            {"id": "coverage_pairs", "dataset": "summary", "sourceId": "performance_coverage", "metrics": [{"label": "日期×包体覆盖", "field": "coverage_pairs_label", "format": "text"}]},
            {"id": "network_success", "dataset": "summary", "sourceId": "performance_metrics", "metrics": [{"label": "7日加权网络成功率", "field": "weighted_network_success_rate", "format": "percent"}]},
            {"id": "analytics_days", "dataset": "summary", "sourceId": "analytics_coverage", "metrics": [{"label": "Android Analytics 有效日", "field": "analytics_covered_days", "format": "number"}]},
        ],
        "charts": [
            {"id": "source_coverage_days", "title": "三端数据覆盖天数", "subtitle": "当前设计基线；Analytics 与 iOS/H5 成熟度不足时不进入跨端趋势。", "dataset": "source_coverage", "sourceId": "current_baseline", "type": "bar", "layout": "full", "encodings": {"x": {"field": "source", "type": "nominal", "label": "数据源"}, "y": {"field": "covered_days", "type": "quantitative", "format": "number", "label": "覆盖天数"}}, "palette": {"kind": "categorical", "name": "blue"}, "settings": {"sort": "descending", "showValues": True}},
            {"id": "android_package_volume", "title": "Android 7日 Performance 记录量", "subtitle": "按包体汇总事件记录数；不代表用户数。", "dataset": "package_totals", "sourceId": "performance_coverage", "type": "bar", "layout": "full", "encodings": {"x": {"field": "label", "type": "nominal", "label": "包体"}, "y": {"field": "performance_record_count", "type": "quantitative", "format": "number", "label": "记录数"}}, "palette": {"kind": "categorical", "name": "blue"}, "settings": {"sort": "descending", "showValues": True}},
            {"id": "daily_performance_trend", "title": "Android Performance 每日记录量", "subtitle": "2026年8月20日至26日；按日期和包体的云端聚合结果。", "dataset": "daily_coverage", "sourceId": "performance_coverage", "type": "line", "layout": "full", "intent": "trend", "question": "三个 Android 包体的 Performance 记录量是否出现断流或明显变化？", "rationale": "7日×3包体的连续日粒度可以同时检查覆盖完整性和包体量级变化。", "comparisonContext": {"grain": "日期 × 包体", "unit": "Performance 事件记录数"}, "encodings": {"x": {"field": "date", "type": "temporal", "label": "日期"}, "y": {"field": "performance_records", "type": "quantitative", "format": "number", "label": "记录数"}, "color": {"field": "label", "type": "nominal", "label": "包体"}}, "palette": {"kind": "categorical", "name": "blue"}, "settings": {"showValues": False}},
            {"id": "latest_duration_p90", "title": "最新完整日 DURATION_TRACE P90", "subtitle": "2026年8月26日；单位毫秒，不能直接等同 App 启动耗时。", "dataset": "latest_duration", "sourceId": "performance_metrics", "type": "bar", "layout": "full", "encodings": {"x": {"field": "label", "type": "nominal", "label": "包体"}, "y": {"field": "duration_p90_ms", "type": "quantitative", "format": "number", "label": "P90（毫秒）"}}, "palette": {"kind": "categorical", "name": "blue"}, "settings": {"sort": "descending", "showValues": True}},
            {"id": "latest_network_p90", "title": "最新完整日 NETWORK_REQUEST P90", "subtitle": "2026年8月26日；单位毫秒，按有效响应完成耗时计算。", "dataset": "latest_network", "sourceId": "performance_metrics", "type": "bar", "layout": "full", "encodings": {"x": {"field": "label", "type": "nominal", "label": "包体"}, "y": {"field": "network_p90_ms", "type": "quantitative", "format": "number", "label": "P90（毫秒）"}}, "palette": {"kind": "categorical", "name": "blue"}, "settings": {"sort": "descending", "showValues": True}},
            {"id": "daily_network_success", "title": "网络成功率每日变化", "subtitle": "2026年8月20日至26日；HTTP 200–399 ÷ 有响应码请求数。", "dataset": "daily_network_success", "sourceId": "performance_metrics", "type": "line", "layout": "full", "intent": "trend", "question": "网络层成功率是否存在日期或包体异常波动？", "rationale": "按日、按包体保留成功率和网络样本数，可避免把一条总体比例误读为所有包体表现。", "comparisonContext": {"grain": "日期 × 包体", "denominator": "有响应码请求数", "unit": "比例"}, "encodings": {"x": {"field": "date", "type": "temporal", "label": "日期"}, "y": {"field": "network_success_rate", "type": "quantitative", "format": "percent", "label": "成功率"}, "color": {"field": "label", "type": "nominal", "label": "包体"}}, "palette": {"kind": "categorical", "name": "blue"}, "settings": {"showValues": False}},
            {"id": "network_success_by_package", "title": "7日加权网络成功率", "subtitle": "按包体加权计算；不等同业务登录或充值成功率。", "dataset": "package_totals", "sourceId": "performance_metrics", "type": "bar", "layout": "full", "encodings": {"x": {"field": "label", "type": "nominal", "label": "包体"}, "y": {"field": "weighted_network_success_rate", "type": "quantitative", "format": "percent", "label": "成功率"}}, "palette": {"kind": "categorical", "name": "blue"}, "settings": {"sort": "descending", "showValues": True}},
            {"id": "latest_slow_frame", "title": "最新完整日慢帧比例", "subtitle": "2026年8月26日；SCREEN_TRACE trace 加权均值，不是用户比例。", "dataset": "latest_package_metrics", "sourceId": "performance_metrics", "type": "bar", "layout": "full", "encodings": {"x": {"field": "label", "type": "nominal", "label": "包体"}, "y": {"field": "slow_frame_ratio", "type": "quantitative", "format": "percent", "label": "慢帧比例"}}, "palette": {"kind": "categorical", "name": "blue"}, "settings": {"sort": "descending", "showValues": True}},
            {"id": "latest_frozen_frame", "title": "最新完整日冻结帧比例", "subtitle": "2026年8月26日；SCREEN_TRACE trace 加权均值，不是用户比例。", "dataset": "latest_package_metrics", "sourceId": "performance_metrics", "type": "bar", "layout": "full", "encodings": {"x": {"field": "label", "type": "nominal", "label": "包体"}, "y": {"field": "frozen_frame_ratio", "type": "quantitative", "format": "percent", "label": "冻结帧比例"}}, "palette": {"kind": "categorical", "name": "blue"}, "settings": {"sort": "descending", "showValues": True}},
            {"id": "device_top_rank", "title": "高样本设备组合排行", "subtitle": "已在 BigQuery 聚合后保留 Top 8；用于兼容性优先级，不代表独立设备数。", "dataset": "device_top_global", "sourceId": "device_mix", "type": "bar", "layout": "full", "encodings": {"x": {"field": "display_label", "type": "nominal", "label": "包体·设备型号"}, "y": {"field": "performance_records", "type": "quantitative", "format": "number", "label": "记录数"}}, "palette": {"kind": "categorical", "name": "blue"}, "settings": {"sort": "descending", "showValues": True}},
            {"id": "analytics_package_volume", "title": "Android Analytics 单日包体事件量", "subtitle": "2026年8月24日；事件记录数，不代表用户数或会话数。", "dataset": "analytics_coverage", "sourceId": "analytics_coverage", "type": "bar", "layout": "full", "encodings": {"x": {"field": "app_package", "type": "nominal", "label": "包体"}, "y": {"field": "event_count", "type": "quantitative", "format": "number", "label": "事件数"}}, "palette": {"kind": "categorical", "name": "blue"}, "settings": {"sort": "descending", "showValues": True}},
            {"id": "quality_state_mix", "title": "当前数据质量状态构成", "subtitle": "按来源状态计数；状态不是业务数值，也不把缺口转成 0。", "dataset": "quality_state_counts", "sourceId": "current_baseline", "type": "bar", "layout": "full", "encodings": {"x": {"field": "status", "type": "nominal", "label": "质量状态"}, "y": {"field": "source_count", "type": "quantitative", "format": "number", "label": "来源数"}}, "palette": {"kind": "categorical", "name": "blue"}, "settings": {"sort": "descending", "showValues": True}},
        ],
        "tables": [
            {"id": "dashboard_pages", "title": "Metabase Dashboard 页面合同", "subtitle": "四页由总览到诊断再到设备/H5 缺口；每页均有目标问题、卡片、图表和明细表。", "dataset": "dashboard_pages", "sourceId": "dashboard_contract_source", "density": "spacious", "layout": "full", "columns": [{"field": "page_name", "label": "页面", "type": "text"}, {"field": "role", "label": "定位", "type": "text"}, {"field": "questions", "label": "核心问题", "type": "text"}, {"field": "hero_cards", "label": "首屏 KPI", "type": "text"}, {"field": "charts", "label": "图表", "type": "text"}, {"field": "tables", "label": "明细表", "type": "text"}], "defaultSort": {"field": "page_name", "direction": "asc"}},
            {"id": "metric_catalog", "title": "核心指标字典", "subtitle": "定义、粒度、单位、分母、资格门槛和状态必须与 BigQuery 聚合层一致。", "dataset": "metric_catalog", "sourceId": "metric_catalog_source", "density": "spacious", "layout": "full", "columns": [{"field": "label", "label": "指标", "type": "text"}, {"field": "definition", "label": "算法/定义", "type": "text"}, {"field": "grain", "label": "粒度", "type": "text"}, {"field": "unit", "label": "单位", "type": "text"}, {"field": "denominator", "label": "分母", "type": "text"}, {"field": "eligibility", "label": "门槛", "type": "text"}, {"field": "status", "label": "状态", "type": "text"}], "defaultSort": {"field": "label", "direction": "asc"}},
            {"id": "daily_coverage", "title": "Android Performance 每日覆盖", "subtitle": "21 个日期×包体组合；用于确认日期和包体没有静默缺失。", "dataset": "daily_coverage", "sourceId": "performance_coverage", "density": "spacious", "layout": "full", "columns": [{"field": "date", "label": "日期", "type": "date"}, {"field": "label", "label": "包体", "type": "text"}, {"field": "performance_records", "label": "记录数", "type": "number"}, {"field": "duration_traces", "label": "DURATION_TRACE", "type": "number"}, {"field": "screen_traces", "label": "SCREEN_TRACE", "type": "number"}, {"field": "network_requests", "label": "NETWORK_REQUEST", "type": "number"}, {"field": "versions", "label": "版本数", "type": "number"}], "defaultSort": {"field": "date", "direction": "asc"}},
            {"id": "latest_package_metrics", "title": "最新完整日包体指标", "subtitle": "2026年8月26日；P90、网络成功率和帧比例集中展示，保留样本数。", "dataset": "latest_package_metrics", "sourceId": "performance_metrics", "density": "spacious", "layout": "full", "columns": [{"field": "label", "label": "包体", "type": "text"}, {"field": "duration_p90_ms", "label": "DURATION_TRACE P90（ms）", "type": "number"}, {"field": "network_p90_ms", "label": "NETWORK P90（ms）", "type": "number"}, {"field": "network_success_rate", "label": "网络成功率", "type": "percent"}, {"field": "slow_frame_ratio", "label": "慢帧比例", "type": "percent"}, {"field": "frozen_frame_ratio", "label": "冻结帧比例", "type": "percent"}, {"field": "duration_sample_count", "label": "时长样本", "type": "number"}, {"field": "network_sample_count", "label": "网络样本", "type": "number"}], "defaultSort": {"field": "label", "direction": "asc"}},
            {"id": "device_top", "title": "高样本设备与系统组合", "subtitle": "每个 Android 包体保留已聚合结果中记录量最高的 8 个组合；不是完整设备排名。", "dataset": "device_top", "sourceId": "device_mix", "density": "spacious", "layout": "full", "columns": [{"field": "label", "label": "包体", "type": "text"}, {"field": "rank", "label": "排名", "type": "number"}, {"field": "device_name", "label": "设备型号", "type": "text"}, {"field": "os_version", "label": "系统版本", "type": "text"}, {"field": "performance_records", "label": "记录数", "type": "number"}], "defaultSort": {"field": "performance_records", "direction": "desc"}},
            {"id": "formula_quality", "title": "公式和值域检查", "subtitle": "事件类型可加总性、负值和非法帧比例。", "dataset": "formula_quality", "sourceId": "formula_quality", "density": "spacious", "layout": "full", "columns": [{"field": "label", "label": "包体", "type": "text"}, {"field": "checked_days", "label": "检查日数", "type": "number"}, {"field": "additive_mismatch_days", "label": "加总不一致日数", "type": "number"}, {"field": "negative_duration_values", "label": "负时长", "type": "number"}, {"field": "negative_network_latency_values", "label": "负网络延迟", "type": "number"}, {"field": "invalid_frame_ratio_values", "label": "非法帧比例", "type": "number"}, {"field": "status", "label": "状态", "type": "text"}], "defaultSort": {"field": "label", "direction": "asc"}},
            {"id": "session_quality", "title": "Sessions 与 Performance 标记", "subtitle": "Performance 标记冲突单独保留，不能据此否定实际 Performance 数据。", "dataset": "session_quality", "sourceId": "sessions_quality", "density": "spacious", "layout": "full", "columns": [{"field": "label", "label": "包体", "type": "text"}, {"field": "checked_days", "label": "日数", "type": "number"}, {"field": "daily_distinct_sessions_sum", "label": "日唯一会话数合计", "type": "number"}, {"field": "performance_flag_share_min", "label": "Performance 标记下限", "type": "percent"}, {"field": "performance_flag_share_max", "label": "Performance 标记上限", "type": "percent"}, {"field": "status", "label": "状态", "type": "text"}], "defaultSort": {"field": "label", "direction": "asc"}},
            {"id": "analytics_coverage", "title": "Android Analytics 包体覆盖", "subtitle": "独立按日期×包体核验；当前仅支持单日基线。", "dataset": "analytics_coverage", "sourceId": "analytics_coverage", "density": "spacious", "layout": "full", "columns": [{"field": "metric_date_lagos", "label": "日期", "type": "date"}, {"field": "app_package", "label": "包体", "type": "text"}, {"field": "event_count", "label": "事件数", "type": "number"}, {"field": "app_version_count", "label": "版本数", "type": "number"}, {"field": "stream_count", "label": "数据流数", "type": "number"}, {"field": "session_start_event_count", "label": "session_start 事件数", "type": "number"}], "defaultSort": {"field": "metric_date_lagos", "direction": "asc"}},
            {"id": "report_catalog", "title": "日报、周报和专项报告合同", "subtitle": "统一使用 BigQuery 聚合视图，报告按不同时间窗口和行动场景输出。", "dataset": "report_catalog", "sourceId": "report_catalog_source", "density": "spacious", "layout": "full", "columns": [{"field": "name", "label": "报告", "type": "text"}, {"field": "window", "label": "统计窗口", "type": "text"}, {"field": "sections", "label": "章节", "type": "text"}], "defaultSort": {"field": "name", "direction": "asc"}},
            {"id": "sql_catalog", "title": "SQL 脚本目录", "subtitle": "管理员对象脚本、定时聚合脚本和 Metabase 只读视图脚本；本轮只生成草案。", "dataset": "sql_catalog", "sourceId": "sql_catalog_source", "density": "spacious", "layout": "full", "columns": [{"field": "file", "label": "脚本", "type": "text"}, {"field": "execution_mode", "label": "执行方式", "type": "text"}, {"field": "status", "label": "状态", "type": "text"}], "defaultSort": {"field": "file", "direction": "asc"}},
        ],
        "blocks": [
            {"id": "title", "type": "markdown", "body": "# Waje 三端设备与性能看板、报表及 BigQuery 聚合设计"},
            {"id": "executive_summary", "type": "markdown", "body": f"## Executive Summary\n\n**本方案把 BigQuery 作为计算层、Metabase 作为展示层，本地只接收汇总结果。** 当前已验证的 Android Performance 数据覆盖 **{summary['coverage_pairs']}/{summary['expected_coverage_pairs']}** 个日期×包体组合，7 日 Performance 记录约 **{summary['performance_records'] / 1_000_000:.2f}M**，7 日加权网络成功率约 **{pct(summary['weighted_network_success_rate'])}**。\n\n**三端设计可以落地，但数据成熟度必须分层展示。** Android Performance 已有 7 日基线；Android Analytics 当前只有 **{summary['analytics_covered_days']}** 个有效日；iOS 和 H5 的部分指标保持 `provisional` 或 `data_gap`，不得在 Metabase 中用空值或 0 掩盖。\n\n**报告不把 Performance 记录数当作用户数，也不把网络成功率当作业务成功率。** P90、Sessions、Analytics 事件和服务端漏斗分别保留自己的分母和质量状态。\n\n**当前仅产出设计、SQL 和配置草案。** 不创建或修改远端 Metabase、BigQuery 数据集、视图或定时任务。"},
            {"id": "kpis", "type": "metric-strip", "cardIds": ["performance_records", "coverage_pairs", "network_success", "analytics_days"]},
            {"id": "architecture", "type": "markdown", "body": "## 一、在线聚合架构：原始数据留在 BigQuery，Metabase 只读授权视图\n\n**数据处理链路：** 原始 Firebase/服务端聚合事实 → BigQuery 日期过滤与字段归一化 → 日/15分钟聚合 → 质量状态 → `vw_metabase_*` 授权视图 → Metabase Dashboard/Report。\n\nBigQuery 负责分区过滤、P90、加权比率、版本/设备分层、周期比较和质量检查；Python 只负责提交 SQL、读取小规模汇总结果、保存 Job ID/扫描量/状态并生成报告。\n\nMetabase 不直接访问原始 Firebase、Crashlytics、Sessions、Origin、订单或支付表。"},
            {"id": "coverage_chart", "type": "chart", "chartId": "source_coverage_days"},
            {"id": "coverage_note", "type": "markdown", "body": "## 当前成熟度：Performance 可做 7 日观察，Analytics/H5 仍需显式标记\n\nAndroid Performance 的 7 日数据可用于包体、版本、网络和设备信号比较；Android Analytics 当前只能作为单日包体覆盖基线。H5 当前只有行为事件，不能将页面浏览、停留或退出代理成 LCP、INP、TTFB 或前端错误率。"},
            {"id": "pages_heading", "type": "markdown", "body": "## 二、Metabase 四页 Dashboard 结构\n\n四页统一采用“总览 → 性能诊断 → 行为边界 → 设备与接入缺口”的阅读路径。首屏只放决策相关指标，明细和质量状态放在图表后方。"},
            {"id": "pages_table", "type": "table", "tableId": "dashboard_pages"},
            {"id": "volume_heading", "type": "markdown", "body": "## Android Performance 规模：三个包体均可比较，但记录数不是用户数\n\n当前 7 日数据覆盖三个 Android 包体。包体规模图用于识别采集量级和排查断流，不用于评价包体好坏或推断用户规模。"},
            {"id": "volume_chart", "type": "chart", "chartId": "android_package_volume"},
            {"id": "daily_volume_chart", "type": "chart", "chartId": "daily_performance_trend"},
            {"id": "performance_heading", "type": "markdown", "body": "## 三、性能指标：P90 为主指标，样本门槛和 Trace 语义必须同时可见\n\n本期主指标使用 P90。DURATION_TRACE 和 NETWORK_REQUEST 分开绘图，避免毫秒和比例混在同一张图中。少于 500 个有效样本时显示 `N/A`，不补零。\n\nDURATION_TRACE P90 不能直接称为 App 启动耗时；只有完成 Trace 分类后，才能拆成启动、游戏初始化、后台或其他业务阶段。"},
            {"id": "duration_chart", "type": "chart", "chartId": "latest_duration_p90"},
            {"id": "network_chart", "type": "chart", "chartId": "latest_network_p90"},
            {"id": "network_success_chart", "type": "chart", "chartId": "network_success_by_package"},
            {"id": "network_trend_chart", "type": "chart", "chartId": "daily_network_success"},
            {"id": "slow_frame_chart", "type": "chart", "chartId": "latest_slow_frame"},
            {"id": "frozen_frame_chart", "type": "chart", "chartId": "latest_frozen_frame"},
            {"id": "metric_table", "type": "table", "tableId": "metric_catalog"},
            {"id": "network_heading", "type": "markdown", "body": "## 网络成功率：只反映 HTTP 响应，不替代服务端业务漏斗\n\n网络成功率 = HTTP 200–399 响应数 ÷ 有响应码请求数。周报必须从 BigQuery 原始事件端重新按周计算，不能平均每日成功率；P90 也不能平均每日 P90。\n\n登录、游戏进入、下注、充值和结算必须接入服务端授权聚合视图，否则相关 KPI 显示 `blocked`。"},
            {"id": "device_heading", "type": "markdown", "body": "## 四、设备与版本：用高样本组合确定兼容性优先级\n\n设备型号、系统版本、网络类型和运营商均在 BigQuery 端完成聚合。Metabase 的设备排行通过 `rank_dimension` 单选切换，每个聚合组至少 10 条样本；报告只保留 Top 组合和汇总字段，不传输设备唯一标识。"},
            {"id": "device_chart", "type": "chart", "chartId": "device_top_rank"},
            {"id": "device_table", "type": "table", "tableId": "device_top"},
            {"id": "quality_heading", "type": "markdown", "body": "## 五、质量检查：数据冲突必须作为状态呈现\n\nPerformance 事件类型可加总和值域检查应进入发布门禁。Sessions 中 Performance 标记为 false、但 Performance 表存在实际记录时，显示 `quality_warning`，不能写成 Performance 未接入。缺失日期、查询延迟、样本不足和字段漂移分别显示 `data_gap`、`delayed`、`immature` 或 `blocked`。"},
            {"id": "quality_chart", "type": "chart", "chartId": "quality_state_mix"},
            {"id": "formula_table", "type": "table", "tableId": "formula_quality"},
            {"id": "session_table", "type": "table", "tableId": "session_quality"},
            {"id": "analytics_chart", "type": "chart", "chartId": "analytics_package_volume"},
            {"id": "analytics_table", "type": "table", "tableId": "analytics_coverage"},
            {"id": "reports_heading", "type": "markdown", "body": "## 六、日报、周报和版本/事故专项报告\n\n**日报：** 最新完整日数据截止、覆盖、P90、网络、版本/设备变化和质量告警。\n\n**周报：** 上周一至周日的加权 P90、成功率、设备/网络回归、包体版本变化和行动项。\n\n**版本/事故报告：** 只在发布、相对回归、断流或字段漂移时触发，呈现变化、样本、分母、排除项和行动项。"},
            {"id": "reports_table", "type": "table", "tableId": "report_catalog"},
            {"id": "sql_heading", "type": "markdown", "body": "## 七、BigQuery SQL 与 Metabase 配置\n\nSQL 目录中的管理员脚本负责创建聚合层和只读视图；定时脚本负责在线计算；Metabase 只执行视图级 SELECT。详细 SQL 文件位于本报告同目录的 `sql/` 文件夹，HTML 以脚本目录、用途和执行方式为主，避免把长 SQL 和业务结论混在首屏。"},
            {"id": "sql_table", "type": "table", "tableId": "sql_catalog"},
            {"id": "security", "type": "markdown", "body": "## 八、权限、成本和隐私\n\n- BigQuery 项目固定为 `wajenigeria`，区域固定为 `europe-west4`，时区固定为 `Africa/Lagos`。\n- 每条查询先 dry run；单查询不超过 5 GiB，单轮不超过 25 GiB。\n- Metabase 仅拥有授权聚合视图的只读权限；不授予 Data Editor/Owner。\n- 不下载原始事件、不返回用户标识、设备唯一标识、URL、请求/响应正文、订单或支付明细。\n- `remote_udf_conn` 不是普通 BigQuery 查询的认证凭证；本方案不使用它连接普通表。"},
            {"id": "acceptance", "type": "markdown", "body": "## 九、验收与发布门禁\n\n1. 源表/视图、区域、字段和分区均通过元数据核验。\n2. 所有聚合 SQL 通过只读、日期过滤、成本和敏感字段检查。\n3. 日期×包体覆盖完整，缺失日期不补零。\n4. P90 样本门槛、网络成功率分母、帧比例值域和事件类型可加总性通过。\n5. 日报/周报与 BigQuery 汇总结果逐项一致。\n6. Metabase 四页筛选器能改变相关卡片，质量状态不会被转换为数字。\n7. HTML 桌面/移动端均有表格或语义回退；浏览器增强检查失败时在回执中说明。"},
            {"id": "questions", "type": "markdown", "body": "## Further Questions\n\n- Android Performance 的 DURATION_TRACE 需要按哪些已批准 Trace 分类拆分？\n- 服务端核心漏斗的授权聚合视图由哪个数据负责人维护？\n- iOS Performance 的真实来源表和 Analytics 覆盖是否已达到 7 个完整日？\n- H5 是否计划补齐 Web Vitals、核心请求、游戏 Ready 和前端错误事件？\n- 相对回归告警是否采用默认的 P90 +20% 与网络成功率 -1pp，还是由研发 SLA 覆盖？"},
            {"id": "caveats", "type": "markdown", "body": "## Caveats and assumptions\n\n- 本文档是 Metabase 创建和 BigQuery 聚合实现设计，不是远端 Dashboard 已创建回执。\n- 当前实际数值来自 2026-08-20 至 08-26 的聚合基线；未来刷新需重新执行 SQL 和质量检查。\n- Performance 记录量、事件量和日唯一会话数不能混称为用户数。\n- `provisional`、`immature`、`data_gap`、`delayed` 和 `blocked` 不是 0，也不是性能正常。\n- 报表涉及的服务端注册、登录、游戏和支付成功事实必须通过批准的服务端聚合视图接入。"},
        ],
    }
    snapshot_summary = dict(summary)
    snapshot_summary["coverage_pairs_label"] = f"{summary['coverage_pairs']}/{summary['expected_coverage_pairs']}"
    return {
        "surface": "report",
        "manifest": manifest,
        "snapshot": {"version": 1, "generatedAt": manifest["generatedAt"], "status": "partial", "accessIssues": manifest["accessIssues"], "datasets": {"summary": [snapshot_summary], **{key: data[key] for key in ("source_coverage", "package_totals", "latest_network", "latest_duration", "daily_coverage", "device_top", "device_top_global", "latest_package_metrics", "daily_network_success", "quality_state_counts", "formula_quality", "session_quality", "analytics_coverage", "metric_catalog", "dashboard_pages", "report_catalog", "sql_catalog")}}},
        "sources": sources,
        "package_info": {"classification": "waje_three_platform_metabase_design", "contains_sensitive_data": False},
    }


def main() -> None:
    data = build_report_data()
    artifact = build_artifact(data)
    OUT_ARTIFACT.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_CHART_MAP.write_text(json.dumps({
        "source_coverage_days": {"family": "bar", "question": "哪些端侧数据已经达到可比较的覆盖天数？", "grain": "source × covered_days", "source": "current_baseline"},
        "android_package_volume": {"family": "bar", "question": "三个 Android 包体的 Performance 记录量如何？", "grain": "package × 7-day aggregate", "source": "performance_coverage"},
        "latest_duration_p90": {"family": "bar", "question": "最新完整日各包体 DURATION_TRACE P90 如何？", "grain": "latest complete day × package", "source": "performance_metrics"},
        "latest_network_p90": {"family": "bar", "question": "最新完整日各包体 NETWORK_REQUEST P90 如何？", "grain": "latest complete day × package", "source": "performance_metrics"},
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT_ARTIFACT)


if __name__ == "__main__":
    main()
