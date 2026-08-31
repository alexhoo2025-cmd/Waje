---
title: Metabase GM 生命周期 V2（Joint）报表开发文档
date: 2026-08-26
type: metabase-development-spec
status: draft-for-data-development
source_status: observed_metadata_and_project_dictionary
owner: data-product
---

# Metabase GM 生命周期 V2（Joint）报表开发文档

> 面向数据开发、Metabase 配置和业务验收。首期主口径为 GM Lifecycle Pool V2（Joint）；V1 只做独立历史对照，不与 V2 直接合并。

## 1. 目标与边界

在 Metabase 建立一个只读生命周期分析主题，统一 Model/View、指标字典、筛选器和质量校验，提供 5 张报表：

1. 原始数据总数；
2. 原始详细奖池；
3. 生命周期奖池分游戏汇总；
4. 原始数据活跃周期-回报；
5. 原始数据活跃周期-付费。

| 系统 | 职责 |
|---|---|
| GM Lifecycle Pool V2（Joint） | 实时排障、生命周期配置、盈利调整和后台修改 |
| Metabase | 聚合 Model、只读问题、看板、筛选、导出和对账 |
| 数据开发层 | 同步快照、建立授权 Model/View、关联维度和质量任务 |
| V1 来源 | 独立历史对照，不进入 V2 查询 |

GM 的修改、盈利调整和扣除能力不迁移到 Metabase。

## 2. 数据源与授权 Model/View

### 2.1 当前 Metabase 真实表

已在 `whot_center` Schema 的元数据中观察到：

```text
whot_center.stat_lifecycle_pool_v2_log
whot_center.stat_lifecycle_pool_log_v2
whot_center.stat_lifecycle_pool_log
whot_center.stat_lifecyclev2_rtp_record
```

V2 主表字段：

```text
id, game_type, lifecycle, data_type, pool_type,
change_type, data, data0, data1, data2, data3, data4,
time, remark
```

说明：

- `stat_lifecycle_pool_v2_log`：每日历史快照主表；
- `stat_lifecyclev2_rtp_record`：15 分钟 RTP 辅助趋势，不用于还原每日历史报表；
- `stat_lifecycle_pool_log`：旧版生命周期候选来源；
- 当前元数据只证明字段存在，不证明实际数据、新鲜度和业务口径已认证。

当前主表没有软件版本、包体、分包渠道、归因媒体和归因渠道字段，不能直接在原始表上伪造这些筛选。

### 2.2 目标 Model

```text
model_lifecycle_v2_joint_daily
```

保存位置：

```text
Waje / Lifecycle / V2 Joint / Models
```

目标粒度：

```text
business_date + data_scope + population_type + display_lifecycle
+ game_id + app_version + package_id + distribution_channel_id
+ attribution_media_id + attribution_channel_id + data_status
```

数据开发必须提供版本、包体、渠道和归因维度的历史授权 Model/View。无法还原历史维度时返回 `unknown` 或 `not_available`，不得使用当前用户属性反推历史值。

### 2.3 Model 字段

业务维度：

```text
business_date, data_scope, population_type, display_lifecycle,
game_id, game_name, game_type, provider, is_joint, is_self_developed,
app_version, package_id, distribution_channel_id,
attribution_media_id, attribution_channel_id, data_status,
snapshot_time, data_cutoff_at, metric_version
```

原始累计值：

```text
real_profit, expected_profit, adjusted_profit, entire_bet,
bankruptcy_bet, bankruptcy_profit, control_bet, control_profit,
expected_rtp_raw, real_reserved, expected_reserved
```

经营值：

```text
user_count, recharge_count, recharge_amount,
repeat_recharge_count, repeat_recharge_amount,
withdraw_count, withdraw_amount, controlled_user_count,
controlled_count, absolute_bankrupt_user_count,
absolute_bankrupt_count, retention_user_count, upgrade_user_count
```

留存值：

```text
cohort_date, retention_day, cohort_user_count,
retention_user_count, upgrade_user_count,
cumulative_upgrade_user_count
```

派生值：

```text
actual_profit, base_bet, base_actual_profit, base_expected_profit,
entire_expected_profit, base_actual_rtp, detail_page_base_actual_rtp,
summary_base_actual_rtp, entire_actual_rtp, base_expected_rtp,
entire_expected_rtp, base_rtp_gap, entire_rtp_gap, entire_bet_share,
bankruptcy_protection_to_bet, user_profit_control_to_bet,
avg_actual_profit_per_user, tc_ratio, flow_recharge_ratio,
loss_coefficient, avg_bankruptcy_count
```

Model 内部可保留受控的 `lifecycle_user_key` 作为查询期去重键，但必须设置为隐藏字段，不得作为维度、表格列、导出列或下钻结果返回。若安全策略不允许 Model 持有该键，数据开发必须提供已经按查询期去重的聚合接口，不能把每日人数直接相加。

TC 比、流充比、折损系数必须由 Model 同时提供原始分子和分母；不能只依赖字段名称猜公式。

建议隐藏保存以下分子/分母字段，供查询期重算比例使用：

```text
profit_ratio_numerator, profit_ratio_denominator,
flow_recharge_numerator, flow_recharge_denominator,
tc_numerator, tc_denominator,
loss_numerator, loss_denominator
```

## 3. 统一筛选器

| 筛选器 | Metabase 控件 | 默认值 | 绑定字段 | 适用报表 |
|---|---|---|---|---|
| 开始日期 | Date filter | 最近 7 个完整日首日 | `business_date` | 全部 |
| 结束日期 | Date filter | 最近完整自然日 | `business_date` | 全部 |
| 数据范围 | Dropdown | `joint` | `data_scope` | 全部 |
| 用户范围 | Dropdown | `all` | `population_type` | 全部 |
| 软件版本 | 多选 | 全部 | `app_version` | 全部 |
| 包体 | 多选 | 全部 | `package_id` | 全部 |
| 分包渠道 | 多选 | 全部 | `distribution_channel_id` | 全部 |
| 归因媒体 | 多选 | 全部 | `attribution_media_id` | 全部 |
| 归因渠道 | 多选 | 全部 | `attribution_channel_id` | 全部 |
| 生命周期 | 多选 | 全部 | `display_lifecycle` | Q02/Q04/Q05 |
| 游戏 | 多选 | 全部 | `game_id` | Q02/Q03 |
| 统计方式 | Dropdown | `summary` | `display_mode` | 全部 |
| 数据状态 | 多选 | `complete` | `data_status` | 全部 |

绑定规则：

- 日期只过滤 `business_date`，不能直接过滤快照 `time`；
- `summary` 模式按查询期汇总，`detail` 模式增加日期分组；
- Joint 包含全部 Joint 游戏范围，包括游戏 ID 1—9；
- V1 使用独立 Model/View，不与 V2 在同一问题中相加；
- `unknown`、`not_available`、`delayed`、`immature` 为数据状态，不填充为 0；
- Dashboard 每个筛选器都必须逐卡绑定并验证结果变化。

Metabase Field Filter 模板：

```sql
[[AND {{business_date}}]]
[[AND {{data_scope}}]]
[[AND {{population_type}}]]
[[AND {{app_version}}]]
[[AND {{package_id}}]]
[[AND {{distribution_channel_id}}]]
[[AND {{attribution_media_id}}]]
[[AND {{attribution_channel_id}}]]
[[AND {{display_lifecycle}}]]
[[AND {{game_id}}]]
[[AND {{data_status}}]]
```

## 4. 指标字典与算法

### 4.1 pool_type 映射

| pool_type | 指标 | 原始值 |
|---:|---|---|
| 1 | 实际盈利 | `data` |
| 2 | 预期盈利 | `data` |
| 3 | 当日实际盈利调整 | `data` |
| 4 | 全量下注 | `data` |
| 5 | 破产保护下注 | `data` |
| 6 | 破产保护盈利 | `data`，通常负值 |
| 7 | 个人盈利控制下注 | `data` |
| 8 | 个人盈利控制盈利 | `data`，通常正值 |
| 11 | 实际回报率策略 | `data0-data4` 复合字段 |
| 12 | 预期回报比 | `data`，万分比 |
| 21 | 达标次数范围 | `data0-data2` |
| 22 | 实际盈利基准值 | `data` |
| 23 | 预期盈利基准值 | `data` |

全量经营指标：`1001/1002` 总充值次数/金额，`1003/1004` 复充次数/金额，`1005/1006` 提现次数/金额，`1007/1008` 受控人数/次数，`1009/1010` 绝对破产人数/次数，`1011` 留存人数，`1023/1024` 全部留存人数/升级人数。

新增经营指标：`11001/11002` 新增充值次数/金额，`11003/11004` 新增复充次数/金额，`11005/11006` 新增提现次数/金额，`11007/11008` 新增受控人数/次数，`11009/11010` 新增绝对破产人数/次数，`11011` 新增留存人数。

留存类型：

```text
1021：全量第 N 日留存，N=data0
1022：全量第 N 日升级，N=data0
1025：全量 N 日内累计升级，N=data0
1031：新增用户第 N 日留存，N=data0
1032：新增用户第 N 日升级，N=data0
1033：新增用户 N 日内累计升级，N=data0
```

### 4.2 基础/完全算法

```text
actual_profit = real_profit - real_reserved
base_bet = entire_bet - bankruptcy_bet - control_bet
base_actual_profit = actual_profit - bankruptcy_profit - control_profit
base_expected_profit = base_bet * (10000 - expected_rtp_raw) / 10000
entire_expected_profit = entire_bet * (10000 - expected_rtp_raw) / 10000
entire_actual_rtp = 1 - actual_profit / entire_bet
detail_page_base_actual_rtp = 1 - base_actual_profit / entire_bet
summary_base_actual_rtp = 1 - base_actual_profit / base_bet
base_rtp_gap = base_actual_rtp / base_expected_rtp - 1
entire_rtp_gap = entire_actual_rtp / entire_expected_rtp - 1
entire_bet_share = group_entire_bet / total_entire_bet
```

金额原始值除以 100 后展示；预期 RTP 原始值除以 100 后展示为百分比。所有除法使用安全除法，零分母返回 `NULL` 并显示 `N/A`。

### 4.3 时间与生命周期

```text
display_lifecycle = lifecycle - 1
business_date = snapshot_date - 1 day
```

每日历史主表固定：

```sql
change_type = 3
AND data_type = 1
```

基础实际回报比必须区分明细页和汇总页分母；不能用一个 `base_actual_rtp` 覆盖两种算法。

## 5. 五张报表字段与可视化

### Q01｜原始数据总数

粒度：`summary` 查询期 1 行；`detail` 按 `business_date`。

字段：

```text
business_date, total_base_bet, total_entire_bet,
total_base_actual_profit, total_entire_actual_profit,
total_base_expected_profit, total_entire_expected_profit,
total_base_actual_rtp, total_entire_actual_rtp,
total_base_expected_rtp, total_entire_expected_rtp,
total_user_count, avg_actual_profit_per_user,
adjusted_profit, data_cutoff_at, data_status
```

首屏 KPI：完全下注额、完全实际盈利、完全真实回报比、完全预期回报比、人数、RTP 差距。

图表：下注额趋势、基础/完全下注对比、实际/预期 RTP 趋势、数据状态。

### Q02｜原始详细奖池

粒度：`display_lifecycle × game_id`；detail 模式增加日期。

字段：

```text
business_date, display_lifecycle, game_id, game_name,
expected_rtp, profit_ratio_per_10000,
base_expected_profit, base_actual_profit, base_bet,
detail_page_base_actual_rtp,
bankruptcy_protection_amount, user_profit_control_amount,
entire_expected_profit, entire_actual_profit, entire_bet,
entire_bet_share, entire_actual_rtp,
base_rtp_gap, entire_rtp_gap, data_status
```

图表：生命周期 × 游戏 RTP 偏差矩阵、下注额排名、RTP 偏差排行、控制金额占比。

### Q03｜生命周期奖池分游戏汇总

粒度：`game_id`；detail 模式增加日期。

字段：

```text
business_date, game_id, game_name, provider, is_joint,
base_bet, base_expected_profit, base_actual_profit,
base_actual_rtp, base_expected_rtp, base_rtp_gap,
bankruptcy_protection_amount, user_profit_control_amount,
bankruptcy_protection_to_bet, user_profit_control_to_bet,
entire_bet, entire_expected_profit, entire_actual_profit,
entire_actual_rtp, entire_expected_rtp, entire_rtp_gap,
entire_bet_share, data_status
```

默认按 `entire_bet DESC`；支持按 RTP 差距、实际盈利和下注贡献排序。

### Q04｜原始数据活跃周期-回报

粒度：`display_lifecycle`；detail 模式增加日期。

字段：

```text
business_date, display_lifecycle, base_bet,
base_actual_profit, base_expected_profit,
summary_base_actual_rtp, base_expected_rtp, base_rtp_gap,
bankruptcy_protection_amount, user_profit_control_amount,
entire_bet, entire_bet_share, entire_actual_profit,
entire_expected_profit, entire_actual_rtp, entire_expected_rtp,
entire_rtp_gap, user_count, avg_actual_profit_per_user, data_status
```

图表：生命周期下注、实际/预期 RTP、RTP 差距、人均实际盈利、控制金额。

### Q05｜原始数据活跃周期-付费

粒度：`display_lifecycle`；detail 模式增加日期。

字段：

```text
business_date, display_lifecycle, user_count,
recharge_count, recharge_amount,
repeat_recharge_count, repeat_recharge_amount,
withdraw_count, withdraw_amount, avg_flow_recharge_ratio,
revenue, tx_amount, avg_actual_revenue_per_user,
tc_ratio, loss_coefficient,
absolute_bankrupt_user_count, absolute_bankrupt_count,
avg_absolute_bankrupt_count, data_status
```

图表：充值/复充/提现、营收与 TX、TC 比和折损系数、破产人数与人均破产次数。

## 6. SQL 与对象清单

SQL 目录：

```text
analysis/metabase_lifecycle_dev_2026_08_26/sql/
```

| 文件 | 用途 |
|---|---|
| [`01_lifecycle_snapshot_base.sql`](../../analysis/metabase_lifecycle_dev_2026_08_26/sql/01_lifecycle_snapshot_base.sql) | V2 每日快照、业务日期、生命周期和快照过滤 |
| [`02_lifecycle_pool_pivot.sql`](../../analysis/metabase_lifecycle_dev_2026_08_26/sql/02_lifecycle_pool_pivot.sql) | pool_type 行转宽表和基础/完全派生指标 |
| [`03_lifecycle_dimension_model.sql`](../../analysis/metabase_lifecycle_dev_2026_08_26/sql/03_lifecycle_dimension_model.sql) | 授权 Model/View 字段契约和维度关联模板 |
| [`04_lifecycle_report_queries.sql`](../../analysis/metabase_lifecycle_dev_2026_08_26/sql/04_lifecycle_report_queries.sql) | Q01—Q05 Metabase Saved Question SQL |
| [`05_lifecycle_quality_checks.sql`](../../analysis/metabase_lifecycle_dev_2026_08_26/sql/05_lifecycle_quality_checks.sql) | 日期、重复、分母、维度覆盖和跨表质量校验 |

Metabase 对象：

```text
Model: model_lifecycle_v2_joint_daily
Q01: Q01_lifecycle_overview
Q02: Q02_lifecycle_pool_detail
Q03: Q03_lifecycle_game_summary
Q04: Q04_lifecycle_return_by_lifecycle
Q05: Q05_lifecycle_payment_by_lifecycle
Dashboard: DB_lifecycle_v2_joint
```

## 7. Metabase 配置步骤

### 7.1 Collection 与权限

Collection：

```text
Waje / Lifecycle / V2 Joint
```

普通分析人员只读聚合结果；Robin、Ryan 和授权人员可编辑问题与 Dashboard；数据开发维护 Model/View；普通角色不得访问用户、订单、KYC、账户和原始资金明细。

### 7.2 Model 配置

1. 创建 `model_lifecycle_v2_joint_daily`；
2. 将 `business_date` 标记为日期字段；
3. 将版本、包体、渠道、媒体、生命周期和游戏标记为分类字段；
4. 金额只在一个层级完成除以 100；
5. RTP、TC 和比例统一配置百分比格式；
6. 显示 `data_status`、`data_cutoff_at` 和 `metric_version`；
7. 隐藏所有用户、订单、KYC 和账户标识字段。

### 7.3 Dashboard 布局

1. 顶部：日期、数据范围、用户范围、版本、包体、渠道；
2. 第一行：完全下注、完全实际盈利、实际 RTP、预期 RTP、RTP 差距、人数；
3. 第二行：下注额和 RTP 趋势；
4. 第三行：游戏规模与 RTP 偏差；
5. 第四行：生命周期回报；
6. 第五行：充值、提现、营收、TX、TC；
7. 底部：Q02 明细和数据质量状态。

V1 单独存放于 `Waje / Lifecycle / V1 Reference`。当前 V1 表字段不足以直接复原完整指标，因此首期不生成 V1 与 V2 合计。

## 8. 质量验收

- 业务日期 D 正确读取 D+1 快照；
- 固定 `change_type=3`、`data_type=1`；
- `display_lifecycle=lifecycle-1`；
- Joint 游戏范围正确；
- Q02 按游戏汇总与 Q03 一致；Q03 按游戏求和与 Q01 一致；
- Q04/Q05 生命周期金额和人数与 Q01 口径一致；
- RTP 使用累计分子/分母，预期 RTP 按下注额加权；
- 人数按查询期去重，不按日累加；
- 零分母、缺失日期、延迟和未成熟数据显示 `N/A` 或独立状态；
- 版本、包体、渠道筛选实际改变结果；
- 普通权限不能看到用户、订单、KYC、账户和原始资金明细；
- 以 `2026-07-27` 至 `2026-08-10` 为金标区间完成 GM ↔ Model/View ↔ Q01-Q05 对账；
- 页面、导出和 SQL 结果一致。

## 9. 实施顺序与待确认项

1. 数据开发建立授权 `model_lifecycle_v2_joint_daily`；
2. 确认数据库时区、快照去重键和业务日 D→D+1 规则；
3. 补齐版本、包体、渠道和归因维度历史关联；
4. 提供 TC 比、流充比和折损系数的真实分子/分母；
5. 配置 Q01-Q05、Dashboard、筛选绑定和权限；
6. 完成金标区间对账后开放日常使用。

当前 `observed_metadata` 只表示字段定义可见。Model/View 实际数据、新鲜度、维度覆盖、业务公式和对账结果通过后，状态才可升级为 `certified`。

## 10. 关联资料

- [生命周期 V2 数据统计口径与算法拆解](./GM-Lifecycle-Pool-v2-数据统计口径与算法拆解-2026-08-25.md)
- [GM Lifecycle Pool V2 Joint 迁移方案](./GM-Lifecycle-Pool-v2-Joint迁移至起源平台实施方案-飞书存档版-2026-08-14.md)
- [GM 与起源报表平台重构方案](./GM与起源报表平台重构方案-2026-08-06.md)
- [Metabase 全库数据资产索引](./Metabase全库数据资产索引-2026-08-26.md)
- [Lifecycle 报表配置合同](../../config/lifecycle_joint_report_spec.json)
