# Phenix 分包付费与留存诊断工件

- Markdown：knowledge/02-数据/Phenix浏览器分包付费与留存异常诊断-2026-09-02.md
- HTML：output/html/Phenix浏览器分包付费与留存异常诊断-2026-09-02.html
- 来源：分包详情 - 2026-09-02T171410.991.xls，只保留分包级聚合。
- 企业 BigQuery API：bigquery_audit.json；只保留 H5 原始入库元数据和日期级聚合计数。
- 运行：python3 scripts/analyze_phenix_channel_retention.py
- 不保存转换后的 xlsx、用户明细、订单明细、账号或凭据。
