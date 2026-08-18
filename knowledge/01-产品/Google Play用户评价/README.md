---
type: moc
status: active
tags: [google-play, user-feedback]
---

# Google Play 用户评价知识库

按日记录公开评价、开发者回复、主题分布和运营线索。公开评论属于 D 级证据，不能替代内部订单、客服或资金流水核验。

## 自动产物

- 日报：`日报/YYYY-MM-DD-Google Play用户评价日报.html`
- 周报：`周报/YYYY-MM-DD-Google Play用户评价周报.html`
- 结构化分析：`data/outputs/play_reviews/`
- 持久化去重与版本索引：`data/processed/play_reviews/review_index.sqlite3`

每日 20:20 采集至少 200 条未入库评价；每周一 08:00 汇总上周一至周日。历史回填不足时报告标记 `shortfall`，不将重复评价计入新增。
