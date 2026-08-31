---
type: access-request
domain: gemini-vertex
product: Waje Game
status: blocked_iam
updated: 2026-08-21
tags: [waje, gemini, vertex-ai, bigquery, iam, access]
---

# Waje 企业 Gemini CLI 权限申请与验证清单

## 当前结论

本机 Gemini CLI 已完成企业 Google 账号登录，并已切换到 `vertex-ai` 认证模式；ADC 可用。当前候选运行项目为 `indigo-gecko-500503-j3`（Cloud 名称：`GE-hkinitial`）。

最小调用已触达 Vertex AI，但被以下权限拒绝：

```text
aiplatform.endpoints.predict
```

因此当前失败不是本机安装、网络、账号登录或个人 API Key 问题，而是企业 Vertex AI 推理 IAM 未授予。项目已强制清除 `GOOGLE_API_KEY` 与 `GEMINI_API_KEY` 后再调用，未回退到个人 API Key。

## 一、请管理员确认的运行项目

请确认 `indigo-gecko-500503-j3` 是否为公司指定的 Gemini/Vertex AI 运行项目。

- 若是：按下文授予最小权限。
- 若否：提供正式 `runtime_project_id` 与运行区域；项目配置会切换到该项目，不再使用当前候选项目。

## 二、最小权限申请

### P0：企业 Gemini/Vertex AI 推理

对 Robin 的企业 Google 账号，在确认的运行项目中授予：

- `roles/aiplatform.user`（Vertex AI User）或包含 `aiplatform.endpoints.predict` 的等价自定义角色；
- 确认 Vertex AI API 已启用；
- 确认允许调用公司批准的 Gemini 模型及区域，例如 `us-central1`。

不需要授予 Owner、Editor、Vertex AI Admin、服务账号管理或项目级写入权限。

### P1：后续 Waje BigQuery 聚合分析

仅在企业 Gemini 需要读取 Waje 内部指标时，再追加：

- 运行查询所需的 `BigQuery Job User`；
- Waje 认证聚合 View 的只读访问，而非底层用户级明细表；
- 默认禁止 KYC 原始字段、手机号、账户、订单明细、完整设备标识和导出。

数据项目 `wajenigeria` 与 Gemini/Vertex 运行项目应保持分离登记；不得因为 Gemini 推理需要而扩大对 Waje 原始数据的权限。

## 三、管理员验证步骤

1. 确认运行项目和 Vertex AI API。
2. 向 Robin 企业账号授予 Vertex AI User 或等价最小权限。
3. 由 Robin 执行无业务数据的最小健康检查。
4. 成功后再验证 `gemini-3.7-flash`；复杂竞品综合任务再验证 `gemini-3.1-pro-preview`。
5. 最后才配置 Waje BigQuery 认证 View 白名单并执行聚合查询。

## 四、本地验收命令

```bash
unset GOOGLE_API_KEY GEMINI_API_KEY
export GOOGLE_CLOUD_PROJECT="<企业运行项目ID>"
export GOOGLE_CLOUD_LOCATION="us-central1"
gemini --approval-mode plan --output-format json --model gemini-3.7-flash \
  -p 'Return only {"status":"ok","check":"vertex-ai-ready"}'
```

验收成功条件：

- 返回 JSON，不出现 `aiplatform.endpoints.predict`、`SUBSCRIPTION_REQUIRED` 或 `PERMISSION_DENIED`；
- 回执确认使用企业运行项目；
- 不读取 Waje 数据、不写入 BigQuery、不输出凭证；
- 后续竞品试运行可进入 Flash 采集阶段。

## 五、当前已验证证据

| 项目 | 结果 |
|---|---|
| Gemini CLI | 已安装，版本 `0.56.0` |
| 企业 Google 登录 | 已完成 |
| ADC | 可用 |
| Gemini CLI 认证模式 | 已切换为 `vertex-ai` |
| 候选运行项目 | `indigo-gecko-500503-j3` 可见 |
| Vertex 最小调用 | 被 `aiplatform.endpoints.predict` 拒绝 |
| 个人 API Key 回退 | 已禁止 |
| Waje 竞品试运行 | 已正确产出 `blocked_iam` 回执，不生成虚构结论 |

## 六、关联资料

- [[../02-数据/Waje Android Firebase接入与数据现状审计-2026-08-21]]
- [[../02-数据/数据平台开发侧现状与治理待办-2026-08-07]]
- [[Waje版本体验与福利风控验证SOP-2026-08-14]]
- `config/gemini-enterprise.json`
- `tools/gemini_bridge.py`
