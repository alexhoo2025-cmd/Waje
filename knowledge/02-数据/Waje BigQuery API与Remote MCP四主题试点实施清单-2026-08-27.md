---
type: bigquery_mcp_pilot_implementation
date: 2026-08-27
status: blocked_external_prerequisites
project: wajenigeria
tags: [BigQuery, MCP, Gemini, API, 数据治理, 查询策略]
---

# Waje BigQuery API 与 Remote MCP 四主题试点实施清单

> 当前状态：本地策略层已就绪，但 Remote MCP 身份、Gemini 运行 IAM、授权聚合 View 和服务端只读拒绝策略仍未完成。所有自动查询保持 fail-closed。

## 1. 目标架构

```text
Codex / Gemini Data Execution Agent
          ↓
本地查询策略层（身份、对象、SQL、成本、结果质量）
          ↓
官方 BigQuery Remote MCP（仅元数据 + execute_sql_readonly）
          ↓
wajenigeria 授权聚合 View
          ↓
Metabase / Ares / 审计报告复用认证口径
```

- BigQuery API/客户端库：固定 SQL、定时质量检查、Dry Run、作业回执和告警。
- Remote MCP：受控自然语言探索、Schema 发现和授权聚合分析。
- Gemini：仅在企业身份、模型权限、MCP 认证和视图白名单均通过后执行聚合初稿。
- Codex：校验 SQL、口径、时间窗、分母、成熟度和最终事实边界。

## 2. 当前预检

- 总状态：`blocked_external_prerequisites`。
- Remote MCP：`blocked_authentication`；信任状态：`False`。
- 已激活授权 View：0。
- 本地策略不保存凭据、不调用写工具、不读取业务行。

## 3. 四主题候选视图契约

| 主题 | 逻辑 View | 当前状态 | 允许维度 | 必要质量字段 |
|---|---|---|---|---|
| kyc | `wajenigeria.agent_analytics.vw_kyc_daily_safe` | `pending_source_mapping` | event_date, flow_type, surface_type, package_id, channel, version, risk_rule_version, failure_stage | data_cutoff, complete_day, linkage_rate, missing_reason |
| game_rtp | `wajenigeria.agent_analytics.vw_game_rtp_daily_safe` | `pending_source_mapping` | event_date, game_id, play_id, mode_id, room_id, surface_type, package_id, channel, config_version, currency_type | effective_stake, final_payout, valid_rounds, complete_day, missing_reason |
| payer_retention | `wajenigeria.agent_analytics.vw_lifecycle_payer_daily_safe` | `pending_source_mapping` | cohort_date, lifecycle_day, payer_segment, surface_type, package_id, channel | mature_cohort, denominator, currency, data_cutoff, complete_day |
| h5_performance | `wajenigeria.agent_analytics.vw_h5_performance_daily_safe` | `pending_source_mapping` | event_date, page_id, game_id, web_version, device_tier, browser, network_type | sample_size, event_coverage, complete_day, data_cutoff, missing_reason |

候选 View 不等于授权 View。数据开发完成真实源表映射、聚合、脱敏、完整日和口径验证后，管理员才可将其加入 `active_allowed_views`。

## 4. 强制查询策略

1. 只允许 `SELECT` / `WITH`；禁止 DDL、DML、导出、过程、动态执行和非批准 AI/ML 操作。
2. 仅允许已激活的授权 View；禁止基础用户、订单、KYC、支付、资产和设备明细表。
3. 非元数据查询必须有日期或分区过滤，并带不超过 3,000 行的 `LIMIT`。
4. 禁止 `SELECT *` 和直接投影身份、订单、设备、支付、KYC、生物或网络标识字段。
5. 每次先 Dry Run；单查询上限 5 GiB，单审计周期上限 25 GiB；涉及用户的结果分组低于 10 个样本时合并或抑制。
6. Remote MCP 仅暴露元数据工具和 `execute_sql_readonly`；`execute_sql` 必须由服务端拒绝策略拦截。

## 5. 外部实施清单

| 责任域 | 必须动作 | 完成证据 |
|---|---|---|
| IAM / MCP 管理员 | 为批准的 MCP 调用身份开通工具调用与只读查询权限；在服务端拒绝非只读工具。 | `list_dataset_ids` 通过；`execute_sql` 被拒绝。 |
| Vertex / Gemini 管理员 | 在运行项目补齐模型预测与服务用量权限。 | 企业模型最小任务返回结构化成功或可审计的业务状态。 |
| 数据开发 | 按四主题映射真实物理表，创建同地区授权聚合 View。 | View 元数据、字段字典、完整日与质量字段通过审计。 |
| 数据分析 | 用 SQL 模板完成 Dry Run、近 7 个完整日聚合和与正式入口的最小对账。 | 查询回执含扫描量、数据截止、完整日和质量状态。 |
| 产品 / 风控 | 审核 KYC、RTP、付费和性能指标的口径、分母与风险边界。 | 认证指标版本进入 Ares/Metabase 统一语义层。 |

## 6. 本地可执行资产

- 策略：`config/bigquery_mcp_policy.json`。
- SQL 守卫：`tools/bigquery_mcp_policy.py`。
- 预检：`scripts/run_bigquery_mcp_preflight.py`。
- 四主题模板：`analysis/bigquery_mcp_pilot_2026_08_27/sql_templates/`。模板在 View 激活前不得执行。

## 7. 试点验收

1. 认证：Remote MCP 元数据工具可调用，当前认证阻塞解除。
2. 安全：非只读工具、未授权对象、写操作、无日期条件、敏感投影和超上限结果均被拦截。
3. 四主题：每个授权 View 可以完成 Dry Run、最近 7 个完整日聚合、质量字段输出和最小口径对账。
4. 运行：查询仅保存哈希、扫描量、行数、截止时间和质量状态，不保存原始聚合结果或任何明细。
5. 效率：连续两周对比人工路径的 SQL 首次通过率、问题到审计 SQL 的中位耗时、扫描量和人工返工次数。

## 8. 关联资料

- [[企业Gemini与BigQuery协同查询机制设计-2026-08-27]]
- [[Waje企业BigQuery数据资产与设备性能分析能力报告-2026-08-27]]
- [[Ares与Metabase看板建设方案对比分析-2026-08-05]]
