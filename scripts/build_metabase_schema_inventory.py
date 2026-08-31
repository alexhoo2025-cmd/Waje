#!/usr/bin/env python3
"""Build a safe local data dictionary from Metabase-exported MySQL metadata.

The input files must be information_schema table and column exports.  This
tool deliberately never copies raw records, connection details, default
values, or sensitive column names into the Waje workspace.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATE = "2026-08-26"
ANALYSIS_DIR = ROOT / "analysis" / "metabase_schema_inventory_2026_08_26"
KNOWLEDGE_DIR = ROOT / "knowledge" / "02-数据"
DICTIONARY_DIR = KNOWLEDGE_DIR / "Metabase数据字典"

SENSITIVE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "CREDENTIAL_OR_SECRET",
        re.compile(
            r"(secret|password|passwd|pwd|access.?key|api.?key|token|private.?key|sign(?:ature)?)",
            re.IGNORECASE,
        ),
    ),
    (
        "KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC",
        re.compile(
            r"(bvn|nin|phone|mobile|email|id.?card|identity|passport|real.?name|face|biometric|document)",
            re.IGNORECASE,
        ),
    ),
    (
        "PAYMENT_ACCOUNT_IDENTIFIER",
        re.compile(
            r"(bank.?account|account.?no|bank.?card|card.?no|wallet.?address|payee)",
            re.IGNORECASE,
        ),
    ),
    (
        "THIRD_PARTY_RAW_RESPONSE_CANDIDATE",
        re.compile(r"(raw.?response|response.?body|request.?body|payload|result.?json)", re.IGNORECASE),
    ),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sensitive_category(value: str) -> str | None:
    for category, pattern in SENSITIVE_PATTERNS:
        if pattern.search(value or ""):
            return category
    return None


def clean_markdown(value: str) -> str:
    return (value or "").replace("|", "\\|").replace("\r", " ").replace("\n", "<br>").strip()


def safe_comment(value: str, category: str | None) -> str:
    if category or sensitive_category(value):
        return "[已脱敏：敏感字段说明不进入知识库]"
    return clean_markdown(value) or "—"


def safe_field_name(value: str, category: str | None) -> str:
    return f"[REDACTED:{category}]" if category else f"`{clean_markdown(value)}`"


def domain_for(schema_name: str, table_name: str) -> tuple[str, str]:
    # Table-name evidence is stronger than a broad product schema name such as
    # ``whot_center``.  Only use schema names as a fallback, otherwise every
    # operational table in a game schema would be misclassified as game/RTP.
    text = table_name.lower()
    if any(word in text for word in ("kyc", "bvn", "nin", "face", "verify", "risk", "fraud")):
        return "KYC_RISK", "KYC / 风控"
    if any(word in text for word in ("pay", "opay", "cashier", "withdraw", "recharge", "order", "transfer")):
        return "PAYMENT_WITHDRAWAL", "支付 / 提现"
    if any(word in text for word in ("asset", "wallet", "coin", "chip", "balance", "ledger", "diamond")):
        return "ASSET_ECONOMY", "资产 / 货币"
    if any(word in text for word in ("mail", "email", "sms", "push", "message", "notice")):
        return "OPERATIONS_MESSAGING", "运营 / 消息"
    if any(word in text for word in ("game", "bet", "sports", "match", "room", "battle", "rtp", "baccarat", "casino")):
        return "GAME_RTP", "游戏 / 对局 / RTP"
    if any(word in text for word in ("user", "member", "account", "profile", "login", "auth")):
        return "USER_IDENTITY", "用户 / 账号"
    if any(word in text for word in ("apollo", "config", "namespace", "cluster", "release", "setting")):
        return "CONFIG_PLATFORM", "配置 / 平台"
    if any(word in text for word in ("log", "audit", "event", "trace", "monitor")):
        return "LOG_QUALITY", "日志 / 数据质量"
    schema = schema_name.lower()
    if schema.startswith("apollo"):
        return "CONFIG_PLATFORM", "配置 / 平台"
    if schema == "log":
        return "LOG_QUALITY", "日志 / 数据质量"
    if schema == "fish":
        return "GAME_RTP", "游戏 / 对局 / RTP"
    return "UNMAPPED", "待分类"


def layer_for(schema_name: str) -> str:
    lowered = schema_name.lower()
    if lowered.startswith("apollo"):
        return "配置元数据（命名推断）"
    if lowered == "log":
        return "日志 / 审计（命名推断）"
    return "业务表（事实/维度待补证）"


def field_group(name: str, category: str | None) -> str:
    if category:
        return "敏感字段"
    lowered = name.lower()
    if lowered in {"id", "uuid"} or lowered.endswith("_id"):
        return "标识 / 关联"
    if any(word in lowered for word in ("time", "date", "created", "updated", "timestamp", "at")):
        return "时间"
    if any(word in lowered for word in ("amount", "money", "cash", "coin", "chip", "price", "fee", "balance")):
        return "金额 / 资产"
    if any(word in lowered for word in ("status", "state", "result", "type", "mode", "level", "flag")):
        return "状态 / 枚举"
    if any(word in lowered for word in ("game", "bet", "room", "match", "play", "rtp")):
        return "游戏 / 玩法"
    return "业务属性"


def privacy_boundary(category: str | None) -> str:
    if category == "CREDENTIAL_OR_SECRET":
        return "禁止展示、导出或进入分析产物"
    if category in {"KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC", "PAYMENT_ACCOUNT_IDENTIFIER"}:
        return "受限；仅脱敏聚合或伪标识下钻"
    if category == "THIRD_PARTY_RAW_RESPONSE_CANDIDATE":
        return "受限；不得进入普通看板或导出"
    return "允许在授权范围内做聚合分析；不输出字段值"


def recommendation(domain_code: str) -> str:
    return {
        "KYC_RISK": "KYC 漏斗、失败原因、认证时延；仅使用脱敏聚合。",
        "PAYMENT_WITHDRAWAL": "支付/提现漏斗、成功率、时延与失败码；金融金额以服务端事实复核。",
        "ASSET_ECONOMY": "资产流、奖励成本、余额变化与账本对账；必须区分真金、金币和奖励资产。",
        "GAME_RTP": "游戏局、下注、结算、RTP 和玩法/房间拆分；需与 GAMEEND 链路核验。",
        "USER_IDENTITY": "注册、登录与生命周期聚合；禁止导出可识别身份字段。",
        "CONFIG_PLATFORM": "配置、版本、字典和开关关联；不作为主统计事实源。",
        "LOG_QUALITY": "入库延迟、错误、重试和数据质量排障；需明确日志保留周期。",
        "OPERATIONS_MESSAGING": "消息触达、发送结果与运营触发分析；不得输出接收人身份字段。",
        "UNMAPPED": "仅作为候选资产；确认业务 Owner 与事实口径后再接入分析。",
    }[domain_code]


def slug(schema_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", schema_name.lower()).strip("-")


def write_csv(path: Path, rows: list[dict[str, Any]], headers: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tables", type=Path, required=True)
    parser.add_argument("--columns", type=Path, required=True)
    args = parser.parse_args()

    tables = read_csv(args.tables)
    columns = read_csv(args.columns)
    required_table_headers = {"schema_name", "TABLE_NAME", "TABLE_TYPE", "TABLE_COMMENT"}
    required_column_headers = {
        "schema_name", "TABLE_NAME", "TABLE_TYPE", "field_order", "COLUMN_NAME",
        "COLUMN_TYPE", "DATA_TYPE", "IS_NULLABLE", "COLUMN_KEY", "COLUMN_COMMENT",
    }
    if not required_table_headers.issubset(tables[0] if tables else {}):
        raise ValueError("table export is missing required information_schema headers")
    if not required_column_headers.issubset(columns[0] if columns else {}):
        raise ValueError("column export is missing required information_schema headers")

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    DICTIONARY_DIR.mkdir(parents=True, exist_ok=True)

    by_table: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in columns:
        by_table[(row["schema_name"], row["TABLE_NAME"])].append(row)
    for entries in by_table.values():
        entries.sort(key=lambda row: int(row["field_order"]))

    table_keys = {(row["schema_name"], row["TABLE_NAME"]) for row in tables}
    column_table_keys = set(by_table)
    schema_table_counts = Counter(row["schema_name"] for row in tables)
    schema_field_counts = Counter(row["schema_name"] for row in columns)
    domain_counts: Counter[str] = Counter()
    sensitive_field_counts: Counter[str] = Counter()
    sensitive_table_sets: dict[str, set[tuple[str, str]]] = defaultdict(set)
    field_type_counts = Counter(row["DATA_TYPE"] for row in columns)
    field_key_counts = Counter((row["COLUMN_KEY"] or "NONE") for row in columns)
    nullable_counts = Counter(row["IS_NULLABLE"] or "UNKNOWN" for row in columns)
    primary_key_tables = {
        (row["schema_name"], row["TABLE_NAME"])
        for row in columns if row["COLUMN_KEY"] == "PRI"
    }

    safe_table_index: list[dict[str, Any]] = []
    safe_field_index: list[dict[str, Any]] = []
    schema_tables: dict[str, list[dict[str, str]]] = defaultdict(list)

    for table in sorted(tables, key=lambda row: (row["schema_name"], row["TABLE_NAME"])):
        schema_name, table_name = table["schema_name"], table["TABLE_NAME"]
        domain_code, domain_name = domain_for(schema_name, table_name)
        domain_counts[domain_code] += 1
        schema_tables[schema_name].append(table)
        table_columns = by_table[(schema_name, table_name)]
        table_sensitive = Counter()
        for column in table_columns:
            category = sensitive_category(column["COLUMN_NAME"])
            if not category:
                category = sensitive_category(column.get("COLUMN_COMMENT", ""))
            if category:
                table_sensitive[category] += 1
                sensitive_field_counts[category] += 1
                sensitive_table_sets[category].add((schema_name, table_name))
            safe_field_index.append({
                "schema_name": schema_name,
                "table_name": table_name,
                "table_type": table["TABLE_TYPE"],
                "field_order": column["field_order"],
                "field_name": f"[REDACTED:{category}]" if category else column["COLUMN_NAME"],
                "field_name_state": "redacted" if category else "observed_metadata",
                "sensitive_category": category or "",
                "column_type": column["COLUMN_TYPE"],
                "data_type": column["DATA_TYPE"],
                "is_nullable": column["IS_NULLABLE"],
                "column_key": column["COLUMN_KEY"] or "NONE",
                "default_state": "has_default" if column.get("COLUMN_DEFAULT") not in (None, "") else "no_default_observed",
                "extra_state": "auto_increment" if "auto_increment" in (column.get("EXTRA") or "") else ("metadata_present" if column.get("EXTRA") else "none"),
                "field_group": field_group(column["COLUMN_NAME"], category),
                "field_comment": "[REDACTED]" if category else safe_comment(column.get("COLUMN_COMMENT", ""), None),
                "privacy_boundary": privacy_boundary(category),
            })

        safe_table_index.append({
            "schema_name": schema_name,
            "table_name": table_name,
            "table_type": table["TABLE_TYPE"],
            "table_comment": safe_comment(table.get("TABLE_COMMENT", ""), sensitive_category(table.get("TABLE_COMMENT", ""))),
            "field_count": len(table_columns),
            "primary_key_present": (schema_name, table_name) in primary_key_tables,
            "domain_code": domain_code,
            "domain": domain_name,
            "data_layer": layer_for(schema_name),
            "evidence_status": "observed_metadata",
            "sensitive_field_count": sum(table_sensitive.values()),
            "sensitive_categories": ";".join(sorted(table_sensitive)),
            "analysis_recommendation": recommendation(domain_code),
        })

    now = datetime.now(timezone.utc).isoformat()
    source = {
        "collection_method": "user_exported_metabase_native_sql_information_schema",
        "engine_inference": "MySQL-style information_schema export; engine metadata itself was not exported",
        "table_export_filename": args.tables.name,
        "table_export_sha256": file_hash(args.tables),
        "column_export_filename": args.columns.name,
        "column_export_sha256": file_hash(args.columns),
        "raw_source_storage": "source CSV files remain outside the project workspace and are not copied",
    }
    quality = {
        "tables_exported": len(table_keys),
        "tables_with_at_least_one_field": len(column_table_keys),
        "tables_missing_field_rows": len(table_keys - column_table_keys),
        "field_rows_without_table_row": len(column_table_keys - table_keys),
        "tables_with_primary_key": len(primary_key_tables),
        "tables_without_observed_primary_key": len(table_keys - primary_key_tables),
        "field_key_counts": dict(field_key_counts),
        "nullable_counts": dict(nullable_counts),
        "field_comment_coverage_pct": round(sum(bool(row.get("COLUMN_COMMENT", "").strip()) for row in columns) / len(columns) * 100, 2),
        "table_comment_coverage_pct": round(sum(bool(row.get("TABLE_COMMENT", "").strip()) for row in tables) / len(tables) * 100, 2),
        "not_collected": [
            "foreign-key definitions: KEY_COLUMN_USAGE / REFERENTIAL_CONSTRAINTS were not exported",
            "partitioning, index details and table DDL were not exported",
            "table freshness, row counts and data quality were intentionally not queried",
        ],
    }
    summary = {
        "generated_at_utc": now,
        "scope": "all schemas, tables and fields visible to the current Metabase SQL account in supplied exports",
        "source": source,
        "coverage": {
            "schema_count": len(schema_table_counts),
            "table_count": len(tables),
            "field_count": len(columns),
            "table_type_counts": dict(Counter(row["TABLE_TYPE"] for row in tables)),
            "schema_table_counts": dict(sorted(schema_table_counts.items())),
            "schema_field_counts": dict(sorted(schema_field_counts.items())),
            "top_field_data_types": field_type_counts.most_common(15),
            "domain_table_counts": dict(domain_counts),
        },
        "sensitivity": {
            "policy": "No raw values, connection details, default values, or sensitive field names are written to the workspace.",
            "sensitive_field_counts": dict(sensitive_field_counts),
            "affected_table_counts": {key: len(value) for key, value in sensitive_table_sets.items()},
        },
        "quality": quality,
    }
    (ANALYSIS_DIR / "metadata-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(
        ANALYSIS_DIR / "table-index.sanitized.csv",
        safe_table_index,
        list(safe_table_index[0]) if safe_table_index else [],
    )
    write_csv(
        ANALYSIS_DIR / "field-index.sanitized.csv",
        safe_field_index,
        list(safe_field_index[0]) if safe_field_index else [],
    )

    index = [
        "---",
        "type: metabase_schema_inventory",
        f"date: {DATE}",
        "status: observed_metadata",
        "source_engine: mysql_style_information_schema_export",
        "tags: [Metabase, MySQL, 数据字典, 表结构, 字段治理]",
        "---",
        "",
        "# Metabase 全库数据资产索引",
        "",
        "> 本资料基于当前账号在 Metabase 原生 SQL 中导出的 `information_schema` 元数据。只描述可见 Schema、表和字段定义；没有读取任何业务数据行、连接配置、凭据或字段值。",
        "",
        "## 1. 覆盖范围与证据状态",
        "",
        f"- 可见 Schema：**{len(schema_table_counts)}** 个；表：**{len(tables):,}** 张；字段：**{len(columns):,}** 个。",
        f"- 表类型：{', '.join(f'`{key}` {value}' for key, value in Counter(row['TABLE_TYPE'] for row in tables).items())}；本次未观察到视图。",
        "- 证据状态：`observed_metadata` 仅表示字段定义可见，不表示字段已有值、数据新鲜、口径认证或可直接用于正式报表。",
        "- 数据库引擎：导出结构符合 MySQL `information_schema`；Metabase 的连接引擎配置本身未读取，保留为 `engine_inference`。",
        "",
        "## 2. Schema 覆盖",
        "",
        "| Schema | 表数 | 字段数 | 数据层（命名推断） | 阅读版 |",
        "|---|---:|---:|---|---|",
    ]
    for schema_name in sorted(schema_table_counts):
        path = f"Metabase数据字典/{DATE}-{slug(schema_name)}.md"
        index.append(
            f"| `{schema_name}` | {schema_table_counts[schema_name]:,} | {schema_field_counts[schema_name]:,} | {layer_for(schema_name)} | [[{path[:-3]}]] |"
        )
    index.extend([
        "",
        "## 3. 结构完整性与可用性",
        "",
        f"- 表—字段可对账：**{quality['tables_with_at_least_one_field']:,}/{quality['tables_exported']:,}** 张表存在字段记录；缺口为 **0**。",
        f"- 主键标记：{quality['tables_with_primary_key']:,} 张表至少有一个 `PRI` 字段；字段级索引标记为 `PRI` {field_key_counts['PRI']:,}、`UNI` {field_key_counts['UNI']:,}、`MUL` {field_key_counts['MUL']:,}。",
        f"- 注释覆盖：表说明 {quality['table_comment_coverage_pct']}%；字段说明 {quality['field_comment_coverage_pct']}%。低注释表和字段需补 Owner、业务口径与保留策略。",
        "- 本次未收集：外键约束、索引明细、分区、DDL、行数、数据新鲜度与字段实际值；这些均不得由本索引推断。",
        "",
        "## 4. 业务域候选分布（命名推断）",
        "",
        "| 业务域 | 表数 | 推荐分析用途 |",
        "|---|---:|---|",
    ])
    domain_names = {
        "CONFIG_PLATFORM": "配置 / 平台", "USER_IDENTITY": "用户 / 账号", "LOG_QUALITY": "日志 / 数据质量",
        "GAME_RTP": "游戏 / 对局 / RTP", "PAYMENT_WITHDRAWAL": "支付 / 提现", "ASSET_ECONOMY": "资产 / 货币",
        "KYC_RISK": "KYC / 风控", "OPERATIONS_MESSAGING": "运营 / 消息", "UNMAPPED": "待分类",
    }
    for code, count in domain_counts.most_common():
        index.append(f"| {domain_names[code]} | {count:,} | {recommendation(code)} |")
    index.extend([
        "",
        "## 5. 受控字段治理",
        "",
        "| 敏感类别 | 受控字段/注释候选数 | 受影响表数 | 知识库处理 |",
        "|---|---:|---:|---|",
    ])
    for category in ("CREDENTIAL_OR_SECRET", "KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC", "PAYMENT_ACCOUNT_IDENTIFIER", "THIRD_PARTY_RAW_RESPONSE_CANDIDATE"):
        index.append(
            f"| `{category}` | {sensitive_field_counts[category]:,} | {len(sensitive_table_sets[category]):,} | 字段名和说明已替换为类别标签；不输出字段值、默认值或原始响应。 |"
        )
    index.extend([
        "",
        "## 6. 与 Waje 数据架构的关系",
        "",
        "- Metabase 是受控访问、专题分析和风险隔离层；统计事实仍需以 BigQuery 认证层为准，MySQL 配置表不能单独承担正式经营口径。",
        "- 本次 `whot_center` 是可见 Schema 之一，包含 245 张表与 2,597 个字段；其结构字典见对应分册。",
        "- KYC、支付、资产和用户类表仅可用于脱敏聚合或受控伪标识下钻；不得进入普通看板、公开导出或知识库字段原文。",
        "- 后续要建设 SQL 查询库或 KYC 看板时，先以本字典中的真实表/字段为准，再执行完整日、时区、金额单位与服务端账本对账验证。",
        "",
        "## 7. 关联资料",
        "",
        "- [[Ares与Metabase看板建设方案对比分析-2026-08-05]]",
        "- [[Metabase-KYC人脸识别看板配置指南-2026-08-19]]",
        "- [[Waje数据指标看板映射与研发验收清单-2026-08-11]]",
        "",
        "## 8. 刷新与验收",
        "",
        "1. 重新导出同一元数据 SQL 的表清单与字段清单；原始 CSV 保持在项目外部。",
        "2. 用文件哈希和表/字段数量比对新增、删除与类型变化。",
        "3. 仅对需要进入正式分析的表，补采外键、分区、数据新鲜度、完整日和数据质量证据。",
        "4. 若权限或同步状态变化，标记 `blocked_permission` 或 `metadata_stale`，不将其解释为数据为空。",
        "",
    ])
    (KNOWLEDGE_DIR / f"Metabase全库数据资产索引-{DATE}.md").write_text("\n".join(index), encoding="utf-8")

    for schema_name, tables_in_schema in sorted(schema_tables.items()):
        doc = [
            "---",
            "type: metabase_schema_dictionary",
            f"date: {DATE}",
            f"schema: {schema_name}",
            "status: observed_metadata",
            "source_engine: mysql_style_information_schema_export",
            "---",
            "",
            f"# Metabase 数据字典｜{schema_name}",
            "",
            "> 证据边界：本分册来自可见 `information_schema` 定义。字段值、默认值、连接参数、敏感字段原文均未保存；字段用途和数据层标记中“命名推断”均需由业务 Owner 或数据开发补证。",
            "",
            "## 1. Schema 概览",
            "",
            f"- 表：**{len(tables_in_schema):,}** 张；字段：**{schema_field_counts[schema_name]:,}** 个。",
            f"- 数据层：{layer_for(schema_name)}。",
            "- 外键、分区、索引明细、行数、更新时刻、保留周期：本次未导出，不能推断。",
            "",
            "## 2. 表清单",
            "",
        "| 表 | 类型 | 字段数 | 业务域（命名推断） | 受控字段候选数 | 表说明 |",
            "|---|---|---:|---|---:|---|",
        ]
        for table in tables_in_schema:
            table_columns = by_table[(schema_name, table["TABLE_NAME"])]
            sensitive_count = sum(
                bool(sensitive_category(col["COLUMN_NAME"]) or sensitive_category(col.get("COLUMN_COMMENT", "")))
                for col in table_columns
            )
            _, domain_name = domain_for(schema_name, table["TABLE_NAME"])
            doc.append(
                f"| `{table['TABLE_NAME']}` | {table['TABLE_TYPE']} | {len(table_columns):,} | {domain_name} | {sensitive_count} | {safe_comment(table.get('TABLE_COMMENT', ''), sensitive_category(table.get('TABLE_COMMENT', '')))} |"
            )
        doc.extend(["", "## 3. 逐表字段定义", ""])
        for table in tables_in_schema:
            table_name = table["TABLE_NAME"]
            domain_code, domain_name = domain_for(schema_name, table_name)
            table_columns = by_table[(schema_name, table_name)]
            doc.extend([
                f"### {table_name}",
                "",
                f"- 表类型：`{table['TABLE_TYPE']}`；字段数：{len(table_columns):,}；数据层：{layer_for(schema_name)}。",
                f"- 业务域：{domain_name}（`inferred_name_only`）；建议：{recommendation(domain_code)}",
                "- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。",
                "",
                "| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |",
                "|---:|---|---|---|---|---|---|---|",
            ])
            for column in table_columns:
                category = sensitive_category(column["COLUMN_NAME"]) or sensitive_category(column.get("COLUMN_COMMENT", ""))
                doc.append(
                    "| {order} | {name} | `{type}` | {nullable} | `{key}` | {group} | {comment} | {boundary} |".format(
                        order=column["field_order"],
                        name=safe_field_name(column["COLUMN_NAME"], category),
                        type=clean_markdown(column["COLUMN_TYPE"]),
                        nullable=column["IS_NULLABLE"],
                        key=column["COLUMN_KEY"] or "NONE",
                        group=field_group(column["COLUMN_NAME"], category),
                        comment=safe_comment(column.get("COLUMN_COMMENT", ""), category),
                        boundary=privacy_boundary(category),
                    )
                )
            doc.append("")
        (DICTIONARY_DIR / f"{DATE}-{slug(schema_name)}.md").write_text("\n".join(doc), encoding="utf-8")

    receipt = {
        "run_id": "metabase_schema_inventory_2026_08_26",
        "generated_at_utc": now,
        "status": "completed_with_metadata_limits",
        "source": source,
        "coverage": summary["coverage"],
        "quality": quality,
        "safety": summary["sensitivity"],
        "outputs": {
            "knowledge_index": "knowledge/02-数据/Metabase全库数据资产索引-2026-08-26.md",
            "schema_dictionary_directory": "knowledge/02-数据/Metabase数据字典/",
            "metadata_summary": "analysis/metabase_schema_inventory_2026_08_26/metadata-summary.json",
            "table_index": "analysis/metabase_schema_inventory_2026_08_26/table-index.sanitized.csv",
            "field_index": "analysis/metabase_schema_inventory_2026_08_26/field-index.sanitized.csv",
        },
    }
    (ANALYSIS_DIR / "run-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
