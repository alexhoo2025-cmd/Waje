#!/usr/bin/env python3
"""Build the Hilo/Plinko lifecycle and wool-risk audit artifact.

The script intentionally works from the reviewed, aggregate lifecycle snapshot
already collected on 2026-08-24. It never reads or emits player-level data.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data/outputs/lifecycle_joint/2026-08-24-lark-update/source-data.json"
DEFAULT_OUTPUT = ROOT / "analysis/new_games_lifecycle_wool_audit_2026_08_24"
DEFAULT_RAW_AUDIT = ROOT / "analysis/lifecycle_joint_data_integrity_2026_08_24/raw-audit.json"
DEFAULT_RECHECK_COMPARISON = ROOT / "analysis/lifecycle_joint_data_integrity_2026_08_24/recheck-comparison.json"
TARGET_GAMES = ["Hilo", "Plinko"]
PEER_GAMES = ["Limbo", "Keno", "EasyWin", "Coin Flips", "ColorGame"]
ANALYSIS_GAMES = TARGET_GAMES + PEER_GAMES


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def as_num(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def iso_date(value: str) -> str:
    year, month, day = value.replace("-", "/").split("/")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def ratio(actual_profit: float, bet: float) -> float | None:
    return 1.0 - actual_profit / bet if bet else None


def pct(value: float | None) -> float | None:
    return None if value is None else value * 100


def round_value(value: float | None, digits: int = 6) -> float | None:
    return None if value is None else round(value, digits)


def game_daily_rows(game_rows: list[list[Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in game_rows:
        game = str(row[1])
        if game not in ANALYSIS_GAMES:
            continue
        base_bet = as_num(row[2])
        entire_bet = as_num(row[12])
        base_actual = as_num(row[4])
        base_expected = as_num(row[3])
        entire_actual = as_num(row[14])
        entire_expected = as_num(row[13])
        rows.append(
            {
                "date": iso_date(str(row[0])),
                "game": game,
                "base_bet": base_bet,
                "entire_bet": entire_bet,
                "base_actual_profit": base_actual,
                "base_expected_profit": base_expected,
                "entire_actual_profit": entire_actual,
                "entire_expected_profit": entire_expected,
                "actual_return_ratio": ratio(base_actual, base_bet),
                "expected_return_ratio": ratio(base_expected, base_bet),
                "entire_actual_return_ratio": ratio(entire_actual, entire_bet),
                "entire_expected_return_ratio": ratio(entire_expected, entire_bet),
                "source_share_display": as_num(row[18]),
            }
        )
    return rows


def aggregate_games(daily: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in daily:
        grouped[row["game"]].append(row)
    output: list[dict[str, Any]] = []
    for game, rows in grouped.items():
        base_bet = sum(row["base_bet"] for row in rows)
        entire_bet = sum(row["entire_bet"] for row in rows)
        base_actual = sum(row["base_actual_profit"] for row in rows)
        base_expected = sum(row["base_expected_profit"] for row in rows)
        entire_actual = sum(row["entire_actual_profit"] for row in rows)
        entire_expected = sum(row["entire_expected_profit"] for row in rows)
        actual = ratio(base_actual, base_bet)
        expected = ratio(base_expected, base_bet)
        entire_actual_ratio = ratio(entire_actual, entire_bet)
        entire_expected_ratio = ratio(entire_expected, entire_bet)
        output.append(
            {
                "game": game,
                "observed_days": len({row["date"] for row in rows}),
                "base_bet": round(base_bet, 2),
                "entire_bet": round(entire_bet, 2),
                "base_actual_profit": round(base_actual, 2),
                "base_expected_profit": round(base_expected, 2),
                "entire_actual_profit": round(entire_actual, 2),
                "entire_expected_profit": round(entire_expected, 2),
                "actual_return_ratio": round_value(actual),
                "expected_return_ratio": round_value(expected),
                "entire_actual_return_ratio": round_value(entire_actual_ratio),
                "entire_expected_return_ratio": round_value(entire_expected_ratio),
                "return_gap_pp": round_value(pct((actual or 0) - (expected or 0)), 3),
                "entire_return_gap_pp": round_value(pct((entire_actual_ratio or 0) - (entire_expected_ratio or 0)), 3),
                "daily_rows": rows,
            }
        )
    return sorted(output, key=lambda row: (-row["base_bet"], row["game"]))


def lifecycle_rows(detail_rows: list[list[Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in detail_rows:
        game = str(row[2])
        if game not in TARGET_GAMES:
            continue
        life = int(as_num(row[1]))
        if life not in range(0, 5):
            continue
        output.append(
            {
                "date": iso_date(str(row[0])),
                "game": game,
                "lifecycle": life,
                "base_bet": as_num(row[9]),
                "entire_bet": as_num(row[15]),
                "base_actual_profit": as_num(row[8]),
                "base_expected_profit": as_num(row[7]),
                "entire_actual_profit": as_num(row[14]),
                "entire_expected_profit": as_num(row[13]),
                "actual_return_ratio": ratio(as_num(row[8]), as_num(row[9])),
                "expected_return_ratio": ratio(as_num(row[7]), as_num(row[9])),
                "entire_actual_return_ratio": ratio(as_num(row[14]), as_num(row[15])),
                "entire_expected_return_ratio": ratio(as_num(row[13]), as_num(row[15])),
            }
        )
    return output


def lifecycle_mix(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    totals: dict[str, float] = defaultdict(float)
    for row in rows:
        grouped[(row["game"], row["lifecycle"])].append(row)
        totals[row["game"]] += row["base_bet"]
    output = []
    for (game, lifecycle), group in sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1])):
        bet = sum(row["base_bet"] for row in group)
        output.append(
            {
                "game": game,
                "lifecycle": lifecycle,
                "base_bet": round(bet, 2),
                "base_bet_share": round(bet / totals[game], 6) if totals[game] else 0,
                "actual_profit": round(sum(row["base_actual_profit"] for row in group), 2),
                "expected_profit": round(sum(row["base_expected_profit"] for row in group), 2),
            }
        )
    return output


def risk_signals(summary: list[dict[str, Any]], mix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_game = {row["game"]: row for row in summary}
    output = [
        {
            "signal": "样本成熟度",
            "scope": "Hilo / Plinko",
            "evidence": "仅 2026-08-21 至 2026-08-23 三个完整自然日",
            "severity": "High",
            "status": "observation_only",
            "interpretation": "不足以判断稳定 RTP、留存或长期生命周期价值。",
        },
        {
            "signal": "羊毛事实链缺失",
            "scope": "Hilo / Plinko",
            "evidence": "当前聚合表没有 user_id_hash、round_id、is_robot、config_version、settlement_status",
            "severity": "High",
            "status": "blocked",
            "interpretation": "不能将聚合回报偏差认定为羊毛或机器人造成。",
        },
    ]
    for game in TARGET_GAMES:
        row = by_game[game]
        life4 = next((item for item in mix if item["game"] == game and item["lifecycle"] == 4), None)
        output.append(
            {
                "signal": "生命周期下注集中",
                "scope": game,
                "evidence": f"生命周期4占目标生命周期下注 {life4['base_bet_share']:.1%}" if life4 else "无生命周期4数据",
                "severity": "Medium",
                "status": "needs_drilldown",
                "interpretation": "需要下钻用户、局数、配置命中和结算分布，不能单独解释为异常。",
            }
        )
        if row["return_gap_pp"] is not None and abs(row["return_gap_pp"]) >= 5:
            output.append(
                {
                    "signal": "实际/预期回报偏差",
                    "scope": game,
                    "evidence": f"基础真实回报比 {row['actual_return_ratio']:.2%}，预期 {row['expected_return_ratio']:.2%}，差值 {row['return_gap_pp']:+.2f}pp",
                    "severity": "High" if game == "Plinko" else "Medium",
                    "status": "needs_settlement_audit",
                    "interpretation": "优先核对大奖、免费注、退款、跨日结算、重复计数和配置版本。",
                }
            )
    return output


def mechanism_evidence() -> list[dict[str, Any]]:
    return [
        {
            "game": "Hilo",
            "confirmed": "配置资料列为 Hi Lo，provider_key=spribe_crypto；上线节点为 2026-08-21。",
            "inferred": "短局、低学习成本的预测型玩法；机制分类来自名称和产品目录，不等同于规则验证。",
            "pending": "game_id、赔率、概率、理论 RTP、下注档位、免费/真金边界、结算版本。",
            "source_status": "confirmed_mapping_inferred_mechanics",
        },
        {
            "game": "Plinko",
            "confirmed": "配置资料列为 Plinko，provider_key=spribe_crypto；上线节点为 2026-08-21。",
            "inferred": "路径/倍率类短周期玩法，尾部结果可能造成单日聚合波动；具体机制未从当前生产规则验证。",
            "pending": "行数、倍率分布、熔断值、理论 RTP、免费注、结算与异常局规则。",
            "source_status": "confirmed_mapping_inferred_mechanics",
        },
    ]


def source_definitions() -> list[dict[str, Any]]:
    return [
        {
            "id": "lifecycle-aggregate",
            "label": "GM Lifecycle Pool v2 (Joint) 聚合导出",
            "href": "https://ksg964l11fam.sg.larksuite.com/wiki/ZBD4wPBsricBWMktFqilAGxlgte?sheet=wjhify",
            "query": {
                "engine": "GM Lifecycle Pool v2 (Joint) export + local Python audit",
                "sql": "SELECT date, game, lifecycle, base_bet, entire_bet, actual_profit, expected_profit FROM reviewed_lifecycle_snapshot WHERE date BETWEEN '2026-08-21' AND '2026-08-23' AND game IN ('Hilo','Plinko');",
                "description": "已完成表头、跨表勾稽、日期完整性和目标生命周期 0–4 筛选校验的本地聚合快照。",
                "tables_used": ["source-data.json:game", "source-data.json:detail", "source-data.json:active"],
                "filters": ["2026-08-21—2026-08-23", "Hilo / Plinko", "目标生命周期 0–4"],
                "metric_definitions": ["GM真实回报比=1-实际盈利/下注额；不是订单收入LTV或独立实测RTP。", "三日结果使用累计分子/分母重算，不平均每日比例。"],
            },
        },
        {
            "id": "mechanism-config",
            "label": "游戏与场次经济配置资料",
            "href": "https://ksg964l11fam.sg.larksuite.com/sheets/WWBBsLNl4hTFnbtI9arlmGsqgoc",
            "query": {
                "engine": "Lark configuration workbook snapshot",
                "sql": "SELECT game_name, provider_key, game_identifier FROM current_candidate_game_config WHERE game_name IN ('Hi Lo','Plinko');",
                "description": "配置资料 revision 17324；current_candidate 仅作为映射和机制线索，不作为已生效生产规则。",
                "tables_used": ["游戏与场次经济", "数值与生命周期"],
                "filters": ["Hi Lo / Plinko", "revision 17324"],
                "metric_definitions": ["机制证据分为 confirmed、inferred、pending。"],
            },
        },
        {
            "id": "wool-history",
            "label": "历史羊毛/机器人机制资料",
            "href": "https://ksg964l11fam.sg.larksuite.com/wiki/Fc18w1zR9i1YsZkEaj8lAIWCgBd",
            "query": {
                "engine": "Lark knowledge snapshot",
                "sql": "SELECT historical_wool_signals, robot_topics, lifecycle_exclusion_rules FROM historical_risk_control_docs;",
                "description": "历史资料包含 501/502 刷子问题和羊毛用户不计生命周期奖池等主题；当前生产有效性待补证。",
                "tables_used": ["风控数值与机器人", "羊毛党不计生命周期奖池"],
                "filters": ["历史资料只作风险假设，不作为现网规则"],
                "metric_definitions": ["没有用户级、局级和规则命中字段时不认定具体羊毛用户或机器人。"],
            },
        },
    ]


def integrity_source_definition() -> dict[str, Any]:
    return {
        "id": "integrity-audit",
        "label": "GM Lifecycle Pool v2 (Joint) 原始导出与独立复查审计",
        "href": "https://prod-ac.waje-special.com:8443/sys/dynamic/lifecyclev2/pool/co",
        "query": {
            "engine": "GM visible-page exports + local deterministic XLSX audit",
            "sql": "SELECT query_date, export_kind, game_name, lifecycle, content_fingerprint FROM local_lifecycle_joint_export_audit WHERE query_date BETWEEN '2026-08-21' AND '2026-08-23' AND game_name IN ('Hilo', 'Plinko');",
            "description": "对首次 24 份原始导出及 8/21–8/23 独立复查的四类导出执行表头、行数、主键、跨表勾稽和内容指纹比较。",
            "tables_used": ["summary.xlsx", "detail.xlsx", "game.xlsx", "active.xlsx"],
            "filters": ["首次快照：2026-08-18—2026-08-23", "独立复查：2026-08-21—2026-08-23", "Hilo / Plinko"],
            "metric_definitions": [
                "source_query_mismatch=同一目标日期的独立导出在标准化表值层面与首次导出不一致。",
                "data_static_suspect=首次快照中同一 game×lifecycle 的相邻日期全字段指纹重复；该状态不是用户行为或羊毛结论。",
            ],
        },
    }


def current_gm_source_definition() -> dict[str, Any]:
    return {
        "id": "current-gm-snapshot",
        "label": "GM Lifecycle Pool v2 (Joint) 稳定重查快照",
        "href": "https://prod-ac.waje-special.com:8443/sys/dynamic/lifecyclev2/pool/co",
        "query": {
            "engine": "GM visible-page export + local four-table audit",
            "sql": "SELECT query_date, game_name, lifecycle, base_bet, actual_return_ratio, expected_return_ratio FROM current_lifecycle_joint_snapshot WHERE query_date BETWEEN '2026-08-21' AND '2026-08-23' AND game_name IN ('Hilo', 'Plinko');",
            "description": "每个日期经日期控件回读、查询后约五分钟的多次内容指纹稳定检查后导出，并完成四表表头、主键和勾稽校验。",
            "tables_used": ["summary.xlsx", "detail.xlsx", "game.xlsx", "active.xlsx"],
            "filters": ["2026-08-21—2026-08-23", "Hilo / Plinko"],
            "metric_definitions": ["GM真实回报比=1-实际盈利/下注额；不是订单收入 LTV 或独立实测 RTP。", "跨日全字段重复为 data_static_suspect，不推断用户行为。"],
        },
    }


def current_static_evidence_rows(raw_audit: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for item in (raw_audit.get("adjacent_content_audit") or {}).get("adjacent_dates", []):
        if item.get("status") != "passed" or item.get("from", "") < "2026-08-21":
            continue
        focus = item.get("focus_games", {})
        for game in TARGET_GAMES:
            result = focus.get(game, {})
            output.append({
                "from_date": item["from"],
                "to_date": item["to"],
                "game": game,
                "game_row_state": result.get("game_state"),
                "detail_state": result.get("detail_state"),
                "status": "data_static_suspect" if result.get("all_fields_static") else "changed",
            })
    return output


def build_static_artifact(analysis: dict[str, Any], generated_at: str) -> dict[str, Any]:
    sources = [current_gm_source_definition(), *source_definitions()[1:]]
    manifest = {
        "version": 1,
        "surface": "report",
        "title": "Hilo、Plinko 生命周期数据更新（静态信号提示）",
        "description": "基于当前 GM 稳定重查快照的数据更新。Hilo/Plinko 跨日静态被明确标为数据质量信号，不用于产品、RTP 或羊毛结论。",
        "generatedAt": generated_at,
        "sources": sources,
        "cards": [
            {"id":"observed-days","dataset":"static_headline","sourceId":"current-gm-snapshot","description":"当前稳定 GM 快照覆盖的日期数。","metrics":[{"label":"查询日期","field":"observed_days","format":"number"}]},
            {"id":"static-signals","dataset":"static_headline","sourceId":"current-gm-snapshot","description":"目标游戏相邻日期同时静态的分游戏及明细实体数。","metrics":[{"label":"静态实体","field":"static_entities","format":"number"}]},
            {"id":"hilo-daily-bet","dataset":"static_headline","sourceId":"current-gm-snapshot","description":"当前快照中 Hilo 每日基础下注额；仅作原始数据展示。","metrics":[{"label":"Hilo 每日基础下注额","field":"hilo_daily_base_bet","format":"number"}]},
            {"id":"plinko-daily-bet","dataset":"static_headline","sourceId":"current-gm-snapshot","description":"当前快照中 Plinko 每日基础下注额；仅作原始数据展示。","metrics":[{"label":"Plinko 每日基础下注额","field":"plinko_daily_base_bet","format":"number"}]},
        ],
        "charts": [
            {"id":"daily-static-bet","title":"Hilo、Plinko 每日基础下注额","subtitle":"2026年8月21日至23日；相同高度即为跨日静态信号，而非稳定表现结论。","type":"bar","dataset":"daily_static_values","sourceId":"current-gm-snapshot","layout":"full","encodings":{"x":{"field":"date_game","type":"nominal","label":"日期与游戏"},"y":{"field":"base_bet","type":"quantitative","format":"number","label":"基础下注额"},"color":{"field":"game","type":"nominal","label":"游戏"},"tooltip":[{"field":"date","type":"temporal"},{"field":"game","type":"nominal"},{"field":"base_bet","type":"quantitative","format":"number"},{"field":"actual_return_ratio","type":"quantitative","format":"percent"},{"field":"expected_return_ratio","type":"quantitative","format":"percent"}]}},
        ],
        "tables": [
            {"id":"daily-static","title":"当前 GM 快照中的目标游戏值","subtitle":"逐日期原始 GM 聚合值；不应据此推断趋势或 RTP。","dataset":"daily_static_values","sourceId":"current-gm-snapshot","density":"comfortable","layout":"full","defaultSort":{"field":"date","direction":"asc"},"columns":[{"field":"date","label":"日期","type":"text"},{"field":"game","label":"游戏","type":"text"},{"field":"base_bet","label":"基础下注额","type":"number","format":"number"},{"field":"actual_return_ratio","label":"基础真实回报比","type":"percent","format":"percent"},{"field":"expected_return_ratio","label":"基础预期回报比","type":"percent","format":"percent"}]},
            {"id":"static-evidence","title":"跨日静态指纹","subtitle":"分游戏行与生命周期明细同时静态时触发数据质量告警。","dataset":"static_evidence","sourceId":"current-gm-snapshot","density":"comfortable","layout":"full","defaultSort":{"field":"from_date","direction":"asc"},"columns":[{"field":"from_date","label":"起始日","type":"text"},{"field":"to_date","label":"结束日","type":"text"},{"field":"game","label":"游戏","type":"text"},{"field":"game_row_state","label":"分游戏行","type":"text"},{"field":"detail_state","label":"明细行","type":"text"},{"field":"status","label":"状态","type":"text"}]},
            {"id":"risk-signals","title":"证据边界与后续核查","subtitle":"静态信号优先进入数据链路核查，而不是归因为用户或风控问题。","dataset":"risk_signals","sourceId":"current-gm-snapshot","density":"spacious","layout":"full","defaultSort":{"field":"severity","direction":"asc"},"columns":[{"field":"severity","label":"严重度","type":"text"},{"field":"scope","label":"范围","type":"text"},{"field":"signal","label":"信号","type":"text"},{"field":"status","label":"状态","type":"text"},{"field":"evidence","label":"证据","type":"text"},{"field":"interpretation","label":"解释边界","type":"text"}]},
            {"id":"mechanism-evidence","title":"机制与配置证据矩阵","subtitle":"名称及供应商映射可用；生产规则仍待核验。","dataset":"mechanism_evidence","sourceId":"mechanism-config","density":"spacious","layout":"full","defaultSort":{"field":"game","direction":"asc"},"columns":[{"field":"game","label":"游戏","type":"text"},{"field":"confirmed","label":"已确认","type":"text"},{"field":"inferred","label":"推断","type":"text"},{"field":"pending","label":"待补证","type":"text"},{"field":"source_status","label":"证据状态","type":"text"}]},
        ],
        "blocks": [
            {"id":"title","type":"markdown","body":"# Hilo、Plinko 生命周期数据更新（静态信号提示）"},
            {"id":"executive-summary","type":"markdown","body":"## Executive Summary\n\n**飞书原始数据已按当前稳定 GM 快照更新。** 8月21日至23日的汇总、详细奖池、分游戏与活跃周期行均已由同一批导出覆盖并回读核验。\n\n**Hilo、Plinko 仍存在跨日全字段重复。** 当前页面的整体汇总和其他游戏随日期变化，但两款目标游戏的分游戏行及生命周期明细行在相邻日期保持静态，因此不输出产品趋势、实际 RTP、用户行为或羊毛结论。\n\n**静态信号优先排查数据链路。** 需要 GM 数据侧确认 game_id 映射、生命周期聚合、结算和历史重处理口径；当前聚合数据也不足以认定具体用户或机器人。","sourceId":"current-gm-snapshot"},
            {"id":"headline","type":"metric-strip","cardIds":["observed-days","static-signals","hilo-daily-bet","plinko-daily-bet"]},
            {"id":"daily-takeaway","type":"markdown","body":"## 当前快照数值已更新，但相同数值不是业务趋势\n\n图表和明细表仅展示本次稳定 GM 查询的原始聚合值。三个日期中相同的 Hilo/Plinko 值被视为数据质量信号；不应因为数值恒定就推断用户持续下注、回报稳定或风险消失。","sourceId":"current-gm-snapshot"},
            {"id":"daily-chart","type":"chart","chartId":"daily-static-bet"},
            {"id":"daily-table","type":"table","tableId":"daily-static"},
            {"id":"static-takeaway","type":"markdown","body":"## 静态指纹要求独立数据链路核查\n\n同一游戏在相邻日期的分游戏行与全部生命周期明细行同时重复，且其他游戏/汇总并非整体重复。这将问题定位在目标实体的数据新鲜度或上游聚合链路，而不是 HTML 图表或飞书格式。","sourceId":"current-gm-snapshot"},
            {"id":"static-table","type":"table","tableId":"static-evidence"},
            {"id":"risk-takeaway","type":"markdown","body":"## 不把聚合静态值归因为羊毛\n\n缺少 user_id_hash、round_id、is_robot、config_version、risk_rule_id 和 settlement_status。即使之后确认 GM 聚合快照无误，也还需要局级与规则证据才能解释回报差异。","sourceId":"current-gm-snapshot"},
            {"id":"risk-table","type":"table","tableId":"risk-signals"},
            {"id":"mechanism","type":"markdown","body":"## 机制资料只用于后续验证设计\n\nHilo、Plinko 的名称与供应商映射可帮助索取 game_id、赔率/倍率、理论 RTP、免费注和 config_version；这些信息尚不能替代当前生产结算规则。","sourceId":"mechanism-config"},
            {"id":"mechanism-table","type":"table","tableId":"mechanism-evidence"},
            {"id":"next-steps","type":"markdown","body":"## 下一步\n\n1. 核对 Hilo/Plinko 的 game_id、聚合任务批次和结算数据更新时间。\n2. 为每次 GM 查询保留日期控件、稳定指纹、四表哈希和导出时间。\n3. 补齐 round_id、有效下注、最终派奖、结算状态、is_robot、risk_rule_id 与 config_version 后再做产品或风控归因。"},
            {"id":"caveats","type":"markdown","body":"## Caveats and Assumptions\n\n- 当前报告只基于 GM 聚合快照，非订单收入 LTV 或独立实测 RTP。\n- Hilo/Plinko 的静态信号不代表没有用户、没有有效局或发生羊毛。\n- 不采集或展示用户、订单、设备、IP、身份或支付明细。"},
        ],
    }
    return {"surface":"report","manifest":manifest,"snapshot":{"version":1,"generatedAt":generated_at,"status":"partial","accessIssues":[{"id":"new-game-static-signal","severity":"high","status":"partial","message":"Hilo/Plinko 相邻日期分游戏及明细指纹静态；性能、RTP 和羊毛结论不可用。"},{"id":"wool-user-grain-missing","severity":"high","status":"blocked","message":"缺少用户、局、规则和结算字段，无法确认羊毛或机器人。"}],"datasets":analysis["datasets"]}}


def snapshot_mismatch_rows(recheck: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for date, item in sorted(recheck.get("dates", {}).items()):
        if item.get("status") != "values_changed":
            continue
        active = item.get("active_lifecycle_rows", {})
        games = item.get("focus_games", {})
        row: dict[str, Any] = {
            "date": date,
            "status": "values_changed",
            "initial_active_lifecycle_rows": active.get("first"),
            "recheck_active_lifecycle_rows": active.get("recheck"),
        }
        for game in TARGET_GAMES:
            slug = game.lower()
            first = (games.get(game, {}).get("first_metrics") or {})
            second = (games.get(game, {}).get("recheck_metrics") or {})
            delta = (games.get(game, {}).get("metric_deltas") or {})
            row[f"{slug}_initial_base_bet"] = first.get("base_bet")
            row[f"{slug}_recheck_base_bet"] = second.get("base_bet")
            row[f"{slug}_base_bet_delta"] = delta.get("base_bet")
        rows.append(row)
    return rows


def snapshot_mismatch_long(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        year, month, day = row["date"].split("-")
        for game in TARGET_GAMES:
            slug = game.lower()
            for snapshot, field in (("首次快照", f"{slug}_initial_base_bet"), ("独立复查", f"{slug}_recheck_base_bet")):
                output.append(
                    {
                        "date": row["date"],
                        "date_game": f"{int(month)}月{int(day)}日 · {game}",
                        "game": game,
                        "snapshot": snapshot,
                        "base_bet": row.get(field),
                    }
                )
    return output


def fingerprint_evidence_rows(raw_audit: dict[str, Any], recheck: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    initial = (raw_audit.get("adjacent_content_audit") or {}).get("adjacent_dates", [])
    independent = (recheck.get("recheck_adjacent_content_audit") or {}).get("adjacent_dates", [])
    for snapshot, items in (("首次采集", initial), ("独立复查", independent)):
        for item in items:
            if item.get("status") != "passed" or item.get("from", "") < "2026-08-21":
                continue
            focus = item.get("focus_games", {})
            hilo = focus.get("Hilo", {})
            plinko = focus.get("Plinko", {})
            output.append(
                {
                    "snapshot": snapshot,
                    "from_date": item["from"],
                    "to_date": item["to"],
                    "hilo_game": hilo.get("game_state"),
                    "hilo_detail": hilo.get("detail_state"),
                    "plinko_game": plinko.get("game_state"),
                    "plinko_detail": plinko.get("detail_state"),
                    "interpretation": "首次采集静态不能代表当前行为" if snapshot == "首次采集" else "独立复查实体已跨日变化",
                }
            )
    return output


def blocked_risk_signals() -> list[dict[str, Any]]:
    return [
        {
            "severity": "Critical",
            "scope": "Hilo / Plinko",
            "signal": "源快照不一致",
            "status": "blocked",
            "evidence": "同一目标日期的独立复查四类 GM 导出均与首次导出不一致；初始快照中活跃生命周期 4 行，复查为 11 行。",
            "interpretation": "冻结所有产品表现、回报比、RTP、用户行为和羊毛结论；先确认 GM 规范快照。",
        },
        {
            "severity": "High",
            "scope": "Hilo / Plinko",
            "signal": "羊毛事实链缺失",
            "status": "blocked",
            "evidence": "当前聚合数据没有 user_id_hash、round_id、is_robot、risk_rule_id、config_version、settlement_status。",
            "interpretation": "即使规范快照确认，也不能仅用聚合回报偏差认定羊毛或机器人。",
        },
        {
            "severity": "High",
            "scope": "生产数值配置",
            "signal": "理论规则未核验",
            "status": "pending",
            "evidence": "理论 RTP、赔率/倍率、免费注、有效局和当前 config_version 尚未完成生产取证。",
            "interpretation": "不得将历史配置或玩法名称当作线上结算规则。",
        },
    ]


def build_blocked_artifact(analysis: dict[str, Any], generated_at: str) -> dict[str, Any]:
    sources = [integrity_source_definition(), *source_definitions()[1:]]
    manifest = {
        "version": 1,
        "surface": "report",
        "title": "Hilo、Plinko 新游戏数据可用性复核（结论冻结）",
        "description": "首次生命周期快照与独立 GM 复查不一致。产品表现、回报比和羊毛结论已冻结，等待数据拥有方确认规范快照。",
        "generatedAt": generated_at,
        "sources": sources,
        "cards": [
            {"id":"first-files","dataset":"integrity_headline","sourceId":"integrity-audit","description":"首次原始导出通过解析及跨表校验的文件数。","metrics":[{"label":"首次审计文件","field":"first_export_files","format":"number"}]},
            {"id":"mismatch-dates","dataset":"integrity_headline","sourceId":"integrity-audit","description":"独立复查与首次导出在标准化表值层面不一致的日期数。","metrics":[{"label":"不一致日期","field":"mismatched_dates","format":"number"}]},
            {"id":"initial-static","dataset":"integrity_headline","sourceId":"integrity-audit","description":"首次快照中目标游戏的相邻日期静态实体次数。","metrics":[{"label":"初始静态实体","field":"initial_static_entities","format":"number"}]},
            {"id":"recheck-changed","dataset":"integrity_headline","sourceId":"integrity-audit","description":"独立复查中目标游戏跨日变化实体次数。","metrics":[{"label":"复查变化实体","field":"recheck_changed_entities","format":"number"}]},
        ],
        "charts": [
            {"id":"snapshot-bet-mismatch","title":"首次与独立复查基础下注额","subtitle":"同一目标日期的 Hilo、Plinko；仅用于定位源快照不一致。","type":"bar","dataset":"snapshot_mismatch_long","sourceId":"integrity-audit","layout":"full","encodings":{"x":{"field":"date_game","type":"nominal","label":"日期与游戏"},"y":{"field":"base_bet","type":"quantitative","format":"number","label":"基础下注额"},"color":{"field":"snapshot","type":"nominal","label":"快照"},"tooltip":[{"field":"date","type":"temporal"},{"field":"game","type":"nominal"},{"field":"snapshot","type":"nominal"},{"field":"base_bet","type":"quantitative","format":"number"}]}},
        ],
        "tables": [
            {"id":"snapshot-mismatch","title":"首次与独立复查的核心差异","subtitle":"同一目标日期、同一 GM 报表；金额为基础下注额。","dataset":"snapshot_mismatch","sourceId":"integrity-audit","density":"comfortable","layout":"full","defaultSort":{"field":"date","direction":"asc"},"columns":[
                {"field":"date","label":"日期","type":"text"},
                {"field":"initial_active_lifecycle_rows","label":"首次活跃周期行","type":"number","format":"number"},
                {"field":"recheck_active_lifecycle_rows","label":"复查活跃周期行","type":"number","format":"number"},
                {"field":"hilo_initial_base_bet","label":"Hilo 首次下注额","type":"number","format":"number"},
                {"field":"hilo_recheck_base_bet","label":"Hilo 复查下注额","type":"number","format":"number"},
                {"field":"hilo_base_bet_delta","label":"Hilo 差异","type":"number","format":"number","movement":True},
                {"field":"plinko_initial_base_bet","label":"Plinko 首次下注额","type":"number","format":"number"},
                {"field":"plinko_recheck_base_bet","label":"Plinko 复查下注额","type":"number","format":"number"},
                {"field":"plinko_base_bet_delta","label":"Plinko 差异","type":"number","format":"number","movement":True},
                {"field":"status","label":"数据状态","type":"text"},
            ]},
            {"id":"fingerprint-evidence","title":"跨日实体指纹证据","subtitle":"分游戏行与全生命周期明细行分别比较；static_entity 表示全字段指纹重复。","dataset":"fingerprint_evidence","sourceId":"integrity-audit","density":"comfortable","layout":"full","defaultSort":{"field":"from_date","direction":"asc"},"columns":[
                {"field":"snapshot","label":"快照","type":"text"},
                {"field":"from_date","label":"起始日","type":"text"},
                {"field":"to_date","label":"结束日","type":"text"},
                {"field":"hilo_game","label":"Hilo 分游戏","type":"text"},
                {"field":"hilo_detail","label":"Hilo 明细","type":"text"},
                {"field":"plinko_game","label":"Plinko 分游戏","type":"text"},
                {"field":"plinko_detail","label":"Plinko 明细","type":"text"},
                {"field":"interpretation","label":"解读","type":"text"},
            ]},
            {"id":"risk-signals","title":"当前风险与数据阻断","subtitle":"先解决源快照一致性，再讨论产品、结算或羊毛问题。","dataset":"risk_signals","sourceId":"integrity-audit","density":"spacious","layout":"full","defaultSort":{"field":"severity","direction":"asc"},"columns":[
                {"field":"severity","label":"严重度","type":"text"},
                {"field":"scope","label":"范围","type":"text"},
                {"field":"signal","label":"信号","type":"text"},
                {"field":"status","label":"状态","type":"text"},
                {"field":"evidence","label":"证据","type":"text"},
                {"field":"interpretation","label":"处理边界","type":"text"},
            ]},
            {"id":"mechanism-evidence","title":"机制与配置证据矩阵","subtitle":"名称及供应商映射可用；线上规则仍待版本化核验。","dataset":"mechanism_evidence","sourceId":"mechanism-config","density":"spacious","layout":"full","defaultSort":{"field":"game","direction":"asc"},"columns":[
                {"field":"game","label":"游戏","type":"text"},
                {"field":"confirmed","label":"已确认","type":"text"},
                {"field":"inferred","label":"推断","type":"text"},
                {"field":"pending","label":"待补证","type":"text"},
                {"field":"source_status","label":"证据状态","type":"text"},
            ]},
        ],
        "blocks": [
            {"id":"title","type":"markdown","body":"# Hilo、Plinko 新游戏数据可用性复核（结论冻结）"},
            {"id":"executive-summary","type":"markdown","body":"## Executive Summary\n\n**初始业务结论已冻结。** 同一 2026-08-21 至 2026-08-23 日期的独立 GM 复查在四类导出中全部与首次快照不一致；初始 Hilo/Plinko 的跨日重复不能继续解释为产品行为、RTP、结算或羊毛。\n\n**确认的流程缺口是完成门禁不足。** 首次采集把“行数可用”当成查询完成，未验证实体级内容指纹稳定；独立复查中 Hilo、Plinko 均已跨日变化。该证据支持“初始快照不可用”，但尚不能在数据所有者确认前断言 GM 上游的具体故障原因。\n\n**飞书不做自动更正。** 现有飞书值保留，直至数据拥有方确认哪一份 GM 快照是规范版本；届时再按差异清单复核并写入。","sourceId":"integrity-audit"},
            {"id":"headline","type":"metric-strip","cardIds":["first-files","mismatch-dates","initial-static","recheck-changed"]},
            {"id":"mismatch-takeaway","type":"markdown","body":"## 同一历史日期的源值不一致，不能建立趋势或回报判断\n\n首次与独立复查的活跃生命周期行数、Hilo 基础下注额和 Plinko 基础下注额均发生显著变化。由于三个日期的基础输入没有唯一稳定版本，原先的每日趋势、三日累计回报比、生命周期集中度和同窗对照全部撤销。这里保留差异表用于数据定位，不把复查值包装成新的产品结论。","sourceId":"integrity-audit"},
            {"id":"mismatch-chart","type":"chart","chartId":"snapshot-bet-mismatch"},
            {"id":"mismatch-table","type":"table","tableId":"snapshot-mismatch"},
            {"id":"fingerprint-takeaway","type":"markdown","body":"## 初始静态指纹是数据质量信号，而非用户行为事实\n\n首次快照中 Hilo 在两个相邻日期、Plinko 在 8 月 22 日至 23 日的分游戏行与全部生命周期明细行完全一致；但独立复查中两款游戏均跨日变化。这排除了把初始静态值直接用于“稳定表现”或“异常用户”分析的可能。","sourceId":"integrity-audit"},
            {"id":"fingerprint-table","type":"table","tableId":"fingerprint-evidence"},
            {"id":"risk-takeaway","type":"markdown","body":"## 当前唯一可行动的结论是数据质量阻断\n\n在规范 GM 快照确认前，不应将 Hilo/Plinko 归因为羊毛、机器人、无新增有效局、RTP 偏差或系统故障。即使源快照后续确认，羊毛认定仍需要局级、用户级、配置和结算证据链。","sourceId":"integrity-audit"},
            {"id":"risk-table","type":"table","tableId":"risk-signals"},
            {"id":"mechanism","type":"markdown","body":"## 已保留的机制证据只用于后续核验设计\n\nHilo 与 Plinko 的名称和供应商映射仍可作为抽取 game_id、赔率/倍率、理论 RTP、免费注和 config_version 的线索；它们不能替代当前生产规则或作为本轮回报差异的解释。","sourceId":"mechanism-config"},
            {"id":"mechanism-table","type":"table","tableId":"mechanism-evidence"},
            {"id":"next-steps","type":"markdown","body":"## 下一步\n\n1. **P0：请 GM 数据所有者确认 8/21–8/23 的规范历史快照与是否存在重处理/延迟聚合。**\n2. **P0：确认后生成逐日期、逐游戏、逐生命周期的飞书更正清单；在确认前不写入。**\n3. **P0：采集完成条件改为两次轮询的实体级内容指纹稳定，并保存日期控件、提交时间、返回行数和导出哈希。**\n4. **P1：规范快照确认后，再补齐 round_id、有效下注、最终派奖、结算状态、is_robot、risk_rule_id 和 config_version。**"},
            {"id":"questions","type":"markdown","body":"## Further Questions\n\n- 首次与复查间，GM 是否执行了历史聚合重处理、奖池/结算补账或 game_id 映射修复？\n- 页面何时才可判定查询最终完成：是否有服务端完成标志，而非仅依靠表格行数？\n- 活跃生命周期从 4 行变为 11 行是历史 cohort 成熟、页面异步补全还是其他口径切换？"},
            {"id":"caveats","type":"markdown","body":"## Caveats and Assumptions\n\n- 本报告是数据可用性复核，不是 Hilo/Plinko 的产品表现或风控结论。\n- 独立复查验证了首次快照不稳定，但尚未取得 GM 后端任务日志，不能断言具体上游根因。\n- 不采集或展示用户、订单、设备、IP、身份或支付明细。"},
        ],
    }
    snapshot = {
        "version": 1,
        "generatedAt": generated_at,
        "status": "blocked",
        "accessIssues": [
            {"id":"source-snapshot-mismatch","severity":"critical","status":"blocked","message":"首次与独立复查的 8/21–8/23 GM 生命周期导出不一致；所有产品、回报和羊毛结论已冻结。"},
            {"id":"wool-user-grain-missing","severity":"high","status":"blocked","message":"缺少 user_id_hash、round_id、is_robot、risk_rule_id、config_version 和 settlement_status。"},
            {"id":"mechanism-production-config-missing","severity":"high","status":"partial","message":"Hilo/Plinko 精确 game_id、理论 RTP、赔率、免费注和当前生效配置待补证。"},
        ],
        "datasets": analysis["datasets"],
    }
    return {"surface":"report","manifest":manifest,"snapshot":snapshot}


def build_artifact(analysis: dict[str, Any], generated_at: str) -> dict[str, Any]:
    if analysis["status"] == "blocked":
        return build_blocked_artifact(analysis, generated_at)
    if analysis["status"] == "static_suspect":
        return build_static_artifact(analysis, generated_at)
    sources = source_definitions()
    headline = analysis["headline"]
    columns = {
        "number": lambda field, label: {"field": field, "label": label, "type": "number", "format": "number"},
        "percent": lambda field, label: {"field": field, "label": label, "type": "percent", "format": "percent"},
    }
    manifest = {
        "version": 1,
        "surface": "report",
        "title": "Hilo、Plinko 新游戏生命周期价值与羊毛风险审计",
        "description": "基于 2026-08-21 至 2026-08-23 三日 GM 生命周期聚合数据的观察性审计；羊毛身份和现网规则仍待补证。",
        "generatedAt": generated_at,
        "sources": sources,
        "cards": [
            {"id":"observation-days","dataset":"headline","sourceId":"lifecycle-aggregate","description":"新游戏上线后的完整观察日数。","metrics":[{"label":"完整观察日","field":"observation_days","format":"number"}]},
            {"id":"hilo-bet","dataset":"headline","sourceId":"lifecycle-aggregate","description":"Hilo 三日基础下注额。","metrics":[{"label":"Hilo 基础下注额","field":"hilo_base_bet","format":"number"}]},
            {"id":"plinko-bet","dataset":"headline","sourceId":"lifecycle-aggregate","description":"Plinko 三日基础下注额。","metrics":[{"label":"Plinko 基础下注额","field":"plinko_base_bet","format":"number"}]},
            {"id":"plinko-gap","dataset":"headline","sourceId":"lifecycle-aggregate","description":"GM 真实回报比与预期回报比的三日加权差异。","metrics":[{"label":"Plinko 回报偏差","field":"plinko_gap_pp","format":"number"}]},
        ],
        "charts": [
            {"id":"daily-bet","title":"Hilo 与 Plinko 每日基础下注额","subtitle":"2026-08-21 至 2026-08-23；按日期和游戏展示原始聚合规模。","type":"line","dataset":"daily_game_metrics","sourceId":"lifecycle-aggregate","layout":"full","encodings":{"x":{"field":"date","type":"temporal","label":"日期"},"y":{"field":"base_bet","type":"quantitative","format":"number","label":"基础下注额"},"color":{"field":"game","type":"nominal","label":"游戏"},"tooltip":[{"field":"date","type":"temporal"},{"field":"game","type":"nominal"},{"field":"base_bet","type":"quantitative","format":"number"}]}},
            {"id":"return-gap","title":"实际与预期回报比对比","subtitle":"三日累计分子/分母重算；回报比为 GM 生命周期口径，不等同订单收入 LTV。","type":"bar","dataset":"return_ratio_long","sourceId":"lifecycle-aggregate","layout":"full","encodings":{"x":{"field":"game","type":"nominal","label":"游戏"},"y":{"field":"ratio","type":"quantitative","format":"percent","label":"回报比"},"color":{"field":"metric","type":"nominal","label":"指标"},"tooltip":[{"field":"game","type":"nominal"},{"field":"metric","type":"nominal"},{"field":"ratio","type":"quantitative","format":"percent"}]}},
            {"id":"lifecycle-mix","title":"Hilo 与 Plinko 生命周期 0–4 下注结构","subtitle":"按目标生命周期 0–4 汇总；展示下注集中度，不推断用户身份。","type":"stackedBar100","dataset":"lifecycle_mix","sourceId":"lifecycle-aggregate","layout":"full","encodings":{"x":{"field":"lifecycle","type":"ordinal","label":"生命周期"},"y":{"field":"base_bet_share","type":"quantitative","format":"percent","label":"下注占比"},"color":{"field":"game","type":"nominal","label":"游戏"},"tooltip":[{"field":"game","type":"nominal"},{"field":"lifecycle","type":"ordinal"},{"field":"base_bet_share","type":"quantitative","format":"percent"}]}},
            {"id":"peer-gap","title":"新游戏与同窗对照游戏的回报偏差","subtitle":"2026-08-21 至 2026-08-23；实际回报比减预期回报比，正值表示平台实际盈利低于预期。","type":"bar","dataset":"peer_summary","sourceId":"lifecycle-aggregate","layout":"full","encodings":{"x":{"field":"game","type":"nominal","label":"游戏"},"y":{"field":"return_gap_pp","type":"quantitative","label":"偏差（百分点）"},"tooltip":[{"field":"game","type":"nominal"},{"field":"return_gap_pp","type":"quantitative"},{"field":"base_bet","type":"quantitative","format":"number"}]}},
        ],
        "tables": [
            {"id":"game-summary","title":"游戏三日加权指标","subtitle":"按游戏汇总 8/21–8/23；比例均由累计分子/分母重算。","dataset":"game_summary","sourceId":"lifecycle-aggregate","density":"comfortable","layout":"full","defaultSort":{"field":"base_bet","direction":"desc"},"columns":[{"field":"game","label":"游戏","type":"text"},{"field":"observed_days","label":"观察日","type":"number","format":"number"},{"field":"base_bet","label":"基础下注额","type":"number","format":"number"},{"field":"actual_return_ratio","label":"实际回报比","type":"percent","format":"percent"},{"field":"expected_return_ratio","label":"预期回报比","type":"percent","format":"percent"},{"field":"return_gap_pp","label":"偏差（pp）","type":"number","format":"number","movement":True},{"field":"lifecycle4_share","label":"生命周期4下注占比","type":"percent","format":"percent"}]},
            {"id":"lifecycle-table","title":"新游戏生命周期分布","subtitle":"仅展示目标生命周期 0–4；用于定位集中度和收益偏差。","dataset":"lifecycle_mix","sourceId":"lifecycle-aggregate","density":"comfortable","layout":"full","defaultSort":{"field":"base_bet","direction":"desc"},"columns":[{"field":"game","label":"游戏","type":"text"},{"field":"lifecycle","label":"生命周期","type":"number"},{"field":"base_bet","label":"基础下注额","type":"number","format":"number"},{"field":"base_bet_share","label":"下注占比","type":"percent","format":"percent"},{"field":"actual_profit","label":"实际盈利","type":"number","format":"number"},{"field":"expected_profit","label":"预期盈利","type":"number","format":"number"}]},
            {"id":"risk-signals","title":"羊毛与结算风险信号","subtitle":"聚合信号只用于优先级，不等于确认羊毛或机器人。","dataset":"risk_signals","sourceId":"wool-history","density":"spacious","layout":"full","defaultSort":{"field":"severity","direction":"asc"},"columns":[{"field":"severity","label":"严重度","type":"text"},{"field":"scope","label":"范围","type":"text"},{"field":"signal","label":"信号","type":"text"},{"field":"status","label":"状态","type":"text"},{"field":"evidence","label":"证据","type":"text"},{"field":"interpretation","label":"解释边界","type":"text"}]},
            {"id":"mechanism-evidence","title":"机制与配置证据矩阵","subtitle":"confirmed、inferred、pending 分层展示。","dataset":"mechanism_evidence","sourceId":"mechanism-config","density":"spacious","layout":"full","defaultSort":{"field":"game","direction":"asc"},"columns":[{"field":"game","label":"游戏","type":"text"},{"field":"confirmed","label":"已确认","type":"text"},{"field":"inferred","label":"推断","type":"text"},{"field":"pending","label":"待补证","type":"text"},{"field":"source_status","label":"证据状态","type":"text"}]},
        ],
        "blocks": [
            {"id":"title","type":"markdown","body":"# Hilo、Plinko 新游戏生命周期价值与羊毛风险审计"},
            {"id":"executive-summary","type":"markdown","body":"## Executive Summary\n\n**Plinko 是本轮优先核查对象。** 三日基础下注额约 79.13 万，GM 真实回报比约 110.17%，明显高于约 96.90% 的预期回报比；该信号需要核对结算、免费注、跨日局和配置版本，不能直接认定为羊毛。\n\n**Hilo 当前更像低样本观察。** 三日基础下注额约 3.54 万，GM 真实回报比约 86.45%，且生命周期 4 下注占比约 63.1%；规模不足以判断稳定性。\n\n**羊毛审计目前受数据粒度阻断。** 现有生命周期聚合数据没有用户、局、机器人、规则命中和结算状态字段，因此本报告只输出聚合风险信号，不认定具体用户、机器人或真实资金事故。","sourceId":"lifecycle-aggregate"},
            {"id":"headline","type":"metric-strip","cardIds":["observation-days","hilo-bet","plinko-bet","plinko-gap"]},
            {"id":"definition","type":"markdown","body":"## 先明确口径：这不是订单收入 LTV\n\n本报告使用 GM Lifecycle Pool v2 (Joint) 的基础/完全下注额、实际/预期盈利和真实/预期回报比。GM 真实回报比按累计实际盈利与累计下注额重算，不能直接替代订单收入、退款、奖励成本或游戏独立实测 RTP。Hilo、Plinko 只有三个完整自然日，D1/D3/D7 留存不纳入本轮结论。","sourceId":"lifecycle-aggregate"},
            {"id":"daily-takeaway","type":"markdown","body":"## Plinko 的规模和偏差需要先做结算核查\n\n每日走势用于判断规模是否稳定，三日累计指标用于判断偏差，二者不混用。Plinko 的回报偏差远高于 Hilo 和同窗对照游戏，第一优先级应是确认有效下注、最终派奖、退款/冲正、免费注和跨日结算是否被正确归集。","sourceId":"lifecycle-aggregate"},
            {"id":"daily-chart","type":"chart","chartId":"daily-bet"},
            {"id":"return-takeaway","type":"markdown","body":"## 实际/预期回报偏差是观察信号，不是羊毛结论\n\nPlinko 的正向偏差意味着按 GM 口径计算的平台实际盈利低于预期；Hilo 的负向偏差方向相反，但 Hilo 样本更小。只有补齐有效局、用户类型、机器人标识和配置命中后，才能判断偏差来自随机波动、玩法概率、奖池控制、结算错误还是异常用户。","sourceId":"lifecycle-aggregate"},
            {"id":"return-chart","type":"chart","chartId":"return-gap"},
            {"id":"lifecycle-takeaway","type":"markdown","body":"## 两款新游戏的下注集中在生命周期 4，但含义仍需下钻\n\n生命周期集中度可以帮助定位风险，但不能说明生命周期 4 用户就是羊毛用户。下一步需要把生命周期、局数、充值时间、设备簇、账号簇、规则命中和结算状态连接起来。","sourceId":"lifecycle-aggregate"},
            {"id":"lifecycle-chart","type":"chart","chartId":"lifecycle-mix"},
            {"id":"lifecycle-table","type":"table","tableId":"lifecycle-table"},
            {"id":"peer-takeaway","type":"markdown","body":"## 同窗对照显示 Plinko 偏差优先级更高\n\n同窗对照只用于发现异常方向，不用于证明因果。比较时使用 8/21–8/23 相同日期窗口，并同时展示下注规模，避免小样本高偏差被误读成稳定产品结论。","sourceId":"lifecycle-aggregate"},
            {"id":"peer-chart","type":"chart","chartId":"peer-gap"},
            {"id":"game-table","type":"table","tableId":"game-summary"},
            {"id":"mechanism","type":"markdown","body":"## 机制与配置证据仍有缺口\n\n现有配置资料可确认 Hilo、Plinko 的名称和 `spribe_crypto` 供应商映射；产品目录支持将 Hilo 视为短局预测类、Plinko 视为路径/倍率类，但精确规则、赔率、理论 RTP、免费注和结算版本尚未从当前生产配置验证。报告不会把历史配置或玩法名称写成线上生效规则。","sourceId":"mechanism-config"},
            {"id":"mechanism-table","type":"table","tableId":"mechanism-evidence"},
            {"id":"wool","type":"markdown","body":"## 羊毛风险：当前只能定位核查优先级\n\n历史资料包含 501/502 刷子问题、羊毛用户不计生命周期奖池以及机器人/匹配主题，但这些资料的当前生产有效性未完成版本化核验。当前聚合表没有用户级和局级链路，因此不能给出“某用户是羊毛”或“Plinko 异常由羊毛造成”的结论。","sourceId":"wool-history"},
            {"id":"risk-table","type":"table","tableId":"risk-signals"},
            {"id":"next-steps","type":"markdown","body":"## P0/P1 下一步\n\n1. **P0：补齐 Hilo、Plinko 的 game_id、理论 RTP、赔率/倍率、下注档位、免费注和 config_version。**\n2. **P0：补齐 round_id、有效下注额、最终派奖额、结算状态、退款/冲正和跨日结算标识。**\n3. **P0：补齐 is_robot、risk_rule_id、is_excluded_from_lifecycle，并核对羊毛排除是否真正生效。**\n4. **P1：补齐 user_id_hash、device_id_hash、account_cluster_id 和首充/提现时间，用于 501/502、短时套利和多账号聚集审计。**\n5. **P1：至少观察 7 个完整自然日后，再更新长期稳定性判断；D1/D3/D7 需等成熟 cohort。"},
            {"id":"questions","type":"markdown","body":"## Further Questions\n\n- Plinko 的正向回报偏差是否由少数大额或高倍率局贡献？\n- Hilo 的固定下注与生命周期 4 集中是否来自低样本、免费注还是实际规则限制？\n- 两款游戏上线后是否同时发生了 risk、奖池、活动、版本或投放变化？\n- 羊毛排除逻辑是否在生命周期聚合前生效，还是仅在用户运营层使用？"},
            {"id":"caveats","type":"markdown","body":"## Caveats and Assumptions\n\n- 观察窗口仅为 2026-08-21 至 2026-08-23 三个完整自然日。\n- 生命周期聚合数据不等同用户级真实 LTV、订单收入或独立实测 RTP。\n- 当前生产机器人、羊毛规则和结算配置尚未完成版本化取证。\n- H5 游戏筛选和设备监控仍存在既有数据阻断，不能据此做渠道、设备或弱网因果归因。"},
        ],
    }
    snapshot = {
        "version": 1,
        "generatedAt": generated_at,
        "status": "partial",
        "accessIssues": [
            {"id":"wool-user-grain-missing","severity":"high","status":"blocked","message":"缺少 user_id_hash、round_id、is_robot、config_version、settlement_status，无法确认羊毛身份或结算根因。"},
            {"id":"mechanism-production-config-missing","severity":"high","status":"partial","message":"Hilo/Plinko 精确 game_id、理论 RTP、赔率、免费注和当前生效配置待补证。"},
            {"id":"maturity-window","severity":"medium","status":"partial","message":"新游戏只有三个完整自然日，D1/D3/D7 尚未成熟。"},
        ],
        "datasets": analysis["datasets"],
    }
    return {"surface":"report","manifest":manifest,"snapshot":snapshot}


def build_analysis(
    source: dict[str, Any],
    raw_audit: dict[str, Any] | None = None,
    recheck: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rows = source["target_rows"]
    daily = game_daily_rows(rows["game"])
    summary = aggregate_games(daily)
    detail = lifecycle_rows(rows["detail"])
    mix = lifecycle_mix(detail)
    by_game = {row["game"]: row for row in summary}
    for row in summary:
        game_mix = [item for item in mix if item["game"] == row["game"]]
        row["lifecycle4_share"] = round(next((item["base_bet_share"] for item in game_mix if item["lifecycle"] == 4), 0), 6)
        row.pop("daily_rows", None)
    daily_chart = [row for row in daily if row["game"] in TARGET_GAMES]
    return_long = []
    for game in TARGET_GAMES:
        row = by_game[game]
        return_long.extend([
            {"game":game,"metric":"实际回报比","ratio":row["actual_return_ratio"]},
            {"game":game,"metric":"预期回报比","ratio":row["expected_return_ratio"]},
        ])
    peer = [row for row in summary if row["game"] in ANALYSIS_GAMES]
    risk = risk_signals(summary, mix)
    severity_rank = {"High":1,"Medium":2,"Low":3}
    for row in risk:
        row["severity_rank"] = severity_rank.get(row["severity"], 9)
    headline = {
        "observation_days": 3,
        "hilo_base_bet": by_game["Hilo"]["base_bet"],
        "plinko_base_bet": by_game["Plinko"]["base_bet"],
        "plinko_gap_pp": by_game["Plinko"]["return_gap_pp"],
        "hilo_actual_return_ratio": by_game["Hilo"]["actual_return_ratio"],
        "plinko_actual_return_ratio": by_game["Plinko"]["actual_return_ratio"],
    }
    datasets = {
        "headline":[headline],
        "daily_game_metrics":daily_chart,
        "game_summary":summary,
        "return_ratio_long":return_long,
        "lifecycle_mix":mix,
        "peer_summary":peer,
        "risk_signals":risk,
        "mechanism_evidence":mechanism_evidence(),
    }
    if (raw_audit or {}).get("data_use_status") == "data_static_suspect" and (recheck or {}).get("classification") != "source_query_mismatch":
        static_daily = []
        for row in daily_chart:
            month, day = row["date"].split("-")[1:]
            static_daily.append({**row, "date_game": f"{int(month)}月{int(day)}日 · {row['game']}"})
        static_evidence = current_static_evidence_rows(raw_audit or {})
        static_entities = sum(1 for row in static_evidence if row["status"] == "data_static_suspect")
        first_daily = {row["game"]: row for row in static_daily if row["date"] == "2026-08-21"}
        static_headline = {
            "observed_days": len({row["date"] for row in static_daily}),
            "static_entities": static_entities,
            "hilo_daily_base_bet": first_daily.get("Hilo", {}).get("base_bet", 0),
            "plinko_daily_base_bet": first_daily.get("Plinko", {}).get("base_bet", 0),
        }
        static_risks = [
            {"severity":"High","scope":"Hilo / Plinko","signal":"跨日实体静态","status":"data_static_suspect","evidence":"相邻日期的分游戏行与生命周期明细行全字段指纹重复。","interpretation":"不将其解释为趋势、RTP、羊毛或机器人；先核查聚合链路。"},
            {"severity":"High","scope":"Hilo / Plinko","signal":"羊毛事实链缺失","status":"blocked","evidence":"没有 user_id_hash、round_id、is_robot、risk_rule_id、config_version、settlement_status。","interpretation":"聚合数据不能认定具体羊毛或机器人。"},
            {"severity":"Medium","scope":"生产配置","signal":"当前规则未核验","status":"pending","evidence":"理论 RTP、赔率/倍率、免费注与结算版本待补证。","interpretation":"不将历史配置当作现网规则。"},
        ]
        return {
            "status":"static_suspect",
            "window":{"start":"2026-08-21","end":"2026-08-23","timezone":"Asia/Hong_Kong"},
            "new_games":TARGET_GAMES,
            "release_date":"2026-08-21",
            "metric_boundary":"当前 GM 聚合快照已更新，但目标游戏跨日静态，禁止推断产品趋势、实际 RTP 或羊毛。",
            "quality":{"source_validation":"passed","cross_table_reconciliation":"passed","current_snapshot_stability":"passed","new_game_static_signal":"detected","performance_conclusions":"blocked","wool_user_audit":"blocked","mechanism_production_config":"pending"},
            "headline":static_headline,
            "datasets":{"static_headline":[static_headline],"daily_static_values":static_daily,"static_evidence":static_evidence,"risk_signals":static_risks,"mechanism_evidence":mechanism_evidence()},
            "assumptions":["每个日期在 GM 页面多次内容指纹一致后导出。","当前数据仅是 GM 聚合快照，不是订单收入 LTV 或独立 RTP。","静态值作为数据质量信号，不归因于用户、机器人或羊毛。"],
        }
    if (recheck or {}).get("classification") == "source_query_mismatch":
        mismatch = snapshot_mismatch_rows(recheck or {})
        fingerprints = fingerprint_evidence_rows(raw_audit or {}, recheck or {})
        blocked_risks = blocked_risk_signals()
        severity_rank = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}
        for row in blocked_risks:
            row["severity_rank"] = severity_rank[row["severity"]]
        initial_static_entities = sum(
            1
            for row in fingerprints
            if row["snapshot"] == "首次采集"
            for field in ("hilo_game", "plinko_game")
            if row[field] == "static_entity"
        )
        recheck_changed_entities = sum(
            1
            for row in fingerprints
            if row["snapshot"] == "独立复查"
            for field in ("hilo_game", "plinko_game")
            if row[field] == "changed"
        )
        integrity_headline = {
            "first_export_files": (raw_audit or {}).get("raw_export_audit", {}).get("files_seen", 0),
            "mismatched_dates": len(mismatch),
            "initial_static_entities": initial_static_entities,
            "recheck_changed_entities": recheck_changed_entities,
        }
        return {
            "status": "blocked",
            "window": {"start": "2026-08-21", "end": "2026-08-23", "timezone": "Asia/Hong_Kong"},
            "new_games": TARGET_GAMES,
            "release_date": "2026-08-21",
            "metric_boundary": "首次 GM 生命周期快照与独立复查不一致，禁止将其用于产品表现、真实回报比、RTP 或羊毛判断。",
            "quality": {
                "source_validation": "passed",
                "cross_table_reconciliation": "passed",
                "initial_snapshot_static_entities": "detected",
                "independent_recheck": "source_query_mismatch",
                "performance_conclusions": "blocked",
                "wool_user_audit": "blocked",
                "mechanism_production_config": "pending",
            },
            "headline": integrity_headline,
            "datasets": {
                "integrity_headline": [integrity_headline],
                "snapshot_mismatch": mismatch,
                "snapshot_mismatch_long": snapshot_mismatch_long(mismatch),
                "fingerprint_evidence": fingerprints,
                "risk_signals": blocked_risks,
                "mechanism_evidence": mechanism_evidence(),
            },
            "initial_snapshot_metrics": {
                "status": "not_for_business_use",
                "headline": headline,
                "game_summary": summary,
                "lifecycle_mix": mix,
            },
            "assumptions": [
                "独立复查页面日期控件已逐次回读为 2026-08-21、2026-08-22、2026-08-23。",
                "首次与复查均只使用 GM 可见页面导出和本地聚合审计，不使用用户级明细。",
                "数据所有者尚未确认规范历史快照，因此不写入飞书，也不将复查值视为最终业务数据。",
            ],
        }
    return {
        "status":"share_with_caveats",
        "window":{"start":"2026-08-21","end":"2026-08-23","timezone":"Asia/Hong_Kong"},
        "new_games":TARGET_GAMES,
        "release_date":"2026-08-21",
        "metric_boundary":"GM真实回报比和生命周期奖池字段不是订单收入LTV或独立实测RTP",
        "quality":{"source_validation":"passed","cross_table_reconciliation":"passed","days":3,"long_retention":"not_mature","wool_user_audit":"blocked","mechanism_production_config":"pending"},
        "headline":headline,
        "datasets":datasets,
        "assumptions":["Hilo/Plinko 首次出现于 2026-08-21，因此作为上周上线的两款新游戏。","只使用已审计的聚合数据，不输出用户、订单或设备明细。","风险信号不等于羊毛或机器人确认。"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-data", default=str(DEFAULT_SOURCE))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--raw-audit", default=str(DEFAULT_RAW_AUDIT))
    parser.add_argument("--recheck-comparison", default=str(DEFAULT_RECHECK_COMPARISON))
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    source = read_json(Path(args.source_data))
    raw_audit_path = Path(args.raw_audit)
    recheck_path = Path(args.recheck_comparison)
    raw_audit = read_json(raw_audit_path) if raw_audit_path.exists() else {}
    recheck = read_json(recheck_path) if recheck_path.exists() else {}
    generated_at = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(timespec="seconds")
    analysis = build_analysis(source, raw_audit, recheck)
    artifact = build_artifact(analysis, generated_at)
    write_json(output_dir / "analysis.json", analysis)
    write_json(output_dir / "quality.json", {
        "status": analysis["status"],
        "quality": analysis["quality"],
        "window": analysis["window"],
        "gates": {
            "source_validation": "passed",
            "cross_table_reconciliation": "passed",
            "weighted_ratio_recompute": "not_used_when_snapshot_mismatch" if analysis["status"] == "blocked" else "passed",
            "independent_recheck": recheck.get("classification", "not_available"),
            "visual_report": "pending",
        },
    })
    write_json(output_dir / "source-registry.json", {
        "generated_at": generated_at,
        "sources": artifact["manifest"]["sources"],
        "source_data": str(Path(args.source_data)),
        "raw_audit": str(raw_audit_path),
        "recheck_comparison": str(recheck_path),
    })
    write_json(output_dir / "artifact.json", artifact)
    print(json.dumps({"status":analysis["status"],"output_dir":str(output_dir),"games":TARGET_GAMES,"headline":analysis["headline"]},ensure_ascii=False))


if __name__ == "__main__":
    main()
