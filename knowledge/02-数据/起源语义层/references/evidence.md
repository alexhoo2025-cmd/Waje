# Evidence Register

| Fact Or Claim | Source Type | Source Locator | Observed | Confidence | Notes |
|---|---|---|---|---|---|
| 平台包含首页、业务看板、敏捷分析、数据统计、用户分析、报表集市、数据管理、AB 测试 | Web navigation | /tracking-web and module menus | 2026-08-03 | High | 以当前账号可见导航为准 |
| 业务看板目录为空/共享分组 0 | Web page | /tracking-web/dataView | 2026-08-03 | High | 不等于全平台没有看板，可能是权限或未配置 |
| 新增日活当前 2026-08-03 为 509 活跃、13 新增、2.55% 新用户占比 | Data statistics table | /tracking-web/dataStatistics/userAnalyze/newActive | 2026-08-03 13:16 | High | 当前日为部分日 |
| 基础留存整体 287 人、次留 21.25%、D3 11.98%、D7 0% | Data statistics table | /tracking-web/dataStatistics/userAnalyze/baseRetained | 2026-08-03 | High | D7 要按成熟 cohort 使用 |
| LTV1 5346.52、LTV7 17438.46、LTV30 0、终身 25030.43 | Data statistics cards/table | /tracking-web/dataStatistics/userValue/fltv | 2026-08-03 | High | 金额单位与成熟窗口待确认 |
| ROI 汇总 CAC 为 0、汇总 ROI 为 NaN | Data statistics table | /tracking-web/dataStatistics/userValue/froi | 2026-08-03 | High | 当前不能用于 ROI 决策 |
| 付费金额 57,878,933，付费次数 15,421 | Data statistics cards | /tracking-web/dataStatistics/paydata/paydata | 2026-08-03 | High | 日期窗口 2026-07-19 至 2026-08-03 |
| 启动用户 2,609、启动设备 1,854、总启动 7,065、页面 PV 84,530 | Data statistics cards | /tracking-web/dataStatistics/startAnalysis/start | 2026-08-03 | High | 日期 2026-08-02 |
| GAMEEND 接收 418,338、入库 287,464、异常 130,874 | Data quality table | /tracking-web/burying/buryingPoint/dataQuality | 2026-08-03 | High | 2026-07-27 至 2026-08-02 窗口 |
| 总错误率 3.30164%、接收 3,963,905、入库 3,833,031、抛弃 0 | Data quality summary | /tracking-web/burying/buryingPoint/dataQuality | 2026-08-03 | High | 以平台展示为准 |
| 报表集市 5 组、70 条目 | Report market directory | /tracking-web/iframe | 2026-08-03 | High | `BQ-` 与非 `BQ-` 版本并列 |
| TC 详情有负利润、极端 TC 比 | Embedded report table | /tracking-web/iframe/40/26 | 2026-08-03 | Medium | 可能受部分日/结算状态影响 |
| 用户分群更新时间主要为 2023-10 至 2023-12 | User analysis table | /tracking-web/users/analyze/usersGroup | 2026-08-03 | High | 不能直接作为当前分群规模 |
| NGN 1:1 为当前货币配置 | Metadata table | /tracking-web/burying/buryingPoint/exchange | 2026-08-03 | Medium | 配置更新时间为 2023-03-23，需确认仍有效 |

## Evidence Limits

- 未读取底层数仓、SQL、调度日志或 SDK 代码，因此未确认指标公式、字段级主键和数据血缘。
- 未把任何账号凭据或用户级明细写入资料库。
- 页面数据为一次观察快照，不能替代持续监控或日终对账。
