#!/usr/bin/env python3
"""Build a compact, aggregate-only Android BigQuery analysis report artifact."""

from __future__ import annotations

import datetime as dt
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
VALIDATION_ROOT = ROOT.parent / "android_bq_api_validation_2026_08_27"
SQL_ROOT = VALIDATION_ROOT / "sql"
FULL_RECEIPT = ROOT / "full-validation-receipt.json"
ANALYTICS_RECEIPT = ROOT / "supplemental-coverage-receipt.json"
ARTIFACT_PATH = ROOT / "report-artifact.json"
REPORT_DATA_PATH = ROOT / "report-data.json"
CHART_MAP_PATH = ROOT / "chart-map.json"

LABELS = {
    "android_main": "Android 主包",
    "android_transsion_old": "Android 传音老包",
    "android_transsion_new": "Android 传音新包",
}
PACKAGES = {
    "android_main": "com.hfhy.waje.special",
    "android_transsion_old": "com.hfhy.wajecasino.palmgame",
    "android_transsion_new": "com.hfhy.wajecasino.game",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rows_for(receipt: dict[str, Any], query_id: str) -> list[dict[str, Any]]:
    for query in receipt.get("queries", []):
        if query.get("id") == query_id:
            return list((query.get("execution") or {}).get("aggregate_rows") or [])
    return []


def rounded(value: float | None, digits: int = 6) -> float | None:
    return None if value is None else round(float(value), digits)


def source_spec(source_id: str, label: str, sql_file: str, description: str, tables: list[str], filters: list[str], definitions: list[str], source_dir: Path = SQL_ROOT, source_path: str | None = None) -> dict[str, Any]:
    sql = (source_dir / sql_file).read_text(encoding="utf-8").strip()
    return {
        "id": source_id,
        "label": label,
        "path": source_path or f"analysis/android_bq_validation_2026_08_27/sql/{sql_file}",
        "query": {
            "engine": "BigQuery",
            "language": "SQL",
            "description": description,
            "sql": sql,
            "tables_used": tables,
            "filters": filters,
            "metric_definitions": definitions,
            "execution_status": "executed_via_google-cloud-bigquery-python-client",
        },
    }


def build_summary(full: dict[str, Any], analytics: dict[str, Any]) -> dict[str, Any]:
    coverage = rows_for(full, "01_performance_daily_coverage")
    metrics = rows_for(full, "02_performance_metric_aggregates")
    device_rows = rows_for(full, "03_device_os_mix")
    network_rows = rows_for(full, "04_network_quality")
    session_rows = rows_for(full, "05_sessions_reconciliation")
    formula_rows = rows_for(full, "07_formula_reconciliation")
    analytics_rows = list((analytics.get("execution") or {}).get("aggregate_rows") or [])

    total_records = sum(int(row.get("performance_record_count") or 0) for row in coverage)
    response_total = sum(int(row.get("network_response_count") or 0) for row in metrics)
    success_total = sum(int(row.get("network_success_count") or 0) for row in metrics)
    network_p90_eligible = sum(1 for row in metrics if row.get("network_p90_ms") is not None)
    duration_p90_eligible = sum(1 for row in metrics if row.get("duration_p90_ms") is not None)
    latest_date = max((row.get("metric_date_lagos") for row in metrics), default=None)
    latest_metrics = [row for row in metrics if row.get("metric_date_lagos") == latest_date]

    package_totals = []
    for endpoint in sorted(LABELS):
        cov = [row for row in coverage if row.get("endpoint") == endpoint]
        met = [row for row in metrics if row.get("endpoint") == endpoint]
        latest = next((row for row in met if row.get("metric_date_lagos") == latest_date), None)
        package_totals.append(
            {
                "endpoint": endpoint,
                "label": LABELS[endpoint],
                "app_package": PACKAGES[endpoint],
                "performance_record_count": sum(int(row.get("performance_record_count") or 0) for row in cov),
                "covered_days": len({row.get("metric_date_lagos") for row in cov}),
                "duration_sample_count": sum(int(row.get("duration_sample_count") or 0) for row in met),
                "network_request_count": sum(int(row.get("network_request_count") or 0) for row in met),
                "weighted_network_success_rate": rounded(
                    sum(int(row.get("network_success_count") or 0) for row in met)
                    / sum(int(row.get("network_response_count") or 0) for row in met)
                    if sum(int(row.get("network_response_count") or 0) for row in met)
                    else None
                ),
                "latest_duration_p90_ms": rounded((latest or {}).get("duration_p90_ms"), 3),
                "latest_network_p90_ms": rounded((latest or {}).get("network_p90_ms"), 3),
                "latest_slow_frame_ratio": rounded((latest or {}).get("slow_frame_ratio_trace_mean")),
                "latest_frozen_frame_ratio": rounded((latest or {}).get("frozen_frame_ratio_trace_mean")),
            }
        )

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

    performance_metrics = [
        {
            "date": row.get("metric_date_lagos"),
            "endpoint": row.get("endpoint"),
            "label": LABELS.get(row.get("endpoint"), row.get("endpoint")),
            "duration_sample_count": int(row.get("duration_sample_count") or 0),
            "duration_p90_ms": rounded(row.get("duration_p90_ms"), 3),
            "network_sample_count": int(row.get("network_sample_count") or 0),
            "network_p90_ms": rounded(row.get("network_p90_ms"), 3),
            "network_success_rate": rounded(row.get("network_success_rate")),
            "slow_frame_ratio": rounded(row.get("slow_frame_ratio_trace_mean")),
            "frozen_frame_ratio": rounded(row.get("frozen_frame_ratio_trace_mean")),
            "quality_status": row.get("quality_status"),
        }
        for row in sorted(metrics, key=lambda item: (item.get("metric_date_lagos"), item.get("endpoint")))
    ]

    network_by_version: dict[tuple[str, str], dict[str, Any]] = defaultdict(lambda: {"requests": 0, "responses": 0, "success": 0, "missing": 0, "p90s": [], "eligible_days": 0})
    for row in network_rows:
        key = (str(row.get("endpoint")), str(row.get("app_version")))
        bucket = network_by_version[key]
        bucket["requests"] += int(row.get("network_request_count") or 0)
        bucket["responses"] += int(row.get("response_code_count") or 0)
        bucket["success"] += int(row.get("network_success_count") or 0)
        bucket["missing"] += int(row.get("missing_response_code_count") or 0)
        if row.get("network_p90_ms") is not None:
            bucket["p90s"].append(float(row["network_p90_ms"]))
            bucket["eligible_days"] += 1
    network_versions = []
    for (endpoint, app_version), bucket in sorted(network_by_version.items(), key=lambda item: -item[1]["requests"]):
        network_versions.append(
            {
                "endpoint": endpoint,
                "label": LABELS.get(endpoint, endpoint),
                "app_version": app_version,
                "network_requests": bucket["requests"],
                "response_codes": bucket["responses"],
                "missing_response_code_rate": rounded(bucket["missing"] / bucket["requests"] if bucket["requests"] else None),
                "weighted_network_success_rate": rounded(bucket["success"] / bucket["responses"] if bucket["responses"] else None),
                "network_p90_min_ms": rounded(min(bucket["p90s"]) if bucket["p90s"] else None, 3),
                "network_p90_max_ms": rounded(max(bucket["p90s"]) if bucket["p90s"] else None, 3),
                "p90_eligible_days": bucket["eligible_days"],
            }
        )
    network_versions = network_versions[:20]

    device_groups: dict[tuple[str, str, str], int] = defaultdict(int)
    for row in device_rows:
        key = (str(row.get("endpoint")), str(row.get("device_name")), str(row.get("os_version")))
        device_groups[key] += int(row.get("performance_record_count") or 0)
    device_top = []
    for endpoint in sorted(LABELS):
        endpoint_rows = sorted(
            ((device, os_version, count) for (ep, device, os_version), count in device_groups.items() if ep == endpoint),
            key=lambda item: -item[2],
        )[:8]
        for rank, (device, os_version, count) in enumerate(endpoint_rows, start=1):
            device_top.append({"endpoint": endpoint, "label": LABELS[endpoint], "rank": rank, "device_name": device, "os_version": os_version, "performance_records": count})

    formula_quality = []
    for endpoint in sorted(LABELS):
        rows = [row for row in formula_rows if row.get("endpoint") == endpoint]
        formula_quality.append(
            {
                "endpoint": endpoint,
                "label": LABELS[endpoint],
                "days": len(rows),
                "sum_mismatch_days": sum(1 for row in rows if int(row.get("additive_reconciliation_delta") or 0) != 0),
                "negative_duration_values": sum(int(row.get("negative_duration_count") or 0) for row in rows),
                "negative_network_latency_values": sum(int(row.get("negative_network_latency_count") or 0) for row in rows),
                "invalid_frame_ratio_values": sum(int(row.get("invalid_frame_ratio_count") or 0) for row in rows),
                "quality_status": "passed" if all(row.get("quality_status") == "basic_formula_checks_pass" for row in rows) else "warning",
            }
        )

    session_quality = []
    for endpoint in sorted(LABELS):
        rows = [row for row in session_rows if row.get("endpoint") == endpoint]
        session_quality.append(
            {
                "endpoint": endpoint,
                "label": LABELS[endpoint],
                "days": len(rows),
                "daily_distinct_sessions_sum": sum(int(row.get("distinct_session_count") or 0) for row in rows),
                "performance_flag_share_min": rounded(min((row.get("performance_flag_share") or 0) for row in rows) if rows else None),
                "performance_flag_share_max": rounded(max((row.get("performance_flag_share") or 0) for row in rows) if rows else None),
                "crashlytics_flag_share_min": rounded(min((row.get("crashlytics_flag_share") or 0) for row in rows) if rows else None),
                "crashlytics_flag_share_max": rounded(max((row.get("crashlytics_flag_share") or 0) for row in rows) if rows else None),
                "quality_status": "warning_performance_flag_conflict" if any(row.get("quality_status") == "quality_warning_check_performance_table" for row in rows) else "observed",
            }
        )

    return {
        "scope": {
            "project_id": "wajenigeria",
            "location": "europe-west4",
            "timezone": "Africa/Lagos",
            "window_start": "2026-08-20",
            "window_end": "2026-08-26",
            "latest_observed_date": latest_date,
        },
        "summary": {
            "performance_record_count": total_records,
            "coverage_combinations": len(coverage),
            "coverage_expected": 21,
            "weighted_network_success_rate": rounded(success_total / response_total if response_total else None),
            "duration_p90_eligible_combinations": duration_p90_eligible,
            "network_p90_eligible_combinations": network_p90_eligible,
            "returned_aggregate_or_metadata_rows": int(full.get("data_rows_read") or 0) + int(analytics.get("data_rows_read") or 0),
            "dry_run_gib": full.get("dry_run", {}).get("total_bytes_processed_gib"),
        },
        "package_totals": package_totals,
        "latest_metrics": [
            {
                "endpoint": row.get("endpoint"),
                "label": LABELS.get(row.get("endpoint"), row.get("endpoint")),
                "duration_p90_ms": rounded(row.get("duration_p90_ms"), 3),
                "network_p90_ms": rounded(row.get("network_p90_ms"), 3),
                "network_success_rate": rounded(row.get("network_success_rate")),
                "slow_frame_ratio": rounded(row.get("slow_frame_ratio_trace_mean")),
                "frozen_frame_ratio": rounded(row.get("frozen_frame_ratio_trace_mean")),
                "duration_sample_count": int(row.get("duration_sample_count") or 0),
                "network_sample_count": int(row.get("network_sample_count") or 0),
            }
            for row in sorted(latest_metrics, key=lambda item: item.get("endpoint"))
        ],
        "daily_coverage": daily_coverage,
        "performance_metrics": performance_metrics,
        "network_versions": network_versions,
        "device_top": device_top,
        "formula_quality": formula_quality,
        "session_quality": session_quality,
        "analytics_coverage": analytics_rows,
    }


def build_artifact(data: dict[str, Any], full: dict[str, Any]) -> dict[str, Any]:
    sources = [
        source_spec("performance_coverage", "Android Performance 每日覆盖", "01_performance_daily_coverage.sql", "按日和 Android 包体统计 Performance 记录、事件类型和版本覆盖。", ["wajenigeria.waje_ng_firebase_android_performance.*"], ["2026-08-20 至 2026-08-26", "Africa/Lagos"], ["记录数为 Performance 事件记录数", "覆盖组合期望为 7 个日期 × 3 个包体"]),
        source_spec("performance_metrics", "Android Performance 性能指标", "02_performance_metric_aggregates.sql", "复算轨迹时长 P90、网络响应 P90、网络成功率和屏幕帧比例。", ["wajenigeria.waje_ng_firebase_android_performance.*"], ["2026-08-20 至 2026-08-26", "P90 合格样本至少 500"], ["P90 使用 APPROX_QUANTILES", "网络成功率为 200–399 响应数除以有响应码请求数", "慢帧和冻结帧为 SCREEN_TRACE trace 加权均值"]),
        source_spec("device_mix", "Android Performance 设备结构", "03_device_os_mix.sql", "按设备型号和系统版本输出达到最小样本量的聚合组合。", ["wajenigeria.waje_ng_firebase_android_performance.*"], ["2026-08-20 至 2026-08-26", "聚合组至少 10 条记录", "每包每日最多 50 组"], ["设备字段只作聚合维度，不代表独立设备数"]),
        source_spec("network_quality", "Android 网络请求质量", "04_network_quality.sql", "按日期、包体和版本核验网络响应码、延迟和成功率。", ["wajenigeria.waje_ng_firebase_android_performance.*"], ["2026-08-20 至 2026-08-26", "仅 NETWORK_REQUEST"], ["网络 P90 样本至少 500", "不返回 URL、请求名或正文"]),
        source_spec("sessions_quality", "Android Sessions 采集标记", "05_sessions_reconciliation.sql", "按日和包体核验去标识化会话量以及 Performance/Crashlytics 采集标记。", ["wajenigeria.waje_ng_firebase_android_sessions.*"], ["2026-08-20 至 2026-08-26"], ["日唯一会话数只在日粒度内去重", "不把 Analytics session_start 与 Sessions 唯一会话数混称"]),
        source_spec("analytics_coverage", "Android Analytics 包体覆盖", "03_android_analytics_coverage.sql", "单独核验 Analytics 日期×包体覆盖，避免 3,000 行结果上限掩盖包体或日期。", ["wajenigeria.waje_ng_firebase_android.events_*"], ["2026-08-20 至 2026-08-26", "platform = ANDROID", "仅三个登记包体"], ["事件数为事件记录数，不是用户数或会话数"], source_dir=ROOT / "sql", source_path="analysis/android_bq_api_client_2026_08_27/sql/03_android_analytics_coverage.sql"),
        source_spec("formula_quality", "Performance 公式和值域检查", "07_formula_reconciliation.sql", "核验事件类型分项可加总性及负值、非法帧比例和缺失响应码。", ["wajenigeria.waje_ng_firebase_android_performance.*"], ["2026-08-20 至 2026-08-26"], ["只输出质量计数", "不删除或修正源数据"]),
        {
            "id": "analysis_contract",
            "label": "Android 设备与性能分析合同",
            "path": "analysis/multiplatform_device_performance_dashboard_v1_2026_08_27/data_contract.json",
            "query": {"engine": "Local JSON contract", "language": "JSON", "description": "定义包体映射、P90 样本门槛、业务时区和聚合隐私边界。"},
        },
    ]

    summary = data["summary"]
    latest = data["latest_metrics"]
    latest_duration = [row for row in latest if row.get("duration_p90_ms") is not None]
    latest_network = [row for row in latest if row.get("network_p90_ms") is not None]

    manifest = {
        "version": 1,
        "surface": "report",
        "title": "Android 设备与性能数据分析报告｜BigQuery 聚合版",
        "description": "基于 BigQuery API 的数据库端聚合结果；本地只接收汇总结果，不下载原始 Performance 或用户明细。",
        "generatedAt": dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(timespec="seconds"),
        "sources": sources,
        "accessIssues": [
            "所有实时 SQL 已通过 Python BigQuery 客户端执行；报告只使用聚合结果。",
            "Android Analytics 当前只覆盖 2026-08-24 一天，不能作为 7 日趋势。",
            "Sessions 的 Performance 采集标记为 false，但 Performance 表有实际记录，属于口径冲突。",
            "Performance 的 DURATION_TRACE P90 是混合 trace 口径，不能直接等同 App 启动耗时。",
        ],
        "statusDefinitions": {
            "provisional": "有实测聚合数据，但仍有成熟度或口径限制。",
            "quality_warning": "查询成功，但存在需研发/数据核查的质量信号。",
            "data_gap": "当前来源或时间窗口不足，不代表业务指标为零。",
        },
        "cards": [
            {"id": "total_performance", "dataset": "summary", "sourceId": "performance_coverage", "metrics": [{"label": "7日 Performance 记录", "field": "performance_record_count", "format": "number"}]},
            {"id": "coverage_pairs", "dataset": "summary", "sourceId": "performance_coverage", "metrics": [{"label": "日期×包体覆盖", "field": "coverage_combinations_label", "format": "text"}]},
            {"id": "weighted_success", "dataset": "summary", "sourceId": "performance_metrics", "metrics": [{"label": "加权网络成功率", "field": "weighted_network_success_rate", "format": "percent"}]},
            {"id": "network_p90_eligible", "dataset": "summary", "sourceId": "performance_metrics", "metrics": [{"label": "网络 P90 合格组合", "field": "network_p90_eligible_label", "format": "text"}]},
        ],
        "charts": [
            {
                "id": "package_volume",
                "title": "7日 Performance 记录量",
                "subtitle": "2026年8月20日至26日；按包体汇总事件记录数，不代表用户数。",
                "dataset": "package_totals",
                "sourceId": "performance_coverage",
                "type": "bar",
                "layout": "full",
                "encodings": {"x": {"field": "label", "type": "nominal", "label": "Android 包体"}, "y": {"field": "performance_record_count", "type": "quantitative", "format": "number", "label": "Performance 记录数"}},
                "palette": {"kind": "categorical", "name": "blue"},
                "settings": {"sort": "descending", "showValues": True},
            },
            {
                "id": "latest_duration_p90",
                "title": "最新完整日 DURATION_TRACE P90",
                "subtitle": "2026年8月26日；单位毫秒，样本数不足时不显示数值。",
                "dataset": "latest_duration",
                "sourceId": "performance_metrics",
                "type": "bar",
                "layout": "full",
                "encodings": {"x": {"field": "label", "type": "nominal", "label": "Android 包体"}, "y": {"field": "duration_p90_ms", "type": "quantitative", "format": "number", "label": "P90（毫秒）"}},
                "palette": {"kind": "categorical", "name": "blue"},
                "settings": {"sort": "descending", "showValues": True},
            },
            {
                "id": "latest_network_p90",
                "title": "最新完整日 NETWORK_REQUEST P90",
                "subtitle": "2026年8月26日；单位毫秒，按有效响应完成耗时计算。",
                "dataset": "latest_network",
                "sourceId": "performance_metrics",
                "type": "bar",
                "layout": "full",
                "encodings": {"x": {"field": "label", "type": "nominal", "label": "Android 包体"}, "y": {"field": "network_p90_ms", "type": "quantitative", "format": "number", "label": "P90（毫秒）"}},
                "palette": {"kind": "categorical", "name": "blue"},
                "settings": {"sort": "descending", "showValues": True},
            },
            {
                "id": "network_success",
                "title": "7日加权网络成功率",
                "subtitle": "2026年8月20日至26日；HTTP 200–399 ÷ 有响应码请求数。",
                "dataset": "package_totals",
                "sourceId": "performance_metrics",
                "type": "bar",
                "layout": "full",
                "encodings": {"x": {"field": "label", "type": "nominal", "label": "Android 包体"}, "y": {"field": "weighted_network_success_rate", "type": "quantitative", "format": "percent", "label": "成功率"}},
                "palette": {"kind": "categorical", "name": "blue"},
                "settings": {"sort": "descending", "showValues": True},
            },
        ],
        "tables": [
            {"id": "daily_coverage", "title": "每日 Performance 覆盖", "subtitle": "21 个日期×包体组合；用于确认日期和包体没有静默缺失。", "dataset": "daily_coverage", "sourceId": "performance_coverage", "density": "spacious", "layout": "full", "columns": [
                {"field": "date", "label": "日期", "type": "date"}, {"field": "label", "label": "包体", "type": "text"}, {"field": "performance_records", "label": "记录数", "type": "number"}, {"field": "duration_traces", "label": "DURATION_TRACE", "type": "number"}, {"field": "screen_traces", "label": "SCREEN_TRACE", "type": "number"}, {"field": "network_requests", "label": "NETWORK_REQUEST", "type": "number"}, {"field": "versions", "label": "版本数", "type": "number"}
            ], "defaultSort": {"field": "date", "direction": "asc"}},
            {"id": "performance_metrics", "title": "性能指标按日与包体", "subtitle": "P90 只在有效样本达到 500 时显示；网络成功率不等同业务接口成功率。", "dataset": "performance_metrics", "sourceId": "performance_metrics", "density": "spacious", "layout": "full", "columns": [
                {"field": "date", "label": "日期", "type": "date"}, {"field": "label", "label": "包体", "type": "text"}, {"field": "duration_sample_count", "label": "时长样本", "type": "number"}, {"field": "duration_p90_ms", "label": "时长 P90（ms）", "type": "number"}, {"field": "network_sample_count", "label": "网络样本", "type": "number"}, {"field": "network_p90_ms", "label": "网络 P90（ms）", "type": "number"}, {"field": "network_success_rate", "label": "网络成功率", "type": "percent"}, {"field": "slow_frame_ratio", "label": "慢帧比例", "type": "percent"}, {"field": "frozen_frame_ratio", "label": "冻结帧比例", "type": "percent"}, {"field": "quality_status", "label": "状态", "type": "text"}
            ], "defaultSort": {"field": "date", "direction": "desc"}},
            {"id": "network_versions", "title": "网络质量版本分层", "subtitle": "按版本汇总请求量；P90 展示同版本日级 P90 的范围，未把多个 P90 直接平均。", "dataset": "network_versions", "sourceId": "network_quality", "density": "spacious", "layout": "full", "columns": [
                {"field": "label", "label": "包体", "type": "text"}, {"field": "app_version", "label": "版本", "type": "text"}, {"field": "network_requests", "label": "网络请求", "type": "number"}, {"field": "weighted_network_success_rate", "label": "加权成功率", "type": "percent"}, {"field": "missing_response_code_rate", "label": "响应码缺失率", "type": "percent"}, {"field": "network_p90_min_ms", "label": "P90下限（ms）", "type": "number"}, {"field": "network_p90_max_ms", "label": "P90上限（ms）", "type": "number"}, {"field": "p90_eligible_days", "label": "P90合格日数", "type": "number"}
            ], "defaultSort": {"field": "network_requests", "direction": "desc"}},
            {"id": "device_top", "title": "高样本设备与系统组合", "subtitle": "每个包体保留 Performance 记录量最高的 8 个聚合组合；不是完整设备排名。", "dataset": "device_top", "sourceId": "device_mix", "density": "spacious", "layout": "full", "columns": [
                {"field": "label", "label": "包体", "type": "text"}, {"field": "rank", "label": "排名", "type": "number"}, {"field": "device_name", "label": "设备型号", "type": "text"}, {"field": "os_version", "label": "系统版本", "type": "text"}, {"field": "performance_records", "label": "记录数", "type": "number"}
            ], "defaultSort": {"field": "performance_records", "direction": "desc"}},
            {"id": "formula_quality", "title": "公式与值域质量检查", "subtitle": "事件类型可加总性、负值和非法帧比例检查。", "dataset": "formula_quality", "sourceId": "formula_quality", "density": "spacious", "layout": "full", "columns": [
                {"field": "label", "label": "包体", "type": "text"}, {"field": "days", "label": "检查日数", "type": "number"}, {"field": "sum_mismatch_days", "label": "加总不一致日数", "type": "number"}, {"field": "negative_duration_values", "label": "负时长", "type": "number"}, {"field": "negative_network_latency_values", "label": "负网络延迟", "type": "number"}, {"field": "invalid_frame_ratio_values", "label": "非法帧比例", "type": "number"}, {"field": "quality_status", "label": "状态", "type": "text"}
            ], "defaultSort": {"field": "label", "direction": "asc"}},
            {"id": "session_quality", "title": "Sessions 与采集标记", "subtitle": "按日聚合的唯一会话数合计，不是整个 7 日窗口去重；Performance 标记冲突单独显示。", "dataset": "session_quality", "sourceId": "sessions_quality", "density": "spacious", "layout": "full", "columns": [
                {"field": "label", "label": "包体", "type": "text"}, {"field": "days", "label": "日数", "type": "number"}, {"field": "daily_distinct_sessions_sum", "label": "日唯一会话数合计", "type": "number"}, {"field": "performance_flag_share_min", "label": "Performance标记下限", "type": "percent"}, {"field": "performance_flag_share_max", "label": "Performance标记上限", "type": "percent"}, {"field": "crashlytics_flag_share_min", "label": "Crashlytics标记下限", "type": "percent"}, {"field": "crashlytics_flag_share_max", "label": "Crashlytics标记上限", "type": "percent"}, {"field": "quality_status", "label": "状态", "type": "text"}
            ], "defaultSort": {"field": "label", "direction": "asc"}},
            {"id": "analytics_coverage", "title": "Android Analytics 覆盖", "subtitle": "独立按日期×包体核验，避免长尾设备/事件结果截断影响覆盖判断。", "dataset": "analytics_coverage", "sourceId": "analytics_coverage", "density": "spacious", "layout": "full", "columns": [
                {"field": "metric_date_lagos", "label": "日期", "type": "date"}, {"field": "app_package", "label": "包体", "type": "text"}, {"field": "event_count", "label": "事件数", "type": "number"}, {"field": "app_version_count", "label": "版本数", "type": "number"}, {"field": "stream_count", "label": "数据流数", "type": "number"}, {"field": "session_start_event_count", "label": "session_start事件数", "type": "number"}
            ], "defaultSort": {"field": "metric_date_lagos", "direction": "asc"}},
        ],
        "blocks": [
            {"id": "title", "type": "markdown", "body": "# Android 设备与性能数据分析报告｜BigQuery 聚合版"},
            {"id": "executive_summary", "type": "markdown", "body": f"## Executive Summary\n\n**数据库端聚合链路已验证可用。** 本次通过 BigQuery Python API 对 8 条核心 SQL 和 1 条 Analytics 覆盖查询完成 dry run 与实际只读执行；7 日 Performance 日期×包体覆盖为 **{len(data['daily_coverage'])}/{summary['coverage_expected']}**，没有发现日期或包体静默缺失。\n\n**性能数据可以支持包体、日期和网络/轨迹信号比较，但仍是 provisional。** 三个 Android 包共返回约 **{summary['performance_record_count'] / 1_000_000:.2f}M** 条 Performance 事件记录；加权网络成功率约 **{summary['weighted_network_success_rate'] * 100:.2f}%**。该成功率只反映 HTTP 响应码，不等同登录、充值、下注或业务成功。\n\n**当前最重要的限制是口径和可观测性。** Analytics 目前只覆盖 8 月 24 日；Sessions 中 Performance 标记与 Performance 表实际记录冲突；DURATION_TRACE P90 是混合 trace 口径，不能直接当作 App 启动耗时。\n\n**本报告只下载并使用数据库端聚合结果。** 未下载原始 Performance 事件、用户明细、设备唯一标识、URL、请求/响应正文或堆栈。"},
            {"id": "metrics", "type": "metric-strip", "cardIds": ["total_performance", "coverage_pairs", "weighted_success", "network_p90_eligible"]},
            {"id": "volume_heading", "type": "markdown", "body": "## 三个 Android 包均有完整 7 日 Performance 覆盖\n\n**Performance 记录主要用于确认采集规模和包体覆盖，不直接代表用户规模。** 下面的比较已在 BigQuery 按日期和包体聚合后才下载到本地。"},
            {"id": "volume_chart", "type": "chart", "chartId": "package_volume"},
            {"id": "coverage_table", "type": "table", "tableId": "daily_coverage"},
            {"id": "performance_heading", "type": "markdown", "body": f"## 最新完整日可计算 P90，但 DURATION_TRACE 需要先确认 trace 语义\n\n**8 月 26 日三个包均有足够 DURATION_TRACE 和 NETWORK_REQUEST 样本。** 7 日窗口中，DURATION_TRACE P90 合格组合为 **{summary['duration_p90_eligible_combinations']}/{len(data['performance_metrics'])}**，网络 P90 合格组合为 **{summary['network_p90_eligible_combinations']}/{len(data['performance_metrics'])}**。8 月 20 日主包网络样本为 434，低于 500，因此该组合的网络 P90 按规则保持空值。\n\n**DURATION_TRACE 最新 P90 数值较大，暂不直接转化为“启动慢”结论。** 需要研发确认 trace 类型、单位和是否包含长时游戏/后台轨迹，再决定是否将其拆成启动、游戏初始化或其他业务阶段。"},
            {"id": "duration_chart", "type": "chart", "chartId": "latest_duration_p90"},
            {"id": "network_p90_chart", "type": "chart", "chartId": "latest_network_p90"},
            {"id": "success_chart", "type": "chart", "chartId": "network_success"},
            {"id": "metrics_table", "type": "table", "tableId": "performance_metrics"},
            {"id": "network_heading", "type": "markdown", "body": "## 网络成功率整体稳定，但版本级 P90 需要按请求类型继续拆分\n\n**当前网络响应码填充完整，网络成功率约在 99.7%–100% 范围内。** 这是网络层的观测信号，不能替代服务端登录、游戏进入、下注、充值或结算成功率。\n\n**版本级 P90 采用日级范围展示。** 不能把多个日期的 P90 再做简单平均；后续如要得到严格的版本窗口 P90，应由 BigQuery 在原始事件端按版本重新计算，而不是从日级 P90 二次平均。"},
            {"id": "network_table", "type": "table", "tableId": "network_versions"},
            {"id": "device_heading", "type": "markdown", "body": "## 设备结构可用于兼容性优先级，但当前不是完整设备排名\n\n**设备型号和系统版本已经可以在数据库端完成聚合。** 报告仅保留每个包体记录量最高的 8 个组合，用于确定首批真机和低端渠道机测试范围；长尾组合没有下载到报告中。\n\n**设备记录量不等于独立设备数。** Performance 数据一条记录可能对应一次 trace 或网络请求，不能直接据此推算设备覆盖人数。"},
            {"id": "device_table", "type": "table", "tableId": "device_top"},
            {"id": "quality_heading", "type": "markdown", "body": "## 公式校验通过，但 Sessions 采集标记存在需要核查的冲突\n\n**Performance 事件类型可加总，值域检查没有发现负时长、负网络延迟或非法帧比例。** 这说明当前聚合公式和字段转换可以运行。\n\n**Sessions 的 Performance 标记不能用来否定 Performance 表。** 三个包的 Sessions 聚合均出现 Performance 标记为 false、但 Performance 表存在大量记录的情况；应核查该字段是用户开关、历史 SDK 状态还是导出语义。"},
            {"id": "formula_table", "type": "table", "tableId": "formula_quality"},
            {"id": "session_table", "type": "table", "tableId": "session_quality"},
            {"id": "analytics_heading", "type": "markdown", "body": "## Analytics 已确认三个包体，但只有一个有效数据日\n\n**8 月 24 日三个 Android 包均出现在 Analytics 日表中。** 主包、传音新包和传音老包分别有事件记录，说明包体映射可用。\n\n**Analytics 目前只能作为单日覆盖基线。** 在形成至少 7 个稳定日表之前，不输出 Android Analytics 的跨日趋势、版本增长或留存判断。"},
            {"id": "analytics_table", "type": "table", "tableId": "analytics_coverage"},
            {"id": "next_steps", "type": "markdown", "body": "## Recommended next steps\n\n1. **优先拆分 DURATION_TRACE 语义：** 在 BigQuery 端按已批准的 trace 分类或业务阶段重新聚合，避免把混合 P90 当成启动耗时。\n2. **建立数据库端授权聚合层：** 将 Performance、Sessions 和 Analytics 的固定聚合结果落到只读视图或定期汇总任务；本地只下载日报级结果。\n3. **完善网络指标：** 按核心请求类别、版本、网络类型和国家聚合 P90/成功率，并与服务端业务成功事实对账。\n4. **核查 Sessions 标记语义：** 解释 Performance 开关字段与实际 Performance 表记录不一致的原因。\n5. **Analytics 累计稳定日后再启用趋势：** 目前保留为 8 月 24 日单日覆盖，不作为 7 日增长结论。\n6. **继续保留 dry run 和成本门禁：** 每次查询先做扫描量估算，保留 SQL 哈希、Job ID、返回行数和数据截止时间。"},
            {"id": "questions", "type": "markdown", "body": "## Further questions\n\n- `DURATION_TRACE` 是否混合了启动、游戏初始化、后台或长时轨迹？\n- `network_info.response_completed_time_us` 的业务定义是否为完整响应完成耗时？\n- Sessions 中 `performance_data_collection_enabled` 的 false 是否表示用户级开关，而不是表级采集状态？\n- Android Analytics 是否会继续生成 8 月 25 日及之后的日表？\n- 哪些授权聚合视图可以供后续报表或 Agent 读取，而不开放底层用户和设备唯一标识？"},
            {"id": "caveats", "type": "markdown", "body": "## Caveats and assumptions\n\n- 统计窗口为 2026 年 8 月 20 日至 26 日，业务时区为 `Africa/Lagos`；报告生成时间为 2026 年 8 月 27 日。\n- 所有指标来自 BigQuery 已聚合查询；事件数、Performance 记录数和日唯一会话数不能混称为用户数。\n- 网络成功率是 HTTP 响应码口径，不等同业务成功率。\n- P90 小于 500 个合格样本时保持空值；缺失、未成熟和质量冲突不补零。\n- 报告不输出用户 ID、用户伪 ID、会话 ID、设备唯一标识、广告标识、URL、请求/响应正文、订单、支付或堆栈信息。\n- 当前状态为 `provisional_with_quality_warnings`，适合数据和研发排查，不作为正式稳定性 SLA 或用户转化结论。"},
        ],
    }

    for card in manifest["cards"]:
        if card["id"] == "coverage_pairs":
            card["metrics"][0]["field"] = "coverage_combinations_label"
        if card["id"] == "network_p90_eligible":
            card["metrics"][0]["field"] = "network_p90_eligible_label"

    snapshot_summary = dict(summary)
    snapshot_summary["coverage_combinations_label"] = f"{summary['coverage_combinations']}/{summary['coverage_expected']}"
    snapshot_summary["network_p90_eligible_label"] = f"{summary['network_p90_eligible_combinations']}/{len(data['performance_metrics'])}"
    snapshot = {
        "version": 1,
        "generatedAt": manifest["generatedAt"],
        "status": "partial",
        "accessIssues": manifest["accessIssues"],
        "datasets": {
            "summary": [snapshot_summary],
            "package_totals": data["package_totals"],
            "latest_duration": latest_duration,
            "latest_network": latest_network,
            "daily_coverage": data["daily_coverage"],
            "performance_metrics": data["performance_metrics"],
            "network_versions": data["network_versions"],
            "device_top": data["device_top"],
            "formula_quality": data["formula_quality"],
            "session_quality": data["session_quality"],
            "analytics_coverage": data["analytics_coverage"],
        },
    }
    return {"surface": "report", "manifest": manifest, "snapshot": snapshot, "sources": sources, "package_info": {"classification": "aggregate_only_android_device_performance_report", "contains_sensitive_data": False}}


def main() -> None:
    full = read_json(FULL_RECEIPT)
    analytics = read_json(ANALYTICS_RECEIPT)
    data = build_summary(full, analytics)
    ARTIFACT_PATH.write_text(json.dumps(build_artifact(data, full), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CHART_MAP_PATH.write_text(json.dumps({
        "package_volume": {"family": "bar", "question": "三个 Android 包的 Performance 记录量是否存在明显规模差异？", "source": "q01_performance_daily_coverage"},
        "latest_duration_p90": {"family": "bar", "question": "最新完整日各包体 DURATION_TRACE P90 如何？", "source": "q02_performance_metric_aggregates"},
        "latest_network_p90": {"family": "bar", "question": "最新完整日各包体网络响应 P90 如何？", "source": "q02_performance_metric_aggregates"},
        "network_success": {"family": "bar", "question": "各包体 7 日加权网络成功率如何？", "source": "q02_performance_metric_aggregates"},
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(ARTIFACT_PATH)


if __name__ == "__main__":
    main()
