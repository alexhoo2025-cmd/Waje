---
type: technical-analysis-report
status: quality_warning
updated: 2026-08-27
---

# Waje Firebase 多端设备与性能汇总分析报告

## 执行摘要

**当前状态：`quality_warning`。** At least one Firebase source/query is missing, delayed or blocked

- 数据范围：Firebase-only；Android/iOS 2026-08-20～2026-08-26，H5 2026-08-14～2026-08-21，时区 `Africa/Lagos`。
- 执行路径：`api_fallback`；Gemini 状态：`blocked_external_prerequisites`；本机 API 状态：`ok`。
- Android、iOS、H5 独立统计；事件数不解释为用户数，Sessions 不与 `session_start` 相加。
- H5 当前只形成行为基线；Web Vitals、白屏、核心请求、前端错误和游戏阶段均标记为 `data_gap` / `blocked`。

## 端侧现状

| 端侧 | 当前实际汇总 | 主要可用指标 | 状态 |
|---|---:|---|---|
| Android | 5.60M Analytics 事件；15.47M Performance 记录；535.2k 去标识化会话 | 会话开始事件、轨迹/网络 P95、HTTP 成功率、慢帧/冻结帧、Fatal/Non-fatal 事件量 | `provisional` |
| iOS | 237.5k Analytics 事件；2.45M Performance 记录 | 会话开始事件、轨迹/网络 P95、屏幕流畅度 | `immature` / `provisional` |
| H5 | 9.05M 行为事件 | page_view、session_start、first_visit、user_engagement | `provisional_behavior_only` |

## 数据覆盖与质量

| 检查项 | 状态 | 说明 |
|---|---|---|
| gemini_mcp_preflight | `blocked` | blocked_external_prerequisites |
| api_identity_preflight | `passed` | ready |
| query:source_inventory | `failed` | Error in query string: Syntax error: Expected end of input but got "-" at
[13:26]

 |
| query:android_analytics_daily | `ok` |  |
| query:ios_analytics_daily | `ok` |  |
| query:h5_analytics_daily | `ok` |  |
| query:android_sessions_daily | `ok` |  |
| query:native_performance_daily | `ok` |  |
| query:native_performance_dimensions | `ok` |  |
| query:crashlytics_stability_daily | `ok` |  |
| query:quality_freshness | `failed` | Error in query string: Syntax error: Expected end of input but got "-" at
[12:26]

 |
| raw_row_output | `passed` | all query outputs are aggregate JSON rows; raw CLI output is not persisted |
| h5_web_performance | `data_gap` | current H5 Firebase Analytics query has no Web Vitals, route-ready, request timing or frontend error contract |
| cross_endpoint_trend_gate | `immature` | publish endpoint trends only after seven complete days per endpoint |

## Analytics 事件与会话汇总

| 日期 | 端侧 | 包体/来源 | 版本 | 事件分类 | 事件名桶 | 事件数 |
|---|---|---|---|---|---|---:|
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | lifecycle | user_engagement | 539.4k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | notification | notification_receive | 518.3k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | page_or_screen | screen_view | 262.4k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | notification | notification_dismiss | 233.3k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.16.0 | notification | notification_receive | 189.7k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.15.0 | notification | notification_receive | 147.0k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | lifecycle | session_start | 115.8k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | other | rechargeAndWithdrawTotalTimes | 105.5k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.16.0 | lifecycle | user_engagement | 85.2k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.16.0 | notification | notification_dismiss | 83.8k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | other | rechargeFix | 71.1k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | other | rechargeDollar | 71.1k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | behavior_signal | recharge | 71.1k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.15.0 | notification | notification_dismiss | 64.0k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.15.0 | lifecycle | user_engagement | 52.9k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.16.0 | page_or_screen | screen_view | 44.8k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | behavior_signal | withdraw | 34.4k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.15.0 | page_or_screen | screen_view | 28.9k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.14.0 | notification | notification_receive | 28.4k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.11.2 | notification | notification_receive | 28.3k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.16.0 | lifecycle | session_start | 23.9k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.16.0 | other | rechargeAndWithdrawTotalTimes | 17.7k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.15.0 | lifecycle | session_start | 16.3k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | other | firebase_campaign | 15.7k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | lifecycle | first_open | 15.0k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.14.0 | notification | notification_dismiss | 13.0k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.11.2 | notification | notification_dismiss | 12.8k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.16.0 | behavior_signal | recharge | 11.7k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.16.0 | other | rechargeDollar | 11.7k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.16.0 | other | rechargeFix | 11.7k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.14.0 | lifecycle | user_engagement | 10.0k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.15.0 | other | rechargeAndWithdrawTotalTimes | 9.7k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | notification | notification_foreground | 9.6k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | other | app_remove | 8.7k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.11.2 | lifecycle | user_engagement | 7.1k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.15.0 | behavior_signal | recharge | 6.7k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.15.0 | other | rechargeFix | 6.7k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.15.0 | other | rechargeDollar | 6.7k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | notification | notification_open | 6.2k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.13.0 | notification | notification_receive | 6.1k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.16.0 | behavior_signal | withdraw | 6.0k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | behavior_signal | register | 5.8k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.14.0 | page_or_screen | screen_view | 5.3k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.11.2 | page_or_screen | screen_view | 4.5k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.11.1 | notification | notification_receive | 4.4k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | other | recharge24HourDollar | 3.7k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | other | recharge24Hour | 3.7k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | behavior_signal | firstCharge | 3.5k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.14.0 | lifecycle | session_start | 3.4k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.15.0 | behavior_signal | withdraw | 3.0k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.13.0 | notification | notification_dismiss | 2.7k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.12.0 | notification | notification_receive | 2.7k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.11.2 | lifecycle | session_start | 2.7k |
| 2026-08-24 | android | com.hfhy.waje.special | unknown | other | rechargeAndWithdrawTotalTimes | 2.7k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | other | register24Charge40 | 2.5k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | other | recharge1Day | 2.4k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.13.0 | lifecycle | user_engagement | 2.1k |
| 2026-08-24 | android | com.hfhy.waje.special | unknown | behavior_signal | register | 2.0k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.10.45 | notification | notification_receive | 2.0k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.10.36 | notification | notification_receive | 2.0k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.11.0 | notification | notification_receive | 1.9k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.16.0 | notification | notification_foreground | 1.9k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.11.1 | notification | notification_dismiss | 1.9k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | other | loginSecondaryRetention | 1.9k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.14.0 | other | rechargeAndWithdrawTotalTimes | 1.8k |
| 2026-08-24 | android | com.hfhy.waje.special | unknown | behavior_signal | recharge | 1.8k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | other | firstCharge300 | 1.8k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | other | firstCharge100 | 1.8k |
| 2026-08-24 | android | com.hfhy.waje.special | unknown | other | rechargeDollar | 1.8k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | other | firstCharge500 | 1.8k |
| 2026-08-24 | android | com.hfhy.waje.special | unknown | other | rechargeFix | 1.8k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.16.0 | notification | notification_open | 1.6k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | other | firstCharge1000 | 1.6k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.16.0 | other | app_remove | 1.4k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.11.4 | notification | notification_receive | 1.4k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.11.1 | lifecycle | user_engagement | 1.4k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.11.2 | other | rechargeAndWithdrawTotalTimes | 1.4k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | other | withdraw1Day | 1.3k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.17.0 | other | firstWithdraw | 1.3k |
| 2026-08-24 | android | com.hfhy.waje.special | 2.14.0 | other | rechargeFix | 1.3k |

## 原生 Performance 汇总

| 日期 | 端侧 | 包体 | 版本 | 性能记录 | 轨迹 P95(ms) | 网络 P95(ms) | 网络成功率 | 样本状态 |
|---|---|---|---|---:|---:|---:|---:|---|
| 2026-08-20 | Android | com.hfhy.waje.special | 2.10.36 | 2 | N/A | N/A | N/A | sample_too_small |
| 2026-08-20 | Android | com.hfhy.waje.special | 2.10.45 | 9 | N/A | N/A | N/A | sample_too_small |
| 2026-08-20 | Android | com.hfhy.waje.special | 2.11.2 | 9 | N/A | N/A | N/A | sample_too_small |
| 2026-08-20 | Android | com.hfhy.waje.special | 2.12.0 | 3 | N/A | N/A | N/A | sample_too_small |
| 2026-08-20 | Android | com.hfhy.waje.special | 2.13.0 | 8 | N/A | N/A | N/A | sample_too_small |
| 2026-08-20 | Android | com.hfhy.waje.special | 2.14.0 | 183 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-20 | Android | com.hfhy.waje.special | 2.15.0 | 184 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-20 | Android | com.hfhy.waje.special | 2.16.0 | 412 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-20 | Android | com.hfhy.waje.special | 2.17.0 | 901 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-20 | Android | com.hfhy.wajecasino.game | 2.14.0 | 2.1k | 216863.099 | 1388.922 | 0.9991673605328892 | eligible |
| 2026-08-20 | Android | com.hfhy.wajecasino.palmgame | 2.10.42 | 1.8k | 305439.405 | 3106.996 | 0.9987468671679198 | eligible |
| 2026-08-20 | Android | com.hfhy.wajecasino.palmgame | 2.15.0 | 424 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-20 | Android | com.hfhy.wajecasino.palmgame | 2.17.0 | 1.5k | 320797.162 | 5220.924 | 1.0 | eligible |
| 2026-08-20 | iOS | com.wajegame.wajegame | 2.17.0 | 2.0k | N/A | 1368.303 | 0.9394606494221244 | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.0.0 | 19 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.10.29 | 2 | N/A | N/A | N/A | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.10.31 | 2 | N/A | N/A | N/A | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.10.32 | 6 | N/A | N/A | N/A | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.10.36 | 17 | N/A | N/A | N/A | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.10.45 | 51 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.11.0 | 2 | N/A | N/A | N/A | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.11.1 | 18 | N/A | N/A | N/A | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.11.2 | 124 | N/A | N/A | N/A | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.12.0 | 12 | N/A | N/A | N/A | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.13.0 | 62 | N/A | N/A | N/A | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.14.0 | 165 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.15.0 | 906 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.16.0 | 1.9k | 610978.918 | 1658.557 | 1.0 | eligible |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.17.0 | 5.2k | 574128.237 | 1889.313 | 1.0 | eligible |
| 2026-08-21 | Android | com.hfhy.waje.special | 2.19.0 | 4 | N/A | N/A | N/A | sample_too_small |
| 2026-08-21 | Android | com.hfhy.wajecasino.game | 2.14.0 | 8.6k | 224542.968 | 4418.931 | 0.9981362600952578 | eligible |
| 2026-08-21 | Android | com.hfhy.wajecasino.palmgame | 2.10.41 | 13 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-21 | Android | com.hfhy.wajecasino.palmgame | 2.10.42 | 8.7k | 299945.096 | 2760.141 | 0.99977079990832 | eligible |
| 2026-08-21 | Android | com.hfhy.wajecasino.palmgame | 2.15.0 | 1.7k | 164093.371 | N/A | 1.0 | sample_too_small |
| 2026-08-21 | Android | com.hfhy.wajecasino.palmgame | 2.17.0 | 6.0k | 156069.459 | 3350.394 | 0.998587570621469 | eligible |
| 2026-08-21 | iOS | com.wajegame.wajegame | 2.17.0 | 7.1k | 429072.991 | 2701.092 | 0.8906095551894564 | eligible |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.0.0 | 8 | N/A | N/A | N/A | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.10.29 | 2 | N/A | N/A | N/A | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.10.33 | 3 | N/A | N/A | N/A | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.10.34 | 3 | N/A | N/A | N/A | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.10.35 | 11 | N/A | N/A | N/A | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.10.36 | 38 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.10.45 | 98 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.11.0 | 44 | N/A | N/A | N/A | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.11.1 | 53 | N/A | N/A | N/A | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.11.2 | 408 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.11.4 | 22 | N/A | N/A | N/A | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.12.0 | 19 | N/A | N/A | N/A | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.13.0 | 85 | N/A | N/A | N/A | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.14.0 | 682 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.15.0 | 3.8k | 687934.109 | 1566.139 | 1.0 | eligible |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.16.0 | 6.8k | 888403.512 | 1923.323 | 1.0 | eligible |
| 2026-08-22 | Android | com.hfhy.waje.special | 2.17.0 | 22.4k | 881507.049 | 1906.463 | 0.999826056705514 | eligible |
| 2026-08-22 | Android | com.hfhy.wajecasino.game | 2.14.0 | 27.1k | 250357.471 | 4231.497 | 0.9969965870307167 | eligible |
| 2026-08-22 | Android | com.hfhy.wajecasino.palmgame | 2.10.41 | 7 | N/A | N/A | N/A | sample_too_small |
| 2026-08-22 | Android | com.hfhy.wajecasino.palmgame | 2.10.42 | 20.7k | 406621.046 | 4118.62 | 0.9976019184652278 | eligible |
| 2026-08-22 | Android | com.hfhy.wajecasino.palmgame | 2.15.0 | 5.7k | 182643.287 | 5710.125 | 1.0 | eligible |
| 2026-08-22 | Android | com.hfhy.wajecasino.palmgame | 2.17.0 | 20.7k | 215659.322 | 5093.969 | 0.9981687776590874 | eligible |
| 2026-08-22 | iOS | com.wajegame.wajegame | 2.17.0 | 39.1k | 676253.666 | 1919.48 | 0.9086764705882353 | eligible |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.0.0 | 1.6k | N/A | 1303.269 | 0.9977753058954394 | sample_too_small |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.10.28 | 3 | N/A | N/A | N/A | sample_too_small |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.10.31 | 1 | N/A | N/A | N/A | sample_too_small |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.10.32 | 39 | N/A | N/A | N/A | sample_too_small |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.10.33 | 9 | N/A | N/A | N/A | sample_too_small |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.10.34 | 70 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.10.35 | 299 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.10.36 | 1.1k | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.10.45 | 1.6k | 648357.859 | 1880.575 | 1.0 | eligible |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.11.0 | 2.5k | 910525.477 | 4852.469 | 1.0 | eligible |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.11.1 | 3.2k | 949853.38 | 2791.944 | 0.9984599589322382 | eligible |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.11.2 | 13.0k | 718596.827 | 3176.953 | 0.9978134110787172 | eligible |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.11.4 | 743 | N/A | N/A | 1.0 | sample_too_small |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.12.0 | 2.2k | 902480.794 | 2697.6 | 1.0 | eligible |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.13.0 | 5.0k | 787270.318 | 4339.28 | 1.0 | eligible |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.14.0 | 20.1k | 673909.01 | 1672.722 | 0.9986852196778788 | eligible |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.15.0 | 111.9k | 708018.284 | 2413.013 | 0.9990951396070321 | eligible |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.16.0 | 176.0k | 725723.239 | 2599.511 | 0.9992286975103367 | eligible |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.17.0 | 1.19M | 711771.39 | 2219.407 | 0.9988240951735224 | eligible |
| 2026-08-23 | Android | com.hfhy.wajecasino.game | 2.14.0 | 976.8k | 388622.405 | 2760.525 | 0.9978494258670184 | eligible |
| 2026-08-23 | Android | com.hfhy.wajecasino.palmgame | 2.10.41 | 375 | N/A | N/A | 1.0 | sample_too_small |

## Crashlytics 稳定性

- 当前只展示按 `event_id` 去重的事件量、按 `issue_id` 去重的问题数和 Fatal/Non-fatal 分类。
- 在官方字段、去重键、ANR 枚举和 Sessions 分母完成认证前，不计算崩溃率、ANR 率或受影响用户数。

| 日期 | 端侧 | 包体 | 版本 | 类型 | 去重事件 | 问题数 |
|---|---|---|---|---|---:|---:|
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 5 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 4 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.15.0 | non_fatal | 3 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.15.0 | non_fatal | 3 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 2 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 2 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.13.0 | non_fatal | 2 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 2 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 2 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 2 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.14.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.15.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.15.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.15.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.14.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.15.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.14.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.15.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_transsion_new | com.hfhy.wajecasino.game | 2.14.0 | non_fatal | 2 | 1 |
| 2026-08-20 | android_transsion_new | com.hfhy.wajecasino.game | 2.14.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_transsion_new | com.hfhy.wajecasino.game | 2.14.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_transsion_new | com.hfhy.wajecasino.game | 2.14.0 | non_fatal | 1 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 5 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 4 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 2 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 2 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 2 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 2 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 2 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 2 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 2 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 1 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 1 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 1 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 1 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 1 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 1 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 1 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 1 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 1 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 1 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | fatal | 1 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.17.0 | non_fatal | 1 | 1 |
| 2026-08-21 | android_main | com.hfhy.waje.special | 2.13.0 | non_fatal | 11 | 1 |
| 2026-08-21 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 5 | 1 |
| 2026-08-21 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 4 | 1 |
| 2026-08-21 | android_main | com.hfhy.waje.special | 2.16.0 | non_fatal | 4 | 1 |
| 2026-08-21 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 3 | 1 |
| 2026-08-21 | android_main | com.hfhy.waje.special | 2.15.0 | non_fatal | 3 | 1 |
| 2026-08-21 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 2 | 1 |
| 2026-08-21 | android_main | com.hfhy.waje.special | 2.17.0 | non_fatal | 2 | 1 |

## H5 性能与核心漏斗缺口

| 指标族 | 当前状态 | 不能直接推断的结论 |
|---|---|---|
| Web Vitals（LCP/INP/CLS/FCP/TTFB） | `data_gap` | 不能从 page_view 或停留事件推断加载速度 |
| 页面白屏/黑屏与前端错误 | `data_gap` | 不能判定网页稳定性 |
| 核心请求 P95 / 超时 / 重试 | `data_gap` | 不能定位弱网接口问题 |
| 游戏就绪 / 可下注 / 首局 | `blocked` | Firebase 行为事件不等于服务端成功 |

## 建议动作

- Gemini MCP 连接、trust 和安全 View 白名单未全部通过时，继续保持 API fallback，不启用自动自然语言查询。
- Android Performance 先按包体、版本、设备、系统和网络单维度做 P95 与成功率观察；样本不足 500 不进入正式排行。
- iOS 继续独立积累至少 7 个完整日，确认现有来源映射后再开放跨端趋势。
- H5 补齐 H5_NAVIGATION_PERF、H5_CORE_REQUEST、H5_GAME_READY、H5_BET_READY、H5_CLIENT_ERROR 等事件后，才能发布网页性能和核心漏斗指标。

## 审计边界

本报告只保存聚合结果、查询回执和状态，不保存原始事件行、用户标识、设备唯一标识、Cookie、Token、URL、请求体、响应体、订单或错误堆栈。
