---
title: TaDa Games 投注机制属性总表拆解
date: 2026-08-06
source: /Users/robin/Downloads/投注機制屬性總表_TaDa Games.xlsx
status: 初版
---

# TaDa Games 投注机制属性总表拆解

## 1. 数据概况

| 项目 | 内容 |
|---|---|
| 原始文件 | `投注機制屬性總表_TaDa Games.xlsx` |
| 工作表 | `投注機制屬性`、`說明` |
| 数据日期 | 2026-08-06 |
| 收录范围 | 至少具备一项投注机制属性的游戏 |
| 游戏数量 | 48 款 |
| 标识方式 | 符合属性标记 `V`，不符合留空 |
| 主键 | GameID |

该表是 TaDa Games 的“投注交互/组局机制字典”，不是赔率、理论 RTP 或实际 RTP 表。它适合用于游戏分类、投注行为分析、RTP 分层和看板筛选，不能单独用于判断游戏概率是否正常。

## 2. 四类投注机制定义

| 属性 | 含义 | 分析价值 |
|---|---|---|
| 单局可对押 | 同一局可同时押注互相对立的目标，是“单局多目标投注”的子集合 | 影响同局下注组合、覆盖率、对冲行为、下注额和实际回报结构 |
| 单局多目标投注 | 同一局可以押注多个目标 | 影响单局下注笔数、下注组合、命中率、局均下注和 RTP 分布 |
| 单局多段投注 | 同一局分多段进行投注 | 影响投注时序、局内加注、局均下注、用户决策和连续下注行为 |
| 多人共玩 | 多名玩家共同参与同一局 | 影响局级与玩家级口径、同局玩家数、共享结果和多人房间 RTP 分摊 |

### 口径关系

- 单局可对押属于单局多目标投注的子集合，但当前表将其单独标记，分析时应保留两个字段。
- 属性之间可以重叠，不应把四类属性当作互斥分类。
- “多人共玩”是 48 款中唯一标记的属性，当前对应 `Crash Fireworks`。
- 表中属性描述的是投注机制，不代表游戏是否为自研、联运、真人、电子、Crash 或 Bingo；游戏类型需要另建字典。

## 3. 游戏按投注机制分组

### 3.1 单局可对押：5 款

| GameID | 游戏 |
|---:|---|
| 79 | Andar Bahar |
| 111 | Number King |
| 123 | Dragon & Tiger |
| 152 | Baccarat |
| 262 | Speed Baccarat |

这类游戏适合重点分析同局对立目标是否同时下注、对押金额占比、单局净结果和玩家实际回报分布。

### 3.2 单局多目标投注：28 款

| GameID | 游戏 |
|---:|---|
| 79 | Andar Bahar |
| 111 | Number King |
| 113 | Poker King |
| 114 | European Roulette |
| 123 | Dragon & Tiger |
| 124 | 7up 7down |
| 125 | Sic BO |
| 152 | Baccarat |
| 197 | Color Game |
| 204 | Color Prediction |
| 219 | Blackjack |
| 220 | Blackjack LuckyLadies |
| 224 | Go Rush |
| 262 | Speed Baccarat |
| 272 | Keno Bonus Number |
| 273 | Keno Super Chance |
| 297 | Jogo Do Bicho |
| 305 | Super Cockfight |
| 397 | Jhandi Munda |
| 407 | Crash Goal |
| 419 | Penalty Kicks |
| 436 | Fortune Roulette |
| 459 | Crash Touchdown |
| 512 | Crash Puck |
| 554 | Golden Treasure |
| 624 | Lucky Roulette |
| 638 | Golden Explorer |
| 694 | Roulette Multiplier Spin |
| 719 | Grand Golden Treasure |
| 792 | Crash Fireworks |

该组适合比较目标数量、下注选项数、局均投注目标数、目标命中率和不同投注组合的回报差异。

### 3.3 单局多段投注：23 款

| GameID | 游戏 |
|---:|---|
| 79 | Andar Bahar |
| 122 | iRich Bingo |
| 139 | Fortune Bingo |
| 143 | Bonus Bingo |
| 147 | Bingo Empire |
| 148 | Bingo Garnavab |
| 149 | Calaca Bingo |
| 150 | Lucky Bingo |
| 151 | Super Bingo |
| 173 | West Hunter Bingo Golden |
| 174 | Jackpot Bingo |
| 177 | Bingo Adventure |
| 178 | Go Goal Bingo Lighting |
| 195 | Pearls of Bingo |
| 216 | Candy Land Bingo |
| 217 | Magic Lamp Bingo |
| 219 | Blackjack |
| 220 | Blackjack LuckyLadies |
| 272 | Keno Bonus Number |
| 273 | Keno Super Chance |
| 404 | 终极德州扑克 |
| 633 | Gallina Fortunata |
| 737 | Jackpot Football |

该组需要区分“同一局内多段下注”与“多局连续下注”，数据上建议使用 `round_id`、`bet_sequence` 或等价字段还原局内投注顺序。

### 3.4 多人共玩：1 款

| GameID | 游戏 |
|---:|---|
| 792 | Crash Fireworks |

多人共玩游戏不能只按玩家行直接计算 RTP。应同时保留局级事实和玩家级事实，避免同一局结果被重复计入或玩家分摊不一致。

## 4. 交叉属性与分类观察

根据表尾汇总：

| 属性 | 游戏数 |
|---|---:|
| 单局可对押 | 5 |
| 单局多目标投注 | 28 |
| 单局多段投注 | 23 |
| 多人共玩 | 1 |

总属性标记数为 57 次，超过 48 款游戏，说明属性存在重叠。重点交叉关系包括：

- `Andar Bahar` 同时具备单局可对押、单局多目标、单局多段。
- `Blackjack` 与 `Blackjack LuckyLadies` 同时具备单局多目标和单局多段。
- `Crash Fireworks` 同时具备单局多目标、单局多段和多人共玩。
- `Keno Bonus Number`、`Keno Super Chance` 属于单局多段投注，原表未标记为单局多目标投注。

这些重叠游戏应作为机制分析样本，而不是重复计数为多个独立游戏。

## 5. 与 RTP/生命周期分析的结合方式

### 5.1 建议增加的维度

在 BigQuery/Ares/Metabase 的游戏字典中增加：

```text
game_id
game_name
provider = TaDa
bet_opposite_target_flag
multi_target_bet_flag
multi_segment_bet_flag
multiplayer_flag
game_type
is_self_developed
is_joint
effective_date
source_file
```

### 5.2 推荐分析指标

按投注机制属性分层比较：

- 参与人数、活跃人数。
- 局数、下注次数、局内下注段数。
- 总下注额、局均下注、玩家人均下注。
- 目标数、单局平均投注目标数、对押率。
- 命中率、派奖额、基础/完全真实回报比。
- 基础/完全预期回报比及差距。
- RTP P5/P50/P95/P99 和波动率。
- 连续参与局数、局间时长、退出率。
- 生命周期 1/2/3/4…N 的下注额、TC 比、TX 率和留存。

### 5.3 重要口径要求

- 多目标投注游戏必须保留“局级结果”和“投注目标级结果”，不能只按投注行聚合。
- 多段投注游戏必须保留段序号，否则无法分析局内加注和提前退出。
- 多人共玩游戏必须按 `round_id` 去重，并区分玩家下注额、公共结果和派奖分摊。
- RTP 应按下注额加权，不应对每个目标/玩家 RTP 做简单平均。
- 该表只有机制属性，没有理论赔率、概率或 RTP 参数；概率正常性仍需结合游戏规则、赔率表和 GM Lifecycle Pool V2 结果。

## 6. 对当前项目的应用

### 看板筛选

在游戏 RTP 和生命周期看板中增加投注机制筛选：

- 单局可对押。
- 单局多目标投注。
- 单局多段投注。
- 多人共玩。
- 属性组合筛选，例如“多目标 + 多段”。

### 异常排查

当 RTP、下注额或 TX 率异常时，优先检查是否集中在某类投注机制：

- 对押游戏：检查对立目标同时下注和净回报计算。
- 多目标游戏：检查投注目标重复计数、目标级派奖和局级去重。
- 多段游戏：检查局内段序、未完成段和跨日结算。
- 多人共玩：检查同局玩家重复计入、房间结果和派奖分摊。

### 产品体验分析

投注机制属性还可以与体验指标关联：

- 多目标投注 → 规则理解成本、下注选项点击、单局操作复杂度。
- 多段投注 → 局内停留、连续下注、加注行为、局间时长。
- 对押 → 策略/对冲行为、风险偏好和实际 RTP 波动。
- 多人共玩 → 房间参与、同时在线人数、社交互动和局级等待时间。

## 7. 数据治理与待确认项

1. 确认 48 款游戏是否为当前有效游戏，补充上线/下线时间和版本。
2. 统一游戏名称空格、大小写和别名，例如 `Fish `、`Whot  `、`RouletteV2 `。
3. 核对 `GameID=792 Crash Fireworks` 的多人共玩与多段投注边界，确认 `round_id`、玩家分摊和多段下注记录是否可追溯。
4. 确认每款游戏的 `round_id`、玩家 ID、下注 ID、bet sequence 和派奖 ID 是否可关联。
5. 追加游戏类型、供应商、自研/联运、理论 RTP、赔率表和规则链接。
6. 将该表作为 `dim_game_bet_mechanism` 维表纳入 BigQuery/Ares 统一数据字典。
7. 每次游戏机制或规则变更时更新 `effective_date` 和属性版本，避免历史数据被当前属性覆盖。

## 来源

- 原始文件：`/Users/robin/Downloads/投注機制屬性總表_TaDa Games.xlsx`
- 关联资料：[[GM-Lifecycle-Pool-v2报表结构与整合优化分析-2026-08-06]]
- 关联资料：[[版本数据分析资料入库-2026-08-04]]
- 关联资料：[[数据平台与报表]]
