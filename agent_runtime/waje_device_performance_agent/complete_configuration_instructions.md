# Waje 端侧设备与性能分析 Agent｜完整配置指令 V1

> 适用项目：`wajenigeria`。本指令由项目管理员、数据平台管理员和 Robin 按顺序执行。
>
> 安全底线：原始 Firebase/GA4 数据始终留在 `europe-west4`；Agent 只读取 `agent_analytics` 下的五个聚合安全视图；不创建或下载任何用户、会话、设备唯一标识、订单、支付、KYC、URL、请求体、响应体或堆栈明细。

## 0｜执行身份与变量

以下命令必须使用 `wajenigeria` 的项目管理员或经授权的数据平台身份执行。不要使用服务账号密钥文件。

```bash
export WJ_PROJECT_ID="wajenigeria"
export WJ_DATA_LOCATION="europe-west4"
export WJ_AGENT_REGION="us-west1"
export WJ_USER="robin@afuruika.net"
export WJ_STAGING_BUCKET="waje-agent-runtime-staging-YOUR_UNIQUE_SUFFIX"

gcloud config set project "$WJ_PROJECT_ID"
```

## 1｜启用 API 与 Robin 的 Agent Studio 权限

需要具备 `roles/serviceusage.serviceUsageAdmin` 的管理员执行：

```bash
gcloud services enable \
  aiplatform.googleapis.com \
  bigquery.googleapis.com \
  serviceusage.googleapis.com \
  storage.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  cloudtrace.googleapis.com \
  cloudresourcemanager.googleapis.com \
  artifactregistry.googleapis.com \
  --project="$WJ_PROJECT_ID"
```

授予 Robin 创建、编辑、预览和部署 Agent 的最小项目权限：

```bash
gcloud projects add-iam-policy-binding "$WJ_PROJECT_ID" \
  --member="user:$WJ_USER" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding "$WJ_PROJECT_ID" \
  --member="user:$WJ_USER" \
  --role="roles/serviceusage.serviceUsageConsumer"
```

如果 Agent Studio 仍显示 `aiplatform.lowcodeAgents.update` 缺失，再补充以下角色；不要给 Owner 或 Editor：

```bash
gcloud projects add-iam-policy-binding "$WJ_PROJECT_ID" \
  --member="user:$WJ_USER" \
  --role="roles/aiplatform.expressUser"
```

> `roles/aiplatform.expressUser` 仅支持 Express/草稿操作，不等于 Agent Runtime 部署权限。若控制台报 `aiplatform.lowcodeAgents.deploy denied`，必须确认 `roles/aiplatform.user` 已实际授予到 `robin@afuruika.net`，而不是只授予 Express User。

核验：

```bash
gcloud services list --enabled \
  --project="$WJ_PROJECT_ID" \
  --filter='config.name:(aiplatform.googleapis.com OR bigquery.googleapis.com OR serviceusage.googleapis.com OR storage.googleapis.com)' \
  --format='table(config.name)'
```

## 2｜创建受控 Agent Runtime Staging Bucket

桶名必须全局唯一，且区域与 Agent Studio 强制部署区域一致：`us-west1`。

```bash
gcloud storage buckets create "gs://$WJ_STAGING_BUCKET" \
  --project="$WJ_PROJECT_ID" \
  --location="$WJ_AGENT_REGION" \
  --uniform-bucket-level-access

gcloud storage buckets add-iam-policy-binding "gs://$WJ_STAGING_BUCKET" \
  --member="user:$WJ_USER" \
  --role="roles/storage.objectAdmin"
```

此 Bucket 仅保存 Agent Runtime 的构建工件；不要上传 Firebase 导出、用户明细、Cookie、Token 或服务账号 JSON。

## 3｜建立 Firebase 聚合层与 Agent 安全视图

### 3.1 先决条件

如果 `waje_device_performance_mart` 尚未建立或未刷新，数据平台管理员必须先依次执行现有聚合脚本：

```bash
export WJ_MART_DIR="/Users/robin/Documents/wajetan_analyst/analysis/multiplatform_device_performance_dashboard_v1_2026_08_27/sql"

for WJ_SQL_FILE in \
  00_create_dataset.sql \
  01_create_dimensions.sql \
  02_refresh_event_session_daily.sql \
  03_refresh_native_performance_daily.sql \
  05_refresh_stability_daily.sql \
  07_refresh_endpoint_coverage_daily.sql; do
  bq query \
    --project_id="$WJ_PROJECT_ID" \
    --location="$WJ_DATA_LOCATION" \
    --use_legacy_sql=false \
    < "$WJ_MART_DIR/$WJ_SQL_FILE"
done
```

### 3.2 Agent 专用聚合与视图

```bash
export WJ_AGENT_DIR="/Users/robin/Documents/wajetan_analyst/agent_runtime/waje_device_performance_agent"

for WJ_SQL_FILE in \
  00_create_agent_analytics_dataset.sql \
  01_refresh_agent_native_performance_aggregates.sql \
  02_create_safe_views.sql; do
  bq query \
    --project_id="$WJ_PROJECT_ID" \
    --location="$WJ_DATA_LOCATION" \
    --use_legacy_sql=false \
    < "$WJ_AGENT_DIR/sql/$WJ_SQL_FILE"
done

bq query \
  --project_id="$WJ_PROJECT_ID" \
  --location="$WJ_DATA_LOCATION" \
  --use_legacy_sql=false \
  < "$WJ_AGENT_DIR/sql/03_validate_safe_views.sql"
```

验证必须看到以下五个 View，且无原始身份字段：

```text
wajenigeria.agent_analytics.vw_firebase_endpoint_coverage_daily_safe
wajenigeria.agent_analytics.vw_firebase_event_session_daily_safe
wajenigeria.agent_analytics.vw_firebase_native_performance_daily_safe
wajenigeria.agent_analytics.vw_firebase_stability_daily_safe
wajenigeria.agent_analytics.vw_firebase_h5_behavior_daily_safe
```

只有验证通过后，才能把这些名称加入本地 `config/bigquery_mcp_policy.json` 的 `active_allowed_views`；在此之前保持该数组为空。

## 4｜配置 Agent Studio 草稿

使用 `robin@afuruika.net` 登录：

```text
https://console.cloud.google.com/agent-platform/studio/agent-designer/edit/new?project=wajenigeria
```

在 Details 面板设置：

```text
名称：Waje 端侧设备与性能分析助手（试运行）
说明：基于经批准 Firebase/GA4 聚合数据分析 Android、iOS 与 H5 的设备、版本、网络、性能、稳定性、事件和数据质量，同时可检索公开技术文档、新闻与竞品资讯。
模型：Gemini 3.1 Pro (preview)
思考级别：MEDIUM
区域：us-west1（控制台当前强制区域）
```

工具设置：

```text
保留：Google 搜索、网址上下文
不添加：无认证 MCP、Google Drive、Agent Search Data Store、任何原始 Firebase/GA4 文件
```

完整系统指令从以下文件复制：

```text
/Users/robin/Documents/wajetan_analyst/agent_runtime/waje_device_performance_agent/system_instruction.md
```

保存草稿后不分享给团队、不发布公共目录、不配置邮件/飞书/Slack/Webhook。

## 5｜部署 Agent Runtime（仅在安全视图与 IAM 已验收后）

先在本机完成 ADC 登录；浏览器登录不替代此步骤：

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project "$WJ_PROJECT_ID"
```

在本地受控虚拟环境安装部署依赖：

```bash
cd /Users/robin/Documents/wajetan_analyst/agent_runtime/waje_device_performance_agent
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cd /Users/robin/Documents/wajetan_analyst
```

先运行无写入预检：

```bash
python3 -m agent_runtime.waje_device_performance_agent.preflight

python3 -m agent_runtime.waje_device_performance_agent.deploy \
  --project="$WJ_PROJECT_ID" \
  --runtime-location="$WJ_AGENT_REGION" \
  --staging-bucket="gs://$WJ_STAGING_BUCKET" \
  --probe-model \
  --dry-run
```

确认 Dry Run 的模型为 `gemini-3.1-pro-preview` 后，才执行真实部署：

```bash
python3 -m agent_runtime.waje_device_performance_agent.deploy \
  --project="$WJ_PROJECT_ID" \
  --runtime-location="$WJ_AGENT_REGION" \
  --staging-bucket="gs://$WJ_STAGING_BUCKET" \
  --probe-model
```

保存输出中的 `reasoningEngines` 资源名；下一步授权必须使用其中的 Agent Runtime ID。

## 6｜部署后给 Agent Identity 最小数据权限

从部署回执取得实际值后填写：

```bash
export WJ_ORG_ID="YOUR_ORGANIZATION_ID"
export WJ_PROJECT_NUMBER="YOUR_PROJECT_NUMBER"
export WJ_AGENT_ENGINE_ID="YOUR_REASONING_ENGINE_ID"

export WJ_AGENT_PRINCIPAL="principal://agents.global.org-${WJ_ORG_ID}.system.id.goog/resources/aiplatform/projects/${WJ_PROJECT_NUMBER}/locations/${WJ_AGENT_REGION}/reasoningEngines/${WJ_AGENT_ENGINE_ID}"
```

项目级角色：

```bash
gcloud projects add-iam-policy-binding "$WJ_PROJECT_ID" \
  --member="$WJ_AGENT_PRINCIPAL" \
  --role="roles/aiplatform.expressUser"

gcloud projects add-iam-policy-binding "$WJ_PROJECT_ID" \
  --member="$WJ_AGENT_PRINCIPAL" \
  --role="roles/serviceusage.serviceUsageConsumer"

gcloud projects add-iam-policy-binding "$WJ_PROJECT_ID" \
  --member="$WJ_AGENT_PRINCIPAL" \
  --role="roles/bigquery.jobUser"
```

仅授予安全视图数据集读取权限：

```bash
bq add-iam-policy-binding \
  --member="$WJ_AGENT_PRINCIPAL" \
  --role="roles/bigquery.dataViewer" \
  "${WJ_PROJECT_ID}:agent_analytics"

bq add-iam-policy-binding \
  --member="$WJ_AGENT_PRINCIPAL" \
  --role="roles/bigquery.metadataViewer" \
  "${WJ_PROJECT_ID}:agent_analytics"
```

绝对不要授予：

```text
roles/owner
roles/editor
roles/bigquery.admin
roles/bigquery.dataEditor
任何 waje_ng_firebase_* 原始数据集的 roles/bigquery.dataViewer
IAM 管理、服务账号密钥创建、BigQuery 写入、导出或通用 SQL 执行权限
```

## 7｜每日监测与验收

在 Agent Studio Schedule 中设置：

```text
Cron：0 13 * * *
时区：Africa/Lagos
输入：daily_monitor_prompt.md 的全文
输出：仅 Agent 运行记录和 Cloud Logging
禁止：邮件、飞书、Slack、Webhook、BigQuery 写表、文件导出
```

最终验收命令：

```bash
cd /Users/robin/Documents/wajetan_analyst
python3 -m unittest discover -s tests -p 'test_waje_device_performance_agent.py' -v
python3 -m agent_runtime.waje_device_performance_agent.preflight
```

验收标准：

1. Agent Studio 草稿显示 `Gemini 3.1 Pro (preview)`、Google 搜索与 URL Context 已启用。
2. 仅 Robin 可使用，未分享任何群组或公共目录。
3. Agent 只能返回五个安全视图的聚合结果，且每次含窗口、截止时间、完整日、样本量、质量状态与实际模型。
4. 用户/设备唯一标识、订单、支付、URL、Cookie、Token、堆栈、DDL/DML 和自由 SQL 请求全部被拒绝。
5. H5 Web 性能缺口显示 `data_gap`；P95 样本不足显示 `N/A`；Crashlytics 不生成率指标。
