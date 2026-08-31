---
type: configuration-reference
domain: product-game-and-business-config
product: Waje Special
status: generated
updated: 2026-08-28
source_revision: 17409
tags: [waje, 新包, 配置, 游戏, 数值, 风控, 生命周期]
---

# Waje 产品与游戏配置资料库

> 本资料库由“线上数值新包”工作簿自动拆解。它记录产品设计配置与版本线索，不等同于当前生产事实；RTP、支付、资产、提现和风控结论仍须以服务端配置快照及事实表验证。

## 1. 同步状态

- 来源：[飞书配置工作簿](https://ksg964l11fam.sg.larksuite.com/sheets/WWBBsLNl4hTFnbtI9arlmGsqgoc)
- 当前 revision：`17409`；读取时间：`2026-08-28T15:03:22+08:00`。
- 工作表：`69` 个，其中隐藏 ` 13` 个；结构化配置项：`24637` 条。
- 本次差异：新增 `332`、修改 `0`、删除 `0`。
- 更新频率：每周五 15:00（Asia/Hong_Kong）；revision 未变化时不重写资料。

## 2. 阅读入口

- [游戏与场次经济](./Waje配置资料/游戏与场次经济.md)：用于统一游戏、供应商、玩法、场次、下注档位、显隐与推荐逻辑，并与游戏维表、下注和结算事实表核对。
- [数值与生命周期](./Waje配置资料/数值与生命周期.md)：用于追踪生命周期、PR、预期回报、奖池、盈利控制和熔断配置；实际 RTP 仍以服务端结算事实为准。
- [任务运营与商业化](./Waje配置资料/任务运营与商业化.md)：用于拆解新手任务、日常任务、弹窗、活动、福利和触达机制，并映射曝光、领取、完成与转化事件。
- [支付提现与风控](./Waje配置资料/支付提现与风控.md)：用于理解充值、商城、提现、KYC、审核和反作弊配置；支付与资产结论以订单、审核和资产流水事实表为准。
- [版本分包与平台配置](./Waje配置资料/版本分包与平台配置.md)：用于维护 H5、Android、iOS、分包、货币、客户端能力和历史版本的配置脉络。

## 3. 本周变更摘要

| 工作表 | 新增 | 修改 | 删除 |
| --- | ---: | ---: | ---: |
| 有效期Chip场景和配置 | 94 | 0 | 0 |
| 轻量游戏Tower(9013) | 238 | 0 | 0 |

## 4. 全部工作表目录

| # | 工作表 | 专题 | 可见性 | 证据状态 | 配置项 |
| ---: | --- | --- | --- | --- | ---: |
| 1 | 各个游戏配置  | 游戏与场次经济 | 可见 | `current_candidate` | 559 |
| 2 | 弹窗队列(老版) | 任务运营与商业化 | 隐藏 | `historical_reference` | 374 |
| 3 | 新包充值体系（老表作废） | 支付提现与风控 | 隐藏 | `obsolete` | 1095 |
| 4 | spribe游戏 | 游戏与场次经济 | 隐藏 | `historical_reference` | 83 |
| 5 | omg游戏 | 游戏与场次经济 | 隐藏 | `historical_reference` | 1873 |
| 6 | pg游戏 | 游戏与场次经济 | 隐藏 | `historical_reference` | 549 |
| 7 | 五张牌 | 游戏与场次经济 | 隐藏 | `historical_reference` | 150 |
| 8 | 大r礼包 | 支付提现与风控 | 隐藏 | `historical_reference` | 229 |
| 9 | 拼奈拉 | 游戏与场次经济 | 隐藏 | `historical_reference` | 964 |
| 10 | 21点 | 游戏与场次经济 | 隐藏 | `historical_reference` | 107 |
| 11 | 匹配时长、反作弊 | 支付提现与风控 | 可见 | `current_candidate` | 26 |
| 12 | 个人盈利控制 | 数值与生命周期 | 可见 | `current_candidate` | 131 |
| 13 | 新包破产保护（V1老玩家） | 数值与生命周期 | 可见 | `historical_reference` | 914 |
| 14 | 百人whot数值 | 游戏与场次经济 | 隐藏 | `historical_reference` | 357 |
| 15 | 外接游戏下注列表 | 游戏与场次经济 | 隐藏 | `historical_reference` | 539 |
| 16 | tada游戏 | 游戏与场次经济 | 隐藏 | `historical_reference` | 1517 |
| 17 | 熔断和必不中 | 数值与生命周期 | 可见 | `current_candidate` | 101 |
| 18 | 分享裂变数值 | 任务运营与商业化 | 隐藏 | `historical_reference` | 45 |
| 19 | 分包分配置 | 版本分包与平台配置 | 可见 | `current_candidate` | 26 |
| 20 | cash上限帽子 | 游戏与场次经济 | 可见 | `current_candidate` | 133 |
| 21 | 免费玩家玩免费游戏 | 游戏与场次经济 | 可见 | `current_candidate` | 65 |
| 22 | 商城、礼包充值 | 支付提现与风控 | 可见 | `current_candidate` | 427 |
| 23 | 商城礼包充值（26年3月18版） | 支付提现与风控 | 可见 | `historical_reference` | 667 |
| 24 | 档位白名单 | 版本分包与平台配置 | 可见 | `current_candidate` | 18 |
| 25 | 新包生命周期 | 数值与生命周期 | 可见 | `current_candidate` | 101 |
| 26 | pr数值（V2） | 数值与生命周期 | 可见 | `current_candidate` | 4212 |
| 27 | 7日任务 | 任务运营与商业化 | 可见 | `current_candidate` | 450 |
| 28 | 每日、终身任务 | 任务运营与商业化 | 可见 | `current_candidate` | 109 |
| 29 | 弹窗队列 | 任务运营与商业化 | 可见 | `current_candidate` | 512 |
| 30 | 游戏bet场次显隐等配置 | 游戏与场次经济 | 可见 | `current_candidate` | 1027 |
| 31 | 游戏顺序 | 游戏与场次经济 | 可见 | `current_candidate` | 1167 |
| 32 | 新包betlist | 游戏与场次经济 | 可见 | `current_candidate` | 401 |
| 33 | tc报警 | 版本分包与平台配置 | 可见 | `current_candidate` | 274 |
| 34 | led | 任务运营与商业化 | 可见 | `current_candidate` | 512 |
| 35 | 刷子 | 支付提现与风控 | 可见 | `current_candidate` | 29 |
| 36 | 支付跳转 | 支付提现与风控 | 可见 | `current_candidate` | 20 |
| 37 | h5-商城、礼包充值 | 支付提现与风控 | 可见 | `current_candidate` | 80 |
| 38 | TX审核、zrxzrisk、sbsz | 支付提现与风控 | 可见 | `current_candidate` | 338 |
| 39 | kyc上线放松 | 支付提现与风控 | 可见 | `current_candidate` | 102 |
| 40 | 外接游戏权限 | 游戏与场次经济 | 可见 | `current_candidate` | 32 |
| 41 | h5 led数值 | 任务运营与商业化 | 可见 | `current_candidate` | 6 |
| 42 | H5相关配置 | 版本分包与平台配置 | 可见 | `current_candidate` | 10 |
| 43 | 发财金 | 数值与生命周期 | 可见 | `current_candidate` | 36 |
| 44 | H5 2.0.6 | 版本分包与平台配置 | 可见 | `historical_reference` | 80 |
| 45 | H5 2.0.7 | 版本分包与平台配置 | 可见 | `historical_reference` | 74 |
| 46 | 圣诞节 | 版本分包与平台配置 | 可见 | `historical_reference` | 832 |
| 47 | APP2.11.2版本配置 | 版本分包与平台配置 | 可见 | `historical_reference` | 321 |
| 48 | H5  2.0.8版本配置 | 版本分包与平台配置 | 可见 | `historical_reference` | 33 |
| 49 | Ios 2.11.2版本配置 | 版本分包与平台配置 | 可见 | `historical_reference` | 40 |
| 50 | H5  2.0.9版本配置 | 版本分包与平台配置 | 可见 | `historical_reference` | 84 |
| 51 | H5  2.1.0版本配置 | 版本分包与平台配置 | 可见 | `historical_reference` | 141 |
| 52 | H5  2.1.2版本配置 | 版本分包与平台配置 | 可见 | `historical_reference` | 90 |
| 53 | H5  2.1.3版本配置 | 版本分包与平台配置 | 可见 | `historical_reference` | 106 |
| 54 | 体彩（H5  2.1.4）配置 | 游戏与场次经济 | 可见 | `historical_reference` | 570 |
| 55 | TX相关 | 支付提现与风控 | 可见 | `current_candidate` | 128 |
| 56 | 新货币配置 | 版本分包与平台配置 | 可见 | `current_candidate` | 283 |
| 57 | 金币配置 | 版本分包与平台配置 | 可见 | `current_candidate` | 128 |
| 58 | H5金币场和新帐单配置 | 版本分包与平台配置 | 可见 | `current_candidate` | 117 |
| 59 | H5  2.1.7版本配置 | 版本分包与平台配置 | 可见 | `historical_reference` | 30 |
| 60 | APP2.13.0和H5 2.1.8版本配置 | 版本分包与平台配置 | 可见 | `historical_reference` | 76 |
| 61 | 新增config8 | 版本分包与平台配置 | 可见 | `current_candidate` | 17 |
| 62 | 轻量游戏相关配置 | 游戏与场次经济 | 可见 | `current_candidate` | 189 |
| 63 | kyc认证 | 支付提现与风控 | 可见 | `current_candidate` | 176 |
| 64 | 人脸识别配置 | 支付提现与风控 | 可见 | `current_candidate` | 50 |
| 65 | 轻量游戏配置_Limbo | 游戏与场次经济 | 可见 | `current_candidate` | 150 |
| 66 | 轻量游戏配置_通用 | 游戏与场次经济 | 可见 | `current_candidate` | 150 |
| 67 | 轻量游戏Tower(9013) | 游戏与场次经济 | 可见 | `current_candidate` | 238 |
| 68 | 2.18.0配置（三端） | 版本分包与平台配置 | 可见 | `current_candidate` | 73 |
| 69 | 有效期Chip场景和配置 | 版本分包与平台配置 | 可见 | `current_candidate` | 94 |

## 5. 使用边界

- `new_current_primary` 是当前新包分析主源；`old_historical_reference`、`historical_release` 与 `obsolete` 仅用于机制和版本演进参考。
- 任何配置数值必须同时核对适用游戏、包、端、版本和生效窗口；工作簿未提供服务端命中证据时，统一标为 `current_candidate`。
- 完整结构化索引（含每项来源单元格、配置键、规范值和哈希）见 [configuration-index.json](../../data/processed/waje_config/current/configuration-index.json)；项目内不保存整表原始快照。

## 6. 关联资料

- [[Waje新老包游戏记录与数值设定资料库-2026-08-13]]
- [[风控数值与机器人机制拆解-2026-08-12]]
- [[Waje全链路数据需求与埋点设计总表-2026-08-11]]
