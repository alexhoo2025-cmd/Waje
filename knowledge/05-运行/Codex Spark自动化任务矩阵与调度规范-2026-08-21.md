---
type: operating-guide
domain: automation
status: active
owner: analyst
updated: 2026-08-21
tags: [codex-spark, automation, scheduler, quality, waje]
sources:
  - ../../jobs/manifest.json
  - ../../knowledge/03-竞品/每日产品与竞品情报管道.md
---

# Codex Spark 自动化任务矩阵与调度规范

## 结论

项目中凡是“固定入口、固定参数、可写本地回执、可重复验证”的任务统一使用 `gpt-5.3-codex-spark`。Spark 负责启动脚本、检查回执、判断成功/降级和交付本地产物；脚本负责数据口径、去重、质量门槛和文件写入。

需要登录浏览器、可见筛选、人工点击“查询历史记录”、确认筛选口径或向飞书在线表格外部写入的任务，不配置无头定时执行，继续使用对应的手动 Skill 和可追溯回执。

## 已配置的定时任务

| 自动化 ID | 时间（Asia/Hong_Kong） | 入口 | Spark 适配结论 |
|---|---:|---|---|
| `robin` | 工作日 10:15 | `scripts/run_lark_meeting_minutes_pipeline.py` | 适合：固定只读查询、权限预检、结构化本地入库 |
| `robin-google-play-spark` | 每日 20:20 | `scripts/run_play_reviews_pipeline.py --period daily` | 适合：公开页面抓取、去重、分析、日报和回执 |
| `robin-google-play-spark-2` | 周一 08:00 | `scripts/run_play_reviews_pipeline.py --period weekly --skip-collect` | 适合：固定上周窗口汇总和报告生成 |
| `robin-waje-html-spark` | 周一 10:00 | `scripts/build_weekly_intelligence_html.py` | 适合：本地工件生成、portable validation/package/verification |
| `robin-waje` | 周五 15:00 | `scripts/run_weekly_intelligence_pipeline.py --mode collect` | 适合：公开来源周批次和支持源采集 |
| `robin-waje-2` | 周五 15:00 | `scripts/run_waje_config_weekly.py` | 适合：Lark 只读 revision 差异和本地知识库刷新 |
| `robin-waje-3` | 周五 17:00 | `scripts/run_weekly_intelligence_pipeline.py --mode report` | 适合：固定报告、质量回执和图谱刷新 |

## 任务分类与模型边界

### Spark 自动执行

- Google Play 评价：公开网页、固定 `Newest`、稳定 ID 去重、短缺/阻断状态和 HTML 报告。
- 公开情报：RSS/公开页面采集、原始快照、标准化、质量回执和周报。
- Lark 只读任务：身份/权限预检、revision 比对、结构化索引和本地报告。
- HTML/JSON/Markdown 工件：固定模板、交付回执、图谱刷新和结构化验收。

### 手动执行

- GM `Lifecycle Pool v2 (Joint)`：查询耗时长且必须在已登录浏览器中设置日期、点击“查询历史记录”，还涉及多页面并行和 Excel/飞书外部写入确认。
- 起源 `BQ-新增付费用户分析`：每个 Sheet 必须先验证筛选条件和成熟日期样本，再写入新 Excel 副本；筛选不唯一、字段不一致或登录失效时必须 fail-closed。
- 飞书在线表格的清空、条件格式、行高和批量写入：需要明确外部写入授权，不能由本地定时任务默默执行。

## 通用运行协议

1. 先确认工作目录、任务日期、窗口和输入文件；禁止把缺失日期当作零值。
2. 先运行脚本自身的锁、revision、登录/权限或来源可达性预检。
3. 原始快照永不覆盖；同批次重复运行必须幂等，成功的同日 Play 批次可由后续日报复用。
4. 读取 `run-log.json`、`quality.json`、`manifest.json` 或 `report-receipt.json`，不能只看进程退出码。
5. 状态只允许 `ok`、`skipped_existing_batch`、`partial`、`degraded`、`shortfall`、`blocked`、`error` 等明确语义；不得用空结果掩盖失败。
6. 任何报告中必须保留统计窗口、来源、抓取时间、缺失项、证据边界和下一步人工核查项。
7. 失败重试最多 2 次；验证码、登录要求、权限失败和页面结构异常不绕过，停止受限阶段并告警。

## 效率优化

- 周五 15:00 周情报采集已经包含 Play 评价采集；若当日产生成功原始批次，20:20 Play 日报复用该批次，避免再次打开浏览器抓取。
- Play 每日任务只把“未入库用户评价”计入 200 条目标；评价编辑、开发者回复变化单独作为版本更新。
- 本地脚本集中完成批处理，Spark 只负责调度、异常分流和回执审阅，减少逐步浏览器操作。
- 任何无法通过稳定接口/脚本完成的交互式页面任务，保留浏览器手动流程，不把不稳定页面硬塞进定时任务。

## 失败处理

| 失败节点 | 标记 | 处理 |
|---|---|---|
| 页面 CAPTCHA、登录页或结构异常 | `blocked` | 停止抓取，保留快照/截图/回执，等待人工恢复 |
| 数据量不足目标 | `shortfall` | 保留实际数据，报告短缺数量，不补造 |
| Lark token/权限失效 | `auth_required` / `degraded` | 不切换身份、不保存 token，记录精确失败原因 |
| 报告或图谱失败 | `degraded` | 保留已生成原始和分析产物，单独重跑报告阶段 |
| 本地锁被占用 | `already_running` | 不并发重入，等待下一次调度或人工确认 |

## 验收清单

- [ ] 调度时间按 Asia/Hong_Kong 生效，且没有重复旧任务。
- [ ] 每个任务使用 `gpt-5.3-codex-spark`，reasoning effort 与任务风险匹配。
- [ ] 每个任务入口、输出目录、状态字段和失败策略在 `jobs/manifest.json` 中可追溯。
- [ ] Play 日报、Play 周报和总周报 HTML 的窗口互不混淆。
- [ ] 旧的每日总情报调度描述不再作为当前配置；`run_daily_pipeline.py` 保持历史手动兼容。
- [ ] 浏览器手动任务没有被错误配置为无头定时任务。
