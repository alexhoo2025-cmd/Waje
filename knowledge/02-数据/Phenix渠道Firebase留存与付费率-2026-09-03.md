---
type: source-status
domain: acquisition-retention
status: blocked-authentication
updated: 2026-09-03
source: Firebase Analytics BigQuery export
channel_marker: p=h5phx
---

# Phenix 渠道：Firebase 留存与付费率

## 当前结论

**当前不能从线上 Firebase 源直接给出 Phenix 的留存率或付费率。** 已验证的线上快照说明 `p=h5phx` 确实进入 Firebase，且在 `analytics_517134955` 的 `2026-08-28` 至 `2026-09-01` 完整日中识别出约 `18,266` 个带标记的首访主体；但现有快照没有跨日 cohort 回访分子，也没有已确认的“成功付费”事件。

把 `session_start` 总量除以 `first_visit` 总量，或把表单/付款页事件当作成功付费，都会得到错误的留存率或付费率，因此本次不输出误导性百分比。

## 已核实的来源口径

| 项目 | 已验证事实 | 可否直接用来计算 |
|---|---|---|
| Phoenix 标记 | `p=h5phx` 位于 `page_location` URL，非独立渠道字段 | 可用于定义首访 cohort |
| Firebase 数据集 | `wajenigeria.analytics_517134955` | 可作为当前主验证源，不与其他数据集混加 |
| 首访规模 | 约 18,266 个主体，窗口为 8/28—9/1 | 仅可作为该窗口 cohort 分母候选 |
| 留存活跃事件 | `session_start` 已观察到 | 必须按同一主体跨日交集计算 |
| 成功付费事件 | 尚未在 Phoenix cohort 中完成事件契约确认 | 未确认前不可计算付费率 |

## 下一次可执行计算

- **次日活跃留存率**：首访带 `p=h5phx` 的主体，在第二天再次出现 `session_start` 的主体数 ÷ 首访主体数。
- **Day+3 活跃留存率**：同一 cohort 在首访后第 3 个自然日活跃的主体数 ÷ 首访主体数。
- **成功付费率**：同一 cohort 内出现已确认成功付费事件的主体数 ÷ 首访主体数。

所有日期以数据截止日判断成熟度：尚未达到对应观察日的 cohort 显示 `N/A`，不显示 `0%`。

## 执行阻断与修复

本次 Firebase 项目环境已验证为 `waje-special`，但当前 BigQuery 只读连接返回 `Auth required`，Firebase 控制台 Analytics 页面分别返回无权限/处理错误。它们是访问阻断，不是“没有 Phoenix 数据”的证据。

可复算的只读 SQL、运行顺序和无敏感数据执行回执已保存至 [Phenix Firebase cohort 工件](../../analysis/phenix_firebase_retention_payment_2026_09_03/README.md)。恢复 `wajenigeria` 的 BigQuery 只读认证后，可以在不导出用户或支付明细的前提下直接计算以上指标。
