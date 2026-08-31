---
type: technical-audit-report
status: blocked_iam
updated: 2026-08-27
---

# 本地 Gemini CLI 企业能力审计

## 结论先行

**当前不能说 Gemini CLI 已经可以完整完成“生成查询思路、SQL 草稿、初步解释并直接查询企业 BigQuery”。** 本机 CLI、gcloud、bq 和个人 ADC 都正常，但 Vertex 模型探针返回 `403`，缺少 `aiplatform.endpoints.predict`；BigQuery MCP 虽然已连接，仍未通过信任和安全 View 白名单门禁。

模型名称不再作为硬性前置条件。已配置“首选模型 → 备选模型 → CLI 企业默认模型”的有序回退；只有模型不可用、暂时不可用、超时或输出无法解析时才换下一个模型，权限错误、许可证错误和 SQL 安全校验错误不会通过更换模型绕过。

本机目前真正可用的是：使用 `robin@afuruika.net` 的 ADC，通过本机 BigQuery API 执行固定的 Firebase-only 聚合 SQL，并生成本地汇总报告。

## 能力状态

| 能力 | 状态 | 证据 |
|---|---|---|
| 启动 Gemini CLI | `ok` | `/Users/robin/.local/bin/gemini`，版本 0.57.0 |
| gcloud / bq | `ok` | Google Cloud SDK 579.0.0，bq 2.1.36 |
| 企业个人 ADC | `ok` | `robin@afuruika.net`，配额项目 `wajenigeria` |
| 生成查询思路、SQL 草稿、初步解释 | `blocked_iam` | Vertex 缺 `aiplatform.endpoints.predict` |
| 模型不可用时自动回退 | `configured` | 首选、备选和 CLI 默认模型均已纳入有序路由 |
| Gemini 通过 BigQuery MCP 查数 | `blocked_external_prerequisites` | MCP `trust=false`，激活安全 View 数量为 0 |
| 本机 BigQuery API 聚合 | `ok` | 最近一次返回 127 行紧凑聚合结果 |
| 本地 HTML / Markdown / JSON 报告 | `ok` | 多端 Firebase 汇总报告已生成 |

## 本次探针

探针只要求 Gemini 返回一段固定 JSON，明确禁止调用工具、读取文件、访问 BigQuery 和修改文件。结果为：

```text
Vertex AI 返回 403
缺少权限：aiplatform.endpoints.predict
运行项目：indigo-gecko-500503-j3
运行区域：us-central1
```

因此当前仍无法验证 Gemini 的 SQL 生成和自然语言分析能力；不是因为 BigQuery 数据为空，而是模型调用权限没有通过。即使首选模型名称不可用，后续会按配置尝试其他企业模型，但所有模型都必须先通过同一 Vertex 权限门禁。

## BigQuery 数据通道

Remote MCP 当前配置为：

- 已连接官方 BigQuery MCP 地址；
- 只暴露元数据和 `execute_sql_readonly`；
- `execute_sql` 已排除；
- 但 `trust=false`；
- `active_allowed_views=0`。

即使 Vertex 模型权限补齐，Gemini 仍不能直接读取企业数据，直到管理员完成安全聚合 View 的创建、审计和白名单激活。

## 当前可用替代路径

本机 BigQuery API 已用固定 SQL 完成 Firebase-only 聚合：

- 项目：`wajenigeria`；区域：`europe-west4`；时区：`Africa/Lagos`；
- Android、iOS、H5 分端统计；
- Performance 返回端/包窗口级指标和维度 Top 3；
- Sessions 只在数据库内去重；
- Crashlytics 只返回去重事件量和问题数；
- H5 Web Vitals、白屏、核心请求和前端错误显示为 `data_gap`；
- 查询结果 127 行，未保存原始事件行或用户/设备唯一标识。

## 管理员需要补齐

1. 为 `robin@afuruika.net` 或实际企业调用主体在 `indigo-gecko-500503-j3` 授予 `aiplatform.endpoints.predict`。
2. 确认运行项目的 `serviceusage.services.use` 和 Vertex Gemini 模型可用性。
3. 将 BigQuery MCP 设置为受控信任，继续拒绝 `execute_sql`。
4. 创建并审计 Firebase-only 安全聚合 View，再加入 `active_allowed_views`。

在上述动作完成前，自动查询路由应继续使用本机 BigQuery API fallback，不应静默切换个人 API Key 或放开原始表。

## 审计边界

本次只保存能力状态、错误权限、查询回执和聚合结果；没有保存 API Key、服务账号密钥、Cookie、Token、原始事件、用户标识、设备唯一标识或原始模型错误报告。
