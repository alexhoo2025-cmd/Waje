---
type: project-handoff
status: active
updated: 2026-09-04
audience: [claude-code, codex, gemini, product, data, engineering]
project: Waje Analyst
workspace: /Users/robin/Documents/wajetan_analyst
---

# Waje Analyst 项目交接手册

> 本文件是 Claude Code 进入 `/Users/robin/Documents/wajetan_analyst` 后的首要项目上下文。它提供稳定的项目地图、读取顺序、工作规范、数据边界和交付标准；不替代专题文档中的详细定义，也不包含任何密钥、Cookie、Token、密码或个人明细。

## 0. 接手原则

### 当前协作策略（2026-09-04 更新）

仅对用户在本项目各聊天中交付的复杂分析、数据处理、方案设计和开发任务按需分派。简单任务及Play报告、竞品周报、晨会、配置差异流程用原默认轻量模型和脚本，不协作。参见AGENTS.md及tools/claude_collaboration.md，入口tools/claude_bridge.py，配置config/agent_dispatch.json。模型按子任务能力选择，不设每日预算限制。Gemini网页Agent用户确认效果较好，保留复杂专项使用；本地Gemini CLI权限未开通，完全排除，不自动恢复或探测，不能混同。

### 0.1 项目定位

这是 Waje Nigeria 真金/社交游戏产品的数据、产品、业务、竞品和市场分析工作区，不是 Waje 线上生产代码仓库。主要分析对象包括 H5/Web、Android、iOS、不同国家/渠道/分包版本，以及注册、首局、充值、下注、结算、提现、生命周期、风控和用户体验。

### 0.2 当前主线

- H5/PWA 新手路径、加载/可玩/可下注、弱网、设备性能和稳定性。
- Firebase、Ares/起源、BigQuery、Metabase、GM 的数据覆盖、质量和报表整合。
- 新用户留存、付费、生命周期、渠道/版本对比和 Dn Day 口径。
- For You 推荐模块、APP/H5 埋点、服务端推荐事件和复玩归因。
- 自研 H5 游戏的加载、可玩、下注和结算埋点契约。
- 游戏、RTP、TC、奖励、资产流水、支付、提现和 KYC/风控诊断。
- Waje 与竞品的产品、活动、支付提现、市场、监管、公开舆情和 Google Play 评价。
- Lark 会议/知识库、Origin 新用户分析、GM Lifecycle Pool V2 和配置资料库的受控更新。

### 0.3 权威优先级

遇到冲突时按以下顺序判断，不要凭记忆猜测：

1. 用户本轮明确要求和当前任务范围。
2. 当前可访问的原始来源、服务端事实、只读查询结果和运行回执。
3. 当前 `config/`、`jobs/manifest.json`、脚本入口和工作区设置。
4. `knowledge/` 中带来源和日期的专题文档。
5. 外部记忆库中的历史回顾。

动态价格、模型、版本、权限、额度、页面状态和运行状态必须重新核验；历史文档和记忆只能提供上下文。

### 0.4 首次接手只读检查

```bash
cd /Users/robin/Documents/wajetan_analyst
pwd
git branch --show-current
git status --short
sed -n '1,260p' GEMINI.md
sed -n '1,240p' knowledge/00-索引/项目首页.md
sed -n '1,240p' knowledge/00-索引/知识地图.md
sed -n '1,240p' knowledge/00-索引/资产地图.md
sed -n '1,220p' jobs/manifest.json
```

先确认日期、时区、包体、版本、数据窗口、权限和工作区变更，再运行任何可能写入文件或外部系统的步骤。

### 0.5 工作区保护

当前工作区曾长期存在大量已修改和未跟踪内容。所有现有变更默认属于用户：

- 不执行 `git reset --hard`、`git checkout --`、批量删除、全量清理或覆盖式同步。
- 不因文件未纳入 Git 就把它当作临时文件；先查看路径、来源和修改时间。
- 不自动提交、推送、切分分支或整理无关变更。
- 修改文件前先确认目标文件与任务直接相关；优先使用可审阅的补丁。
- 生成目录、原始快照和历史报告不得被新运行覆盖。

## 1. 知识库导航

### 1.1 推荐读取顺序

1. `knowledge/00-索引/项目首页.md`
2. `knowledge/00-索引/知识地图.md`
3. `knowledge/00-索引/资产地图.md`
4. `knowledge/00-索引/Agent项目背景与知识图谱快速上手-2026-08-17.md`
5. `GEMINI.md`
6. 目标主题对应的产品、数据、竞品、方法或运行规范
7. 对应的原始快照、标准化数据、质量回执、运行日志和报告工件

如果任务涉及指标，先读 `knowledge/04-方法/分析方法与证据规范.md`。如果任务涉及文档拆解/入库，先读 `knowledge/04-方法/相关文档拆解与知识入库默认工作流.md`。如果任务涉及最终报告，先读 `knowledge/05-运行/分析报告交付与HTML渲染规范-2026-08-14.md` 和必要的飞书发布 SOP。

### 1.2 目录职责

| 目录 | 内容 | 使用方式 |
|---|---|---|
| `knowledge/00-索引/` | 项目首页、地图、资产关系、Agent 上下文 | 进入项目的导航层 |
| `knowledge/01-产品/` | 产品总览、玩法、体验、PRD、版本、用户评价 | 产品和体验事实/线索 |
| `knowledge/02-数据/` | 平台、指标、埋点、生命周期、RTP、配置、看板、风控 | 口径、契约、查询和验收 |
| `knowledge/03-竞品/` | 竞品、市场、公开舆情、公众号、日报和周报 | 公开来源和市场信号 |
| `knowledge/04-方法/` | 证据等级、分析模板、入库与报告方法 | 方法和质量门禁 |
| `knowledge/05-运行/` | 自动化、发版、Lark、体验、工作日志、交付 SOP | 执行和协作规范 |
| `knowledge/90-模板/` | 工作日志、指标、主题笔记模板 | 新文件结构参考 |
| `knowledge/_generated/` | `code-graph.json`、代码与资产图谱 | 自动生成；禁止手工编辑 |

### 1.3 高频入口

- 产品总览：`knowledge/01-产品/Waje产品总览.md`
- 项目知识库索引：`knowledge/README.md`
- 产品部门索引和扫描：`knowledge/01-产品/产品部门知识库总览-2026-08-31.md`、`产品部门文档索引-2026-08-31.md`
- 公开情报管道：`knowledge/03-竞品/每日产品与竞品情报管道.md`
- 数据平台与报表：`knowledge/02-数据/数据平台与报表.md`
- 埋点地图：`knowledge/02-数据/埋点与数据上报地图.md`
- H5 全量埋点盘点：`knowledge/02-数据/Waje-H5起源埋点上报全量盘点-2026-08-28.md`
- H5 自研游戏埋点：`knowledge/02-数据/Waje自研游戏H5加载、可玩与可下注埋点上报需求-V2-2026-09-01.md`
- For You 埋点：`knowledge/02-数据/For You推荐模块APP-H5埋点开发需求-2026-08-31.md`
- 多端性能看板：`knowledge/02-数据/Waje多端设备与性能报表看板需求-V3-六模块-2026-09-02.md`
- RTP/资产诊断：`knowledge/02-数据/Waje-TC异常、RTP与资产流水诊断框架-2026-08-28.md`
- 生命周期口径：`knowledge/02-数据/GM-Lifecycle-Pool-v2-数据统计口径与算法拆解-2026-08-25.md`
- 运行规范：`knowledge/05-运行/Codex Spark自动化任务矩阵与调度规范-2026-08-21.md`

## 2. 项目、代码和配置地图

### 2.1 物理目录

| 路径 | 责任 | 关键边界 |
|---|---|---|
| `scripts/` | 采集、清洗、分析、报告、校验、Lark/Origin/Phenix 编排 | 先读脚本参数和回执逻辑，再运行 |
| `config/` | 数据源、权限、质量、输出和任务配置 | 不把配置候选当成线上生效事实 |
| `jobs/` | 任务清单、调度、输入/输出和失败策略 | 与外部 Codex automation 定义交叉核对 |
| `tools/` | 图谱、Gemini/BigQuery 策略和辅助审计 | 安全策略优先于方便查询 |
| `data/raw/` | 原始网页、授权导出和批次快照 | 不覆盖历史；不存凭据或个人明细 |
| `data/processed/` | 标准化、去重、索引和受控中间结果 | 记录来源和质量状态 |
| `data/outputs/` | 分析结果、receipt、quality、run-log、交付工件 | 进程成功不等于业务成功 |
| `analysis/` | 按日期/主题保存 SQL、脚本、证据、工件和回执 | 当前工作区已有大量历史与未跟踪分析目录 |
| `agent_runtime/` | 设备性能等 Agent 的运行配置和依赖 | 先看各自 README/requirements |
| `workflows/` | 手动流程说明，如生命周期联合周更 | 不把浏览器人工流程改成无头定时任务 |
| `.venv/`、`.venv-wechat/`、`node_modules/` | 本机运行环境 | 不当作业务源代码或知识事实 |

### 2.2 核心脚本入口

#### 公开情报和报告

- `scripts/collect_intelligence.py`：公开来源采集。
- `scripts/normalize_intelligence.py`：标准化、去重和统一字段。
- `scripts/analyze_intelligence.py`：主题、实体、情绪、重要性和变化分析。
- `scripts/assess_intelligence_quality.py`：来源覆盖、失败和质量状态。
- `scripts/build_daily_intelligence_report.py`：历史日报报告。
- `scripts/run_weekly_intelligence_pipeline.py`：周批次采集或报告阶段。
- `scripts/build_weekly_intelligence_html.py`：总周报 HTML 交付。

#### Google Play 用户评价

- `scripts/collect_play_reviews.mjs`：浏览器采集。
- `scripts/play_review_index.py`：稳定评价 ID、版本和去重索引。
- `scripts/normalize_play_reviews.py`、`analyze_play_reviews.py`：标准化与分析。
- `scripts/assess_play_reviews_quality.py`：短缺、重复、失败来源和质量回执。
- `scripts/build_play_reviews_knowledge.py`、`build_play_reviews_report.py`：知识库和报告。
- `scripts/run_play_reviews_pipeline.py`：日报/周报编排入口。

#### Lark、Origin、GM 和配置

- `scripts/run_lark_meeting_minutes_pipeline.py`：晨会智能纪要只读入库。
- `scripts/collect_lark_messages.py`、`parse_lark_messages.py`：Lark 内容采集与解析。
- `scripts/collect_lifecycle_pool.mjs`：Lifecycle Pool 浏览器流程。
- `scripts/update_lark_lifecycle_*`、`validate_lark_lifecycle_*`：生命周期工作簿准备、更新和验证。
- `scripts/update_origin_new_user_workbook.mjs` 及相关 `prepare/build/finalize/validate` 脚本：Origin 新用户工作簿流程。
- `scripts/run_waje_config_weekly.py`、`scripts/waje_config_workbook.py`：配置资料库 revision/Sheet 差异。

#### Phenix、Firebase、BigQuery 和 Agent 协作

- `scripts/run_phenix_*`：Phenix 渠道、Firebase、H5PHX、归因、留存/付费和审计流程。
- `scripts/run_gemini_waje_analysis.py`、`run_gemini_competitor_trial.py`、`run_gemini_multiplatform_firebase_analysis.py`：企业 Gemini 协作入口。
- `scripts/run_bigquery_mcp_preflight.py`：BigQuery MCP 只读安全预检。
- `tools/gemini_bridge.py`、`tools/gemini_model_routing.py`：企业 Gemini 认证/模型路由/交接契约。
- `tools/bigquery_mcp_policy.py`、`tools/firebase_multiplatform_policy.py`：查询和 Firebase 来源边界。
- `tools/build_graph.py`：扫描知识、脚本和相对关系，生成 `knowledge/_generated/`。

### 2.3 配置入口

- `config/intel_sources.json`：公开情报主题、实体、搜索词和来源关系。
- `config/weekly_intelligence.json`：周批次窗口、时间和输出。
- `config/play_reviews.json`：Play 包体、市场、排序、滚动、目标数量和索引。
- `config/lark_meeting_minutes.json`：晨会检索范围、Owner、回看天数、输出和隐私。
- `config/waje_config_workbook.json`：配置工作簿来源、revision、读取和存储策略。
- `config/release_experience_watch.json`：发版检测、状态和体验监控门槛。
- `config/report_output_policy.json`：默认格式、报告角色、质量和回读要求。
- `config/gemini-enterprise.json`：企业 Gemini 专项恢复门禁、模型回退、Firebase 白名单、聚合输出和权限边界；通用默认路由见 config/agent_dispatch.json。
- `config/bigquery_mcp_policy.json`：只读 SQL、项目、允许视图、字节和行数限制。

`package.json` 当前主要提供 Playwright 相关 Node 入口；Python 依赖见 `requirements-wechat.txt` 和各 Agent 的 requirements 文件。不要因为某个配置里存在模型名、项目名或候选表名，就直接认定它当前可用；先做权限、revision、来源和时间窗口核验。

## 3. 数据架构与业务边界

### 3.1 系统职责

```text
客户端 / 服务端 / 配置后台
          ↓
原始事件、订单、结算、资产和配置事实
          ↓
BigQuery 统一统计/认证层
      ↙        ↓        ↘
   Ares/起源   GM     Metabase/BI
          ↓
产品、运营、商业化、风控和竞品决策
```

| 系统 | 主要职责 | 默认边界 |
|---|---|---|
| Ares/起源 | 埋点、行为分析、报表集市、质量和用户/页面/模块分析 | 用于正式业务入口和埋点语义；确认引擎/版本 |
| BigQuery | 事件、订单、游戏、下注、派奖、生命周期、RTP、质量和安全汇总 | 统计事实首选；只读、聚合、带日期过滤 |
| MySQL | 字典、配置、事件定义、系统元数据和权限 | 元数据/配置参考；不要在报告中硬编码 |
| GM | Lifecycle Pool、RTP、运营排障和历史回溯 | 排障与既有报表；口径必须注明 |
| Metabase | 受控查询、验证和专题看板 | 仅使用授权数据集/视图，避免生产明细下钻 |
| Firebase | Analytics、Crashlytics、ANR、Performance | 性能/稳定性线索，不替代服务端交易事实 |
| Impala | 旧统计引擎 | 迁移对账用途；新分析优先 BQ |
| 企业 Gemini | 公开检索、长文档、授权聚合查询、多源比较、报告初稿 | 必须有企业身份、运行项目和质量回执 |
| Claude/Codex | 任务路由、代码执行、来源/指标审计、最终编辑和交付 | 不绕过权限，不把模型输出当证据 |

### 3.2 新包、老包和配置状态

- `new_current_primary`：当前新包主分析对象，可用于新包 KPI、版本、留存、LTV、付费、RTP 和风控。
- `old_historical_reference`：老包/历史机制，只用于历史演进、假设和字段参考。
- `current_candidate`：配置工作簿中的可能当前配置，只能触发验证任务，不能证明线上生效。
- `historical_reference` / `obsolete`：历史或作废资料，不得混入当前统计。

新包与老包即使出现同名游戏或策略，也只能写成机制演进对照；不得混合分母、KPI、RTP、LTV、支付或风控结果。任何配置结论需尽可能关联 `config_version`、生效时间、服务端快照或命中日志。

### 3.3 关键指标底线

- 留存：确认注册日/首登日/首局日、成熟 cohort、时区和 Dn Day 命名；未成熟 D7/D15/D30/D60 不填 0。
- 付费：先明确分母是注册用户、首登用户、新用户还是成熟 cohort；货币、退款、冲正和金额口径必须一致。
- 实际 RTP：优先使用 `final settled payout / effective real-money stake`；排除取消、退款、失败、重复、未结算、免费筹码污染，并记录有效局数和数据截止时间。
- TC/TX/GM 回报比：沿用源报表定义，记录基础/完全下注额、资产类型、分母、汇总方式和完整日；不能互相替代。
- 支付/提现：服务端订单、回调、账本和到账事实优先；客户端点击只能说明路径体验。
- 性能/稳定性：客户端事件、Firebase 和 H5 信号用于诊断；没有遥测时写 `data_gap`，不能写成没有问题。
- 指标报告：每个指标至少写“定义、算法、分母、来源、粒度、维度、时间窗口和质量状态”。

### 3.4 证据等级

沿用 `knowledge/04-方法/分析方法与证据规范.md`：

| 等级 | 含义 | 可用方式 |
|---|---|---|
| A | 内部明细/平台数据，可复算 | 定量结论和决策，仍需隐私与授权边界 |
| B | 内部报表或人工核验结果 | 运营判断，注明口径和复核范围 |
| C | 官方公开页面、商店、帮助文档 | 功能、市场和产品信号 |
| D | 评论、访谈、单次体验、未验证推测 | 只能作线索，必须安排验证 |

## 4. 企业 Gemini、BigQuery 和隐私边界

### 4.1 Gemini 协作

当前 `config/gemini-enterprise.json` 采用企业网页优先、按任务委派的设计：

- 通用公开资料分析、长文档拆解、多来源比较和报告初稿按新机制委派 Claude；授权查询由主Agent或已验证企业通道承担，Claude仅接收精选脱敏聚合结果。
- Claude/Codex 负责任务范围、指标定义、来源审计、质量判断和最终交付。
- `model_fallback` 只处理模型不可用、临时故障、超时或无效 JSON；权限、许可证和 SQL 安全错误不能靠换模型绕过。
- 先确认企业账号、运行项目、区域和允许对象；未确认前不得真实调用。
- Gemini 交接包只返回简明结论、结构化证据、来源/SQL、数据截止时间、质量状态和开放问题。

### 4.2 BigQuery 规则

- 只读 `SELECT/WITH`，带日期/分区过滤和明确字节/行数上限。
- 优先使用已批准的安全视图；当前 `allowed_datasets`/`allowed_views` 为空或权限未通过时，状态为 `blocked`/`auth_required`，不是零数据。
- 只输出聚合结果、指标和质量回执；不下载或展示用户、KYC、支付、设备、订单、账号或明细行。
- 任何新 SQL 先核对表名、字段、分区、币种、时区和数据截止时间，不使用猜测表名。
- 服务端事实、客户端路径、配置候选和公开页面信号必须分层展示。

### 4.3 禁止保留的内容

项目文件、知识库、报告、日志和交接包不得保存：

- API Key、App Secret、Token、Cookie、密码、服务账号文件和 OAuth 凭据；
- 手机号、邮箱、open_id、用户/设备明细、订单号、银行账户、BVN/NIN 和生物识别信息；
- 完整会议逐字稿、原始私聊、浏览器 Profile 或含授权码的截图/直链；
- 未经脱敏的原始附件和不可公开传播的第三方资料。

需要记录时只保留规则、字段、流程、阈值、来源定位、哈希和验证要求。

### 4.4 Claude Code 成本/模型路由

当前机器的 Claude Code 通过本地代理使用 Claude Code 官方别名，并将别名精确映射到 provider-prefixed model ID；这些设置位于用户环境和 `~/.claude/settings.json`，不写入项目配置或交接文档中的密钥。当前代理已验证 `anthropic/claude-opus-5`、`anthropic/claude-sonnet-5` 和 `anthropic/claude-haiku-4.5`，暂未提供 `anthropic/claude-haiku-5`。

| 任务类型 | 默认模型 | 使用边界 |
|---|---|---|
| 简单检索、文件索引、格式化、摘要、字段检查、低风险机械修改 | `haiku` → `anthropic/claude-haiku-4.5` | 优先节省 Token；不负责高风险结论 |
| 日常产品/数据分析、脚本开发、常规调试、多文件修改、报告初稿 | `sonnet` → `anthropic/claude-sonnet-5` | 当前全局默认，兼顾质量、速度和成本 |
| 复杂架构、跨域诊断、金融/RTP/KYC/安全、生产影响评估、最终高风险审计 | `opus` → `anthropic/claude-opus-5` | 必须有明确复杂度/风险理由；完成后回到 Sonnet/Haiku 做整理 |

效率与模型路由规则（费用仅记录，不设默认预算门槛）：

- 新会话默认使用 Sonnet 5；不要因为“可能更好”直接使用 Opus。
- 简单任务可使用 `claude-quick`；复杂任务可使用 `claude-deep`。
- 项目非交互协作使用 `tools/claude_bridge.py`；不调用全局 `claude-fallback`。Haiku不可用可升级Sonnet，Sonnet不可用可升级Opus，不自动降低复杂任务的模型能力。
- 子 Agent 默认使用 Haiku 4.5；只有需要跨文件推理、复杂代码修改或高风险判断时，显式提升为 Sonnet/Opus。
- P0 资金、提现、RTP、KYC、风控、权限和生产配置任务不得自动降级后直接形成结论；回退后必须标记并人工复核。
- 缩小上下文、优先读取索引/摘要/回执、避免重复读取同一原文；不要为简单任务启动多个并行 Agent。
- 代理模型列表、权限、价格和额度是动态事实；开始任务前可用 `/status`、`/model` 或代理 `/v1/models` 重新核验。

## 5. 标准工作流

### 5.1 任务执行链

```text
任务识别
→ 范围/日期/时区/包体/版本确认
→ 知识、来源和权限预检
→ 数据质量/可达性/成熟度检查
→ 原始快照或只读聚合查询
→ 标准化、去重、分析
→ 质量回执和失败分流
→ 结论先行的报告
→ 知识库回写
→ 必要时刷新图谱
→ 输出路径、来源、状态和待确认项
```

### 5.2 执行要求

1. 先说明任务属于产品、数据、游戏/RTP、支付风控、版本、竞品、Lark、运行维护或代码工具。
2. 固定窗口、时区、端、包体、版本、渠道、游戏、生命周期和分母。
3. 先读对应专题文档、配置、原始输入和上一轮质量回执。
4. 先判断权限/来源/样本/日期是否完整；阻断时停止受限阶段。
5. 原始快照不可覆盖；同一批次重复运行要幂等。
6. 同时检查进程退出码、`run-log.json`、`quality.json`、`manifest.json`、实际数据和报告内容。
7. 结论按“事实 → 解释/推断 → 风险 → 建议动作 → 验收指标”组织。
8. 任何外部写入、消息发送、支付/提现、配置发布、清空表格或权限绕过前，必须获得明确授权。

### 5.3 状态语义

| 状态 | 含义 |
|---|---|
| `ok` | 目标阶段执行完成，来源和质量满足门槛 |
| `partial` | 部分来源/日期/字段可用，仍有明确缺口 |
| `degraded` | 结构或部分产物完成，但关键来源/质量/交付下降 |
| `blocked` | 权限、登录、网络、页面或安全门禁阻止执行 |
| `auth_required` | 需要恢复原授权身份或用户会话 |
| `shortfall` | 采集完成但样本/目标数量不足 |
| `immature` | cohort 或统计窗口尚未成熟 |
| `unknown` | 当前证据不足以判断 |
| `not_run` | 设计了阶段但未实际调用 |
| `already_running` | 已有同批次/同任务运行，禁止并发重入 |

缺失、空快照、未执行、页面 401/403、短缺和数据延迟不能转成 `ok` 或 0 值。公开评论、论坛和单次体验不能直接证明故障、收入、留存、LTV、RTP 或刷量。

## 6. 自动化任务矩阵

任务清单以 `jobs/manifest.json` 为项目内入口；外部 Codex automation 定义位于用户级 automation 目录，时间、模型和状态需现场复核，不能只看历史记忆。

| 任务 | 当前计划 | 入口 | 结果重点 |
|---|---|---|---|
| 晨会智能纪要 | 工作日 10:15 | `run_lark_meeting_minutes_pipeline.py` | Lark 身份预检、去标识摘要、事件台账和本地回执 |
| Google Play 评价日报 | 每日 20:20 | `run_play_reviews_pipeline.py --period daily` | 未入库评价、稳定 ID 去重、短缺/阻断和日报 |
| Google Play 评价周报 | 周一 08:00 | `--period weekly --skip-collect` | 上周一至周日汇总和专项周报 |
| 总周报 HTML | 周一 10:00 | `build_weekly_intelligence_html.py` | HTML、artifact、delivery receipt 和缺失日期 |
| 周情报/公开来源采集 | 周五 15:00 | `run_weekly_intelligence_pipeline.py --mode collect` | 周批次、公开来源、Play/公众号和发布监测 |
| 配置资料库更新 | 周五 15:00 | `run_waje_config_weekly.py` | revision、全部 Sheet/隐藏页、差异和本地索引 |
| 周情报报告 | 周五 17:00 | `run_weekly_intelligence_pipeline.py --mode report` | 产品/竞品/Play/公众号报告、质量和图谱 |
| 旧每日总情报 | 历史手动 | `run_daily_pipeline.py` | 仅兼容历史批次，不作为当前主调度 |

注意：`jobs/manifest.json` 中记录的模型字段可能滞后于用户级 automation 实际配置；涉及模型切换时先查看实际 automation 定义，保持原调度、项目、提示词、通知和隐私设置。

### 6.1 浏览器和外部写入任务

GM Lifecycle Pool、Origin 新用户工作簿、飞书在线表格清空/格式/批量写入以及需要 Google 验证的页面任务保持手动流程。原因是它们依赖已登录浏览器、可见筛选、用户确认、历史查询或外部写入授权，不得改成无头定时任务。

### 6.2 常见失败处理

- Play `Newest` 元素 DOM detach、Chromium 启动失败或页面超时：保留 raw/receipt，标 `blocked/degraded/shortfall`，不要写成无评论。
- Lark `auth_required` 或 user token 失效：恢复同一用户授权，不切换 Bot/个人身份，不把候选数 0 当无会议。
- Gemini `runtime_project_id_missing`、IAM/许可证失败：标 `blocked`，不切换个人 Key/项目绕过。
- BQ 表/字段/SQL 不明确：输出模板或待研发映射，不能虚构结果。
- 报告构建成功但采集失败：以采集和质量状态为准；HTML marker 通过不等于业务成功。
- 任何页面/插件 401/403：视为访问阻断，不能推断没有数据。

## 7. 产出物与交付标准

### 7.1 默认格式

依据 `config/report_output_policy.json`：

- 飞书云文档是团队主阅读/评审版本，若有授权连接；
- Markdown 是项目存档、差异比较和知识库来源版本；
- HTML/PDF 只有用户明确要求离线分享、打印、外部发送或归档时才追加；
- Claude Code 没有可用飞书连接时，明确记录 `not_run`/`blocked`，不能把本地 Markdown 当作已发布飞书文档。

### 7.2 Markdown 报告结构

```text
标题 / 日期 / 来源与统计窗口
执行摘要（结论先行）
范围、口径和证据边界
核心指标与质量状态
事实发现
分群/版本/渠道/玩法拆解
原因、风险和不确定性
产品/运营/数据/研发行动
验收指标与回归标准
来源、抓取时间、缺失项和待确认事项
```

重要数字、结论和行动加粗；方法、限制和数据边界放入就近备注；使用业务语言解释 cohort、LTV、RTP、TC 等术语。

### 7.3 JSON receipt 最低契约

```json
{
  "status": "ok|partial|degraded|blocked|shortfall|auth_required|immature|unknown|not_run",
  "run_at": "ISO-8601",
  "window": {"start": "...", "end": "...", "timezone": "..."},
  "source_coverage": {},
  "quality": {},
  "artifacts": [],
  "verification": {},
  "open_questions": []
}
```

实际项目可增加字段，但不得删除来源、窗口、状态、质量、产物、验证和待确认项。receipt 不保存原始凭证、用户明细或完整网页/会议原文。

### 7.4 HTML/PDF 质量

- 自包含、响应式、无不必要外部资源；
- 桌面和移动端均可阅读；
- 图表配一句直接结论，表格有可访问的表头和单位；
- 报告保留 `validation/package/verification` 或同等回执；
- 没有浏览器时标记 `structural_only`，不能声称完成视觉验收。

## 8. 记忆库接入

### 8.1 入口

- 主索引：`/Users/robin/.codex/memories/MEMORY.md`
- 相关回顾：`/Users/robin/.codex/memories/rollout_summaries/`

### 8.2 使用方法

1. 先按 `wajetan_analyst`、主题名、脚本名、状态或路径检索 `MEMORY.md`。
2. 只有主索引直接指向时，读取 1–2 个最相关的 rollout summary。
3. 只提取历史决策、已知失败模式、用户偏好和复核边界。
4. 以当前配置、代码、运行日志和用户最新指令覆盖旧记忆。
5. 记忆库默认只读；只有用户明确要求更新时，才按记忆更新流程写入单独的 ad-hoc note。

记忆不能证明当前权限、模型、价格、数据、部署或任务状态。无法访问记忆库时说明 `memory_unavailable`，继续依据项目内现行文件，不自行补猜。

## 9. 当前状态快照（接手时必须复核）

本段是截至 2026-09-04 的交接快照，不是永久事实：

- 工作区：`/Users/robin/Documents/wajetan_analyst`；当前 Git 分支为 `main`，工作区包含已修改和未跟踪内容，必须先保护再操作。
- 知识库最近集中更新在多端设备/性能看板、H5 自研游戏埋点、For You 埋点、Firebase→BigQuery 导出审计、Phenix 归因/留存/付费、TC/RTP、生命周期和新用户工作簿。
- `knowledge/_generated/` 已存在大规模生成图谱变更；除非用户明确要求，不要为单个交接文档自动重建图谱。
- 当前高风险/高频缺口：物理表和字段映射、BigQuery/Gemini 运行权限、配置生效证据、H5 遥测完整性、Lark/Origin/GM 登录态、公众号授权来源、Play 浏览器稳定性和模型/套餐动态。
- 外部 Codex/GPT 额度监测属于用户级 automation，不等于项目脚本任务；查看实际 automation 文件确认状态和调度。
- 价格、额度、模型、版本、套餐权益和第三方平台可用性均为动态事实，交接文档只提供核验入口，不固化实时值。

## 10. 安全、协作和变更协议

### 10.1 协作回复最低要求

每次交付至少说明：

- 做了什么、没有做什么；
- 实际时间窗口、数据截止时间和时区；
- 来源、权限状态、样本/字段覆盖和证据等级；
- 产物路径、receipt/run-log/quality 状态；
- 缺失、阻断、未成熟、冲突和下一步核验。

### 10.2 新知识入库

相关外部文档、网页、PDF、Excel、图片、Lark 资料和会议内容默认拆解后写入相应 `knowledge/` 专题，保留来源、revision/content hash、抓取时间、证据状态和待确认项。用户明确要求“只回答、不入库”时才跳过持久化。

成熟结论回填主题笔记；工作日志只记录过程。新增跨资产关系时优先更新 `knowledge/00-索引/资产地图.md`，再按需要运行 `python3 tools/build_graph.py`。

### 10.3 变更前确认

以下动作必须取得明确授权，不能从“分析/交接/检查”推断授权：

- 写入或修改线上 Lark/Sheets、Ares、GM、Metabase、Firebase 或云端配置；
- 发送 Lark/邮件/IM 消息；
- 真实支付、下注、提现、批量领取或风控绕过；
- 删除、覆盖、重置、提交、推送或大范围重写现有文件；
- 使用个人凭证替代企业身份，或把敏感内容发给第三方服务。

## 11. Claude Code 快速启动清单

### 11.1 只读启动

```bash
cd /Users/robin/Documents/wajetan_analyst
pwd
git status --short
git branch --show-current
find knowledge/00-索引 knowledge/04-方法 knowledge/05-运行 -maxdepth 1 -type f -print | sort
python3 -m json.tool jobs/manifest.json >/dev/null
python3 -m json.tool config/report_output_policy.json >/dev/null
```

### 11.2 任务开始前

```text
确认任务类型
确认时间窗口、时区、端、包体、版本、渠道、游戏和分母
确认知识文档、配置、输入数据和最新 receipt
确认读/写权限与外部授权
确认当前 Git 变更不被覆盖
```

### 11.3 任务结束前

```text
检查实际数据和质量回执，不只看退出码
区分事实、推断、建议、待验证和未执行
保留原始快照与失败证据
写入正确知识目录或明确说明未入库
给出产物路径、来源、状态、缺口和下一步
```

## 12. 文档维护

- 稳定规则和目录结构变化时更新对应章节，并修改 front matter 的 `updated` 日期。
- 当前状态只记录高价值的项目主线、阻断和待复核项；不要把每日数据、密钥或长日志复制进来。
- 发现本文与 `GEMINI.md`、`knowledge/00-索引/Agent项目背景与知识图谱快速上手-2026-08-17.md` 或 `jobs/manifest.json` 冲突时，以当前用户指令、现行配置/回执和最新专题文档为准，并在任务结果中说明冲突。
- 这是项目交接入口，不是所有主题的百科；详细定义应留在对应知识文档，避免根文件膨胀和多处口径漂移。

> 一句话交接：这是一个以 Waje 新包为当前主线、以 BigQuery/服务端事实为统计底座、以 Ares/起源为正式分析入口、以 GM/Metabase/Firebase 为查询与诊断补充、以埋点质量和版本回归保证可信度的产品与业务分析项目；任何结论都必须带窗口、口径、端/包体/版本和证据状态。
