# Waje Firebase 设备与性能报表可实现性说明

本目录是飞书文档《Waje Firebase 设备与性能数据可实现报表、字段与埋点缺口清单 V1》的本地可追溯材料。

## 内容

- `field-metric-matrix.json`：端侧、字段、指标计算、展示门槛与敏感字段边界。
- `data-quality-receipt.json`：数据窗口、聚合方式、实时查询阻断与发布门槛。
- `lark-delivery-receipt.json`：飞书发布后的文档、空间和回读状态。

## 证据边界

- 聚合基线：`analysis/firebase_multiplatform_device_performance_2026_08_27/runs/firebase-multiplatform-20260827T112000Z-c44037e0/`。
- 本次仅通过 Firebase MCP 复核注册应用及 Crashlytics 聚合；不保存错误堆栈、用户、会话、设备唯一标识、URL、订单或支付明细。
- 企业 BigQuery MCP 处于 `blocked_authentication`。因此这里的 8 月 27 日基线不是实时数据，任何后续趋势结论须在认证只读聚合恢复后重新核验。
