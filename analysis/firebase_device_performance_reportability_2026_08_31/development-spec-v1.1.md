# Waje Firebase 设备与性能｜开发执行规格 V1.1

本文件是飞书文档“开发执行规格 V1.1”章节的本地可追溯副本。目标是让开发按卡片实现，不自行补口径。

## 数据状态

- 已验收基线：2026-08-27 的 Firebase-only 聚合快照；Android/iOS Performance 窗口为 2026-08-20—26，H5 行为窗口为 2026-08-14—21，业务日为 Africa/Lagos。
- 当前 BigQuery MCP：`blocked_authentication`。目标聚合 View 是开发合同，不代表目前已认证存在。
- 状态字段必须取 `certified`、`provisional`、`immature`、`data_gap`、`blocked` 或 `delayed`，不可以 0、空白或成功占位替代。

## 报表清单

| ID | 页面 | 当前可交付 | 主要输入 | 关键边界 |
|---|---|---|---|---|
| R01 | 数据健康与覆盖 | 是 | 覆盖、截止时间、来源记录量、质量状态 | 先判定数据能否用 |
| R02 | Android 原生性能与网络 | 是，试运行 | DURATION_TRACE、NETWORK_REQUEST、SCREEN_TRACE | P95 非启动耗时；HTTP 成功率非业务成功率 |
| R03 | Crashlytics 稳定性 | 是 | issue、版本、设备、OS 聚合 | 不计算 Crash/ANR 率，不跨 issue/包相加用户 |
| R04 | H5 行为基线 | 是 | page_view、session_start、first_visit、user_engagement | 不代表网页性能 |
| R05 | iOS 早期观察 | 仅质量观察 | Performance / Analytics 聚合 | 覆盖未达到 7 完整日 |
| R06 | 设备、版本、网络排行 | 是，复用 R02 | 单一排名维度 | 不混合设备/OS/运营商/网络排行 |
| R07 | H5 RUM 与业务漏斗 | 仅接入状态页 | 待补 H5 RUM 与 Origin 服务端事实 | 不输出数值 KPI |

详细字段、数值基线、公式、筛选和无数据行为以同目录 `development-spec-v1.1.xml` 及飞书文档为准。
