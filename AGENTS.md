# Waje 项目 Agent 协作入口

项目是 Waje 产品、数据和市场分析工作区。先读 CLAUDE.md 的项目地图，再按主题读取知识索引、输入窗口和质量回执。已有修改属于用户，禁止重置、清理或覆盖无关文件。

## 自动分派（2026-09-04）

协作仅用于用户在本项目各聊天框交付的复杂分析、数据处理、方案设计及复杂开发任务；主Agent先识别可独立验收的子任务，明确分派能带来的收益再调用Claude。简单任务、常规日报周报、晨会、配置资料更新用原默认轻量模型和既有脚本直接完成，不调用多Agent，不因题目带“分析/数据”就分派。规则在共享项目目录内适用，不修改其他项目或聊天的全局模型。

先读 tools/claude_collaboration.md。入口：python3 tools/claude_bridge.py；配置：config/agent_dispatch.json。

- 在符合条件的复杂任务内：organizer/Haiku处理必要的独立整理子任务；analyst/developer/reviewer/Sonnet处理分析、数据处理、设计、开发或审查；确需深度推理时用specialist/Opus。主任务复杂不等于每个子任务都要Opus。
- 任务包明确origin=interactive、parent_complexity=complex和delegation_reason，说明具体分派收益；缺少复杂度或收益说明默认直接执行。简单任务不能用force_delegate绕过此规则。
- 提供目标、精选脱敏证据、窗口/时区、口径、预期产物和验收标准。Claude不自行读取仓库或用户记忆。
- dispatch后台返回，主Agent继续其他工作；status/collect逐项验收。依赖accepted结果，同一文件一个开发任务负责。
- 模型输出是候选结果，引用、计算、成熟窗口、币种、补丁与测试必须核验；多模型一致不证明事实。
- revise集中反馈并返工；无实质进展时升级或接管。禁止递归Agent和传递整个历史会话。
- collect --decision accepted --note记录验收，再publish生成新的Markdown交付版本。主Agent用apply_patch应用候选补丁并实际运行验证。

## 简单日常任务排除

Play报告、竞品周报、晨会纪要和配置差异流程已移除协作钩子；不生成Claude分派、附加分析或待审任务。保持原任务时间和默认模型/脚本。不因旧测试报告曾展示日常集成就重新启用。
用户另行交付这些主题的复杂专项分析时，可作为独立交互任务按复杂度分派；自动日常流程本身仍不接入。

## Gemini 专项调整

用户已确认Gemini网页Agent执行效果较好，偶有账户/凭证验证需求，保留为复杂任务的可用专项通道（企业资料、授权查询、多源研究等）。遇登录失效恢复同一授权账号后继续，不因此整条停用。该确认是用户反馈，不虚构网页调用次数或本地成功回执。
本地Gemini CLI权限未开通（用户确认），完全排除出调配与协作，不自动调用、重试或做恢复探测；CLI问题不得推及网页Agent。详细评估见analysis/gemini_usage_review_2026_09_04/reviewed-report.md。现有企业身份、查询和数据边界继续生效。
不将企业查询凭据或权限交给第三方代理，Claude只分析精选脱敏材料。外部消息、发布和生产写入依照用户已有授权范围执行。
