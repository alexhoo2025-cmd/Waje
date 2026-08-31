# GA4 H5 → BigQuery 首次数据审计报告

> 审计时间：2026-08-20  
> 状态：GA4 历史基线已完成；BigQuery 链接已创建，等待首个每日导出表生成。

## 结论

GA4 属性 `504208609`（`wajeH5`）正在稳定采集 H5 Web 行为数据，且已于 2026-08-21 创建到 `waje-analytics-readonly` 的 BigQuery 链接。目标项目处于 US BigQuery Sandbox；链接创建后即时核验仍无数据集，等待 GA4 首次每日导出。

已提交的导出配置：

- 目标项目：`waje-analytics-readonly`
- 区域：US
- 数据流：`wajeH5` Web（ID `12134390945`）
- 事件：全量导出，无排除项
- 模式：仅 Daily；Sandbox 不支持 Streaming
- 用户数据导出：未启用

提交后预期生成数据集 `analytics_504208609` 与每日表 `events_YYYYMMDD`。Sandbox 中的表、视图与分区默认 60 天过期，因此本方案只适用于短期验证与 60 天内审计。

## 90 天 GA4 历史基线

- 属性时区：`Africa/Lagos`
- 数据日期：2026-05-22 至 2026-08-19，共 90 天
- 聚合事件量：12,395,001
- GA4 API 查询状态：成功；未出现阈值限制或 `Other` 数据丢失标记

近 28 天主要生产 Host 为 `www.wajegame.com`：39,468 活跃用户、174,925 会话、4,383,373 事件。流量以移动端为主（38,564 活跃用户）；Android 与 iOS 是主要操作系统。

## 事件覆盖评估

| 能力 | 状态 | 证据 |
|---|---|---|
| 基础访问与归因 | 可直接分析 | `page_view`、`session_start`、`user_engagement` |
| 充值与提现行为 | 可辅助分析 | `recharge`、`withdraw`、`firstcharge` 等聚合事件 |
| 游戏进入与加载 | 缺失需补充 | 未发现 `game_load`、`game_ready`、`game_start` 等事件 |
| 可下注与首注 | 缺失需补充 | 未发现 `bet_ready`、`first_bet`、`place_bet` 等事件 |
| 游戏结算 | 缺失需补充 | 未发现 `settlement`、`game_end`、`round_end` 等事件 |
| 前端异常与恢复 | 缺失需补充 | 未发现 `client_error`、`js_error`、`exception`、`retry` 等事件 |
| Web Vitals / 页面性能 | 缺失需补充 | 未发现 `web_vital`、`fcp`、`lcp`、`inp`、`cls`、`page_load` 等事件 |
| 网络与低端机分层 | 缺失需补充 | 未发现网络、设备等级、内存或性能自定义事件 |
| 版本、渠道与游戏分层 | 缺失需补充 | 未发现可用于该分层的标准化自定义事件 |

这些缺口不代表 H5 没有对应能力，只能说明当前 GA4 聚合事件中未采到可审计的标准事件名称或字段。

## BigQuery 导出审计状态

当前状态为 `pending_first_daily_export`：导出配置已提交，目标 Sandbox 仍尚无数据集。按以下顺序验证：

1. 24 小时内确认 `analytics_504208609` 与首张 `events_YYYYMMDD` 出现。
2. 从稳定至少 3 天的日表检查日期连续性、导出延迟、事件量与事件字典。
3. 使用同一 `Africa/Lagos` 日期边界，比对 GA4 Data API 与 BigQuery 的每日总事件量；差异超过 5% 时排查数据流、事件排除、时区与迟到事件。

可复跑的只读聚合 SQL 位于 [ga4_h5_export_audit.sql](../../analysis/ga4_h5_export_audit_2026_08_20/ga4_h5_export_audit.sql)。GA4 API 原始聚合基线位于 `data/outputs/ga4-h5-readiness/ga4-h5-readiness.json`。

## 数据与隐私边界

本审计只读取和保存聚合结果；不查询或输出用户标识、Cookie、广告标识、交易明细或原始事件行。GA4 的行为事件不能替代认证业务数据中的充值、下注、结算与长期留存口径。
