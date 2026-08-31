#!/usr/bin/env python3
"""Create a schema-only KYC/Metabase readiness audit without copying PII.

Inputs are the safe Metabase dictionary, the KYC dashboard contract, and
historical KYC design notes.  The generated artifacts intentionally do not
contain source field names for sensitive categories, data rows, default values,
or database credentials.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATE = "2026-08-26"
AUDIT_DIR = ROOT / "analysis" / "kyc_metabase_schema_audit_2026_08_26"
KNOWLEDGE_PATH = ROOT / "knowledge" / "02-数据" / f"KYC人脸识别Metabase数据可用性与埋点缺口审计-{DATE}.md"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def scan_dictionary_privacy_leaks(raw_columns: Path, dictionary_paths: list[Path]) -> dict[str, int]:
    """Count literal candidate names in outputs, never emit the names themselves."""
    patterns = {
        "credential_or_secret": r"(secret|password|passwd|pwd|access[_-]?key|api[_-]?key|token|private[_-]?key|sign(?:ature)?)",
        "identity_or_contact": r"(bvn|nin|phone|mobile|email|id[_-]?card|identity|passport|real[_-]?name|first[_-]?name|last[_-]?name|full[_-]?name|birth[_-]?date)",
        "biometric_or_media": r"(face|biometric|photo|image|portrait|liveness|document)",
        "financial_identifier": r"(bank[_-]?account|account[_-]?(?:no|number)|bank[_-]?card|card[_-]?(?:no|number)|wallet[_-]?address|payee)",
        "network_identifier": r"(^|[_-])ip($|[_-])|ip_address|device[_-]?id|advertising[_-]?id",
        "raw_response": r"(raw[_-]?response|response[_-]?body|request[_-]?body|payload|result[_-]?json)",
    }
    compiled = {key: re.compile(pattern, re.IGNORECASE) for key, pattern in patterns.items()}
    with raw_columns.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    output = "\n".join(path.read_text(encoding="utf-8") for path in dictionary_paths)
    found: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        name = row["COLUMN_NAME"]
        for category, pattern in compiled.items():
            if pattern.search(name) and re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])", output):
                found[category].add(name)
    return {category: len(names) for category, names in sorted(found.items())}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-columns", type=Path, required=True)
    args = parser.parse_args()

    metabase_dir = ROOT / "analysis" / "metabase_schema_inventory_2026_08_26"
    metadata_summary = load_json(metabase_dir / "metadata-summary.json")
    kyc_contract = load_json(ROOT / "analysis" / "kyc_face_2026_08_16" / "metabase_kyc_v1_dashboard_contract.json")
    dict_dir = ROOT / "knowledge" / "02-数据" / "Metabase数据字典"
    dictionary_paths = [
        ROOT / "knowledge" / "02-数据" / "Metabase全库数据资产索引-2026-08-26.md",
        *sorted(dict_dir.glob("2026-08-26-*.md")),
    ]
    privacy_leaks = scan_dictionary_privacy_leaks(args.raw_columns, dictionary_paths)
    privacy_leak_total = sum(privacy_leaks.values())
    generated_at = datetime.now(timezone.utc).isoformat()

    # Statuses are intentionally structural: no table row, freshness, or join data is used.
    capability_rows = [
        {
            "area": "顶部 KPI",
            "status": "schema_supported_candidate",
            "score": 3,
            "candidate_assets": "KYC 日级事件/人脸结果候选表",
            "evidence": "历史 V1 契约列出日级人数；现有字典存在日期、包体和计数型 KYC 候选结构。",
            "blocking_gap": "未执行日级对账、完整日与新鲜度验证。",
        },
        {
            "area": "认证漏斗",
            "status": "partial_schema",
            "score": 2,
            "candidate_assets": "KYC 事件、身份结果与人脸结果候选表",
            "evidence": "触发、身份、人脸和结果阶段有历史定义与候选结构。",
            "blocking_gap": "无稳定流程键、身份通过终态与阶段级关联证据；无结果只能按差值估计。",
        },
        {
            "area": "每日效率趋势",
            "status": "partial_schema",
            "score": 2,
            "candidate_assets": "按日期的 KYC 聚合候选表",
            "evidence": "存在日期和计数型候选结构。",
            "blocking_gap": "数据延迟、完整日、版本/配置切分和日级口径尚未验证。",
        },
        {
            "area": "失败原因诊断",
            "status": "partial_schema",
            "score": 2,
            "candidate_assets": "KYC 失败统计与人脸事件候选表",
            "evidence": "历史文档定义了失败尝试次数与当前保留失败原因。",
            "blocking_gap": "失败历史可被成功状态清理；不是不可变用户级失败轨迹。",
        },
        {
            "area": "流失阶段诊断",
            "status": "partial_schema",
            "score": 2,
            "candidate_assets": "KYC 日级聚合候选表",
            "evidence": "可按阶段差值观察流失。",
            "blocking_gap": "缺 SDK、权限、活体、退出、超时和网络阶段，无法真实归因。",
        },
        {
            "area": "BVN/NIN 对比",
            "status": "not_independently_verified",
            "score": 1,
            "candidate_assets": "身份认证候选表与历史日汇总契约",
            "evidence": "历史 V1 契约支持方式级统计；字典中可见部分身份结果候选结构。",
            "blocking_gap": "当前安全字典不能独立确认两种方式的聚合映射、口径和关联粒度。",
        },
        {
            "area": "端与包体对比",
            "status": "partial_schema",
            "score": 2,
            "candidate_assets": "包体字段与 KYC 候选表",
            "evidence": "主要人脸聚合候选结构中可见包体线索。",
            "blocking_gap": "端类型未观察到稳定字段；包体到 App/H5 的映射未验证。",
        },
        {
            "area": "认证流程筛选",
            "status": "missing_not_observed",
            "score": 0,
            "candidate_assets": "—",
            "evidence": "历史契约要求区分提现触发与主动认证。",
            "blocking_gap": "当前安全字典未观察到稳定流程/场景字段。",
        },
        {
            "area": "渠道、版本、配置、风控规则切分",
            "status": "missing_not_observed",
            "score": 0,
            "candidate_assets": "—",
            "evidence": "历史契约列为未来维度。",
            "blocking_gap": "未观察到渠道、端版本、配置版本和风险规则版本的完整 KYC 链路字段。",
        },
        {
            "area": "认证到最终提现结果",
            "status": "missing_not_observed",
            "score": 0,
            "candidate_assets": "提现订单/审核候选表",
            "evidence": "结构上存在订单状态和审核结果候选表。",
            "blocking_gap": "KYC 与提现终态之间未观察到可验证的一对一关联键。",
        },
    ]

    filter_rows = [
        {"filter": "日期", "status": "schema_supported_candidate", "evidence": "KYC 候选表存在日期/时间线索", "gap": "完整日与时区未验证"},
        {"filter": "认证流程", "status": "missing_not_observed", "evidence": "历史契约要求", "gap": "需新增 kyc_flow / scene"},
        {"filter": "端", "status": "partial_schema", "evidence": "包体可见", "gap": "需稳定 platform 及包体映射"},
        {"filter": "包体", "status": "schema_supported_candidate", "evidence": "主要人脸候选表存在包体线索", "gap": "需日级对账"},
        {"filter": "渠道", "status": "missing_not_observed", "evidence": "历史契约列为未来维度", "gap": "需服务端/客户端统一渠道字段"},
        {"filter": "App/H5 版本", "status": "missing_not_observed", "evidence": "当前安全字典未观察到", "gap": "需 app_version / web_version / build_version"},
        {"filter": "配置/规则版本", "status": "missing_not_observed", "evidence": "当前安全字典未观察到", "gap": "需 config_version / risk_rule_version"},
    ]

    event_rows = [
        {"priority": "P0", "event": "KYC_RISK_DECISION", "authority": "服务端", "purpose": "记录规则触发、拦截或放行", "required_safe_fields": "event_uid, kyc_flow_id, withdraw_id, trace_id, decision, rule_version, event_time_server"},
        {"priority": "P0", "event": "KYC_IDV_RESULT", "authority": "服务端", "purpose": "记录身份认证方法、终态、结果码与耗时", "required_safe_fields": "event_uid, kyc_flow_id, request_id, idv_method, result, error_code, duration_ms, event_time_server"},
        {"priority": "P0", "event": "WITHDRAW_FINAL_RESULT", "authority": "服务端", "purpose": "建立认证到提现最终结果的事实链路", "required_safe_fields": "event_uid, kyc_flow_id, withdraw_id, trace_id, withdraw_status, failure_stage, event_time_server"},
        {"priority": "P0", "event": "KYC_STAGE_RESULT", "authority": "服务端", "purpose": "保存不可变的逐次失败/成功阶段历史", "required_safe_fields": "event_uid, kyc_flow_id, stage, result, error_code, retry_no, event_time_server"},
        {"priority": "P1", "event": "FACE_SDK_LAUNCH_RESULT", "authority": "客户端/SDK", "purpose": "区分 SDK 拉起、黑屏和初始化失败", "required_safe_fields": "event_uid, kyc_flow_id, platform, sdk_version, result, error_code, duration_ms"},
        {"priority": "P1", "event": "FACE_PERMISSION_RESULT", "authority": "客户端", "purpose": "定位相机授权前流失", "required_safe_fields": "event_uid, kyc_flow_id, permission_state, platform, event_time_client"},
        {"priority": "P1", "event": "FACE_LIVENESS_RESULT", "authority": "SDK/服务端", "purpose": "记录活体结果、超时和网络异常", "required_safe_fields": "event_uid, kyc_flow_id, result, error_code, duration_ms, network_type"},
        {"priority": "P1", "event": "FACE_MATCH_RESULT", "authority": "服务端", "purpose": "记录匹配终态和阈值版本", "required_safe_fields": "event_uid, kyc_flow_id, result, error_code, threshold_version, event_time_server"},
        {"priority": "P1", "event": "KYC_STAGE_ABORT", "authority": "客户端", "purpose": "区分主动退出、超时、断网和恢复失败", "required_safe_fields": "event_uid, kyc_flow_id, abort_reason, stage, network_type, event_time_client"},
        {"priority": "P2", "event": "KYC_CONTEXT_SNAPSHOT", "authority": "客户端/服务端", "purpose": "补齐端、版本、渠道与配置切分", "required_safe_fields": "event_uid, kyc_flow_id, platform, package_name, channel, app_version, web_version, config_version, risk_rule_version"},
    ]

    quality_gates = [
        {"gate": "完整日", "rule": "每个统计日有显式 complete_day 标记；不完整日不进入默认 KPI。", "priority": "P0"},
        {"gate": "阶段守恒", "rule": "同一流程内后续阶段不得大于前序阶段；差值进入异常明细。", "priority": "P0"},
        {"gate": "链路完整率", "rule": "KYC 风险、认证、人脸、提现终态可按流程键关联；缺失单独报告。", "priority": "P0"},
        {"gate": "枚举与终态", "rule": "未知 stage/result/error_code 隔离；终态缺失不可视为主动放弃。", "priority": "P1"},
        {"gate": "版本与渠道覆盖", "rule": "核心事件必须可按端、包、版本、渠道和规则版本切分。", "priority": "P1"},
    ]

    source_inventory = [
        {
            "id": "metabase_metadata",
            "label": "Metabase 脱敏 Schema/字段索引（2026-08-26）",
            "path": "analysis/metabase_schema_inventory_2026_08_26/metadata-summary.json",
            "hash": sha256(metabase_dir / "metadata-summary.json"),
            "scope": "6 个 Schema、797 张表、12,251 个字段的元数据；无业务行。",
            "query": {
                "engine": "mysql",
                "language": "sql",
                "sql": "SELECT table_schema AS schema_name, table_name, table_type, table_comment\nFROM information_schema.tables\nWHERE table_schema NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')\nORDER BY table_schema, table_type, table_name;",
                "description": "用户提供的 Metabase information_schema 表清单导出所对应的只读元数据查询；报告中的 Schema 计数由该导出聚合而来。",
                "filters": ["排除 MySQL 系统 Schema", "只读取表/视图元数据，不读取业务数据行"],
                "tables_used": ["information_schema.tables"],
            },
        },
        {
            "id": "kyc_contract",
            "label": "KYC 人脸识别 Metabase 看板 V1 合同",
            "path": "analysis/kyc_face_2026_08_16/metabase_kyc_v1_dashboard_contract.json",
            "hash": sha256(ROOT / "analysis" / "kyc_face_2026_08_16" / "metabase_kyc_v1_dashboard_contract.json"),
            "scope": "V1 卡片、筛选器、已知缺口与敏感字段边界。",
        },
        {
            "id": "kyc_design",
            "label": "KYC 看板 V1 与 2.20 埋点方案",
            "path": "knowledge/02-数据/Waje-KYC人脸识别Metabase看板V1与2.20埋点方案-2026-08-19.md",
            "hash": sha256(ROOT / "knowledge" / "02-数据" / "Waje-KYC人脸识别Metabase看板V1与2.20埋点方案-2026-08-19.md"),
            "scope": "历史指标口径、埋点建议和验收约束。",
        },
        {
            "id": "kyc_history",
            "label": "KYC 人脸识别与提现认证历史分析",
            "path": "knowledge/02-数据/Waje-KYC人脸识别与提现认证分析-2026-08-16.md",
            "hash": sha256(ROOT / "knowledge" / "02-数据" / "Waje-KYC人脸识别与提现认证分析-2026-08-16.md"),
            "scope": "历史问题、口径限制和待补数据；不作为当前 Metabase 实测。",
        },
    ]

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    audit_matrix = {
        "generated_at_utc": generated_at,
        "audit_mode": "schema_only_partial",
        "coverage": metadata_summary["coverage"],
        "dashboard_capabilities": capability_rows,
        "filter_capabilities": filter_rows,
        "tracking_gap_events": event_rows,
        "quality_gates": quality_gates,
        "dictionary_privacy_scan": {
            "candidate_literal_name_count": privacy_leak_total,
            "counts_by_category": privacy_leaks,
            "interpretation": "扩展命名规则下的候选泄露数；不输出字段原名。",
        },
        "evidence_limits": [
            "未读取任何业务数据行、用户明细、KYC 明细、支付明细或第三方原始响应。",
            "未验证外键、真实 join 覆盖、数据新鲜度、完整日、迟到数据、行数或字段非空率。",
            "历史文档中的业务数值仅作为历史上下文，不能解释为当前 Metabase 实测。",
        ],
    }
    (AUDIT_DIR / "audit-matrix.json").write_text(json.dumps(audit_matrix, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (AUDIT_DIR / "source-inventory.json").write_text(json.dumps(source_inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    chart_map = {
        "schema_table_counts": [
            {"schema": key, "table_count": value, "field_count": metadata_summary["coverage"]["schema_field_counts"][key]}
            for key, value in metadata_summary["coverage"]["schema_table_counts"].items()
        ],
        "readiness": [{"area": row["area"], "status": row["status"], "score": row["score"]} for row in capability_rows],
        "priority_counts": [
            {"priority": priority, "gap_count": sum(row["priority"] == priority for row in event_rows)}
            for priority in ("P0", "P1", "P2")
        ],
    }
    (AUDIT_DIR / "chart-data.json").write_text(json.dumps(chart_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def capabilities_table(rows: list[dict[str, Any]]) -> list[str]:
        lines = [
            "| 看板区域/能力 | 结构审计状态 | 候选资产 | 主要阻塞 |",
            "|---|---|---|---|",
        ]
        for row in rows:
            lines.append(
                "| {area} | `{status}` | {assets} | {gap} |".format(
                    area=markdown_escape(row["area"]),
                    status=row["status"],
                    assets=markdown_escape(row["candidate_assets"]),
                    gap=markdown_escape(row["blocking_gap"]),
                )
            )
        return lines

    markdown = [
        "---",
        "type: kyc_metabase_schema_audit",
        f"date: {DATE}",
        "status: partial_schema_only",
        "audience: product-risk",
        "tags: [KYC, 人脸识别, Metabase, 数据审计, 埋点, 风控]",
        "---",
        "",
        "# KYC 人脸识别看板｜Metabase 数据可用性与埋点缺口审计",
        "",
        "> 审计结论：现有结构能够形成 KYC V1 的**候选数据底座**，但尚不能认证为正式看板数据源。缺少稳定流程/端/版本维度、KYC→提现终态关联和 SDK 阶段事实；在完成日级对账、链路核验和数据新鲜度审计前，V1 必须保持 `provisional`。",
        "",
        "## 1. 技术摘要",
        "",
        f"- 已盘点结构：{metadata_summary['coverage']['schema_count']} 个 Schema、{metadata_summary['coverage']['table_count']:,} 张表、{metadata_summary['coverage']['field_count']:,} 个字段；所有结论均为元数据层，不代表数据有值或可用。",
        "- KYC、风险、提现和生命周期提现候选表均可见，具备日期、结果状态、包体或订单状态等片段性线索；外键、行级覆盖和真实链路键未导出。",
        "- P0 数据可信性缺口：认证阶段与最终提现结果无法按稳定流程键验证关联；失败原因不具备不可变历史；字典扩展隐私扫描识别到需修复的脱敏漏网候选。",
        "- 本报告不输出原始身份、支付账户、图像、生物特征、三方响应、默认值或业务数据行。",
        "",
        "## 2. 看板可用性审计",
        "",
        *capabilities_table(capability_rows),
        "",
        "### 全局筛选器",
        "",
        "| 筛选器 | 结构审计状态 | 证据 | 补齐要求 |",
        "|---|---|---|---|",
        *[
            f"| {row['filter']} | `{row['status']}` | {markdown_escape(row['evidence'])} | {markdown_escape(row['gap'])} |"
            for row in filter_rows
        ],
        "",
        "## 3. 可信链路的断点",
        "",
        "```text",
        "风险判定",
        "  → 身份认证请求/结果",
        "  → 人脸 SDK 拉起/权限/活体/匹配",
        "  → 认证终态",
        "  → 提现复核",
        "  → 最终提现结果",
        "```",
        "当前结构可见其中若干表级片段，但没有可验证的统一 `kyc_flow_id + request_id + withdraw_id + trace_id` 关联链。故“人脸成功”不能解释为“提现成功”，而“无最终结果”也不能归因于主动放弃、SDK、网络或服务端失败。",
        "",
        "## 4. P0 数据字典治理发现",
        "",
        f"- 扩展规则在现有字典中识别到 **{privacy_leak_total}** 个可能仍以原名出现的敏感字段候选，涉及 {len(privacy_leaks)} 类命名模式。报告不输出字段原名。",
        "- 风险：当前资料库若被广泛共享，可能暴露身份、媒体、生物特征、账户或网络标识字段名；同时会削弱 KYC 看板的最小权限边界。",
        "- 整改：更新字典脱敏规则，覆盖下划线、驼峰、姓名、图像/生物、账户、网络与密钥命名变体；重新生成所有分册，并以“原始候选字段名零泄漏”作为回归门禁。",
        "",
        "## 5. 研发整改：事件与字段契约",
        "",
        "| 优先级 | 事件 | 事实来源 | 解决的问题 | 最小安全字段 |",
        "|---|---|---|---|---|",
        *[
            f"| {row['priority']} | `{row['event']}` | {row['authority']} | {markdown_escape(row['purpose'])} | `{row['required_safe_fields']}` |"
            for row in event_rows
        ],
        "",
        "公共规则：所有事件仅使用伪标识用户键；服务端终态优先；客户端不得上传身份号码、手机号、图像、证件、生物特征或三方原始响应。核心事件同时携带端、包、版本、渠道、配置/规则版本与客户端/服务端时间。",
        "",
        "## 6. 数据质量门禁",
        "",
        "| 门禁 | 规则 | 优先级 |",
        "|---|---|---|",
        *[f"| {row['gate']} | {markdown_escape(row['rule'])} | {row['priority']} |" for row in quality_gates],
        "",
        "## 7. 范围与待确认项",
        "",
        "- 本次没有执行数据行 SQL，未验证记录数、空值、重复、时延、新鲜度、漏斗数值守恒或跨表 join 覆盖。",
        "- 历史 KYC 文档中的指标与问题只用于定义审计目标，不能视作当前 Metabase 实测。",
        "- 下一轮应先完成脱敏字典回归、KYC 日汇总日级对账和流程键关联审计；之后才适合将 V1 提升为正式看板。",
        "",
        "## 8. 关联资料",
        "",
        "- [[Metabase全库数据资产索引-2026-08-26]]",
        "- [[Metabase-KYC人脸识别看板配置指南-2026-08-19]]",
        "- [[Waje-KYC人脸识别Metabase看板V1与2.20埋点方案-2026-08-19]]",
        "- [[Waje-KYC人脸识别与提现认证分析-2026-08-16]]",
        "",
    ]
    KNOWLEDGE_PATH.write_text("\n".join(markdown), encoding="utf-8")

    # The archive keeps full tables; the portable reader uses narrower
    # card-like narrative sections so long contracts remain readable on mobile.
    capability_markdown = "\n\n".join([
        "### {area}\n\n- **审计状态：** `{status}`\n- **候选资产：** {assets}\n- **主要阻塞：** {gap}".format(
            area=row["area"],
            status=row["status"],
            assets=markdown_escape(row["candidate_assets"]),
            gap=markdown_escape(row["blocking_gap"]),
        )
        for row in capability_rows
    ])
    event_markdown = "\n\n".join([
        "### {priority} · `{event}`\n\n- **事实来源：** {authority}\n- **解决的问题：** {purpose}\n- **最小安全字段：** {fields}".format(
            priority=row["priority"],
            event=row["event"],
            authority=row["authority"],
            purpose=markdown_escape(row["purpose"]),
            fields=markdown_escape(row["required_safe_fields"]).replace(", ", "；"),
        )
        for row in event_rows
    ])

    artifact = {
        "surface": "report",
        "manifest": {
            "version": 1,
            "surface": "report",
            "title": "KYC 人脸识别看板｜Metabase 数据可用性与埋点缺口审计",
            "description": "面向产品与风控负责人的结构审计；不包含业务数据行或敏感身份信息。",
            "generatedAt": generated_at,
            "blocks": [
                {"id": "title", "type": "markdown", "body": "# KYC 人脸识别看板｜Metabase 数据可用性与埋点缺口审计"},
                {"id": "summary", "type": "markdown", "body": "## 技术摘要\n\n**结论：KYC V1 现阶段只能作为候选数据底座，不能认证为正式风控或经营看板。** 结构中存在 KYC、人脸、风险和提现候选资产，但未验证日级对账、完整日、外键或真实链路；认证成功不能等同最终提现成功。\n\n- 现有结构可支持部分 KPI、基础漏斗与包体维度候选分析。\n- 流程、端、版本、配置/规则版本和 KYC→提现终态关联是主要缺口。\n- 字典脱敏规则存在 P0 漏网风险，须先修复后再扩大资料库共享范围。"},
                {"id": "schema_intro", "type": "markdown", "body": "## 可见数据资产范围\n\n本次只验证可见元数据：6 个 Schema、797 张基础表、12,251 个字段。下图显示各 Schema 的表数量，用于说明审计覆盖范围，不表示业务数据量、更新频率或可直接用于 KYC 看板。", "sourceId": "metabase_metadata"},
                {"id": "schema_chart", "type": "chart", "chartId": "schema_distribution_chart"},
                {"id": "readiness_matrix", "type": "markdown", "body": "## KYC 看板能力不是二元判断\n\n`schema_supported_candidate` 表示结构上具备候选字段但仍需日级对账；`partial_schema` 表示可支持部分分析但缺关键维度、关联键或终态；`not_independently_verified` 表示历史资料声称可用、当前安全字典无法独立确认；`missing_not_observed` 表示本次未观察到。\n\n" + capability_markdown},
                {"id": "chain", "type": "markdown", "body": "## 认证到提现的可信链路仍然断裂\n\n风险判定 → 身份认证 → SDK/活体/匹配 → 认证终态 → 提现复核 → 最终提现结果。当前能看到部分表级片段，却没有稳定的流程键、请求键和提现键将它们连成同一条用户流程。\n\n因此，“无最终结果”不能被解释为用户放弃，也不能区分 SDK、权限、网络、超时、服务端或风控拦截；“人脸成功”也不能作为提现成功率。"},
                {"id": "priority_intro", "type": "markdown", "body": "## 整改优先级与研发事件\n\nP0 先修复可信链路与隐私治理；P1 再补齐体验归因和版本/渠道维度；P2 建设认证日汇总与受控下钻模型。\n\n" + event_markdown},
                {"id": "limitations", "type": "markdown", "body": "## 审计边界\n\n本报告仅审计导出的 MySQL 风格元数据和既有 KYC 合同，未读取数据行、用户明细、KYC 明细或支付明细。所有缺失表示“当前安全元数据未观察到或无法独立验证”，不等同生产系统绝对不存在。\n\n下一步应依次完成：字典脱敏回归 → KYC 日汇总日级对账 → 流程键关联审计 → 事件灰度与质量门禁 → V1 正式化。"},
            ],
            "cards": [],
            "charts": [
                {
                    "id": "schema_distribution_chart",
                    "type": "bar",
                    "title": "各 Schema 的可见基础表数量",
                    "subtitle": "仅反映当前账号可见的元数据盘点覆盖，不反映业务数据量。",
                    "dataset": "schema_distribution",
                    "sourceId": "metabase_metadata",
                    "encodings": {"x": {"field": "schema"}, "y": {"field": "table_count"}},
                },
            ],
            "tables": [],
            "sources": source_inventory,
        },
        "snapshot": {
            "version": 1,
            "status": "partial",
            "generatedAt": generated_at,
            "accessIssues": [
                {"scope": "live_metabase_data", "message": "本审计未读取业务数据行，因此无法验证行级覆盖、数据新鲜度、完整日、外键关联和日级对账。"},
            ],
            "datasets": {
                "schema_distribution": chart_map["schema_table_counts"],
            },
        },
        "sources": source_inventory,
        "package_info": {"classification": "internal_schema_audit", "contains_sensitive_data": False},
    }
    (AUDIT_DIR / "artifact.json").write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
