# Waje 多端设备、性能、事件与会话看板 V1

## 当前执行状态

- BigQuery 目标项目：`wajenigeria`，区域：`europe-west4`。
- 目标聚合数据集：`waje_device_performance_mart`。
- 2026-08-27 远端创建结果：`blocked_iam`。企业账号 `robin@afuruika.net` 缺少 `bigquery.datasets.create`，因此尚未创建数据集、聚合表、授权视图或定时任务。
- Metabase 远端创建结果：`blocked_metabase_write_access`。当前工作区没有 Metabase URL、SSO 会话、API 身份或可调用管理接口，不能安全创建远端 Collection、Model、Saved Question 或 Dashboard。
- 本目录包含可复跑 SQL、Dashboard 合同、Metabase 手工配置册、实际数据基线与验收清单；在补齐权限后按 `sql/` 编号顺序执行。
- `dashboard_preview.html` 是新版窄屏友好阅读入口；`report_v2.html` 是指标/算法报表；`dashboard_preview_legacy.html` 仅保留旧版标准阅读器作历史对照。
- `design_spec_v2.html` 是按《设备监控及性能优化指标系统开发需求》重做的详细设计阅读版：包含 8 个看板页面、三端适用性、筛选器、指标定义/分母/算法、样式线框、报表节奏和埋点缺口；`design_spec_v2.json` 是其结构化索引。
- 对应 Markdown 设计文档：`knowledge/02-数据/Waje多端设备性能报表看板详细设计V2-2026-08-27.md`。

## 已实际核验的数据基线

所有数值均为只读聚合，时间按 `Africa/Lagos` 解释。

| 数据域 | 当前覆盖 | 结论 |
|---|---|---|
| Android Analytics | `events_20260824`，三个生产包 | 只有一个完整日；行为事件可用但趋势未成熟 |
| Android Performance | 三包均为 2026-08-20 至 26 | 主包 7,106,698 条、传音新包 3,886,596 条、传音老包 4,473,554 条性能记录 |
| Android Sessions | 三包为 2026-08-18 至 26 | 去标识化会话数：301,471 / 108,193 / 125,526 |
| Android Crashlytics | 三包为 2026-08-13 至 26 | 导出记录数：53,212 / 3,647 / 6,066；不是崩溃率 |
| iOS Analytics | 2026-08-20 至 24 | 5 个数据日，未达到 7 日跨端趋势门槛 |
| iOS Performance | 2026-08-20 至 25 | 2,452,741 条性能记录，2 个版本 |
| H5 Firebase Analytics | 2026-08-14 至 21 | 仅 `page_view`、`session_start`、`first_visit`、`user_engagement` 四类标准事件 |

## 重要数据质量边界

- Android Performance 表已有实际记录，但 Android Sessions 表中 `performance_data_collection_enabled` 聚合为 `false`。将其记录为数据质量冲突，不能据此判断 Performance 未接入。
- Android/iOS Firebase Analytics 的 `session_start` 是事件数，不能与 Android Sessions 的 `COUNT(DISTINCT session_id)` 混称为同一个会话指标。
- H5 当前没有 Web Vitals、路由 ready、核心请求时延、前端错误、白/黑屏、游戏就绪或可下注事件；所有 H5 性能/核心漏斗指标必须显示 `data_gap` 或 `blocked`。
- Crashlytics 导出记录数不等于 Fatal、ANR、Non-fatal 或受影响用户数；稳定性指标在字段、去重键和会话分母核验前保持 `provisional`。

## 部署顺序

1. 管理员向目标执行身份授予 `bigquery.datasets.create`，或预先创建 `waje_device_performance_mart`（`europe-west4`）。
2. 执行 `sql/00_create_dataset.sql` 至 `sql/10_create_metabase_rank_view.sql`；每个数据刷新 SQL 先 `--dry_run`，再执行。
3. 创建两类计划任务：D+1 聚合刷新与 15 分钟原生性能新鲜度诊断。计划任务 SQL 在 `sql/12_scheduled_query_commands.md`。
4. 由 Metabase 管理员授予 `Waje / Device & Performance / V1` Collection Curate 与该聚合数据集的只读查询权限；禁止连接 Firebase/Origin 原始表。
5. 按 `metabase_configuration_guide.md` 创建四页 Dashboard，并执行 `sql/11_quality_checks.sql`。

## 安全约束

所有新对象只输出脱敏聚合。禁止写入或展示用户标识、设备标识、完整 URL、请求/响应正文、订单、支付明细、错误堆栈或 Cookie/Token。
