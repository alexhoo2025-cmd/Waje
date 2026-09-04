# Waje 端侧设备与性能分析 Agent Runtime

此目录实现 Agent Platform V1 的本地可审阅工件。它将自然语言模型与 BigQuery 原始 Firebase 表隔离：模型只能调用六个固定函数，函数只查询 `agent_analytics` 下的五个安全聚合视图。

## 运行契约

- 数据项目与区域：`wajenigeria / europe-west4`；业务时区：`Africa/Lagos`。
- 模型：Agent Studio 当前可用的 `gemini-3.1-pro-preview`、思考级别 `medium`；模型不可用时仅可选择 Agent Studio 已批准的 `gemini-2.5-pro`，并记录实际模型。
- 身份：生产部署使用 Agent Identity；不使用个人 ADC、API Key、服务账号 JSON 或浏览器会话。
- 安全：不提供自由 SQL、写入、导出或明细检索能力；日期最多 30 个完整日、每次工具查询不超过 1 GiB、每个 Agent 运行不超过 5 GiB、结果最多 100 行。
- 网络能力：启用 Google Search 与 URL Context，仅检索公开新闻、竞品、应用商店和技术文档；公开来源必须单列 URL、时间、证据等级和事实边界，不能替代 BigQuery 聚合事实。
- 状态：`certified`、`provisional`、`immature`、`delayed`、`data_gap`、`blocked` 或 `no_data`，绝不将缺口渲染为零。

## 先决条件

在部署前，管理员必须执行本目录 `sql/` 中的聚合层与视图脚本，并完成视图字段、完整日、样本门槛与脱敏核验。当前项目中 `active_allowed_views` 为空且本机 gcloud/MCP 均未通过认证；这意味着在核验成功前，不能部署一个可查询的 Agent。

最小权限：Robin 需要 `roles/aiplatform.user`；Agent Identity 需要项目级 `roles/aiplatform.expressUser`、`roles/serviceusage.serviceUsageConsumer`、`roles/bigquery.jobUser`，以及仅对 `agent_analytics` 数据集的 BigQuery Data Viewer/Metadata Viewer。不得向 Agent Identity 授予原始 Firebase 数据集读取、BigQuery 写入、IAM 管理或密钥创建权限。

## 验证与部署

```bash
python3 -m unittest tests.test_waje_device_performance_agent

python3 -m agent_runtime.waje_device_performance_agent.deploy \
  --project wajenigeria \
  --runtime-location us-west1 \
  --staging-bucket gs://APPROVED_AGENT_STAGING_BUCKET \
  --probe-model \
  --dry-run
```

移除 `--dry-run` 会创建 Agent Runtime 资源，因此只能在视图、IAM、预算和项目授权均已通过后执行。
