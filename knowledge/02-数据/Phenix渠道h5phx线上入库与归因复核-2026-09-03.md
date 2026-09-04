# Phenix 渠道 h5phx（p=h5phx）线上入库与归因复核

> 修正版审计日期：2026-09-03。完整日窗口：2026-08-27 至 2026-09-01；9 月 2/3 的 intraday 不纳入比较。

## 一、结论先行

**`p=h5phx` 在 Firebase H5 原始入库中确实存在；问题不是 Phenix 流量完全没有进入 Firebase，而是该标记没有被稳定标准化为 Origin 的 `h5phx` 渠道。**

上一轮只检查独立字段和独立参数键，因此得到“Phenix 命中 0”。本轮改为搜索 URL 字符串中的 `p=h5phx` 后，发现它主要位于 `page_location`，也出现在 `page_referrer` / `form_destination`；Firebase 中独立参数键名为 `p` 的记录仍为 0。

| 数据集 | 完整日 | page_location 命中事件 | first_visit 命中事件 | first_visit 命中主体（约） | direct/(none) 命中事件 | 付费媒介命中事件 | 独立 p 键 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| analytics_504208609 | 2026-08-28～09-01 | 859 | 32 | 29 | 188 | 663 | 0 |
| analytics_517134955 | 2026-08-28～09-01 | 62,231 | 18,777 | 18,266 | 61,686 | 377 | 0 |
| waje_ng_firebase_h5 | 2026-08-27 | 1,054 | 305 | 294 | 1,050 | 4 | 0 |

## 二、这说明什么

1. **Firebase 已收到 Phenix 标记。** `analytics_517134955` 在 8/28–9/1 有 62,231 个 `page_location` 标记命中事件，首次访问命中事件 18,777 个，命中主体约 18,266 个。
2. **Firebase 的首触归因没有自动变成 h5phx。** `analytics_517134955` 的标记命中事件中，61,686 个仍被归为 `(direct) / (none)`；这会把 Phenix 流量混入直接访问/自然流量。
3. **不同 Firebase 数据集的表现不一致。** `analytics_504208609` 的标记命中事件中有 663 个落在付费媒介，说明数据流、站点或归因规则之间可能存在差异，不能跨数据集直接合并。
4. **当前不能把 `p=h5phx` 直接当成付费投放事实。** 它证明链接参数存在，但还需要确认参数由哪一类投放链路生成，以及是否与注册、首次付费、成本事实一致。

### 2.1 命中参数键

| 数据集 | URL 字符串中命中的参数键及次数 |
| --- | --- |
| analytics_504208609 | page_location: 841, page_referrer: 124, form_destination: 19 |
| analytics_517134955 | page_location: 62,194, page_referrer: 281 |
| waje_ng_firebase_h5 | page_location: 1,050 |

### 2.2 首次访问的来源分类

| 数据集 | first_visit 命中的首触来源/媒介 |
| --- | --- |
| analytics_504208609 | (direct) / (none): 32 |
| analytics_517134955 | (direct) / (none): 18,756, m.facebook.com / referral: 45 |
| waje_ng_firebase_h5 | (direct) / (none): 305 |

## 三、Origin 侧再次核验

| 检查项 | 结果 | 判断 |
| --- | --- | --- |
| Origin 实时 H5 p=h5phx URL 标记 | 0 | 当前实时 H5 没有保留该标记 |
| Origin 实时 H5 任意 h5phx/phenix 标记 | 0 | 没有观察到标准化后的渠道标记 |
| Origin UTM source/medium/campaign=h5phx | 0 / 0 / 0 | 没有进入 UTM 字段 |
| Origin 归因变更值=h5phx | 0 | 归因变更表也没有该值 |
| Origin user_events 视图 download_channel=h5phx | no_data | 本窗口没有返回记录 |
| 90006 渠道聚合表 download_channel=h5phx | no_data | 表最新日期早于当前窗口，不能用空结果下业务结论 |

Origin 实时 H5 本窗口有约 22,112,231 条行为事件，但会话键缺失 100.00%，事件键缺失约 24.10%。

## 四、对付费率和留存异常的影响

| 层面 | 当前证据 | 可下的结论 |
| --- | --- | --- |
| 渠道归因 | Firebase 能找到 p=h5phx，但 Origin H5 和渠道视图找不到 h5phx | 归因映射/透传存在问题，优先级 P0 |
| 报表分母 | 本地明细表和截图的付费率分母不同 | 付费率差异不能直接解释为人群差异 |
| 留存信号 | Phenix 成熟 D1 5.04%，自然对照 30.71% | 方向性差异仍存在，但需先完成渠道归因和源表刷新 |
| 事件是否全部丢失 | Firebase 有 p 标记和标准行为事件，Origin 有 H5 行为事件 | 没有证据证明全链路事件全部丢失；更像链路字段未统一 |

本次结果把之前的结论修正为：**Phenix 访问标记在 Firebase 层存在，但下游报表没有把它识别为 h5phx。** 如果 `p=h5phx` 是约定的渠道参数，那么报表中的“自然/无渠道 ID”和异常低付费/留存，很可能包含归因丢失或渠道混入；但参数本身还不能证明每个命中主体都是付费投放用户。

## 五、整改顺序

### P0：修复归因链路

1. 明确规定 `p=h5phx` 为标准渠道参数，在首次访问时解析并写入统一渠道字段 `h5phx`；同时保留原始参数来源类型。
2. 让 Origin H5 PV/PD/MV/MC/AQ/AL 和 Firebase `page_location` 使用同一渠道映射；不能只依赖 `utm_source`。
3. 补齐 H5 会话键和事件键，验证 `p=h5phx → 注册 → 首次付费 → D1/D3/D7` 的脱敏聚合链路。
4. 确认当前报表实际 SQL/视图；不要继续使用最新只到 2026-05-31 或 2025-04-30 的旧聚合表复核 8/27–9/2。

### P1：归因修复后再判断人群

- 用统一 `h5phx` 渠道与 Google、Facebook、自然流量做同分母、同成熟窗口比较。
- 将 p 标记命中但未进入 Origin 的数量作为渠道链路完整率监控。
- 分开展示 Firebase 原始标记、Origin 标准渠道、付费事实和留存事实，避免用一个字段替代四层事实。

## 六、执行回执与来源

- 精确渠道审计：26/26 个作业成功或按预期为空，dry-run 约 5.46 GiB。
- Firebase 命中明细：3/3 个作业成功，dry-run 约 1.33 GiB。
- Firebase 命中汇总：3/3 个作业成功，dry-run 约 1.33 GiB。
- 所有查询均为只读聚合；没有保存 URL 值、参数值、用户明细、设备标识、支付明细、凭据或令牌。
- 最终状态：**Share with caveats / provisional**。

> 来源快照、SQL hash 和作业回执保存在 `analysis/phenix_h5phx_audit_2026_09_03/`。
