---
type: metric-standard
domain: retention
status: active
owner: data-product
updated: 2026-09-01
tags: [retention, Dn-Day, metric-definition, GA4, Origin, Firebase]
---

# Waje 留存口径与 Dn Day 命名规范

## 结论

从 2026-09-01 起，Waje 面向业务的所有报告、看板、图表和表格统一使用 **`Dn Day`** 表示注册或首次访问后的第 n 个自然日。

```text
D1 Day = 注册/首次访问当天
D2 Day = 次日
D3 Day = 第3个自然日
Dn Day = cohort_date + (n - 1) 个自然日
```

禁止直接把不同平台的原始 `D1`、`D3` 字段名写入业务报告。

## 示例

若用户在 2026-08-21 注册或首次访问：

| 日期 | 业务显示 | 日期偏移 |
|---|---|---:|
| 8/21 | D1 Day | D0 + 0 天 |
| 8/22 | D2 Day（次日） | D0 + 1 天 |
| 8/23 | D3 Day（第3个自然日） | D0 + 2 天 |
| 8/27 | D7 Day | D0 + 6 天 |

## 来源映射

| 来源 | 原始口径/字段 | 报告显示 | 计算校验 |
|---|---|---|---|
| Waje 生命周期 / 新增用户表 | 次留 | D2 Day | 需确认其 cohort 后第1天口径 |
| Waje 生命周期 / 新增用户表 | 3日留 | D3 Day | 需确认其 cohort 后第2天口径 |
| GA4 正确重算 | `active_date = cohort_date + 1` | D2 Day | 次日应用回访 |
| GA4 正确重算 | `active_date = cohort_date + 2` | D3 Day | 第3个自然日应用回访 |
| GA4 旧查询 | `active_date = cohort_date + 3` | D4 Day | 不得再标为 D3 Day |

## 报告展示要求

- 表头使用 `D2 Day（次日）`、`D3 Day（第3个自然日）` 等完整名称；空间不足时可用 `D2 Day`、`D3 Day`，但图表下方必须给出定义。
- 明确 cohort：注册批次、首次访问批次、首次进入游戏批次或首充批次。
- 明确活跃事实：应用回访、同游戏复玩、有效开局、有效下注或结算，不得混称“留存”。
- 未到相应自然日时显示 `N/A·未达到Dn Day统计口径`。
- 跨平台对比前先验证“来源字段 → Dn Day”的日期偏移；无法验证时标记 `blocked`，不做横向结论。

## H5 当前整改

GA4 游戏页回访旧查询采用 `D0+1` 和 `D0+3`，旧展示中的 `D1/D3` 实际对应 `D2 Day/D4 Day`。在重算 `D0+2` 的真正 `D3 Day` 前，不得把旧 D3 数值写成 Waje 口径 D3 Day。
