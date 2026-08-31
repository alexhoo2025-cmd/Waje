# Waje H5轻量化游戏效果分析 V4：数据审计工件

本目录服务于“轻量化游戏是否改善入口、首局、复玩、留存和付费”的数据整理与审计，不重复生产既有新增用户留存/付费分析。

## 工件说明

- `source_registry.json`：数据源优先级、修订号、映射和可访问状态。
- `report_inventory.json`：起源BQ报表与敏捷分析的现场字段审计。
- `data_quality_audit.json`：质量门禁、已知阻断和处理规则。
- `agile_analysis_templates.md`：不保存书签的起源敏捷分析取数模板。
- `source_registry.json`：保留经筛选的轻量化发布、故障和干扰节点；不保留完整更新记录原文。

## 复用而非重复提取

新增用户、留存、付费和C-T基线复用：

`analysis/h5_pwa_lightgame_effect_v2_2026_08_19/analysis.json`

本轮用于修订638结构校验的四份重复新增用户快照已移至废纸篓，未纳入V4数据工件。完整更新记录原文含无关历史敏感文本，也已移至废纸篓；V4仅保留脱敏后的轻量化节点摘要。正式新增用户数据更新仅在用户明确要求刷新时间窗口时，按 `waje-origin-new-user-analysis-update` 的完整八表映射与成熟样本验证执行。

## 当前阻断

1. 起源设备监控查询报 `app_id` 字段歧义，性能归因阻断。
2. 事件中心缺少`game_ready`、`bet_ready`、前端异常、Web Vitals、标准`game_id`和真实版本属性。
3. GA4 H5已具备流量/设备聚合，但不能替代服务端游戏、下注、结算和支付事实。
