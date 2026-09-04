# Phenix 线上 BigQuery 归因与跨渠道上报审计

> 审计窗口：2026-08-27 至 2026-09-01（完整日）；2026-09-02 为进行中数据，不纳入横向比较。审计对象：Phenix 浏览器分包 `wajeh5phx` 的 Origin 聚合现象与企业 BigQuery 入库链路。

## 一、结论先行

**当前优先修复归因、源表刷新和 H5 会话链路，不应先把低留存定性为投放人群质量问题。**

| 判断 | 线上证据 | 结论 |
| --- | --- | --- |
| Phenix 是否进入 Firebase BigQuery | 5 个可见 Firebase 数据集、487 个聚合组中标识命中 0 次 | 未观察到 Phenix 可分配记录 |
| 其他渠道是否能归因 | H5 侧观察到 `google / cpc`、`fb / paid`、`an / paid` 和 referral | 其他渠道可以进入 Firebase 归因字段 |
| Origin H5 是否有事件 | 实时表约 22,112,231 条 PV/PD/MV/MC/AQ/AL | 事件能到达，但归因和会话链路不完整 |
| Origin H5 是否有渠道归因 | UTM source/medium/campaign 计数均为 0；会话键缺失 100.00% | 当前 H5 实时表不能支撑稳定渠道归因和会话串联 |
| Origin 报表源表是否覆盖本窗口 | 渠道表最新 2026-05-31；留存表最新 2025-04-30 | 当前可见聚合表无法复核 8/27–9/2 |
| 低留存是否已证明是人群问题 | 成熟 D1 5.04%，自然对照 30.71% | 存在方向性差异，暂不能做因果判断 |

## 二、审计方法与证据边界

本轮通过企业 BigQuery API 执行只读聚合；先做 SQL 策略校验和 dry-run，再执行。未读取或保存用户明细、设备唯一标识、支付金额明细、原始 URL、原始参数值、凭据或令牌。小于 10 个匿名主体的渠道组不进入结果。

Firebase 使用完整日表；9 月 2 日的 intraday 表仅盘点存在性，不与完整日混算。不同 Firebase 数据集独立展示，不跨数据集相加。

## 三、Firebase BigQuery 跨渠道结果

| 数据集 | 平台/对象 | 完整日表 | 表行数 | 聚合覆盖 | 业务事件候选 | Phenix 命中 |
| --- | --- | --- | --- | --- | --- | --- |
| analytics_470712959 | ANDROID | 6 | 9,780,301 | 100.00% | 1,589,474 | 0 |
| analytics_504208609 | WEB | 5 | 809,332 | 99.63% | 18,844 | 0 |
| analytics_517134955 | WEB | 5 | 2,071,655 | 99.82% | 0 | 0 |
| analytics_546634805 | IOS | 5 | 789,097 | 99.90% | 249,172 | 0 |
| waje_ng_firebase_h5 | WEB | 1 | 771,647 | 99.87% | 0 | 0 |

### 3.1 H5 其他渠道对照

以下是事件层结果，不是 Origin 新增用户或付费事实。`first_visit` 只用于判断渠道是否能进入 Firebase 入库。

| H5 数据集/站点 | 渠道组 | 事件数 | first_visit 事件数 | 解释 |
| --- | --- | --- | --- | --- |
| analytics_517134955 / www.wajegame.com | google / organic | 167,252 | 7,398 | 其他渠道可见；Phenix 未命中 |
| analytics_517134955 / www.wajegame.com | fb / paid | 136,470 | 22,521 | 其他渠道可见；Phenix 未命中 |
| analytics_517134955 / www.wajegame.com | google / cpc | 69,836 | 996 | 其他渠道可见；Phenix 未命中 |
| analytics_517134955 / www.wajegame.com | an / paid | 49,663 | 11,005 | 其他渠道可见；Phenix 未命中 |
| analytics_517134955 / www.wajegame.com | waje.bet / referral | 26,764 | 1,094 | 其他渠道可见；Phenix 未命中 |
| analytics_517134955 / www.wajegame.com | l.facebook.com / referral | 15,622 | 1,620 | 其他渠道可见；Phenix 未命中 |
| analytics_517134955 / www.wajegame.com | waje-game.com / referral | 10,679 | 164 | 其他渠道可见；Phenix 未命中 |
| analytics_517134955 / www.wajegame.com | waje-special.com / referral | 5,964 | 197 | 其他渠道可见；Phenix 未命中 |
| analytics_517134955 / www.wajegame.com | m.facebook.com / referral | 5,885 | 1,014 | 其他渠道可见；Phenix 未命中 |
| analytics_517134955 / www.wajegame.com | Data Not Available / Data Not Available | 3,933 | 63 | 其他渠道可见；Phenix 未命中 |
| analytics_517134955 / www.wajegame.com | ig / paid | 3,461 | 806 | 其他渠道可见；Phenix 未命中 |
| analytics_517134955 / www.wajegame.com | bing / organic | 2,384 | 110 | 其他渠道可见；Phenix 未命中 |
| analytics_517134955 / www.wajegame.com | googleads.g.doubleclick.net / referral | 1,704 | 440 | 其他渠道可见；Phenix 未命中 |
| analytics_517134955 / www.wajegame.com | facebook.com / referral | 1,561 | 287 | 其他渠道可见；Phenix 未命中 |

Android 侧能观察到 Google Play Organic、Google CPC 和 Facebook 来源；iOS 侧能观察到 Google CPC 与 Facebook Paid。这说明 Firebase 的来源字段并非全部失效，但不能证明 Phenix 已正确归因。

### 3.2 Firebase 侧问题定位

- 当前完整日聚合中没有观察到 `wajeh5phx`、`waje5phx` 或 `phenix` 标识。
- H5 其他渠道可被分组，而 Phenix 不出现，优先怀疑 Phenix 落地页、包体或 UTM 映射未透传，或 Phenix 数据进入了未盘点的 Firebase 数据流。
- H5 Firebase 数据集之间的业务事件覆盖不一致：有的数据集出现付费类事件名候选，有的数据集只有页面/会话事件，不能直接把 Firebase 事件量当作付费人数。

## 四、Origin 线上实时 H5 表

| 检查项 | 结果 | 影响 |
| --- | --- | --- |
| 事件类型 | PV: 9,262,415；AL: 3,777,666；PD: 3,893,957；MC: 3,530,050；AQ: 1,550,534；MV: 97,609 | PV/PD/MV/MC/AQ/AL 到达 |
| UTM source / medium / campaign | 0 / 0 / 0 | 没有可用的 H5 UTM 归因 |
| 会话键缺失 | 100.00% | 无法稳定做访问→注册→付费串联 |
| 事件键缺失 | 24.10% | 部分事件无法事件级去重 |
| Phenix 标识 | 0 | 当前字段/窗口未发现 Phenix |

Origin 实时 H5 表与 Firebase H5 表的共同点是：有行为事件，但没有稳定的 Phenix 归因证据。APP 实时客户端表则能看到包体、包渠道和子渠道，说明 APP 侧渠道维度更完整；APP 结果不能替代 H5 验证。

## 五、报表源表与线上数据刷新

| 源表 | 最早日期 | 最新日期 | 8/27–9/2 是否有返回 |
| --- | --- | --- | --- |
| campaign_conversion_cost | 2024-01-01 | 2026-05-31 | 否 |
| daily_new_user_retention | 2024-01-01 | 2025-04-30 | 否 |
| first_pay_retention | 2024-01-21 | 2025-04-30 | 否 |

`90006.campaign_conversion_cost` 最新到 2026-05-31；`bigdata.daily_new_user_retention` 和 `bigdata.first_pay_retention` 最新到 2025-04-30。两类表在本窗口返回空，不能把空结果解释为“没有付费”或“没有留存”。截图数据应来自尚未同步到这些表的其他源，或另一个报表模型。

本地 Origin 导出显示：Phenix 7 个日期行，新增用户 21,945，新增付费 154，媒体为自然/无渠道 ID，消耗为 0；成熟 D1 约 5.04%，自然对照约 30.71%。这些是报表现象和方向性对照，不是线上 BigQuery 已独立复算的结果。

## 六、根因判断

| 可能原因 | 状态 | 优先级 | 确认动作 |
| --- | --- | --- | --- |
| Phenix 未透传包体/渠道/UTM | 已观察；其他渠道可见，Phenix 未命中 | P0 | 测试访问贯穿落地页→Origin→Firebase |
| 报表源表过期或报表使用了其他模型 | 已确认源表无本窗口数据 | P0 | 回读线上报表实际 SQL/视图/刷新作业 |
| H5 会话键缺失 | 已观察；缺失 100.00% | P0 | 统一会话/访问键并验证去重 |
| 付费率分母不一致 | 已确认；本地明细与截图比例使用不同分母 | P0 | 同时展示分子、分母和命名 |
| Phenix 人群质量偏弱 | 方向性信号，需归因清洗后确认 | P1 | 同源按设备、版本、落地页分层 |
| 留存事件全链路丢失 | 尚未证实；当前 cohort 源表无本窗口数据 | P1 | 补脱敏 cohort 事实并重算 D1/D3/D7 |

## 七、整改建议

### P0

1. 统一 Phenix 渠道编码为 `wajeh5phx`，建立 UTM、包体、落地页和报表渠道的映射。
2. 为 H5 PV/PD/MV/MC/AQ/AL 补齐统一会话键和事件键。
3. 恢复当前日期的渠道事实与留存 cohort 事实，明确报表实际来源。
4. 统一新增用户付费率与激活注册用户付费率的口径；观察窗口未结束的数据不显示 0%。

### P1

1. 归因修复后，使用相同来源、相同分母比较 Phenix、Google、Facebook、自然流量的注册、首付和 D1/D3/D7。
2. 补齐 `H5_GAME_LOAD → H5_GAME_READY → H5_BET_READY → GAMESTART → GAMEEND → 结算`，区分人群问题和游戏体验问题。
3. 建立原始事件→Origin 聚合→看板的日级对账，覆盖行数、事件类型、渠道、分母、去重键和迟到数据。

## 八、复现回执

- Firebase：22/22 个聚合作业成功；dry-run 约 4.30 GiB。
- Origin：7/7 个作业成功或按预期为空；dry-run 约 3.78 GiB。
- 数据区域分开执行：`90006` 使用 US，`bigdata` 与 `origin_hfyl` 使用 europe-west4；未执行跨区域联查。
- 未修改 BigQuery、Firebase、Origin、权限、看板或埋点配置。

> 最终状态：**Share with caveats / provisional**。在归因字段打通、源表刷新、会话键补齐和日级对账完成前，不作为投放扩量或正式经营考核依据。
