# 本次任务改用官方BigQuery客户端

用户已明确批准“改回之前的方式”，即复用隔离企业ADC，通过Google官方BigQuery Python客户端执行本任务只读聚合查询。此授权仅切换本任务访问方式，不修改Google IAM、不扩大到其他项目或生产写入。

- 已验证指定企业身份；已成功列出wajenigeria数据集。
- 已检查注册、支付、日活相关来源元数据，记录见direct-source-metadata.json。
- 已执行01_daily_source_profile.sql，估算与实际账本见对应dry/result及direct-query-ledger.json；扫描约0.18GiB。
- 来源包含90005与90006，后续Waje业务查询必须明确限制app_id=90006。9月9日日活记录存在不等于已证明H5活跃覆盖完整。
- MCP认证接入配置保留，但云端mcp.tools.call权限仍缺失；本任务不通过MCP查询，不要求增加该权限。
- 继续保持单条5GiB、整次25GiB、查询前估算、聚合返回、不足10人不展示。不得以切换客户端为由撤销限制。
- 当前仅恢复查询与来源初查；8月两类人群对比、9月9日完整性核验及报告更新仍待执行。原报告未改动。
