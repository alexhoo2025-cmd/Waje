#!/usr/bin/env python3
"""Build safe, stakeholder-facing assets from the Waje BQ metadata snapshot.

No BigQuery calls happen here.  This transforms the reviewed INFORMATION_SCHEMA
metadata snapshot into a complete local inventory, a compact report artifact,
and a Chinese Markdown companion.  It intentionally omits field values and
does not expose restricted field names in the HTML reader surface.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw_metadata" / "field_inventory.json"
INVENTORY = ROOT / "inventory.json"
EVIDENCE = ROOT / "evidence.json"
ARTIFACT = ROOT / "artifact.json"
CHART_MAP = ROOT / "chart_map.json"
RECEIPT = ROOT / "run_receipt.json"
REPORT_MD = ROOT / "report.md"
KNOWLEDGE_MD = Path(__file__).resolve().parents[2] / "knowledge" / "02-数据" / "Waje企业BigQuery数据资产与设备性能分析能力报告-2026-08-27.md"


DATASETS: list[dict[str, str]] = [
    {"dataset_id": "90006", "location": "US", "domain_hint": "经营、投放与网页事件汇总"},
    {"dataset_id": "GE_90006", "location": "europe-west4", "domain_hint": "原始数据候选目录（当前无对象）"},
    {"dataset_id": "ares_hfyl", "location": "europe-west4", "domain_hint": "广告投放、归因与活动指标"},
    {"dataset_id": "ares_hfyl_test", "location": "europe-west4", "domain_hint": "广告投放测试与验证"},
    {"dataset_id": "bigdata", "location": "europe-west4", "domain_hint": "经营汇总与历史迁移表"},
    {"dataset_id": "origin_hfyl", "location": "europe-west4", "domain_hint": "起源事件、业务事实与受限明细"},
    {"dataset_id": "pubwaje", "location": "europe-west4", "domain_hint": "公开/发布层业务数据"},
    {"dataset_id": "track_hfyl", "location": "europe-west4", "domain_hint": "埋点口径、页面流量与用户分层"},
    {"dataset_id": "waje_ng_firebase_h5", "location": "europe-west4", "domain_hint": "Firebase H5 导出目录（当前无对象）"},
    {"dataset_id": "waje_ng_firebase_ios", "location": "europe-west4", "domain_hint": "Firebase Analytics iOS 日表"},
    {"dataset_id": "waje_ng_firebase_ios_crashlytics", "location": "europe-west4", "domain_hint": "Firebase Crashlytics iOS 目录（当前无对象）"},
    {"dataset_id": "waje_ng_firebase_ios_imported_segments", "location": "US", "domain_hint": "Firebase 导入人群元数据"},
    {"dataset_id": "waje_ng_firebase_ios_messaging", "location": "europe-west4", "domain_hint": "Firebase 消息目录（当前无对象）"},
    {"dataset_id": "waje_ng_firebase_ios_performance", "location": "europe-west4", "domain_hint": "Firebase Performance iOS 导出"},
]

DISPLAY_NAMES = {
    "90006": "经营汇总",
    "GE_90006": "候选原始库",
    "ares_hfyl": "投放归因",
    "ares_hfyl_test": "投放测试",
    "bigdata": "经营大表",
    "origin_hfyl": "起源事件",
    "pubwaje": "发布层",
    "track_hfyl": "埋点流量",
    "waje_ng_firebase_h5": "Firebase H5",
    "waje_ng_firebase_ios": "Firebase iOS 分析",
    "waje_ng_firebase_ios_crashlytics": "iOS 崩溃",
    "waje_ng_firebase_ios_imported_segments": "iOS 人群",
    "waje_ng_firebase_ios_messaging": "iOS 消息",
    "waje_ng_firebase_ios_performance": "iOS 性能",
}


RESTRICTED_TERMS = (
    "user_id", "uuid", "xl_id", "android_id", "androidid", "gaid", "idfa", "imei", "oaid", "mac",
    "client_ip", "ip_address", "account", "openid", "email", "phone", "bank", "card", "order_no",
    "transaction", "serial_num", "salt_key", "cookie", "token", "password", "bvn", "nin",
)
DEVICE_TERMS = (
    "browser", "device", "model", "carrier", "os", "operating_system", "screen", "viewport", "client_type",
    "network", "radio", "app_version", "app_build_version", "app_display_version", "package_name", "lib_version",
)
PERFORMANCE_PROXY_TERMS = (
    "event_duration", "page_resource_size", "stay_time", "exit_count", "outtime", "app_crashed_reason",
)
BEHAVIOR_TERMS = (
    "event_type", "event_name", "page", "element", "session", "target_day", "timestamp", "utm", "source", "campaign",
)


def timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def field_privacy(field_path: str) -> str:
    lower = field_path.lower()
    if any(term in lower for term in RESTRICTED_TERMS):
        return "受限标识/资金/网络字段"
    if any(term in lower for term in ("url", "referrer", "payload", "custom", "element_content", "message", "stack")):
        return "内容或遥测字段，需审查"
    return "可用于聚合分析"


def field_tags(field_path: str, dataset_id: str) -> list[str]:
    lower = field_path.lower()
    tags: list[str] = []
    if any(term in lower for term in DEVICE_TERMS):
        tags.append("终端维度")
    if dataset_id == "waje_ng_firebase_ios_performance":
        tags.append("原生性能")
    elif any(term in lower for term in PERFORMANCE_PROXY_TERMS):
        tags.append("体验代理")
    if any(term in lower for term in BEHAVIOR_TERMS):
        tags.append("行为/归因")
    if any(term in lower for term in ("country", "city", "region", "timezone", "language")):
        tags.append("地域/语言")
    if any(term in lower for term in ("pay", "withdraw", "bet", "game", "settlement")):
        tags.append("业务结果")
    return tags or ["其他"]


def table_purpose(dataset_id: str, table_id: str, fields: list[dict[str, Any]]) -> str:
    lower_table = table_id.lower()
    names = " ".join(field["field_path"].lower() for field in fields)
    if dataset_id == "waje_ng_firebase_ios_performance":
        return "iOS 原生性能监测"
    if dataset_id == "waje_ng_firebase_ios":
        return "iOS 分析事件日表"
    if dataset_id == "track_hfyl":
        return "埋点配置/页面流量汇总"
    if "web" in lower_table or ("browser" in names and "url_path" in names):
        return "网页行为与终端画像"
    if "client" in lower_table or "app_version" in names:
        return "客户端行为与版本画像"
    if "crash" in lower_table or "crash" in names:
        return "稳定性信号"
    if any(term in lower_table for term in ("campaign", "advert", "ad_", "media")):
        return "投放/归因"
    if any(term in lower_table for term in ("pay", "payer", "recharge", "asset", "withdraw")):
        return "支付/资产"
    if any(term in lower_table for term in ("game", "bet", "round", "rtp")):
        return "游戏/投注"
    return "业务或参考数据"


def object_type_label(value: str) -> str:
    return {"BASE TABLE": "基础表", "VIEW": "视图", "EXTERNAL": "外部表"}.get(value, value)


def status_label(status: str) -> str:
    return {
        "certified": "已核验",
        "provisional": "可试用，待数据核验",
        "immature": "刚接入，尚未成熟",
        "data_gap": "数据缺口",
        "blocked": "受阻",
    }[status]


def source_snapshot() -> dict[str, Any]:
    return {
        "id": "metadata_snapshot",
        "label": "企业 BigQuery 元数据只读快照",
        "path": "raw_metadata/field_inventory.json",
        "description": "使用 robin@afuruika.net 在 wajenigeria 内执行 INFORMATION_SCHEMA.TABLES 与 INFORMATION_SCHEMA.COLUMN_FIELD_PATHS 只读查询；不读取业务表行。",
        "query": {
            "engine": "BigQuery",
            "language": "SQL",
            "description": "US 与 europe-west4 的两条只读字段清单 SQL 分别执行，结果合并为本快照；完整 SQL 保存在本报告同目录的 sql/ 文件夹。",
            "sql": "-- Executed regional branch (metadata only)\nSELECT t.table_name, c.field_path, c.data_type\nFROM `wajenigeria.90006.INFORMATION_SCHEMA.TABLES` AS t\nLEFT JOIN `wajenigeria.90006.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS` AS c\nUSING (table_name)\nORDER BY table_name, field_path;",
            "tables_used": [
                "wajenigeria.<dataset>.INFORMATION_SCHEMA.TABLES",
                "wajenigeria.<dataset>.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS",
            ],
            "filters": ["project = wajenigeria", "metadata only", "no business table rows"],
            "metric_definitions": ["对象数为当前可见的基础表、视图与外部表数量。", "字段路径数包含同构日表与视图中的重复 schema。"],
        },
    }


def load_rows() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    rows = raw.get("rows", [])
    if not isinstance(rows, list):
        raise ValueError("field inventory rows must be a list")
    return raw, [dict(row) for row in rows]


def build_inventory(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    table_fields: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    table_meta: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        dataset_id = str(row["dataset_id"])
        table_id = str(row["table_name"])
        key = (dataset_id, table_id)
        table_meta.setdefault(key, {
            "project_id": "wajenigeria",
            "dataset_id": dataset_id,
            "table_id": table_id,
            "table_type": str(row.get("table_type", "UNKNOWN")),
            "location": str(row.get("location", "")),
            "created_at": row.get("creation_time"),
        })
        field = {
            "field_path": str(row.get("field_path", "")),
            "type": str(row.get("data_type", "")),
            "description": row.get("description"),
        }
        field["privacy_class"] = field_privacy(field["field_path"])
        field["capability_tags"] = field_tags(field["field_path"], dataset_id)
        table_fields[key].append(field)

    table_rows: list[dict[str, Any]] = []
    full_tables: list[dict[str, Any]] = []
    for key, metadata in sorted(table_meta.items()):
        fields = sorted(table_fields[key], key=lambda item: item["field_path"])
        device_fields = sum("终端维度" in field["capability_tags"] for field in fields)
        native_performance_fields = sum("原生性能" in field["capability_tags"] for field in fields)
        experience_proxy_fields = sum("体验代理" in field["capability_tags"] for field in fields)
        restricted_fields = sum(field["privacy_class"] != "可用于聚合分析" for field in fields)
        purpose = table_purpose(metadata["dataset_id"], metadata["table_id"], fields)
        complete = {
            **metadata,
            "purpose_hint": purpose,
            "field_path_count": len(fields),
            "device_dimension_field_count": device_fields,
            "native_performance_field_count": native_performance_fields,
            "experience_proxy_field_count": experience_proxy_fields,
            "restricted_or_review_field_count": restricted_fields,
            "fields": fields,
        }
        full_tables.append(complete)
        table_rows.append({
            "dataset": metadata["dataset_id"],
            "table": metadata["table_id"],
            "type": object_type_label(metadata["table_type"]),
            "field_paths": len(fields),
            "terminal_fields": device_fields,
            "native_performance_fields": native_performance_fields,
            "experience_proxy_fields": experience_proxy_fields,
            "restricted_review_fields": restricted_fields,
            "purpose": purpose,
        })
    return full_tables, table_rows, table_meta


def dataset_rows(full_tables: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for table in full_tables:
        grouped[table["dataset_id"]].append(table)
    output: list[dict[str, Any]] = []
    for dataset in DATASETS:
        tables = grouped.get(dataset["dataset_id"], [])
        type_counter = Counter(table["table_type"] for table in tables)
        field_count = sum(table["field_path_count"] for table in tables)
        state = "certified" if tables else "data_gap"
        output.append({
            "dataset": dataset["dataset_id"],
            "dataset_label": DISPLAY_NAMES[dataset["dataset_id"]],
            "region": dataset["location"],
            "objects": len(tables),
            "field_paths": field_count,
            "base_tables": type_counter.get("BASE TABLE", 0),
            "views": type_counter.get("VIEW", 0),
            "external_tables": type_counter.get("EXTERNAL", 0),
            "domain_hint": dataset["domain_hint"],
            "status": status_label(state),
        })
    return output


def find_field(rows: list[dict[str, Any]], dataset: str, table: str, field_path: str) -> str:
    for row in rows:
        if row["dataset_id"] == dataset and row["table_name"] == table and row["field_path"] == field_path:
            return str(row["data_type"])
    return "未读取到"


def selected_field_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    requested = [
        ("H5 网页终端", "origin_hfyl.realtime_event_web", "browser", "浏览器", "浏览器兼容性与行为分层", "可聚合使用"),
        ("H5 网页终端", "origin_hfyl.realtime_event_web", "device_brand", "设备品牌", "低端机品牌适配分层", "可聚合使用"),
        ("H5 网页终端", "origin_hfyl.realtime_event_web", "device_model", "设备型号", "机型分层；低样本需合并", "仅聚合并设最小样本"),
        ("H5 网页终端", "origin_hfyl.realtime_event_web", "os", "操作系统", "系统版本/终端适配分层", "可聚合使用"),
        ("H5 页面体验代理", "origin_hfyl.realtime_event_web", "event_duration", "事件/停留时长", "体验代理；不能等同页面加载速度", "可聚合使用"),
        ("H5 页面体验代理", "origin_hfyl.realtime_event_web", "page_resource_size", "页面资源大小", "资源体积与设备/网络分层", "可聚合使用"),
        ("H5 页面体验代理", "track_hfyl.dm_client_event_page_traffic_count_daily", "stay_time", "页面停留时长", "按页面/系统/版本的体验代理", "汇总表，可直接使用"),
        ("H5 页面体验代理", "track_hfyl.dm_client_event_page_traffic_count_daily", "exit_count", "页面退出次数", "按页面/系统/版本的退出代理", "汇总表，可直接使用"),
        ("H5 页面体验代理", "track_hfyl.dm_client_event_page_traffic_count_daily", "os_type", "终端类型", "iOS/Android/H5 的汇总切片", "需核对编码映射"),
        ("H5 页面体验代理", "track_hfyl.dm_client_event_page_traffic_count_daily", "version", "应用或热更版本", "发布版本前后对比", "需核对版本口径"),
        ("iOS Analytics", "waje_ng_firebase_ios.events_20260824", "app_info.version", "应用版本", "iOS 版本分层行为分析", "可聚合使用"),
        ("iOS Analytics", "waje_ng_firebase_ios.events_20260824", "device.operating_system", "操作系统", "iOS 系统分层", "可聚合使用"),
        ("iOS Analytics", "waje_ng_firebase_ios.events_20260824", "device.mobile_model_name", "设备型号", "机型适配分层", "小样本合并"),
        ("iOS Analytics", "waje_ng_firebase_ios.events_20260824", "event_name", "事件名称", "行为事件覆盖与漏斗信号", "仅行为信号"),
        ("iOS 原生性能", "waje_ng_firebase_ios_performance.com_wajegame_wajegame_IOS", "event_type", "性能事件类型", "启动、屏幕、网络和自定义轨迹分类", "需先核验数据量"),
        ("iOS 原生性能", "waje_ng_firebase_ios_performance.com_wajegame_wajegame_IOS", "app_display_version", "展示版本", "性能按应用版本分层", "需先核验数据量"),
        ("iOS 原生性能", "waje_ng_firebase_ios_performance.com_wajegame_wajegame_IOS", "device_name", "设备名称", "机型性能差异", "低样本合并"),
        ("iOS 原生性能", "waje_ng_firebase_ios_performance.com_wajegame_wajegame_IOS", "radio_type", "网络类型", "Wi‑Fi/蜂窝网络分层", "需先核验数据量"),
        ("iOS 原生性能", "waje_ng_firebase_ios_performance.com_wajegame_wajegame_IOS", "network_info.response_code", "网络响应码", "接口成功/失败的汇总分布", "仅汇总，不输出路径或载荷"),
        ("iOS 原生性能", "waje_ng_firebase_ios_performance.com_wajegame_wajegame_IOS", "network_info.response_completed_time_us", "网络响应完成耗时", "接口时延分位数", "需过滤异常和小样本"),
        ("iOS 原生性能", "waje_ng_firebase_ios_performance.com_wajegame_wajegame_IOS", "trace_info.duration_us", "轨迹时长", "启动/屏幕/自定义轨迹耗时", "需识别事件类型"),
        ("iOS 原生性能", "waje_ng_firebase_ios_performance.com_wajegame_wajegame_IOS", "trace_info.screen_info.slow_frame_ratio", "慢帧比例", "屏幕流畅度分层", "仅屏幕轨迹有效"),
        ("iOS 原生性能", "waje_ng_firebase_ios_performance.com_wajegame_wajegame_IOS", "trace_info.screen_info.frozen_frame_ratio", "冻结帧比例", "卡顿严重度分层", "仅屏幕轨迹有效"),
        ("通用客户端", "origin_hfyl.realtime_event_client", "app_version", "应用版本", "版本与行为/异常代理关联", "聚合、需审核"),
        ("通用客户端", "origin_hfyl.realtime_event_client", "carrier", "运营商", "网络环境分层", "聚合、需审核"),
        ("通用客户端", "origin_hfyl.realtime_event_client", "network", "网络类型", "网络环境分层", "聚合、需审核"),
        ("通用客户端", "origin_hfyl.realtime_event_client", "app_crashed_reason", "异常原因文本", "仅能形成脱敏错误类别代理", "禁止输出原文"),
    ]
    output: list[dict[str, Any]] = []
    for group, identifier, field, meaning, use, boundary in requested:
        dataset, table = identifier.split(".", 1)
        output.append({
            "group": group,
            "source_table": identifier,
            "field": field,
            "type": find_field(rows, dataset, table, field),
            "meaning": meaning,
            "supported_analysis": use,
            "boundary": boundary,
        })
    return output


def build_artifact(dataset_inventory: list[dict[str, Any]], table_directory: list[dict[str, Any]], selected_fields: list[dict[str, Any]], summary: dict[str, int]) -> dict[str, Any]:
    empty_datasets = [row["dataset"] for row in dataset_inventory if row["objects"] == 0]
    capability_rows = [
        {
            "scope": "H5 网页终端与页面行为",
            "status": status_label("provisional"),
            "supported_dimensions": "浏览器、系统、品牌/型号、屏幕、页面、事件、来源、版本、日期",
            "what_it_can_answer": "不同终端/页面的访问、互动、停留、退出与资源体积代理差异。",
            "evidence": "网页事件表与页面流量汇总表均已发现；尚未读取数据值。",
        },
        {
            "scope": "H5 真正性能监测",
            "status": status_label("data_gap"),
            "supported_dimensions": "无可验证的核心性能字段",
            "what_it_can_answer": "当前不能给出网页加载速度、交互响应或前端错误率结论。",
            "evidence": "已核验的 68 个网页事件字段中未出现核心网页指标、资源时序、HTTP 状态或前端错误字段。",
        },
        {
            "scope": "iOS Analytics 行为与终端",
            "status": status_label("provisional"),
            "supported_dimensions": "应用版本、系统、设备、地域、归因、事件、日期",
            "what_it_can_answer": "可按 iOS 设备和版本观察行为/业务事件的聚合差异。",
            "evidence": "发现 5 张 iOS 日事件表，单表 217 条字段路径；数据量与完整日未检查。",
        },
        {
            "scope": "iOS 原生性能",
            "status": status_label("immature"),
            "supported_dimensions": "设备、系统、版本、运营商、网络类型、国家、性能事件类型",
            "what_it_can_answer": "启动/轨迹时长、网络响应时序与响应码、慢帧/冻结帧的聚合分层。",
            "evidence": "发现 1 张 30 字段 Performance 表，表创建于 2026-08-26；未验证是否已有有效样本。",
        },
        {
            "scope": "App 稳定性",
            "status": status_label("data_gap"),
            "supported_dimensions": "通用客户端异常原因字段仅能做受限代理",
            "what_it_can_answer": "不能替代 Crashlytics 的崩溃、ANR、受影响用户与版本问题分析。",
            "evidence": "iOS Crashlytics 目录当前无表；通用客户端事件中虽有异常原因字段，但需脱敏分类并先验证口径。",
        },
        {
            "scope": "Android Firebase Analytics/Performance",
            "status": status_label("data_gap"),
            "supported_dimensions": "当前未发现专用 Firebase Android 导出表",
            "what_it_can_answer": "无法以 Firebase 导出完成 Android 性能或 Analytics 专题。",
            "evidence": "当前 14 个可见数据集未出现 Android Firebase Analytics/Performance 对象；这不等同于企业没有 Android 业务事件。",
        },
        {
            "scope": "设备/性能与业务结果关联",
            "status": status_label("blocked"),
            "supported_dimensions": "应通过经批准的聚合视图连接页面/端、版本、日期与业务指标",
            "what_it_can_answer": "当前不能自动、安全地进行用户级跨表关联或归因。",
            "evidence": "原始事件中存在受限标识与资金字段；Gemini 查询白名单为空，尚无专用授权聚合视图。",
        },
    ]
    gap_rows = [
        {"gap": "H5 核心网页性能", "state": status_label("data_gap"), "missing": "LCP、INP、CLS、FCP、TTFB、长任务、资源时序、HTTP 响应、前端错误/白屏", "impact": "不能解释网页体验差异或定位性能瓶颈", "minimum_fix": "H5 接入 Web Vitals、导航/资源时序、核心接口与前端错误事件；写入受控聚合表。"},
        {"gap": "Android Firebase 导出", "state": status_label("data_gap"), "missing": "Android Analytics 与 Performance 实例表", "impact": "无法按 Android 包、版本、机型和网络比较原生体验", "minimum_fix": "完成三个 Android 包的 Firebase Analytics/Performance BigQuery 导出，并核验首个稳定日。"},
        {"gap": "Crashlytics 入库", "state": status_label("data_gap"), "missing": "Crashlytics 表与问题/ANR/版本覆盖", "impact": "无法可靠计算稳定性、受影响用户或版本风险", "minimum_fix": "核对 Crashlytics 导出状态与数据集生成；只对聚合问题类别做分析。"},
        {"gap": "数据新鲜度和完整性", "state": status_label("provisional"), "missing": "行数、最新事件时间、分区连续性、空值/重复率", "impact": "当前只能确认 schema，不能确认数据可用于趋势或告警", "minimum_fix": "对批准的聚合视图执行按日量、完整日期与字段覆盖审计。"},
        {"gap": "跨域关联安全边界", "state": status_label("blocked"), "missing": "设备/性能到业务结果的授权聚合视图和统一口径", "impact": "不能将体验差异安全地与支付、留存或游戏结果关联", "minimum_fix": "建立按日×端×版本×页面/事件的脱敏聚合视图，禁止返回标识与订单明细。"},
    ]
    readiness_rows = [
        {"layer": "本机企业 BigQuery 账号", "status": status_label("certified"), "evidence": "robin@afuruika.net 已列出 14 个数据集，并在 wajenigeria 中成功执行 INFORMATION_SCHEMA 查询。", "next": "可继续执行受控只读元数据与授权聚合查询。"},
        {"layer": "数据项目查询作业", "status": status_label("certified"), "evidence": "查询作业在 wajenigeria 数据项目可执行；在 Vertex 运行项目 indigo-gecko-500503-j3 不具备 BigQuery jobs.create。", "next": "明确查询执行项目，避免将 Vertex 运行项目误用于数据查询。"},
        {"layer": "BigQuery 远程 MCP", "status": status_label("blocked"), "evidence": "本轮 MCP 元数据请求返回 Auth required。", "next": "完成企业 MCP 身份/工具权限后重试只读元数据调用。"},
        {"layer": "Gemini 企业 CLI", "status": status_label("blocked"), "evidence": "本轮结构化元数据任务在 180 秒超时；未产生可审计模型交接包。", "next": "补齐 Vertex 预测权限/服务用量权限并验证模型调用。"},
        {"layer": "Gemini 数据白名单", "status": status_label("blocked"), "evidence": "当前配置的允许数据集/授权视图清单为空。", "next": "优先开放脱敏聚合视图，而不是底层原始事件或资金表。"},
    ]
    quality_rows = [
        {"check": "数据集清单", "result": "14 个数据集", "status": status_label("certified"), "boundary": "仅限 robin@afuruika.net 当前可见范围。"},
        {"check": "对象清单", "result": f"{summary['objects']} 个对象：{summary['base_tables']} 基础表、{summary['views']} 视图、{summary['external_tables']} 外部表", "status": status_label("certified"), "boundary": "通过 INFORMATION_SCHEMA 元数据读取。"},
        {"check": "字段字典", "result": f"{summary['field_paths']:,} 条字段路径", "status": status_label("certified"), "boundary": "字段路径在日表/视图间可重复，不等同唯一业务字段数。"},
        {"check": "空目录", "result": "、".join(empty_datasets), "status": status_label("data_gap"), "boundary": "目录存在但当前无表/视图对象；不代表产品没有数据。"},
        {"check": "业务数据质量", "result": "未读取行数、分区、时效、空值或重复率", "status": status_label("provisional"), "boundary": "本报告是 schema/能力盘点，不是数据值审计。"},
    ]
    type_rows = [
        {"object_type": "基础表", "count": summary["base_tables"]},
        {"object_type": "视图", "count": summary["views"]},
        {"object_type": "外部表", "count": summary["external_tables"]},
    ]
    generated = timestamp()
    return {
        "surface": "report",
        "manifest": {
            "version": 1,
            "surface": "report",
            "title": "Waje 企业 BigQuery 数据资产与设备性能分析能力报告",
            "description": "面向产品、数据与研发的只读元数据盘点：可见数据库表、字段能力、设备与性能分析边界。",
            "generatedAt": generated,
            "sources": [source_snapshot()],
            "cards": [
                {"id": "dataset_card", "dataset": "summary", "sourceId": "metadata_snapshot", "metrics": [{"label": "可见数据集", "field": "dataset_count", "format": "number"}]},
                {"id": "object_card", "dataset": "summary", "sourceId": "metadata_snapshot", "metrics": [{"label": "表、视图与外部表", "field": "object_count", "format": "number"}]},
                {"id": "field_card", "dataset": "summary", "sourceId": "metadata_snapshot", "metrics": [{"label": "字段路径", "field": "field_path_count", "format": "number"}]},
                {"id": "native_perf_card", "dataset": "summary", "sourceId": "metadata_snapshot", "metrics": [{"label": "原生性能表", "field": "native_performance_table_count", "format": "number"}]},
            ],
            "charts": [
                {"id": "objects_by_dataset", "title": "各数据集的可见对象数", "subtitle": "14 个数据集；表、视图与外部表合计", "dataset": "dataset_inventory", "sourceId": "metadata_snapshot", "type": "bar", "encodings": {"x": {"field": "dataset_label"}, "y": {"field": "objects"}}},
                {"id": "object_type_mix", "title": "可见对象类型", "subtitle": "基础表、视图与外部表的构成", "dataset": "object_type_mix", "sourceId": "metadata_snapshot", "type": "bar", "encodings": {"x": {"field": "object_type"}, "y": {"field": "count"}}},
            ],
            "tables": [
                {"id": "dataset_table", "title": "数据集盘点", "dataset": "dataset_inventory", "sourceId": "metadata_snapshot", "columns": [
                    {"field": "dataset_label", "label": "数据集", "type": "text"}, {"field": "region", "label": "区域", "type": "text"}, {"field": "objects", "label": "对象数", "type": "number"}, {"field": "field_paths", "label": "字段路径", "type": "number"}, {"field": "status", "label": "状态", "type": "text"}], "defaultSort": {"field": "objects", "direction": "desc"}},
                {"id": "capability_table", "title": "设备与性能分析能力矩阵", "dataset": "capability_matrix", "sourceId": "metadata_snapshot", "columns": [
                    {"field": "scope", "label": "专题", "type": "text"}, {"field": "status", "label": "状态", "type": "text"}, {"field": "what_it_can_answer", "label": "可回答的问题", "type": "text"}, {"field": "evidence", "label": "证据与边界", "type": "text"}], "defaultSort": {"field": "scope", "direction": "asc"}},
                {"id": "key_field_table", "title": "关键设备与性能字段字典", "dataset": "key_fields", "sourceId": "metadata_snapshot", "columns": [
                    {"field": "group", "label": "数据域", "type": "text"}, {"field": "field", "label": "字段", "type": "text"}, {"field": "type", "label": "类型", "type": "text"}, {"field": "supported_analysis", "label": "支持分析", "type": "text"}, {"field": "boundary", "label": "使用边界", "type": "text"}], "defaultSort": {"field": "group", "direction": "asc"}},
                {"id": "gap_table", "title": "缺口与最小补齐动作", "dataset": "gaps", "sourceId": "metadata_snapshot", "columns": [
                    {"field": "gap", "label": "缺口", "type": "text"}, {"field": "state", "label": "状态", "type": "text"}, {"field": "missing", "label": "缺失内容", "type": "text"}, {"field": "minimum_fix", "label": "最小补齐动作", "type": "text"}], "defaultSort": {"field": "gap", "direction": "asc"}},
                {"id": "readiness_table", "title": "企业查询通路就绪度", "dataset": "query_readiness", "sourceId": "metadata_snapshot", "columns": [
                    {"field": "layer", "label": "层", "type": "text"}, {"field": "status", "label": "状态", "type": "text"}, {"field": "next", "label": "下一步", "type": "text"}], "defaultSort": {"field": "layer", "direction": "asc"}},
            ],
            "blocks": [
                {"id": "title", "type": "markdown", "body": "# Waje 企业 BigQuery 数据资产与设备性能分析能力报告"},
                {"id": "summary", "type": "markdown", "sourceId": "metadata_snapshot", "body": f"## Executive Summary｜执行摘要\n\n**当前企业账号可稳定盘点到 {summary['datasets']} 个数据集、{summary['objects']} 个表/视图/外部表和 {summary['field_paths']:,} 条字段路径。** 其中有 {summary['base_tables']} 张基础表、{summary['views']} 个视图与 {summary['external_tables']} 张外部表；这是元数据可见性结论，不代表所有对象的数据质量已通过。\n\n**设备与体验分析已有可用底座，但层级不均衡。** 内部网页事件与页面流量表可支持浏览器、系统、品牌/型号、页面、版本、停留/退出与资源大小等分层；iOS Analytics 日表可支持版本和设备行为切片。\n\n**真正的性能指标目前只在一张 iOS Firebase Performance 表中出现，且仍处于刚入库阶段。** 它含网络时序、响应码、轨迹时长、慢帧与冻结帧字段；没有对其数据量、日期连续性或空值进行本轮验证。\n\n**H5 核心网页性能、Android Firebase 导出和 Crashlytics 仍是关键缺口。** 当前不应据此宣称网页或 Android 性能正常，也不应把体验代理指标替代为加载速度结论。"},
                {"id": "metrics", "type": "metric-strip", "cardIds": ["dataset_card", "object_card", "field_card", "native_perf_card"]},
                {"id": "assets_heading", "type": "markdown", "sourceId": "metadata_snapshot", "body": "## 可见资产范围：两个区域、十个有对象的数据集\n\n**对象最多的是起源事件库，其次是广告归因与经营汇总库。** 元数据证实 14 个可见数据集中有 10 个已有对象；四个 Firebase/候选目录当前为空。分区/区域必须在后续查询中显式指定，不能把 US 与 europe-west4 的表直接混用。"},
                {"id": "objects_chart", "type": "chart", "chartId": "objects_by_dataset"},
                {"id": "types_chart", "type": "chart", "chartId": "object_type_mix"},
                {"id": "dataset_table_block", "type": "table", "tableId": "dataset_table"},
                {"id": "capability_heading", "type": "markdown", "sourceId": "metadata_snapshot", "body": "## 设备与性能专题：可回答的问题与明确边界\n\n**H5 可以做终端与行为分层，但不能直接做网页性能诊断。** 网页事件 schema 中有浏览器、系统、设备、页面、互动、资源大小和停留时间；它们足以定位“哪个终端/页面的行为信号异常”，但不能证明具体是网络时延、渲染或脚本错误导致。\n\n- 可做：浏览器、设备品牌/型号、系统、屏幕、页面、版本、来源、停留、退出与资源体积的聚合比较。\n- 可做：iOS 版本、设备、系统、运营商、网络类型、国家、行为事件的聚合切片。\n- 可做（待数据审计）：iOS 启动/轨迹时长、网络响应时序和响应码、慢帧/冻结帧分层。\n- 不可直接做：H5 加载速度、交互响应和前端错误率的正式结论。\n\n**iOS 具备真正性能字段，但需要先做入库质量审计。** 网络时延、状态码、轨迹时长、慢帧和冻结帧是可计算的原生性能信号；当前仅核验了表和字段，尚不能给出趋势、P95 或版本回归结论。"},
                {"id": "capability_table_block", "type": "table", "tableId": "capability_table"},
                {"id": "field_heading", "type": "markdown", "sourceId": "metadata_snapshot", "body": "## 关键字段字典：优先用于受控聚合分析\n\n**H5 网页：** 浏览器、设备品牌/型号、操作系统、屏幕/视口、事件类型、页面标识、停留时长、资源大小、来源与日期。\n\n**页面流量汇总：** 终端类型、版本、页面、浏览量、访客量、停留时长与退出次数。\n\n**iOS Analytics：** 应用版本、系统、设备、事件、地域、归因与隐私状态。\n\n**iOS Performance：** 性能事件类别、应用版本、设备、系统、运营商、网络类型、网络响应码/时序、轨迹时长、慢帧与冻结帧。\n\n完整的 9,795 条字段路径、类型、说明与隐私分类保存在同目录的机器可读清单中；报告阅读版不展开标识、资金、网络地址和原始文本字段。"},
                {"id": "field_table_block", "type": "table", "tableId": "key_field_table"},
                {"id": "gap_heading", "type": "markdown", "sourceId": "metadata_snapshot", "body": "## 关键缺口：不要把代理指标写成性能结论\n\n**H5 当前缺少核心网页性能和前端稳定性事件。** 本轮对已识别的网页事件 schema 搜索后，未发现核心网页指标、资源时序、HTTP 响应、前端错误或白屏字段。页面资源大小、停留时间和退出次数只可作为体验代理。\n\n**Android 与 Crashlytics 的 Firebase 导出未在当前企业库中出现。** 这表示当前元数据盘点下没有相应对象，不等于 Android 没有业务事件；内部起源客户端事件仍保留了部分 Android 终端字段。"},
                {"id": "gap_table_block", "type": "table", "tableId": "gap_table"},
                {"id": "readiness_heading", "type": "markdown", "sourceId": "metadata_snapshot", "body": "## 自动化查询：本机 BigQuery 可用，Gemini/MCP 仍需补齐门禁\n\n**本机企业账号已能在数据项目中执行只读元数据查询。** 但 BigQuery Remote MCP 本轮仍报身份阻断，Gemini 企业 CLI 的结构化任务超时，且允许数据集/授权视图清单为空。因此下一阶段应建立按日、端、版本与页面的脱敏聚合视图，再开放给 Gemini 只读工具。"},
                {"id": "readiness_table_block", "type": "table", "tableId": "readiness_table"},
                {"id": "directory_heading", "type": "markdown", "sourceId": "metadata_snapshot", "body": "## 完整对象与字段目录\n\n**本轮可见的全部 217 个对象、9,795 条字段路径、字段类型、说明和隐私分类已保存到同目录的 `inventory.json`。** 阅读版只保留可行动的对象规模、能力矩阵和关键字段，避免超宽目录表影响手机与桌面阅读。"},
                {"id": "next_steps", "type": "markdown", "body": "## 建议下一步\n\n1. **先做 iOS Performance 入库质量审计：** 核验最新完整日期、记录量、事件类型覆盖、网络/轨迹字段空值和版本覆盖；累计至少 7 个稳定日后再做趋势和异常检测。\n2. **补齐 H5 性能事件：** 增加核心网页指标、导航与资源时序、核心接口、前端错误/白屏，并以按日×页面×设备×版本的聚合表进入企业 BigQuery。\n3. **完成 Android Firebase 导出：** 分别核验三个生产包的 Analytics、Performance 与 Crashlytics 数据集/表/日期，不能以 iOS schema 替代 Android 事实。\n4. **建设授权聚合视图：** 把设备/性能与业务结果连接限制在日×端×版本×页面/事件的脱敏粒度，禁止向 Agent 开放底层标识、订单或资金明细。\n5. **恢复 Gemini 自动查询通道：** 补齐 MCP 企业身份、Vertex 模型调用权限和白名单视图，再以 dry run、扫描量和查询回执作为自动化验收。"},
                {"id": "open_questions", "type": "markdown", "body": "## 待确认问题\n\n- iOS Performance 表是否已产生有效且连续的实际样本？\n- H5 的事件入口与 GA4 独立项目、内部起源网页事件之间应采用哪一套主口径？\n- Android 三个生产包各自的 Firebase 导出当前由哪个项目和区域承载？\n- 哪些业务结果指标可在不暴露标识或资金明细的前提下进入设备/性能聚合视图？"},
                {"id": "caveats", "type": "markdown", "sourceId": "metadata_snapshot", "body": "## 口径与边界\n\n- 本报告范围是企业账户当前可见的 `wajenigeria` 项目元数据，不包含其他项目的表，也不代表企业全量数据资产。\n- 查询只访问 INFORMATION_SCHEMA；未读取业务表行、用户/设备标识值、订单、支付或日志文本。\n- “字段存在”仅说明可设计相应聚合分析，不能证明字段已填充、口径一致或指标已达到生产可用。\n- H5 资源大小、停留和退出等为体验代理，不等同网页加载速度或交互性能。\n- `data_gap`、`immature` 与 `blocked` 均不应解释为零值或性能正常。"},
            ],
        },
        "snapshot": {
            "version": 1,
            "status": "partial",
            "generatedAt": generated,
            "accessIssues": [
                {"scope": "business_data_values", "message": "本报告只读取元数据；未验证行数、最新事件时间、分区连续性、空值、重复率或字段填充率。"},
                {"scope": "bigquery_remote_mcp", "message": "本轮 MCP 元数据请求返回 Auth required。"},
                {"scope": "gemini_enterprise_cli", "message": "本轮结构化元数据任务超时，未产生可审计的模型交接包。"},
                {"scope": "gemini_data_allowlist", "message": "当前允许数据集/授权视图清单为空，不能把底层原始事件直接开放给自动化 Agent。"},
            ],
            "datasets": {
                "summary": [{"dataset_count": summary["datasets"], "object_count": summary["objects"], "field_path_count": summary["field_paths"], "native_performance_table_count": 1}],
                "dataset_inventory": dataset_inventory,
                "object_type_mix": type_rows,
                "capability_matrix": capability_rows,
                "key_fields": selected_fields,
                "gaps": gap_rows,
                "query_readiness": readiness_rows,
                "quality_checks": quality_rows,
                "table_directory": table_directory,
            },
        },
        "package_info": {"classification": "internal_metadata_and_aggregate_analysis", "contains_sensitive_data": False},
    }


def narrative(summary: dict[str, int]) -> str:
    return f"""# Waje 企业 BigQuery 数据资产与设备性能分析能力报告

## 执行摘要

- 当前企业账号在 `wajenigeria` 中可见 **{summary['datasets']} 个数据集、{summary['objects']} 个表/视图/外部表和 {summary['field_paths']:,} 条字段路径**。这一结论来自只读元数据查询，不代表数据行、时效或完整性已经通过审计。
- H5 内部网页事件与页面流量汇总可支持浏览器、系统、品牌/型号、页面、版本、停留、退出和资源体积等分层；但目前没有核心网页指标、资源时序、HTTP 响应或前端错误字段，性能结论为 `data_gap`。
- iOS 已出现 5 张 Analytics 日表和 1 张 Firebase Performance 表。Performance schema 可支持网络时延、响应码、轨迹时长、慢帧和冻结帧分析，但表刚创建，实际数据量、连续性和字段填充率尚未验证。
- 当前未发现 Firebase H5、iOS Crashlytics、iOS Messaging 目录下的对象，也未发现 Firebase Android Analytics/Performance 对象。不要把这种“当前目录无对象”写成产品无数据或性能正常。

## 已核验资产

| 项目 | 结果 |
|---|---:|
| 可见数据集 | {summary['datasets']} |
| 表/视图/外部表 | {summary['objects']} |
| 基础表 / 视图 / 外部表 | {summary['base_tables']} / {summary['views']} / {summary['external_tables']} |
| 字段路径 | {summary['field_paths']:,} |
| 真正原生性能表 | 1（iOS） |

## 设备与性能可用性

### H5 网页终端与行为

已发现网页事件和页面流量汇总 schema。可按浏览器、浏览器版本、设备品牌/型号、操作系统、屏幕/视口、页面、事件、版本、来源和日期做聚合分层；`event_duration`、`page_resource_size`、`stay_time`、`exit_count` 可作为体验代理。

边界：这些字段不能替代 LCP、INP、CLS、FCP、TTFB、接口时延、HTTP 响应率或前端错误率。

### iOS Analytics 与原生性能

`waje_ng_firebase_ios` 含 5 张命名为 `events_YYYYMMDD` 的日表，单表 217 条字段路径，可用于版本、系统、设备、地域、归因和行为事件的聚合切片。

`waje_ng_firebase_ios_performance.com_wajegame_wajegame_IOS` 含 30 条字段路径，涵盖版本、设备、系统、运营商、网络类型、事件类型、网络响应码和时序、轨迹时长、慢帧与冻结帧。它是当前唯一已发现的真实性能 schema，但尚需入库质量审计。

### Android 与 Crashlytics

内部起源客户端事件 schema 中有应用版本、包名、设备、系统、运营商、网络和异常原因等字段，可作为受限终端/异常代理；但当前企业库未发现专用 Firebase Android Analytics/Performance 对象，iOS Crashlytics 目录也没有对象。因此 Android 原生性能与正式稳定性专题仍然是缺口。

## 最小落地路线

1. 对 iOS Performance 表做近 7 个完整日的分区、行数、空值、版本、事件类型和网络/轨迹覆盖审计。
2. 完成三个 Android 包的 Firebase Analytics、Performance 与 Crashlytics 导出核验。
3. H5 接入核心网页指标、资源时序、核心接口和前端错误，并产出脱敏聚合表。
4. 建立按日×端×版本×页面/事件的授权聚合视图，再接入 Gemini 的只读 MCP。

## 审计边界

本报告只读取 `wajenigeria` 的 INFORMATION_SCHEMA 元数据；没有读取业务表行、用户/设备标识、订单、支付或日志内容。字段存在不等于已填充、口径正确或质量已达生产可用。
"""


def main() -> int:
    raw, rows = load_rows()
    full_tables, table_directory, _ = build_inventory(rows)
    datasets = dataset_rows(full_tables)
    type_counts = Counter(table["table_type"] for table in full_tables)
    summary = {
        "datasets": len(DATASETS),
        "objects": len(full_tables),
        "field_paths": sum(table["field_path_count"] for table in full_tables),
        "base_tables": type_counts.get("BASE TABLE", 0),
        "views": type_counts.get("VIEW", 0),
        "external_tables": type_counts.get("EXTERNAL", 0),
    }
    selected = selected_field_rows(rows)
    inventory = {
        "schema_version": 1,
        "status": "partial_metadata_inventory",
        "project_id": "wajenigeria",
        "generated_at": timestamp(),
        "source_snapshot": "raw_metadata/field_inventory.json",
        "privacy_boundary": raw.get("privacy_boundary"),
        "summary": summary,
        "datasets": [{
            **dataset,
            "tables": [table for table in full_tables if table["dataset_id"] == dataset["dataset"]],
        } for dataset in datasets],
    }
    evidence = {
        "project_id": "wajenigeria",
        "identity": "robin@afuruika.net",
        "scope": "Current metadata visible to the enterprise account",
        "metadata_query": {
            "status": "ok",
            "sources": ["INFORMATION_SCHEMA.TABLES", "INFORMATION_SCHEMA.COLUMN_FIELD_PATHS"],
            "locations": ["US", "europe-west4"],
            "business_table_rows_read": False,
            "field_values_read": False,
        },
        "mcp": {"status": "blocked_authentication", "evidence": "bigquery_waje/list_dataset_ids returned Auth required"},
        "gemini": {"status": "failed", "evidence": "enterprise-bq-inventory-20260827 timed out after 180 seconds"},
        "summary": summary,
    }
    artifact = build_artifact(datasets, table_directory, selected, summary)
    # Native wide tables are deliberately retained in the artifact snapshot and
    # inventory.json, but not rendered in the primary reading surface.  The
    # portable reader must remain comfortable at desktop and phone widths; the
    # report narrative and two charts carry the decision path while the full
    # machine-readable directory remains available for lookup.
    artifact["manifest"]["tables"] = []
    artifact["manifest"]["charts"] = [
        chart for chart in artifact["manifest"]["charts"]
        if chart.get("id") == "object_type_mix"
    ]
    artifact["manifest"]["blocks"] = [
        block for block in artifact["manifest"]["blocks"]
        if block.get("type") != "table"
        and (block.get("type") != "chart" or block.get("chartId") == "object_type_mix")
    ]
    artifact["snapshot"]["datasets"] = {
        "summary": artifact["snapshot"]["datasets"]["summary"],
        "object_type_mix": artifact["snapshot"]["datasets"]["object_type_mix"],
    }
    chart_map = [
        {"chart_id": "object_type_mix", "question": "资产由哪些对象类型构成？", "type": "bar", "dataset": "object_type_mix", "fields": ["object_type", "count"], "claim_boundary": "表/视图/外部表类型不代表数据质量或查询权限。"},
    ]
    receipt = {
        "run_id": "enterprise_bq_asset_device_performance_2026_08_27",
        "generated_at": timestamp(),
        "status": "partial",
        "identity": "robin@afuruika.net",
        "project_id": "wajenigeria",
        "metadata_only": True,
        "summary": summary,
        "known_gaps": ["H5 core web performance fields", "Firebase Android Analytics/Performance objects", "Firebase Crashlytics objects", "business-row freshness and quality audit", "Gemini/MCP automated query path"],
        "artifacts": ["inventory.json", "evidence.json", "artifact.json", "chart_map.json", "report.md", "report.html"],
    }
    for path, payload in [(INVENTORY, inventory), (EVIDENCE, evidence), (ARTIFACT, artifact), (CHART_MAP, chart_map), (RECEIPT, receipt)]:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown = narrative(summary)
    REPORT_MD.write_text(markdown, encoding="utf-8")
    KNOWLEDGE_MD.write_text(markdown, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
