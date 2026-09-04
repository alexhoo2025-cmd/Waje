# 全平台用户生命周期与付费价值分析

## 交付物

- 离线报告：`output/apps/all-platform-cohort-value-2026-09-03/dist/index.html`
- 已审核数据快照：`reviewed_snapshot.json`
- 报告摘要数据：`report_summary.json`
- SQL：`sql/`
- 聚合查询结果与窗口回执：`results/`

## 范围

- 数据截止日：2026-09-02。
- 生命周期/留存 cohort：2026-06-01 至 2026-08-31。
- H5 重点专题：首包 `com.wajegame.web` 且 `download_channel`、`first_channel`、`first_sub_channel` 均为 `PAWAJEBETH5`。
- 平台对照：按用户首端类型（H5 / Android / iOS）重建，不用渠道名称推断平台。

## 当前状态

`reviewed_partial`：报告已交付可验证的聚合结论，但以下指标不认证为完整结果：

1. 2026-08 严格自然渠道的唯一老付费/复充人数：8 月已可按首平台和首包统计唯一首充/复充用户；但带渠道字段的严格 PAWAJEBETH5 自然查询超过单次 5 GiB 成本护栏，不以首包级结果替代渠道级结果。
2. 严格 H5 自然 cohort 的 D30/D60/D90 正式付费率：6—8 月已按同一严格注册 cohort 计算 Day1/Day7/Day14；长生命周期付款率尚未认证。
3. H5 自然第 2 至第 14 日的 2026-06 早期 cohort：日活事实从 2026-06-30 开始，早期生命周期显示 `N/A`。
4. Ares 聚合表不含 D9—D13；这些天数由严格 H5 cohort 日活重建，但未在全平台分包级聚合中补写。

## 认证口径

- 成功订单：`origin_hfyl.view_event_pay` 的 `order_success`，按 `target_day × user_id × order_no` 去重。
- 首充用户：历史 `first_pay_date` 当日存在成功订单的唯一用户。
- 复充/老付费用户：成功订单发生日严格晚于历史 `first_pay_date` 的唯一用户。
- 留存：同一账号在目标自然日有 `realtime_edw_user_version_daily` 活跃记录。
- 所有本地结果为聚合数据；未保存用户、订单、支付方式或凭据明细。
