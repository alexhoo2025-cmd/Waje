# Claude CLI 协作操作说明

## 执行与调用

适用范围已收窄：仅用户在本项目聊天中交付的复杂分析、数据处理、方案设计和复杂开发任务。简单任务及四类日常流程使用原默认轻量模型/脚本，不分派。先说明可独立验收的子任务及分派收益；复杂主任务中的普通子任务仍可用Sonnet/Haiku，不自动全部升级Opus。

主Agent管理证据、正式文件和最终验收。Claude worker无工具，通过精选任务包返回JSON。默认并发2；最近2个模型调用健康且任务独立时最多4。普通调用10分钟，Opus20分钟，任务可指定timeout_seconds（上限2小时）；队列等待最多30分钟。费用仅观察。

```bash
python3 tools/claude_bridge.py preflight
python3 tools/claude_bridge.py dispatch --task tools/examples/complex-analysis-task.json
python3 tools/claude_bridge.py status TASK_ID
python3 tools/claude_bridge.py collect TASK_ID
python3 tools/claude_bridge.py revise TASK_ID --feedback feedback.json
python3 tools/claude_bridge.py collect TASK_ID --decision accepted --note '已核对引用、复算指标和验证候选补丁'
python3 tools/claude_bridge.py publish TASK_ID --output analysis/MY_TASK/reviewed.md --original analysis/MY_TASK/draft.md
python3 tools/claude_bridge.py cancel TASK_ID
```

从项目根运行。preflight仅检查配置和参数，不证明真实可用。dispatch默认后台返回，--wait支持同步流程。publish写新Markdown，已有输出拒绝覆盖。

最小任务包：

```json
{"parent_task_id":"my-complex-analysis","origin":"interactive","parent_complexity":"complex","delegation_reason":"独立核对跨来源口径，主Agent并行分析另一维度","goal":"检查口径，解释变化","role":"analyst","complexity":"normal","window":{"from":"2026-08-22","to":"2026-09-04","timezone":"Asia/Hong_Kong"},"evidence":[{"id":"aggregate-1","text":"精选脱敏的完整证据片段。","source":"来源定位"}],"acceptance":["引用可追溯","缺失不填零"],"targets":[],"depends_on":[]}
```

role可选organizer/analyst/developer/reviewer/specialist。只有复杂交互主任务并提供delegation_reason才进入分派；未知/普通/简单主任务、scheduled来源及四类日常workflow均返回skipped_direct，不启动CLI，force_delegate不绕过门禁。通过资格检查后，子任务complexity=complex或risk=high才直接Opus，其余按角色选择。targets是项目相对文件路径；提供完整代码及换行，worker不能自行读取。

反馈：`{"message":"具体验收反馈","evidence":[{"id":"新的唯一ID","text":"补充材料"}],"upgrade":false}`。第一次返工保留模型，第二次升级Opus，之后主Agent接管或重新拆分。返工生成新ID；后继任务应依赖修正后的ID。

## 沟通与验收

消息存入SQLite事件表：assignment、running、result_ready/needs_context、revision_request、accepted/rejected/handed_back、cancel_requested/cancelled。执行失败保留blocked/failed及原因。
同一输入、策略和模型命中同一任务；失败后需要重跑时显式增加retry_nonce并注明原因，不得用于无限循环。

result.json含summary、findings（fact/inference/recommendation、evidence_ids、quote）、patches、assumptions、checks、open_questions。receipt记录实际请求/报告模型、退出码、耗时和用量。模型checks不等于测试已执行；成本是CLI估算，缺失为null。

程序发布的只有与输入全文完全相等的事实摘录，生成分析保持待验收。主Agentcollect接受后publish实际写入新交付版本；候选补丁使用apply_patch应用，先校验diff可应用性，随后运行目标测试。接受时重新检查基线，文件已变化则要求重新对齐。

模型只选择来源，程序实际渲染完整输入，避免局部引用丢失限定条件。日期覆盖完整不等于采集完整，采集目标不等于统计显著性门槛。result_ready后到达的cancel保留结果供主Agent接受或拒绝；needs_context可用revise补材料或cancel结束。实际应用补丁前还需重新检查文件，SQLite不锁住用户编辑器。

## 日常流程不接入

Play报告、竞品周报、晨会、配置差异已移除enrich调用；旧enrich接口保留为永不分派的兼容返回。pipeline_stages为空。旧日常集成样例和报告仅是历史验证记录，不代表当前启用。config/agent_dispatch.json的enabled只控制符合条件的复杂交互任务分派。

## Gemini及资料边界

用户确认Gemini网页Agent效果较好，偶尔需要账户/凭证验证，保留为复杂任务专项通道；按需恢复同一授权会话后继续。本地Gemini CLI权限未开通，完全排除，返回blocked_cli_excluded；--recovery-probe也不触发调用。不根据CLI问题停用网页Agent。用户反馈和CLI回执分别标注来源，不自动调整IAM、云端部署或授权数据范围。

任务包经过第三方代理，仅允许用户授权的精选脱敏材料；正则检查仅为辅助，不替代主Agent判断。费用、吞吐和成功率以可见回执为边界，不推测未记录的云端活动。
