# Waje Analyst 项目上下文

## 项目定位

这是 Robin 负责的 Waje H5 真金游戏产品与数据分析项目，重点关注产品体验、核心玩法、商业化、用户偏好、运营状况、竞品市场和数据诊断。

Waje 的重点工作环境包括低端手机、弱网、页面稳定性、充值、下注、结算和提现等关键链路。涉及资金状态、用户信任和数据安全的结论必须谨慎核验。

## 目录约定

- `knowledge/`：项目知识库，按产品、数据、竞品、方法和运行资料分层维护。
- `knowledge/00-索引/`：项目首页、知识地图和资产地图。
- `knowledge/_generated/`：自动生成的知识/代码图谱，只能通过脚本更新，不要手工编辑。
- `scripts/`：资讯采集、清洗、分析、日报和任务编排脚本。
- `config/`：数据源和分析配置。
- `jobs/`：定时任务定义和管道清单。
- `data/raw/`：原始采集快照，禁止覆盖历史快照。
- `data/processed/`、`data/outputs/`：标准化数据、分析结果、日报运行日志。

## 常用命令

```bash
python3 tools/build_graph.py
python3 scripts/run_daily_pipeline.py
```

每日情报任务默认在 Asia/Hong_Kong 时区 19:33 执行。执行后检查 `data/outputs/YYYY-MM-DD/run-log.json`、失败来源和日报。

## 工作规则

1. 先读取相关知识库索引、方法规范和数据语义层，再做产品或数据分析。
2. 结论明确区分事实、推断、建议和待验证项；指标先说明口径、时间范围、粒度和来源。
3. 起源 TC-玩法、羊毛分析、GM 生命周期 V2、Metabase 玩家资产分析等内部数据只能在用户已授权的连接或脱敏文件范围内使用。
4. 不读取、输出或提交密码、Cookie、令牌、API Key、服务账号文件和未脱敏玩家明细。
5. 修改代码或配置前先检查现有工作区变更；使用可审阅的补丁方式，保留用户已有修改。
6. 资金相关链路重点关注幂等、重复扣款、重复下注、超时重试、状态恢复和审计证据。
7. 公开资讯需要保留来源链接、抓取时间和证据边界，不能把新闻标题直接当作已验证事实。
8. 与 Waje 项目密切相关的飞书、网页、PDF、Excel、图片和会议资料，完成拆解后默认写入对应 `knowledge/` 专题 Markdown，保留来源/revision/哈希和证据状态，并刷新知识图谱；如用户明确要求只回答、不入库，再跳过持久化。
9. 文档入库执行 [[knowledge/04-方法/相关文档拆解与知识入库默认工作流]]；涉及敏感资料时只保存脱敏规则、机制和验证要求，不复制证件号、账号、完整逐字稿或带授权码的原始资源。

## 企业 Gemini 专项入口（2026-09-04 调整）

- 协作仅用于本项目聊天中的复杂分析、数据处理、方案设计等任务，规则见AGENTS.md；简单日常任务用原默认轻量模型/脚本，不分派。用户确认Gemini网页Agent效果较好，偶有认证需求，保留复杂专项使用；只有本地Gemini CLI桥接调用暂停，--recovery-probe用于该CLI恢复测试。
- Codex 负责识别任务边界、选择 Agent、审计来源/口径/数据质量并完成最终可交付产物。简单润色、项目本地文件修改与最终质量把关可直接由 Codex 完成。
- Waje BigQuery 分析任务使用 `config/gemini-enterprise.json`、`tools/gemini_bridge.py` 和 `scripts/run_gemini_waje_analysis.py`。
- Firebase 多端设备/性能汇总使用 `scripts/run_gemini_multiplatform_firebase_analysis.py`；默认执行 `analysis/firebase_multiplatform_device_performance_2026_08_27/sql/summary/` 的窗口级聚合 SQL，不下载明细行。Gemini MCP 未通过安全门禁时，才按回执标记 `api_fallback` 并使用个人 ADC 的只读 BigQuery API 复核。
- 企业网页Agent按用户反馈作为可用专项通道：企业资料、授权聚合查询及跨资料研究适合时使用。偶发账户/凭证验证恢复同一授权会话即可，不受CLI门禁影响；网页的精确运行量和成功率未单独采集，不虚构这些统计。
- 企业 Gemini 只负责认证聚合视图的只读查询和初步解释；Codex 负责指标口径、数据质量、相关性边界和最终报告。
- BigQuery 数据项目与 Gemini/Vertex 运行项目分开维护；未确认 `runtime_project_id` 前不得真实调用。
- 模型名称是有序偏好而非硬性依赖：读取 `config/gemini-enterprise.json` 的 `model_fallback`，首选不可用时依次尝试候选模型，最后允许 Gemini CLI 使用企业默认模型；权限错误不通过更换模型绕过。
- 首次执行必须确认企业账号和企业 BigQuery 连接；认证失败标记为 `blocked_authentication`，不得切换个人账号或项目凭证。
- 查询只能使用 `SELECT/WITH`、日期过滤和授权对象；不得保存原始 CLI 输出、用户级明细、凭证或敏感字段。
- 网页 Agent 的会话、Cookie、账号信息和上传原文件不写入本地；只归档经审计的公开来源、授权聚合结果、来源链接和质量回执。
- Gemini 向 Codex 的交接应包含简明结论、结构化证据、来源/SQL、数据截止时间、质量状态和待确认项；避免回传原始网页、用户明细或冗长逐字材料，以控制 Codex 上下文消耗。
