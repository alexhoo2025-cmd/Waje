#!/usr/bin/env python3
"""Build the KYC face cashflow analysis design, dashboard contract, and Feishu XML."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
KNOWLEDGE = ROOT / "knowledge/02-数据/Waje-KYC人脸用户提充比与疑似刷子整体分析方案-V1-2026-08-26.md"


SOURCES = [
    {
        "id": "kyc-mechanism",
        "label": "KYC人脸识别核心设计逻辑与机制拆解",
        "path": "knowledge/02-数据/KYC人脸识别核心设计逻辑与机制拆解-2026-08-17.md",
        "status": "verified_design",
        "use": "定义人脸成功、风险触发、提现复核和状态关联键。",
    },
    {
        "id": "event-dictionary",
        "label": "Waje埋点事件与属性字典",
        "path": "knowledge/02-数据/Waje埋点事件与属性字典-2026-08-11.md",
        "status": "verified_event_contract",
        "use": "定义ORDER、WITHDRAW、AUDIT、ASSET、BETREWARD及首充虚拟事件。",
    },
    {
        "id": "kyc-dashboard-v2",
        "label": "Waje KYC人脸识别Metabase看板V1与2.20埋点方案",
        "path": "knowledge/02-数据/Waje-KYC人脸识别Metabase看板V1与2.20埋点方案-2026-08-19.md",
        "status": "design_ready_live_facts_missing",
        "use": "确认当前仅有日汇总KYC漏斗，认证后提现结果和用户级关联仍缺失。",
    },
    {
        "id": "payment-risk-config",
        "label": "支付提现与风控配置资料",
        "path": "knowledge/02-数据/Waje配置资料/支付提现与风控.md",
        "status": "candidate_configuration",
        "use": "提供24小时提现-充值、首充带币、关联账号和提现审核的候选规则维度；不直接作为线上事实。",
    },
]


def fact_contracts() -> list[dict]:
    return [
        {
            "name": "fact_kyc_face_status",
            "owner": "KYC服务端",
            "purpose": "确定人脸KYC成功 cohort 与触发/提现时序。",
            "required_fields": [
                "user_id_hash", "face_success_ts", "kyc_flow", "platform", "package", "channel",
                "app_version", "web_version", "config_version", "risk_rule_version", "withdraw_id",
                "trace_id", "result_code", "status",
            ],
            "current_status": "planned_extension",
            "events": ["KYC_RISK_DECISION", "KYC_FACE_STATUS_UPDATE", "WITHDRAW_RECHECK"],
        },
        {
            "name": "fact_cash_order",
            "owner": "支付服务端",
            "purpose": "识别成功现金充值、首充、Bonus、退款和冲正。",
            "required_fields": [
                "order_id", "user_id_hash", "order_success_ts", "cash_recharge_amount", "bonus_amount",
                "currency", "order_status", "reversal_amount", "payment_channel", "is_first_cash_recharge",
                "platform", "package", "channel",
            ],
            "current_status": "partial_existing_event_contract",
            "events": ["ORDER", "ASSET", "view_metaevent_order_fisrtpay"],
        },
        {
            "name": "fact_withdraw_order",
            "owner": "提现与审核服务端",
            "purpose": "识别申请、审核、拒绝、最终打款和提现手续费。",
            "required_fields": [
                "withdraw_id", "user_id_hash", "withdraw_request_ts", "audit_ts", "paid_ts",
                "requested_amount", "paid_amount", "fee_amount", "currency", "withdraw_status",
                "reject_reason_group", "risk_hit", "risk_rule_version", "review_result",
            ],
            "current_status": "partial_existing_event_contract",
            "events": ["WITHDRAW", "AUDIT", "ASSET"],
        },
        {
            "name": "fact_game_cash_activity",
            "owner": "游戏与账本服务端",
            "purpose": "判断提现前是否形成真实游戏参与，而非只依赖TC。",
            "required_fields": [
                "user_id_hash", "activity_date", "valid_cash_bet_amount", "settled_cash_payout_amount",
                "completed_round_count", "bonus_bet_amount", "game_id", "asset_type",
            ],
            "current_status": "partial_existing_event_contract",
            "events": ["GAMEEND", "BETREWARD", "ASSET"],
        },
        {
            "name": "fact_risk_linkage_aggregate",
            "owner": "风控服务端",
            "purpose": "只输出已脱敏的关联规模和既有规则命中，不输出原始身份或设备信息。",
            "required_fields": [
                "user_id_hash", "risk_decision_ts", "risk_rule_id", "risk_rule_version", "risk_hit",
                "review_outcome", "device_cluster_size", "ip_cluster_size", "bank_cluster_size",
                "linked_account_count",
            ],
            "current_status": "needs_new_aggregate_view",
            "events": ["KYC_RISK_DECISION", "WITHDRAW", "AUDIT"],
        },
    ]


def metrics() -> list[dict]:
    return [
        {
            "id": "face_cohort_tc_d30",
            "name": "人脸成功用户D30金额TC",
            "definition": "人脸成功后30天内成功打款提现金额÷成功现金充值金额。",
            "denominator": "同一人脸成功 cohort 在D30内的成功现金充值金额。",
            "grain": "人脸成功周×端×包体×渠道×风险规则版本",
            "status": "primary",
        },
        {
            "id": "first_recharge_tc_d7",
            "name": "首充用户D7金额TC",
            "definition": "首次成功现金充值后7天内成功打款提现金额÷成功现金充值金额。",
            "denominator": "同一首充 cohort 在D7内的成功现金充值金额。",
            "grain": "首充周×人脸时序×端×包体×渠道×首充金额档位",
            "status": "primary",
        },
        {
            "id": "user_tc_distribution",
            "name": "用户TC分布",
            "definition": "每位有成功现金充值用户的成功打款提现÷成功现金充值，展示P50、P90和高TC占比。",
            "denominator": "窗口内有成功现金充值的用户。",
            "grain": "同主cohort；小样本不展示。",
            "status": "driver",
        },
        {
            "id": "fast_cashout_share",
            "name": "快速提现占比",
            "definition": "首充后24小时或7天内出现成功提现的用户占比。",
            "denominator": "对应首充 cohort 的成功现金充值用户。",
            "grain": "首充周×人脸时序×端/渠道。",
            "status": "risk_signal",
        },
        {
            "id": "real_play_depth",
            "name": "真实游戏参与深度",
            "definition": "有效真金下注÷现金充值、完成局数及首充后无有效游戏行为占比。",
            "denominator": "对应充值 cohort。",
            "grain": "首充周×人脸状态×游戏/端。",
            "status": "risk_signal",
        },
        {
            "id": "bonus_dependence",
            "name": "Bonus依赖度",
            "definition": "Bonus金额÷成功现金充值金额，并观察提现前资产来源。",
            "denominator": "成功现金充值金额。",
            "grain": "首充金额档位×人脸状态×渠道。",
            "status": "risk_signal",
        },
        {
            "id": "existing_risk_mix",
            "name": "既有风控命中结构",
            "definition": "提现审核、zrxz/sbsz/withdraw_review命中和关联规模分布。",
            "denominator": "人脸成功且有提现申请的用户。",
            "grain": "风险规则版本×端×渠道。",
            "status": "guardrail",
        },
        {
            "id": "cashflow_link_coverage",
            "name": "认证—支付—提现关联率",
            "definition": "可用user_id_hash关联到人脸成功、订单和提现服务端事实的用户占比。",
            "denominator": "人脸成功用户。",
            "grain": "日期×端×包体。",
            "status": "quality_gate",
        },
    ]


def dashboard_contract(metric_items: list[dict]) -> dict:
    return {
        "dashboard_name": "Waje / Risk & KYC / 人脸用户资金行为 V1",
        "status": "design_ready_live_data_blocked",
        "collection_target": "Waje / Risk & KYC / 人脸资金行为",
        "access": {
            "audience": ["风控", "数据", "KYC产品负责人"],
            "mode": "aggregate_only",
            "no_export": True,
            "small_group_suppression": {"min_recharge_users": 20},
            "restricted_fields": ["bvn", "nin", "phone", "face_image", "document_image", "biometric", "raw_device_id", "raw_ip", "raw_bank_account"],
        },
        "filters": [
            "cohort_date", "observation_window", "platform", "package", "channel", "first_recharge_band",
            "kyc_flow", "config_version", "risk_rule_version", "data_status",
        ],
        "pages": [
            {
                "name": "01 人脸KYC资金全貌",
                "question": "人脸成功 cohort 的资金进出是否与基线存在结构性差异？",
                "cards": ["face_cohort_tc_d30", "user_tc_distribution", "cashflow_link_coverage", "existing_risk_mix"],
            },
            {
                "name": "02 首充用户专项",
                "question": "首充后的提现速度、TC和游戏深度是否异常集中？",
                "cards": ["first_recharge_tc_d7", "fast_cashout_share", "real_play_depth", "bonus_dependence"],
            },
            {
                "name": "03 风险结构",
                "question": "高TC是否同时伴随低游戏参与、Bonus依赖或既有规则命中？",
                "cards": ["user_tc_distribution", "real_play_depth", "bonus_dependence", "existing_risk_mix"],
            },
            {
                "name": "04 数据质量",
                "question": "当前数字是否可以用于风险结构判断？",
                "cards": ["cashflow_link_coverage"],
            },
        ],
        "metrics": metric_items,
        "non_goals": ["用户名单", "自动刷子标签", "自动提现限制", "生物特征或身份信息展示"],
    }


def collection_contract(metric_items: list[dict]) -> dict:
    return {
        "schema_version": 1,
        "status": "design_ready_live_data_blocked",
        "primary_question": "人脸KYC成功用户及首充用户的提充比是否呈现需进一步核查的异常结构？",
        "decision_boundary": "仅聚合整体分析，不生成名单、不自动标记、不限制提现。",
        "cohort_rules": {
            "face_success": "服务端KYC_FACE_STATUS_UPDATE=success，且face_success_ts有效。",
            "first_cash_recharge": "每用户首次成功现金充值；失败、退款、冲正和Bonus不计入。",
            "face_sequence": ["face_before_first_recharge", "first_recharge_before_face_before_first_paid_withdraw", "face_after_first_paid_withdraw"],
            "maturity": {"D1": 1, "D7": 7, "D30": 30, "unmatured": "N/A"},
        },
        "fact_contracts": fact_contracts(),
        "metrics": metric_items,
        "analysis_rules": {
            "tc": "sum(successful_paid_withdraw_amount) / sum(successful_cash_recharge_amount)",
            "user_tc": "successful_paid_withdraw_amount_per_user / successful_cash_recharge_amount_per_user",
            "risk_expression": "只有高TC与至少一类独立行为信号同步上升时，才表述为疑似异常结构上升；不等同于刷子事实。",
            "baseline": "按首充周、端、包体、渠道、首充金额档位、注册年龄和风险规则版本做描述性对照，不写KYC因果结论。",
        },
        "quality_gates": [
            {"name": "关联率", "rule": "face_success→payment→withdraw 使用user_id_hash关联率≥99%"},
            {"name": "提现金额对账", "rule": "成功打款金额与账本差异≤0.1%"},
            {"name": "首充唯一性", "rule": "每个user_id_hash仅一笔is_first_cash_recharge=true"},
            {"name": "状态完整", "rule": "pending/rejected/failed/refunded/reversed与success分开统计"},
            {"name": "小样本保护", "rule": "充值用户<20的聚合不公开"},
        ],
        "restricted_outputs": ["user_id", "bank_account", "bvn", "nin", "phone", "face_image", "document_image", "biometric", "raw_ip", "raw_device_id"],
        "sources": SOURCES,
    }


def markdown(metric_items: list[dict]) -> str:
    metric_rows = "\n".join(
        f"| {item['name']} | {item['definition']} | {item['denominator']} | {item['status']} |"
        for item in metric_items
    )
    fact_rows = "\n".join(
        f"| `{item['name']}` | {item['purpose']} | {item['current_status']} |"
        for item in fact_contracts()
    )
    return f"""---
type: kyc-risk-analysis-design
status: design_ready_live_data_blocked
updated: 2026-08-26
owner: data-product
tags: [KYC, 人脸识别, 提充比, 首充, 提现, 风控, 羊毛]
---

# Waje KYC人脸用户提充比与疑似刷子整体分析方案 V1

## 核心结论

当前人脸KYC日汇总只能说明认证漏斗，不能回答“人脸KYC用户是否混入刷子”。首期先建立**受限的聚合资金行为分析**：不输出用户名单、不自动打刷子标签、不限制提现。

主判断不只看TC。只有高TC同时伴随低真实游戏参与、Bonus依赖、快速提现或既有风控命中时，才表述为“疑似异常结构上升”；它不构成刷子事实。

## 1. 统一口径

- **人脸成功用户**：服务端 `KYC_FACE_STATUS_UPDATE=success`，不使用客户端成功页或人脸请求人数代替。
- **金额TC**：成功打款提现金额 ÷ 成功现金充值金额；失败、退款、冲正、审核中和Bonus分开统计。
- **首充用户TC**：以首次成功现金充值为T0，计算D1/D7/D30；未达到观察期统一为 `N/A`。
- **人脸后TC**：以人脸成功为T0计算D1/D7/D30；首充先后关系单独拆分，避免漏掉人脸前充值。
- **用户TC分布**：在有成功现金充值用户中，展示P50、P90、高TC占比和按现网规则版本分桶。

| 指标 | 算法 | 分母 | 角色 |
|---|---|---|---|
{metric_rows}

## 2. 数据收集与关联

| 事实层 | 用途 | 当前状态 |
|---|---|---|
{fact_rows}

复用 `ORDER`、`WITHDRAW`、`AUDIT`、`ASSET`、`BETREWARD` 和首充虚拟事件。必须补齐 `KYC_RISK_DECISION`、`KYC_FACE_STATUS_UPDATE`、`WITHDRAW_RECHECK`，并且统一携带 `user_id_hash`、服务端时间、状态、`withdraw_id`、配置/风险规则版本。

报表只使用用户哈希和脱敏关联规模。不得输出BVN/NIN、手机号、人脸、证件、银行卡、原始IP或设备标识。

## 3. 分析与看板

### 人脸KYC资金全貌

按人脸成功周、端、包体、渠道、首充金额档位和规则版本展示：人脸成功人数、充值用户率、提现成功用户率、D30金额TC、用户TC分布、审核/拒绝率和关联率。

### 首充用户专项

按首充后D1/D7/D30观察现金充值、成功提现、有效真金下注、完成局数、Bonus占比和TC；与同周、同端、同渠道、同首充档位的基线人群做描述性对照。

### 风险结构

固定观察四类组合：快速提现、高TC、低真实游戏参与、Bonus依赖、既有风控命中。展示群体占比、趋势和交叉矩阵，不输出个人结果。

### 数据质量

展示人脸—支付—提现关联率、首充唯一性、成功提现与账本差异、状态缺失率、未成熟cohort和小样本抑制数。

## 4. 质量门禁与退出条件

1. 支付按 `order_id`、提现按 `withdraw_id`、账本按 `ledger_id` 去重；成功状态不得与退款、冲正、拒绝或审核中混算。
2. 每个用户只有一笔首次成功现金充值；人脸成功、首充、首提时序必须可验证。
3. D7/D30只使用达到观察天数的 cohort；金额TC与用户TC绝不合并。
4. 认证—支付—提现关联率≥99%；低于该目标、成功提现金额与账本差异超过0.1%、或小样本未抑制时，相关结论状态为 `blocked`。
5. 当前没有服务端用户级人脸—支付—提现关联事实，因此首份真实“刷子混入度”结论暂不发布。

## 5. 实施顺序

1. 数据侧提供五类受限聚合事实和字段映射；确认现金、Bonus、退款、手续费与币种口径。
2. 风控侧确认现网 `zrxz/sbsz/withdraw_review` 规则版本与阈值；历史配置只作候选维度。
3. 通过质量门禁后，配置 `Waje / Risk & KYC / 人脸资金行为 V1` 四页看板。
4. 首份报告只输出D1/D7成熟 cohort；D30在成熟后补齐；所有异常结构均进入“待核查”而非“刷子事实”。

## 数据来源与边界

- KYC人脸识别核心设计逻辑与机制拆解（机制与事件链路）
- Waje埋点事件与属性字典（订单、提现、审核、账本和首充事件）
- Waje KYC人脸识别Metabase看板V1与2.20埋点方案（当前缺口）
- 支付提现与风控配置资料（候选规则维度，不等同于线上已生效规则）
"""


def table(headers: list[str], rows: list[list[str]]) -> str:
    thead = "".join(f'<th background-color="light-gray"><p><b>{escape(item)}</b></p></th>' for item in headers)
    tbody = "".join("<tr>" + "".join(f"<td><p>{escape(item)}</p></td>" for item in row) + "</tr>" for row in rows)
    return f"<table><thead><tr>{thead}</tr></thead><tbody>{tbody}</table>"


def xml(metric_items: list[dict]) -> str:
    metric_rows = [[item["name"], item["definition"], item["denominator"], item["status"]] for item in metric_items[:5]]
    fact_rows = [[item["name"], item["purpose"], item["current_status"]] for item in fact_contracts()]
    return f"""<title>Waje KYC人脸用户提充比与疑似刷子整体分析方案 V1</title>
<p>状态：设计完成，等待服务端用户级事实关联｜范围：仅聚合整体分析，不输出名单、不自动限制提现</p>
<h1 seq="auto">核心判断</h1>
<callout emoji="🔒" background-color="light-blue" border-color="blue"><p><b>首期边界：</b>本方案只分析人脸成功用户的群体资金行为，不生成用户级刷子标签、复核名单或自动提现限制。</p></callout>
<callout emoji="⚠️" background-color="light-yellow" border-color="yellow"><p><b>当前数据缺口：</b>现有KYC日汇总没有用户级人脸成功—支付—提现关联，因此暂不能发布“人脸KYC混入刷子”的真实结论。</p></callout>
<p>核心判断采用“高TC + 至少一类独立行为信号”的群体结构，而不是只看提充比；异常结构不构成刷子事实。</p>
<h1 seq="auto">指标口径</h1>
<p><b>人脸成功用户：</b>服务端KYC_FACE_STATUS_UPDATE=success。<b>金额TC：</b>成功打款提现金额÷成功现金充值金额。<b>首充TC：</b>以首次成功现金充值为T0，计算D1/D7/D30；未达到观察期显示N/A。</p>
{table(["指标", "算法", "分母", "角色"], metric_rows)}
<h1 seq="auto">数据收集</h1>
{table(["受限事实层", "用途", "状态"], fact_rows)}
<p>复用ORDER、WITHDRAW、AUDIT、ASSET、BETREWARD和首充虚拟事件；补齐KYC_RISK_DECISION、KYC_FACE_STATUS_UPDATE、WITHDRAW_RECHECK。所有服务端事实使用user_id_hash关联，禁止输出身份、生物、银行卡、原始IP或设备标识。</p>
<h1 seq="auto">四页看板</h1>
<ol><li><b>人脸KYC资金全貌：</b>D30金额TC、用户TC分布、充值/提现成功率、规则命中结构。</li><li><b>首充用户专项：</b>D1/D7/D30 TC、快速提现、真金下注深度与Bonus依赖。</li><li><b>风险结构：</b>高TC、低参与、Bonus依赖、既有规则命中的交叉分布。</li><li><b>数据质量：</b>人脸—支付—提现关联率、订单唯一性、账本对账、未成熟cohort与小样本抑制。</li></ol>
<h1 seq="auto">质量门禁</h1>
<ul><li>支付按order_id、提现按withdraw_id、账本按ledger_id去重；退款、冲正、拒绝和审核中不进入成功金额。</li><li>每位用户只有一笔首次成功现金充值；人脸成功、首充、首提时序必须可验证。</li><li>关联率≥99%，成功提现金额与账本差异≤0.1%，小于20个充值用户的分群不公开。</li><li>未成熟D7/D30显示N/A；金额TC与用户TC分开呈现。</li></ul>
<h1 seq="auto">实施顺序</h1>
<ol><li>数据侧交付五类受限事实和字段映射，确认现金、Bonus、退款、手续费与币种口径。</li><li>风控侧确认现网zrxz/sbsz/withdraw_review规则版本；历史配置不得直接当作线上事实。</li><li>质量门禁通过后配置受限Metabase Collection；首份真实结果只输出聚合结构和成熟cohort。</li></ol>
"""


def main() -> None:
    items = metrics()
    dashboard = dashboard_contract(items)
    collection = collection_contract(items)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "data_collection_contract.json").write_text(json.dumps(collection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "risk_kyc_dashboard_contract.json").write_text(json.dumps(dashboard, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = markdown(items)
    (OUT / "report.md").write_text(report, encoding="utf-8")
    KNOWLEDGE.write_text(report, encoding="utf-8")
    (OUT / "feishu_release.xml").write_text(xml(items), encoding="utf-8")
    receipt = {
        "status": "design_ready_live_data_blocked",
        "primary_artifacts": [str(KNOWLEDGE), str(OUT / "data_collection_contract.json"), str(OUT / "risk_kyc_dashboard_contract.json")],
        "dashboard_remote_status": "not_created_missing_live_source_and_collection_access",
        "privacy": "aggregate_only_no_user_list_no_auto_action",
    }
    (OUT / "run_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
