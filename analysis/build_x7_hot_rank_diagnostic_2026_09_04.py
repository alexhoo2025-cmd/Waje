#!/usr/bin/env python3
"""Build an aggregate-only X7 HOT diagnostic report.

This run is deliberately evidence-bounded: it packages the existing Waje
snapshots and the BigQuery authentication failure without inventing X7 HOT
facts. The output is a canonical Data Analytics report artifact plus a
portable Markdown companion and a precise follow-up contract.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "analysis" / "x7_hot_rank_diagnostic_2026_09_04"
RUN.mkdir(parents=True, exist_ok=True)

RUN_AT = "2026-09-04T18:00:00+08:00"


def read_json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


aug_games = read_json("analysis/tc_august_monthly_2026_09_03/game_summary.json")
recent_games = read_json(
    "analysis/tc_three_day_global_audit_2026_08_28/lifecycle_game_rtp_14d/game_summary_weighted.json"
)
ga4_summary = read_json(
    "analysis/h5_lightgame_report_reorg_2026_08_31/analysis_summary.json"
)
game_dictionary = read_json(
    "analysis/game_code_dictionary_2026_08_31/game_code_name_mapping.json"
)
aug_artifact = read_json("analysis/tc_august_monthly_2026_09_03/artifact.json")
ga4_receipt = read_json(
    "analysis/h5_lightgame_report_reorg_2026_08_31/ga4_query_receipt.json"
)


def has_x7(value) -> bool:
    return "x7" in str(value or "").lower()


def compact_game_rows(rows, bet_key, rtp_key, share_key, profit_key):
    out = []
    for row in sorted(rows, key=lambda x: float(x.get(bet_key) or 0), reverse=True)[:10]:
        out.append(
            {
                "game": row.get("game"),
                "bet_amount": row.get(bet_key),
                "actual_profit": row.get(profit_key),
                "actual_rtp": row.get(rtp_key),
                "bet_share": row.get(share_key),
                "data_state": row.get("data_state", "actual_aggregate"),
                "granularity_note": "Tada is provider-level aggregate; not an individual game fact."
                if str(row.get("game", "")).lower() == "tada"
                else "game-level aggregate in current snapshot",
            }
        )
    return out


aug_total_bet = sum(float(x.get("full_bet") or 0) for x in aug_games)
aug_total_profit = sum(float(x.get("actual_profit") or 0) for x in aug_games)
aug_actual_rtp = 1 - (aug_total_profit / aug_total_bet) if aug_total_bet else None
aug_top = compact_game_rows(
    aug_games, "full_bet", "actual_rtp", "bet_share", "actual_profit"
)

recent_total_bet = sum(float(x.get("second_full_bet") or 0) for x in recent_games)
recent_total_profit = sum(float(x.get("second_actual_profit") or 0) for x in recent_games)
recent_actual_rtp = (
    1 - recent_total_profit / recent_total_bet if recent_total_bet else None
)
recent_top = compact_game_rows(
    [
        {
            "game": x.get("game"),
            "second_full_bet": x.get("second_full_bet"),
            "second_actual_profit": x.get("second_actual_profit"),
            "second_actual_rtp": x.get("second_actual_rtp"),
            "second_bet_share": x.get("second_bet_share"),
            "data_status": x.get("data_status"),
        }
        for x in recent_games
    ],
    "second_full_bet",
    "second_actual_rtp",
    "second_bet_share",
    "second_actual_profit",
)

ga4_games = []
for game in ga4_summary.get("games", []):
    ga4_games.append(
        {
            "game_id": game.get("game_id"),
            "game": game.get("game"),
            "new_visitors": game.get("new_visitors"),
            "all_visitors": game.get("all_visitors"),
            "page_views": game.get("page_views"),
            "d1_return_rate": game.get("d1_return_rate"),
            "d3_return_rate": game.get("d3_return_rate"),
            "data_state": "provisional_h5_ga4",
            "granularity_note": "game page behavior, not exposure/click/ranking or server settlement",
        }
    )

x7_name_matches = [
    x
    for x in game_dictionary.get("top_games", [])
    if has_x7(x.get("game_name")) or has_x7(x.get("game_id"))
]
x7_aug_matches = [x for x in aug_games if has_x7(x.get("game"))]
x7_recent_matches = [x for x in recent_games if has_x7(x.get("game"))]
x7_ga4_matches = [x for x in ga4_games if has_x7(x.get("game")) or has_x7(x.get("game_id"))]

coverage_matrix = [
    {
        "source": "BigQuery wajenigeria",
        "window": "requested near-90-day Waje facts",
        "grain": "not read",
        "status": "blocked_authentication",
        "supports_x7": "not_available",
        "evidence": "list_dataset_ids returned Auth required",
    },
    {
        "source": "Lifecycle V2 Joint game summary",
        "window": "2026-08-01—2026-08-31",
        "grain": "business_date × game × lifecycle; 31 game rows in monthly summary",
        "status": "actual_aggregate",
        "supports_x7": "no_match",
        "evidence": "Tada is present as provider-level aggregate; no X7 HOT label or ID",
    },
    {
        "source": "Lifecycle game RTP 14-day snapshot",
        "window": "2026-08-19—2026-09-01",
        "grain": "two-window game aggregate; 31 game rows",
        "status": "actual_aggregate",
        "supports_x7": "no_match",
        "evidence": "no X7 HOT label or ID; no package/entry/ranking dimensions",
    },
    {
        "source": "GA4 H5 Top Game page snapshot",
        "window": "2026-08-21—2026-08-27",
        "grain": "five self-developed lightweight game IDs × day",
        "status": "provisional",
        "supports_x7": "no_match",
        "evidence": "page visits and return behavior only; no exposure/click or X7 HOT",
    },
    {
        "source": "Waje game code dictionary",
        "window": "revision 609",
        "grain": "game ID × name × provider",
        "status": "actual_dictionary",
        "supports_x7": "no_match",
        "evidence": "596 valid records, 156 TaDa provider rows, no X7 HOT mapping",
    },
]

requested_contract = [
    {
        "field": "game_id / canonical_game_name",
        "status": "blocked",
        "current_gap": "X7 HOT ID/name mapping is not present in local Waje dictionary or game snapshots",
        "needed_source": "authenticated Waje game dictionary or TaDa game mapping",
    },
    {
        "field": "daily_top_game_rank / display_position",
        "status": "blocked",
        "current_gap": "no historical Top Game position or ranking-policy snapshot",
        "needed_source": "recommendation/ranking decision log or daily display-position aggregate",
    },
    {
        "field": "impressions / exposed_users / clicks",
        "status": "blocked",
        "current_gap": "GA4 page visits cannot substitute for Top Game exposure or click facts",
        "needed_source": "RECO_ITEM_IMPRESSION and RECO_ITEM_CLICK aggregate view",
    },
    {
        "field": "favorite_users / repeat_users / repeat_rate",
        "status": "blocked",
        "current_gap": "no X7 HOT favorite or game-level repeat-user event",
        "needed_source": "favorite event plus user-hash deduplicated repeat aggregate",
    },
    {
        "field": "valid_bet / payout / GGR / actual_RTP",
        "status": "blocked",
        "current_gap": "current lifecycle source aggregates TaDa as provider-level Tada; BigQuery is auth-blocked",
        "needed_source": "package × platform × game × date terminal-settlement aggregate",
    },
    {
        "field": "H5_vs_App / package / version",
        "status": "blocked",
        "current_gap": "current X7 facts do not carry platform, package, release or version",
        "needed_source": "authenticated event and settlement view with platform/package/version",
    },
]

aggregate_results = {
    "schema_version": 1,
    "status": "partial_blocked_x7_fact",
    "generated_at": RUN_AT,
    "question": "为什么 X7 HOT 长期排名靠前，并且在 Waje H5/App 表现强？",
    "requested_window": "近90天 + Top Game位置变化前后",
    "available_windows": {
        "august_lifecycle": {"start": "2026-08-01", "end": "2026-08-31"},
        "recent_game_rtp": {"start": "2026-08-19", "end": "2026-09-01"},
        "ga4_h5": {"start": "2026-08-21", "end": "2026-08-27"},
    },
    "privacy": "aggregate_only; no user/order/device/credential detail",
    "x7_match_counts": {
        "dictionary": len(x7_name_matches),
        "august_game_summary": len(x7_aug_matches),
        "recent_game_rtp": len(x7_recent_matches),
        "ga4_h5": len(x7_ga4_matches),
    },
    "context_metrics": {
        "august_game_count": len(aug_games),
        "august_total_full_bet": aug_total_bet,
        "august_total_actual_profit": aug_total_profit,
        "august_weighted_actual_rtp": aug_actual_rtp,
        "august_tada_provider_full_bet": next(
            (x.get("full_bet") for x in aug_games if str(x.get("game")).lower() == "tada"),
            None,
        ),
        "august_tada_provider_bet_share": next(
            (x.get("bet_share") for x in aug_games if str(x.get("game")).lower() == "tada"),
            None,
        ),
        "recent_game_count": len(recent_games),
        "recent_total_full_bet": recent_total_bet,
        "recent_weighted_actual_rtp": recent_actual_rtp,
        "ga4_h5_game_ids": len(ga4_games),
    },
    "august_top_games": aug_top,
    "recent_top_games": recent_top,
    "ga4_h5_games": ga4_games,
    "coverage_matrix": coverage_matrix,
    "requested_contract": requested_contract,
    "source_receipts": {
        "august_source_manifest": "analysis/tc_august_monthly_2026_09_03/source_manifest.json",
        "august_quality_checks": "analysis/tc_august_monthly_2026_09_03/quality_checks.json",
        "ga4_receipt": "analysis/h5_lightgame_report_reorg_2026_08_31/ga4_query_receipt.json",
        "bigquery_attempt": "2026-09-04 list_dataset_ids project= w ajenigeria -> Auth required",
    },
}

(RUN / "aggregate-results.json").write_text(
    json.dumps(aggregate_results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)

quality_checks = {
    "schema_version": 1,
    "status": "partial_blocked",
    "checks": [
        {
            "check": "BigQuery authentication",
            "result": "Auth required",
            "status": "blocked",
            "impact": "cannot read requested near-90-day package/platform/event/settlement facts",
        },
        {
            "check": "X7 HOT game dictionary match",
            "result": len(x7_name_matches),
            "status": "blocked",
            "impact": "no canonical X7 game_id/name mapping",
        },
        {
            "check": "August lifecycle snapshot completeness",
            "result": "31/31 days; 31 game rows in summary",
            "status": "passed_for_context",
            "impact": "context only; TaDa remains provider aggregate",
        },
        {
            "check": "Recent 14-day game snapshot",
            "result": f"{len(recent_games)} game rows; no X7 match",
            "status": "passed_for_context",
            "impact": "cannot explain X7 ranking or platform split",
        },
        {
            "check": "GA4 H5 Top Game evidence",
            "result": f"{len(ga4_games)} self-developed game IDs; page behavior only",
            "status": "provisional",
            "impact": "cannot substitute for exposure, click, favorite, or settlement facts",
        },
        {
            "check": "Sensitive-data boundary",
            "result": "aggregate-only outputs; no credentials or user-level rows",
            "status": "passed",
            "impact": "safe for internal review",
        },
    ],
}
(RUN / "quality-checks.json").write_text(
    json.dumps(quality_checks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)

source_receipt = {
    "schema_version": 1,
    "status": "partial_blocked_x7_fact",
    "executed_at": RUN_AT,
    "question": aggregate_results["question"],
    "sources": [
        {
            "label": "Lifecycle V2 Joint August game summary",
            "path": "analysis/tc_august_monthly_2026_09_03/game_summary.json",
            "window": "2026-08-01—2026-08-31",
            "grain": "game × lifecycle monthly aggregate",
            "status": "actual_aggregate",
        },
        {
            "label": "Lifecycle game RTP 14-day snapshot",
            "path": "analysis/tc_three_day_global_audit_2026_08_28/lifecycle_game_rtp_14d/game_summary_weighted.json",
            "window": "2026-08-19—2026-09-01",
            "grain": "two-window game aggregate",
            "status": "actual_aggregate",
        },
        {
            "label": "GA4 H5 Top Game page snapshot",
            "path": "analysis/h5_lightgame_report_reorg_2026_08_31/analysis_summary.json",
            "window": "2026-08-21—2026-08-27",
            "grain": "H5 game page behavior aggregate",
            "status": "provisional",
        },
        {
            "label": "Waje game code dictionary",
            "path": "analysis/game_code_dictionary_2026_08_31/game_code_name_mapping.json",
            "window": "revision 609",
            "grain": "game ID × name × provider",
            "status": "actual_dictionary",
        },
        {
            "label": "BigQuery Waje project",
            "path": "project wajenigeria",
            "window": "requested near-90-day window",
            "grain": "not read",
            "status": "blocked_authentication",
            "error": "Auth required",
        },
    ],
    "safety": "aggregate-only; no user, order, device, account, credential or raw response detail",
}
(RUN / "source-receipt.json").write_text(
    json.dumps(source_receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)


def pct(value):
    return "N/A" if value is None else f"{value * 100:.2f}%"


def money(value):
    return "N/A" if value is None else f"{value:,.2f}"


aug_tada = next((x for x in aug_games if str(x.get("game")).lower() == "tada"), {})

report_md = f"""# X7 HOT 长期排名与高表现原因分析｜Waje 侧数据入口审计

## Executive Summary

**当前还不能回答“X7 HOT 为什么长期排名第一”。** 本轮 Waje 侧核查没有取得 X7 HOT 的可识别游戏 ID、历史 Top Game 展示位置、曝光/点击、收藏/复玩或单游戏结算事实；BigQuery `wajenigeria` 元数据访问返回 `Auth required`。

**现有数据可以证明 Waje 的游戏经营数据存在，但不能证明 X7 HOT 的单游戏表现。** 2026 年 8 月生命周期游戏汇总有 31 个游戏粒度行、完全下注额约 {money(aug_total_bet)}、加权实际 RTP {pct(aug_actual_rtp)}；其中 `Tada` 下注额约 {money(aug_tada.get('full_bet'))}、占比 {pct(aug_tada.get('bet_share'))}，但这是 TaDa 厂商级聚合，不是 X7 HOT。

**现有 H5 Top Game 数据也不能替代推荐数据。** GA4 仅覆盖 5 个自研轻量化游戏 ID的页面访问和回访行为，没有 X7 HOT、Top Game 曝光/点击、收藏事件，也没有 App 对照。

**本次已完成数据入口、可用背景和补数合同；正式原因分析需要补齐 X7 HOT 映射和认证聚合事实。** 在这些事实到位前，不能把“用户收藏复玩”“推荐算法”“游戏 RTP/GGR”中的任何一个写成已验证原因。

## 1. 当前可用背景：规模数据存在，但 X7 HOT 不在可识别粒度

| 数据源 | 时间窗口 | 当前粒度 | 可见结果 | 对 X7 HOT 的支持 |
|---|---|---|---|---|
| Lifecycle V2 Joint 游戏汇总 | 2026-08-01—08-31 | 游戏×生命周期月度聚合 | 31 个游戏行；总完全下注额 {money(aug_total_bet)}；实际 RTP {pct(aug_actual_rtp)} | 不支持；TaDa 为厂商级 `Tada` |
| 游戏 RTP 14 日快照 | 2026-08-19—09-01 | 游戏两窗口聚合 | {len(recent_games)} 个游戏行；没有 X7 HOT | 不支持；缺端、包体、入口和排名 |
| GA4 H5 Top Game 页面 | 2026-08-21—08-27 | 5 个自研轻量化游戏×日 | 有页面访问及 D1/D3 回访 | 不支持；页面访问不等于曝光/点击/有效下注 |
| 游戏字典 | revision 609 | 游戏 ID×名称×厂商 | 596 条有效记录，其中 TaDa 156 条 | 不支持；无 X7 HOT映射 |

### 现有游戏下注规模背景

图表中的 `Tada` 代表 TaDa 厂商聚合，不代表 X7 HOT；该图只用于说明当前 Waje 汇总层的规模结构，不能用于解释 X7 HOT 排名。

## 2. X7 HOT 原因分析的关键证据缺口

| 需要验证的事实 | 当前状态 | 缺失原因 | 不能替代的字段 |
|---|---|---|---|
| X7 HOT canonical `game_id` | `blocked` | 本地字典、8 月汇总、14 日快照和 GA4 H5 快照均无匹配 | 不能用 `Tada` 厂商名代替 |
| Top Game 历史排名/展示位置 | `blocked` | 没有历史排序决策或每日展示位快照 | 不能用当前页面位置反推长期排名 |
| Top Game 曝光用户/次数 | `blocked` | 没有 `RECO_ITEM_IMPRESSION` 聚合 | 不能用 `page_view`代替 |
| Top Game 点击及点击率 | `blocked` | 没有推荐卡片点击事实 | 不能用游戏进入或页面访问代替 |
| 收藏用户与收藏后复玩 | `blocked` | 没有收藏事件与关联键 | 不能用重复 page_view代替收藏 |
| X7 HOT 复玩用户占比 | `blocked` | 没有 X7 HOT 单游戏用户去重事实 | 不能由全平台 D1/D7 留存推导 |
| X7 HOT 下注、派奖、GGR、RTP | `blocked` | 当前 TaDa 为厂商级聚合；BigQuery 认证阻断 | 不能用厂商 RTP或生命周期 RTP代替 |
| H5/App/包体/版本分层 | `blocked` | 当前 X7事实未带端、包体、版本 | 不能把 H5现象概括为全平台现象 |

## 3. 已完成的假设验证边界

### 用户收藏与重复游玩

当前没有 X7 HOT 的收藏事件、游戏级复玩用户或收藏后再次进入事实。因此该假设目前只能列为**待验证假设**，没有支持或否定证据。

### 推荐展示位或排序算法

当前没有 Top Game 历史位置、曝光次数、推荐策略版本或排序原因。不能判断 X7 HOT 的高表现是流量位置带来的，还是本身吸引力带来的。

### 游戏自身投注表现

当前只能看到 `Tada` 厂商聚合下注与 RTP，无法从中拆出 X7 HOT。不能将 TaDa 厂商级规模、RTP或GGR归因到 X7 HOT。

### H5/App或包体流量结构

当前 GA4 数据只提供 H5 自研轻量化游戏页面行为，且没有 X7 HOT；App、包体、版本和推荐入口事实均缺失。因此不能作 H5/App 差异结论。

## 4. 下一轮认证数据到位后的执行顺序

1. **先做游戏映射。** 将 X7 HOT 映射到唯一 `game_id`，同时核对 TaDa 游戏名称、别名、厂商和版本。
2. **再复现排名。** 按日读取 H5/App 的 Top Game 展示位置、策略版本、曝光、点击和游戏进入。
3. **拆用户行为。** 仅保留聚合结果，计算 X7 HOT 的复玩用户占比、人均游戏次数、D1/D7复玩和收藏后复访。
4. **对齐经营事实。** 按端、包体、版本、日期和游戏读取有效下注、最终派奖、GGR、RTP、有效局数和高额派奖占比。
5. **做驱动分解。** 将 GGR 拆成用户规模、参与深度、客单/下注深度和 RTP/留存贡献，区分流量位置效应与游戏自身效应。
6. **再做 TaDa 对账。** TaDa 后台仅作为第二阶段事实源，对齐时区、币种、Agent/Company、下注/派奖状态和结算延迟。

目标公式：

```text
点击率 = 推荐卡片点击次数 ÷ 合格推荐卡片曝光次数
进入率 = X7 HOT进入用户数 ÷ X7 HOT点击用户数
复玩用户占比 = 窗口内再次有效游玩用户数 ÷ X7 HOT活跃游戏用户数
RTP = 最终派奖金额 ÷ 有效下注金额
GGR = 有效下注金额 − 最终派奖金额
```

所有比率按累计分子/分母计算；禁止对日 RTP、用户 RTP或局 RTP做简单平均。

## 5. 下一步最小数据合同

需要数据开发提供一张只读、聚合、可按日刷新视图，至少包含：

```text
business_date
platform
package_name
app_version / web_version
release_id
entry_source
placement_id
display_position
recommendation_policy_version
game_id
canonical_game_name
impression_count
exposed_user_count
click_count
click_user_count
game_enter_user_count
favorite_user_count
repeat_user_count
valid_bet_amount
final_payout_amount
valid_round_count
high_payout_amount
data_cutoff_at
data_status
```

用户关联只允许使用哈希键在受限环境中去重，正式报告只输出聚合结果。

## Recommended next steps

1. **P0：解除 BigQuery 认证阻断。** 先验证 `wajenigeria` 可读项目、数据集和授权聚合 View。
2. **P0：确认 X7 HOT 的唯一游戏 ID。** 同步 TaDa 游戏字典与 Waje 游戏字典，消除名称/别名歧义。
3. **P0：补齐 Top Game 推荐事实。** 建立曝光、点击、位置、推荐原因和策略版本的日级聚合。
4. **P0：补齐 X7 HOT 结算事实。** 端、包体、版本、有效下注、最终派奖和 GGR/RTP必须能同口径对账。
5. **P1：再判断收藏与复玩。** 在关联键和成熟窗口具备后，单独检验“用户偏好”假设。

## Further Questions

- X7 HOT 在 TaDa 后台对应的唯一 `game_id` 和正式名称是什么？
- “长期排名第一”是 Top Game 固定展示排名，还是按下注额、GGR、活跃用户或综合分数排名？
- Top Game 位置何时发生过变化？是否有推荐策略或版本发布记录？
- X7 HOT 是否同时出现在 H5、Android、iOS及哪些包体？
- 收藏功能是否在 H5/App 两端都存在，并且是否已有事件上报？

## Caveats and Assumptions

- 本轮报告状态为 `partial_blocked_x7_fact`，不是 X7 HOT 业务结论。
- 近 90 天主窗口尚未取得；当前实际可用背景为 8 月完整月、8 月 19 日至 9 月 1 日游戏快照和 8 月 21—27 日 GA4 H5 快照。
- `Tada` 是当前生命周期游戏汇总中的厂商级名称，不等于 X7 HOT。
- GA4 游戏页面访问是行为信号，不等于 Top Game曝光、点击、有效下注或结算成功。
- BigQuery `wajenigeria` 当前访问返回 `Auth required`；没有把认证失败解释为数据不存在。
- 本次只保存聚合结果、数据质量回执和字段合同，不保存账号、密码、Cookie、Token、用户、订单或设备明细。

来源与回执：`aggregate-results.json`、`quality-checks.json`、`source-receipt.json`；原始来源引用保留在本分析目录及现有快照目录中。
"""
(RUN / "report.md").write_text(report_md, encoding="utf-8")

external_reply = """# 给 TaDa 的 X7 HOT 问题回复稿（待 Waje 数据核验后发送）

我们正在核对 X7 HOT 长期表现较好的原因。目前 Waje 侧还需要先确认 X7 HOT 对应的唯一游戏 ID，并补齐 H5/App 的展示位置、曝光、点击、复玩、收藏以及下注/派奖数据。

我们会分别判断：

1. 是否主要由 Top Game 展示位或推荐策略带来流量；
2. 是否存在较高的用户重复游玩和收藏后复访；
3. 是否由游戏自身的下注规模、GGR 和稳定 RTP 表现带动；
4. 是否只集中在某一端、包体、版本或渠道。

在完成游戏 ID、时间窗口和结算口径对齐前，我们不会把当前的厂商级 TaDa 汇总数据直接归因到 X7 HOT。核验完成后，我们会提供按日和按端的聚合对比结果。
"""
(RUN / "external-reply.md").write_text(external_reply, encoding="utf-8")


def source_query(label, description, path, filters, status="actual"):
    sql_path = {
        "analysis/tc_august_monthly_2026_09_03/game_summary.json": "analysis/x7_hot_rank_diagnostic_2026_09_04/sql/02_august_game_context_snapshot.sql",
        "analysis/tc_three_day_global_audit_2026_08_28/lifecycle_game_rtp_14d/game_summary_weighted.json": "analysis/x7_hot_rank_diagnostic_2026_09_04/sql/03_recent_game_context_snapshot.sql",
        "analysis/h5_lightgame_report_reorg_2026_08_31/analysis_summary.json": "analysis/h5_lightgame_report_reorg_2026_08_31/sql/09_ga4_top_game_pages.sql",
        "analysis/game_code_dictionary_2026_08_31/game_code_name_mapping.json": "analysis/game_code_dictionary_2026_08_31/build_game_dictionary.py",
    }.get(path)
    return {
        "id": label,
        "label": description,
        **({"path": sql_path} if sql_path else {}),
        "query": {
            "engine": "local reviewed aggregate snapshot",
            "description": description,
            "executed_at": RUN_AT,
            "filters": filters,
            "tables_used": [path],
            "status": status,
        },
    }


manifest_sources = [
    source_query(
        "src-aug-game",
        "Lifecycle V2 Joint August game summary; Tada is provider-level aggregate.",
        "analysis/tc_august_monthly_2026_09_03/game_summary.json",
        ["2026-08-01—2026-08-31", "lifecycle 1—4", "aggregate only"],
    ),
    source_query(
        "src-recent-game",
        "Lifecycle two-window game RTP snapshot for recent context; no X7 HOT match.",
        "analysis/tc_three_day_global_audit_2026_08_28/lifecycle_game_rtp_14d/game_summary_weighted.json",
        ["2026-08-19—2026-09-01", "game aggregate", "no package or ranking fields"],
    ),
    source_query(
        "src-ga4-h5",
        "GA4 H5 game page and return snapshot; page behavior only.",
        "analysis/h5_lightgame_report_reorg_2026_08_31/analysis_summary.json",
        ["2026-08-21—2026-08-27", "H5", "five self-developed game IDs"],
        status="provisional",
    ),
    source_query(
        "src-game-dictionary",
        "Waje game ID/name/provider dictionary revision 609.",
        "analysis/game_code_dictionary_2026_08_31/game_code_name_mapping.json",
        ["revision 609", "game ID/name/provider"],
    ),
    {
        "id": "src-bq-blocked",
        "label": "BigQuery Waje project authentication attempt",
        "path": "analysis/x7_hot_rank_diagnostic_2026_09_04/sql/01_x7_hot_diagnostic_contract.sql",
        "query": {
            "engine": "BigQuery MCP",
            "description": "Dataset discovery for project wajenigeria was attempted before data queries.",
            "executed_at": RUN_AT,
            "filters": ["project: wajenigeria"],
            "status": "blocked_authentication",
            "error": "Auth required",
        },
    },
]

snapshot_datasets = {
    "coverage_matrix": coverage_matrix,
    "august_top_games": aug_top,
    "recent_top_games": recent_top,
    "ga4_h5_games": ga4_games,
    "requested_contract": requested_contract,
}

artifact = {
    "surface": "report",
    "manifest": {
        "version": 1,
        "surface": "report",
        "title": "X7 HOT 长期排名与高表现原因分析｜Waje 侧数据入口审计",
        "description": "基于现有 Waje 聚合快照，审计 X7 HOT 长期排名问题的可验证性；不虚构缺失的单游戏、推荐或结算事实。",
        "generatedAt": RUN_AT,
        "sources": manifest_sources,
        "cards": [],
        "charts": [
            {
                "id": "august-game-bet-share",
                "title": "2026年8月游戏下注额占比（现有粒度）",
                "subtitle": "仅作为 Waje 规模背景；Tada 为厂商级聚合，不代表 X7 HOT。",
                "type": "bar",
                "dataset": "august_top_games",
                "sourceId": "src-aug-game",
                "layout": "full",
                "encodings": {
                    "x": {"field": "game", "type": "nominal", "label": "游戏/厂商聚合"},
                    "y": {"field": "bet_share", "type": "quantitative", "format": "percent", "label": "下注额占比"},
                    "tooltip": [
                        {"field": "game", "type": "nominal"},
                        {"field": "bet_amount", "type": "quantitative", "format": "number"},
                        {"field": "actual_rtp", "type": "quantitative", "format": "percent"},
                        {"field": "granularity_note", "type": "text"},
                    ],
                },
            },
            {
                "id": "recent-game-bet-share",
                "title": "近14日游戏下注额占比（现有粒度）",
                "subtitle": "2026年8月19日至9月1日；用于背景对照，不包含 X7 HOT 单游戏事实。",
                "type": "bar",
                "dataset": "recent_top_games",
                "sourceId": "src-recent-game",
                "layout": "full",
                "encodings": {
                    "x": {"field": "game", "type": "nominal", "label": "游戏/厂商聚合"},
                    "y": {"field": "bet_share", "type": "quantitative", "format": "percent", "label": "下注额占比"},
                    "tooltip": [
                        {"field": "game", "type": "nominal"},
                        {"field": "bet_amount", "type": "quantitative", "format": "number"},
                        {"field": "actual_rtp", "type": "quantitative", "format": "percent"},
                        {"field": "granularity_note", "type": "text"},
                    ],
                },
            },
        ],
        "tables": [
            {
                "id": "coverage-matrix",
                "title": "数据源与 X7 HOT 可用性矩阵",
                "subtitle": "Auth、无匹配、行为代理和厂商聚合分别显示，不把缺失显示为 0。",
                "dataset": "coverage_matrix",
                "sourceId": "src-aug-game",
                "layout": "full",
                "defaultSort": {"field": "status", "direction": "asc"},
                "columns": [
                    {"field": "source", "label": "数据源", "type": "text"},
                    {"field": "window", "label": "时间窗口", "type": "text"},
                    {"field": "grain", "label": "粒度", "type": "text"},
                    {"field": "status", "label": "状态", "type": "text"},
                    {"field": "supports_x7", "label": "X7 HOT支持", "type": "text"},
                    {"field": "evidence", "label": "证据说明", "type": "text"},
                ],
            },
            {
                "id": "august-top-games",
                "title": "2026年8月现有游戏汇总背景",
                "subtitle": "精确值用于查阅；Tada 行是供应商聚合，不能作为 X7 HOT。",
                "dataset": "august_top_games",
                "sourceId": "src-aug-game",
                "layout": "full",
                "defaultSort": {"field": "bet_amount", "direction": "desc"},
                "columns": [
                    {"field": "game", "label": "游戏/厂商", "type": "text"},
                    {"field": "bet_amount", "label": "完全下注额", "type": "number", "format": "number"},
                    {"field": "actual_profit", "label": "实际盈利", "type": "number", "format": "number"},
                    {"field": "actual_rtp", "label": "实际RTP", "type": "number", "format": "percent"},
                    {"field": "bet_share", "label": "下注额占比", "type": "number", "format": "percent"},
                    {"field": "granularity_note", "label": "粒度说明", "type": "text"},
                ],
            },
            {
                "id": "requested-contract",
                "title": "X7 HOT 后续认证数据合同",
                "subtitle": "数据开发补齐后才能完成原因归因；当前全部按状态显示。",
                "dataset": "requested_contract",
                "sourceId": "src-bq-blocked",
                "layout": "full",
                "defaultSort": {"field": "status", "direction": "asc"},
                "columns": [
                    {"field": "field", "label": "字段/指标", "type": "text"},
                    {"field": "status", "label": "状态", "type": "text"},
                    {"field": "current_gap", "label": "当前缺口", "type": "text"},
                    {"field": "needed_source", "label": "所需来源", "type": "text"},
                ],
            },
        ],
        "blocks": [
            {"id": "title", "type": "markdown", "body": "# X7 HOT 长期排名与高表现原因分析｜Waje 侧数据入口审计"},
            {"id": "summary", "type": "markdown", "body": "## Executive Summary\n\n" + report_md.split("## 1. 当前可用背景")[0].split("## Executive Summary\n\n", 1)[1]},
            {"id": "context", "type": "markdown", "body": "## 1. 当前可用背景：规模数据存在，但 X7 HOT 不在可识别粒度\n\n现有快照可以用于说明 Waje 的整体游戏规模和数据覆盖，但不包含 X7 HOT 单游戏事实。`Tada` 是供应商聚合名称，不能当作 X7 HOT。"},
            {"id": "context-chart", "type": "chart", "chartId": "august-game-bet-share"},
            {"id": "evidence", "type": "markdown", "body": "## 2. X7 HOT 原因分析的关键证据缺口\n\n没有唯一游戏 ID、历史展示位、曝光/点击、收藏/复玩和单游戏结算事实，当前不能判断用户偏好、推荐算法、游戏自身表现或端/包体结构哪个是主因。"},
            {"id": "coverage-table", "type": "table", "tableId": "coverage-matrix"},
            {"id": "hypotheses", "type": "markdown", "body": "## 3. 已完成的假设验证边界\n\n当前只能确认数据入口和缺口，不能把收藏复玩、推荐位置或 RTP/GGR 写成已验证原因。GA4 页面访问也不能替代推荐曝光、点击或结算事实。"},
            {"id": "recent-chart", "type": "chart", "chartId": "recent-game-bet-share"},
            {"id": "execution", "type": "markdown", "body": "## 4. 下一轮认证数据到位后的执行顺序\n\n先做 X7 HOT 游戏映射，再复现排名和推荐漏斗，随后拆用户复玩与收藏，最后对齐下注、派奖、GGR/RTP和 H5/App 包体维度。"},
            {"id": "contract-table", "type": "table", "tableId": "requested-contract"},
            {"id": "next", "type": "markdown", "body": "## Recommended next steps\n\n1. **P0：解除 BigQuery 认证阻断。** 验证 `wajenigeria` 可读项目、数据集和授权聚合 View。\n2. **P0：确认 X7 HOT 唯一游戏 ID。** 同步 TaDa 与 Waje 游戏字典。\n3. **P0：补齐推荐曝光/点击/位置和 X7 HOT 结算事实。**\n4. **P1：在关联键和成熟窗口具备后，检验收藏与复玩假设。"},
            {"id": "questions", "type": "markdown", "body": "## Further Questions\n\n- X7 HOT 在 TaDa 后台对应哪个唯一 `game_id`？\n- 长期排名第一的排序指标和 Top Game 位置变化日期是什么？\n- X7 HOT 是否同时覆盖 H5、Android、iOS及哪些包体？"},
            {"id": "caveats", "type": "markdown", "body": "## Caveats and Assumptions\n\n- 本轮状态为 `partial_blocked_x7_fact`，不是 X7 HOT 业务结论。\n- BigQuery 访问失败不解释为数据不存在。\n- 所有输出仅保留聚合数据，不保存用户、订单、设备或凭证。"},
        ],
    },
    "snapshot": {
        "version": 1,
        "generatedAt": RUN_AT,
        "status": "partial",
        "accessIssues": [
            {"id": "bq-auth", "severity": "high", "status": "blocked", "message": "BigQuery project wajenigeria dataset discovery returned Auth required."},
            {"id": "x7-mapping", "severity": "high", "status": "blocked", "message": "No X7 HOT game ID/name match in the reviewed Waje snapshots and dictionary."},
            {"id": "ranking-history", "severity": "medium", "status": "blocked", "message": "No historical Top Game position, exposure, click or favorite aggregate is available."},
            {"id": "platform-split", "severity": "medium", "status": "blocked", "message": "Current X7 facts do not support H5/App/package/version comparison."},
        ],
        "datasets": snapshot_datasets,
    },
}
(RUN / "artifact.json").write_text(
    json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)

print(json.dumps({"status": aggregate_results["status"], "run": str(RUN), "august_games": len(aug_games), "x7_matches": aggregate_results["x7_match_counts"]}, ensure_ascii=False))
