# Phenix Firebase 留存与付费率计算工件

状态：`blocked_authentication`。本工件已定义可复算的线上 Firebase cohort 口径和只读聚合 SQL，但没有把不可用的数据源伪造成计算结果。

## 已验证来源事实

- Phoenix 在 Firebase 中的可见标记是首访页面 URL 内的 `p=h5phx`，不是独立 `p` 事件参数。
- `analytics_517134955` 在 `2026-08-28` 至 `2026-09-01` 的首访标记主体约为 `18,266`。
- 该数值仅说明该窗口内的 Firebase 标记首访规模，不能代替留存分母以外的留存分子，不能代替成功付费人数。

## 将要输出的指标

1. **次日活跃留存率**：首访带 `p=h5phx` 的用户，在 `cohort_date + 1` 出现 `session_start` 的主体数 ÷ cohort 主体数。
2. **Day+3 活跃留存率**：相同 cohort，在 `cohort_date + 3` 出现 `session_start` 的主体数 ÷ cohort 主体数。
3. **付费率**：仅在事件盘点确认某个事件为“成功付费”后计算；分子为 cohort 内至少一次该成功事件的主体数，分母为 cohort 主体数。付款页、表单提交、点击或支付发起不得替代成功付费。

## 运行顺序

1. 先执行 `sql/02_h5phx_cohort_event_inventory.sql`，由事件契约确认唯一的成功付费事件名。
2. 执行 `sql/01_h5phx_first_visit_cohort_retention.sql`，只展示已成熟的自然日偏移；不把未成熟 cohort 显示为 0%。
3. 在确认成功付费事件后，基于同一 cohort 新建“首次成功付费率”只读聚合，并保存包含来源、窗口、分子、分母、成熟度和查询作业信息的回执。

详细状态见 `execution_receipt.json`。所有查询都只返回日期和渠道级聚合；不会保存或输出用户、URL、支付明细、账号或凭据。
