# X7 HOT 长期排名与高表现原因分析｜Waje 侧数据入口审计

## Executive Summary

**当前还不能回答“X7 HOT 为什么长期排名第一”。** 本轮 Waje 侧核查没有取得 X7 HOT 的可识别游戏 ID、历史 Top Game 展示位置、曝光/点击、收藏/复玩或单游戏结算事实；BigQuery `wajenigeria` 元数据访问返回 `Auth required`。

**现有数据可以证明 Waje 的游戏经营数据存在，但不能证明 X7 HOT 的单游戏表现。** 2026 年 8 月生命周期游戏汇总有 31 个游戏粒度行、完全下注额约 74,166,138,180.39、加权实际 RTP 96.62%；其中 `Tada` 下注额约 36,811,311,576.00、占比 49.63%，但这是 TaDa 厂商级聚合，不是 X7 HOT。

**现有 H5 Top Game 数据也不能替代推荐数据。** GA4 仅覆盖 5 个自研轻量化游戏 ID的页面访问和回访行为，没有 X7 HOT、Top Game 曝光/点击、收藏事件，也没有 App 对照。

**本次已完成数据入口、可用背景和补数合同；正式原因分析需要补齐 X7 HOT 映射和认证聚合事实。** 在这些事实到位前，不能把“用户收藏复玩”“推荐算法”“游戏 RTP/GGR”中的任何一个写成已验证原因。

## 1. 当前可用背景：规模数据存在，但 X7 HOT 不在可识别粒度

| 数据源 | 时间窗口 | 当前粒度 | 可见结果 | 对 X7 HOT 的支持 |
|---|---|---|---|---|
| Lifecycle V2 Joint 游戏汇总 | 2026-08-01—08-31 | 游戏×生命周期月度聚合 | 31 个游戏行；总完全下注额 74,166,138,180.39；实际 RTP 96.62% | 不支持；TaDa 为厂商级 `Tada` |
| 游戏 RTP 14 日快照 | 2026-08-19—09-01 | 游戏两窗口聚合 | 31 个游戏行；没有 X7 HOT | 不支持；缺端、包体、入口和排名 |
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
