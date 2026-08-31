---
title: GM Lifecycle Pool v2 数据统计口径与算法拆解
date: 2026-08-25
type: data-dictionary-and-algorithm-spec
source: /Users/robin/Downloads/生命周期V2报表数据口径.md
source_sha256: b5f346dce157e69d3f52cd1905a29e1d8f2f0603cba0f34f67c478c3753eb086
status: 用户提供口径整理版，待生产 SQL 与页面导出逐项复核
owner: analyst
tags: [GM, Lifecycle Pool v2, Joint, 数据口径, 算法, RTP, 生命周期, 留存]
---

# GM Lifecycle Pool v2 数据统计口径与算法拆解

## 1. 文档定位

本文将用户提供的《生命周期 V2 报表数据口径》整理为项目可执行的指标字典、数据血缘、算法公式和验收清单，服务于：

- GM `Lifecycle Pool v2 (Joint)` 数据采集与 Excel/飞书更新；
- 生命周期价值、RTP、充值提现和破产风险分析；
- GM 报表迁移到起源平台后的字段映射和对账；
- 后续事实表、宽表和指标层设计。

证据边界：本文的 `confirmed_by_source_doc` 内容来自用户提供的口径文件；尚未用生产数据库 SQL、GM 页面原始导出和起源字段逐项复核的内容，保留为 `to_be_verified`，不能直接当作生产实现已经验证。

## 2. 一页结论

### 2.1 每日历史报表主链路

```text
stat_lifecycle_pool_v2_log
  → change_type = 3（每日自动快照）
  → data_type = 1（每日调整前）
  → 业务日 D 对应次日落库快照 D+1
  → 后端 lifecycle - 1 = 页面展示生命周期
  → 按游戏 × 生命周期拆解
  → 计算基础/完全下注、盈利、RTP、保护和控制金额
  → 汇总到总览、按游戏、按生命周期报表
```

### 2.2 两张容易混淆的源表

| 源表 | 用途 | 是否替代每日历史主表 |
|---|---|---|
| `stat_lifecycle_pool_v2_log` | 每日生命周期历史快照、奖池、经营、留存和升级指标 | 是，页面历史报表主表 |
| `stat_lifecyclev2_rtp_record` | 15 分钟级 RTP 采样和日内趋势 | 否，不用于还原每日历史快照 |

### 2.3 三个必须写入程序门禁的规则

1. 页面业务日期 `D` 查询的是落库日期 `D+1` 的每日快照，不能直接用 `D` 过滤 `time`。
2. `data_type = 1` 是历史报表主要口径，`data_type = 2` 是日切后的重置值，不能混用。
3. 基础实际回报率存在页面特殊口径：明细页使用“基础实际盈利 ÷ 全量下注”作为分母，不能擅自替换为基础下注分母。

## 3. 报表区域与分析粒度

| 页面区域 | 业务粒度 | 主要用途 |
|---|---|---|
| 总体汇总 | 日期或查询期 | 总下注、总盈利、回报率、人数和调整 |
| 奖池明细 | 日期 × 展示生命周期 × 游戏 | 定位单个生命周期/游戏的下注、盈利、RTP 和控制差异 |
| 按游戏汇总 | 日期 × 游戏 | 比较游戏规模、实际/预期 RTP 和控制金额 |
| 按生命周期汇总 | 日期 × 展示生命周期 | 观察生命周期价值、充值、提现、破产和用户数 |
| 新增用户生命周期汇总 | 日期 × 展示生命周期 | 单独观察新增用户人群 |
| 生命周期留存 | cohort 日期 × 展示生命周期 | 次日、3 日、7 日留存和升级比例 |
| 新增用户留存 | cohort 日期 × 展示生命周期 | 新增用户留存和升级 |

生产宽表建议显式增加 `population_type`：

- `all`：全量/活跃用户口径；
- `new`：新增用户口径。

两种人群不能直接合计，也不能把新增用户表当作全量用户表。

## 4. 源表字段与过滤口径

### 4.1 `stat_lifecycle_pool_v2_log`

| 字段 | 含义 | 使用注意 |
|---|---|---|
| `id` | 自增主键 | 物理记录标识，不作为业务维度 |
| `game_type` | 游戏 ID | `>0` 通常为具体游戏；`0` 通常为生命周期/全局汇总 |
| `lifecycle` | 后端生命周期 ID | 页面展示通常为 `lifecycle - 1` |
| `data_type` | 快照类型 | `1` 每日调整前；`2` 每日调整后 |
| `pool_type` | 指标类型 | 决定行表示下注、盈利、充值、留存等 |
| `change_type` | 变更类型 | `1` 批量修改；`2` 单独修改；`3` 每日自动快照 |
| `data` | 主指标值 | 大多数金额、人数、次数位于此字段 |
| `data0`–`data4` | 扩展字段 | 留存天数、策略区间、控制类型/值等按 `pool_type` 解释 |
| `time` | Unix 秒时间戳 | 实际落库时间，不等于页面业务日期 |
| `remark` | 备注 | 每日快照通常为空 |

历史页面固定过滤：

```sql
change_type = 3
AND data_type = 1
AND time 位于业务日 D 次日的落库时间窗口
```

### 4.2 `stat_lifecyclev2_rtp_record`

15 分钟级 RTP 趋势辅助表字段包括：`cycle`、`game_id`、`real_profit`、`real_profit_reserved`、`bet`、`entire_real_rtp`、`year_day`、`create_at`。

它适合日内 RTP 趋势，不应与每日历史快照混合，也不能用它替代 `stat_lifecycle_pool_v2_log` 的每日回填。

### 4.3 游戏范围

| 页面 | 规则 |
|---|---|
| 普通 Lifecycle V2 | 排除游戏 ID 1–9 |
| CO / Joint 页面 | 不排除游戏 ID 1–9，包含全部游戏 |

`game_type = 0` 不应作为具体游戏名称展示。游戏 ID 到名称应使用版本化字典，不应长期依赖前端硬编码映射。

## 5. 单位、生命周期和日期转换

### 5.1 单位转换

| 数据类型 | 存储口径 | 页面口径 |
|---|---|---|
| 金额 | 最小货币单位 | 除以 100，通常保留两位小数 |
| 预期回报比 | 万分比 | 除以 100 后显示 `%`，如 9700 → 97.00% |
| 盈利比 | 万分比 | 页面通常直接显示万分比整数，需独立命名避免与 RTP 混淆 |
| 人数/次数 | 整数 | 原值显示 |
| 比例 | 小数 | 乘以 100 后显示 `%` |

### 5.2 生命周期转换

```text
display_lifecycle = lifecycle - 1
```

示例：后端 `lifecycle=1/2/3` 对应页面展示 `0/1/2`。总体和汇总指标通常排除展示生命周期 0；具体页面若存在不同范围，必须在回执中记录。

### 5.3 业务日期转换

```text
页面业务日期 D → 查询落库日期 D+1 的每日快照
```

任务实现必须固定数据库时区并使用明确的 Unix 秒边界。若页面查询日期与导出数据日期不一致，必须标记 `query_stale` 或 `date_mismatch`，不能靠相邻日期补值。

## 6. `pool_type` 指标字典

### 6.1 游戏 × 生命周期奖池指标

这些指标通常满足 `game_type > 0`。

| `pool_type` | 指标 | `data` 含义 | 单位 |
|---:|---|---|---|
| 1 | 实际盈利 | 实际奖池累计值 | 金额 |
| 2 | 预期盈利 | 预期奖池累计值 | 金额 |
| 3 | 当日实际盈利调整 | 人工或自动调整累计值 | 金额 |
| 4 | 全量下注 | 全部受控下注 | 金额 |
| 5 | 破产保护下注 | 破产保护场景下注 | 金额 |
| 6 | 破产保护盈利 | 破产保护场景盈利 | 金额，通常负值 |
| 7 | 个人盈利控制下注 | 个人控制场景下注 | 金额 |
| 8 | 个人盈利控制盈利 | 个人控制场景盈利 | 金额，通常正值 |
| 11 | 实际回报率策略 | 终身盈利区间到实际回报比的策略 | 复合字段 |
| 12 | 预期回报比 | 游戏/生命周期目标 RTP | 万分比 |
| 21 | 达标次数范围 | 生命周期达标次数范围 | 次数 |
| 22 | 实际盈利基准值 | 日切后实际奖池起始基准 | 金额 |
| 23 | 预期盈利基准值 | 日切后预期奖池起始基准 | 金额 |

`pool_type=11` 的页面展示：

```text
[data1, data2) → data
```

其中 `data0` 是策略序号，`data1`/`data2` 是终身盈利区间左闭右开边界，`data` 是实际回报比，`data3`/`data4` 是控制类型和值。

### 6.2 新增用户奖池指标

| `pool_type` | 指标 |
|---:|---|
| 10001 | 新增用户实际盈利 |
| 10002 | 新增用户预期盈利 |
| 10004 | 新增用户全量下注 |
| 10005/10006 | 新增用户破产保护下注/盈利 |
| 10007/10008 | 新增用户个人盈利控制下注/盈利 |

新增用户与全量用户共用 `pool_type=12` 的预期回报比。新增用户快照没有独立的实际/预期盈利基准字段，渲染时通常按 0 处理，但必须确认实现页面的实际默认值。

### 6.3 全量生命周期经营指标

这些指标通常满足 `game_type=0`：

| `pool_type` | 指标 |
|---:|---|
| 1001/1002 | 总充值次数/金额 |
| 1003/1004 | 复充次数/金额 |
| 1005/1006 | 总提现次数/金额 |
| 1007/1008 | 受控人数/次数 |
| 1009/1010 | 绝对破产人数/次数 |
| 1011 | 留存人数 |
| 1023/1024 | 全部留存人数/全部升级人数 |

### 6.4 新增用户生命周期经营指标

| `pool_type` | 指标 |
|---:|---|
| 11001/11002 | 新增用户总充值次数/金额 |
| 11003/11004 | 新增用户复充次数/金额 |
| 11005/11006 | 新增用户总提现次数/金额 |
| 11007/11008 | 新增用户受控人数/次数 |
| 11009/11010 | 新增用户绝对破产人数/次数 |
| 11011 | 新增用户留存人数 |

### 6.5 留存与升级

| `pool_type` | 人群 | `data` | `data0` | `data1` |
|---:|---|---|---|---|
| 1021 | 全量 | 第 N 日留存人数 | N | cohort 总人数 |
| 1022 | 全量 | 第 N 日升级人数 | N | cohort 总人数 |
| 1025 | 全量 | N 日内累计升级人数 | N | cohort 总人数 |
| 1031 | 新增 | 第 N 日留存人数 | N | cohort 总人数 |
| 1032 | 新增 | 第 N 日升级人数 | N | cohort 总人数 |
| 1033 | 新增 | N 日内累计升级人数 | N | cohort 总人数 |

页面的周期升级比例使用累计升级类型 `1025/1033`，不能误用单日升级类型 `1022/1032`。

## 7. 奖池明细算法

设当前游戏、展示生命周期的字段为：

```text
real_profit       = pool_type 1
expected_profit   = pool_type 2
adjusted_profit   = pool_type 3
entire_bet        = pool_type 4
bankruptcy_bet    = pool_type 5
bankruptcy_profit = pool_type 6
control_bet       = pool_type 7
control_profit    = pool_type 8
expected_rtp      = pool_type 12
real_reserved     = pool_type 22
expected_reserved = pool_type 23
```

### 7.1 核心派生字段

| 页面指标 | 公式 |
|---|---|
| 全量实际盈利 | `real_profit - real_reserved` |
| 基础下注 | `entire_bet - bankruptcy_bet - control_bet` |
| 基础实际盈利 | `全量实际盈利 - bankruptcy_profit - control_profit` |
| 基础预期盈利 | `基础下注 × (10000 - expected_rtp) / 10000` |
| 全量预期盈利 | `全量下注 × (10000 - expected_rtp) / 10000` |
| 全量实际回报率 | `1 - 全量实际盈利 / 全量下注` |
| 基础实际回报率（明细页口径） | `1 - 基础实际盈利 / 全量下注` |
| 生命周期全量下注占比 | `当前游戏全量下注 / 同生命周期所有游戏全量下注` |
| 当日实际盈利调整 | `adjusted_profit` |

金额最终展示时除以 100。

### 7.2 关键口径冲突防护

“基础实际回报率”在不同报表层级可能有不同分母：

- 明细页：按页面口径，分母是全量下注；
- 按游戏/按生命周期汇总：通常是 `1 - 基础实际盈利 / 基础下注`。

离线报表必须保留字段名区分，例如：

```text
detail_page_base_actual_rtp
summary_base_actual_rtp
```

不能用一个通用 `base_actual_rtp` 覆盖两种算法。

## 8. 汇总算法

### 8.1 总体汇总

总体汇总只纳入展示生命周期 `>0` 的记录：

| 指标 | 口径 |
|---|---|
| 总基础/全量下注 | 明细求和 |
| 总基础/全量实际盈利 | 明细求和 |
| 总基础/全量预期盈利 | 明细求和；全量预期盈利按页面规定取整后求和 |
| 总基础/全量实际回报率 | `1 - 总实际盈利 / 总下注` |
| 总基础/全量预期回报率 | `1 - 总预期盈利 / 总下注` |
| 总用户数 | 展示生命周期 `>0` 的受控人数之和 |
| 当日实际盈利调整 | `adjusted_profit` 求和 |

不要平均每日百分比；RTP、TC、TX 等比例优先从累计分子/分母重算。

### 8.2 按游戏汇总

按 `game_type` 汇总展示生命周期 `>0` 的明细：

```text
base_rtp_gap   = base_actual_rtp / base_expected_rtp - 1
entire_rtp_gap = entire_actual_rtp / entire_expected_rtp - 1
protection_to_bet = protection_amount / game_entire_bet
control_to_bet    = control_amount / game_entire_bet
game_bet_share    = game_entire_bet / all_game_entire_bet
```

基础和全量回报比、预期盈利、实际盈利、控制金额必须分别保存，不能混成一套指标。

### 8.3 按生命周期汇总

奖池指标按生命周期汇总后，再关联 `pool_type=1001–1011` 的全量经营指标或 `11001–11011` 的新增用户经营指标。

常用派生：

```text
avg_repeat_count = repeat_recharge_count / controlled_headcount
avg_bet_recharge = lifecycle_entire_bet / total_recharge_amount
actual_revenue   = total_recharge_amount - total_withdraw_amount
avg_actual_profit = lifecycle_entire_actual_profit / controlled_headcount
avg_actual_revenue = actual_revenue / controlled_headcount
withdraw_to_recharge = total_withdraw_amount / total_recharge_amount
depreciation_factor = withdraw_to_recharge / (entire_actual_rtp ^ avg_bet_recharge)
avg_bankruptcy_count = absolutely_bankruptcy_count / controlled_headcount
```

当分母为 0 时统一返回 0，并在质量报告中区分“真实为 0”和“因无分母返回 0”。

## 9. 留存和加权平均

留存行粒度：

```text
cohort_date × display_lifecycle × population_type
```

全量用户：

```text
D2 留存率 = pool_type 1021, N=2 的留存人数 / cohort 总人数
D3 留存率 = pool_type 1021, N=3 的留存人数 / cohort 总人数
D7 留存率 = pool_type 1021, N=7 的留存人数 / cohort 总人数
```

周期升级比例使用 `pool_type=1025`；新增用户改用 `1031/1033`。

加权平均：

```text
weighted_retention
  = Σ(每日留存率 × 当日 cohort 人数) / Σ当日 cohort 人数

weighted_upgrade
  = Σ(每日升级比例 × 当日 cohort 人数) / Σ当日 cohort 人数
```

加权平均行的“用户数”是日期范围内每日 cohort 人数的算术平均，不是总人数。

## 10. 推荐事实模型

### 10.1 游戏日宽表

```text
business_date + display_lifecycle + game_type + population_type
```

建议字段：下注、实际/预期盈利、实际盈利基准、破产保护、个人控制、基础派生字段、实际/预期 RTP、盈利比、调整值。

### 10.2 生命周期日宽表

```text
business_date + display_lifecycle + population_type
```

同时保存奖池、充值、复充、提现、营收、受控人数/次数、破产人数/次数、人均指标和折损系数。

### 10.3 留存宽表

```text
cohort_date + display_lifecycle + population_type + nth_day
```

`nth_day` 至少覆盖 2/3/7，并保存 cohort 人数、留存人数/率、累计升级人数/比例。

## 11. 采集与数据质量门禁

### 11.1 查询门禁

- 来源固定为 GM `Lifecycle Pool v2 (Joint)`，不能误用普通 `Lifecycle Pool v2`。
- 日期控件值必须与查询回执一致；点击“查询历史记录”后等待结果稳定。
- 四类导出应分别保存：汇总、详细奖池、按游戏汇总、活跃周期。
- 每个日期保存页面日期、查询时间、返回行数、文件哈希和跨表校验结果。

### 11.2 完整性门禁

- 汇总：1 行；详细奖池：展示生命周期 0–4 × 游戏；分游戏：游戏数；活跃周期：实际返回集合中筛选生命周期 1–4。
- 同一业务日期、生命周期、游戏和 `pool_type` 不应出现重复快照。
- 不补零、不用前一天代替缺失日期。
- 8/25 这类尚未达到统计口径的日期，应清除或标记 `not_mature`，不能参与趋势和周报统计。
- 留存 N=2/3/7 未成熟时留空或标记 `not_mature`，不能当成真实 0。

### 11.3 跨表勾稽

- 详细奖池按游戏求和应与分游戏汇总一致。
- 分游戏汇总按游戏求和应与总体汇总一致。
- 活跃周期的生命周期奖池与经营指标应按同一用户口径关联。
- RTP、TC、TX 和人均指标应从累计分子/分母重算，不平均每日比例。
- 发现 `data_static_suspect` 时，禁止输出新游戏趋势、RTP 或羊毛结论，先独立复查同一日期。

## 12. 待生产验证项

以下项目来自口径文档，但仍应与生产 SQL、GM 页面和原始导出逐项核对：

1. `pool_type=11` 策略区间的边界是否始终左闭右开，以及 `data` 的实际回报比单位。
2. `pool_type=1/2` 的盈利是否已经包含所有结算、奖励和退款调整。
3. `real_reserved` / `expected_reserved` 在不同页面的显示名称和扣除方向。
4. 普通 V2 与 CO/Joint 的游戏 ID 1–9 过滤是否在后端统一执行。
5. `data_type=1/2` 的日切时间和固定时区边界。
6. 新增用户预期/实际基准值按 0 处理是否与当前生产页面一致。
7. 0 分母返回 0 的页面行为是否需要在分析层额外保存 `no_denominator` 状态。
8. 页面汇总对“全量预期盈利”的取整时点，是明细取整后求和还是汇总后取整。

## 13. 相关项目知识

- [[GM-Lifecycle-Pool-v2报表结构与整合优化分析-2026-08-06]]
- [[GM-Lifecycle-Pool-v2-Joint迁移至起源平台实施方案-2026-08-14]]
- [[GM与起源报表平台重构方案-2026-08-06]]
- [[Waje数据平台架构梳理和优化整合方案-2026-08-07]]
- [[../05-运行/2026-08-24-生命周期价值飞书在线更新复盘与采集优化SOP]]

## 14. 证据状态

- `confirmed_by_source_doc`：字段名、`pool_type` 字典、日期 D→D+1、生命周期转换、页面公式和留存公式，均来自用户提供文件。
- `implementation_guardrail`：不补零、未成熟日期移除、快照稳定性、跨表勾稽和异常状态，作为项目执行规范。
- `to_be_verified`：生产 SQL 的具体时间边界、调整字段是否已含退款/奖励、普通/CO 游戏过滤和页面取整时点。
- 原始文件位于 `/Users/robin/Downloads/生命周期V2报表数据口径.md`，未复制任何账号、Token、Cookie 或用户明细。
