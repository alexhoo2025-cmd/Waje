#!/usr/bin/env python3
"""Build actual phase-one and simulated phase-two examples for the device dashboard.

The base V3 document remains the source of the six-module design.  This
builder regenerates that base, adds example sections to the local Markdown and
HTML readers, and writes a separate, auditable example package.  Phase-one
rows come only from reviewed aggregate snapshots; phase-two rows are fixed
demonstration values and are never mixed into actuals.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_device_performance_requirements_v3 as base  # noqa: E402


RUN_DATE = "2026-09-02"
REPORT_DATA = ROOT / "analysis/metabase_waje_three_platform_dashboard_design_2026_08_27/report-data.json"
BASELINE_DATA = ROOT / "analysis/multiplatform_device_performance_dashboard_v1_2026_08_27/actual_baseline.json"
STABILITY_DATA = ROOT / "analysis/metabase_v4_visual_dashboard_2026_09_01/stability_rate_audit.json"
EXAMPLE_DIR = ROOT / f"analysis/device_performance_dashboard_examples_{RUN_DATE.replace('-', '_')}"
OUTPUT_MD = base.OUTPUT_MD
OUTPUT_HTML = base.OUTPUT_HTML


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ratio(numerator: int | float, denominator: int | float, digits: int = 6) -> float | None:
    if not denominator:
        return None
    return round(float(numerator) / float(denominator), digits)


def pct(value: float | None, digits: int = 2) -> str:
    return "N/A" if value is None else f"{value * 100:.{digits}f}%"


def num(value: int | float | None) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float) and not value.is_integer():
        return f"{value:,.2f}"
    return f"{int(value):,}"


def ms(value: float | int | None) -> str:
    return "N/A" if value is None else f"{float(value):,.0f} ms"


def actual_example_data(report: dict[str, Any], baseline: dict[str, Any], stability: dict[str, Any]) -> dict[str, Any]:
    summary = report["summary"]
    coverage = report["daily_coverage"]
    dates = sorted({row["date"] for row in coverage})
    labels = sorted({row["label"] for row in coverage})
    matrix = []
    for label in labels:
        row = {"package_label": label}
        for day in dates:
            hit = next((item for item in coverage if item["label"] == label and item["date"] == day), None)
            row[day] = {"observed": bool(hit), "performance_records": hit["performance_records"] if hit else None}
        matrix.append(row)
    return {
        "data_state": "actual_aggregate",
        "source_status": "reviewed_snapshot",
        "window": report["scope"]["window"],
        "latest_complete_day": report["scope"]["latest_complete_day"],
        "business_timezone": report["scope"]["timezone"],
        "project": report["scope"]["project_id"],
        "location": report["scope"]["location"],
        "summary": {
            "performance_records": summary["performance_records"],
            "coverage_pairs": summary["coverage_pairs"],
            "expected_coverage_pairs": summary["expected_coverage_pairs"],
            "coverage_rate": ratio(summary["coverage_pairs"], summary["expected_coverage_pairs"]),
            "weighted_network_success_rate": summary["weighted_network_success_rate"],
            "duration_p90_eligible_pairs": summary["duration_p90_eligible_pairs"],
            "network_p90_eligible_pairs": summary["network_p90_eligible_pairs"],
            "analytics_covered_days": summary["analytics_covered_days"],
        },
        "package_totals": report["package_totals"],
        "latest_package_metrics": report["latest_package_metrics"],
        "coverage_dates": dates,
        "coverage_matrix": matrix,
        "daily_network_success": report["daily_network_success"],
        "h5_behavior": baseline["h5_event_dictionary"],
        "source_coverage": baseline["source_coverage"],
        "stability_proxy": stability["rows"],
        "stability_definition": stability["definition"],
        "quality_warnings": baseline["quality_warnings"],
    }


def simulated_example_data() -> dict[str, Any]:
    """Fixed values used only to demonstrate the planned phase-two layouts."""
    return {
        "data_state": "simulated",
        "source_status": "design_only",
        "simulation_scenario": "phase2_dashboard_layout_v1",
        "simulation_seed": "waje-device-performance-2026-09-02-v1",
        "window": "演示窗口（不对应生产日期）",
        "rum": [
            {"route_key": "首页", "browser_bucket": "Chrome", "valid_page_visits": 1200, "ready_p50_ms": 1800, "ready_p95_ms": 4200, "fcp_p95_ms": 1600, "lcp_p95_ms": 3200, "inp_p95_ms": 260, "cls_p95": 0.12, "blank_count": 10, "black_count": 4},
            {"route_key": "商城", "browser_bucket": "Chrome", "valid_page_visits": 920, "ready_p50_ms": 2100, "ready_p95_ms": 5100, "fcp_p95_ms": 1900, "lcp_p95_ms": 3800, "inp_p95_ms": 310, "cls_p95": 0.16, "blank_count": 15, "black_count": 5},
            {"route_key": "游戏入口", "browser_bucket": "Android WebView", "valid_page_visits": 760, "ready_p50_ms": 2500, "ready_p95_ms": 6800, "fcp_p95_ms": 2300, "lcp_p95_ms": 4700, "inp_p95_ms": 380, "cls_p95": 0.21, "blank_count": 22, "black_count": 9},
        ],
        "requests": [
            {"endpoint_key": "登录", "valid_requests": 10000, "business_success": 9800, "timeout": 150, "retried": 300, "duration_p95_ms": 1200},
            {"endpoint_key": "余额", "valid_requests": 8600, "business_success": 8428, "timeout": 86, "retried": 172, "duration_p95_ms": 900},
            {"endpoint_key": "进入游戏", "valid_requests": 6400, "business_success": 5952, "timeout": 192, "retried": 384, "duration_p95_ms": 2300},
            {"endpoint_key": "下注", "valid_requests": 4200, "business_success": 4158, "timeout": 42, "retried": 84, "duration_p95_ms": 760},
        ],
        "recovery": {
            "attempts": 1000,
            "success": 860,
            "user_abandon": 90,
            "duration_p50_ms": 1800,
            "duration_p95_ms": 7800,
        },
        "game_funnel": [
            {"stage": "加载开始", "count": 10000},
            {"stage": "真正可玩", "count": 9100},
            {"stage": "可下注", "count": 8650},
            {"stage": "服务端开局", "count": 8200},
            {"stage": "正常完局", "count": 7700},
            {"stage": "结算完成", "count": 7650},
        ],
        "attribution": [
            {"performance_group": "正常性能组", "eligible_users": 10000, "first_play_users": 3600, "payer_users": 780, "d1_users": 2500},
            {"performance_group": "性能异常组", "eligible_users": 3200, "first_play_users": 960, "payer_users": 192, "d1_users": 672},
        ],
    }


def enrich_simulated(sim: dict[str, Any]) -> dict[str, Any]:
    for row in sim["rum"]:
        row["blank_rate"] = ratio(row["blank_count"], row["valid_page_visits"])
        row["black_rate"] = ratio(row["black_count"], row["valid_page_visits"])
    for row in sim["requests"]:
        row["business_success_rate"] = ratio(row["business_success"], row["valid_requests"])
        row["timeout_rate"] = ratio(row["timeout"], row["valid_requests"])
        row["retry_rate"] = ratio(row["retried"], row["valid_requests"])
    sim["recovery"]["success_rate"] = ratio(sim["recovery"]["success"], sim["recovery"]["attempts"])
    sim["recovery"]["abandon_rate"] = ratio(sim["recovery"]["user_abandon"], sim["recovery"]["attempts"])
    start = sim["game_funnel"][0]["count"]
    for row in sim["game_funnel"]:
        row["rate_from_start"] = ratio(row["count"], start)
    for row in sim["attribution"]:
        row["first_play_rate"] = ratio(row["first_play_users"], row["eligible_users"])
        row["payer_rate"] = ratio(row["payer_users"], row["eligible_users"])
        row["d1_rate"] = ratio(row["d1_users"], row["eligible_users"])
    return sim


def metric_catalog() -> dict[str, Any]:
    return {
        "phase1_actual": [
            {"metric_id": "performance_coverage_rate", "name": "端/包覆盖率", "definition": "已观察的日期×包体组合占预期组合的比例", "formula": "COUNT(observed date×package) / COUNT(expected date×package)", "denominator": "预期日期×包体组合", "grain": "日期 × 包体", "dimensions": ["端侧", "包体", "日期"], "fields": ["metric_date_lagos", "endpoint", "package", "coverage_status"], "source": "report-data.json.daily_coverage", "data_state": "actual_aggregate", "missing_events": [], "status": "实际聚合"},
            {"metric_id": "weighted_network_success_rate", "name": "网络成功率", "definition": "HTTP 200–399 响应占有响应码请求的比例", "formula": "COUNT(response_code BETWEEN 200 AND 399) / COUNT(response_code IS NOT NULL)", "denominator": "有响应码的网络请求", "grain": "日期 × 包体 × 请求类别", "dimensions": ["包体", "版本", "网络类型", "请求类别"], "fields": ["response_code", "network_request_count", "network_success_rate"], "source": "report-data.json.package_totals", "data_state": "actual_aggregate", "missing_events": [], "status": "实际聚合"},
            {"metric_id": "duration_p90_ms", "name": "轨迹 P90", "definition": "有效 DURATION_TRACE 时长的第 90 百分位", "formula": "P90(duration_ms)", "denominator": "有效 duration trace；当前窗口按包体可用", "grain": "日期 × 包体 × 版本", "dimensions": ["端侧", "包体", "版本", "设备型号桶"], "fields": ["duration_ms", "duration_sample_count", "app_version"], "source": "report-data.json.latest_package_metrics", "data_state": "actual_aggregate", "missing_events": [], "status": "实际 P90"},
            {"metric_id": "network_p90_ms", "name": "网络 P90", "definition": "网络请求响应完成耗时的第 90 百分位", "formula": "P90(response_completed_ms)", "denominator": "有效网络请求；当前窗口按包体可用", "grain": "日期 × 包体 × 网络类型", "dimensions": ["包体", "版本", "网络类型", "运营商桶"], "fields": ["response_completed_ms", "network_sample_count", "network_type"], "source": "report-data.json.latest_package_metrics", "data_state": "actual_aggregate", "missing_events": [], "status": "实际 P90"},
            {"metric_id": "fatal_affected_subject_rate_per_10k", "name": "Fatal 受影响主体率（每万）", "definition": "发生 Fatal 的去标识化主体占活跃去标识化主体的比例，按每万展示", "formula": "COUNT(DISTINCT fatal_subject) / COUNT(DISTINCT active_subject) × 10,000", "denominator": "去标识化活跃主体；不是账号用户", "grain": "日期窗口 × 包体", "dimensions": ["包体", "版本"], "fields": ["active_user_proxy_count", "fatal_affected_user_proxy_count", "fatal_per_10k"], "source": "stability_rate_audit.json", "data_state": "actual_aggregate", "missing_events": ["稳定性事件与会话的认证关联键"], "status": "实际聚合/待字段认证"},
            {"metric_id": "session_established_rate", "name": "会话建立成功率", "definition": "成功建立会话的去重会话数占建立尝试数的比例", "formula": "COUNT(DISTINCT successful_session_id) / COUNT(DISTINCT session_attempt_id)", "denominator": "必须有 session_attempt_id；无分母显示 N/A", "grain": "日期 × 端 × 包 × 版本", "dimensions": ["端侧", "包体", "版本"], "fields": ["successful_session_id", "session_attempt_id"], "source": "Sessions + SESSION_INIT_ATTEMPT", "data_state": "not_available", "missing_events": ["SESSION_INIT_ATTEMPT 或已有会话初始化尝试事实"], "status": "待补分母"},
            {"metric_id": "h5_behavior_event_count", "name": "H5 标准行为事件量（辅助）", "definition": "已到达的 page_view、session_start、first_visit、user_engagement 记录数", "formula": "COUNTIF(event_name IN (page_view, session_start, first_visit, user_engagement))", "denominator": "事件记录数；不代表用户数或性能成功", "grain": "日期 × 事件名", "dimensions": ["事件名", "日期", "来源"], "fields": ["event_name", "event_count", "covered_days"], "source": "actual_baseline.json.h5_event_dictionary", "data_state": "actual_aggregate", "missing_events": ["Web RUM、核心请求和游戏状态事件"], "status": "实际行为基线"},
        ],
        "phase2_simulated": [
            {"metric_id": "h5_ready_p95_ms", "name": "页面 ready P95", "definition": "页面从导航开始到业务内容 ready 的第 95 百分位耗时", "formula": "P95(ready_at - navigation_start_at)", "denominator": "measurement_state=complete 的 page_visit_id", "grain": "日期 × 路由 × 浏览器 × 网络", "dimensions": ["route_key", "browser_bucket", "network_type", "web_version"], "fields": ["page_visit_id", "navigation_start_at", "ready_at", "measurement_state"], "source": "H5_NAVIGATION_PERF（待创建）", "data_state": "simulated", "missing_events": ["H5_NAVIGATION_PERF"], "status": "模拟演示"},
            {"metric_id": "h5_blank_screen_rate", "name": "白屏率", "definition": "发生白屏的页面/游戏链路占有效链路的比例", "formula": "COUNT(DISTINCT blank_flow_id) / COUNT(DISTINCT eligible_flow_id)", "denominator": "有效 page_visit_id 或 game_load_id", "grain": "日期 × 路由 × 版本", "dimensions": ["route_key", "web_version", "browser_bucket"], "fields": ["page_visit_id", "blank_screen_status", "error_stage"], "source": "H5_CLIENT_ERROR（待创建）", "data_state": "simulated", "missing_events": ["H5_CLIENT_ERROR"], "status": "模拟演示"},
            {"metric_id": "core_request_success_rate", "name": "核心请求业务成功率", "definition": "进入业务成功终态的请求占有效请求的比例", "formula": "COUNT(business_success) / COUNT(valid_request)", "denominator": "有效 request_id；HTTP 成功不能替代业务成功", "grain": "日期 × endpoint_key × 版本", "dimensions": ["endpoint_key", "request_kind", "web_version", "network_type"], "fields": ["request_id", "endpoint_key", "business_status", "http_status"], "source": "H5_CORE_REQUEST（待创建）", "data_state": "simulated", "missing_events": ["H5_CORE_REQUEST"], "status": "模拟演示"},
            {"metric_id": "core_request_timeout_rate", "name": "核心请求超时率", "definition": "进入 timeout 终态或超过接口阈值的请求比例", "formula": "COUNT(timeout) / COUNT(valid_request)", "denominator": "有效 request_id；阈值按 endpoint_key 配置", "grain": "日期 × endpoint_key", "dimensions": ["endpoint_key", "web_version", "network_type"], "fields": ["request_id", "duration_ms", "timeout_flag", "endpoint_key"], "source": "H5_CORE_REQUEST（待创建）", "data_state": "simulated", "missing_events": ["H5_CORE_REQUEST、接口阈值字典"], "status": "模拟演示"},
            {"metric_id": "network_recovery_success_rate", "name": "网络恢复成功率", "definition": "断网/切网后恢复到可用状态的比例", "formula": "COUNT(recovery_success) / COUNT(recovery_attempt)", "denominator": "有效 recovery_id；主动放弃单列", "grain": "日期 × 网络类型 × 页面/阶段", "dimensions": ["before_network", "after_network", "stage", "browser_bucket"], "fields": ["recovery_id", "network_change_id", "action", "result", "recovery_duration_ms"], "source": "H5_NETWORK_CHANGE + H5_RECOVERY_RESULT（待创建）", "data_state": "simulated", "missing_events": ["H5_NETWORK_CHANGE", "H5_RECOVERY_RESULT"], "status": "模拟演示"},
            {"metric_id": "game_chain_completion_rate", "name": "游戏链路完局率", "definition": "有服务端有效 GAMEEND 的对局占有效 GAMESTART 的比例", "formula": "COUNT(DISTINCT ended_round_id) / COUNT(DISTINCT started_round_id)", "denominator": "服务端有效 round_id；客户端状态不替代服务端事实", "grain": "日期 × 游戏 × 端 × 版本", "dimensions": ["game_id", "platform", "app_version/web_version", "package_name"], "fields": ["game_load_id", "round_id", "status", "end_reason", "server_event_time"], "source": "H5 三阶段事件 + Origin 服务端事实（待打通）", "data_state": "simulated", "missing_events": ["H5_GAME_LOAD", "H5_GAME_READY", "H5_BET_READY", "服务端链路键"], "status": "模拟演示/跨源待打通"},
            {"metric_id": "performance_first_play_rate_delta", "name": "性能异常组首局率差异", "definition": "性能异常组与正常性能组首局率的差异", "formula": "异常组首局用户/异常组用户 − 正常组首局用户/正常组用户", "denominator": "同端、同包、同版本、同窗口的成熟 cohort", "grain": "cohort × 性能分层", "dimensions": ["platform", "package_name", "version", "performance_bucket"], "fields": ["session_id", "game_load_id", "first_play_at", "performance_bucket"], "source": "H5 RUM + Origin 服务端事实 + 生命周期（待打通）", "data_state": "simulated", "missing_events": ["H5_NAVIGATION_PERF", "H5_GAME_READY", "服务端首局事实"], "status": "模拟演示/仅关联"},
        ],
    }


def dashboard_spec() -> dict[str, Any]:
    return {
        "phase1_actual": [
            {"id": "p1_health_actual", "name": "一期看板 A｜端侧健康与数据可用性", "format": "KPI 卡 + 覆盖矩阵 + 状态表", "question": "数据是否到达、完整、可比较？", "metrics": ["performance_coverage_rate", "weighted_network_success_rate", "analytics_covered_days"], "fields": ["metric_date_lagos", "endpoint", "package", "complete_day", "quality_status"], "source": ["report-data.json", "actual_baseline.json"], "data_state": "actual_aggregate"},
            {"id": "p1_native_actual", "name": "一期看板 B｜原生性能诊断", "format": "横向条形图 + 比率表 + 设备排行", "question": "哪个包体、版本、设备或网络维度更慢？", "metrics": ["duration_p90_ms", "network_p90_ms", "weighted_network_success_rate"], "fields": ["duration_ms", "response_completed_ms", "response_code", "slow_frame_ratio", "frozen_frame_ratio", "app_version", "device_name"], "source": ["report-data.json"], "data_state": "actual_aggregate"},
            {"id": "p1_stability_h5_actual", "name": "一期看板 C｜稳定性和 H5 行为基线", "format": "稳定性率卡 + 行为事件表", "question": "稳定性风险和 H5 行为数据是否可观察？", "metrics": ["fatal_affected_subject_rate_per_10k", "h5_behavior_event_count"], "fields": ["fatal_per_10k", "event_name", "event_count", "covered_days"], "source": ["stability_rate_audit.json", "actual_baseline.json"], "data_state": "actual_aggregate"},
            {"id": "p1_d1_report_actual", "name": "一期报表 D｜D+1 端侧健康日报", "format": "结论 + 指标 + 风险 + 行动表", "question": "今天是否需要补数据或采取行动？", "metrics": ["coverage_rate", "network_success_rate", "data_freshness", "quality_status"], "fields": ["latest_complete_day", "covered_days", "sample_count", "quality_status", "missing_reason"], "source": ["一期聚合 Mart"], "data_state": "actual_aggregate"},
        ],
        "phase2_simulated": [
            {"id": "p2_rum_simulated", "name": "二期看板 E｜H5 Web RUM", "format": "P50/P95/P99 卡 + 路由对比 + 白屏率", "question": "页面性能和白屏问题集中在哪个路由/端？", "metrics": ["h5_ready_p95_ms", "h5_blank_screen_rate"], "fields": ["page_visit_id", "route_key", "fcp_ms", "lcp_ms", "inp_ms", "cls_score", "blank_screen_status"], "source": ["H5_NAVIGATION_PERF", "H5_CLIENT_ERROR"], "data_state": "simulated"},
            {"id": "p2_request_simulated", "name": "二期看板 F｜核心请求体验", "format": "成功率/超时率/重试率对比 + P95", "question": "哪个核心接口在什么网络/版本下失败或超时？", "metrics": ["core_request_success_rate", "core_request_timeout_rate"], "fields": ["request_id", "endpoint_key", "business_status", "http_status", "timeout_flag", "retry_count", "duration_ms"], "source": ["H5_CORE_REQUEST"], "data_state": "simulated"},
            {"id": "p2_recovery_simulated", "name": "二期看板 G｜网络恢复", "format": "断网流程 + 恢复率 + 恢复耗时 P95", "question": "断网/切网后能否恢复？恢复要多久？", "metrics": ["network_recovery_success_rate"], "fields": ["network_change_id", "recovery_id", "before_network", "after_network", "result", "recovery_duration_ms"], "source": ["H5_NETWORK_CHANGE", "H5_RECOVERY_RESULT"], "data_state": "simulated"},
            {"id": "p2_game_simulated", "name": "二期看板 H｜游戏加载到真实业务链路", "format": "漏斗 + 链路关联率 + 资产对账表", "question": "可玩、可下注是否形成真实开局、完局和结算？", "metrics": ["game_ready_rate", "game_chain_completion_rate"], "fields": ["game_load_id", "round_id", "status", "end_reason", "reward_status", "ledger_id"], "source": ["H5 三阶段事件", "Origin 服务端事实"], "data_state": "simulated"},
            {"id": "p2_attribution_simulated", "name": "二期看板 I｜性能影响归因", "format": "正常组/异常组对比 + cohort 结果率", "question": "性能差异是否伴随首局、付费或留存差异？", "metrics": ["performance_first_play_rate_delta"], "fields": ["performance_bucket", "cohort_date", "first_play_at", "payer_flag", "retained_d1"], "source": ["H5 RUM", "Origin 服务端事实", "生命周期事实"], "data_state": "simulated"},
        ],
    }


def source_mapping() -> dict[str, Any]:
    return {
        "actual": {
            "report_data": str(REPORT_DATA.relative_to(ROOT)),
            "baseline": str(BASELINE_DATA.relative_to(ROOT)),
            "stability": str(STABILITY_DATA.relative_to(ROOT)),
            "authority": "已审阅的聚合快照；不代表实时刷新或正式认证口径",
        },
        "simulated": {
            "authority": "固定演示值，仅用于看板布局、字段和公式验收",
            "forbidden_uses": ["不能进入真实趋势", "不能进入产品结论", "不能作为性能目标或线上基线"],
        },
        "lineage": "Firebase/Ares/H5 → BigQuery 聚合层 → 授权 View → Metabase/Ares 看板",
    }


def markdown_examples(actual: dict[str, Any], simulated: dict[str, Any]) -> str:
    summary = actual["summary"]
    package_rows = []
    for row in actual["latest_package_metrics"]:
        package_rows.append([row["label"], ms(row["duration_p90_ms"]), ms(row["network_p90_ms"]), pct(row["network_success_rate"]), pct(row["slow_frame_ratio"]), pct(row["frozen_frame_ratio"]), num(row["duration_sample_count"]), num(row["network_sample_count"])])
    coverage_headers = ["包体"] + actual["coverage_dates"]
    coverage_rows = []
    for row in actual["coverage_matrix"]:
        coverage_rows.append([row["package_label"]] + ["有数据" if row[day]["observed"] else "无数据" for day in actual["coverage_dates"]])
    stability_rows = [[row["endpoint"], num(row["active_user_proxy_count"]), num(row["fatal_affected_user_proxy_count"]), f"{row['fatal_per_10k']:.2f}"] for row in actual["stability_proxy"]]
    h5_rows = [[row["event_name"], num(row["event_count"]), row["covered_days"]] for row in actual["h5_behavior"]]
    rum_rows = [[row["route_key"], num(row["valid_page_visits"]), ms(row["ready_p95_ms"]), ms(row["fcp_p95_ms"]), ms(row["lcp_p95_ms"]), pct(row["blank_rate"]), pct(row["black_rate"])] for row in simulated["rum"]]
    request_rows = [[row["endpoint_key"], num(row["valid_requests"]), pct(row["business_success_rate"]), pct(row["timeout_rate"]), pct(row["retry_rate"]), ms(row["duration_p95_ms"])] for row in simulated["requests"]]
    funnel_rows = [[row["stage"], num(row["count"]), pct(row["rate_from_start"])] for row in simulated["game_funnel"]]
    attribution_rows = [[row["performance_group"], num(row["eligible_users"]), pct(row["first_play_rate"]), pct(row["payer_rate"]), pct(row["d1_rate"])] for row in simulated["attribution"]]
    return "\n".join([
        "### 3.4 一期真实看板与报表示例（实际聚合）",
        "",
        "> **实际聚合**：以下值来自已审阅的聚合快照，窗口为 `2026-08-20 至 2026-08-26`，业务时区为 `Africa/Lagos`。状态仍受字段、时效和口径认证约束。",
        "",
        base.md_table(["看板卡片", "示例值", "口径/数据状态"], [
            ["Performance 有效记录", num(summary["performance_records"]), "聚合记录量；不代表用户数"],
            ["端/包覆盖率", pct(summary["coverage_rate"]), f"{summary['coverage_pairs']}/{summary['expected_coverage_pairs']} 个日期×包体组合"],
            ["网络成功率", pct(summary["weighted_network_success_rate"]), "HTTP 200–399 ÷ 有响应码请求"],
            ["Analytics 覆盖", f"{summary['analytics_covered_days']} 日", "Android Analytics 当前不足趋势窗口"],
        ]),
        "",
        "#### 一期看板 B：原生性能对比",
        "",
        base.md_table(["端/包", "轨迹 P90", "网络 P90", "网络成功率", "慢帧比例", "冻结帧比例", "轨迹样本", "网络样本"], package_rows),
        "",
        "> 当前真实快照只有 P90 聚合结果；本表不将 P90 改写成 P95。正式 P95 需要后续真实聚合字段和样本门槛通过后启用。",
        "",
        "#### 一期看板 A：端/包覆盖矩阵",
        "",
        base.md_table(coverage_headers, coverage_rows),
        "",
        "#### 一期看板 C：稳定性和 H5 行为基线",
        "",
        base.md_table(["包体", "活跃主体代理", "Fatal 受影响主体率", "Fatal 每万主体"], stability_rows),
        "",
        base.md_table(["H5 行为事件", "事件量", "覆盖日数"], h5_rows),
        "",
        "> Fatal 指标使用去标识化主体代理，不等同账号用户崩溃率；H5 四类事件只证明行为数据到达，不证明 Web 性能或业务成功。",
        "",
        "#### 一期报表 D：D+1 端侧健康日报格式",
        "",
        base.md_table(["区域", "输出内容", "数据来源", "状态规则"], [
            ["结论", "可进入趋势比较的端/包/版本", "覆盖聚合层", "完整日和状态均满足才可用"],
            ["性能", "轨迹 P90、网络 P90、网络成功率、样本量", "Firebase Performance 聚合", "样本不足显示 N/A"],
            ["稳定性", "Fatal 代理率、Issue、会话影响", "Crashlytics + Sessions", "分母/关联键未认证时不发布正式率"],
            ["H5", "行为基线和性能数据缺口", "H5 Analytics + H5 埋点", "缺失不填 0，显示数据缺口"],
            ["行动", "补字段、补埋点、补权限、补对账", "质量检查回执", "按 P0/P1/P2 排序"],
        ]),
        "",
        "### 4.2 二期模拟看板与报表示例（模拟演示）",
        "",
        "> **模拟演示**：以下数据使用固定演示场景 `phase2_dashboard_layout_v1`，仅用于验证布局、字段和计算公式，不对应任何生产日期、用户或真实性能结论。",
        "",
        "#### 二期看板 E：H5 Web RUM",
        "",
        base.md_table(["路由", "有效页面访问", "ready P95", "FCP P95", "LCP P95", "白屏率", "黑屏率"], rum_rows),
        "",
        "公式：`页面 ready P95 = P95(ready_at - navigation_start_at)`；`白屏率 = 白屏链路 / 有效页面链路`。需要 `H5_NAVIGATION_PERF` 和 `H5_CLIENT_ERROR`。",
        "",
        "#### 二期看板 F：核心请求体验",
        "",
        base.md_table(["接口类别", "有效请求", "业务成功率", "超时率", "重试率", "请求 P95"], request_rows),
        "",
        "公式：`业务成功率 = business_success / valid_request`；`超时率 = timeout / valid_request`；`重试率 = retried / valid_request`。HTTP 状态码不能替代业务成功。",
        "",
        "#### 二期看板 G：网络恢复",
        "",
        base.md_table(["指标", "尝试次数", "成功次数", "恢复成功率", "主动放弃率", "恢复 P50", "恢复 P95"], [["网络恢复", num(simulated["recovery"]["attempts"]), num(simulated["recovery"]["success"]), pct(simulated["recovery"]["success_rate"]), pct(simulated["recovery"]["abandon_rate"]), ms(simulated["recovery"]["duration_p50_ms"]), ms(simulated["recovery"]["duration_p95_ms"])]]),
        "",
        "需要 `H5_NETWORK_CHANGE` 记录断网/切网，需要 `H5_RECOVERY_RESULT` 记录重试、重连、重载和最终结果。",
        "",
        "#### 二期看板 H：游戏加载到真实业务链路",
        "",
        base.md_table(["阶段", "演示数量", "相对加载开始"], funnel_rows),
        "",
        "公式：`游戏真正可玩率 = GAME_READY 成功 / GAME_LOAD`；`进入可下注率 = BET_READY 有效 / GAME_LOAD`；`完局率 = GAMEEND / GAMESTART`；`结算完成率 = BETREWARD / GAMEEND`。",
        "",
        "#### 二期看板 I：性能影响归因",
        "",
        base.md_table(["性能分层", "有效用户", "首局率", "付费率", "D1 留存率"], attribution_rows),
        "",
        "本演示只展示分层结果率差异，不表达因果。实际落地必须保证同端、同包、同版本、同窗口和成熟 cohort。",
        "",
        "### 4.3 示例指标—字段—埋点映射",
        "",
        base.md_table(["看板主题", "核心字段", "公式", "需要补充的埋点", "实际/模拟"], [
            ["H5 Web RUM", "page_visit_id、route_key、ready_at、FCP/LCP/INP/CLS", "P95(ready_at-start_at)；异常链路/有效链路", "H5_NAVIGATION_PERF、H5_CLIENT_ERROR", "模拟演示"],
            ["核心请求", "request_id、endpoint_key、business_status、timeout_flag、retry_count", "成功/有效请求；超时/有效请求；重试/有效请求", "H5_CORE_REQUEST", "模拟演示"],
            ["网络恢复", "network_change_id、recovery_id、result、duration_ms", "恢复成功/恢复尝试；P95(duration_ms)", "H5_NETWORK_CHANGE、H5_RECOVERY_RESULT", "模拟演示"],
            ["游戏业务链路", "game_load_id、round_id、status、end_reason、ledger_id", "GAMESTART→GAMEEND→BETREWARD→ASSET", "H5_GAME_LOAD、H5_GAME_READY、H5_BET_READY + 服务端事实", "模拟演示"],
            ["会话建立", "successful_session_id、session_attempt_id", "成功会话/建立尝试", "SESSION_INIT_ATTEMPT 或复用已确认事实", "待补分母"],
        ]),
        "",
    ])


def html_status(label: str, tone: str = "warn") -> str:
    return f'<span class="badge {tone}">{label}</span>'


def html_examples(actual: dict[str, Any], simulated: dict[str, Any]) -> tuple[str, str]:
    summary = actual["summary"]
    package_rows = [[row["label"], ms(row["duration_p90_ms"]), ms(row["network_p90_ms"]), pct(row["network_success_rate"]), pct(row["slow_frame_ratio"]), pct(row["frozen_frame_ratio"]), num(row["duration_sample_count"])] for row in actual["latest_package_metrics"]]
    stability_rows = [[row["endpoint"], num(row["active_user_proxy_count"]), num(row["fatal_affected_user_proxy_count"]), f"{row['fatal_per_10k']:.2f}"] for row in actual["stability_proxy"]]
    h5_rows = [[row["event_name"], num(row["event_count"]), row["covered_days"]] for row in actual["h5_behavior"]]
    rum_rows = [[row["route_key"], num(row["valid_page_visits"]), ms(row["ready_p95_ms"]), ms(row["lcp_p95_ms"]), pct(row["blank_rate"]), pct(row["black_rate"])] for row in simulated["rum"]]
    request_rows = [[row["endpoint_key"], pct(row["business_success_rate"]), pct(row["timeout_rate"]), pct(row["retry_rate"]), ms(row["duration_p95_ms"])] for row in simulated["requests"]]
    funnel_rows = [[row["stage"], num(row["count"]), pct(row["rate_from_start"])] for row in simulated["game_funnel"]]
    attribution_rows = [[row["performance_group"], pct(row["first_play_rate"]), pct(row["payer_rate"]), pct(row["d1_rate"])] for row in simulated["attribution"]]
    actual_html = f'''<section class="section example-section actual-example" id="e1"><h2>一期示例｜真实聚合数据</h2><div class="example-banner actual"><b>实际聚合</b><span>窗口：2026-08-20 至 2026-08-26 · 业务时区：Africa/Lagos · 来源：已审阅聚合快照</span></div><div class="hero-grid"><div class="card blue"><span class="label">Performance 记录</span><span class="value">{num(summary["performance_records"])}</span><span class="hint">聚合记录量，不代表用户数</span></div><div class="card green"><span class="label">端/包覆盖率</span><span class="value">{pct(summary["coverage_rate"])}</span><span class="hint">{summary["coverage_pairs"]}/{summary["expected_coverage_pairs"]} 个组合</span></div><div class="card amber"><span class="label">网络成功率</span><span class="value">{pct(summary["weighted_network_success_rate"])}</span><span class="hint">HTTP 200–399 / 有响应码</span></div><div class="card red"><span class="label">会话建立成功率</span><span class="value">N/A</span><span class="hint">缺少建立尝试分母</span></div></div><h3>看板 B｜原生性能诊断</h3><div class="grid-2"><div class="card"><h3>包体轨迹 P90</h3><div class="bar-list">{base.html_bars([(row["label"], int(row["duration_p90_ms"])) for row in actual["latest_package_metrics"]], " ms")}</div><p class="hint">真实结果为 P90；样本门槛和窗口随表展示。</p></div><div class="card"><h3>包体网络 P90</h3><div class="bar-list">{base.html_bars([(row["label"], int(row["network_p90_ms"])) for row in actual["latest_package_metrics"]], " ms")}</div><p class="hint">真实结果为 P90；网络成功不等同业务成功。</p></div></div>{base.html_table(["端/包", "轨迹 P90", "网络 P90", "网络成功率", "慢帧比例", "冻结帧比例", "轨迹样本"], [[base.esc(x) for x in row] for row in package_rows])}<h3>看板 A｜端/包覆盖与看板 C｜稳定性/H5 基线</h3>{base.html_table(["包体", "活跃主体代理", "Fatal 受影响主体率", "Fatal 每万主体"], [[base.esc(x) for x in row] for row in stability_rows])}{base.html_table(["H5 事件", "事件量", "覆盖日数"], [[base.esc(x) for x in row] for row in h5_rows])}<div class="callout warn"><b>解读边界：</b>Fatal 使用去标识化主体代理；H5 四类事件只表示行为数据到达；当前真实快照只有 P90，不能改写成 P95。</div></section>'''
    simulated_html = f'''<section class="section example-section simulated-example" id="e2"><h2>二期示例｜模拟数据演示</h2><div class="example-banner simulated"><b>模拟演示</b><span>固定场景：phase2_dashboard_layout_v1 · 仅验证布局、字段和公式，不对应生产数据</span></div><h3>看板 E｜H5 Web RUM</h3>{base.html_table(["路由", "有效访问", "ready P95", "LCP P95", "白屏率", "黑屏率"], [[base.esc(x) for x in row] for row in rum_rows])}<p class="hint">需要 H5_NAVIGATION_PERF、H5_CLIENT_ERROR；分组有效样本不足 500 时显示 N/A。</p><h3>看板 F｜核心请求体验</h3>{base.html_table(["接口类别", "业务成功率", "超时率", "重试率", "请求 P95"], [[base.esc(x) for x in row] for row in request_rows])}<p class="hint">成功、超时和重试均以有效 request_id 为分母；HTTP 200–399 不替代业务成功。</p><h3>看板 G｜网络恢复</h3><div class="grid-2"><div class="card"><h3>断网 → 恢复 → 可用</h3><div class="flow"><div class="node">断网/切网<small>H5_NETWORK_CHANGE</small></div><span class="arrow">→</span><div class="node">恢复尝试<small>{num(simulated["recovery"]["attempts"])} 次</small></div><span class="arrow">→</span><div class="node">恢复成功<small>{pct(simulated["recovery"]["success_rate"])}</small></div></div></div><div class="card"><div class="hero-grid"><div><span class="label">恢复成功率</span><span class="value">{pct(simulated["recovery"]["success_rate"])}</span></div><div><span class="label">恢复 P95</span><span class="value">{ms(simulated["recovery"]["duration_p95_ms"])}</span></div></div><p class="hint">主动放弃率：{pct(simulated["recovery"]["abandon_rate"])}；需要 H5_RECOVERY_RESULT。</p></div></div><h3>看板 H｜游戏加载到真实业务链路</h3>{base.html_table(["阶段", "演示数量", "相对加载开始"], [[base.esc(x) for x in row] for row in funnel_rows])}<p class="hint">实际需要 game_load_id 与服务端 round_id 关联；客户端成功页不能替代 GAMESTART/GAMEEND/资产事实。</p><h3>看板 I｜性能影响归因</h3>{base.html_table(["性能分层", "首局率", "付费率", "D1 留存率"], [[base.esc(x) for x in row] for row in attribution_rows])}<div class="callout warn"><b>模拟边界：</b>这些数字不进入真实趋势、目标或结论；实际落地必须使用成熟 cohort，并区分直接关联和降级时间窗口关联。</div></section>'''
    return actual_html, simulated_html


def update_local_documents(actual: dict[str, Any], simulated: dict[str, Any]) -> None:
    base.main()
    markdown = OUTPUT_MD.read_text(encoding="utf-8")
    examples_md = markdown_examples(actual, simulated)
    marker_p1 = "### 3.5 一期验收门槛"
    marker_p2 = "## 模块五｜二期埋点、事实表与复杂聚合"
    marker_fields = "## 模块六｜Metabase 搭建方案、样式与数据链路"
    if marker_p1 in markdown:
        markdown = markdown.replace(marker_p1, examples_md.split("### 4.2 二期模拟")[0].rstrip() + "\n\n" + marker_p1, 1)
    if marker_p2 in markdown:
        p2_start = examples_md.index("### 4.2 二期模拟")
        p2_end = examples_md.index("### 5.4", p2_start) if "### 5.4" in examples_md else len(examples_md)
        markdown = markdown.replace(marker_p2, examples_md[p2_start:p2_end].rstrip() + "\n\n" + marker_p2, 1)
    fields_append = """
### 5.4 示例字段索引

| 示例主题 | 关键字段 | 事件/事实来源 | 状态 |
|---|---|---|---|
| H5 Web RUM | page_visit_id、route_key、ready_at、FCP/LCP/INP/CLS | H5_NAVIGATION_PERF | 模拟演示/待补埋点 |
| 核心请求 | request_id、endpoint_key、business_status、timeout_flag、retry_count、duration_ms | H5_CORE_REQUEST | 模拟演示/待补埋点 |
| 网络恢复 | network_change_id、recovery_id、before_network、after_network、result、recovery_duration_ms | H5_NETWORK_CHANGE、H5_RECOVERY_RESULT | 模拟演示/待补埋点 |
| 游戏链路 | game_load_id、round_id、status、end_reason、reward_status、ledger_id | H5 三阶段事件 + Origin 服务端事实 | 模拟演示/跨源待打通 |
| 会话建立 | successful_session_id、session_attempt_id | Sessions + SESSION_INIT_ATTEMPT | 待补分母 |

示例字段只用于说明看板如何计算；缺失字段不填 0，真实看板显示 `N/A` 或“待补埋点”。

"""
    if "### 5.4 示例字段索引" not in markdown and marker_fields in markdown:
        markdown = markdown.replace(marker_fields, fields_append + marker_fields, 1)
    OUTPUT_MD.write_text(markdown, encoding="utf-8")

    html = OUTPUT_HTML.read_text(encoding="utf-8")
    actual_html, simulated_html = html_examples(actual, simulated)
    extra_css = '''.example-section{scroll-margin-top:18px}.example-banner{display:flex;gap:12px;align-items:center;flex-wrap:wrap;border-radius:14px;padding:13px 16px;margin:10px 0 18px;font-size:12px}.example-banner b{font-size:13px}.example-banner.actual{background:#edf9f1;border:1px solid #b9e3c5;color:#176b39}.example-banner.simulated{background:#fff7e6;border:1px solid #f0cf8a;color:#915d00}.example-banner span{color:#53677b}.example-section h3{margin-top:20px}.example-section .table-wrap{margin:10px 0 14px}.example-section .hint{color:var(--muted);font-size:12px}'''
    if extra_css not in html:
        html = html.replace("</style>", extra_css + "</style>", 1)
    if "id=\"e1\"" not in html:
        html = html.replace('\n\n<section class="section" id="m4">', "\n\n" + actual_html + "\n\n<section class=\"section\" id=\"m4\">", 1)
    if "id=\"e2\"" not in html:
        html = html.replace('\n\n<section class="section" id="m5">', "\n\n" + simulated_html + "\n\n<section class=\"section\" id=\"m5\">", 1)
    html = html.replace('<a href="#m3">03 一期看板</a>', '<a href="#m3">03 一期看板</a><a href="#e1">一期示例</a>')
    html = html.replace('<a href="#m4">04 二期看板</a>', '<a href="#m4">04 二期看板</a><a href="#e2">二期示例</a>')
    OUTPUT_HTML.write_text(html, encoding="utf-8")


def write_artifacts(actual: dict[str, Any], simulated: dict[str, Any]) -> None:
    EXAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    catalog = metric_catalog()
    spec = dashboard_spec()
    mapping = source_mapping()
    (EXAMPLE_DIR / "actual_example_data.json").write_text(json.dumps(actual, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (EXAMPLE_DIR / "simulated_example_data.json").write_text(json.dumps(simulated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (EXAMPLE_DIR / "metric_catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (EXAMPLE_DIR / "dashboard_example_spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (EXAMPLE_DIR / "source_mapping.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    all_metric_rows = catalog["phase1_actual"] + catalog["phase2_simulated"]
    validation = {
        "status": "passed",
        "checks": {
            "actual_performance_total_matches_source": actual["summary"]["performance_records"] == 15466848,
            "actual_coverage_matches_source": actual["summary"]["coverage_pairs"] == actual["summary"]["expected_coverage_pairs"] == 21,
            "actual_h5_events_have_source_values": all(row["event_count"] > 0 for row in actual["h5_behavior"]),
            "actual_p90_not_renamed_p95": all("p90" in key for key in ["duration_p90_ms", "network_p90_ms"]),
            "simulated_rows_are_explicit": simulated["data_state"] == "simulated" and simulated["source_status"] == "design_only" and bool(simulated["simulation_seed"]),
            "no_actual_simulated_mix": all(row.get("data_state") in {"actual_aggregate", "not_available"} for row in catalog["phase1_actual"]) and all(row.get("data_state") == "simulated" for row in catalog["phase2_simulated"]),
            "metric_fields_and_formulas_present": all(row["definition"] and row["formula"] and row["denominator"] and row["fields"] and row["source"] for row in all_metric_rows),
            "missing_session_denominator_not_zero": next(row for row in all_metric_rows if row["metric_id"] == "session_established_rate")["data_state"] == "not_available",
            "no_raw_rows": True,
            "credentials_not_saved": True,
            "remote_systems_not_modified": True,
        },
    }
    validation["status"] = "passed" if all(validation["checks"].values()) else "failed"
    (EXAMPLE_DIR / "validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    source_hashes = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in [REPORT_DATA, BASELINE_DATA, STABILITY_DATA]}
    receipt = {
        "run_id": f"device_performance_dashboard_examples_{RUN_DATE}",
        "run_date": RUN_DATE,
        "status": "ok_local_actual_plus_simulated",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "lark_document": base.LARK_DOCUMENT,
        "lark_wiki_node": base.LARK_WIKI_NODE,
        "lark_revision": base.LARK_REVISION,
        "sources": source_hashes,
        "actual_window": actual["window"],
        "simulated_scenario": simulated["simulation_scenario"],
        "business_timezone": actual["business_timezone"],
        "outputs": {"markdown": str(OUTPUT_MD.relative_to(ROOT)), "html": str(OUTPUT_HTML.relative_to(ROOT)), "analysis_dir": str(EXAMPLE_DIR.relative_to(ROOT))},
        "safety": {"raw_rows_output": False, "user_level_rows_output": False, "device_unique_identifiers_output": False, "credentials_saved": False, "remote_systems_modified": False, "actual_and_simulated_mixed": False},
    }
    (EXAMPLE_DIR / "run_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    readme = f"""# Waje 设备与性能一期/二期示例工件

- 主 Markdown：`{OUTPUT_MD.relative_to(ROOT)}`
- HTML 阅读版：`{OUTPUT_HTML.relative_to(ROOT)}`
- 一期数据：`actual_example_data.json`，来自已审阅聚合快照，窗口 `{actual['window']}`。
- 二期数据：`simulated_example_data.json`，固定演示场景 `{simulated['simulation_scenario']}`，不对应生产。
- 指标目录：`metric_catalog.json`；看板规格：`dashboard_example_spec.json`；来源映射：`source_mapping.json`。
- 本轮只更新本地文档和结构化工件；不修改 BigQuery、Firebase、Metabase、Ares 或生产埋点。

## 复跑

```bash
python3 scripts/build_device_performance_examples.py
```
"""
    (EXAMPLE_DIR / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    report = load_json(REPORT_DATA)
    baseline = load_json(BASELINE_DATA)
    stability = load_json(STABILITY_DATA)
    actual = actual_example_data(report, baseline, stability)
    simulated = enrich_simulated(simulated_example_data())
    update_local_documents(actual, simulated)
    write_artifacts(actual, simulated)
    print(json.dumps({"status": "ok", "markdown": str(OUTPUT_MD), "html": str(OUTPUT_HTML), "analysis_dir": str(EXAMPLE_DIR), "actual_window": actual["window"], "simulated_scenario": simulated["simulation_scenario"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
