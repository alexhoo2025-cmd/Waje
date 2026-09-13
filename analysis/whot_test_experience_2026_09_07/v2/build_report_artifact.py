#!/usr/bin/env python3
"""Build the canonical portable-report artifact from the V2 analysis snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "analysis_snapshot.json"
DEFAULT_OUTPUT = ROOT / "report" / "artifact.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def pct(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.1%}"


def source_specs() -> list[dict[str, Any]]:
    return [
        {
            "id": "src_v2_db",
            "label": "WHOT V2 local sample database",
            "path": "analysis/whot_test_experience_2026_09_07/v2/whot_samples_v2.sqlite3",
            "query": {
                "engine": "SQLite",
                "language": "sql",
                "description": "Aggregate-only WHOT match, turn, quality, and strategy evaluation snapshot.",
                "executed_at": "2026-09-07T11:30:22+00:00",
                "tables_used": [
                    "matches",
                    "turns",
                    "strategy_evaluations",
                    "experiment_schedule"
                ],
                "filters": [
                    "host = test-h5.wajew.com",
                    "game_id = 6001",
                    "no user, device, session, credential, hidden-card, or raw network fields"
                ],
                "metric_definitions": [
                    "Completed matches = result in win, loss, or draw",
                    "Observed win rate = wins / completed matches",
                    "Settlement coverage = completed matches with visible settlement / completed matches",
                    "Controlled eligibility requires known stake, visible settlement, no auto-play, and >=95% captured human-turn context"
                ],
                "sql": "SELECT COUNT(*) AS observed, SUM(result IN ('win','loss','draw')) AS completed, SUM(result='win') AS wins, SUM(result='loss') AS losses FROM matches WHERE host='test-h5.wajew.com' AND game_id='6001';"
            }
        },
        {
            "id": "src_strategy",
            "label": "WHOT V2 strategy evaluation query",
            "path": "analysis/whot_test_experience_2026_09_07/v2/whot_samples_v2.sqlite3",
            "query": {
                "engine": "SQLite",
                "language": "sql",
                "description": "Strategy results separated by strategy and displayed stake; no cross-stake aggregation.",
                "executed_at": "2026-09-07T11:30:22+00:00",
                "tables_used": ["strategy_evaluations"],
                "filters": ["data_scope = exploratory_all_completed", "eligible_for_selection = 0 for current data"],
                "metric_definitions": ["Win rate = win_count / sample_count", "Wilson interval is the 95% binomial score interval"],
                "sql": "SELECT strategy_arm, room_stake_displayed_units, sample_count, win_count, loss_count, draw_count, win_rate, wilson_lower_95, wilson_upper_95, settlement_coverage, turn_capture_coverage, auto_play_rate, decision_latency_p95_ms, eligible_for_selection FROM strategy_evaluations ORDER BY strategy_arm, room_stake_displayed_units;"
            }
        },
        {
            "id": "src_schedule",
            "label": "WHOT V2 controlled experiment schedule",
            "path": "analysis/whot_test_experience_2026_09_07/v2/whot_samples_v2.sqlite3",
            "query": {
                "engine": "SQLite",
                "language": "sql",
                "description": "Remaining controlled matches by preassigned strategy arm.",
                "executed_at": "2026-09-07T11:30:22+00:00",
                "tables_used": ["experiment_schedule"],
                "filters": ["status = pending", "77 planned valid matches"],
                "metric_definitions": ["Planned matches = count of pending schedule rows by strategy arm"],
                "sql": "SELECT strategy_arm, COUNT(*) AS planned FROM experiment_schedule WHERE status='pending' GROUP BY strategy_arm ORDER BY strategy_arm;"
            }
        },
        {
            "id": "src_v1_receipts",
            "label": "WHOT V1 run receipts and manual observations",
            "path": "analysis/whot_test_experience_2026_09_07/runs",
            "query": {
                "engine": "filesystem",
                "language": "json",
                "description": "Immutable V1 run receipts plus the curated manual observation JSONL used for V2 migration.",
                "executed_at": "2026-09-07T11:29:11+00:00",
                "tables_used": [
                    "run_receipt.json",
                    "manual_observations.jsonl"
                ],
                "filters": ["2026-09-07 test runs", "WHOT only"],
                "sql": "WITH process_stage(stage,completed_matches,result_summary) AS (VALUES ('访问预检',0,'地域限制'),('外部Chrome与登录',0,'测试站可访问'),('历史基线',10,'7胜3负'),('重启复测',1,'1胜'),('快速策略',4,'2胜2负'),('低倍房继续测试',8,'5胜3负，另1局未完成')) SELECT * FROM process_stage;"
            }
        },
        {
            "id": "src_rules",
            "label": "WHOT product and instrumentation requirements",
            "path": "knowledge/02-数据/Whot新版玩法与旧版埋点对照及规划-2026-09-07.md",
            "query": {
                "engine": "filesystem",
                "language": "markdown",
                "description": "Current reviewed product requirements for Last Card, tie-break, robots, reconnect, and action measurement.",
                "executed_at": "2026-09-07T11:20:00+00:00",
                "filters": ["review-ready requirements; not proof of production instrumentation"]
            }
        },
        {
            "id": "src_sop",
            "label": "WHOT test SOP V2",
            "path": "analysis/whot_test_experience_2026_09_07/v2/whot_test_sop_v2.md",
            "query": {
                "engine": "filesystem",
                "language": "markdown",
                "description": "Single-browser, WHOT-only, five-second decision and recovery contract.",
                "executed_at": "2026-09-07T11:30:00+00:00"
            }
        }
    ]


def build(input_path: Path) -> dict[str, Any]:
    report = load(input_path)
    quality = report["quality"]
    matches = quality["matches"]
    turns = quality["turns"]
    generated_at = quality["as_of"]

    headline_rows = [{
        "observed": matches["observed"],
        "completed": matches["completed"],
        "wins": matches["wins"],
        "losses": matches["losses"],
        "win_rate": matches["win_rate"],
        "wilson_lower": matches["wilson_95_lower"],
        "wilson_upper": matches["wilson_95_upper"],
        "eligible_controlled": matches["eligible_controlled"],
        "robot_or_auto": turns["robot_or_auto"],
        "turn_total": turns["total"],
    }]

    quality_rows = [
        {
            "metric": "结算覆盖",
            "coverage": matches["settlement_visible"] / matches["completed"],
            "numerator": matches["settlement_visible"],
            "denominator": matches["completed"],
            "status": "通过最低门槛",
            "severity": "medium"
        },
        {
            "metric": "回合上下文",
            "coverage": turns["full_context_human"] / turns["human"] if turns["human"] else 0,
            "numerator": turns["full_context_human"],
            "denominator": turns["human"],
            "status": "不通过",
            "severity": "high"
        },
        {
            "metric": "超时测量",
            "coverage": (turns["human"] - turns["timeout_unknown"]) / turns["human"] if turns["human"] else 0,
            "numerator": turns["human"] - turns["timeout_unknown"],
            "denominator": turns["human"],
            "status": "不通过",
            "severity": "high"
        },
        {
            "metric": "合格策略样本",
            "coverage": matches["eligible_controlled"] / matches["completed"] if matches["completed"] else 0,
            "numerator": matches["eligible_controlled"],
            "denominator": matches["completed"],
            "status": "不通过",
            "severity": "high"
        }
    ]

    strategy_labels = {
        "baseline_unknown": "历史基线",
        "reduce_high_point_cards": "清理高点"
    }
    strategy_rows = []
    outcome_rows = []
    for row in report["strategy_evaluations"]:
        stake_label = "未知" if row["stake"] is None else f"{row['stake']:g}"
        label = strategy_labels.get(row["strategy_arm"], row["strategy_arm"])
        if row["strategy_arm"] != "baseline_unknown":
            label = f"{label}｜下注{stake_label}"
        strategy_row = {
            "cohort": label,
            "strategy_arm": row["strategy_arm"],
            "stake": stake_label,
            "sample_count": row["sample_count"],
            "wins": row["win_count"],
            "losses": row["loss_count"],
            "win_rate": row["win_rate"],
            "wilson_lower": row["wilson_lower_95"],
            "wilson_upper": row["wilson_upper_95"],
            "settlement_coverage": row["settlement_coverage"],
            "turn_capture_coverage": row["turn_capture_coverage"],
            "auto_play_rate": row["auto_play_rate"],
            "decision_p95_ms": row["decision_latency_p95_ms"],
            "eligible": bool(row["eligible_for_selection"]),
            "status": "合格" if row["eligible_for_selection"] else "探索性"
        }
        strategy_rows.append(strategy_row)
        outcome_rows.extend([
            {**strategy_row, "outcome": "胜", "count": row["win_count"]},
            {**strategy_row, "outcome": "负", "count": row["loss_count"]}
        ])

    timeline_rows = [
        {"order": 1, "stage": "访问预检", "completed_matches": 0, "result": "内置浏览器受地域限制", "issue": "产生无效路径；后续固定普通 Chrome"},
        {"order": 2, "stage": "外部 Chrome 与登录", "completed_matches": 0, "result": "测试站可访问并完成登录准备", "issue": "登录和游戏测试未形成连续会话"},
        {"order": 3, "stage": "历史基线", "completed_matches": 10, "result": "7胜3负", "issue": "只有局级结果，策略无法认证"},
        {"order": 4, "stage": "重启复测", "completed_matches": 1, "result": "1胜", "issue": "胜局仍有35点，缺少结束原因"},
        {"order": 5, "stage": "快速策略", "completed_matches": 4, "result": "2胜2负", "issue": "下注档位缺失"},
        {"order": 6, "stage": "低倍房继续测试", "completed_matches": 8, "result": "5胜3负，另1局未完成", "issue": "托管、结算缺失、回合上下文不足"},
        {"order": 7, "stage": "测试工具恢复", "completed_matches": 0, "result": "定位到普通 Chrome 首页", "issue": "曾误入WajeSpin、PWA和外部搜索"}
    ]

    issue_rows = [
        {"priority": 1, "category": "产品/环境", "issue": "测试站重复展示提现文案与 Toa pesa", "evidence": "至少3次复现", "status": "confirmed", "severity": "high"},
        {"priority": 2, "category": "测试工具", "issue": "过期辅助树编号导致误入相邻游戏", "evidence": "1次 WajeSpin 误触", "status": "confirmed", "severity": "high"},
        {"priority": 3, "category": "测试工具", "issue": "窗口恢复时错误切换 PWA / 外部搜索", "evidence": "本轮已复现", "status": "confirmed", "severity": "high"},
        {"priority": 4, "category": "可访问性", "issue": "Cocos 画布未暴露牌面和按钮语义", "evidence": "需要截图坐标操作", "status": "confirmed", "severity": "medium"},
        {"priority": 5, "category": "玩法公平性", "issue": "非法出牌、重复结算或套利机制", "evidence": "当前无可复现证据", "status": "not_confirmed", "severity": "unknown"}
    ]

    schedule_rows = []
    schedule_label = {
        "first_legal_play": "第一合法牌",
        "reduce_high_point_cards": "清理高点",
        "retain_special_or_wild_cards_until_needed": "保留特殊牌"
    }
    for row in report["experiment_schedule"]:
        schedule_rows.append({
            "strategy_arm": row["strategy_arm"],
            "strategy": schedule_label[row["strategy_arm"]],
            "planned": row["planned"],
            "remaining_total": 77,
            "required_settlement_coverage": 0.95,
            "required_turn_coverage": 0.95,
            "required_auto_play_rate": 0.0,
            "required_decision_p95_ms": 2000
        })

    source_sql_quality = "SELECT COUNT(*) AS observed, SUM(result IN ('win','loss','draw')) AS completed, SUM(result='win') AS wins, SUM(result='loss') AS losses FROM matches WHERE host='test-h5.wajew.com' AND game_id='6001';"
    sources = source_specs()
    title = "WHOT 测试复盘与策略系统 V2"
    blocks = [
        {"id": "title", "type": "markdown", "body": f"# {title}"},
        {
            "id": "technical-summary",
            "type": "markdown",
            "sourceId": "src_v2_db",
            "body": (
                "## 技术结论\n\n"
                f"**现有数据可以复盘流程，但不能选出最优策略。** V2 重建后共有 {matches['observed']} 局观察、"
                f"{matches['completed']} 局完成、{matches['wins']} 胜 {matches['losses']} 负；观察胜率为 "
                f"{pct(matches['win_rate'])}，95% Wilson 区间为 {pct(matches['wilson_95_lower'])}–{pct(matches['wilson_95_upper'])}。"
                "历史10局已从错误的 `first_legal_play` 改为 `baseline_unknown`。\n\n"
                f"**自动选优保持冻结。** 当前仅 {matches['eligible_controlled']} 局满足受控策略门禁，且没有任何策略队列达到选优门槛；正式 RTP 也因缺少 `gross_return`、`fee` 和经余额对账的 `net_delta` 而处于 `blocked`。"
            )
        },
        {
            "id": "continuation-section",
            "type": "markdown",
            "sourceId": "src_v2_db",
            "body": (
                "## 本次续测已扩充样本，但自动接管仍是主要阻断\n\n"
                f"本次继续测试新增 7 局已结算观察（第25–31局），其中多局在页面倒计时后进入自动出牌；"
                f"因此当前累计为 {matches['observed']} 局观察、{matches['completed']} 局完成，"
                f"仅 {matches['eligible_controlled']} 局可进入受控门禁。新增混合局保留用于机器人行为观察，"
                "不用于人工策略胜率或正式 RTP。"
            )
        },
        {"id": "headline-strip", "type": "metric-strip", "cardIds": ["completed-card", "winrate-card", "eligible-card", "robot-card"]},
        {
            "id": "quality-section",
            "type": "markdown",
            "sourceId": "src_v2_db",
            "body": (
                "## 回合上下文而非局数，是当前最大缺口\n\n"
                f"{matches['completed']} 局完成结果中有 {matches['settlement_visible']} 局看到结算；"
                f"{turns['human']} 条人工回合中仅 {turns['full_context_human']} 条同时具备顶牌、手牌数、合法动作数和决策时延。"
                "因此胜负可以描述，策略选择过程却无法审计；缺失的超时字段必须保持 `unknown`，不能作为0参与评分。"
            )
        },
        {"id": "quality-chart-block", "type": "chart", "chartId": "quality-chart"},
        {
            "id": "strategy-section",
            "type": "markdown",
            "sourceId": "src_strategy",
            "body": (
                "## 三组历史结果不可直接比较\n\n"
                "历史基线使用下注200，快速策略缺少下注档位，低倍房使用下注1；三组的规则、记录覆盖和托管状态也不同。"
                "图表只展示探索性胜负构成，不代表策略效果。下一阶段必须固定房间、下注档位和规则版本。"
            )
        },
        {"id": "strategy-chart-block", "type": "chart", "chartId": "strategy-outcome-chart"},
        {"id": "strategy-table-block", "type": "table", "tableId": "strategy-table"},
        {
            "id": "timeline-section",
            "type": "markdown",
            "body": (
                "## 主要效率损失来自测试控制链，而非算法计算\n\n"
                "今日先后经历地域限制、登录切换、Cocos画布识别、过期辅助树编号、PWA切换和外部搜索。"
                "V2 将浏览器表面、域名、游戏ID和回合状态设为硬门禁，并取消固定等待与盲目双击。"
            )
        },
        {"id": "timeline-table-block", "type": "table", "tableId": "timeline-table"},
        {"id": "issues-table-block", "type": "table", "tableId": "issues-table"},
        {
            "id": "sop-section",
            "type": "markdown",
            "sourceId": "src_sop",
            "body": (
                "## V2 把每手操作压缩为一次可验证状态转换\n\n"
                "流程固定为 `LOBBY → MATCHING → DEALING → OPPONENT_TURN → PLAYER_TURN → SPECIAL_RESOLUTION → SETTLEMENT → NEXT_MATCH`。"
                "只有明确出现 `ZAMU YAKO` 才操作；每回合在2.2秒内完成读取、规则过滤、决策、点击和确认，剩余时间只用于一次受控重试。"
            )
        },
        {
            "id": "system-section",
            "type": "markdown",
            "body": (
                "## V2 数据库将来源、动作和结论分层\n\n"
                "新库保留 `runs`、`matches`、`turns`、`special_events`、`policy_decisions`、`source_lineage`、`strategy_evaluations` 和 `experiment_schedule`。"
                "重复导入按来源哈希跳过或更新；`report` 与 `quality` 只读；策略必须在每局开始时显式指定。"
            )
        },
        {
            "id": "schedule-section",
            "type": "markdown",
            "sourceId": "src_schedule",
            "body": (
                "## 剩余77局使用固定平衡排期\n\n"
                "排期为26局第一张合法牌、26局清理高点牌和25局保留特殊/万能牌。托管、URL错误、结算缺失或规则不确定的局不进入合格样本，需要补测。"
            )
        },
        {"id": "schedule-chart-block", "type": "chart", "chartId": "schedule-chart"},
        {
            "id": "method-section",
            "type": "markdown",
            "sourceId": "src_rules",
            "body": (
                "## 口径、限制与稳健性\n\n"
                "胜率按完整局计算并展示 Wilson 区间；不同下注档位分开；策略选择要求每组至少25个合格局。"
                "正式 RTP 只允许使用 `SUM(gross_return) / SUM(stake)`，当前页面结算变化不满足这一口径。"
                "机器人智能只评估可观察的合法性、时延、特殊状态和 Last Card，不推断隐藏牌。"
            )
        },
        {
            "id": "next-steps",
            "type": "markdown",
            "body": (
                "## 推荐下一步\n\n"
                "1. 使用普通 Chrome 与站内 `data-game-id=6001` 入口恢复 WHOT 测试。\n"
                "2. 按排期完成77个合格完整局，每局结算后立即写入 V2。\n"
                "3. 产品确认完整特殊牌映射、结束原因和结算字段语义。\n"
                "4. 修复测试环境提现提示，并提供固定测试筹码种子或重置能力。\n"
                "5. 满足门禁后再重新计算策略差异、机器人行为和 RTP。"
            )
        },
        {
            "id": "further-questions",
            "type": "markdown",
            "body": (
                "## 尚待确认的问题\n\n"
                "- `SUSPENSION`、`SOKO LA WOTE` 和 Last Card 对应牌值及服务端状态机的正式版本是什么？\n"
                "- 页面显示的 `+360/-200`、`+1.8/-1` 是总返还、净变化还是其他结算展示？\n"
                "- 是否可以为测试账号提供固定筹码种子，避免通过低倍局维持测试资格？"
            )
        }
    ]

    cards = [
        {
            "id": "completed-card",
            "dataset": "headline",
            "sourceId": "src_v2_db",
            "description": "结果为胜、负或平的完整对局；另有1局未完成。",
            "metrics": [{"label": "完成局", "field": "completed", "format": "number"}]
        },
        {
            "id": "winrate-card",
            "dataset": "headline",
            "sourceId": "src_v2_db",
            "description": f"{matches['wins']}胜{matches['losses']}负；仅为探索性观察。",
            "metrics": [
                {"label": "观察胜率", "field": "win_rate", "format": "percent"},
                {"label": "95%下界", "field": "wilson_lower", "format": "percent"}
            ]
        },
        {
            "id": "eligible-card",
            "dataset": "headline",
            "sourceId": "src_v2_db",
            "description": f"通过结算、回合覆盖、托管和时延门禁的局数；当前为 {matches['eligible_controlled']} 局。",
            "metrics": [{"label": "合格受控样本", "field": "eligible_controlled", "format": "number"}]
        },
        {
            "id": "robot-card",
            "dataset": "headline",
            "sourceId": "src_v2_db",
            "description": f"机器人或托管动作观察；当前 {turns['robot_or_auto']} 条，上下文仍不完整。",
            "metrics": [{"label": "机器人/托管观察", "field": "robot_or_auto", "format": "number"}]
        }
    ]

    charts = [
        {
            "id": "quality-chart",
            "title": "关键数据覆盖率",
            "subtitle": "2026年9月7日，分子/分母见数据表；百分比为覆盖率",
            "intent": "status",
            "question": "哪些数据质量门禁阻止当前样本进入策略选优？",
            "rationale": "四个同尺度覆盖率用水平条形图最容易比较，并保留分子分母用于审计。",
            "comparisonContext": {"denominator": "各指标对应的完成局或人工回合", "grain": "质量门禁", "unit": "比例"},
            "type": "horizontalBar",
            "dataset": "quality_coverage",
            "sourceId": "src_v2_db",
            "encodings": {
                "x": {"field": "metric", "type": "nominal", "label": "门禁"},
                "y": {"field": "coverage", "type": "quantitative", "format": "percent", "label": "覆盖率"},
                "tooltip": [
                    {"field": "numerator", "type": "quantitative", "label": "分子"},
                    {"field": "denominator", "type": "quantitative", "label": "分母"},
                    {"field": "status", "type": "text", "label": "状态"}
                ]
            },
            "valueFormat": "percent",
            "layout": "full",
            "palette": {"kind": "sequential", "name": "blue"},
            "settings": {"orientation": "horizontal", "showValues": False, "sort": "descending"},
            "surface": {"surface": "card", "viewMode": "both"}
        },
        {
            "id": "strategy-outcome-chart",
            "title": "历史策略样本的胜负构成",
            "subtitle": "分下注档位展示；仅为探索性样本，不代表策略效果",
            "intent": "composition",
            "question": "现有各策略/下注档位分别包含多少胜负样本？",
            "rationale": "堆叠条形图展示每个不可直接比较队列的样本构成，不暗示连续趋势。",
            "comparisonContext": {"denominator": "各策略与下注档位的完整局", "grain": "策略 × 下注档位", "unit": "局"},
            "type": "stackedBar",
            "dataset": "strategy_outcomes",
            "sourceId": "src_strategy",
            "encodings": {
                "x": {"field": "cohort", "type": "nominal", "label": "策略队列"},
                "y": {"field": "count", "type": "quantitative", "label": "局数"},
                "color": {"field": "outcome", "type": "nominal", "label": "结果"},
                "tooltip": [
                    {"field": "sample_count", "type": "quantitative", "label": "完整局"},
                    {"field": "win_rate", "type": "quantitative", "format": "percent", "label": "观察胜率"},
                    {"field": "stake", "type": "text", "label": "下注显示单位"}
                ]
            },
            "layout": "full",
            "palette": {"kind": "categorical", "name": "blue-orange"},
            "legend": {"position": "bottom", "title": "结果"},
            "settings": {"groupMode": "stacked", "showValues": False},
            "surface": {"surface": "card", "viewMode": "both"}
        },
        {
            "id": "schedule-chart",
            "title": "剩余77局受控排期",
            "subtitle": "固定规则、房间和下注档位；无效局必须补测",
            "intent": "comparison",
            "question": "剩余77局如何在三个策略臂之间平衡分配？",
            "rationale": "三个离散策略的计划局数使用直接比较条形图。",
            "comparisonContext": {"denominator": "剩余77个合格完整局", "grain": "策略", "unit": "局"},
            "type": "bar",
            "dataset": "schedule",
            "sourceId": "src_schedule",
            "encodings": {
                "x": {"field": "strategy", "type": "nominal", "label": "策略"},
                "y": {"field": "planned", "type": "quantitative", "label": "计划局数"},
                "tooltip": [
                    {"field": "required_turn_coverage", "type": "quantitative", "format": "percent", "label": "回合覆盖门槛"},
                    {"field": "required_decision_p95_ms", "type": "quantitative", "label": "决策P95门槛(ms)"}
                ]
            },
            "layout": "full",
            "palette": {"kind": "categorical", "name": "blue-orange-olive"},
            "settings": {"showValues": False, "sort": "none"},
            "surface": {"surface": "card", "viewMode": "both"}
        }
    ]

    tables = [
        {
            "id": "strategy-table",
            "title": "策略样本质量明细",
            "subtitle": "按策略与下注显示单位分层；无队列通过选优门禁",
            "dataset": "strategy_evaluations",
            "sourceId": "src_strategy",
            "density": "spacious",
            "layout": "full",
            "defaultSort": {"field": "sample_count", "direction": "desc"},
            "columns": [
                {"field": "cohort", "label": "策略队列", "type": "text"},
                {"field": "sample_count", "label": "完整局", "type": "number"},
                {"field": "wins", "label": "胜", "type": "number"},
                {"field": "losses", "label": "负", "type": "number"},
                {"field": "win_rate", "label": "观察胜率", "format": "percent"},
                {"field": "settlement_coverage", "label": "结算覆盖", "format": "percent"},
                {"field": "status", "label": "选优状态", "type": "text"}
            ]
        },
        {
            "id": "timeline-table",
            "title": "今日测试过程",
            "subtitle": "按执行先后排列；局数只计完成局",
            "dataset": "timeline",
            "sourceId": "src_v1_receipts",
            "density": "spacious",
            "layout": "full",
            "defaultSort": {"field": "order", "direction": "asc"},
            "columns": [
                {"field": "order", "label": "顺序", "type": "number"},
                {"field": "stage", "label": "阶段", "type": "text"},
                {"field": "completed_matches", "label": "完成局", "type": "number"},
                {"field": "result", "label": "产出", "type": "text"},
                {"field": "issue", "label": "主要问题", "type": "text"}
            ]
        },
        {
            "id": "issues-table",
            "title": "缺陷与执行错误清单",
            "subtitle": "产品问题与测试工具问题分开，不将执行错误归因于玩法",
            "dataset": "issues",
            "sourceId": "src_v1_receipts",
            "density": "spacious",
            "layout": "full",
            "defaultSort": {"field": "priority", "direction": "asc"},
            "columns": [
                {"field": "priority", "label": "优先级", "type": "number"},
                {"field": "category", "label": "类别", "type": "text"},
                {"field": "issue", "label": "问题", "type": "text"},
                {"field": "evidence", "label": "证据", "type": "text"},
                {"field": "status", "label": "状态", "type": "text"},
                {"field": "severity", "label": "严重度", "type": "text"}
            ]
        }
    ]

    manifest = {
        "version": 1,
        "surface": "report",
        "title": title,
        "description": "2026年9月7日 WHOT 测试流程、样本质量、策略引擎和后续77局受控计划。",
        "generatedAt": generated_at,
        "blocks": blocks,
        "cards": cards,
        "charts": charts,
        "tables": tables,
        "sources": sources
    }
    snapshot = {
        "version": 1,
        "generatedAt": generated_at,
        "status": "ready",
        "datasets": {
            "headline": headline_rows,
            "quality_coverage": quality_rows,
            "strategy_evaluations": strategy_rows,
            "strategy_outcomes": outcome_rows,
            "timeline": timeline_rows,
            "issues": issue_rows,
            "schedule": schedule_rows
        }
    }
    return {"surface": "report", "manifest": manifest, "snapshot": snapshot, "sources": sources}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    artifact = build(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "output": str(args.output), "blocks": len(artifact["manifest"]["blocks"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
