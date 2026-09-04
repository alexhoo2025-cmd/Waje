# 本机 Metabase 三端设备与性能看板快照

> 2026-08-31 已新增需求方案版总览大看板；本目录保留为 2026-08-28 历史快照。当前阅读入口请使用 [Waje / 三端设备与性能总览（需求方案版）](http://127.0.0.1:3010/dashboard/6-waje)。

快照日期：2026-08-28  
本机地址：<http://127.0.0.1:3010>  
集合：<http://127.0.0.1:3010/collection/5-waje-device-performance-v1>

## 已保存内容

- 4 个看板：全端健康、原生性能、事件与会话、设备网络与 H5 接入差距。
- 9 个聚合问题：Android / iOS / H5 Analytics、Sessions、原生 Performance、Crashlytics、设备网络排行、元数据健康和 H5 性能缺口。
- 3 个阅读版报表：日报、周报、版本/事故专项报告。

看板和问题使用 BigQuery 上的只读聚合 SQL，数据源为 `wajenigeria` 的 `europe-west4` 区域；本地 Metabase 使用 H2 保存界面配置。

## 看板入口

1. [01 全端健康与数据可用性](http://127.0.0.1:3010/dashboard/2-01)
2. [02 Android 与 iOS 原生性能](http://127.0.0.1:3010/dashboard/3-02-android-ios)
3. [03 事件、会话与行为链路](http://127.0.0.1:3010/dashboard/4-03)
4. [04 设备、网络与 H5 接入差距](http://127.0.0.1:3010/dashboard/5-04-h5)

## 口径和安全边界

- 事件量是事件行计数，不是用户数；Sessions 的去重会话数只在 Sessions 表内使用，不与 `session_start` 相加。
- 原生性能 P95、网络成功率、慢帧和冻结帧仅在当前性能表可提供的字段上计算；样本不足或没有样本时显示 `N/A` 或 `data_gap`。
- Crashlytics 导出记录不直接解释为崩溃率；当前稳定性卡片保留导出事件/问题聚合并标记 `provisional`。
- H5 性能指标未采集，不从 Analytics 行为事件推断性能。
- 不查询或保存用户标识、设备唯一标识、Cookie、令牌、订单、请求/响应正文和完整堆栈。

## 筛选说明

当前看板使用固定审计窗口，以避免保存未绑定的假筛选控件。H5 事件问题保留了可选的“日期范围”字段筛选；全局日期筛选要等所有卡片改为统一日期字段变量后再启用。

## 可追溯回执

- 对象清单：[`metabase_objects.json`](./metabase_objects.json)
- 运行回执：[`run_receipt.json`](./run_receipt.json)
- 方案与指标契约：[`metabase-dashboard-contract.json`](../metabase_waje_three_platform_dashboard_design_2026_08_27/metabase-dashboard-contract.json)
