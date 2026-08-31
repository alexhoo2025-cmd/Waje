---
type: kyc_metabase_schema_audit
date: 2026-08-26
status: partial_schema_only
audience: product-risk
tags: [KYC, 人脸识别, Metabase, 数据审计, 埋点, 风控]
---

# KYC 人脸识别看板｜Metabase 数据可用性与埋点缺口审计

> 审计结论：现有结构能够形成 KYC V1 的**候选数据底座**，但尚不能认证为正式看板数据源。缺少稳定流程/端/版本维度、KYC→提现终态关联和 SDK 阶段事实；在完成日级对账、链路核验和数据新鲜度审计前，V1 必须保持 `provisional`。

## 1. 技术摘要

- 已盘点结构：6 个 Schema、797 张表、12,251 个字段；所有结论均为元数据层，不代表数据有值或可用。
- KYC、风险、提现和生命周期提现候选表均可见，具备日期、结果状态、包体或订单状态等片段性线索；外键、行级覆盖和真实链路键未导出。
- P0 数据可信性缺口：认证阶段与最终提现结果无法按稳定流程键验证关联；失败原因不具备不可变历史；字典扩展隐私扫描识别到需修复的脱敏漏网候选。
- 本报告不输出原始身份、支付账户、图像、生物特征、三方响应、默认值或业务数据行。

## 2. 看板可用性审计

| 看板区域/能力 | 结构审计状态 | 候选资产 | 主要阻塞 |
|---|---|---|---|
| 顶部 KPI | `schema_supported_candidate` | KYC 日级事件/人脸结果候选表 | 未执行日级对账、完整日与新鲜度验证。 |
| 认证漏斗 | `partial_schema` | KYC 事件、身份结果与人脸结果候选表 | 无稳定流程键、身份通过终态与阶段级关联证据；无结果只能按差值估计。 |
| 每日效率趋势 | `partial_schema` | 按日期的 KYC 聚合候选表 | 数据延迟、完整日、版本/配置切分和日级口径尚未验证。 |
| 失败原因诊断 | `partial_schema` | KYC 失败统计与人脸事件候选表 | 失败历史可被成功状态清理；不是不可变用户级失败轨迹。 |
| 流失阶段诊断 | `partial_schema` | KYC 日级聚合候选表 | 缺 SDK、权限、活体、退出、超时和网络阶段，无法真实归因。 |
| BVN/NIN 对比 | `not_independently_verified` | 身份认证候选表与历史日汇总契约 | 当前安全字典不能独立确认两种方式的聚合映射、口径和关联粒度。 |
| 端与包体对比 | `partial_schema` | 包体字段与 KYC 候选表 | 端类型未观察到稳定字段；包体到 App/H5 的映射未验证。 |
| 认证流程筛选 | `missing_not_observed` | — | 当前安全字典未观察到稳定流程/场景字段。 |
| 渠道、版本、配置、风控规则切分 | `missing_not_observed` | — | 未观察到渠道、端版本、配置版本和风险规则版本的完整 KYC 链路字段。 |
| 认证到最终提现结果 | `missing_not_observed` | 提现订单/审核候选表 | KYC 与提现终态之间未观察到可验证的一对一关联键。 |

### 全局筛选器

| 筛选器 | 结构审计状态 | 证据 | 补齐要求 |
|---|---|---|---|
| 日期 | `schema_supported_candidate` | KYC 候选表存在日期/时间线索 | 完整日与时区未验证 |
| 认证流程 | `missing_not_observed` | 历史契约要求 | 需新增 kyc_flow / scene |
| 端 | `partial_schema` | 包体可见 | 需稳定 platform 及包体映射 |
| 包体 | `schema_supported_candidate` | 主要人脸候选表存在包体线索 | 需日级对账 |
| 渠道 | `missing_not_observed` | 历史契约列为未来维度 | 需服务端/客户端统一渠道字段 |
| App/H5 版本 | `missing_not_observed` | 当前安全字典未观察到 | 需 app_version / web_version / build_version |
| 配置/规则版本 | `missing_not_observed` | 当前安全字典未观察到 | 需 config_version / risk_rule_version |

## 3. 可信链路的断点

```text
风险判定
  → 身份认证请求/结果
  → 人脸 SDK 拉起/权限/活体/匹配
  → 认证终态
  → 提现复核
  → 最终提现结果
```
当前结构可见其中若干表级片段，但没有可验证的统一 `kyc_flow_id + request_id + withdraw_id + trace_id` 关联链。故“人脸成功”不能解释为“提现成功”，而“无最终结果”也不能归因于主动放弃、SDK、网络或服务端失败。

## 4. P0 数据字典治理发现

- 扩展规则在现有字典中识别到 **17** 个可能仍以原名出现的敏感字段候选，涉及 4 类命名模式。报告不输出字段原名。
- 风险：当前资料库若被广泛共享，可能暴露身份、媒体、生物特征、账户或网络标识字段名；同时会削弱 KYC 看板的最小权限边界。
- 整改：更新字典脱敏规则，覆盖下划线、驼峰、姓名、图像/生物、账户、网络与密钥命名变体；重新生成所有分册，并以“原始候选字段名零泄漏”作为回归门禁。

## 5. 研发整改：事件与字段契约

| 优先级 | 事件 | 事实来源 | 解决的问题 | 最小安全字段 |
|---|---|---|---|---|
| P0 | `KYC_RISK_DECISION` | 服务端 | 记录规则触发、拦截或放行 | `event_uid, kyc_flow_id, withdraw_id, trace_id, decision, rule_version, event_time_server` |
| P0 | `KYC_IDV_RESULT` | 服务端 | 记录身份认证方法、终态、结果码与耗时 | `event_uid, kyc_flow_id, request_id, idv_method, result, error_code, duration_ms, event_time_server` |
| P0 | `WITHDRAW_FINAL_RESULT` | 服务端 | 建立认证到提现最终结果的事实链路 | `event_uid, kyc_flow_id, withdraw_id, trace_id, withdraw_status, failure_stage, event_time_server` |
| P0 | `KYC_STAGE_RESULT` | 服务端 | 保存不可变的逐次失败/成功阶段历史 | `event_uid, kyc_flow_id, stage, result, error_code, retry_no, event_time_server` |
| P1 | `FACE_SDK_LAUNCH_RESULT` | 客户端/SDK | 区分 SDK 拉起、黑屏和初始化失败 | `event_uid, kyc_flow_id, platform, sdk_version, result, error_code, duration_ms` |
| P1 | `FACE_PERMISSION_RESULT` | 客户端 | 定位相机授权前流失 | `event_uid, kyc_flow_id, permission_state, platform, event_time_client` |
| P1 | `FACE_LIVENESS_RESULT` | SDK/服务端 | 记录活体结果、超时和网络异常 | `event_uid, kyc_flow_id, result, error_code, duration_ms, network_type` |
| P1 | `FACE_MATCH_RESULT` | 服务端 | 记录匹配终态和阈值版本 | `event_uid, kyc_flow_id, result, error_code, threshold_version, event_time_server` |
| P1 | `KYC_STAGE_ABORT` | 客户端 | 区分主动退出、超时、断网和恢复失败 | `event_uid, kyc_flow_id, abort_reason, stage, network_type, event_time_client` |
| P2 | `KYC_CONTEXT_SNAPSHOT` | 客户端/服务端 | 补齐端、版本、渠道与配置切分 | `event_uid, kyc_flow_id, platform, package_name, channel, app_version, web_version, config_version, risk_rule_version` |

公共规则：所有事件仅使用伪标识用户键；服务端终态优先；客户端不得上传身份号码、手机号、图像、证件、生物特征或三方原始响应。核心事件同时携带端、包、版本、渠道、配置/规则版本与客户端/服务端时间。

## 6. 数据质量门禁

| 门禁 | 规则 | 优先级 |
|---|---|---|
| 完整日 | 每个统计日有显式 complete_day 标记；不完整日不进入默认 KPI。 | P0 |
| 阶段守恒 | 同一流程内后续阶段不得大于前序阶段；差值进入异常明细。 | P0 |
| 链路完整率 | KYC 风险、认证、人脸、提现终态可按流程键关联；缺失单独报告。 | P0 |
| 枚举与终态 | 未知 stage/result/error_code 隔离；终态缺失不可视为主动放弃。 | P1 |
| 版本与渠道覆盖 | 核心事件必须可按端、包、版本、渠道和规则版本切分。 | P1 |

## 7. 范围与待确认项

- 本次没有执行数据行 SQL，未验证记录数、空值、重复、时延、新鲜度、漏斗数值守恒或跨表 join 覆盖。
- 历史 KYC 文档中的指标与问题只用于定义审计目标，不能视作当前 Metabase 实测。
- 下一轮应先完成脱敏字典回归、KYC 日汇总日级对账和流程键关联审计；之后才适合将 V1 提升为正式看板。

## 8. 关联资料

- [[Metabase全库数据资产索引-2026-08-26]]
- [[Metabase-KYC人脸识别看板配置指南-2026-08-19]]
- [[Waje-KYC人脸识别Metabase看板V1与2.20埋点方案-2026-08-19]]
- [[Waje-KYC人脸识别与提现认证分析-2026-08-16]]
