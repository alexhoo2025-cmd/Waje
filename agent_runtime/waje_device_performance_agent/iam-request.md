# Waje 端侧设备与性能分析 Agent｜最小权限申请单

## 当前阻断证据

- Agent Studio 已切换至：`robin@afuruika.net`。
- 项目：`wajenigeria`。
- 账号切换后可进入 Agent Designer，但控制台提示“请让管理员启用所需 API”。
- 当前模型下拉显示 Gemini 3.5 Flash、3.1 Pro (preview)、2.5 Flash 与 2.5 Pro。按产品负责人确认，V1 使用 `gemini-3.1-pro-preview`，不等待 `gemini-3.8-flash` 出现在此控制台。
- 本机 BigQuery MCP 当前为 `Auth required`；安全视图仍未激活。

## 第一阶段：创建与预览权限

管理员应先确定试运行创建者。按已确认设计，优先使用：`user:robin@afuruika.net`。

在项目 `wajenigeria` 授予该身份：

```text
roles/aiplatform.user
```

如果组织策略只允许 Express 权限，可改授：

```text
roles/aiplatform.expressUser
```

同时启用并核验：

```text
aiplatform.googleapis.com
bigquery.googleapis.com
serviceusage.googleapis.com
```

启用后重新打开 Agent Designer 并确认模型下拉中仍可选择：

```text
Gemini 3.1 Pro (preview)
```

部署工件需要一个受控的 Staging Bucket。优先由管理员预创建专用 Bucket，并仅给创建者该 Bucket 的对象写入权限；不要因部署方便而授予项目级 Owner。

## 第二阶段：数据平台权限

数据平台身份负责执行本目录 `sql/00` 至 `sql/03`，创建并核验：

```text
wajenigeria.agent_analytics.vw_firebase_endpoint_coverage_daily_safe
wajenigeria.agent_analytics.vw_firebase_event_session_daily_safe
wajenigeria.agent_analytics.vw_firebase_native_performance_daily_safe
wajenigeria.agent_analytics.vw_firebase_stability_daily_safe
wajenigeria.agent_analytics.vw_firebase_h5_behavior_daily_safe
```

安全视图建成前，不能把它们写入 `active_allowed_views`，也不能给 Agent 读取 Firebase 原始数据集。

## 第三阶段：部署后的 Agent Identity

部署产生 Agent Runtime 资源后，管理员以其 Agent Identity 为主体授予：

```text
roles/aiplatform.expressUser
roles/serviceusage.serviceUsageConsumer
roles/bigquery.jobUser                  # 项目 wajenigeria
roles/bigquery.dataViewer               # 仅数据集 agent_analytics
roles/bigquery.metadataViewer           # 仅数据集 agent_analytics
```

明确不授予：

```text
roles/owner
roles/editor
roles/bigquery.admin
roles/bigquery.dataEditor
任何 waje_ng_firebase_* 原始数据集的 dataViewer
服务账号密钥创建、IAM 管理或 BigQuery 写入权限
```

## 验收

管理员完成后，返回以下非敏感证据即可：创建者账号、已授予角色名称、五个视图名称、部署 Staging Bucket 名称、Agent Runtime 资源名。无需提供密码、Token、服务账号 JSON 或截图中的密钥内容。
