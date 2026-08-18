#!/usr/bin/env python3
"""Build the canonical Data Analytics report artifact from verified summary data."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any


def pct(value: float | None) -> str:
    return "—" if value is None else f"{value * 100:.1f}%"


def pp(current: float | None, prior: float | None) -> float | None:
    if current is None or prior is None:
        return None
    return round(current - prior, 6)


def sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return repr(value)
    return "'" + str(value).replace("'", "''") + "'"


def values_sql(name: str, columns: list[str], rows: list[dict[str, Any]]) -> str:
    rows_sql = ",\n  ".join(
        "(" + ", ".join(sql_literal(row.get(column)) for column in columns) + ")"
        for row in rows
    )
    quoted_columns = ", ".join('"' + column.replace('"', '""') + '"' for column in columns)
    return f"WITH {name} ({quoted_columns}) AS (\n  VALUES\n  {rows_sql}\n)\nSELECT * FROM {name};"


def summarize_period(summary: dict[str, Any], horizon: int) -> list[dict[str, Any]]:
    period = summary["newcomer"]["latest_matured_periods"][f"d{horizon}"]
    recent = period["recent_window"]
    prior = period["prior_window"]
    metrics = [
        ("D1 留存", recent["retention"]["d1"]["value"], prior["retention"]["d1"]["value"]),
        ("D3 留存", recent["retention"]["d3"]["value"], prior["retention"]["d3"]["value"]),
        (f"D{horizon} 留存", recent["retention"][f"d{horizon}"]["value"], prior["retention"][f"d{horizon}"]["value"]),
        (
            "显示新增付费率",
            recent["payment"]["new_payment"]["displayed_rate_weighted_by_new_users"],
            prior["payment"]["new_payment"]["displayed_rate_weighted_by_new_users"],
        ),
        (
            "报告新增付费人数/新增人数",
            recent["payment"]["new_payment"]["reported_people_per_new_user"],
            prior["payment"]["new_payment"]["reported_people_per_new_user"],
        ),
        (
            "显示首充付费率",
            recent["payment"]["first_charge"]["displayed_rate_weighted_by_new_users"],
            prior["payment"]["first_charge"]["displayed_rate_weighted_by_new_users"],
        ),
        (
            "报告首充人数/新增人数",
            recent["payment"]["first_charge"]["reported_people_per_new_user"],
            prior["payment"]["first_charge"]["reported_people_per_new_user"],
        ),
    ]
    return [
        {"metric": name, "prior_window": prior_value, "recent_window": recent_value, "change": pp(recent_value, prior_value)}
        for name, recent_value, prior_value in metrics
    ]


def build_artifact(summary: dict[str, Any]) -> dict[str, Any]:
    newcomer = summary["newcomer"]
    lifecycle = summary["lifecycle_pool"]
    as_of = newcomer["as_of_date"]
    matured = newcomer["matured"]
    d7_period = newcomer["latest_matured_periods"]["d7"]
    recent_d7 = d7_period["recent_window"]
    prior_d7 = d7_period["prior_window"]
    d30_period = newcomer["latest_matured_periods"]["d30"]
    recent_d30 = d30_period["recent_window"]
    prior_d30 = d30_period["prior_window"]
    h7_channels = newcomer["channel_h7_latest_28_days"]
    h5_fb = next(row for row in h7_channels if row["channel"] == "wajeH5-fb")
    primary_google = next(row for row in h7_channels if row["channel"] == "WajeSpecial-googleadwords_int")
    ios = next(row for row in h7_channels if row["channel"] == "PAWAJEIOS-AppStore商店")
    h5_paid = next(row for row in h7_channels if row["channel"] == "PAWAJEBETH5")
    quality = newcomer["data_quality"]
    overlap = quality["2026_07_06_vs_2026_07_27_overlap"]["totals"]
    total_life_days = sum(row["user_days"] for row in lifecycle["by_lifecycle"])
    lifecycle_table = [
        row
        | {
            "user_day_share": round(row["user_days"] / total_life_days, 6) if total_life_days else None,
            "coverage": f"{lifecycle['date_start']} 至 {lifecycle['date_end']}（非连续）",
        }
        for row in lifecycle["by_lifecycle"]
    ]
    mature_retention = [
        {
            "lifecycle_day": f"D{horizon}",
            "retention_rate": matured[f"d{horizon}"]["retention"]["value"],
            "new_users": matured[f"d{horizon}"]["retention"]["new_users"],
            "cohort_count": matured[f"d{horizon}"]["retention"]["cohorts"],
            "maturity_cutoff": matured[f"d{horizon}"]["maturity_cutoff"],
        }
        for horizon in (1, 3, 7, 15, 30, 60)
    ]
    channel_chart = sorted(h7_channels, key=lambda row: row["d7_retention"], reverse=True)
    quality_table = [
        {
            "check": "显示付费率分母",
            "evidence": f"用‘人数 / 显示付费率’反推的分母合计约为新增人数的 {pct(quality['rate_denominator_check']['new_payment']['inferred_denominator_per_new_user'])}。",
            "impact": "显示付费率不能直接称为新用户付费转化率；需明确有效分母。",
        },
        {
            "check": "生命周期 V2 复充字段",
            "evidence": "812 条日期×生命周期记录的‘当日复充总金额’均为 0。",
            "impact": "无法用该表计算复购人数、复购率或复购金额。",
        },
        {
            "check": "生命周期 V2 日期覆盖",
            "evidence": "仅覆盖 2025-03-17 至 2025-05-20、2026-01-21 至 2026-05-31、2026-07-21 至 2026-07-27 三段日期。",
            "impact": "不适合直接作连续生命周期趋势判断。",
        },
        {
            "check": "快照可变性",
            "evidence": f"7 月 6 日与 7 月 27 日两版重叠 cohort 中，‘终身’列变更 {overlap['终身']['changed_rows']}/{overlap['终身']['comparable_rows']}；新增人数也变更 {overlap['新增人数']['changed_rows']}/{overlap['新增人数']['comparable_rows']}。",
            "impact": "需要为每次导出保留快照日，且把动态生命周期值与稳定 cohort 指标分开使用。",
        },
    ]
    d7_period_comparison = summarize_period(summary, 7)
    d30_period_comparison = summarize_period(summary, 30)
    source_specs = [
        (
            "mature_retention_query",
            "新包分析2026.7.27.xlsx｜成熟 cohort 留存汇总",
            "由 8 个渠道工作表的成熟 cohort 生成；粒度为生命周期天数。",
            mature_retention,
            ["lifecycle_day", "retention_rate", "new_users", "cohort_count", "maturity_cutoff"],
            ["新增人数 > 0", "仅纳入已达到对应生命周期的 cohort"],
            ["留存：源表 D1/D3/D7/D15/D30/D60 列按新增人数加权。"],
            ["workbook: 新包分析2026.7.27.xlsx"],
        ),
        (
            "channel_h7_query",
            "新包分析2026.7.27.xlsx｜近 28 天渠道 cohort 汇总",
            "由 8 个渠道工作表的成熟 D7 cohort 生成；粒度为渠道。",
            channel_chart,
            list(channel_chart[0].keys()),
            [f"cohort 日期 {h5_fb['cohort_start']} 至 {h5_fb['cohort_end']}", "新增人数 > 0", "仅纳入成熟 D7 cohort"],
            [
                "D1/D3/D7 留存：按新增人数加权。",
                "显示新增付费率/显示首充率：源表率列，分母待确认。",
                "报告首充人数/新增人数：两个源表列的直接比值。",
            ],
            ["workbook: 新包分析2026.7.27.xlsx"],
        ),
        (
            "d7_period_query",
            "新包分析2026.7.27.xlsx｜成熟 D7 cohort 窗口比较",
            "最近与前一段各 28 天成熟 D7 cohort 的汇总比较。",
            d7_period_comparison,
            ["metric", "prior_window", "recent_window", "change"],
            [f"最近窗口 {recent_d7['start']} 至 {recent_d7['end']}", f"前一窗口 {prior_d7['start']} 至 {prior_d7['end']}"],
            ["显示付费率分母与新增人数不一致，报告同时提供人数/新增人数的直接比值。"],
            ["workbook: 新包分析2026.7.27.xlsx"],
        ),
        (
            "lifecycle_pool_query",
            "新包生命周期V2 - 含联运2026.7.27.xlsx｜生命周期分层",
            "GM 生命周期奖池 V2 的日期 × 生命周期分层汇总，引用‘原始数据活跃周期’。",
            lifecycle_table,
            list(lifecycle_table[0].keys()),
            ["生命周期 1–4", "保留文件内实际日期，不假设连续覆盖"],
            ["人数为分层人次。", "当日复充总金额在所有可用记录中为 0；不可用于计算真实复购。"],
            ["workbook: 新包生命周期V2 - 含联运2026.7.27.xlsx / 原始数据活跃周期"],
        ),
        (
            "quality_checks_query",
            "新包分析导出与生命周期 V2｜数据质量检查",
            "对新包 7 月 6 日与 7 月 27 日快照、生命周期 V2 复充字段及覆盖范围的检查。",
            quality_table,
            ["check", "evidence", "impact"],
            ["按同一渠道与新增日期匹配两版新包导出"],
            ["历史 cohort 可能被回填；终身列与付费率需保留快照日和正式口径。"],
            ["workbook: 新包分析2026.7.6.xlsx", "workbook: 新包分析2026.7.27.xlsx", "workbook: 新包生命周期V2 - 含联运2026.7.27.xlsx"],
        ),
    ]
    sources = [
        {
            "id": source_id,
            "label": label,
            "path": f"analysis/newbie_lifecycle_payment_2026_07_27/{source_id}.sql",
            "query": {
                "engine": "SQLite",
                "language": "sql",
                "sql": values_sql(source_id, columns, rows),
                "description": description,
                "executed_at": as_of,
                "filters": filters,
                "metric_definitions": definitions,
                "tables_used": tables_used,
            },
        }
        for source_id, label, description, rows, columns, filters, definitions, tables_used in source_specs
    ]
    title = f"新包新手生命周期与付费分析（截至 {as_of}）"
    manifest = {
        "version": 1,
        "surface": "report",
        "title": title,
        "description": "面向产品与增长团队的新手 cohort 生命周期、付费和复购数据可用性分析。",
        "generatedAt": summary["generated_at"],
        "sources": sources,
        "charts": [
            {
                "id": "mature_retention_curve",
                "title": "成熟新用户 cohort 留存",
                "subtitle": f"截至 {as_of}；按新增人数加权，仅纳入观察期已成熟的 cohort",
                "type": "bar",
                "dataset": "mature_retention",
                "sourceId": "mature_retention_query",
                "intent": "funnel",
                "question": "新用户从 D1 到 D60 的留存衰减到什么程度？",
                "comparisonContext": {"grain": "新增日期 cohort", "denominator": "新增人数", "unit": "留存率"},
                "encodings": {
                    "x": {"field": "lifecycle_day", "type": "ordinal", "label": "生命周期"},
                    "y": {"field": "retention_rate", "type": "quantitative", "format": "percent", "label": "留存率"},
                    "tooltip": [
                        {"field": "new_users", "type": "quantitative", "format": "compact", "label": "纳入新增人数"},
                        {"field": "cohort_count", "type": "quantitative", "format": "number", "label": "cohort 数"},
                        {"field": "maturity_cutoff", "type": "temporal", "label": "成熟截止日期"},
                    ],
                },
                "palette": {"kind": "sequential", "name": "blue"},
                "settings": {"sort": "none", "showValues": True},
                "layout": "full",
            },
            {
                "id": "channel_d7_retention",
                "title": "近 28 天成熟 cohort 的 D7 留存",
                "subtitle": f"{h5_fb['cohort_start']} 至 {h5_fb['cohort_end']}；按新增人数加权",
                "type": "bar",
                "dataset": "channel_h7",
                "sourceId": "channel_h7_query",
                "intent": "comparison",
                "question": "各渠道的短期留存差异是否足以改变优化优先级？",
                "comparisonContext": {"grain": "渠道 × 新增日期 cohort", "denominator": "新增人数", "unit": "D7 留存率"},
                "encodings": {
                    "x": {"field": "channel", "type": "nominal", "label": "渠道"},
                    "y": {"field": "d7_retention", "type": "quantitative", "format": "percent", "label": "D7 留存"},
                    "tooltip": [
                        {"field": "new_users", "type": "quantitative", "format": "compact", "label": "新增人数"},
                        {"field": "d1_retention", "type": "quantitative", "format": "percent", "label": "D1 留存"},
                        {"field": "d3_retention", "type": "quantitative", "format": "percent", "label": "D3 留存"},
                        {"field": "first_charge_rate", "type": "quantitative", "format": "percent", "label": "显示首充率"},
                    ],
                },
                "palette": {"kind": "categorical", "name": "blue"},
                "settings": {"sort": "descending", "categoryLabelPolicy": "rotate", "showValues": True},
                "layout": "full",
            },
        ],
        "tables": [
            {
                "id": "recent_d7_comparison",
                "title": "近两段 28 天成熟 cohort 对比",
                "subtitle": f"最近窗口 {recent_d7['start']} 至 {recent_d7['end']}；上一窗口 {prior_d7['start']} 至 {prior_d7['end']}",
                "dataset": "d7_period_comparison",
                "sourceId": "d7_period_query",
                "density": "spacious",
                "defaultSort": {"field": "metric", "direction": "asc"},
                "columns": [
                    {"field": "metric", "label": "指标", "type": "text"},
                    {"field": "prior_window", "label": "上一窗口", "format": "percent", "type": "percent"},
                    {"field": "recent_window", "label": "最近窗口", "format": "percent", "type": "percent"},
                    {"field": "change", "label": "变化", "format": "percent", "type": "percent", "movement": True, "role": "movement"},
                ],
                "layout": "full",
            },
            {
                "id": "channel_h7_table",
                "title": "渠道新手表现明细",
                "subtitle": f"{h5_fb['cohort_start']} 至 {h5_fb['cohort_end']} 的成熟 D7 cohort；率字段保持源表标签",
                "dataset": "channel_h7",
                "sourceId": "channel_h7_query",
                "density": "spacious",
                "defaultSort": {"field": "new_users", "direction": "desc"},
                "columns": [
                    {"field": "channel", "label": "渠道", "type": "text"},
                    {"field": "new_users", "label": "新增人数", "format": "compact", "type": "number"},
                    {"field": "d1_retention", "label": "D1 留存", "format": "percent", "type": "percent"},
                    {"field": "d7_retention", "label": "D7 留存", "format": "percent", "type": "percent"},
                    {"field": "new_payment_rate", "label": "显示新增付费率", "format": "percent", "type": "percent"},
                    {"field": "first_charge_rate", "label": "显示首充率", "format": "percent", "type": "percent"},
                    {"field": "first_charge_people_per_new_user", "label": "报告首充人数/新增人数", "format": "percent", "type": "percent"},
                ],
                "layout": "full",
            },
            {
                "id": "lifecycle_pool_table",
                "title": "生命周期 V2 分层与复充字段检查",
                "subtitle": "日期×生命周期汇总；复充字段为 0，不视为真实复购表现",
                "dataset": "lifecycle_pool",
                "sourceId": "lifecycle_pool_query",
                "density": "spacious",
                "defaultSort": {"field": "lifecycle", "direction": "asc"},
                "columns": [
                    {"field": "lifecycle", "label": "生命周期分层", "type": "number"},
                    {"field": "records", "label": "分层记录数", "format": "number", "type": "number"},
                    {"field": "user_days", "label": "人次", "format": "compact", "type": "number"},
                    {"field": "recharge_amount", "label": "当日充值总金额合计", "format": "compact", "type": "number"},
                    {"field": "repurchase_amount", "label": "当日复充总金额合计", "format": "compact", "type": "number"},
                    {"field": "repurchase_amount_share_of_recharge", "label": "复充/充值", "format": "percent", "type": "percent"},
                ],
                "layout": "full",
            },
            {
                "id": "quality_table",
                "title": "影响新手与付费决策的数据质量问题",
                "subtitle": "这些问题决定了哪些结论可用、哪些必须等待补数或口径确认",
                "dataset": "quality_checks",
                "sourceId": "quality_checks_query",
                "density": "spacious",
                "defaultSort": {"field": "check", "direction": "asc"},
                "columns": [
                    {"field": "check", "label": "检查项", "type": "text"},
                    {"field": "evidence", "label": "证据", "type": "text"},
                    {"field": "impact", "label": "对决策的影响", "type": "text"},
                ],
                "layout": "full",
            },
        ],
        "blocks": [
            {"id": "title", "type": "markdown", "body": f"# {title}"},
            {
                "id": "executive_summary",
                "type": "markdown",
                "body": "\n".join(
                    [
                        "## Executive Summary",
                        f"- **新手生命周期的主要损耗发生在首周。** 8 个渠道共覆盖 {newcomer['all_channels']['new_users']:,} 名新增用户、{newcomer['all_channels']['date_count']} 个新增日期；成熟 cohort 的留存从 D1 {pct(matured['d1']['retention']['value'])} 降至 D7 {pct(matured['d7']['retention']['value'])}、D30 {pct(matured['d30']['retention']['value'])}、D60 {pct(matured['d60']['retention']['value'])}。",
                        f"- **最近 cohort 的留存继续走弱，而显示付费率的改善不能直接当成转化提升。** 最近 28 天成熟 D7 cohort 的 D7 留存为 {pct(recent_d7['retention']['d7']['value'])}，较上一窗口 {pp(recent_d7['retention']['d7']['value'], prior_d7['retention']['d7']['value']) * 100:+.1f} 个百分点；显示新增付费率升至 {pct(recent_d7['payment']['new_payment']['displayed_rate_weighted_by_new_users'])}，但“报告新增付费人数/新增人数”仅由 {pct(prior_d7['payment']['new_payment']['reported_people_per_new_user'])} 升至 {pct(recent_d7['payment']['new_payment']['reported_people_per_new_user'])}。",
                        f"- **H5 新客体验是优先排查对象。** wajeH5-fb 在最近 28 天带来 {h5_fb['new_users']:,} 名新增（最大单渠道），但 D7 留存仅 {pct(h5_fb['d7_retention'])}、显示首充率 {pct(h5_fb['first_charge_rate'])}；相对地，Google Ads 渠道 D7 为 {pct(primary_google['d7_retention'])}、显示首充率 {pct(primary_google['first_charge_rate'])}。PAWAJEBETH5 则呈现“显示首充率 {pct(h5_paid['first_charge_rate'])}、D7 仅 {pct(h5_paid['d7_retention'])}”的付费后留存断层。",
                        f"- **复购与生命周期价值目前不能下结论。** 生命周期 V2 的复充金额字段在 {lifecycle['records']} 条分层记录中均为 0，且日期覆盖有断档；新包表的“终身”列未提供定义和统一成熟窗，不能直接称为 LTV 或用于渠道价值排序。",
                    ]
                ),
            },
            {
                "id": "lifecycle_takeaway",
                "type": "markdown",
                "sourceId": "mature_retention_query",
                "body": f"## 首周留存是新手生命周期的核心断点\n\n**成熟 cohort 的 D1→D7 留存从 {pct(matured['d1']['retention']['value'])} 降至 {pct(matured['d7']['retention']['value'])}，约六成 D1 留存用户在随后六天流失。** D30 仅 {pct(matured['d30']['retention']['value'])}，说明首周激活、首局体验和首充后的价值交付比长生命周期刺激更应前置。下图严格剔除了尚未成熟的 cohort，避免把“尚未走到该天”的用户当作流失。",
            },
            {"id": "lifecycle_chart", "type": "chart", "chartId": "mature_retention_curve"},
            {
                "id": "recent_movement",
                "type": "markdown",
                "sourceId": "d7_period_query",
                "body": f"## 最近 cohort：留存下降快于付费改善\n\n**最近成熟 D7 cohort 的 D1、D3、D7 分别较上一窗口下降 {pp(recent_d7['retention']['d1']['value'], prior_d7['retention']['d1']['value']) * 100:.1f}、{pp(recent_d7['retention']['d3']['value'], prior_d7['retention']['d3']['value']) * 100:.1f}、{pp(recent_d7['retention']['d7']['value'], prior_d7['retention']['d7']['value']) * 100:.1f} 个百分点。** 同期显示新增付费率上升，但其反推有效分母占新增人数的比例从 {pct(prior_d7['payment']['new_payment']['inferred_denominator_per_new_user'])} 降至 {pct(recent_d7['payment']['new_payment']['inferred_denominator_per_new_user'])}。因此应把“报告人数/新增人数”的小幅提升与显示率的提升分开跟踪，先确认分母变化来源。",
            },
            {"id": "recent_table", "type": "table", "tableId": "recent_d7_comparison"},
            {
                "id": "channel_takeaway",
                "type": "markdown",
                "sourceId": "channel_h7_query",
                "body": f"## H5 大盘量级与首周留存同时构成风险\n\n**wajeH5-fb 占最近窗口新增的 {pct(h5_fb['new_users'] / recent_d7['new_users'])}，但 D7 留存只有 {pct(h5_fb['d7_retention'])}，是本次数据中最值得优先验证的新手体验路径。** PAWAJEBETH5 的显示首充率达到 {pct(h5_paid['first_charge_rate'])}，却只有 {pct(h5_paid['d7_retention'])} 的 D7 留存，更像是支付动作之后未持续感知价值，而不是单纯的支付入口问题。iOS 样本较小（{ios['new_users']:,} 新增）但 D7 {pct(ios['d7_retention'])}、显示首充率 {pct(ios['first_charge_rate'])}，可作为体验和渠道质量的对照样本，而非直接复制结论。",
            },
            {"id": "channel_chart", "type": "chart", "chartId": "channel_d7_retention"},
            {"id": "channel_table", "type": "table", "tableId": "channel_h7_table"},
            {
                "id": "repurchase_blocker",
                "type": "markdown",
                "sourceId": "lifecycle_pool_query",
                "body": "## 复购分析被生命周期 V2 数据缺口阻断\n\n**当前生命周期 V2 只能用于观察分层充值、下注和营收金额，不能用于计算真实复购。** ‘当日复充总金额’在所有可用分层记录中为 0；并且文件实际只覆盖三段不连续日期。将 0 解释为“没有复购”会得出错误结论，应视为缺数/默认值或口径未接入，待与 GM 后台 owner 核对。",
            },
            {"id": "lifecycle_pool_table_block", "type": "table", "tableId": "lifecycle_pool_table"},
            {
                "id": "recommendations",
                "type": "markdown",
                "body": "## 建议的产品与数据动作\n\n1. **先做 H5 首周漏斗专项。** 按渠道 × H5版本 × 设备档位 × 网络质量拆开“落地/注册/首局完成/关键任务完成/首充/次日回访/D7 回访”；优先验证 wajeH5-fb 的低端机加载、首局完成与支付后留存断点。\n2. **把 PAWAJEBETH5 放入“首充后 7 天”实验。** 保持首充转化为 guardrail，以首充后 D1、D3、D7 留存与二次付费作为主指标，测试奖励发放节奏、首充后任务、资产可用性与回流触达。\n3. **建立用户级新手付费事实表。** 以用户 ID + 新增日期 cohort 为主键，固定输出新增、活跃、首付、二付、订单金额、首付时延、D1/D3/D7/D30；分别定义“显示率分母”“新增人数”和“有效新手”，禁止在报表中混用。\n4. **修复生命周期 V2 的复充链路与时间覆盖。** 复充相关字段应在无数据时显式标为缺失，而不是 0；补齐缺失日期并增加‘复购用户数、复购率、复购金额、累计 LTV’的 cohort 明细。",
            },
            {
                "id": "quality_block",
                "type": "markdown",
                "body": "## 数据质量与使用边界\n\n**本报告的留存结论可用于方向判断；付费率、终身价值和复购结论需带条件使用。** 同一批历史 cohort 在两次导出间出现新增人数、付费率及‘终身’列回填，说明源表不是不可变快照。后续看板应记录数据快照日、cohort 成熟状态、分母定义和数据完整性状态。",
            },
            {"id": "quality_table_block", "type": "table", "tableId": "quality_table"},
            {
                "id": "further_questions",
                "type": "markdown",
                "body": "## Further Questions\n\n- ‘终身’列的正式公式、币种/单位、累计截止日和是否按用户去重是什么？\n- ‘新增付费率’与‘首充付费率’的分母为何仅约为新增人数的 76%？有效用户、风控剔除、归因规则还是跨端去重造成差异？\n- 8 个 sheet 分别对应的包、端（Android/iOS/H5）和媒体归因规则是什么？pww 的端形态需确认。\n- 复充字段为 0 是业务事实、数据缺失，还是 GM 生命周期 V2 的计算逻辑未接入？",
            },
            {
                "id": "caveats",
                "type": "markdown",
                "body": "## Caveats and Assumptions\n\n- 文件未给出时区；本分析暂沿用项目默认 Asia/Hong_Kong，需由源系统确认。\n- 渠道间差异为观察性比较，不能直接归因于产品端或投放渠道；优化动作应通过分端、分版本的漏斗和实验验证。\n- ‘报告人数/新增人数’是两列的直接比值，不等于经用户级去重验证的转化率。\n- 生命周期 V2 的人数为分层人次，不等于新手 cohort 的唯一用户数。",
            },
        ],
    }
    snapshot = {
        "version": 1,
        "generatedAt": summary["generated_at"],
        "status": "ready",
        "datasets": {
            "mature_retention": mature_retention,
            "channel_h7": channel_chart,
            "d7_period_comparison": summarize_period(summary, 7),
            "d30_period_comparison": summarize_period(summary, 30),
            "lifecycle_pool": lifecycle_table,
            "quality_checks": quality_table,
        },
    }
    return {"surface": "report", "manifest": manifest, "snapshot": snapshot, "sources": sources}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    artifact = build_artifact(summary)
    args.output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for source in artifact["sources"]:
        sql_path = args.output.parent / f"{source['id']}.sql"
        sql_path.write_text(source["query"]["sql"] + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
