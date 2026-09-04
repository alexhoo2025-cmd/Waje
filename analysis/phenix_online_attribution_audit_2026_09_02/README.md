# Phenix 线上 BigQuery 归因与跨渠道上报审计工件

- Markdown：`knowledge/02-数据/Phenix线上BigQuery归因与跨渠道上报审计-2026-09-02.md`
- HTML：`output/html/Phenix线上BigQuery归因与跨渠道上报审计-2026-09-02.html`
- 结构化汇总：`channel_summary.json`
- Firebase 聚合回执：`run_receipt.json`
- Origin/实时链路回执：`origin_crosscheck_receipt.json`
- 可复现 Notebook：`phenix_online_attribution_audit_2026_09_02.ipynb`
- SQL：`sql/`；按 Firebase、Origin US 和 Origin europe-west4 分开执行

本轮结论：其他 H5/APP 渠道可以在 Firebase 或 Origin APP 实时客户端表中观察到，但当前 Firebase 与 Origin H5 聚合均未观察到 Phenix 标识；Origin H5 实时表的 UTM 和会话键缺失。用于报表复核的 90006/留存聚合表没有审计窗口数据，空结果不代表业务值为 0。

本轮通过企业 BigQuery API 完成只读聚合；未读取或保存原始事件、用户明细、设备唯一标识、支付明细、原始 URL、凭据或令牌，也未修改 BigQuery、Firebase、Origin、权限、看板或埋点配置。
