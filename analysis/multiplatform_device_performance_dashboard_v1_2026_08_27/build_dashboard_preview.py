#!/usr/bin/env python3
"""Create a portable dashboard preview from reviewed aggregate baseline data.

This is a local delivery fallback only. It does not claim that the Metabase
dashboard or BigQuery aggregate mart has been published.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BASELINE = ROOT / "actual_baseline.json"
ARTIFACT = ROOT / "dashboard_preview_artifact.json"


def iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def main() -> int:
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    performance = baseline["native_performance"]
    coverage = baseline["source_coverage"]
    sessions = baseline["android_sessions"]
    h5 = baseline["h5_event_dictionary"]
    total_native_records = sum(item["performance_record_count"] for item in performance)
    total_android_sessions = sum(item["distinct_session_count"] for item in sessions)
    total_h5_events = sum(item["event_count"] for item in h5)
    source = {
        "id": "current_bq_baseline",
        "label": "当前企业 BigQuery 脱敏聚合基线",
        "path": "actual_baseline.json",
        "query": {
            "engine": "BigQuery",
            "language": "SQL",
            "description": "按端、包、日期和事件/性能类别读取的脱敏聚合；完整的可复跑查询位于 baseline_aggregate_queries.sql。",
            "sql": "SELECT DATE(event_timestamp, 'Africa/Lagos') AS metric_date_lagos, COUNT(*) AS aggregate_record_count FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_waje_special_ANDROID` WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-13' AND DATE '2026-08-27' GROUP BY metric_date_lagos",
            "tables_used": [
                "wajenigeria.waje_ng_firebase_android.events_20260824",
                "wajenigeria.waje_ng_firebase_h5.events_*",
                "wajenigeria.waje_ng_firebase_ios.events_*",
                "wajenigeria.waje_ng_firebase_android_performance.*",
                "wajenigeria.waje_ng_firebase_ios_performance.com_wajegame_wajegame_IOS",
                "wajenigeria.waje_ng_firebase_android_sessions.*",
                "wajenigeria.waje_ng_firebase_android_crashlytics.*"
            ],
            "filters": [
                "Africa/Lagos date window",
                "aggregate-only",
                "no user/device/order/request detail"
            ],
            "metric_definitions": [
                "Performance record count is Firebase Performance export record count.",
                "session_start is an Analytics event count, not a unique session count.",
                "Android distinct session count is only comparable within Firebase Sessions.",
                "Crashlytics export record count is not a crash rate."
            ]
        }
    }
    source_coverage_rows = [
        {
            **row,
            "label": f"{row['endpoint']} / {row['source']}",
            "coverage_days": row["covered_days"],
        }
        for row in coverage
    ]
    quality_rows = [
        {"status": "BigQuery 聚合层", "value": "受阻", "detail": "缺少 bigquery.datasets.create；未创建 waje_device_performance_mart。"},
        {"status": "Metabase 远端看板", "value": "受阻", "detail": "没有可用 SSO、API 身份或 Collection Curate 权限。"},
        {"status": "Android Sessions/Performance", "value": "质量警告", "detail": "Sessions 开关为 false，但 Performance 表有实际记录；真实性能覆盖以 Performance 表为准。"},
        {"status": "H5 RUM", "value": "数据缺口", "detail": "当前只有四类标准行为事件，尚无 Web Vitals、请求时延、错误或游戏就绪事件。"}
    ]
    artifact = {
        "surface": "dashboard",
        "manifest": {
            "version": 1,
            "surface": "dashboard",
            "title": "Waje 多端设备与性能看板 V1｜当前数据预览",
            "description": "基于当前可读取的企业 BigQuery 聚合结果。此文件是 Metabase 远端看板的本地预览，不替代生产 Dashboard。",
            "generatedAt": iso_now(),
            "sources": [source],
            "cards": [
                {"id": "native_records", "dataset": "summary", "sourceId": "current_bq_baseline", "metrics": [{"label": "原生性能记录", "field": "total_native_records", "format": "number"}]},
                {"id": "android_sessions", "dataset": "summary", "sourceId": "current_bq_baseline", "metrics": [{"label": "Android 去标识化会话", "field": "total_android_sessions", "format": "number"}]},
                {"id": "h5_events", "dataset": "summary", "sourceId": "current_bq_baseline", "metrics": [{"label": "H5 标准行为事件", "field": "total_h5_events", "format": "number"}]},
                {"id": "source_count", "dataset": "summary", "sourceId": "current_bq_baseline", "metrics": [{"label": "已见数据源", "field": "source_count", "format": "number"}]}
            ],
            "charts": [
                {"id": "performance_records", "title": "各包原生性能记录量", "subtitle": "当前已入库窗口；记录量不是用户数或性能好坏结论", "dataset": "native_performance", "sourceId": "current_bq_baseline", "type": "bar", "encodings": {"x": {"field": "label"}, "y": {"field": "performance_record_count"}}},
                {"id": "coverage_days", "title": "数据源覆盖天数", "subtitle": "不足 7 个完整日的端侧不参与跨端趋势比较", "dataset": "source_coverage", "sourceId": "current_bq_baseline", "type": "bar", "encodings": {"x": {"field": "label"}, "y": {"field": "coverage_days"}}},
                {"id": "h5_events", "title": "H5 当前事件结构", "subtitle": "仅四类标准行为事件，未包含 Web RUM 或核心游戏漏斗指标", "dataset": "h5_event_dictionary", "sourceId": "current_bq_baseline", "type": "bar", "encodings": {"x": {"field": "event_name"}, "y": {"field": "event_count"}}}
            ],
            "tables": [
                {"id": "coverage_table", "title": "端侧数据覆盖与成熟度", "dataset": "source_coverage", "sourceId": "current_bq_baseline", "columns": [{"field": "endpoint", "label": "端侧", "type": "text"}, {"field": "source", "label": "来源", "type": "text"}, {"field": "first_day", "label": "首日", "type": "date"}, {"field": "last_day", "label": "最新日", "type": "date"}, {"field": "covered_days", "label": "覆盖天数", "type": "number"}, {"field": "status", "label": "状态", "type": "text"}], "defaultSort": {"field": "covered_days", "direction": "desc"}},
                {"id": "quality_table", "title": "当前上线阻断与数据质量", "dataset": "quality", "sourceId": "current_bq_baseline", "columns": [{"field": "status", "label": "对象", "type": "text"}, {"field": "value", "label": "状态", "type": "text"}, {"field": "detail", "label": "说明", "type": "text"}], "defaultSort": {"field": "status", "direction": "asc"}}
            ],
            "blocks": [
                {"id": "title", "type": "markdown", "body": "# Waje 多端设备与性能看板 V1｜当前数据预览"},
                {"id": "summary", "type": "markdown", "sourceId": "current_bq_baseline", "body": "## 当前结论\n\n**Android 原生性能数据已形成可试运行基线，但 H5 与 iOS 仍未达到统一趋势对比条件。** Android 三包 Performance 均已覆盖 7 个数据日；H5 仅有四类标准行为事件；iOS Analytics/Performance 覆盖不足 7 日。\n\n**此预览只展示已核验的聚合事实和数据状态。** 它不将记录量解释为用户数、体验质量或业务成功率，也不把 Crashlytics 导出行数称为崩溃率。"},
                {"id": "metrics", "type": "metric-strip", "cardIds": ["native_records", "android_sessions", "h5_events", "source_count"]},
                {"id": "coverage_heading", "type": "markdown", "sourceId": "current_bq_baseline", "body": "## 数据覆盖与成熟度\n\n**跨端看板必须先通过完整日门禁。** Android Analytics 当前只有 1 个数据日；iOS 当前不足 7 个完整日；H5 行为数据虽有 8 日，但没有性能事件。生产 Metabase 看板会据此显示 `immature`、`data_gap` 或 `delayed`，不会插入零值。"},
                {"id": "coverage_chart", "type": "chart", "chartId": "coverage_days"},
                {"id": "coverage_table_block", "type": "table", "tableId": "coverage_table"},
                {"id": "performance_heading", "type": "markdown", "sourceId": "current_bq_baseline", "body": "## Android 与 iOS 原生性能\n\n**记录已入库不等于性能良好。** 后续 Metabase 会基于版本、设备、网络类型和国家计算轨迹 P95、网络 P95、HTTP 成功率、慢帧和冻结帧；当前预览只展示记录覆盖。"},
                {"id": "performance_chart", "type": "chart", "chartId": "performance_records"},
                {"id": "h5_heading", "type": "markdown", "sourceId": "current_bq_baseline", "body": "## H5 当前状态\n\n**H5 目前只适合做基础访问与互动观察。** 现有事件没有 Web Vitals、路由 ready、核心请求、前端错误、白/黑屏或游戏就绪/可下注信号；这些指标在正式看板中必须保持 `data_gap` 或 `blocked`。"},
                {"id": "h5_chart", "type": "chart", "chartId": "h5_events"},
                {"id": "blockers_heading", "type": "markdown", "sourceId": "current_bq_baseline", "body": "## 实施状态\n\n**BigQuery 聚合层和 Metabase 远端对象尚未创建。** 本地已生成可复跑 SQL、数据契约、Dashboard 合同与 Metabase 配置册；待管理员授予项目 Dataset 创建权限及 Metabase Collection/数据源权限后即可按顺序上线。"},
                {"id": "quality_table_block", "type": "table", "tableId": "quality_table"}
            ]
        },
        "snapshot": {
            "version": 1,
            "status": "partial",
            "generatedAt": iso_now(),
            "accessIssues": [
                {"scope": "bigquery_aggregate_mart", "message": "企业账号缺少 bigquery.datasets.create；目标数据集尚未创建。"},
                {"scope": "metabase_remote_dashboard", "message": "没有可用的 Metabase SSO/API 身份、Collection Curate 或数据源写入权限。"},
                {"scope": "h5_web_rum", "message": "H5 当前仅有四类标准 Analytics 事件，未接入 Web RUM、核心请求、错误和游戏就绪指标。"}
            ],
            "datasets": {
                "summary": [{"total_native_records": total_native_records, "total_android_sessions": total_android_sessions, "total_h5_events": total_h5_events, "source_count": len(coverage)}],
                "native_performance": performance,
                "source_coverage": source_coverage_rows,
                "h5_event_dictionary": h5,
                "quality": quality_rows
            }
        },
        "package_info": {"classification": "internal_aggregate_analysis", "contains_sensitive_data": False}
    }
    ARTIFACT.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "artifact": str(ARTIFACT), "native_records": total_native_records}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
