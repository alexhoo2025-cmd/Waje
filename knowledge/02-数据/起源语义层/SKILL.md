---
name: waje-origin-semantic-layer
description: Use when answering data questions for Waje Game in the Origin Analytics platform, including metric definitions, report selection, filters, freshness, and known data-quality caveats.
---

# Waje Game 起源数据语义层

用于回答 Waje Game 在起源分析平台中的指标、报表、埋点和数据质量问题。

## Start Here

1. 阅读 `references/semantic-layer.md`。
2. 按来源优先级选择报表：数据质量/元事件定义 → 数据统计明细 → 报表集市 → 页面快照推断。
3. 回答时间敏感问题前先检查数据更新时间、是否完整日和 cohort 是否成熟。
4. 如果口径冲突或报表显示 `No Data`，保留冲突并要求核对筛选、数据源和计算逻辑。

## References

- `references/semantic-layer.md`：核心指标、实体、筛选、报表选择和已知问题。
- `references/source-inventory.md`：已检查来源、权限边界和更新边界。
- `references/evidence.md`：本轮页面快照和关键证据登记。
- `../起源分析平台盘点-2026-08-03.md`：完整平台盘点和当前快照。

## Answering Rules

- 将“平台定义”“当前页面值”“推断/待确认项”分开表达。
- 保留时间粒度、时区、cohort、用户去重键、筛选条件、币种和数据更新时间。
- 不把报表显示值自动视为稳定 KPI；先核对完整日、数据质量和计算公式。
- 不把 `NaN`、负利润、异常高 TC 比或默认 `No Data` 直接解释为业务结论。
- 本语义层不包含账号、密码、Cookie、令牌或任何原始用户明细。
