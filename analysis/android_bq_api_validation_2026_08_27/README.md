# Android BigQuery API 查询与聚合验证

## 当前状态

`blocked_authentication`

2026-08-27（Asia/Hong_Kong）使用受控的 `bigquery_waje` 只读工具对项目
`wajenigeria` 进行预检时，`list_dataset_ids` 返回 `Auth required`。因此本目录已
生成并完成静态审查的 SQL 只能作为待授权的实测包，不能把历史本地基线写成此次
实时 API 查询结果。

## 验证问题

验证既有《Waje 多端设备、性能、事件与会话看板 V1》中的 Android 口径是否能由
BigQuery 直接查询和复算：

- 性能数据：按日、包体、事件类型、应用版本、设备型号、系统版本、网络类型聚合；
- 性能指标：DURATION_TRACE P90、NETWORK_REQUEST P90、HTTP 200–399 成功率、慢帧/冻结帧 trace 加权均值；
- 会话数据：去标识化会话数与 Performance/Crashlytics 采集标记的对照；
- Analytics：按 Android 包体、版本、设备和事件的聚合覆盖；
- 质量：日期完整性、空值、异常范围、样本门槛、跨来源口径冲突。

## 固定分析口径

| 项目 | 口径 |
|---|---|
| BigQuery 项目 | `wajenigeria` |
| 连接资源 | `europe-west4` 的 `remote_udf_conn`；普通表查询不需要引用该连接 |
| 业务时区 | `Africa/Lagos` |
| 本次测试窗口 | 2026-08-20 至 2026-08-26，作为 2026-08-27 的 7 个完整日 |
| Android 主包 | `com.hfhy.waje.special` |
| Android 传音老包 | `com.hfhy.wajecasino.palmgame` |
| Android 传音新包 | `com.hfhy.wajecasino.game` |
| P90 门槛 | 合格样本数至少 500；不足时返回 NULL，不补值 |
| 小组门槛 | 设备/系统分层仅保留至少 10 条性能样本的聚合组 |
| 数据边界 | 不输出用户 ID、会话 ID、设备唯一 ID、URL、请求正文、响应正文或堆栈 |

数据源表名来自既有已审阅的 `data_contract.json` 和上一轮元数据材料；本次实时
表存在性、字段类型和最新分区仍须在认证恢复后重新核验。

## 测试文件

| 文件 | 目的 |
|---|---|
| `sql/00_metadata_columns.sql` | 核验 Android 来源表字段、类型和区域级元数据 |
| `sql/01_performance_daily_coverage.sql` | 逐日性能记录、事件类型、版本和时间覆盖 |
| `sql/02_performance_metric_aggregates.sql` | P90、网络成功率和帧比例聚合复算 |
| `sql/03_device_os_mix.sql` | 设备型号×系统版本的聚合规模和覆盖 |
| `sql/04_network_quality.sql` | 网络请求响应码、P90、成功率和无响应码比例 |
| `sql/05_sessions_reconciliation.sql` | Sessions 去标识化会话与性能/Crashlytics 标记对照 |
| `sql/06_android_analytics_mix.sql` | Android Analytics 包体、版本、设备和事件覆盖 |
| `sql/07_formula_reconciliation.sql` | 性能事件类型可加总性、有效值范围和指标分母检查 |

所有 SQL 都是单条 `SELECT/WITH`、含日期过滤、无 `SELECT *`、只返回聚合结果，
执行前必须通过：

```bash
python3 /Users/robin/.codex/skills/waje-bigquery-readonly/scripts/validate_readonly_sql.py analysis/android_bq_api_validation_2026_08_27/sql/01_performance_daily_coverage.sql
```

## 实测前置门禁

1. `list_dataset_ids(projectId=wajenigeria)` 成功；
2. 目标来源表的 `get_table_info` 成功，字段与 SQL 一致；
3. 项目和目标数据集位置确认是 `europe-west4`；
4. 每条 SQL 先 dry run，单条不超过 5 GiB，整轮不超过 25 GiB；
5. 仅使用批准的数据集/授权聚合视图；若原始 Performance 表未列入批准范围，停止实测并改用授权视图；
6. 结果带数据截止时间、完整日状态、样本量和质量状态；
7. 所有跨来源比较先确认粒度和分母，不把 Analytics `session_start` 事件数与 Sessions 唯一会话数混称。

## 当前可复用历史证据

上一轮本地基线记录了 2026-08-20 至 2026-08-26 三个 Android Performance 来源存在
实际记录，但本目录不把那些数字作为本次 API 实测结果。历史基线只用于检查 SQL
输出结构和后续做数量级合理性对照：

`analysis/multiplatform_device_performance_dashboard_v1_2026_08_27/actual_baseline.json`

## 预期状态

- `certified`：字段、分区、粒度、公式、样本和跨来源勾稽均通过；
- `provisional`：有数据且可计算，但仍有字段映射或完整日限制；
- `immature`：窗口不足 7 个完整日或近期分区未成熟；
- `blocked`：认证、IAM、对象白名单、成本或查询质量门禁未通过；
- `data_gap`：没有对象/字段或没有样本，但必须先排除权限、延迟和筛选错误。

