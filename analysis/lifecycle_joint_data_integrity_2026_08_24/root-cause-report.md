# 生命周期数据重复值根因审计

## 结论

当前证据将 Hilo、Plinko 标记为 `data_static_suspect`。这表示其跨日实体级导出值存在完整重复，**不等于**羊毛、机器人、无用户、RTP 异常或系统故障。对 Hilo/Plinko 的日趋势、稳定回报或用户行为解释应暂停，直至独立复查完成。

## 原始文件全量检查

- 计划文件数：24；实际通过解析文件数：24；全量原始审计状态：`passed`。
- 每日均检查了表头、行数、主键唯一性、生命周期覆盖和四表下注额/盈利/回报比勾稽。
- 所有日期的整表二进制哈希及标准化内容指纹均保存在 `raw-audit.json`，避免把“某游戏静态”误判为整份导出缓存。

## 跨日实体指纹

- Hilo：2026-08-18 → 2026-08-19 分游戏=missing_entity，明细=missing_entity。
- Plinko：2026-08-18 → 2026-08-19 分游戏=missing_entity，明细=missing_entity。
- Hilo：2026-08-19 → 2026-08-20 分游戏=missing_entity，明细=missing_entity。
- Plinko：2026-08-19 → 2026-08-20 分游戏=missing_entity，明细=missing_entity。
- Hilo：2026-08-20 → 2026-08-21 分游戏=new_entity，明细=new_entity。
- Plinko：2026-08-20 → 2026-08-21 分游戏=new_entity，明细=new_entity。
- Hilo：2026-08-21 → 2026-08-22 的分游戏行和全部生命周期明细行均为全字段同指纹。
- Plinko：2026-08-21 → 2026-08-22 分游戏=changed，明细=changed。
- Hilo：2026-08-22 → 2026-08-23 的分游戏行和全部生命周期明细行均为全字段同指纹。
- Plinko：2026-08-22 → 2026-08-23 的分游戏行和全部生命周期明细行均为全字段同指纹。

### 整体快照是否重复

- 2026-08-18 → 2026-08-19：整表内容变化的区块为 summary, detail, game, active。
- 2026-08-19 → 2026-08-20：整表内容变化的区块为 summary, detail, game, active。
- 2026-08-20 → 2026-08-21：整表内容变化的区块为 summary, detail, game, active。
- 2026-08-21 → 2026-08-22：整表内容变化的区块为 summary, detail, game, active。
- 2026-08-22 → 2026-08-23：整表内容变化的区块为 summary, detail, game, active。

因此，若整体快照/其他游戏仍变化而某个新游戏持续静态，优先归类为**实体级源数据静态信号**，不是 HTML 渲染缓存或飞书批量写入的直接证据。

## 飞书写入层复核

- 首次源数据→待写入载荷比对状态：`passed`。
- 既有在线回读验证由 2026-08-24 更新回执保留；本次审计不修改飞书。
- 当前策略：只有独立复查导出显示首次查询值不同，才冻结相关结论并提出更正清单；在数据拥有方复核前不覆盖飞书历史。

## 独立复查状态

- 当前分类：`source_query_mismatch`。
- All independent source exports differ from the first query. This is consistent with an incomplete/unstable first snapshot or historical-source reprocessing; it is not evidence of player behavior. Do not overwrite Lark until the data owner resolves the source snapshot state.

- 2026-08-21：活跃生命周期行数 4 → 11；Hilo 基础下注额 11,800.00 → 314,505.83；Plinko 基础下注额 263,687.35 → 1,647,277.32。
- 2026-08-22：活跃生命周期行数 4 → 11；Hilo 基础下注额 11,800.00 → 159,587.34；Plinko 基础下注额 263,805.35 → 1,228,927.62。
- 2026-08-23：活跃生命周期行数 4 → 11；Hilo 基础下注额 11,800.00 → 133,075.08；Plinko 基础下注额 263,805.35 → 1,087,055.08。

独立查询的日期控件均已回读为目标日期，且四类导出均通过表头/主键/勾稽校验。首次与复查在三日、四表均不一致，因此**原先报告的数值不能继续用作业务分析依据**。最可能的流程缺口是首次采集只凭行数可用即导出，没有等待查询结果的值指纹稳定；“上游历史聚合在两次查询之间重处理”仍是待数据拥有方确认的替代解释。

- 独立复查 2026-08-21 → 2026-08-22：Hilo=changed/changed；Plinko=changed/changed。
- 独立复查 2026-08-22 → 2026-08-23：Hilo=changed/changed；Plinko=changed/changed。

独立复查中若 Hilo/Plinko 的实体指纹跨日已变动，说明初始快照中的“跨日完全相同”不能作为当前产品行为事实，也不能继续用于回报或羊毛判断。

## 可能原因与不可下结论的边界

1. 新游戏在所选日期没有新增有效局，或新增局未进入该生命周期聚合。
2. Provider/game-id 映射、生命周期聚合、跨日结算、免费/测试局或风险排除存在延迟/静态快照。
3. 首轮查询的日期关联或下载关联错误；只有独立复查返回不同值时，才把这一项升级为 `source_query_mismatch`。

现有聚合数据没有用户、订单、设备、IP、局号、机器人标识、规则命中或结算状态。因此本报告不得把重复值归因为羊毛或任何具体用户行为。

## 建议的强制门禁

新游戏上线后前 7 天，在报告生成前比较 `date×game` 与 `date×lifecycle×game` 的相邻日期全字段指纹。若整体数据变化、目标新游戏却保持静态，则：

1. 设为 `data_static_suspect`；
2. 禁止使用该实体构建日趋势、产品表现、RTP 或羊毛结论；
3. 保存“选择日期 → 查询时间 → 返回行数 → 导出哈希”回执；
4. 先执行独立复查，再决定是否需要更正飞书数据。
