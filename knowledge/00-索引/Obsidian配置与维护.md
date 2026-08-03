---
type: operating-guide
status: active
updated: 2026-08-03
tags: [obsidian, workflow, maintenance]
---

# Obsidian 配置与维护

## 打开方式

在 Obsidian 中打开项目根目录：

`/Users/robin/Documents/wajetan_analyst`

这样可以同时管理 `knowledge/` 知识库和根目录的 JSON、HTML、脚本及未来源码。

## 推荐功能

先使用 Obsidian 内置能力：文件属性、反向链接、关系图谱、模板、命令面板和搜索。

当笔记数量增加后，再按需安装社区插件：

- Dataview：按 `type/status/domain/updated` 汇总笔记和指标。
- Templater：自动生成日期、标题和标准化 frontmatter。
- Tasks：统一追踪权限申请、数据核验和分析任务。
- Git：把知识和配置的变更纳入版本历史；提交前检查是否含敏感数据。

插件不是知识体系本身，插件失效时，Markdown 文件仍应可独立阅读。

## 文件夹职责

| 目录 | 职责 | 维护方式 |
|---|---|---|
| `knowledge/00-索引` | MOC、资产关系、项目入口 | 手工维护 |
| `knowledge/01-产品` | 产品、玩法、商业化、用户体验 | 手工维护 |
| `knowledge/02-数据` | 平台、指标、报表、埋点、数据质量 | 手工维护 |
| `knowledge/03-竞品` | 竞品、市场、用户反馈、来源 | 手工维护 |
| `knowledge/04-方法` | 分析方法、证据等级、模板约束 | 稳定后少改 |
| `knowledge/05-运行` | 工作日志、权限、阻塞、下一步 | 高频维护 |
| `knowledge/90-模板` | 新笔记模板 | 谨慎修改 |
| `knowledge/_generated` | 自动生成图谱和机器可读数据 | 禁止手工编辑 |

## 日常闭环

1. 工作中先记到 `05-运行/工作日志`。
2. 新事实写入对应主题笔记，并标注来源、时间和口径。
3. 形成结论后补充“事实—推断—建议—验证指标”。
4. 新增资产或跨文件关系时更新 `00-索引/资产地图`。
5. 执行 `python3 tools/build_graph.py` 更新图谱。
6. 每周清理孤立笔记、失效链接、未验证结论和过期待办。

## 命名与属性规范

- 文件名使用明确业务概念，不使用“新建笔记 1”等临时名称。
- 每个主题笔记至少包含 `type`、`status`、`owner`、`updated`、`tags`。
- 事实型笔记补 `sources`；指标型笔记补 `metric_id`、`source`、`grain`。
- 状态建议使用：`seed`（初始）、`draft`（草稿）、`active`（使用中）、`validated`（已验证）、`deprecated`（废弃）。
