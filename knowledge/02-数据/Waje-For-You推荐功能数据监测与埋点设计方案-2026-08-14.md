---
type: data-monitoring-design
date: 2026-08-14
status: design
product_version: "2.20"
tags: [For-You, 推荐系统, 数据指标, 埋点, H5, APP, 留存]
---

# Waje 2.20「For You」推荐功能数据监测与埋点设计方案

## 1. 设计目标

围绕“推荐是否帮助用户更快找到可玩的游戏，并形成有效游玩与长期留存”建设数据闭环，覆盖：

```text
推荐请求 → 列表生成 → 模块/卡片曝光 → 点击 → 游戏可玩 → 有效局 → D7复玩与付费留存
```

适用范围：H5/PWA、Android、iOS 的 For You 推荐模块；H5 的 Show all、换一批和 My Games 可复用同一套关联键。

## 2. 核心指标

| # | 指标ID | 指标 | 口径 | 作用 |
|---:|---|---|---|---|
| 1 | `reco_request_success_rate` | 推荐请求成功率 | 成功返回合法列表的请求 ÷ 有效请求 | 服务可用性 |
| 2 | `reco_module_view_rate` | 模块到达率 | 看到 For You 模块的用户 ÷ 进入游戏首页用户 | 模块触达 |
| 3 | `reco_item_ctr` | 推荐卡片点击率 | 去重点击曝光 ÷ 合格卡片曝光 | 内容吸引力 |
| 4 | `reco_click_playable_rate` | 点击后可玩率 | 到达 `BET_READY` 的推荐点击 ÷ 推荐点击 | 体验质量 |
| 5 | `reco_click_valid_play_rate` | 点击后有效游玩率 | 产生服务端有效局的推荐点击用户 ÷ 推荐点击用户 | 推荐准确性 |
| 6 | `reco_exposure_valid_play_rate` | 推荐有效游玩转化率 | 通过推荐形成有效局的用户 ÷ 模块曝光用户 | **核心业务指标** |
| 7 | `reco_new_game_discovery_rate` | 新游戏发现率 | 玩到近30天未玩游戏的用户 ÷ 推荐有效游玩用户 | 游戏发现 |
| 8 | `reco_repeat_play_d7` | 推荐游戏D7复玩率 | D1–D7再次玩该游戏的成熟用户 ÷ 首次推荐有效游玩用户 | 内容长期价值 |
| 9 | `payer_retention_d7_lift` | 付费用户D7留存增量 | 实验组付费用户D7留存 − 对照组 | **战略结果指标** |

### 诊断指标

- 推荐服务：空结果率、兜底率、平均候选数、平均返回数、接口 P50/P95/P99、缓存命中率和错误码分布。
- 推荐质量：位置转化、推荐原因转化、游戏/供应商覆盖率、Top 10曝光占比、列表重复率。
- 体验护栏：页面 ready、`GAME_READY/BET_READY` P75/P90、加载失败率、下注与结算成功率。
- 数据质量：事件入库率、必填字段完整率、重复率、入库延迟和跨事件关联率。

## 3. 转化漏斗与归因

主漏斗：

```text
游戏首页访问
  → For You模块曝光
  → 推荐卡片曝光
  → 推荐点击
  → GAME_LOAD
  → GAME_READY
  → BET_READY
  → 服务端有效局
  → D7复玩 / 付费用户D7留存
```

推荐点击后生成 `entry_context_id`，贯穿游戏加载和服务端有效局：

```text
recommendation_request_id
  → recommendation_list_id
  → impression_id
  → click_id
  → entry_context_id
  → game_load_id
  → round_id
```

默认直接归因窗口建议为“点击后30分钟内、同一用户、同一游戏”。第三方游戏无法透传关联键时，可用 `user_id + game_id + 时间窗`推导，并标记 `attribution_confidence=derived`。

## 4. 埋点事件设计

### 4.1 推荐专项事件

| 事件 | 来源与触发 | 关键字段 |
|---|---|---|
| `RECO_REQUESTED` | 服务端接受推荐请求 | 请求ID、页面/坑位、数量、策略版、实验组、用户/环境快照 |
| `RECO_LIST_GENERATED` | 服务端完成决策或失败 | 列表ID、状态、候选/过滤/返回数、兜底、耗时、缓存、错误码 |
| `RECO_LIST_RENDERED` | 客户端渲染列表成功或失败 | 列表ID、实际卡片数、渲染状态/耗时/错误 |
| `RECO_MODULE_VIEWED` | 模块达到可见标准 | 模块曝光ID、列表ID、页面、坑位、可见时长 |
| `RECO_ITEM_IMPRESSION` | 卡片可见≥50%且持续≥1秒 | 曝光ID、游戏、算法排名、展示位置、推荐原因 |
| `RECO_ITEM_CLICK` | 点击推荐卡片 | 点击ID、曝光ID、游戏、位置、入口上下文ID |
| `RECO_BATCH_CHANGED` | 点击换一批并返回结果 | 列表ID、前后批次、cursor、has_more、结果和耗时 |
| `RECO_SHOW_ALL_CLICK` | 点击 Show all | 页面、列表ID、当前批次和位置 |

### 4.2 复用业务事件

| 现有事件/事实 | 需要补充的关联字段 |
|---|---|
| `H5_GAME_LOAD / H5_GAME_READY / H5_BET_READY` | `entry_context_id`、请求ID、曝光ID、`entry_source=for_you` |
| APP游戏进入/可玩状态 | 与H5等价的入口、结果、耗时和关联键 |
| `GAMESTART`、有效局与结算事实 | 入口上下文、请求ID、实验ID/组别 |
| `ORDER`、支付与生命周期事实 | 实验ID/组别，用于整体付费和留存效果分析 |

有效游玩必须使用服务端认证事实，不新建客户端自报的“有效游玩”事件。

## 5. 字段规范

### 通用字段

```text
event_name / event_version / event_uid
event_time_client / event_time_server / received_at
user_id / uuid / session_id / trace_id
platform / surface_type / app_version / web_version / release_id
package_name / channel / country
```

### 推荐专有字段

```text
recommendation_request_id / recommendation_list_id / impression_id
click_id / entry_context_id / game_load_id
game_id / provider_id / source_page / placement_id
batch_no / cursor / algorithm_rank / display_position
reason_code / status / error_code / latency_ms / cache_hit
recommendation_policy_version / game_tag_version
experiment_id / group_id / attribution_confidence
```

客户端不上传完整用户画像、历史充值金额或风险分值，只传快照ID、策略版本和有限原因码。

## 6. 看板设计

### 看板一：推荐核心总览

- 九项核心指标卡片及日/周趋势。
- H5、Android、iOS及包体/版本对比。
- 推荐策略版本和实验组对比。

### 看板二：推荐转化漏斗

- 首页→模块→卡片→点击→可玩→有效局→D7复玩。
- 按游戏、供应商、位置、推荐原因、设备和网络下钻。
- 展示各环节流失人数、转化率及主要失败原因。

### 看板三：服务与数据质量

- 请求成功、空结果、兜底、接口耗时、缓存和错误码。
- 请求→返回→渲染→曝光数量对账。
- 入库完整率、重复率、延迟和关联率。

### 看板四：实验与长期效果

- 实验组/对照组有效游玩增量、新游戏发现和D7复玩。
- 付费用户D1/D7留存、首充与复充作为长期结果。
- D7未成熟 cohort 显示 `N/A`，不显示为0。

全局筛选：日期、实验组、端、包体、版本、渠道、页面/坑位、策略版本、游戏/供应商、用户阶段、设备和网络。

## 7. 数据质量与验收

| 验收项 | 标准 |
|---|---|
| 核心事件入库率 | ≥99.5% |
| 必填字段缺失率 | ≤0.1% |
| 重复事件率 | ≤0.1% |
| 核心事件P95入库延迟 | ≤15分钟 |
| 请求→列表→曝光关联率 | ≥98% |
| 点击→可玩→有效局关联率 | ≥98% |
| 数量对账 | 请求、返回、渲染和曝光差异可解释 |
| 经营事实 | 有效局、结算、支付以服务端认证数据为准 |

无数据、数据延迟、字段缺失、权限不足和D7未成熟必须分别显示。

## 8. 实施顺序

1. **P0：指标与事件契约**——确认九项核心指标、有效游玩口径、关联键和事件字段。
2. **P0：服务端与客户端接入**——完成推荐请求/决策、曝光点击和游戏可玩链路上报。
3. **P0：事实层与数据质量**——建立请求、推荐项、交互和结果事实表，完成对账与告警。
4. **P1：核心看板**——上线总览、漏斗、服务质量和数据质量页面。
5. **P1：实验与长期效果**——稳定分流，评估有效游玩、D7复玩和付费用户D7留存增量。

