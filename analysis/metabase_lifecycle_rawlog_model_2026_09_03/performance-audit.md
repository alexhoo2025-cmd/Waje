# Lifecycle V2 Joint 报表性能审计

日期：2026-09-03（Africa/Lagos 业务日口径）

## 已验证事实

- `whot_center.stat_lifecycle_pool_v2_log` 的主键基数约为 4,800,627 行。
- 该表只有单列 `game_type`、`lifecycle`、`pool_type`、`change_type`、`time` 索引；没有 `change_type + data_type + time` 复合索引。
- Model 240 从 2026-08-01 起透视全部符合条件的原始日志，并在每次 Q01—Q05 查询中被作为派生表重复执行。
- 原 Dashboard 10 在日期筛选后五张卡片同时运行；界面显示单卡历史平均约 17—18 秒。
- Dashboard 11 已移除 Q02 首屏明细，保留四张聚合卡；相同 2026-09-01—03 筛选窗口在本次采样的 16 秒仍未全部完成，约 31 秒内完成加载。

## 已实施

- Q02 从最多 500 个聚合分组缩减为最多 100 个。
- 新建 Dashboard 11：`Lifecycle V2 Joint｜快速总览（试运行）`，只包含 Q01、Q03、Q04、Q05。
- Dashboard 11 的“开始日期”“结束日期”均已映射到四张报表的同名 SQL 参数。

## 仍受阻的优化

- Metabase 数据源运行在只读模式，直接执行 `CREATE TABLE` 返回 `Running in read-only mode`。
- 当前账户无权访问 `/admin/settings/caching`，无法启用 30 分钟缓存。
- 现有 Model 的 SQL 转换入口会生成新的 Question 而非原地替换 Model，因此没有对 Model 240 做不安全的原地 SQL 覆盖。

## 结论

首屏去掉 Q02 能降低结果传输和渲染，但无法避免其他四张卡重复扫描、透视同一批原始日志。要获得稳定的秒级响应，必须由 DBA 通过直接 MySQL 通道建立 `mart_lifecycle_v2_joint_daily_rawlog`、添加刷新索引、执行 D+1 增量刷新，并将 Metabase Model 改为读取该物化表。

可执行 SQL 位于 `sql/01_create_mart.sql`、`sql/02_refresh_mart.sql` 和 `sql/03_validate_mart.sql`。
