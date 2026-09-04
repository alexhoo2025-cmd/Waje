# Phenix 渠道 h5phx（p=h5phx）线上复核工件

- 修正版 Markdown：`knowledge/02-数据/Phenix渠道h5phx线上入库与归因复核-2026-09-03.md`
- 修正版 HTML：`output/html/Phenix渠道h5phx线上入库与归因复核-2026-09-03.html`
- 精确审计回执：`run_receipt.json`
- Firebase 参数命中明细：`marker_focus_results.json`
- Firebase 参数命中汇总：`marker_summary_results.json`
- 修正版汇总：`corrected_summary.json`
- 报告校验：`corrected_report_validation.json`
- SQL：`sql/`

本轮确认：`p=h5phx` 主要嵌在 Firebase 的 `page_location` / `page_referrer` URL 字符串中，不是独立的 `p` 参数键。Firebase H5 能找到该标记，但 Origin 实时 H5、Origin 渠道视图和当前可见 90006 渠道聚合表没有对应的 `h5phx` 结果，说明下游渠道标准化/报表衔接仍有问题。

数据范围为完整日 2026-08-27 至 2026-09-01；2026-09-02 和 2026-09-03 的 intraday 仅做表存在性盘点，不参与结论。所有查询均为只读聚合，未保存 URL 值、参数值、用户明细、设备标识、支付明细、凭据或令牌。
