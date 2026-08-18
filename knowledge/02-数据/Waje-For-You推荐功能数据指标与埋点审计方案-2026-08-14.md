---
type: data-requirement-audit
date: 2026-08-14
status: draft_for_review
owner: Robin
product_version: "2.20"
source_url: https://ksg964l11fam.sg.larksuite.com/wiki/V7yxwT516icdOCkT7wWlyizMg1e
source_title: 游戏曝光[为你推荐]功能需求
tags: [For-You, 推荐系统, 数据指标, 埋点, H5, PWA, APP, 用户分层, RTP, L3]
related:
  - ../01-产品/WajeGame PRD分级规范-试运行版v1.0-2026-08-04.md
  - ../01-产品/用户分层与场景运营V1.0-V1.1-数据观测与埋点设计-2026-08-10.md
  - Waje埋点事件与属性字典-2026-08-11.md
  - Waje-H5-PWA设备性能转化专项分析与监控方案-2026-08-13.md
  - Waje数据指标看板映射与研发验收清单-2026-08-11.md
---

# Waje 2.20「For You」推荐功能：数据指标与埋点审计方案

## 0. 审计结论

**结论：产品方向具备价值，但数据侧建议“有条件通过”；完成 P0 修订前不进入正式开发验收。**

现有需求已较完整地描述页面范围、用户/游戏标签和推荐顺序，但仍缺少四类关键设计：

1. **需求等级需由 L2 调整为 L3。** 推荐服务使用 RTP、波动性、付费价值、流失分值和投注额度，自动过滤及排序真金游戏，已触发 WajeGame PRD 规范中“RTP/概率、经营决策数据系统、自动化决策和责任博彩”相关的 L3 条件。
2. **业务目标不可验收。** 当前只描述“提升点击、进入和有效游玩”，没有北极星指标、基线、目标值、实验组/对照组、观察周期与停止条件。
3. **现有六个埋点不足以解释推荐结果。** 缺少推荐请求、服务端决策、算法/规则版本、空结果/兜底、过滤原因、渲染失败、接口耗时、实验分组和配置变更记录。
4. **部分标签口径不可直接实施。** “高延迟”“资源等级”“RTP 高中低”“波动性”“有效实际游玩”“PR 值”均缺少可计算口径、版本和数据新鲜度；浏览器侧 RAM 也不能保证可获得。

建议把需求拆成四个可独立验收的交付：

```text
标签与规则配置
  → 推荐决策服务及审计事实
  → 客户端曝光/点击与游戏进入链路
  → 实验、指标看板与发布后验证
```

## 1. 需求方案汇总

### 1.1 产品目标与范围

- 全端由服务端统一生成推荐结果，客户端不计算推荐逻辑。
- H5：游戏首页 For You、Show all、换一批、Recently Played 提升、My Games 入口与页面、普通分类个性化排序。
- Android/iOS：仅游戏首页 For You 标签和推荐游戏展示。
- 推荐逻辑：先过滤不可展示/不适配游戏，再按用户偏好排序，再按体验友好程度排序，最后补足并按游戏 ID 兜底。
- 使用的用户信息：用户阶段、最近行为、偏好标签、付费价值、流失风险、当前网络和设备。
- 使用的游戏信息：分类、主题、玩法、资源、连接方式、复杂度、单局时长、投注额度、RTP、波动性、活动和运营优先级。

### 1.2 产品价值判断

该功能同时解决两个问题：

1. 让低端机、弱网用户优先看到更容易加载、可玩的游戏，降低从首页到首局前的损失。
2. 让不同付费阶段和偏好的用户更快找到可能愿意玩的内容，提高游戏发现、有效游玩和长期留存。

因此，推荐功能不能只用点击率评价。必须同时验证：**是否推荐得准、是否真的能进入并下注、是否发现新游戏、是否形成重复游玩、是否改善付费用户留存，以及是否伤害性能、风险和游戏生态。**

## 2. P0 审计问题与修改建议

| 审计项 | 当前问题 | 风险 | 必须修改 |
|---|---|---|---|
| 需求分级 | 标为 L2，但规则直接使用 RTP、波动性、付费价值和流失风险自动决定游戏曝光 | 缺少高风险规则评审、配置审计、灰度和回滚 | 升为 L3，增加数据系统、RTP/责任博彩、权限审计与发布专项附录 |
| 目标指标 | 没有基线、目标值、实验方案和观察周期 | 上线后只能描述变化，无法判断是否由推荐造成 | 确认主指标、护栏、实验单位、分组比例、最小样本量和 D1/D7 成熟规则 |
| 有效实际游玩 | 未定义 | 客户端点击或 `GAMESTART/GAMEEND` 异常可能被误算为真实游玩 | 以服务端有效局事实为准：有合法 `round_id`、有效下注、最终结算、非测试/机器人；允许资产类型需明确 |
| PR 值 | 名称和方向不清；“流失风险分值”却以 `PR≤70%` 判高风险 | 可能将留存概率、流失概率或百分制混用 | 改为明确字段：`score_type`、`score_value`、`scale`、`model_version`、`scored_at`；缺失为 `unknown`，不得默认成中低风险 |
| 风险类型 | 把“流失风险”与其他风险混在同一语义 | 可能将召回模型用于责任博彩、风控或羊毛用户，造成错误自动决策 | 分开 `churn_risk`、`responsible_gaming_risk`、`fraud_abuse_risk`、`payment_risk`；后三类只能按审批规则限制，不能作为普通偏好排序 |
| 游戏可展示底线 | 未包含封禁、自我排除、国家/渠道限制、供应商故障、币种/资产兼容等 | 可能向不应进入的用户或不可用环境展示真金游戏 | 先执行合规与可用性硬门禁，再做网络/偏好/体验排序；硬门禁必须有原因码 |
| 网络高延迟 | 只有“正常/高延迟”，无测量窗口与阈值 | 不同端判断不一致、网络抖动导致列表频繁变化 | 定义来源、RTT/effective type/超时阈值、测量时间窗与 `unknown` 降级；一次推荐请求内冻结环境快照 |
| 设备等级 | 按 RAM 划分，但 H5 浏览器常无法获得可靠 RAM | 大量 H5 用户被错误分层或无结果 | 保留 `unknown`；由容器注入或认证维表映射，不能通过指纹推断；未知不作为硬性不展示条件 |
| 游戏体验标签 | 资源、复杂度、时长主要靠人工枚举，缺少阈值和生效版本 | 标签主观、过期，无法解释推荐效果 | 游戏标签必须含 owner、来源、`tag_version`、`valid_from/to`；资源和时长优先用真实 P75/P90 数据校准 |
| RTP/波动性 | 只有高中低标签，没有映射区间、配置版本与有效期 | 规则无法复算，第三方 RTP 与实际配置可能不一致 | 保存理论 RTP 数值、来源、配置版本和生效时间；波动性给出供应商/统计口径，人工标签必须可审计 |
| 投注额度 | 用“通常单次投注”划分高中低 | 同一游戏可能同时支持低到高多个档位，容易误过滤 | 保存最小/默认/最大投注及币种，标签由配置版本生成；不使用模糊的“通常”作硬门禁 |
| 点击未玩 | 一律作为兴趣信号 | 点击后未玩可能源于加载失败、卡顿或不喜欢 | 拆分 `load_fail`、`bet_not_ready`、主动退出和未知；仅无体验异常的点击未玩可作为弱正向信号 |
| 兜底排序 | 最后按游戏 ID 从小到大 | 低 ID 游戏获得长期固定曝光，冷启动游戏没有公平探索 | 使用按 `user_id + policy_version + date` 的稳定哈希打散；保留小比例探索位并受安全门禁约束 |
| 换一批 | 只写读取下一批，缺少结果冻结与缓存规则 | 跨页面、跨端或重试后批次不一致 | 固定 `recommendation_list_id`、TTL、`batch_no/cursor`、`has_more`；同一列表不重复游戏，配置变化后生成新列表版本 |
| 埋点负载 | 每次曝光/点击重复上报完整用户标签、PR 和游戏标签 | 事件体积大、字段易漂移、泄露敏感分层 | 客户端只传快照/版本 ID 和必要原因码；完整用户画像与决策明细只保存在受控服务端事实层 |

## 3. 推荐规则的建议重构

### 3.1 四层决策

```text
第一层：合规与可用性硬门禁
  游戏上线状态、国家/渠道/币种、供应商健康、用户封禁/限制、自我排除、配置完整性

第二层：体验适配
  网络、设备、资源、连接、真实 game_ready/bet_ready 表现

第三层：个性化排序
  最近有效游玩、无故障点击未玩、子类/玩法/主题/大类偏好、付费价值适配

第四层：探索与兜底
  冷启动池、稳定随机、曝光均衡；不得突破第一层门禁
```

硬门禁与排序必须分开记录。网络、设备和体验数据原则上优先用于降权；只有已有明确不可用证据和审核规则时才硬过滤，避免静态标签造成误杀。

### 3.2 标签快照与版本

一次推荐请求使用一份冻结快照：

- `user_profile_snapshot_id`：用户阶段、付费价值、偏好、流失模型及生成时间。
- `game_tag_version`：游戏标签版本；每个游戏记录标签来源、负责人和有效期。
- `recommendation_policy_version`：过滤、排序、阈值和兜底规则版本。
- `game_catalog_version`：当时可用游戏目录与上下架状态。
- `environment_snapshot_id`：当前网络、设备、端和版本信息。

用户标签或环境在同一次请求过程中变化时，不重排已返回列表；下一次新请求生成新快照和列表。

## 4. 核心指标设计

### 4.1 指标目标层级

- **业务北极星：** 推荐曝光用户的有效实际游玩转化率。
- **战略结果：** 实验组相对对照组的付费用户 D7 留存提升。
- **过程指标：** 请求成功、曝光、点击、可下注、有效游玩、发现新游戏和重复游玩。
- **护栏：** 页面/游戏性能、错误率、支付/下注/结算、风险与投诉、游戏曝光集中度。

### 4.2 首屏十项核心指标

| # | metric_id | 指标 | 公式/口径 | 主要切分 |
|---:|---|---|---|---|
| 1 | `reco_request_success_rate` | 推荐请求成功率 | 成功且返回合法结果的请求 ÷ 服务端接受的有效请求 | 端、版本、页面、规则版本、网络 |
| 2 | `reco_module_view_rate` | For You 模块到达率 | 真实看到 For You 模块的用户 ÷ 进入游戏首页用户 | H5/APP、版本、渠道、设备 |
| 3 | `reco_item_ctr` | 推荐卡片点击率 | 被点击的去重 `impression_id` ÷ 合格卡片曝光数 | 游戏、位置、推荐原因、批次 |
| 4 | `reco_click_playable_rate` | 点击后可玩率 | 到达 `BET_READY`/原生等价状态的推荐点击 ÷ 推荐点击 | 游戏、供应商、设备、网络 |
| 5 | `reco_click_valid_play_rate` | 点击后有效游玩率 | 归因窗口内产生服务端有效局的推荐点击用户 ÷ 推荐点击用户 | 用户类型、游戏、推荐原因 |
| 6 | `reco_exposure_valid_play_rate` | 推荐有效游玩转化率（主指标） | 归因窗口内产生推荐游戏有效局的用户 ÷ For You 模块曝光用户 | 实验组、端、付费价值、设备 |
| 7 | `reco_new_game_discovery_rate` | 新游戏发现率 | 玩到近30天未有效游玩游戏的用户 ÷ 推荐有效游玩用户 | 游戏大类、用户偏好、端 |
| 8 | `reco_repeat_play_d7` | 推荐游戏7日复玩率 | D1–D7 再次有效游玩该推荐游戏的成熟用户 ÷ 首次通过推荐有效游玩用户 | 游戏、供应商、付费价值 |
| 9 | `reco_incremental_valid_play_lift` | 有效游玩增量 | 实验组主指标 − 对照组主指标；同时给相对提升和区间 | 实验、端、版本、cohort |
| 10 | `payer_retention_d7_lift` | 付费用户D7留存增量 | 实验组成熟付费用户D7留存 − 对照组 | 端、包体、渠道、付费层级 |

建议初始直接归因窗口为“点击后 30 分钟内、同一用户、同一游戏”，最终时长由业务和历史分布评审后配置。超出窗口的行为可记为辅助转化，不计直接点击转化。

### 4.3 诊断与护栏指标

**推荐服务质量**

- 空结果率、兜底率、平均候选数、平均返回数、缓存命中率、推荐接口 P50/P95/P99。
- 各过滤原因占比、用户画像缺失率、游戏标签缺失/过期率、PR/流失分值缺失率。
- 推荐列表重复率、同一用户换一批重复率、列表版本不一致率。

**排序与生态**

- Top 1/3/8 点击和游玩转化、位置偏差、推荐原因分布。
- 游戏/供应商/大类覆盖率、Top 10 游戏曝光占比、曝光集中度、冷启动游戏探索量。
- 个性化命中率、冷启动占比、点击未玩由性能失败导致的比例。

**体验与经营护栏**

- For You 页面 ready P75/P90、推荐接口超时、页面白/黑屏、无严重异常会话率。
- 推荐点击后的 `GAME_LOAD → GAME_READY → BET_READY → 首次下注 → 首局结算` 漏斗。
- 首充率、复充率、D1/D7 留存、有效下注额、结算成功率；收入与 RTP 仅作分层结果，不作为单独证明推荐有效的依据。
- 高流失用户、责任博彩受限用户、羊毛/欺诈风险用户的曝光与拦截情况；受限用户不得因运营优先级重新进入推荐池。

## 5. 实验与归因方案

### 5.1 实验设计

1. 以登录 `user_id` 进行稳定分流；匿名用户只用于体验漏斗，不进入付费和留存主结论。
2. H5、Android、iOS 分开实验和出结论，包体/版本/渠道不混入同一总分母。
3. 对照组保持当前首页及游戏排序；实验组开启 For You。H5 的 My Games、Recently Played 提升应单独灰度，避免与推荐算法效果混在一起。
4. 通过 `hash(user_id + experiment_id + allocation_version)` 稳定分组。比例根据样本量和最小可检测提升确定，不在 PRD 中凭经验写死。
5. 主分析采用 ITT；曝光、点击和实际游玩作为过程漏斗。D1/D7 只统计成熟 cohort，未成熟显示 `N/A`。
6. 修改过滤阈值、标签映射、排序权重、兜底或探索比例时，必须生成新的 `recommendation_policy_version` 和 `allocation_version`。

### 5.2 归因主键

推荐点击后应生成 `entry_context_id`，并把以下键带入游戏启动链路：

```text
recommendation_request_id
recommendation_list_id
impression_id
entry_context_id
user_id / session_id
game_id
experiment_id / group_id
recommendation_policy_version
```

H5 通过 `game_load_id` 关联 `H5_GAME_LOAD/GAME_READY/BET_READY`；游戏服务端通过 `entry_context_id` 或可信透传键关联有效局。第三方游戏无法透传时，可用 `user_id + game_id + 时间窗`做降级关联，但必须标记 `attribution_confidence=derived`，不能与直接关联混为同一质量等级。

## 6. 埋点与服务端事实设计

### 6.1 对现有埋点章节的审计

现有“推荐曝光、推荐点击、成功进入、有效实际游玩、换一批点击、换一批曝光”存在以下缺口：

- 没有推荐请求和服务端响应，无法判断无推荐、服务失败或客户端未展示。
- 没有算法、规则、游戏标签、用户画像和配置版本，历史结果无法复算。
- 没有空结果、兜底、过滤数量和过滤原因，无法诊断推荐池问题。
- “推荐曝光”的 50% 可见且持续 1 秒与现有 `MV` 的 1px 触发口径冲突，不能直接复用 `MV` 名称却使用不同语义。
- 客户端重复携带 PR 值和完整标签既冗余又敏感，应改为快照 ID 与有限原因码。
- “成功进入”只到可操作页面仍不足以证明可下注；H5 应至少到 `H5_BET_READY`。
- “有效实际游玩”必须来自服务端有效局，不新建客户端自报事实。

### 6.2 新增事件

| 事件 | 来源/触发时机 | 主键 | 核心专有字段 | 采集 |
|---|---|---|---|---|
| `RECO_REQUESTED` | 服务端接受一次推荐请求 | `recommendation_request_id` | 页面/坑位、所需数量、列表模式、环境快照、画像/策略/实验版本 | 100% |
| `RECO_LIST_GENERATED` | 服务端完成推荐决策或失败 | `recommendation_request_id` | `status`、候选/过滤/返回数、空/兜底类型、耗时、缓存、错误码、`recommendation_list_id` | 100% |
| `RECO_LIST_RENDERED` | 客户端成功渲染列表或渲染失败 | `render_id` | 列表 ID、实际卡片数、页面、批次、渲染状态/耗时/错误 | 100% |
| `RECO_MODULE_VIEWED` | For You 模块达到可见标准 | `module_view_id` | 页面、坑位、列表 ID、可见持续时长 | 100%去重 |
| `RECO_ITEM_IMPRESSION` | 卡片可见面积≥50%且持续≥1秒 | `impression_id` | 列表、批次、`algorithm_rank`、`display_position`、游戏、首要原因码、适配等级 | 100%去重 |
| `RECO_ITEM_CLICK` | 点击推荐卡片 | `click_id` | `impression_id`、游戏、位置、入口、`entry_context_id` | 100% |
| `RECO_BATCH_CHANGED` | 点击换一批并返回结果 | `batch_change_id` | 前后批次、列表 ID、cursor、`has_more`、结果/耗时 | H5 100% |
| `RECO_SHOW_ALL_CLICK` | 点击 Show all | `event_uid` | 来源页面、列表 ID、当前批次/位置 | H5 100% |
| `MY_GAMES_TAB_VIEWED` | My Games 中切换 For You/近期/收藏 | `event_uid` | tab、来源入口、页面访问 ID | H5 100% |
| `RECO_CONFIG_CHANGED` | 标签、阈值、规则、权重、开关或回滚生效 | `change_id` | 配置类型、前后版本、操作人、审批、范围、生效时间、回滚版本 | 服务端100% |

不另建客户端“有效实际游玩”事件。复用服务端 `GAMESTART`、有效局/结算事实；现有 `GAMEEND` 异常治理完成前，以认证的服务端结算事实为准。

### 6.3 复用并扩展现有事件

| 现有事件/事实 | 新增关联字段 |
|---|---|
| `H5_GAME_LOAD`、`H5_GAME_READY`、`H5_BET_READY` | `entry_context_id`、`recommendation_request_id`、`impression_id`、`entry_source=for_you` |
| APP 游戏进入/可玩状态 | 同上，并补原生页面/模块、加载结果和耗时 |
| `GAMESTART`、服务端有效局/结算 | `entry_context_id`、`recommendation_request_id`、`experiment_id/group_id`；无法直传时输出关联置信度 |
| `ORDER`、支付事实 | 实验上下文仅用于总体效果归因；不得把推荐点击直接当成支付因果 |
| `PV/MV/MC` | 保留通用页面分析；For You 合格曝光和点击使用专用事件，避免口径冲突 |

### 6.4 通用字段契约

所有新增事件继承项目统一事件信封：

```text
event_name / event_version / event_uid / ingest_id
event_time_client / event_time_server / received_at
user_id / uuid / session_id / trace_id
platform / surface_type / app_version / web_version / release_id
package_name / channel / sub_channel / country
is_retry / retry_count / sample_rate / sample_weight
```

推荐专有字段：

```text
recommendation_request_id / recommendation_list_id / entry_context_id
algorithm_version / recommendation_policy_version / allocation_version
experiment_id / group_id
user_profile_snapshot_id / environment_snapshot_id
game_tag_version / game_catalog_version
source_page / placement_id / list_mode / batch_no / cursor
game_id / provider_id / algorithm_rank / display_position
reason_code / match_level / experience_fit_level
status / fallback_type / filter_reason / cache_hit / latency_ms
```

客户端事件不传完整用户标签、历史充值金额、完整 PR 数值或全量候选决策。此类数据只保留在受控服务端快照和事实表中，普通看板默认聚合展示。

### 6.5 原因码建议

**推荐原因 `reason_code`**

`clicked_same_game`、`clicked_same_subcategory`、`recent_same_game`、`recent_same_subcategory`、`recent_same_gameplay`、`recent_same_theme`、`preference_subcategory`、`preference_gameplay`、`preference_theme`、`preference_category`、`environment_fit`、`cold_start`、`fallback`、`exploration`。

**过滤原因 `filter_reason`**

`game_offline`、`provider_unavailable`、`country_or_channel_restricted`、`user_restricted`、`responsible_gaming_restricted`、`currency_or_asset_incompatible`、`config_missing`、`device_not_supported`、`network_not_supported`、`bet_tier_conflict`、`churn_policy_conflict`、`risk_policy_conflict`。

一个候选可有多个内部原因，但客户端只记录首要原因码；完整原因集合保存在服务端决策事实中。

## 7. 推荐数据模型

| 表/数据集 | 粒度 | 主键 | 用途 |
|---|---|---|---|
| `dim_reco_policy_version` | 一版推荐策略 | `recommendation_policy_version` | 过滤、排序、阈值、探索和生效范围 |
| `dim_game_reco_tag_version` | 游戏—标签版本 | `game_id + game_tag_version` | 标签值、来源、owner、有效期和审核 |
| `fact_user_reco_profile_snapshot` | 用户一次画像快照 | `user_profile_snapshot_id` | 用户阶段、偏好、付费价值、分值版本和新鲜度 |
| `fact_reco_request` | 一次推荐请求 | `recommendation_request_id` | 请求、响应、候选数、过滤数、兜底、耗时和错误 |
| `fact_reco_item_served` | 一次请求返回的一款游戏 | `recommendation_request_id + game_id` | 排名、推荐原因、适配层级和版本 |
| `fact_reco_candidate_diagnostic` | 候选游戏决策样本 | 请求+游戏 | 过滤原因和分数组件；空结果/错误请求全量，其余确定性抽样 |
| `fact_reco_interaction` | 一次曝光/点击/换批交互 | 对应事件主键 | 页面行为漏斗 |
| `fact_reco_outcome_daily` | 用户—请求/实验—日期 | 复合键 | 有效游玩、付费、留存、风险和实验结果 |

高频被过滤候选不建议永久全量保存。空结果、服务错误、P0/P1 风险场景全量保存；普通请求按稳定键抽样，`fact_reco_request` 保留完整过滤数量与原因分布。

## 8. 看板规划

### 8.1 六层结构

1. **数据可用性：** 请求、响应、曝光、点击、游戏链路的接收/入库/关联率、延迟、缺失和版本覆盖。
2. **推荐服务：** 成功率、空结果、兜底、候选量、接口耗时、缓存和错误原因。
3. **推荐漏斗：** 首页→模块曝光→卡片曝光→点击→可玩→有效局→复玩。
4. **算法质量：** 推荐原因、过滤原因、标签命中、位置转化、覆盖、多样性、集中度和探索表现。
5. **经营结果：** 新游戏发现、D1/D7、付费用户留存、首充/复充及实验增量。
6. **体验与风险：** 页面/游戏性能、失败阶段、受限用户拦截、责任博彩/欺诈风险、投诉和异常。

### 8.2 全局筛选

日期/小时、实验/组别、H5/PWA/APP、包体、应用/Web版本、渠道/媒体、页面/坑位、推荐策略版本、游戏/供应商/大类、用户阶段、付费价值、设备/网络、推荐原因、适配等级、数据质量状态。

敏感风险与付费分层只向授权角色开放；普通产品看板使用聚合标签，不提供用户级导出。

## 9. 数据质量与验收

### 9.1 上线阻断项

- 需求升为 L3，产品、服务端、H5、Android、iOS、数据开发、QA、风控/合规和发布负责人明确。
- `recommendation_request_id → recommendation_list_id → impression_id → click_id → entry_context_id → game_load_id/round_id` 可追踪。
- 核心事件入库率 ≥99.5%，必填字段缺失率 ≤0.1%，重复率和 P95 入库延迟可监控。
- 推荐请求、返回游戏和实际展示数量可对账；空结果、兜底、错误、缓存和版本状态不显示为 0 或 `-`。
- 所有上线游戏的标签有版本、来源、owner 和有效期；RTP/波动/投注/资源映射无缺失配置。
- 责任博彩限制、封禁、国家/渠道、供应商不可用等硬门禁测试 100% 通过，运营优先级不能绕过。
- H5 推荐链路与 `GAME_LOAD/GAME_READY/BET_READY` 关联；APP 提供等价可玩状态；有效游玩以服务端事实认证。
- 实验稳定分流、对照组、配置版本、D1/D7 成熟状态和回滚/关闭开关通过验收。

### 9.2 必测场景

- 新用户、未激活、未付费、首充、复充大/中/小客户、种子潜力、回流及无偏好用户。
- PR/流失分值缺失、用户画像过期、游戏标签缺失、服务超时、空结果、候选不足和配置回滚。
- 正常/高延迟、低端/普通/高端/未知设备、断网重连、网络切换及 H5/PWA/APP WebView。
- Show all、换一批到末页、列表重试、跨页返回、My Games 标签切换、Recently Played 和收藏为空。
- 游戏下线、供应商故障、用户封禁/受限、自我排除、币种不兼容及运营优先级冲突。
- 点击后加载失败、游戏 ready 但不可下注、下注失败、结算失败、第三方游戏无法透传关联键。

## 10. 与策划沟通的确认清单

### P0：评审前必须确认

1. 是否同意按现行规范将需求从 L2 升为 L3，并补充风控/合规、RTP、配置审计、灰度和回滚负责人？
2. 北极星指标是否采用“推荐曝光用户有效实际游玩率”，战略指标是否采用“付费用户 D7 留存增量”？
3. 对照组保持什么页面和排序；H5 的 My Games、Recently Played 提升是否与 For You 拆开实验？
4. “有效实际游玩”的服务端口径、允许资产、异常局、机器人和第三方游戏如何处理？
5. PR 到底是留存概率还是流失概率，取值范围、阈值、模型版本和更新频率是什么？
6. 流失风险、责任博彩风险、羊毛/欺诈风险是否已拆成不同标签和权限？
7. 高延迟的阈值、测量窗口和网络未知值如何处理？H5 无法取得 RAM 时是否允许继续推荐？
8. 资源、复杂度、单局时长、投注额度、理论 RTP 和波动性的具体映射口径、数据源、owner 与有效版本是什么？
9. 点击未玩在加载失败、主动退出和正常浏览三种情况下分别如何计入偏好？
10. 游戏 ID 顺序兜底是否改为稳定打散并增加受控探索位？
11. 推荐列表何时重新计算，TTL、多页/换批、去重、缓存、配置变化和跨端一致性如何定义？
12. 受限用户、封禁、自我排除、国家/渠道、币种/资产和供应商故障是否加入最高优先级硬门禁？
13. 是否接受客户端不上传完整 PR 和全量用户标签，只上传快照 ID、策略版本和有限原因码？
14. 第三方游戏能否接收并回传 `entry_context_id/game_load_id`；不能时允许何种降级归因？
15. 实验样本量、灰度范围、发布观察期、回滚阈值和最终签字人分别是谁？

## 11. 数据侧评审意见（可直接反馈策划）

> 数据侧认可通过“设备/网络适配 + 用户偏好”提升游戏发现和有效游玩的产品方向，但当前版本仍缺少可复算的标签口径、推荐决策版本、实验对照、服务失败链路和服务端有效游玩事实。由于需求使用 RTP、波动性、付费价值和流失分值自动决定真金游戏曝光，建议按 L3 需求评审。完成 P0 口径确认、事件契约、配置审计、实验和回滚方案后，再进入开发排期；数据侧将据此建设推荐服务、曝光点击、游戏可玩、有效局、付费留存和风险护栏的完整观测闭环。

## 12. 建议实施顺序

| 阶段 | 交付 | 验收结果 |
|---|---|---|
| P0A | L3 分级、规则/标签口径、责任与权限 | 规则可计算、可审批、可回滚 |
| P0B | 推荐请求/决策事实、策略与快照版本 | 任一推荐结果可解释和复算 |
| P0C | 客户端曝光点击、H5/APP游戏进入、服务端有效局关联 | 完整推荐转化漏斗可用 |
| P0D | 稳定实验分流、首屏看板、数据质量和告警 | 能判断增量效果和异常原因 |
| P1 | My Games/Recently Played 独立实验、探索策略、标签自动校准 | 持续优化且不污染首期因果结论 |

