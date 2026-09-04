---
type: tracking-development-requirement
domain: for-you-recommendation
status: ares_created_lark_delivered_binding_partial
updated: 2026-08-31
owner: Robin
scope: [h5, android, ios, for-you, ares, tracking]
source_prd_revision: 6
tags: [ForYou, 推荐, 埋点, Ares, H5, Android, iOS, 研发交付]
---

# For You 推荐模块｜APP/H5 标准埋点开发需求

> 本文是研发实施版。依据 For You 策划文档 revision 6、页面/模块埋点标准 Sheet、本地 H5/Ares 埋点盘点和 Waje Special 起源平台实测结果整理。

## 1. 交付结论

### 1.1 Ares 已创建对象

| 对象 | 实际 ID | 端/页面 | 事件 | 状态 |
|---|---|---|---|---|
| H5-首页 For You 推荐模块 | `wxkp9lm776` | H5 / `n9pixal64m` | `wxkp9lm776_mv`、`wxkp9lm776_mc` | `created_successfully` |
| APP大厅 For You 推荐模块 | `eittdmb81f` | Android、iOS / `ppqy3z3xv9` | `eittdmb81f_mv`、`eittdmb81f_mc` | `created_successfully` |

本轮没有创建独立 For You 页面，也没有重复创建 `PV/PD/MV/MC` 元事件。

### 1.2 字段处理结果

| 结果 | 数量 | 处理方式 |
|---|---:|---|
| 已有/重复配置 | 11 | 按已有字段复用；不覆盖、不改类型。 |
| 新创建成功 | 4 | `open_status`、`load_duration_ms`、`error_code`、`fallback_type`。 |
| 模块参数绑定 | 待补证 | Ares 自定义参数选择列表当前返回“暂无数据”，不能证明字段不存在或已绑定。 |

## 2. 产品范围与埋点边界

### 2.1 覆盖链路

```text
推荐请求
  → 推荐列表生成
  → 列表渲染
  → 模块/卡片曝光
  → 卡片点击 / Show all / 换一批 / 重试
  → 游戏打开
  → GAMESTART
  → GAMEEND / BETREWARD / ASSET
```

推荐结果、排序、去重和兜底由服务端决定；APP/H5 客户端只按返回顺序展示，不自行重排。

### 2.2 不在本次 Ares 创建范围

- 不创建新的 `PV`、`PD`、`MV`、`MC` 元事件。
- 不创建独立 For You 占位页面；当前使用已有首页页面。
- 不把 `RECO_REQUESTED`、`RECO_LIST_GENERATED` 等服务端事实创建成客户端模块事件。
- 不新增客户端“有效实际游玩”事实；有效局、结算和资产以服务端事件为准。
- 不上传完整用户画像、风险分值、请求正文、完整 URL 查询串或支付明细。

## 3. 页面埋点方案

### 3.1 H5 首页

| 字段 | 内容 |
|---|---|
| 页面名称 | `h5-首页` |
| 页面 ID | `n9pixal64m` |
| 平台 | H5 |
| PV | `n9pixal64m_pv`，进入首页时上报；历史登记/页面已见，功能详情 ID仍按页面详情核验。 |
| PD | `n9pixal64m_pd`，离开首页时上报；`event_duration` 为页面停留秒数。 |
| For You 位置 | 首页内模块，不另建页面。 |

PV 行不携带业务参数，参数列在飞书 Sheet 中统一填为“无”；只有 PD 行需要上报 `event_duration`。

### 3.2 APP 大厅页

| 字段 | 内容 |
|---|---|
| 页面名称 | `APP大厅页` |
| 页面 ID | `ppqy3z3xv9` |
| 平台 | Android、iOS |
| PV | `ppqy3z3xv9_pv`，进入 APP 大厅时上报；功能详情 ID待页面详情回读。 |
| PD | `ppqy3z3xv9_pd`，离开 APP 大厅时上报；`event_duration` 为页面停留秒数。 |
| For You 位置 | APP 大厅内模块，不另建页面。 |

PV 行不携带业务参数，参数列在飞书 Sheet 中统一填为“无”；只有 PD 行需要上报 `event_duration`。

## 4. Ares 模块埋点方案

### 4.1 H5 For You 模块

| 项目 | 配置 |
|---|---|
| 模块名称 | `H5-首页-For You推荐模块` |
| 模块 ID | `wxkp9lm776` |
| 关联页面 | `n9pixal64m / h5-首页` |
| 端类型 | H5 |
| 模块事件 | `MV + MC` |
| 曝光类型 | 多值曝光 |
| MV 触发 | For You 模块/推荐卡片进入可视区域时上报；客户端记录 `visible_ms`。 |
| MC 触发 | 点击推荐卡片、Show all、换一批或重试时上报；通过 `click_action` 区分。 |
| 功能埋点 ID | `wxkp9lm776_mv`、`wxkp9lm776_mc` |

### 4.2 APP For You 模块

| 项目 | 配置 |
|---|---|
| 模块名称 | `APP大厅-For You推荐模块` |
| 模块 ID | `eittdmb81f` |
| 关联页面 | `ppqy3z3xv9 / APP大厅页` |
| 端类型 | Android、iOS |
| 模块事件 | `MV + MC` |
| 曝光类型 | 多值曝光 |
| MV 触发 | For You 模块/推荐卡片进入可视区域时上报；客户端记录 `visible_ms`。 |
| MC 触发 | 点击推荐卡片、Show all、换一批或重试时上报；通过 `click_action` 区分。 |
| 功能埋点 ID | `eittdmb81f_mv`、`eittdmb81f_mc` |

### 4.3 Ares 端实现规则

| 端 | 实现方式 | 注意事项 |
|---|---|---|
| H5 | 使用手动 PV/PD/MV/MC | 不依赖 `AUTOPV/AUTOMC/AUTOPD/PAGELOAD`；历史自动 Web 事件量不足。 |
| Android | 使用既有 Ares SDK 模块曝光/点击调用 | 透传推荐关联键和版本字段；不自行排序。 |
| iOS | 使用与 Android 同构的 Ares 事件契约 | 本轮模块已创建；实际客户端调用和数据接收仍需发布后验收。 |

## 5. 字段定义

### 5.1 优先复用字段

| 字段 | 类型 | 业务用途 | 备注 |
|---|---|---|---|
| `element_id` | String | 游戏卡片或动作元素标识 | 复用 MC 全局属性；卡片建议使用 `game_id`。 |
| `element_name` | String | 卡片、Show all、换一批、重试名称 | 复用 MC 全局属性。 |
| `element_content` | String | 展示内容或标准化推荐原因 | 禁止上传完整用户画像。 |
| `element_offset` | Integer | 推荐展示位置，从 0 开始 | 作为 `recommend_position` 的兼容映射。 |
| `play_id` | Integer | 游戏/玩法标识 | 仅在现有玩法口径适用时上报。 |
| `ab_trial_id` | Integer | 实验 ID | 与现有实验配置保持一致。 |
| `ab_layer_id` | Integer | 实验层 ID | 与现有实验配置保持一致。 |
| `ab_group_id` | Integer | 实验组 ID | 与现有实验配置保持一致。 |
| `game_type` | String | 游戏分类 | 复用现有公共字段；无值不填。 |
| `app_key` | String | 联运/供应商游戏标识 | 需要供应商维度时使用。 |

### 5.2 For You 专用字段

| 字段 | 类型 | 必填 | 取值/算法 | Ares 状态 |
|---|---|---:|---|---|
| `recommendation_request_id` | String | 是 | 一次推荐请求唯一键 | `duplicate_or_existing`；模块绑定待补证 |
| `recommendation_list_id` | String | 是 | 一批推荐结果唯一键 | `duplicate_or_existing`；模块绑定待补证 |
| `entry_context_id` | String | 条件 | 点击到游戏打开/开局的关联键 | `duplicate_or_existing`；模块绑定待补证 |
| `game_id` | String | 条件 | 推荐游戏唯一标识 | `duplicate_or_existing`；模块绑定待补证 |
| `recommend_reason` | String | 条件 | 服务端标准化推荐命中原因 | `duplicate_or_existing`；模块绑定待补证 |
| `algorithm_version` | String | 是 | 生成推荐结果的算法版本 | `duplicate_or_existing`；模块绑定待补证 |
| `strategy_version` | String | 是 | 端/付费/设备/网络策略版本 | `duplicate_or_existing`；模块绑定待补证 |
| `render_status` | String | 条件 | `success/empty/error` | `duplicate_or_existing`；模块绑定待补证 |
| `render_duration_ms` | Integer | 条件 | 收到列表到完成渲染的耗时，毫秒 | `duplicate_or_existing`；模块绑定待补证 |
| `click_action` | String | MC 条件 | `game_card/show_all/change_batch/retry` | `duplicate_or_existing`；模块绑定待补证 |
| `visible_ms` | Integer | MV 条件 | 有效可见时长，毫秒 | `duplicate_or_existing`；模块绑定待补证 |
| `open_status` | String | 条件 | `success/fail/timeout` | `created_successfully`；模块绑定待补证 |
| `load_duration_ms` | Integer | 条件 | 点击到游戏打开完成的耗时，毫秒 | `created_successfully`；模块绑定待补证 |
| `error_code` | String | 条件 | 请求/渲染/打开阶段标准化错误码 | `created_successfully`；模块绑定待补证 |
| `fallback_type` | String | 条件 | `none/position/overall` | `created_successfully`；服务端事实优先 |

### 5.3 字段上报规则

- 未知、不可测字段留空，不用 `0` 伪造正常值。
- ID 字段统一 String；耗时、位置和数量使用 Integer。
- `recommend_position` 不新建字段，使用 `element_offset`。
- 客户端只传必要快照和版本 ID；完整画像、候选明细和过滤原因保存在服务端受控事实层。
- `open_status`、`load_duration_ms`、`error_code` 可由客户端/桥接上报，但不能替代服务端游戏事实。

## 6. 服务端推荐事件契约

以下事件由推荐服务和数据开发实现，不在 Ares 重复创建：

```text
RECO_REQUESTED
RECO_LIST_GENERATED
RECO_LIST_RENDERED
RECO_ITEM_IMPRESSION
RECO_ITEM_CLICK
RECO_GAME_OPEN
RECO_BATCH_CHANGED
RECO_SHOW_ALL_CLICK
RECO_FALLBACK
RECO_CONFIG_CHANGED
```

### 6.1 必须统一的关联键

```text
recommendation_request_id
recommendation_list_id
impression_id
click_id
entry_context_id
session_id
game_id
experiment_id
algorithm_version
strategy_version
config_version
```

### 6.2 服务端关键字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `request_type` | String | 是 | `initial/change_batch/retry` |
| `response_status` | String | 是 | `success/empty/error` |
| `candidate_count` | Integer | 是 | 进入过滤前候选数 |
| `filtered_count` | Integer | 是 | 被过滤结果数 |
| `returned_count` | Integer | 是 | 实际返回数 |
| `fallback_type` | String | 是 | `none/position/overall` |
| `fallback_reason` | String | 条件 | `no_match/error/insufficient_pool` |
| `response_latency_ms` | Integer | 是 | 服务端响应耗时 |
| `cache_hit` | Boolean | 条件 | 是否命中推荐缓存 |
| `recommendation_policy_version` | String | 是 | 规则和排序策略版本 |
| `game_tag_version` | String | 是 | 游戏标签版本 |
| `user_profile_snapshot_id` | String | 条件 | 用户画像快照引用，不传画像明细 |

## 7. 核心指标与算法

| 指标名称 | 指标编码 | 定义与算法 | 分母/成熟规则 |
|---|---|---|---|
| 推荐请求成功率 | `reco_request_success_rate` | `response_status=success` 的请求数 / 有效请求数 | 按端、版本、策略版本拆分。 |
| 推荐空结果率 | `reco_empty_rate` | `response_status=empty` 的请求数 / 成功请求数 | 记录空结果原因。 |
| For You 模块到达率 | `reco_module_view_rate` | 有效 For You 模块曝光用户 / 首页进入用户 | H5、Android、iOS 分开。 |
| 推荐卡片曝光数 | `reco_item_impression_count` | 有效曝光 `impression_id` 去重计数 | 曝光规则需明确；多值曝光不重复计数。 |
| 推荐卡片点击率 | `reco_item_ctr` | 去重点击数 / 合格卡片曝光数 | 按游戏、位置、推荐原因拆分。 |
| 点击后可玩率 | `reco_click_playable_rate` | 达到 `BET_READY` 或 APP 等价状态的点击数 / 点击数 | 不以页面打开成功替代。 |
| 点击有效游玩率 | `reco_click_valid_play_rate` | 归因窗口内产生服务端有效局的点击用户 / 点击用户 | 默认点击后 30 分钟、同用户同游戏。 |
| 新游戏发现率 | `reco_new_game_discovery_rate` | 玩到近 30 天未玩游戏的用户 / 推荐有效游玩用户 | 以服务端有效游玩为准。 |
| 推荐游戏 D1/D3/D7 复玩率 | `reco_replay_d1/d3/d7` | `cohort_date+N` 再次有效开局用户 / 首次推荐有效游玩用户 | N=1/3/7；未成熟为 `N/A`。 |
| 推荐后真金回流率 | `reco_real_game_return_rate` | 推荐 cohort 后进入真金游戏用户 / 推荐 cohort 用户 | 不把推荐行为计入真金游戏分母。 |
| 兜底率 | `reco_fallback_rate` | 触发兜底的请求或结果项 / 请求或结果项总数 | 区分 position/overall。 |
| 同批无重复率 | `reco_no_duplicate_rate` | 无重复 `game_id` 批次 / 批次总数 | 目标 100%。 |
| 推荐接口 P50/P95 | `reco_latency_p50/p95` | 服务端响应耗时的分位数 | 端、网络、版本拆分。 |
| 列表渲染失败率 | `reco_render_error_rate` | `render_status=error` 列表 / 客户端收到列表 | 区分空结果与渲染失败。 |

## 8. 埋点上报示例

### 8.1 H5/APP 推荐卡片点击

```json
{
  "event_name": "wxkp9lm776_mc 或 eittdmb81f_mc",
  "platform": "h5 | android | ios",
  "page_id": "n9pixal64m | ppqy3z3xv9",
  "module_id": "wxkp9lm776 | eittdmb81f",
  "recommendation_request_id": "<request-id>",
  "recommendation_list_id": "<list-id>",
  "entry_context_id": "<entry-context-id>",
  "game_id": "<game-id>",
  "element_offset": 0,
  "click_action": "game_card",
  "algorithm_version": "<algorithm-version>",
  "strategy_version": "<strategy-version>"
}
```

### 8.2 推荐游戏进入后关联游戏事实

```text
FOR_YOU_CLICK
  → entry_context_id
  → GAMESTART
  → GAMEEND
  → BETREWARD / ASSET
```

无法透传关联键的第三方游戏允许用 `user_id + game_id + 时间窗`降级关联，但必须标记 `attribution_confidence=derived`。

## 9. 研发验收

### 9.1 Ares 配置验收

- [ ] 当前产品为 Waje Special。
- [ ] H5 模块 ID 为 `wxkp9lm776`，页面为 `n9pixal64m`，端类型为 H5。
- [ ] APP 模块 ID 为 `eittdmb81f`，页面为 `ppqy3z3xv9`，端类型为 Android/iOS。
- [ ] 四个功能埋点 ID分别为 `wxkp9lm776_mv`、`wxkp9lm776_mc`、`eittdmb81f_mv`、`eittdmb81f_mc`。
- [ ] 两个模块均配置 MV + MC，曝光类型为多值曝光。
- [ ] 既有页面 PV/PD 和元事件未被修改。
- [ ] 参数绑定列表恢复后，按字段名和类型逐项回读并补齐绑定状态。

### 9.2 客户端/服务端链路验收

- [ ] 首次加载、正常返回、空结果、接口错误、渲染错误均可区分。
- [ ] 卡片曝光、Show all、换一批、重试、卡片点击均可区分。
- [ ] 同批次 `game_id` 不重复，展示位置从 0 开始。
- [ ] H5、Android、iOS 不混用页面或模块 ID。
- [ ] 推荐点击可关联 `GAMESTART`；推荐游戏结算以服务端事实为准。
- [ ] 服务端记录候选数、过滤数、返回数、兜底类型和策略版本。
- [ ] 机器人不进入用户复玩、留存和付费分母。

### 9.3 数据质量门禁

| 检查项 | 建议标准 |
|---|---|
| 核心事件入库率 | ≥99.5% |
| 必填字段缺失率 | ≤0.1% |
| 重复事件率 | ≤0.1% |
| 请求→列表→曝光关联率 | ≥98% |
| 点击→可玩→有效局关联率 | ≥98% |
| 同批无重复率 | 100% |
| D1/D3/D7 未成熟 cohort | 显示 `N/A`，不得显示 0 |
| 版本/端/包体 | 必须可拆分 |

## 10. 实际回执与未关闭项

### 10.1 已完成

- Ares Waje Special H5 For You 模块已创建：`wxkp9lm776`。
- Ares Waje Special APP For You 模块已创建：`eittdmb81f`。
- 两模块均已配置 MV + MC 和多值曝光。
- 四个新增字段已创建成功或按平台重复配置复用。
- 飞书标准工作簿已创建并完成 5 个 Sheet 写入、样式处理和回读验证。

### 10.2 待补证/待研发

- Ares 自定义参数选择列表当前返回“暂无数据”，新增字段是否已绑定到模块事件需平台恢复后回读。
- 页面 PV/PD 的功能详情 ID仍沿用历史登记，未在页面编辑详情中逐项回读。
- Ares 模块页面未上传示意图；平台提示已选择“下次添加”，不影响当前埋点 ID创建。
- 服务端推荐事件、推荐策略版本、列表事实和 `GAMESTART` 关联需要研发实现。
- 发布后需使用埋点测试、数据质量和 BQ/Ares 聚合完成实际接收验证。

## 11. 飞书与本地资产

- [For You推荐模块APP-H5标准埋点需求飞书工作簿](https://ksg964l11fam.sg.larksuite.com/wiki/JjFUwxasiiKqEVkDRyZlrnclgfd)
- [For You 策划/指标与埋点原文](https://ksg964l11fam.sg.larksuite.com/wiki/QOl7wpeUMipmrBkIO8nlAet7gcf?from=from_copylink)
- [页面埋点方式标准工作簿](https://ksg964l11fam.sg.larksuite.com/wiki/OdIUweqY0ivlDhk7Xj6ljXvhgGc?fromScene=spaceOverview&sheet=UfeS8F)
- [模块埋点方案标准工作簿](https://ksg964l11fam.sg.larksuite.com/wiki/JoHBwnONVi15DxkbVZ2lBVWDgse?from=from_copylink&sheet=Cb1KyM)
- [Ares H5 埋点全量盘点](./Waje-H5起源埋点上报全量盘点-2026-08-28.md)
- [本次创建与发布回执](../../analysis/for_you_tracking_delivery_2026_08_31/README.md)
