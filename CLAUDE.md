---
type: project-map
status: active
updated: 2026-09-22
audience: [codex, gemini, product, data, engineering]
project: Waje Analyst
workspace: /Users/robin/Documents/wajetan_analyst
---

# Waje Analyst｜精简项目地图

> 本文件只提供稳定项目地图和入口，不是每个任务的必读全文。新任务默认使用根目录 `AGENTS.md`；需要项目结构时按段读取本文。续接任务优先读取 `analysis/thread_handoffs/<任务>/CURRENT.md` 与其中列出的回执。

## 1. 项目定位与权威顺序

本工作区用于 Waje Nigeria 的产品、数据、业务、游戏、竞品和市场分析，不是线上生产代码仓库。常见范围包括 H5/Web、Android、iOS、不同国家/渠道/分包版本，以及注册、留存、付费、生命周期、RTP、资产、支付提现、风控、性能和体验。

发生冲突时按以下顺序判断：

1. 用户本轮明确要求和当前任务范围。
2. 当前原始来源、服务端事实、授权只读查询、在线 revision 和运行回执。
3. 当前 `config/`、`jobs/manifest.json`、脚本和工作区状态。
4. `knowledge/` 中带日期、来源和证据状态的专题文档。
5. 历史交接、记忆和旧报告。

动态价格、额度、模型、权限、版本、页面和任务状态必须重新核验。历史记忆只能提供线索，不能覆盖当前事实。

## 2. 目录与入口

| 路径 | 责任 | 边界 |
|---|---|---|
| `knowledge/00-索引/` | 项目首页、知识地图、资产地图 | 项目导航首选 |
| `knowledge/01-产品/` | 产品、玩法、体验、PRD、版本、用户评价 | 产品事实与线索 |
| `knowledge/02-数据/` | 指标、埋点、生命周期、RTP、配置、看板 | 数据口径与契约 |
| `knowledge/03-竞品/` | 竞品、市场、舆情、日报和周报 | 公开来源证据 |
| `knowledge/04-方法/` | 证据、分析、查询和入库方法 | 质量门禁 |
| `knowledge/05-运行/` | 自动化、Lark、发版、浏览器和交付 SOP | 执行规范 |
| `knowledge/90-模板/` | 报告、工作日志和指标模板 | 新产物骨架 |
| `scripts/` | 采集、清洗、分析、校验、报告、Lark/Origin/GM 编排 | 先读参数和回执逻辑 |
| `config/` | 数据源、权限、质量和输出策略 | 配置候选不等于线上生效 |
| `jobs/` | 调度、输入、输出和失败策略 | 与实际 automation 交叉核对 |
| `tools/` | 图谱、策略和辅助审计 | 安全规则优先 |
| `data/raw/` | 原始快照 | 不覆盖、不保存凭据 |
| `data/processed/` | 标准化和索引数据 | 保留来源与质量状态 |
| `data/outputs/` | receipt、quality、run-log 和交付工件 | 退出码不等于业务成功 |
| `analysis/` | 专项 SQL、脚本、证据和报告 | 每个任务独立目录 |
| `analysis/thread_handoffs/` | 长任务检查点和换窗交接 | 不复制旧聊天全文 |
| `knowledge/_generated/` | 自动生成图谱 | 禁止手工编辑 |

高频入口：

- 项目首页：`knowledge/00-索引/项目首页.md`
- 知识地图：`knowledge/00-索引/知识地图.md`
- 资产地图：`knowledge/00-索引/资产地图.md`
- 分析证据规范：`knowledge/04-方法/分析方法与证据规范.md`
- 数据平台与报表：`knowledge/02-数据/数据平台与报表.md`
- 生命周期口径：`knowledge/02-数据/GM-Lifecycle-Pool-v2-数据统计口径与算法拆解-2026-08-25.md`
- 报告排版：`knowledge/05-运行/报告排版与配色规范-2026-09-07.md`
- 跨格式定稿：`knowledge/05-运行/报告定稿与跨格式同步工作流-2026-09-09.md`

## 3. 核心执行边界

### 3.1 工作区保护

工作区可能包含大量用户修改和未跟踪文件。禁止未经明确授权执行 reset、checkout、批量删除、清理、覆盖式同步、提交或推送。只修改任务直接相关文件；原始快照、历史报告和失败证据不得被新运行覆盖。

### 3.2 查询与数据

- 新查询先固定时间窗口、时区、端、包体、版本、渠道、游戏、生命周期、分母和币种。
- 只选必要字段，下推日期/分区和业务过滤；禁止默认扫描完整历史。
- BigQuery 默认使用企业 API/客户端库的受控只读 runner，执行 SQL 校验、窗口检查、dry-run 和字节/行数门禁。Remote MCP 不是前置条件。
- 缺失、未成熟、权限失败、页面异常和未执行不得写成 0 或成功。
- 用户级、设备级、订单级、KYC、支付和资产明细不得进入报告或普通交接包；默认使用授权聚合结果。

正式结论必须区分：事实、跨来源归纳、推断、建议和待验证项。公开来源只能支持公开事实；支付、提现、资产、RTP、收入、留存和真实故障必须回到服务端事实或授权聚合结果。

### 3.3 状态语义

使用 `ok`、`partial`、`degraded`、`blocked`、`auth_required`、`shortfall`、`immature`、`unknown`、`not_run`、`query_stale`。状态来自来源覆盖和回执，不从 HTML 存在、退出码为 0、日期控件或单次截图推断。

### 3.4 外部系统与授权

任何 Lark/Sheets、Ares/起源、GM、Metabase、Firebase、消息发送、配置发布或其他外部写入，必须处于用户明确授权范围。遇到登录或授权阻断，默认在 Codex 内置浏览器前台打开对应授权页；用户完成密码、验证码或同意操作后，再复核身份、目标资源和必要 scope。

不代填或保存密码、OTP、Token、API Key、Cookie、授权 URL 和个人账号数据；不切换账号或放宽权限。授权页已打开不等于授权完成。

## 4. 标准工作流

```text
任务识别
→ 固定范围、窗口、口径和权限
→ 读取相关索引、SOP、输入与最新回执
→ 来源/成熟度/质量预检
→ 原始快照或最小只读查询
→ 标准化、去重、计算与分析
→ 质量回执
→ 结论先行的交付
→ 外部写入回读（仅在已授权时）
→ 更新检查点或完成回执
```

每次交付至少说明：做了什么、没有做什么、窗口与时区、来源和权限、覆盖与质量、产物路径、回执状态、阻断和待确认项。

## 5. 报告与产物标准

- 用户最后修改或确认的版本是内容和排版基准；同步前读取最新全文、revision 和哈希，解决冲突后再写。
- 分析、评估和总结报告默认交付可读 HTML，Markdown 作为项目存档；飞书仅在获得创建或同步授权时写入。
- 正文顺序：结论 → 核心指标 → 事实发现 → 原因/风险 → 行动 → 验收。
- 重要数字、决策和行动加粗；方法、限制和证据边界下沉到就近备注。
- 交付前运行 `node scripts/check_report_quality.mjs --input <artifact.json|report.md|report.xml>`；HTML 使用 `scripts/deliver_readable_report.mjs`，并完成桌面、窄屏和必要的飞书回读。

JSON receipt 至少包含：

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

## 6. 上下文、检查点与记忆

- 每个聊天只处理一个独立成果；不同报表、外部写入、浏览器流程和代码改造分开建聊天。
- 当剩余上下文约 35% 或更低、系统即将压缩、关键阶段完成、准备产生大型输出或需要换窗时，先生成 `CURRENT.md`：

```bash
python3 scripts/create_thread_checkpoint.py \
  --task "任务名称" \
  --slug task-slug \
  --objective "本轮具体目标" \
  --scope analysis/相关任务目录 \
  --next "下一步动作"
```

- 统一模板：`analysis/thread_handoffs/TEMPLATE.md`。
- 新聊天只读 `AGENTS.md`、任务 `CURRENT.md` 和其中列出的最新回执，不导入旧聊天全文。
- 大型 DOM、JSON、SQL 结果、表格和日志落盘；聊天只保留摘要和路径。
- 记忆库只用于稳定偏好、历史失败模式和检索线索；当前进度、在线 revision、权限、数据窗口和最新产物必须以检查点及回执为准。

## 7. Agent 与工具状态

- Claude Code Agent 分派已停用；`config/agent_dispatch.json` 为 `enabled: false`。桥接代码和历史回执只读保留。
- Gemini 网页 Agent 仅在用户授权、企业会话可用且结果可验收时用于复杂专项。
- 本地 Gemini CLI 权限未开通，不调用、不探测、不恢复。
- 简单日常流程使用既有脚本和默认模型，不启动多 Agent。

## 8. 快速接手

新任务：

```bash
cd /Users/robin/Documents/wajetan_analyst
git status --short
git branch --show-current
```

然后只读取与当前主题直接相关的知识索引、SOP、输入数据和最新回执。

续接任务使用：

```text
继续“<任务名>”。先读取 AGENTS.md、analysis/thread_handoffs/<任务>/CURRENT.md，
以及 CURRENT.md 中列出的最新回执。以当前文件、在线状态和用户最新指令为准；
不要导入旧聊天全文，不重复已完成步骤。
```

## 9. 维护原则

本文只保留稳定地图和边界。动态状态写入任务检查点和回执；详细方法写入 `knowledge/`；自动生成图谱仅通过脚本刷新。项目结构、数据架构或交付契约发生重大变化时再更新本文日期。
