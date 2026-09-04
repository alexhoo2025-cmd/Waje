# H5 GA4 Dn Day 重算状态

状态：`blocked_authentication`  
更新时间：2026-09-01

## 需要重算的原因

当前 GA4 游戏页回访旧查询使用：

```text
旧 D1 = cohort_date + 1 天 = Waje D2 Day
旧 D3 = cohort_date + 3 天 = Waje D4 Day
```

Waje 的统一业务显示为：

```text
D1 Day = cohort 当天
D2 Day = cohort + 1 天
D3 Day = cohort + 2 天
```

因此旧 GA4 D3 数值不能改名为 D3 Day，必须重新查询。

## 已准备的聚合 SQL

`sql/13_ga4_top_games_d2_d3_day.sql`

- 范围：2026-08-21—2026-08-27；
- 粒度：game_id 聚合；
- 不输出用户、设备、订单或支付明细；
- D2 Day 使用 `entry_date + 1 day`；
- D3 Day 使用 `entry_date + 2 day`；
- D2 分母截至 8/26，D3 分母截至 8/25。

## 阻断与后续

本机 `waje-h5-readonly` Google Cloud 登录令牌在 2026-09-01 非交互查询时已过期。完成只读账号重新认证后，执行该 SQL、更新图表、替换飞书表格与图注，并将旧 GA4 D1/D3图表归档为废弃版本。
