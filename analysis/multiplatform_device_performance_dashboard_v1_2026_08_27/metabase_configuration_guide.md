# Metabase 配置册：Waje 多端设备与性能 V1

## 远端权限前置

当前状态：`blocked_metabase_write_access`。

管理员需提供以下最小权限：

1. Collection `Waje / Device & Performance / V1` 的 Curate 权限；
2. 对 `waje_device_performance_mart` 的只读查询、Model 创建与 Schema Sync 权限；
3. 不授予 Firebase、Origin、支付、订单、设备标识或 URL 原始表的访问权限；
4. 使用已登录的浏览器 SSO 或受控短期 API 身份。不要把会话、Token 或密码写入工作区。

## 数据源与 Model

创建以下 Metabase Model，名称保持与 BigQuery View 一致：

- `vw_metabase_endpoint_health`
- `vw_metabase_native_performance`
- `vw_metabase_native_performance_rank`
- `vw_metabase_event_session`
- `vw_metabase_core_funnel`
- `vw_metabase_stability_and_quality`
- `vw_metabase_native_performance_15m`

将 `metric_date_lagos` 设为日期语义；所有百分比字段设为比例格式；`*_p95_ms`、`page_p50_ms`、`page_p99_ms` 设为毫秒；所有 `quality_status` 保持文本状态，不映射为数字。

## 四页 Dashboard 与问题清单

### 01 全端健康与数据可用性

- 数据截止时间：`MAX(data_cutoff_at)`，按端/包展示；
- 完整日覆盖：按 `complete_day` 计数；
- 会话开始事件：仅 `source_name=firebase_analytics`；
- 原生 Performance 记录量：仅 `source_name=firebase_performance`；
- 数据状态：按 `quality_status`、`source_freshness_lag_minutes` 展示。

### 02 Android 与 iOS 原生性能和稳定性

- 轨迹 P95、网络 P95、网络成功率、慢帧、冻结帧；P50/P99 只作为诊断列；
- 版本趋势：按 `metric_date_lagos`、`app_version`；
- 单维度排行：仅使用 `vw_metabase_native_performance_rank`，`rank_dimension` 单选；
- Crashlytics：可展示 Fatal 事件量、Non-fatal 事件量、问题数和导出覆盖，均标记 `provisional_event_dedup_and_denominator`；不得创建 Fatal/ANR/Non-fatal **率**、受影响用户数或无崩溃会话率卡片。

### 03 事件、会话与核心漏斗

- 事件结构：`event_category`；`notification` 单独卡片；
- 行为链路：`session_start`、`page_or_screen_view`、`register_behavior`、`recharge_behavior`；
- 服务端阶段：从 `vw_metabase_core_funnel` 的 `quality_status` 显示 `blocked`，直到 Origin 聚合事实接入。

### 04 设备、版本、网络与 H5 接入差距

- 设备/OS/网络/运营商排行；
- 未知版本、未知网络占比和数据质量状态；
- H5 仅显示 Analytics 行为基线；`h5_web_vitals`、`game_ready_and_bet_ready` 必须显示 `data_gap`/`blocked`。

## 全局筛选器绑定

对每一个 Metabase Card 分别绑定：日期、端、包体、版本、国家、设备、OS、网络、运营商、事件分类、性能轨迹类别、数据状态。H5 无对应维度时应显示“未采集”，不可强制过滤为零。所有排行问题只允许一个 `rank_dimension`。

## 验收

- 每个筛选器改变后至少一张相关卡片结果变化；
- 默认最近 7 个完整 `Africa/Lagos` 自然日；
- Analytics 天数不足 7 天时跨端趋势卡片显示 `immature`；
- 任意源延迟超过 45 分钟时 15 分钟诊断显示 `delayed`，不发送性能结论；
- 任何结果均不含用户、会话、设备、URL、堆栈、订单或支付明细。
