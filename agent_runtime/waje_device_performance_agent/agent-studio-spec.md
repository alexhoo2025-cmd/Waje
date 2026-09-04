# Agent Studio 配置规格｜Waje 端侧设备与性能分析助手

此文件是 Agent Designer 创建草稿时的唯一输入规格。Agent Studio 只用于设计、预览和导出代码；生产数据查询必须由本目录的 Agent Runtime 函数工具执行，不连接无认证 MCP。

## 基本设置

- 项目：`wajenigeria`
- 名称：`Waje 端侧设备与性能分析助手`
- 类型：单步骤 Agent
- 模型：`gemini-3.1-pro-preview`（控制台显示为 Gemini 3.1 Pro (preview)）
- 模型位置：`global`
- 思考级别：`MEDIUM`
- 搜索工具：启用 Google Search 与 URL Context，仅用于公开资讯、公开技术文档、竞品与新闻追踪
- 可见性：仅 Robin；不发布到团队或公共目录
- 外部数据工具：不添加 MCP Server、不上传原始 Firebase/GA4 数据、不添加 Google Drive 或 Agent Search Data Store。网页搜索与 URL Context 不得访问私有登录页、内部链接或敏感资料。

## 指令

将 `system_instruction.md` 的完整内容粘贴到 Agent 的 Instructions 字段。

## 推荐开场问题

1. 过去 7 个完整 Lagos 自然日，哪个 Android 包或版本出现最明显的原生性能问题？
2. 按设备型号、系统版本或网络类型查看当前 P95 异常 Top 5，并说明样本量与数据质量状态。
3. 检查 Android、iOS、H5 的数据截止时间、完整日与 H5 性能埋点缺口。

## 每日调度

- 时区：`Africa/Lagos`
- Cron：`0 13 * * *`
- 调度 Prompt：完整使用 `daily_monitor_prompt.md`。
- 输出：仅保留 Agent 运行记录与 Cloud Logging；不启用邮件、飞书、Slack、Webhook、BigQuery 写表或文件导出。

## 从 Studio 到安全生产版本

1. 保存 Agent Studio 草稿并使用 Preview 验证它不承诺访问未经批准的数据。
2. 点击 Get code；以本目录 `agent.py`、`query_gateway.py` 和 `system_instruction.md` 替换生成的 Agent 定义。
3. 只有在 `sql/03_validate_safe_views.sql`、IAM 和模型探针均通过后，才以 Agent Identity 部署 Agent Runtime。
4. 生产 Agent 的实际模型、运行区域和资源 ID 写入不含凭证的部署回执；每天 13:00 WAT 运行质量摘要，不配置外部通知。
