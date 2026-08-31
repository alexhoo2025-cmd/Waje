#!/usr/bin/env python3
"""Build the canonical portable report artifact for the Android BQ SQL pack."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SQL_ROOT = ROOT / "sql"
REL_ROOT = "analysis/android_bq_api_validation_2026_08_27"

QUERY_SPECS = [
    {
        "id": "q00_metadata_columns",
        "file": "00_metadata_columns.sql",
        "title": "字段与源表元数据核验",
        "purpose": "确认 Android Analytics、Performance、Sessions 来源表的字段、类型和排序位置。",
        "tables": [
            "wajenigeria.waje_ng_firebase_android.events_*",
            "wajenigeria.waje_ng_firebase_android_performance.*",
            "wajenigeria.waje_ng_firebase_android_sessions.*",
        ],
        "filters": ["INFORMATION_SCHEMA 元数据范围", "三个 Android 来源数据集"],
        "definitions": ["只返回元数据字段，不读取业务表行。"],
    },
    {
        "id": "q01_performance_daily_coverage",
        "file": "01_performance_daily_coverage.sql",
        "title": "实时读取与每日 Performance 覆盖",
        "purpose": "验证三个 Android 包在 2026-08-20 至 2026-08-26 的日期、事件类型、记录量和版本覆盖。",
        "tables": [
            "wajenigeria.waje_ng_firebase_android_performance.com_hfhy_waje_special_ANDROID",
            "wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_palmgame_ANDROID",
            "wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_game_ANDROID",
        ],
        "filters": ["DATE(event_timestamp, 'Africa/Lagos') BETWEEN 2026-08-20 AND 2026-08-26"],
        "definitions": ["目标结果最多 21 行：7 个日期 × 3 个 Android 包。"],
    },
    {
        "id": "q02_performance_metric_aggregates",
        "file": "02_performance_metric_aggregates.sql",
        "title": "P90、网络成功率与帧比例聚合",
        "purpose": "复算轨迹时长 P90、网络响应 P90、HTTP 成功率和慢帧/冻结帧 trace 加权均值。",
        "tables": [
            "wajenigeria.waje_ng_firebase_android_performance.com_hfhy_waje_special_ANDROID",
            "wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_palmgame_ANDROID",
            "wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_game_ANDROID",
        ],
        "filters": ["DATE(event_timestamp, 'Africa/Lagos') BETWEEN 2026-08-20 AND 2026-08-26", "P90 合格样本至少 500"],
        "definitions": [
            "P90 使用 APPROX_QUANTILES；样本不足 500 时返回 NULL。",
            "网络成功率 = HTTP 200–399 响应数 ÷ 有响应码请求数。",
            "慢帧/冻结帧为 SCREEN_TRACE 的 trace 加权均值，不是用户比例。",
        ],
    },
    {
        "id": "q03_device_os_mix",
        "file": "03_device_os_mix.sql",
        "title": "设备型号与系统版本结构",
        "purpose": "识别性能记录集中在哪些设备型号和 Android 系统版本，供兼容性测试优先级使用。",
        "tables": [
            "wajenigeria.waje_ng_firebase_android_performance.com_hfhy_waje_special_ANDROID",
            "wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_palmgame_ANDROID",
            "wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_game_ANDROID",
        ],
        "filters": ["DATE(event_timestamp, 'Africa/Lagos') BETWEEN 2026-08-20 AND 2026-08-26", "每个设备/系统聚合组至少 10 条记录", "每日每包最多 50 个组"],
        "definitions": ["仅输出聚合后的设备名称与系统版本，不输出设备唯一标识。"],
    },
    {
        "id": "q04_network_quality",
        "file": "04_network_quality.sql",
        "title": "网络响应码、延迟与缺失率",
        "purpose": "验证网络请求响应码填充、HTTP 错误、成功率和网络延迟 P90。",
        "tables": [
            "wajenigeria.waje_ng_firebase_android_performance.com_hfhy_waje_special_ANDROID",
            "wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_palmgame_ANDROID",
            "wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_game_ANDROID",
        ],
        "filters": ["DATE(event_timestamp, 'Africa/Lagos') BETWEEN 2026-08-20 AND 2026-08-26", "event_type = NETWORK_REQUEST", "每个日期/包/版本至少 10 条请求"],
        "definitions": ["不返回 URL、请求名、请求正文或响应正文。"],
    },
    {
        "id": "q05_sessions_reconciliation",
        "file": "05_sessions_reconciliation.sql",
        "title": "Sessions 与 Performance 采集标记对照",
        "purpose": "检查去标识化会话量与 Performance/Crashlytics 采集标记的关系，识别开关与实际表数据冲突。",
        "tables": [
            "wajenigeria.waje_ng_firebase_android_sessions.com_hfhy_waje_special_ANDROID",
            "wajenigeria.waje_ng_firebase_android_sessions.com_hfhy_wajecasino_palmgame_ANDROID",
            "wajenigeria.waje_ng_firebase_android_sessions.com_hfhy_wajecasino_game_ANDROID",
        ],
        "filters": ["DATE(event_timestamp, 'Africa/Lagos') BETWEEN 2026-08-20 AND 2026-08-26"],
        "definitions": [
            "distinct_session_count 只在 COUNT(DISTINCT session_id) 内使用。",
            "Analytics session_start 事件数不与 Sessions 唯一会话数混称。",
        ],
    },
    {
        "id": "q06_android_analytics_mix",
        "file": "06_android_analytics_mix.sql",
        "title": "Android Analytics 包体、设备与事件结构",
        "purpose": "验证三个 Android 包的日表覆盖，并按包体、版本、设备维度和事件进行聚合。",
        "tables": ["wajenigeria.waje_ng_firebase_android.events_*"],
        "filters": ["_TABLE_SUFFIX BETWEEN 20260820 AND 20260826", "platform = ANDROID", "仅三个已登记包体", "每个聚合组至少 10 条事件"],
        "definitions": ["事件数量是行为事件记录数，不是用户数、会话数、订单数或收入。"],
    },
    {
        "id": "q07_formula_reconciliation",
        "file": "07_formula_reconciliation.sql",
        "title": "事件类型可加总性与值域检查",
        "purpose": "检查事件类型分项是否能回到源记录总量，并识别负时长、负延迟、非法帧比例和缺失响应码。",
        "tables": [
            "wajenigeria.waje_ng_firebase_android_performance.com_hfhy_waje_special_ANDROID",
            "wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_palmgame_ANDROID",
            "wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_game_ANDROID",
        ],
        "filters": ["DATE(event_timestamp, 'Africa/Lagos') BETWEEN 2026-08-20 AND 2026-08-26"],
        "definitions": ["异常返回 quality_status，不删除原始记录，不补零。"],
    },
]


def source_for(spec: dict, sql: str) -> dict:
    return {
        "id": spec["id"],
        "label": f"BigQuery SQL｜{spec['title']}",
        "path": f"{REL_ROOT}/sql/{spec['file']}",
        "query": {
            "engine": "BigQuery",
            "language": "SQL",
            "description": spec["purpose"],
            "sql": sql,
            "tables_used": spec["tables"],
            "filters": spec["filters"],
            "metric_definitions": spec["definitions"],
            "status": "prepared_not_executed",
        },
    }


def build_artifact() -> dict:
    generated = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(timespec="seconds")
    sources: list[dict] = []
    query_rows: list[dict] = []
    sql_blocks: list[dict] = []

    for number, spec in enumerate(QUERY_SPECS):
        sql = (SQL_ROOT / spec["file"]).read_text(encoding="utf-8").strip()
        sources.append(source_for(spec, sql))
        query_rows.append(
            {
                "id": spec["id"],
                "title": spec["title"],
                "purpose": spec["purpose"],
                "file": f"sql/{spec['file']}",
                "static_status": "passed",
                "live_status": "blocked_authentication",
            }
        )
        sql_blocks.append(
            {
                "id": f"sql_{number:02d}_{spec['id']}",
                "type": "markdown",
                "body": (
                    f"## {number}. {spec['title']}\n\n"
                    f"{spec['purpose']}\n\n"
                    f"**执行文件：** `{REL_ROOT}/sql/{spec['file']}`\n\n"
                    f"```sql\n{sql}\n```"
                ),
                "sourceId": spec["id"],
            }
        )

    validation_rows = [
        {"check": "BigQuery API/MCP 身份", "expected": "可调用项目 wajenigeria 的只读元数据工具", "status": "blocked", "evidence": "list_dataset_ids 返回 Auth required"},
        {"check": "SQL 静态策略", "expected": "8 条查询全部通过只读、聚合、日期和结果行数约束", "status": "passed", "evidence": "8/8 passed"},
        {"check": "实时源表读取", "expected": "三个 Android Performance 表返回目标日期数据", "status": "not_run", "evidence": "认证阻断"},
        {"check": "P90 与网络公式", "expected": "按有效样本和正确分母复算", "status": "not_run", "evidence": "认证阻断"},
        {"check": "设备/系统聚合", "expected": "仅保留达到最小样本量的聚合组", "status": "not_run", "evidence": "认证阻断"},
        {"check": "Sessions 对照", "expected": "标记 Performance 开关与实际记录冲突", "status": "not_run", "evidence": "认证阻断"},
    ]

    summary = [{"sql_count": 8, "static_pass_count": 8, "live_executed_count": 0, "data_rows_read": 0}]

    source_registry = {
        "id": "local_contract",
        "label": "既有 Android 设备/性能看板数据合同",
        "path": "analysis/multiplatform_device_performance_dashboard_v1_2026_08_27/data_contract.json",
        "query": {
            "engine": "Local JSON contract",
            "language": "JSON",
            "description": "提供三个 Android 包、字段口径、P90 样本门槛和隐私边界；不作为本次实时查询结果。",
        },
    }
    validation_source = {
        "id": "static_validation",
        "label": "本地 SQL 只读策略校验",
        "path": f"{REL_ROOT}/static-validation.json",
        "query": {
            "engine": "SQLite (local artifact validation)",
            "language": "SQL",
            "description": "对 8 条 SQL 检查单条 SELECT/WITH、无写入/导出、无 SELECT *、日期过滤、聚合结果和 3000 行上限。",
            "sql": "WITH stage_counts(stage, count) AS (SELECT 'SQL 静态校验通过', 8 UNION ALL SELECT '实时查询已执行', 0 UNION ALL SELECT '业务数据行已读取', 0) SELECT stage, count FROM stage_counts;",
            "tables_used": ["local artifact: static-validation.json"],
            "filters": ["8 条 SQL 静态校验结果", "不读取 BigQuery 业务数据"],
            "metric_definitions": ["数量是本地验证阶段计数，不是业务数据量。"],
        },
    }
    sources.extend([source_registry, validation_source])

    manifest = {
        "version": 1,
        "surface": "report",
        "title": "Android BigQuery API 查询与聚合验证｜SQL 阅读版",
        "description": "面向数据、研发和分析人员的 Android 设备/性能 BigQuery 只读查询验证包；包含可直接粘贴到 BigQuery 查询编辑器的 SQL。",
        "generatedAt": generated,
        "sources": sources,
        "accessIssues": [
            "本次 BigQuery 只读工具预检返回 Auth required，实时查询尚未执行。",
            "remote_udf_conn 是远程资源连接，不是 BigQuery 查询登录凭证。",
            "当前报告不把上一轮本地基线数字冒充成此次实时 API 结果。",
        ],
        "statusDefinitions": {
            "passed": "本地静态校验或明确的 live check 通过。",
            "blocked_authentication": "BigQuery API/MCP 身份不可用；不是无数据。",
            "not_run": "依赖实时权限或源表回读，当前未执行。",
            "provisional": "有数据但仍需口径、完整日或字段质量复核。",
        },
        "cards": [
            {"id": "sql_count", "dataset": "summary", "sourceId": "static_validation", "metrics": [{"label": "已准备 SQL", "field": "sql_count", "format": "number"}]},
            {"id": "static_pass", "dataset": "summary", "sourceId": "static_validation", "metrics": [{"label": "静态校验通过", "field": "static_pass_count", "format": "number"}]},
            {"id": "live_count", "dataset": "summary", "sourceId": "static_validation", "metrics": [{"label": "已执行实时查询", "field": "live_executed_count", "format": "number"}]},
            {"id": "rows_read", "dataset": "summary", "sourceId": "static_validation", "metrics": [{"label": "本次读取数据行", "field": "data_rows_read", "format": "number"}]},
        ],
        "charts": [
            {
                "id": "verification_stage",
                "title": "验证阶段数量",
                "subtitle": "静态 SQL 检查已完成；实时查询因身份认证未执行。",
                "dataset": "stage_counts",
                "sourceId": "static_validation",
                "type": "bar",
                "layout": "full",
                "encodings": {
                    "x": {"field": "stage", "type": "nominal", "label": "阶段"},
                    "y": {"field": "count", "type": "quantitative", "format": "number", "label": "数量"},
                },
                "settings": {"sort": "none", "showValues": True},
            }
        ],
        "tables": [
            {
                "id": "query_catalog",
                "title": "查询目录与当前状态",
                "subtitle": "8 条可复制 SQL；静态策略全部通过，实时执行因身份认证阻断。",
                "dataset": "query_catalog",
                "sourceId": "static_validation",
                "density": "spacious",
                "layout": "full",
                "columns": [
                    {"field": "id", "label": "编号", "type": "text"},
                    {"field": "title", "label": "查询名称", "type": "text"},
                    {"field": "purpose", "label": "用途", "type": "text"},
                    {"field": "file", "label": "文件", "type": "text"},
                    {"field": "static_status", "label": "静态校验", "type": "text"},
                    {"field": "live_status", "label": "实时状态", "type": "text"},
                ],
                "defaultSort": {"field": "id", "direction": "asc"},
            },
            {
                "id": "validation_matrix",
                "title": "验收矩阵",
                "subtitle": "认证恢复后按此顺序执行；阻断、未成熟和无数据不转成数字零。",
                "dataset": "validation_matrix",
                "sourceId": "static_validation",
                "density": "spacious",
                "layout": "full",
                "columns": [
                    {"field": "check", "label": "检查项", "type": "text"},
                    {"field": "expected", "label": "通过条件", "type": "text"},
                    {"field": "status", "label": "状态", "type": "text"},
                    {"field": "evidence", "label": "证据/阻断原因", "type": "text"},
                ],
                "defaultSort": {"field": "check", "direction": "asc"},
            },
        ],
        "blocks": [
            {"id": "title", "type": "markdown", "body": "# Android BigQuery API 查询与聚合验证｜SQL 阅读版"},
            {
                "id": "summary",
                "type": "markdown",
                "sourceId": "static_validation",
                "body": "## Technical Summary｜先看结果\n\n**8 条 Android 设备/性能只读 SQL 已准备完成，静态安全校验 8/8 通过；本次实时 BigQuery 查询尚未执行。** 项目级预检在 `wajenigeria` 返回 `Auth required`，因此当前不能对真实数据的日期覆盖、记录量、P90、网络成功率或设备分布做实时结论。\n\n**这不是“没有安卓数据”。** 当前阻断发生在 API/MCP 身份层；上一轮本地基线只作为口径参考，没有被当作本次实时查询结果。\n\n**执行区域固定为 `europe-west4`，业务时区固定为 `Africa/Lagos`。** 页面登录、`remote_udf_conn` 连接资源和 BigQuery API 调用身份是三个不同层次。",
            },
            {"id": "metrics", "type": "metric-strip", "cardIds": ["sql_count", "static_pass", "live_count", "rows_read"]},
            {"id": "stage_chart_block", "type": "chart", "chartId": "verification_stage"},
            {
                "id": "scope",
                "type": "markdown",
                "sourceId": "local_contract",
                "body": "## 验证范围与指标口径\n\n| 项目 | 口径 |\n|---|---|\n| 项目 | `wajenigeria` |\n| 查询位置 | `europe-west4` |\n| 时间窗口 | 2026-08-20 至 2026-08-26，7 个完整日 |\n| 时区 | `Africa/Lagos` |\n| Android 包 | `com.hfhy.waje.special`、`com.hfhy.wajecasino.palmgame`、`com.hfhy.wajecasino.game` |\n| P90 门槛 | 有效样本至少 500；不足返回 `NULL` |\n| 分层门槛 | 设备/系统聚合组至少 10 条记录 |\n| 隐私边界 | 不返回用户标识、设备唯一标识、URL、请求/响应正文或堆栈 |\n\n**主要指标：** DURATION_TRACE 时长 P90、NETWORK_REQUEST 响应耗时 P90、HTTP 200–399 成功率、SCREEN_TRACE 慢帧/冻结帧 trace 加权均值、Performance 记录覆盖、Sessions 唯一会话数和 Analytics 事件量。",
            },
            {"id": "run_order", "type": "markdown", "body": "## 页面执行顺序\n\n1. 在 BigQuery 查询编辑器中选择项目 `wajenigeria`。\n2. 将 Processing location 设置为 `europe-west4`。\n3. 使用 GoogleSQL。\n4. 先执行“字段与源表元数据核验”。\n5. 再执行“实时读取与每日 Performance 覆盖”。\n6. 覆盖返回日期、包体和记录量后，再执行 P90、网络、设备和 Sessions 聚合。\n7. 最后执行 Analytics 与公式检查。\n8. 每条查询保留 Job ID、扫描字节数、返回行数、数据截止时间和错误信息。\n\n**不要把 `remote_udf_conn` 写到普通表查询的 `FROM` 中。** 它是远程函数/远程模型连接资源，不是普通表查询的认证方式。",
            },
            {"id": "catalog_heading", "type": "markdown", "body": "## 查询目录\n\n下表说明每条 SQL 的用途和状态。代码区块保留完整 SQL，可直接复制到 BigQuery 查询编辑器。"},
            {"id": "catalog_table", "type": "table", "tableId": "query_catalog"},
            {"id": "sql_heading", "type": "markdown", "body": "## 完整 SQL 查询\n\n所有查询均为单条 `SELECT/WITH`，带日期或分区过滤，只输出聚合结果，最大返回 3,000 行。"},
            *sql_blocks,
            {"id": "quality_heading", "type": "markdown", "body": "## 验收矩阵与数据质量规则\n\n实时权限恢复后，必须完成以下检查。认证失败、权限不足、日期不完整、数据延迟和未成熟数据均保留状态，不转换为零值。"},
            {"id": "quality_table", "type": "table", "tableId": "validation_matrix"},
            {
                "id": "interpretation",
                "type": "markdown",
                "body": "## 结果解释边界\n\n- `duration_p90_ms` 或 `network_p90_ms` 为 `NULL` 时，优先解释为样本不足或有效值不足，不自动解释为性能缺失。\n- `network_success_rate` 的分母是有响应码的网络请求，不是全部请求，也不是业务登录成功率。\n- Analytics 的 `session_start` 是事件记录数，不能直接替代 Sessions 表的 `COUNT(DISTINCT session_id)`。\n- Performance 表有记录而 Sessions 中 Performance 开关为 `false` 时，应标记为数据质量冲突，不能写成 SDK 未接入。\n- 设备型号分层是聚合样本，不代表独立设备数；不输出设备唯一标识。\n- 只有完成实时查询、字段核对、扫描量检查和公式复算后，才可把结果用于安卓版本或设备兼容性判断。",
            },
            {"id": "status", "type": "markdown", "body": "## 当前阻断与继续条件\n\n当前状态为 **`blocked_authentication`**：`bigquery_waje/list_dataset_ids` 返回 `Auth required`。请恢复当前 BigQuery API/MCP 调用身份，并确认目标 Android 数据集或已批准的只读聚合视图。恢复后按上面的顺序执行；不要使用个人密钥回退，也不要把 Google Cloud 控制台的浏览器登录当作本地 API 已认证。"},
            {"id": "next_steps", "type": "markdown", "body": "## 下一步\n\n1. 恢复 BigQuery API/MCP 的 OAuth/ADC 身份。\n2. 确认 `waje_ng_firebase_android`、`waje_ng_firebase_android_performance`、`waje_ng_firebase_android_sessions` 的实际位置和字段。\n3. 先 dry run，单查询扫描量不超过 5 GiB，整轮不超过 25 GiB。\n4. 执行 8 条 SQL 并补齐 live query receipt。\n5. 由数据质量检查复核日期连续性、空值、重复、分母和跨来源冲突。\n6. 只有实时结果通过后，再生成设备/性能分析报告或接入聚合看板。"},
            {"id": "caveats", "type": "markdown", "sourceId": "local_contract", "body": "## Caveats and assumptions\n\n- 本 HTML 是 SQL 与验收流程阅读版，不是本次实时业务数据结果。\n- 来源表名和字段来自既有项目数据合同，实时存在性和类型必须由元数据查询重新确认。\n- 所有业务性能、稳定性和转化结论必须建立在实时聚合、数据截止时间和成熟度校验之上。\n- 当前不输出任何用户级、设备唯一标识、订单、支付、URL、Cookie、Token 或原始请求/响应内容。"},
        ],
    }

    return {
        "surface": "report",
        "manifest": manifest,
        "snapshot": {
            "version": 1,
            "generatedAt": generated,
            "status": "blocked",
            "accessIssues": [
                {"scope": "bigquery_authentication", "message": "bigquery_waje/list_dataset_ids returned Auth required."},
                {"scope": "live_data", "message": "No live business rows were read in this run."},
                {"scope": "source_approval", "message": "Governed MCP active authorized views remain empty; source table mapping is pending live metadata confirmation."},
            ],
            "datasets": {
                "summary": summary,
                "stage_counts": [
                    {"stage": "SQL 静态校验通过", "count": 8},
                    {"stage": "实时查询已执行", "count": 0},
                    {"stage": "业务数据行已读取", "count": 0},
                ],
                "query_catalog": query_rows,
                "validation_matrix": validation_rows,
            },
        },
        "sources": sources,
        "package_info": {
            "classification": "internal_sql_methodology_and_access_status",
            "contains_sensitive_data": False,
        },
    }


def main() -> None:
    output = ROOT / "artifact.json"
    output.write_text(json.dumps(build_artifact(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
