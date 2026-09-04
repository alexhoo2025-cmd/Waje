# Android Firebase BigQuery 导出筛选审计工件

## 用途

本目录保存 2026-08-31 基于本地知识库的 Android Firebase Analytics 导出降量审计结果、事件处理矩阵、下游字段投影矩阵和只读验证 SQL。它不包含业务数据行、用户标识、参数值、凭据或 Firebase 控制台导出设置回执。

## 工件

- `event_filter_matrix.json`：事件保留、排除候选、二选一和待核对矩阵。
- `field_projection_matrix.json`：GA4 标准字段在安全聚合视图中的保留、限制、裁剪和排除规则。
- `sql/00_event_volume_by_package.sql`：按日、包体、版本和事件聚合事件量。
- `sql/01_event_policy_coverage.sql`：按策略分组比较事件量。
- `sql/02_parameter_presence_guard.sql`：只返回参数/受限 key 候选数量，不返回原始 key 或值。
- `sql/03_instance_schema_check.sql`：`INFORMATION_SCHEMA` 元数据核验。
- `run-receipt.json`：本轮证据边界、覆盖状态和未执行的实时查询说明。

## 运行边界

- 当前 SQL 中 `wajenigeria.waje_ng_firebase_android.events_*` 是历史准备包中的候选路径，不是本轮已验证实例表。
- 2026-08-27 BigQuery API 实时验证因认证阻断，以上 SQL 只完成静态准备，不代表已经执行。
- Firebase 控制台的事件排除需要人工核对完整列表、关键事件、受众和下游依赖后分批实施；本工件不执行远程配置修改。
