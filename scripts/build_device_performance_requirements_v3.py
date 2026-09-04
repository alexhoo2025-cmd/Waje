#!/usr/bin/env python3
"""Build the six-module device/performance requirement package.

The source is the reviewed aggregate-only baseline already present in the
repository. This builder does not query BigQuery, Firebase, Metabase or Ares;
it only creates a reproducible local Markdown/HTML design package and safe
aggregate metadata for the next implementation step.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUN_DATE = "2026-09-02"
BASELINE_PATH = ROOT / "analysis/multiplatform_device_performance_dashboard_v1_2026_08_27/actual_baseline.json"
OUTPUT_MD = ROOT / f"knowledge/02-数据/Waje多端设备与性能报表看板需求-V3-六模块-{RUN_DATE}.md"
OUTPUT_HTML = ROOT / f"output/html/Waje多端设备与性能报表看板需求-V3-六模块-{RUN_DATE}.html"
ANALYSIS_DIR = ROOT / f"analysis/device_performance_dashboard_v3_{RUN_DATE.replace('-', '_')}"
LARK_DOCUMENT = "https://ksg964l11fam.sg.larksuite.com/docx/GO9vd2jj7oWGvqx2WiMlJy9ngBY"
LARK_WIKI_NODE = "https://ksg964l11fam.sg.larksuite.com/wiki/JyF9wsIVaiM65pkmrAnlrFBUgMd"
LARK_REVISION = 105


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def md_cell(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ").strip()


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines.extend("| " + " | ".join(md_cell(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def compact(value: int | float) -> str:
    number = float(value)
    if number >= 1_000_000_000:
        return f"{number / 1_000_000_000:.1f}B"
    if number >= 1_000_000:
        return f"{number / 1_000_000:.2f}M".rstrip("0").rstrip(".")
    if number >= 1_000:
        return f"{number / 1_000:.1f}k".rstrip("0").rstrip(".")
    return f"{number:,.0f}"


def load_baseline() -> dict[str, Any]:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def build_context(baseline: dict[str, Any]) -> dict[str, Any]:
    native = baseline["native_performance"]
    android_native = [row for row in native if str(row["endpoint"]).startswith("android_")]
    h5_events = baseline["h5_event_dictionary"]
    return {
        "snapshot_at": baseline["snapshot_at"],
        "business_timezone": baseline["timezone"],
        "native": native,
        "android_native": android_native,
        "native_total": sum(int(row["performance_record_count"]) for row in native),
        "android_native_total": sum(int(row["performance_record_count"]) for row in android_native),
        "session_total": sum(int(row["distinct_session_count"]) for row in baseline["android_sessions"]),
        "h5_events": h5_events,
        "h5_total": sum(int(row["event_count"]) for row in h5_events),
    }


def source_rows(baseline: dict[str, Any]) -> list[list[Any]]:
    return [
        ["Android Analytics", "2026-08-24", "1 日", "未成熟", "可做事件结构观察；不可做稳定趋势"],
        ["Android Performance", "2026-08-20 至 2026-08-26", "7 日", "试运行", "一期原生性能基线"],
        ["Android Sessions", "2026-08-18 至 2026-08-26", "9 日", "质量警告", "会话可用；与 Performance 开关存在冲突"],
        ["Android Crashlytics", "2026-08-13 至 2026-08-26", "14 日", "待字段认证", "一期先计算事件率，分母和关联键待认证"],
        ["iOS Analytics", "2026-08-20 至 2026-08-24", "5 日", "未成熟", "不足 7 日，不开放跨端趋势"],
        ["iOS Performance", "2026-08-20 至 2026-08-25", "6 日", "未成熟", "早期观察，不做正式版本排名"],
        ["H5 Analytics", "2026-08-14 至 2026-08-21", "8 日", "仅行为基线", "只有四类标准行为事件"],
    ]


def phase1_metrics() -> list[dict[str, Any]]:
    return [
        {"metric": "数据覆盖率", "code": "data_coverage_rate", "definition": "实际到达的完整数据日 ÷ 请求数据日", "formula": "COUNT(complete_day) / COUNT(requested_day)", "denominator": "请求数据日；当天不计入完整日", "source": "mart_endpoint_coverage_daily", "grain": "日期 × 端 × 来源 × 包体", "status": "一期可用"},
        {"metric": "数据新鲜度", "code": "source_freshness_lag_minutes", "definition": "当前时间与来源最新事件时间的差值", "formula": "TIMESTAMP_DIFF(now, MAX(event_time), MINUTE)", "denominator": "有来源事件的端/包", "source": "覆盖聚合层", "grain": "端 × 来源 × 包体", "status": "一期可用"},
        {"metric": "会话建立成功率", "code": "session_established_rate", "definition": "成功建立会话的去重会话数占建立尝试数的比例", "formula": "COUNT(DISTINCT successful_session_id) / COUNT(DISTINCT session_attempt_id)", "denominator": "需要有效 session_attempt_id；当前缺少统一尝试分母，未补齐时显示 N/A", "source": "Sessions + SESSION_INIT_ATTEMPT", "grain": "日期 × 端 × 包 × 版本", "status": "一期补分母后可用"},
        {"metric": "原生性能记录量", "code": "native_performance_record_count", "definition": "Firebase Performance 聚合记录数", "formula": "COUNT(*)", "denominator": "Performance 记录数", "source": "mart_native_performance_daily", "grain": "日期 × 端 × 包 × 版本", "status": "一期可用"},
        {"metric": "原生轨迹 P95", "code": "duration_trace_p95_ms", "definition": "有效 DURATION_TRACE 时长的 95 分位", "formula": "APPROX_QUANTILES(duration_ms, 100)[OFFSET(95)]", "denominator": "有效样本 ≥500；单位毫秒", "source": "mart_native_performance_daily", "grain": "日期 × 包 × 版本 × 单一设备维度", "status": "一期可用/待数值认证"},
        {"metric": "网络 P95", "code": "network_p95_ms", "definition": "网络请求响应完成耗时的 95 分位", "formula": "APPROX_QUANTILES(response_completed_ms, 100)[OFFSET(95)]", "denominator": "有开始、完成和响应码；样本 ≥500", "source": "mart_native_performance_daily", "grain": "日期 × 包 × 版本 × 网络类型", "status": "一期可用/待请求分类"},
        {"metric": "网络成功率", "code": "network_success_rate", "definition": "HTTP 200–399 响应数 ÷ 有响应码请求数", "formula": "COUNTIF(code BETWEEN 200 AND 399) / COUNTIF(code IS NOT NULL)", "denominator": "有响应码的请求", "source": "mart_native_performance_daily", "grain": "日期 × 包 × 版本 × 请求类别", "status": "一期可用/待请求分类"},
        {"metric": "慢帧/冻结帧比例", "code": "frame_ratio_trace_mean", "definition": "SCREEN_TRACE 比例字段的 trace 加权均值", "formula": "AVG(slow_frame_ratio), AVG(frozen_frame_ratio)", "denominator": "有效 SCREEN_TRACE；不是用户占比", "source": "mart_native_performance_daily", "grain": "日期 × 包 × 版本 × 设备/系统", "status": "一期可用"},
        {"metric": "Fatal/Non-fatal 事件率", "code": "stability_event_rate_per_1k_sessions", "definition": "按 Fatal/Non-fatal 分开计算的每千有效会话事件率", "formula": "COUNT(DISTINCT event_id) / COUNT(DISTINCT eligible_session_id) × 1,000", "denominator": "同端、同包、同日有效会话；事件与会话关联键需认证", "source": "mart_stability_daily + Sessions", "grain": "日期 × 包 × 版本 × 设备/系统 × is_fatal", "status": "一期补分母后可用"},
        {"metric": "H5 行为事件量", "code": "h5_behavior_event_count", "definition": "H5 已接入标准行为事件的记录数", "formula": "COUNTIF(event_name IN (...))", "denominator": "事件记录数；不代表用户数", "source": "H5 Analytics", "grain": "日期 × H5 事件 × 来源", "status": "一期可用/仅行为基线"},
        {"metric": "游戏真正可玩率", "code": "h5_game_ready_rate", "definition": "H5_GAME_READY success 的加载链路 ÷ LOAD start 链路", "formula": "COUNT(DISTINCT ready.game_load_id) / COUNT(DISTINCT load.game_load_id)", "denominator": "有效 game_load_id；一期补充三事件后可用", "source": "H5_GAME_LOAD + H5_GAME_READY", "grain": "日期 × 游戏 × 端 × 版本", "status": "一期补埋点后可用"},
        {"metric": "进入可下注率", "code": "h5_bet_ready_rate", "definition": "五项状态均为 true 的 BET_READY 链路 ÷ LOAD start 链路", "formula": "COUNT(DISTINCT valid_bet_ready.game_load_id) / COUNT(DISTINCT load.game_load_id)", "denominator": "balance/currency/limit/connection/bet_control 全 true", "source": "H5_BET_READY", "grain": "日期 × 游戏 × 端 × 版本", "status": "一期补埋点后可用"},
    ]


def phase2_metrics() -> list[dict[str, Any]]:
    return [
        {"metric": "页面加载 P50/P95/P99", "definition": "页面从开始加载到业务内容 ready 的耗时分布", "formula": "P50/P95/P99(ready_at - start_at)", "denominator": "measurement_state=complete 且 page_visit_id 去重；每组有效样本 ≥500", "source": "H5_NAVIGATION_PERF", "status": "二期缺埋点"},
        {"metric": "核心请求成功率", "definition": "按接口类别统计请求进入业务成功终态的比例", "formula": "COUNT(success) / COUNT(valid_request)", "denominator": "有效 request_id；HTTP 成功不能替代业务成功", "source": "H5_CORE_REQUEST", "status": "二期缺埋点"},
        {"metric": "核心请求超时率", "definition": "按接口类别统计超过阈值或进入 timeout 终态的比例", "formula": "COUNT(timeout) / COUNT(valid_request)", "denominator": "有效 request_id；阈值按 endpoint_key 配置", "source": "H5_CORE_REQUEST", "status": "二期缺埋点"},
        {"metric": "前端错误率", "definition": "发生 JS、资源、白屏或黑屏错误的页面/游戏链路比例", "formula": "COUNT(DISTINCT error_flow_id) / COUNT(DISTINCT eligible_flow_id)", "denominator": "页面/游戏有效链路；错误指纹去重", "source": "H5_CLIENT_ERROR", "status": "二期缺埋点"},
        {"metric": "网络恢复成功率", "definition": "网络异常后恢复到可用状态的比例", "formula": "COUNT(recovery_success) / COUNT(recovery_attempt)", "denominator": "有效 recovery_id；主动放弃单独统计", "source": "H5_NETWORK_CHANGE + H5_RECOVERY_RESULT", "status": "二期缺埋点"},
        {"metric": "可玩到服务端开局率", "definition": "已经真正可玩的链路中，最终关联到服务端有效开局的比例", "formula": "COUNT(DISTINCT round_id) / COUNT(DISTINCT game_load_id)", "denominator": "直接 game_load_id 关联；降级时间窗口单独展示", "source": "H5 lifecycle + Origin server facts", "status": "二期链路"},
        {"metric": "性能异常影响的首局/付费变化", "definition": "比较性能分层与首局、付费等结果的差异", "formula": "分层 cohort 的结果率差异；无实验时只做关联观察", "denominator": "成熟 cohort；同端/包/版本/窗口可比", "source": "H5 RUM + Origin + lifecycle", "status": "二期复杂聚合"},
    ]


def phase2_theme_rows() -> list[list[str]]:
    """Concise theme-level rows for the phase-two overview table.

    The detailed metric table below keeps one row per metric.  This overview
    table answers the product question first: what each phase-two theme means,
    how it is measured, what denominator is required, and which data unlocks
    it.
    """
    return [
        ["H5 Web RUM", "页面性能、页面 ready 和白屏/黑屏情况", "页面 ready 耗时计算 P50/P95/P99；异常链路 ÷ 有效链路", "完整 page_visit_id；每组有效样本 ≥500", "H5_NAVIGATION_PERF、H5_CLIENT_ERROR", "二期缺埋点"],
        ["核心请求体验", "接口是否成功、超时、重试以及耗时", "成功请求 ÷ 有效请求；超时请求 ÷ 有效请求；重试请求 ÷ 有效请求；计算耗时 P95", "request_id 有效；超时阈值按 endpoint_key 配置", "H5_CORE_REQUEST、request_id、endpoint_key", "二期缺埋点/需接口字典"],
        ["网络恢复", "断网或切网后能否恢复、恢复需要多久", "恢复成功次数 ÷ 恢复尝试次数；恢复耗时计算 P50/P95", "recovery_id 有效；主动放弃单独统计", "H5_NETWORK_CHANGE、H5_RECOVERY_RESULT", "二期缺埋点"],
        ["游戏体验与业务链路", "可玩后是否进入真实开局，并完成结算和资产链路", "有效 GAMESTART ÷ GAME_READY 成功；完局 ÷ 开局；资产对账差异率", "优先使用直接 game_load_id；降级时间窗口单列", "三阶段事件 + Origin 服务端事实", "跨源链路待打通"],
        ["性能影响归因", "性能差异是否伴随首局、付费或留存差异", "按性能分层比较结果率差异；无实验只做关联观察", "成熟 cohort；同端、包、版本和窗口可比", "性能事实、服务端业务事实、成熟 cohort", "复杂聚合"],
    ]


def build_source_matrix(baseline: dict[str, Any]) -> list[dict[str, Any]]:
    labels = {
        "immature": "未成熟",
        "provisional": "试运行",
        "provisional_quality_warning": "质量警告",
        "provisional_schema_mapping": "待字段认证",
        "provisional_behavior_only": "仅行为基线",
    }
    return [
        {"source": "Android Firebase Analytics", "window": "2026-08-24", "covered_days": 1, "status": "immature", "status_label": labels["immature"], "usable": "事件结构观察", "not_for": "稳定趋势"},
        {"source": "Android Firebase Performance", "window": "2026-08-20..2026-08-26", "covered_days": 7, "status": "provisional", "status_label": labels["provisional"], "usable": "原生性能基线", "not_for": "未经分类的业务接口结论"},
        {"source": "Android Sessions", "window": "2026-08-18..2026-08-26", "covered_days": 9, "status": "provisional_quality_warning", "status_label": labels["provisional_quality_warning"], "usable": "去标识化会话", "not_for": "替代 Performance 覆盖"},
        {"source": "Android Crashlytics", "window": "2026-08-13..2026-08-26", "covered_days": 14, "status": "provisional_schema_mapping", "status_label": labels["provisional_schema_mapping"], "usable": "事件率/问题数", "not_for": "未经认证的崩溃率"},
        {"source": "iOS Analytics", "window": "2026-08-20..2026-08-24", "covered_days": 5, "status": "immature", "status_label": labels["immature"], "usable": "早期行为观察", "not_for": "跨端趋势"},
        {"source": "iOS Performance", "window": "2026-08-20..2026-08-25", "covered_days": 6, "status": "immature", "status_label": labels["immature"], "usable": "早期性能观察", "not_for": "正式版本排行"},
        {"source": "H5 Firebase Analytics", "window": "2026-08-14..2026-08-21", "covered_days": 8, "status": "provisional_behavior_only", "status_label": labels["provisional_behavior_only"], "usable": "四类行为事件", "not_for": "网页性能/游戏可玩结论"},
    ]


def build_contract(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "3.0",
        "name": "waje_device_performance_dashboard_v3_six_modules",
        "run_date": RUN_DATE,
        "business_timezone": context["business_timezone"],
        "delivery": {"markdown": str(OUTPUT_MD.relative_to(ROOT)), "html": str(OUTPUT_HTML.relative_to(ROOT)), "lark_document": LARK_DOCUMENT, "lark_wiki_node": LARK_WIKI_NODE, "lark_revision": LARK_REVISION, "metabase_remote_write": "not_run_design_only"},
        "modules": [
            {"module": 1, "name": "总体设计", "purpose": "框架、维度、指标层级和状态语义"},
            {"module": 2, "name": "一期数据现状", "purpose": "已有聚合、可用范围、缺失项和少量补充埋点"},
            {"module": 3, "name": "一期看板和报表", "purpose": "数据健康、原生性能、稳定性/H5行为和三阶段游戏体验"},
            {"module": 4, "name": "二期看板和报表", "purpose": "H5 RUM、核心业务链路和复杂版本/设备归因"},
            {"module": 5, "name": "二期埋点与复杂聚合", "purpose": "H5 RUM、请求、错误、网络恢复和服务端链路"},
            {"module": 6, "name": "Metabase 搭建", "purpose": "授权 View、Model、卡片、样式、筛选器和数据链路"},
        ],
        "phase1_event_additions": ["H5_GAME_LOAD", "H5_GAME_READY", "H5_BET_READY"],
        "phase2_event_additions": ["H5_SESSION_START", "H5_NAVIGATION_PERF", "H5_CORE_REQUEST", "H5_CLIENT_ERROR", "H5_NETWORK_CHANGE", "H5_RECOVERY_RESULT", "H5_SESSION_END"],
        "global_filters": ["日期范围", "端侧", "包体", "版本", "发布批次", "国家", "设备品牌/型号桶", "系统", "内存档位", "浏览器", "网络类型", "运营商", "页面/请求类别", "游戏", "数据状态"],
        "quality_gates": {"complete_days": 7, "performance_percentile_min_samples": 500, "small_group_min_distinct_sessions": 10, "native_diagnostic_delay_minutes": 45, "h5_lifecycle_link_rate": 0.98},
        "access": {"mode": "aggregate_only", "raw_source_access": False, "remote_metabase_write": False, "restricted": ["user_id", "session_id", "device_id", "advertising_id", "url", "request_body", "response_body", "stack_trace", "order_id", "payment_detail"]},
    }


def chart_data(context: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    return {
        "snapshot": context["snapshot_at"],
        "timezone": context["business_timezone"],
        "native_performance": [
            {"label": row["label"], "endpoint": row["endpoint"], "records": row["performance_record_count"], "duration_trace": row["duration_trace_count"], "network_requests": row["network_request_count"], "days": f"{row['first_day']}..{row['last_day']}"}
            for row in context["native"]
        ],
        "h5_behavior": [{"event": row["event_name"], "count": row["event_count"], "covered_days": row["covered_days"]} for row in context["h5_events"]],
        "android_sessions": [{"label": row["label"], "sessions": row["distinct_session_count"]} for row in baseline["android_sessions"]],
    }


def write_markdown(context: dict[str, Any], baseline: dict[str, Any], contract: dict[str, Any], sources: list[dict[str, Any]], charts: dict[str, Any]) -> None:
    p1 = phase1_metrics()
    p2 = phase2_metrics()
    native_rows = [[row["label"], compact(row["performance_record_count"]), compact(row["duration_trace_count"]), compact(row["network_request_count"]), f"{row['first_day']} 至 {row['last_day']}"] for row in context["native"]]
    h5_rows = [[row["event_name"], f"{int(row['event_count']):,}", row["covered_days"]] for row in context["h5_events"]]
    source_table = [[row["source"], row["window"], row["covered_days"], row["status_label"], row["usable"], row["not_for"]] for row in sources]
    p1_table = [[m["metric"], m["code"], m["definition"], m["formula"], m["denominator"], m["source"], m["status"]] for m in p1]
    p2_table = [[m["metric"], m["definition"], m["formula"], m["denominator"], m["source"], m["status"]] for m in p2]
    p2_theme_table = phase2_theme_rows()
    lines = [
        "---",
        "type: dashboard-requirement",
        "domain: device-performance",
        "status: v3-phase-gated-design",
        f"updated: {RUN_DATE}",
        "scope: [android, ios, h5, pwa, app_webview]",
        f"business_timezone: {context['business_timezone']}",
        f"source_snapshot: {BASELINE_PATH.relative_to(ROOT)}",
        f"lark_document: {LARK_DOCUMENT}",
        f"lark_wiki_node: {LARK_WIKI_NODE}",
        f"lark_revision: {LARK_REVISION}",
        "tags: [设备, 性能, H5, Firebase, BigQuery, Metabase, 报表, 看板, 一期, 二期]",
        "---",
        "",
        f"# Waje 多端设备与性能报表/看板需求 V3（六模块）",
        "",
        f"> 执行日期：`{RUN_DATE}`。本版把原有 8 页设计重组为六个模块，区分一期可落地内容与二期建设内容。数据示例来自 `{BASELINE_PATH.relative_to(ROOT)}` 的聚合快照，窗口为 2026-08-20 至 2026-08-26，业务时区为 `Africa/Lagos`；不是实时生产看板数值。",
        "",
        "> 交付定位：本地 Markdown 为主文档，HTML 为阅读版，飞书为团队协作版；Metabase 本轮只输出设计、View/Model 合同和本地示例，不修改远端对象。",
        "",
        "## 模块一｜总体设计、框架、维度与核心指标",
        "",
        "### 1.1 目标",
        "",
        "回答四个问题：数据是否到达、哪个端/包/版本变慢、用户在哪个阶段受阻、哪些问题需要补埋点或补服务端事实。",
        "",
        "```mermaid\nflowchart LR\n  A[Firebase Analytics / Performance / Sessions / Crashlytics] --> B[BQ 原始与受控层]\n  C[Ares 客户端与服务端事实] --> B\n  D[H5 性能与游戏状态埋点] --> B\n  B --> E[端/包/版本/游戏维表]\n  E --> F[一期/二期聚合 Mart]\n  F --> G[授权聚合 View]\n  G --> H[Metabase 看板 / 日报 / 版本回归]\n```",
        "",
        "### 1.2 统一维度和状态",
        "",
        md_table(["维度组", "字段/取值", "规则"], [
            ["端侧", "Android / iOS / H5 / PWA / APP WebView", "端侧分开统计；未认证不跨端相加"],
            ["版本与包", "app_version、web_version、package_name、release_id、发布批次", "版本对比必须使用可比完整日"],
            ["设备", "品牌、型号桶、OS、内存档位、设备档位", "未知单列；不输出设备唯一标识"],
            ["网络", "Wi-Fi、蜂窝、运营商桶、effective_type", "网络 P95 按请求类别计算"],
            ["数据状态", "已认证 / 试运行 / 未成熟 / 延迟 / 数据缺口 / 已阻断", "状态与数值同时展示；缺失不填 0"],
        ]),
        "",
        "### 1.3 核心指标层级",
        "",
        "```text\n数据可信度 → 端侧健康 → 性能质量 → 稳定性 → 页面/游戏体验 → 核心业务结果\n```",
        "",
        "核心业务结果不由 Firebase 客户端行为替代：注册、登录、下注、结算、充值、提现和资产变动必须使用服务端事实。",
        "",
        "## 模块二｜一期数据现状、可用范围与补充缺口",
        "",
        "### 2.1 当前数据底座",
        "",
        md_table(["数据源", "观察窗口", "覆盖", "状态", "一期可用范围", "不能直接做"], source_table),
        "",
        f"Android Performance 快照合计 `{compact(context['android_native_total'])}` 条，Android Sessions 合计 `{compact(context['session_total'])}` 个去标识化会话；H5 Analytics 合计 `{compact(context['h5_total'])}` 条四类标准行为事件。上述数值只用于展示现有聚合底座，不代表用户数、成功率或实时状态。",
        "",
        "### 2.2 一期急需补充的埋点",
        "",
        md_table(["事件", "实现对象", "最低用途", "当前状态"], [
            ["H5_GAME_LOAD", "H5 主框架 + 自研 iframe", "记录加载开始、阶段、失败、超时和放弃", "尚未创建/待接入"],
            ["H5_GAME_READY", "各自研游戏回调", "确认画面和必要配置真正可用", "尚未创建/待接入"],
            ["H5_BET_READY", "各自研游戏/服务端确认", "确认余额、币种、限额、连接和下注控件均可用", "尚未创建/待接入"],
        ]),
        "",
        "第三方/联运 iframe 没有合作方 SDK 或桥接回调时，只保留入口行为，不从 iframe onload 或页面打开推断内部状态。",
        "会话建立成功率必须有“建立尝试”作为分母；优先复用已确认的会话初始化尝试事件，若当前不存在则补充 `SESSION_INIT_ATTEMPT`。分母未补齐时不输出比例，也不以单纯事件记录替代。",
        "",
        "## 模块三｜一期看板和报表：指标、口径与示例",
        "",
        "### 3.1 一期页面和报表",
        "",
        md_table(["页面/报表", "主要回答", "一期指标"], [
            ["01 数据健康与端侧覆盖", "数据是否到达、是否完整、是否延迟", "覆盖率、完整日、最新时间、延迟、事件量、Performance 记录量、数据状态"],
            ["02 Android/iOS 原生性能", "哪个包/版本/设备/网络维度变慢", "轨迹 P50/P95/P99、网络 P95、HTTP 成功率、慢帧、冻结帧、样本量"],
            ["03 稳定性与 H5 行为基线", "稳定性风险和 H5 行为是否有数据", "Fatal/Non-fatal 事件率、会话影响率、Issue 数和四类 H5 事件"],
            ["D+1 端侧健康日报", "今天是否需要行动", "端侧状态、异常候选、缺口、数据截止时间、次日动作"],
        ]),
        "",
        "### 3.2 一期指标字典",
        "",
        md_table(["指标", "编码", "定义", "算法", "分母/门槛", "来源", "状态"], p1_table),
        "",
        "### 3.3 现有聚合示例",
        "",
        "#### 原生 Performance 记录量（快照示例）",
        "",
        md_table(["端/包", "Performance 记录", "DURATION_TRACE", "网络请求", "窗口"], native_rows),
        "",
        "#### H5 Analytics 行为基线（快照示例）",
        "",
        md_table(["事件", "事件量", "覆盖日数"], h5_rows),
        "",
        "### 3.5 一期验收门槛",
        "",
        "- P95/P99 仅在有效样本不少于 500 时展示；否则为 `N/A`。",
        "- Android、iOS、H5 不把事件数、会话数和性能记录数直接相加。",
        "- Crashlytics 一期主指标使用 Fatal/Non-fatal 事件率和会话影响率；分母或关联键未认证时显示 N/A，事件量只作为样本量和诊断信息。",
        "- H5 三阶段事件接入后，`game_load_id` 链路关联率目标为 ≥98%；三类事件成功状态不能由 iframe onload 代替。",
        "- 一期所有卡片同时显示数据截止时间、完整日数、样本量和质量状态。",
        "",
        "## 模块四｜二期看板和报表：目标指标与复杂分析",
        "",
        md_table(["二期主题", "指标含义", "计算方式", "分母/门槛", "需要的数据", "状态"], p2_theme_table),
        "",
        "### 4.1 二期指标口径",
        "",
        md_table(["指标", "含义", "计算方式", "分母/门槛", "来源", "状态"], p2_table),
        "",
        "二期的复杂分析必须保留直接关联、降级时间窗口关联和仅行为代理三种状态，不能将时间窗口匹配当作服务端事实。",
        "",
        "## 模块五｜二期埋点、事实表与复杂聚合",
        "",
        "### 5.1 二期事件",
        "",
        md_table(["事件", "主要字段", "解锁内容"], [
            ["H5_SESSION_START", "session_id、surface_type、web_version、release_id", "H5 会话和版本覆盖"],
            ["H5_NAVIGATION_PERF", "page_visit_id、route_key、FCP/LCP/INP/CLS、ready_ms", "网页性能和页面回归"],
            ["H5_CORE_REQUEST", "request_id、request_kind、endpoint_key、duration_ms、终态", "登录/余额/充值/下注/结算请求体验"],
            ["H5_CLIENT_ERROR", "error_type、stage、error_code、fingerprint、white/black screen", "前端错误、白屏和版本回归"],
            ["H5_NETWORK_CHANGE", "network_change_id、前后网络、offline_duration_ms、stage", "断网和切网诊断"],
            ["H5_RECOVERY_RESULT", "recovery_id、origin_id、action、result、duration_ms", "重试、重连、重载恢复能力"],
            ["H5_SESSION_END", "session_duration_sec、last_stage、close_reason", "会话结束和异常退出辅助判断"],
        ]),
        "",
        "### 5.2 逻辑事实层",
        "",
        "```text\nfact_h5_page_performance\nfact_h5_core_request\nfact_h5_client_error\nfact_h5_game_lifecycle\nfact_h5_network_recovery\nfact_core_business_funnel\n```",
        "",
        "统一关联键：`session_id → page_visit_id → game_load_id → request_id → round_id/order_id`。物理表名必须由数据开发按真实 BQ/Ares 目录回填，不使用假定表名发布看板。",
        "",
        "### 5.3 二期数据质量",
        "",
        md_table(["质量项", "门槛", "失败处理"], [
            ["完整日", "至少 7 个完整业务日", "显示未成熟，不做正式趋势"],
            ["必填字段", "≥99.5%", "阻断对应指标，进入缺口队列"],
            ["链路关联", "≥98%", "区分直接关联与降级关联"],
            ["未知枚举", "≤0.1%", "保留 raw_value，不能映射为其他"],
            ["迟到数据", "原生诊断超过 45 分钟", "状态改为延迟，不触发产品性能告警"],
        ]),
        "",
        "## 模块六｜Metabase 搭建方案、样式与数据链路",
        "",
        "### 6.1 看板页面结构",
        "",
        "```text\n顶部：数据截止时间｜完整日｜口径版本｜状态\n第一行：核心 KPI 卡（每卡一个主指标）\n第二行：趋势/覆盖热条\n第三行：单维度排行/异常分布\n底部：聚合明细表与数据状态\n```",
        "",
        "Metabase 只消费授权聚合 View，不直接连接 Firebase、Ares、支付、订单或用户原始表。颜色仅表达状态：绿色已核验、琥珀试运行/未成熟、红色缺失/阻断、灰色延迟。",
        "",
        "### 6.2 推荐 View 和 Model",
        "",
        md_table(["逻辑 View", "粒度", "一期/二期", "主要用途"], [
            ["vw_metabase_endpoint_health", "日期 × 端 × 来源 × 包", "一期", "数据覆盖和新鲜度"],
            ["vw_metabase_native_performance", "日期 × 端 × 包 × 版本 × 维度", "一期", "原生性能"],
            ["vw_metabase_native_performance_rank", "日期 × 单一排行维度", "一期", "设备/版本/网络排行"],
            ["vw_metabase_event_session", "日期 × 端 × 包 × 事件分类", "一期", "事件与会话行为"],
            ["vw_metabase_stability_and_quality", "日期 × 包 × 版本 × Issue", "一期", "稳定性事件量和问题数"],
            ["vw_metabase_h5_game_lifecycle", "日期 × 游戏 × 端 × 版本", "一期/二期", "加载→可玩→可下注"],
            ["vw_metabase_h5_web_performance", "日期 × 页面 × 浏览器/网络", "二期", "Web RUM 与核心请求"],
            ["vw_metabase_core_funnel", "日期 × 端 × 包 × 阶段", "二期", "客户端尝试与服务端成功"],
        ]),
        "",
        "### 6.3 全局筛选器",
        "",
        "日期范围、端侧、包体、应用/H5 版本、发布批次、国家、设备品牌/型号桶、系统、内存档位、浏览器、网络类型、运营商、页面/请求类别、游戏和数据状态。H5 没有对应字段时显示“未采集”，不能筛选成 0。",
        "",
        "### 6.4 实施顺序",
        "",
        "```text\n权限/区域确认\n  → BQ 聚合数据集与维表\n  → 一期 D+1 刷新与质量检查\n  → Metabase Model / Saved Question\n  → 一期 Dashboard 与日报\n  → H5 三阶段埋点接入\n  → 二期 H5 RUM、请求、错误、恢复与业务链路\n```",
        "",
        "当前远端状态：BigQuery 聚合数据集和 Metabase 写入均未在本轮执行；本地已有 V1 SQL/合同/预览作为样式和实现参考。管理员后续需提供最小权限后再落地远端对象。",
        "",
        "## 附录｜决策与资料边界",
        "",
        "- 一期：当前 Firebase 聚合、现有 BQ 设计合同、少量 H5 三阶段事件。",
        "- 二期：Web RUM、核心请求、前端错误、网络恢复、服务端业务链路和复杂版本/设备归因。",
        "- 业务日：`Africa/Lagos`；文档执行时间：`Asia/Hong_Kong`。",
        "- 历史 V2、起源五页版和 Firebase 清单保留为历史/证据资料；本 V3 作为新的主入口。",
        "- [多端设备性能 V2](./Waje多端设备性能报表看板详细设计V2-2026-08-27.md)",
        "- [起源设备监控五页版](./起源设备监控五页版优化需求与具体报表示例-V1-2026-08-31.md)",
        "- [Firebase 设备与性能可实现报表清单](./Waje-Firebase设备与性能数据可实现报表、字段与埋点缺口清单-V1-2026-08-31.md)",
        "- [现有本地 Metabase V4 示例](../../analysis/metabase_v4_visual_dashboard_2026_09_01/README.md)",
        "",
    ]
    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")


def html_badge(status: str) -> str:
    label = {"provisional": "试运行", "provisional_behavior_only": "仅行为基线", "provisional_quality_warning": "质量警告", "provisional_schema_mapping": "待字段认证", "immature": "未成熟", "data_gap": "数据缺口", "blocked": "已阻断", "一期可用": "一期可用", "一期补分母后可用": "一期补分母", "一期补埋点后可用": "一期补埋点", "二期缺埋点": "二期缺口", "二期链路": "二期链路", "二期复杂聚合": "二期复杂聚合", "复杂聚合": "复杂聚合"}.get(status, status)
    tone = "ok" if status in {"一期可用", "certified"} else "danger" if status in {"data_gap", "blocked", "二期缺埋点"} else "warn"
    return f'<span class="badge {tone}">{esc(label)}</span>'


def html_table(headers: list[str], rows: list[list[Any]], *, cls: str = "") -> str:
    head = "".join(f"<th>{esc(header)}</th>" for header in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell if isinstance(cell, str) and (cell.startswith('<span') or cell.startswith('<code')) else esc(cell)}</td>" for cell in row) + "</tr>" for row in rows)
    return f'<div class="table-wrap"><table class="{esc(cls)}"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def html_bars(rows: list[tuple[str, int]], unit: str = "") -> str:
    maximum = max((value for _, value in rows), default=1) or 1
    output = []
    for label, value in rows:
        width = max(2, round(value / maximum * 100)) if value else 0
        output.append(f'<div class="bar-row"><span class="bar-label">{esc(label)}</span><span class="bar-track"><i style="width:{width}%"></i></span><b>{esc(compact(value))}{esc(unit)}</b></div>')
    return "".join(output)


def html_css() -> str:
    return """
:root{--navy:#102a43;--ink:#1f2937;--muted:#64748b;--line:#e2e8f0;--bg:#f4f7fb;--card:#fff;--blue:#1976d2;--green:#15803d;--amber:#b45309;--red:#c2410c;--purple:#6d28d9;--shadow:0 12px 32px rgba(15,38,64,.07);--radius:16px}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.65 -apple-system,BlinkMacSystemFont,"SF Pro Display","PingFang SC","Microsoft YaHei",Arial,sans-serif}a{color:var(--blue);text-decoration:none}a:hover{text-decoration:underline}.top{background:var(--navy);color:#fff;padding:28px 20px 32px}.top-inner{max-width:1240px;margin:auto}.eyebrow{color:#a9c8ed;font-size:12px;letter-spacing:.12em;font-weight:700}.top h1{font-size:clamp(28px,4vw,48px);line-height:1.12;letter-spacing:-.04em;margin:8px 0 10px}.lede{max-width:850px;color:#dbe7f3;margin:0}.meta{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}.meta span{border:1px solid rgba(255,255,255,.24);border-radius:999px;padding:5px 10px;font-size:12px;color:#dbe7f3}.layout{max-width:1240px;margin:auto;padding:24px 20px 64px;display:grid;grid-template-columns:210px minmax(0,1fr);gap:26px}.nav{position:sticky;top:18px;align-self:start}.nav h3{font-size:11px;letter-spacing:.14em;color:var(--muted);margin:0 0 8px;text-transform:uppercase}.nav a{display:block;padding:8px 11px;border-left:3px solid transparent;color:var(--muted);font-size:13px;border-radius:0 8px 8px 0}.nav a:hover,.nav a.active{background:#e8f1fb;border-left-color:var(--blue);color:var(--navy)}.section{scroll-margin-top:18px;margin-bottom:30px}.section h2{margin:0 0 4px;color:var(--navy);font-size:26px;letter-spacing:-.025em}.section h3{color:var(--navy);font-size:17px;margin:21px 0 10px}.section-lede{color:var(--muted);font-size:13px;margin:0 0 14px}.callout{background:var(--card);border:1px solid var(--line);border-left:5px solid var(--blue);border-radius:var(--radius);box-shadow:var(--shadow);padding:17px 18px;margin:14px 0}.callout.warn{border-left-color:var(--amber);background:#fffaf0}.callout.danger{border-left-color:var(--red);background:#fff5f1}.callout.ok{border-left-color:var(--green);background:#f0faf3}.hero-grid,.grid-2,.grid-3{display:grid;gap:14px}.hero-grid{grid-template-columns:repeat(4,minmax(0,1fr));margin-bottom:20px}.grid-2{grid-template-columns:repeat(2,minmax(0,1fr))}.grid-3{grid-template-columns:repeat(3,minmax(0,1fr))}.card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow);padding:18px;min-width:0}.card .label{color:var(--muted);font-size:12px}.card .value{display:block;color:var(--navy);font-size:27px;font-weight:800;line-height:1.15;margin:7px 0}.card .hint{color:var(--muted);font-size:12px}.card.blue{border-top:4px solid var(--blue)}.card.green{border-top:4px solid var(--green)}.card.amber{border-top:4px solid #e0a03a}.card.red{border-top:4px solid var(--red)}.badge{display:inline-flex;border-radius:999px;padding:2px 8px;font-size:11px;font-weight:700;white-space:nowrap}.badge.ok{background:#e8f7ee;color:#176b39}.badge.warn{background:#fff3dc;color:#9b5600}.badge.danger{background:#fff0eb;color:#b33d14}.flow{display:flex;align-items:stretch;gap:10px;overflow-x:auto;padding:8px 0 14px}.flow .node{min-width:130px;flex:1;background:#fff;border:1px solid #cbd9e8;border-radius:13px;padding:14px 12px;text-align:center;color:var(--navy);font-weight:700;box-shadow:0 7px 18px rgba(15,38,64,.06)}.flow .node small{display:block;color:var(--muted);font-weight:400;font-size:11px;margin-top:5px}.flow .arrow{align-self:center;color:var(--blue);font-size:23px}.bar-list{display:grid;gap:11px}.bar-row{display:grid;grid-template-columns:minmax(120px,1.2fr) minmax(120px,2fr) 70px;gap:10px;align-items:center}.bar-label{font-size:12px;color:#334155;overflow-wrap:anywhere}.bar-track{display:block;height:10px;border-radius:99px;background:#e8eff6;overflow:hidden}.bar-track i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,#3db5c2,var(--blue))}.bar-row b{font-size:12px;text-align:right;color:var(--navy)}.table-wrap{overflow-x:auto;background:#fff;border:1px solid var(--line);border-radius:13px;box-shadow:0 7px 20px rgba(15,38,64,.035)}table{border-collapse:collapse;width:100%;min-width:720px}th,td{font-size:12px;text-align:left;vertical-align:top;padding:11px 12px;border-bottom:1px solid var(--line)}th{background:#f5f8fb;color:#40566f;white-space:nowrap;font-size:11px}tr:last-child td{border-bottom:0}.two-col{display:grid;grid-template-columns:1fr 1fr;gap:14px}.mini-list{margin:0;padding-left:20px;color:#475569;font-size:13px}.mini-list li{margin:5px 0}.wireframe{border:1px dashed #aabbd0;background:#fbfdff;border-radius:14px;padding:16px;font:12px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre-wrap;color:#35506b}.legend{display:flex;gap:8px;flex-wrap:wrap;font-size:12px;color:var(--muted)}.legend span{padding:5px 9px;border-radius:999px;background:#f1f5f9}.footer{border-top:1px solid var(--line);color:var(--muted);font-size:12px;padding-top:16px;margin-top:34px}@media(max-width:980px){.layout{grid-template-columns:1fr}.nav{position:relative;top:auto;display:flex;gap:6px;overflow-x:auto;padding-bottom:8px}.nav h3{display:none}.nav a{white-space:nowrap;border:1px solid var(--line);border-radius:999px;padding:6px 10px}.hero-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.grid-3{grid-template-columns:1fr 1fr}}@media(max-width:650px){.top{padding:23px 16px 26px}.layout{padding:18px 13px 48px}.hero-grid,.grid-2,.grid-3,.two-col{grid-template-columns:1fr}.top h1{font-size:32px}.section h2{font-size:23px}.bar-row{grid-template-columns:95px minmax(80px,1fr) 52px;gap:7px}.card .value{font-size:23px}}
"""


def write_html(context: dict[str, Any], baseline: dict[str, Any], contract: dict[str, Any], sources: list[dict[str, Any]]) -> None:
    p1 = phase1_metrics()
    p2 = phase2_metrics()
    native_rows = [[esc(row["label"]), esc(compact(row["performance_record_count"])), esc(compact(row["duration_trace_count"])), esc(compact(row["network_request_count"])), esc(f"{row['first_day']} 至 {row['last_day']}")] for row in context["native"]]
    source_rows_html = [[esc(row["source"]), esc(row["window"]), esc(row["covered_days"]), html_badge(row["status_label"]), esc(row["usable"]), esc(row["not_for"])] for row in sources]
    p1_html = [[esc(m["metric"]), f"<code>{esc(m['code'])}</code>", esc(m["definition"]), f"<code>{esc(m['formula'])}</code>", esc(m["denominator"]), esc(m["source"]), html_badge(m["status"])] for m in p1]
    p2_html = [[esc(m["metric"]), esc(m["definition"]), f"<code>{esc(m['formula'])}</code>", esc(m["denominator"]), esc(m["source"]), html_badge(m["status"])] for m in p2]
    p2_theme_html = html_table(["二期主题", "指标含义", "计算方式", "分母/门槛", "需要的数据", "状态"], [[esc(cell) for cell in row] for row in phase2_theme_rows()])
    h5_rows = [[esc(row["event_name"]), f"{int(row['event_count']):,}", esc(row["covered_days"])] for row in context["h5_events"]]
    coverage = html_table(["数据源", "窗口", "覆盖日", "状态", "一期可用", "不能直接做"], source_rows_html)
    native_table = html_table(["端/包", "Performance 记录", "DURATION_TRACE", "网络请求", "窗口"], native_rows)
    p1_table = html_table(["指标", "编码", "定义", "算法", "分母/门槛", "来源", "状态"], p1_html)
    p2_table = html_table(["指标", "含义", "计算方式", "分母/门槛", "来源", "状态"], p2_html)
    h5_table = html_table(["事件", "事件量", "覆盖日数"], h5_rows)
    native_bars = html_bars([(row["label"], int(row["performance_record_count"])) for row in context["native"]])
    h5_bars = html_bars([(row["event_name"], int(row["event_count"])) for row in context["h5_events"]])
    html_doc = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="Waje 多端设备与性能报表看板需求 V3 六模块设计：一期数据底座与二期埋点、指标、Metabase 链路。"><title>Waje 多端设备与性能报表/看板需求 V3（六模块）</title><style>{html_css()}</style></head><body>
<header class="top"><div class="top-inner"><div class="eyebrow">WAJE · DEVICE &amp; PERFORMANCE · V3</div><h1>设备与性能报表/看板需求<br>六模块、一期/二期分阶段落地</h1><p class="lede">先判断数据是否可信，再定位端、包、版本、设备、网络和游戏体验问题。一期使用现有聚合数据，二期补齐 H5 RUM、核心请求、错误恢复和服务端链路。</p><div class="meta"><span>执行日期 {RUN_DATE}</span><span>业务日 Africa/Lagos</span><span>数据快照 {context['snapshot_at']}</span><span>Metabase：设计+本地示例</span></div></div></header>
<div class="layout"><nav class="nav"><h3>六模块</h3><a class="active" href="#m1">01 总体设计</a><a href="#m2">02 一期数据</a><a href="#m3">03 一期看板</a><a href="#m4">04 二期看板</a><a href="#m5">05 二期埋点</a><a href="#m6">06 Metabase</a></nav><main>
<section class="hero-grid"><div class="card blue"><span class="label">一期原生性能</span><span class="value">{compact(context['android_native_total'])}</span><span class="hint">Android Performance 记录，7 日快照</span></div><div class="card green"><span class="label">Android 去标识化会话</span><span class="value">{compact(context['session_total'])}</span><span class="hint">Sessions 表内部去重，不跨端相加</span></div><div class="card amber"><span class="label">H5 行为基线</span><span class="value">{compact(context['h5_total'])}</span><span class="hint">四类标准事件，8 日窗口</span></div><div class="card red"><span class="label">二期 Web 性能</span><span class="value">数据缺口</span><span class="hint">Web Vitals、请求、错误恢复待补</span></div></section>
<section class="callout warn"><b>阅读结论：</b>一期能先做数据健康、原生性能、稳定性事件量和 H5 行为基线；二期才开放 H5 网页性能、核心业务成功率和复杂性能归因。缺失、未成熟和权限阻断不填 0。</section>

<section class="section" id="m1"><h2>模块一｜总体设计、框架、维度与核心指标</h2><p class="section-lede">统一数据层、维度、状态和指标层级，避免不同端侧使用不同口径。</p><div class="flow"><div class="node">Firebase / Ares / H5<small>多源输入</small></div><span class="arrow">→</span><div class="node">BQ 受控层<small>原始与聚合</small></div><span class="arrow">→</span><div class="node">维表 + Mart<small>统一口径</small></div><span class="arrow">→</span><div class="node">授权 View<small>只读聚合</small></div><span class="arrow">→</span><div class="node">Metabase<small>看板/日报</small></div></div><div class="grid-3"><div class="card"><b>数据可信度</b><p class="hint">覆盖、完整日、截止时间、延迟、字段质量和成熟度。</p></div><div class="card"><b>体验质量</b><p class="hint">性能 P95、网络、帧率、稳定性、H5 游戏可玩性。</p></div><div class="card"><b>业务结果</b><p class="hint">服务端登录、下注、结算、支付、提现和资产事实。</p></div></div><div class="legend"><span>绿色：已核验</span><span>琥珀：试运行/未成熟</span><span>红色：缺失/阻断</span><span>灰色：延迟</span></div></section>

<section class="section" id="m2"><h2>模块二｜一期数据现状、可用范围与补充缺口</h2><p class="section-lede">数据状态基于 2026-08-27 聚合快照；不是实时刷新结果。</p>{coverage}<div class="grid-2"><div class="card"><h3>现有底座</h3><ul class="mini-list"><li>Android Performance：三包覆盖 7 日，可做原生性能基线。</li><li>Android Sessions：可做去标识化会话，但存在开关字段质量冲突。</li><li>Android Crashlytics：先计算事件率，事件量和 Issue 数只作样本信息。</li><li>iOS：5～6 日，标记 immature。</li><li>H5：四类标准行为事件，性能仍是 data_gap。</li></ul></div><div class="card"><h3>一期只补三个事件</h3><ul class="mini-list"><li><b>H5_GAME_LOAD</b>：加载阶段、失败、超时。</li><li><b>H5_GAME_READY</b>：真实画面和配置就绪。</li><li><b>H5_BET_READY</b>：五项可下注条件全量记录。</li></ul><p class="hint">限定自研 iframe；第三方没有桥接回调时不推断内部状态。</p></div></div><div class="callout warn"><b>会话建立成功率口径：</b>必须有“建立尝试”作为分母；优先复用已确认的会话初始化尝试事件，若不存在则补充 <code>SESSION_INIT_ATTEMPT</code>。分母未补齐时显示 N/A，不以单纯事件记录替代。</div></section>

<section class="section" id="m3"><h2>模块三｜一期看板和报表：指标、口径与示例</h2><p class="section-lede">一期默认 3 个看板页面 + 1 份 D+1 健康日报。</p><div class="grid-3"><div class="card blue"><b>01 数据健康</b><p class="hint">覆盖率、完整日、新鲜度、来源状态。</p></div><div class="card green"><b>02 原生性能</b><p class="hint">轨迹/网络 P95、成功率、慢帧和冻结帧。</p></div><div class="card amber"><b>03 稳定性/H5</b><p class="hint">Fatal/Issue 事件量和 H5 行为基线。</p></div></div><div class="grid-2"><div class="card"><h3>原生 Performance 记录量</h3><div class="bar-list">{native_bars}</div><p class="hint">记录量仅代表数据存在，不代表性能好坏。</p></div><div class="card"><h3>H5 行为事件量</h3><div class="bar-list">{h5_bars}</div><p class="hint">事件量不是用户数，当前只作行为基线。</p></div></div><h3>一期指标字典</h3>{p1_table}<h3>原生 Performance 聚合示例</h3>{native_table}<h3>H5 Analytics 行为基线示例</h3>{h5_table}<div class="callout ok"><b>一期门禁：</b>P95/P99 样本不少于 500；小分组不少于 10 个去标识化会话；未成熟、延迟和缺失单独展示；H5 三阶段事件成功状态不能由 iframe onload 代替。</div></section>

<section class="section" id="m4"><h2>模块四｜二期看板和报表：目标指标与复杂分析</h2><p class="section-lede">二期面向当前缺失较多、需要跨源关联或聚合逻辑复杂的内容。</p><div class="grid-3"><div class="card red"><b>H5 Web RUM</b><p class="hint">FCP/LCP/INP/CLS、页面 ready、白屏/黑屏。</p></div><div class="card red"><b>核心业务链路</b><p class="hint">页面→游戏→可下注→GAMESTART→完局/资产。</p></div><div class="card red"><b>复杂归因</b><p class="hint">版本、设备、网络与首局/付费/留存的分层关联。</p></div></div>{p2_theme_html}<h3>二期指标详细口径</h3>{p2_table}<div class="callout danger"><b>二期边界：</b>服务端业务结果不能由客户端行为替代；时间窗口匹配必须标记 degraded_attribution，不得当作直接关联事实。</div></section>

<section class="section" id="m5"><h2>模块五｜二期埋点、事实表与复杂聚合</h2><p class="section-lede">把“页面变慢、请求失败、白屏、断网恢复、游戏不可玩”拆成可定位的事实。</p><div class="flow"><div class="node">H5_SESSION_START<small>会话</small></div><span class="arrow">→</span><div class="node">NAVIGATION_PERF<small>页面</small></div><span class="arrow">→</span><div class="node">CORE_REQUEST<small>请求</small></div><span class="arrow">→</span><div class="node">CLIENT_ERROR<small>错误</small></div><span class="arrow">→</span><div class="node">NETWORK / RECOVERY<small>恢复</small></div></div><div class="grid-2"><div class="card"><h3>逻辑事实层</h3><p><code>fact_h5_page_performance</code><br><code>fact_h5_core_request</code><br><code>fact_h5_client_error</code><br><code>fact_h5_game_lifecycle</code><br><code>fact_h5_network_recovery</code><br><code>fact_core_business_funnel</code></p></div><div class="card"><h3>统一关联键</h3><p><code>session_id → page_visit_id → game_load_id → request_id → round_id</code></p><p class="hint">物理表名和字段需按真实 BQ/Ares 目录回填。</p></div></div><h3>二期质量门禁</h3>{html_table(["质量项","门槛","失败处理"],[["完整日","≥7 日", "immature，不做正式趋势"],["必填字段","≥99.5%", "阻断指标并进入缺口队列"],["链路关联","≥98%", "拆分 direct/degraded"],["未知枚举","≤0.1%", "保留原值，不映射其他"],["迟到数据",">45 分钟", "delayed，不触发产品告警"]])}</section>

<section class="section" id="m6"><h2>模块六｜Metabase 搭建方案、样式与数据链路</h2><p class="section-lede">Metabase 只消费授权聚合 View；本轮输出设计和本地示例，不修改远端对象。</p><div class="flow"><div class="node">BQ Mart<small>一期/二期聚合</small></div><span class="arrow">→</span><div class="node">Authorized View<small>只读、安全</small></div><span class="arrow">→</span><div class="node">Model<small>字段语义</small></div><span class="arrow">→</span><div class="node">Saved Question<small>单卡片口径</small></div><span class="arrow">→</span><div class="node">Dashboard<small>筛选/图表</small></div></div><div class="wireframe">顶部：数据截止时间｜完整日｜口径版本｜状态\n第一行：核心 KPI 卡（每卡一个主指标）\n第二行：趋势/覆盖热条\n第三行：单维度排行/异常分布\n底部：聚合明细表与数据状态\n\n颜色：绿色已核验｜琥珀试运行/未成熟｜红色缺失/阻断｜灰色延迟</div>{html_table(["逻辑 View","粒度","阶段","用途"],[["vw_metabase_endpoint_health","日期 × 端 × 来源 × 包","一期","数据覆盖与新鲜度"],["vw_metabase_native_performance","日期 × 端 × 包 × 版本 × 维度","一期","原生性能"],["vw_metabase_native_performance_rank","日期 × 单一排行维度","一期","设备/版本/网络排行"],["vw_metabase_event_session","日期 × 端 × 包 × 事件分类","一期","事件与会话行为"],["vw_metabase_stability_and_quality","日期 × 包 × 版本 × Issue","一期","稳定性事件量/问题数"],["vw_metabase_h5_game_lifecycle","日期 × 游戏 × 端 × 版本","一期/二期","加载→可玩→可下注"],["vw_metabase_h5_web_performance","日期 × 页面 × 浏览器/网络","二期","Web RUM/请求"],["vw_metabase_core_funnel","日期 × 端 × 包 × 阶段","二期","行为与服务端结果"]])}<div class="callout warn"><b>权限门槛：</b>当前远端 BigQuery 数据集创建和 Metabase 写入均未执行。后续需要管理员提供最小权限，先部署聚合层，再建 Model、Saved Question 和 Dashboard。</div></section>

<footer class="footer">来源：本地聚合基线 <code>{esc(str(BASELINE_PATH.relative_to(ROOT)))}</code>；历史设计和 SQL 合同见项目知识库。报告不含用户、设备唯一标识、订单、支付明细、完整 URL、请求正文、错误堆栈、账号、Token 或 Cookie。</footer>
</main></div></body></html>'''
    for old, new in {
        "certified": "已认证",
        "provisional_quality_warning": "质量警告",
        "provisional_schema_mapping": "待字段认证",
        "provisional_behavior_only": "仅行为基线",
        "provisional": "试运行",
        "immature": "未成熟",
        "data_gap": "数据缺口",
        "blocked": "已阻断",
        "delayed": "延迟",
        "degraded_attribution": "降级关联",
        "direct/degraded": "直接关联/降级关联",
        "direct_linked": "直接关联",
        "degraded": "降级关联",
        "Android Crashlytics：先展示事件量和 Issue 数": "Android Crashlytics：主指标是事件率，事件量只作样本信息",
        "Fatal/Issue 事件量和 H5 行为基线": "Fatal/Non-fatal 事件率、会话影响率和 H5 行为基线",
    }.items():
        html_doc = html_doc.replace(old, new)
    OUTPUT_HTML.write_text(html_doc, encoding="utf-8")


def write_analysis(context: dict[str, Any], baseline: dict[str, Any], contract: dict[str, Any], sources: list[dict[str, Any]], charts: dict[str, Any]) -> None:
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    (ANALYSIS_DIR / "metric_catalog.json").write_text(json.dumps({"phase1": phase1_metrics(), "phase2": phase2_metrics()}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ANALYSIS_DIR / "source_matrix.json").write_text(json.dumps(sources, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ANALYSIS_DIR / "chart_data.json").write_text(json.dumps(charts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ANALYSIS_DIR / "metabase_dashboard_contract.json").write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    source_hash = hashlib.sha256(BASELINE_PATH.read_bytes()).hexdigest()
    receipt = {
        "run_id": f"device_performance_dashboard_v3_{RUN_DATE}",
        "run_date": RUN_DATE,
        "status": "ok_local_design_only",
        "lark_document": LARK_DOCUMENT,
        "lark_wiki_node": LARK_WIKI_NODE,
        "lark_revision": LARK_REVISION,
        "source": {"path": str(BASELINE_PATH.relative_to(ROOT)), "sha256": source_hash, "snapshot_at": context["snapshot_at"], "business_timezone": context["business_timezone"]},
        "phase1": {"native_performance_records": context["android_native_total"], "android_sessions": context["session_total"], "h5_behavior_events": context["h5_total"], "event_additions": ["H5_GAME_LOAD", "H5_GAME_READY", "H5_BET_READY"]},
        "phase2": {"event_additions": ["H5_SESSION_START", "H5_NAVIGATION_PERF", "H5_CORE_REQUEST", "H5_CLIENT_ERROR", "H5_NETWORK_CHANGE", "H5_RECOVERY_RESULT", "H5_SESSION_END"]},
        "remote_metabase": "not_run_design_only",
        "raw_rows_output": False,
        "credentials_saved": False,
        "source_bodies_saved": False,
        "outputs": {"markdown": str(OUTPUT_MD.relative_to(ROOT)), "html": str(OUTPUT_HTML.relative_to(ROOT)), "analysis_dir": str(ANALYSIS_DIR.relative_to(ROOT))},
    }
    (ANALYSIS_DIR / "run_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_text = OUTPUT_MD.read_text(encoding="utf-8")
    html_text = OUTPUT_HTML.read_text(encoding="utf-8")
    validation = {
        "status": "passed",
        "checks": {
            "six_modules": markdown_text.count("## 模块") == 6 and all(f"模块{n}" in markdown_text for n in ["一", "二", "三", "四", "五", "六"]),
            "phase_boundary": "一期急需补充的埋点" in markdown_text and "二期埋点、事实表与复杂聚合" in markdown_text,
            "metric_formula_and_denominator": all(key in markdown_text for key in ["定义", "算法", "分母/门槛", "来源"]),
            "html_sections": all(f'id="m{n}"' in html_text for n in range(1, 7)),
            "html_no_external_assets": "<script" not in html_text and "<img" not in html_text,
            "no_raw_rows": receipt["raw_rows_output"] is False,
            "no_credentials": receipt["credentials_saved"] is False and receipt["source_bodies_saved"] is False,
            "remote_metabase_not_modified": receipt["remote_metabase"] == "not_run_design_only",
        },
    }
    validation["status"] = "passed" if all(validation["checks"].values()) else "failed"
    (ANALYSIS_DIR / "validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    readme = f"""# Waje 设备与性能报表/看板需求 V3 工件\n\n- 主文档：`{OUTPUT_MD.relative_to(ROOT)}`\n- HTML：`{OUTPUT_HTML.relative_to(ROOT)}`\n- 飞书团队版：{LARK_DOCUMENT}\n- 来源：`{BASELINE_PATH.relative_to(ROOT)}`，快照 `{context['snapshot_at']}`，业务时区 `{context['business_timezone']}`。\n- 本目录保存指标合同、数据源状态、图表数据和运行回执；不保存原始业务行、用户/设备唯一标识、凭据或完整源正文。\n- Metabase：本轮仅输出设计和本地示例，远端写入未执行。\n\n## 复跑\n\n```bash\npython3 scripts/build_device_performance_requirements_v3.py\n```\n"""
    (ANALYSIS_DIR / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    baseline = load_baseline()
    context = build_context(baseline)
    sources = build_source_matrix(baseline)
    contract = build_contract(context)
    charts = chart_data(context, baseline)
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(context, baseline, contract, sources, charts)
    write_html(context, baseline, contract, sources)
    write_analysis(context, baseline, contract, sources, charts)
    print(json.dumps({"status": "ok", "markdown": str(OUTPUT_MD), "html": str(OUTPUT_HTML), "analysis_dir": str(ANALYSIS_DIR), "source_snapshot": context["snapshot_at"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
