# Metabase 配置实施册：Waje 三端设备与性能 V2

## 配置边界

本册是 Metabase 管理员的创建草案。本轮不直接写入远端 Metabase。Metabase 只连接
`wajenigeria.waje_device_performance_mart` 下的授权聚合视图，禁止直接连接 Firebase、
Origin、Crashlytics、Sessions 或任何含用户/设备唯一标识的原始表。

## 创建顺序

1. 在 BigQuery `europe-west4` 创建 `waje_device_performance_mart`；
2. 按 `sql/01` 至 `sql/09` 创建或刷新聚合表；
3. 执行 `sql/10_metabase_readonly_views.sql`；
4. 在 Metabase 同步 Schema，只同步 `vw_metabase_*`；
   5. 创建 Model：`vw_metabase_endpoint_health`、`vw_metabase_native_performance`、
   `vw_metabase_native_performance_rank`、`vw_metabase_event_session`、
   `vw_metabase_native_performance_15m`、`vw_metabase_core_funnel`、
   `vw_metabase_stability_and_quality`；
6. 创建 Collection：`Waje / Device & Performance / V2`；
7. 按 `metabase-dashboard-contract.json` 创建四页 Dashboard；
8. 创建日报、周报和版本专项问题；
9. 绑定日期、端/包体、版本和质量状态筛选器；
10. 完成筛选器、权限、数值勾稽和移动端阅读验收。

## 字段格式

| 字段类型 | Metabase 设置 |
|---|---|
| `metric_date_lagos` | Date；默认最近 7 个完整 Africa/Lagos 自然日 |
| `*_p90_ms` | Number；单位毫秒；NULL 显示为 N/A |
| `*_rate`、`*_ratio`、`*_share` | Percent/ratio；保留 2 位展示，底层保留原始比例 |
| `performance_record_count`、`event_count` | Integer/number；显示为记录数或事件数，不标注用户数 |
| `quality_status` | Text；禁止映射为数字 0/1 |
| `complete_day` | Boolean；false 不进入成熟趋势比较 |
| `data_cutoff_at` | DateTime；显示最新数据截止时间 |

## Dashboard 绑定原则

- 首页只放数据可用性和端侧健康，不把数据缺口隐藏在空图表中；
- P90 图表只在样本数大于等于 500 时绘制数值；
- 设备排行使用 `rank_dimension` 单选，禁止同时混合设备、OS、网络和运营商；
- 事件与会话页面明确区分事件数和日唯一会话数；
- H5 页面将 Web Vitals、核心请求、前端错误和游戏 Ready 标记为 `data_gap`，不补零；
- Crashlytics 只展示事件量、问题量和覆盖状态，未认证前不创建崩溃率；
- 表格保留样本数、分母、数据状态和数据截止时间，避免只显示一个比例。

## 告警

默认只配置以下规则：

- 数据截止时间落后当前检查时间超过 45 分钟：`delayed`；
- P90 相对前 7 个完整日中位数上升超过 20%，且两侧样本均达到 500：`regression_warning`；
- 网络成功率下降超过 1 个百分点，且有响应码样本达到 500：`network_warning`；
- 预期数据日无记录：`data_gap`；
- 端侧不足 7 个完整日：`immature`。

这些是数据诊断门槛，不是业务 SLA。绝对业务目标需由产品/研发另行确认后才能加入。

## 权限

Metabase Reader/Viewer 只可读取授权 Model。禁止授予：

- BigQuery Data Editor/Owner；
- Firebase 原始表访问；
- Origin 原始业务表访问；
- 设备唯一标识、用户标识、订单、支付、URL、请求/响应正文和堆栈字段访问。

## 验收

- 默认打开首页即可看到最新截止时间、覆盖状态和质量状态；
- 日期、端侧、包体、版本筛选会使相关卡片变化；
- 图表与表格在同一筛选条件下勾稽一致；
- P90、网络成功率、慢帧比例均显示样本数和口径；
- `data_gap`、`immature`、`delayed`、`blocked` 不显示成 0；
- Metabase 无法浏览原始明细；
- 日报/周报只读取 BigQuery 已聚合数据。
