---
type: technical-analysis-report
status: quality_warning
updated: 2026-08-27
---

# Waje Firebase 多端设备与性能汇总分析报告

## 执行摘要

**当前状态：`quality_warning`。** Gemini MCP 未满足企业安全门禁，本次使用本机 BigQuery API 完成聚合复核

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
| gemini_mcp_preflight | `blocked` | MCP 未同时满足连接、信任和安全 View 白名单 |
| api_identity_preflight | `passed` | 通过 |
| query:source_inventory | `ok` |  |
| query:android_analytics_daily | `ok` |  |
| query:ios_analytics_daily | `ok` |  |
| query:h5_analytics_daily | `ok` |  |
| query:android_sessions_daily | `ok` |  |
| query:native_performance_daily | `ok` |  |
| query:native_performance_dimensions | `ok` |  |
| query:crashlytics_stability_daily | `ok` |  |
| query:quality_freshness | `ok` |  |
| raw_row_output | `passed` | 仅保存聚合 JSON；未保存原始命令行输出 |
| h5_web_performance | `data_gap` | 当前 H5 Firebase Analytics 没有 Web Vitals、路由完成、请求耗时或前端错误字段 |
| cross_endpoint_trend_gate | `immature` | 每个端侧达到 7 个完整数据日后才允许发布趋势 |

## Firebase 数据集清单

| 数据集 | 表/视图数量 | 基础表 | 视图 | 首次创建时间 |
|---|---:|---:|---:|---|
| waje_ng_firebase_android | 1 | 1 | 0 | 2026-08-27 06:48:13 |
| waje_ng_firebase_android_crashlytics | 3 | 3 | 0 | 2026-08-27 06:48:13 |
| waje_ng_firebase_android_messaging | 1 | 1 | 0 | 2026-08-27 06:48:15 |
| waje_ng_firebase_android_performance | 3 | 3 | 0 | 2026-08-27 06:48:15 |
| waje_ng_firebase_android_sessions | 3 | 3 | 0 | 2026-08-27 06:48:16 |
| waje_ng_firebase_h5 | 8 | 8 | 0 | 2026-08-27 06:32:41 |
| waje_ng_firebase_ios | 5 | 5 | 0 | 2026-08-26 09:55:49 |
| waje_ng_firebase_ios_performance | 1 | 1 | 0 | 2026-08-26 10:47:11 |

## 表结构与质量元数据

| 数据集 | 表 | 类型 | 创建时间 | 字段路径数 |
|---|---|---|---|---:|
| waje_ng_firebase_android | events_20260824 | BASE TABLE | 2026-08-27 06:48:13 | 217 |
| waje_ng_firebase_android_crashlytics | com_hfhy_waje_special_ANDROID | BASE TABLE | 2026-08-27 06:48:14 | 202 |
| waje_ng_firebase_android_crashlytics | com_hfhy_wajecasino_game_ANDROID | BASE TABLE | 2026-08-27 06:48:13 | 202 |
| waje_ng_firebase_android_crashlytics | com_hfhy_wajecasino_palmgame_ANDROID | BASE TABLE | 2026-08-27 06:48:14 | 202 |
| waje_ng_firebase_android_messaging | data | BASE TABLE | 2026-08-27 06:48:15 | 15 |
| waje_ng_firebase_android_performance | com_hfhy_waje_special_ANDROID | BASE TABLE | 2026-08-27 06:48:15 | 30 |
| waje_ng_firebase_android_performance | com_hfhy_wajecasino_game_ANDROID | BASE TABLE | 2026-08-27 06:48:16 | 30 |
| waje_ng_firebase_android_performance | com_hfhy_wajecasino_palmgame_ANDROID | BASE TABLE | 2026-08-27 06:48:16 | 30 |
| waje_ng_firebase_android_sessions | com_hfhy_waje_special_ANDROID | BASE TABLE | 2026-08-27 06:48:16 | 20 |
| waje_ng_firebase_android_sessions | com_hfhy_wajecasino_game_ANDROID | BASE TABLE | 2026-08-27 06:48:16 | 20 |
| waje_ng_firebase_android_sessions | com_hfhy_wajecasino_palmgame_ANDROID | BASE TABLE | 2026-08-27 06:48:16 | 20 |
| waje_ng_firebase_h5 | events_20260814 | BASE TABLE | 2026-08-27 06:32:41 | 217 |
| waje_ng_firebase_h5 | events_20260815 | BASE TABLE | 2026-08-27 06:32:41 | 217 |
| waje_ng_firebase_h5 | events_20260816 | BASE TABLE | 2026-08-27 06:32:41 | 217 |
| waje_ng_firebase_h5 | events_20260817 | BASE TABLE | 2026-08-27 06:32:41 | 217 |
| waje_ng_firebase_h5 | events_20260818 | BASE TABLE | 2026-08-27 06:32:41 | 217 |
| waje_ng_firebase_h5 | events_20260819 | BASE TABLE | 2026-08-27 06:32:41 | 217 |
| waje_ng_firebase_h5 | events_20260820 | BASE TABLE | 2026-08-27 06:32:41 | 217 |
| waje_ng_firebase_h5 | events_20260821 | BASE TABLE | 2026-08-27 06:32:41 | 217 |
| waje_ng_firebase_ios | events_20260820 | BASE TABLE | 2026-08-26 09:55:49 | 217 |
| waje_ng_firebase_ios | events_20260821 | BASE TABLE | 2026-08-26 09:55:49 | 217 |
| waje_ng_firebase_ios | events_20260822 | BASE TABLE | 2026-08-26 09:55:49 | 217 |
| waje_ng_firebase_ios | events_20260823 | BASE TABLE | 2026-08-26 09:55:49 | 217 |
| waje_ng_firebase_ios | events_20260824 | BASE TABLE | 2026-08-26 09:55:49 | 217 |
| waje_ng_firebase_ios_performance | com_wajegame_wajegame_IOS | BASE TABLE | 2026-08-26 10:47:11 | 30 |

## Analytics 事件与会话汇总

| 日期 | 端侧 | 包体/来源 | 版本 | 事件分类 | 事件名桶 | 事件数 |
|---|---|---|---|---|---|---:|
| 2026-08-24 | android | com.hfhy.waje.special | all_versions | notification | category_total | 1.37M |
| 2026-08-24 | android | com.hfhy.waje.special | all_versions | lifecycle | category_total | 883.7k |
| 2026-08-24 | android | com.hfhy.waje.special | all_versions | other | category_total | 392.0k |
| 2026-08-24 | android | com.hfhy.waje.special | all_versions | page_or_screen | category_total | 350.8k |
| 2026-08-24 | android | com.hfhy.waje.special | all_versions | behavior_signal | category_total | 153.6k |
| 2026-08-24 | android | com.hfhy.wajecasino.game | all_versions | lifecycle | category_total | 419.3k |
| 2026-08-24 | android | com.hfhy.wajecasino.game | all_versions | notification | category_total | 235.1k |
| 2026-08-24 | android | com.hfhy.wajecasino.game | all_versions | page_or_screen | category_total | 154.8k |
| 2026-08-24 | android | com.hfhy.wajecasino.game | all_versions | other | category_total | 41.0k |
| 2026-08-24 | android | com.hfhy.wajecasino.palmgame | all_versions | lifecycle | category_total | 682.3k |
| 2026-08-24 | android | com.hfhy.wajecasino.palmgame | all_versions | notification | category_total | 499.7k |
| 2026-08-24 | android | com.hfhy.wajecasino.palmgame | all_versions | page_or_screen | category_total | 306.0k |
| 2026-08-24 | android | com.hfhy.wajecasino.palmgame | all_versions | other | category_total | 91.2k |
| 2026-08-24 | android | com.hfhy.wajecasino.palmgame | all_versions | behavior_signal | category_total | 22.5k |
| 2026-08-20 | ios | com.wajegame.wajegame | all_versions | lifecycle | category_total | 107 |
| 2026-08-20 | ios | com.wajegame.wajegame | all_versions | page_or_screen | category_total | 22 |
| 2026-08-20 | ios | com.wajegame.wajegame | all_versions | notification | category_total | 4 |
| 2026-08-21 | ios | com.wajegame.wajegame | all_versions | lifecycle | category_total | 107 |
| 2026-08-21 | ios | com.wajegame.wajegame | all_versions | page_or_screen | category_total | 35 |
| 2026-08-21 | ios | com.wajegame.wajegame | all_versions | notification | category_total | 4 |
| 2026-08-21 | ios | com.wajegame.wajegame | all_versions | other | category_total | 1 |
| 2026-08-22 | ios | com.wajegame.wajegame | all_versions | lifecycle | category_total | 357 |
| 2026-08-22 | ios | com.wajegame.wajegame | all_versions | page_or_screen | category_total | 109 |
| 2026-08-22 | ios | com.wajegame.wajegame | all_versions | notification | category_total | 10 |
| 2026-08-22 | ios | com.wajegame.wajegame | all_versions | other | category_total | 1 |
| 2026-08-23 | ios | com.wajegame.wajegame | all_versions | lifecycle | category_total | 1.5k |
| 2026-08-23 | ios | com.wajegame.wajegame | all_versions | page_or_screen | category_total | 466 |
| 2026-08-23 | ios | com.wajegame.wajegame | all_versions | notification | category_total | 39 |
| 2026-08-23 | ios | com.wajegame.wajegame | all_versions | other | category_total | 4 |
| 2026-08-24 | ios | com.wajegame.wajegame | all_versions | lifecycle | category_total | 124.8k |
| 2026-08-24 | ios | com.wajegame.wajegame | all_versions | other | category_total | 59.7k |
| 2026-08-24 | ios | com.wajegame.wajegame | all_versions | page_or_screen | category_total | 24.8k |
| 2026-08-24 | ios | com.wajegame.wajegame | all_versions | behavior_signal | category_total | 24.2k |
| 2026-08-24 | ios | com.wajegame.wajegame | all_versions | notification | category_total | 1.2k |
| 2026-08-14 | h5 | waje_ng_firebase_h5 | unknown | page_or_screen | page_view | 161.1k |
| 2026-08-14 | h5 | waje_ng_firebase_h5 | unknown | lifecycle | session_start | 80.5k |
| 2026-08-14 | h5 | waje_ng_firebase_h5 | unknown | lifecycle | user_engagement | 66.7k |
| 2026-08-14 | h5 | waje_ng_firebase_h5 | unknown | lifecycle | first_visit | 47.8k |
| 2026-08-15 | h5 | waje_ng_firebase_h5 | unknown | page_or_screen | page_view | 165.5k |
| 2026-08-15 | h5 | waje_ng_firebase_h5 | unknown | lifecycle | session_start | 84.9k |
| 2026-08-15 | h5 | waje_ng_firebase_h5 | unknown | lifecycle | user_engagement | 63.9k |
| 2026-08-15 | h5 | waje_ng_firebase_h5 | unknown | lifecycle | first_visit | 49.4k |
| 2026-08-16 | h5 | waje_ng_firebase_h5 | unknown | page_or_screen | page_view | 141.0k |
| 2026-08-16 | h5 | waje_ng_firebase_h5 | unknown | lifecycle | session_start | 69.3k |
| 2026-08-16 | h5 | waje_ng_firebase_h5 | unknown | lifecycle | user_engagement | 54.7k |
| 2026-08-16 | h5 | waje_ng_firebase_h5 | unknown | lifecycle | first_visit | 36.1k |
| 2026-08-17 | h5 | waje_ng_firebase_h5 | unknown | page_or_screen | page_view | 140.1k |
| 2026-08-17 | h5 | waje_ng_firebase_h5 | unknown | lifecycle | session_start | 70.4k |
| 2026-08-17 | h5 | waje_ng_firebase_h5 | unknown | lifecycle | user_engagement | 54.0k |
| 2026-08-17 | h5 | waje_ng_firebase_h5 | unknown | lifecycle | first_visit | 37.6k |
| 2026-08-18 | h5 | waje_ng_firebase_h5 | unknown | page_or_screen | page_view | 150.1k |
| 2026-08-18 | h5 | waje_ng_firebase_h5 | unknown | lifecycle | session_start | 73.7k |
| 2026-08-18 | h5 | waje_ng_firebase_h5 | unknown | lifecycle | user_engagement | 59.9k |
| 2026-08-18 | h5 | waje_ng_firebase_h5 | unknown | lifecycle | first_visit | 39.5k |
| 2026-08-19 | h5 | waje_ng_firebase_h5 | unknown | page_or_screen | page_view | 664.0k |
| 2026-08-19 | h5 | waje_ng_firebase_h5 | unknown | lifecycle | session_start | 526.2k |
| 2026-08-19 | h5 | waje_ng_firebase_h5 | unknown | lifecycle | first_visit | 397.8k |
| 2026-08-19 | h5 | waje_ng_firebase_h5 | unknown | lifecycle | user_engagement | 63.5k |
| 2026-08-20 | h5 | waje_ng_firebase_h5 | unknown | page_or_screen | page_view | 1.28M |
| 2026-08-20 | h5 | waje_ng_firebase_h5 | unknown | lifecycle | session_start | 1.07M |
| 2026-08-20 | h5 | waje_ng_firebase_h5 | unknown | lifecycle | first_visit | 556.8k |
| 2026-08-20 | h5 | waje_ng_firebase_h5 | unknown | lifecycle | user_engagement | 67.4k |
| 2026-08-21 | h5 | waje_ng_firebase_h5 | unknown | page_or_screen | page_view | 1.25M |
| 2026-08-21 | h5 | waje_ng_firebase_h5 | unknown | lifecycle | session_start | 1.05M |
| 2026-08-21 | h5 | waje_ng_firebase_h5 | unknown | lifecycle | first_visit | 396.7k |
| 2026-08-21 | h5 | waje_ng_firebase_h5 | unknown | lifecycle | user_engagement | 62.9k |

## Android Sessions 汇总

| 日期 | 端侧 | 包体 | 去标识化会话数 | Sessions 事件数 | Performance 开关覆盖 | Crashlytics 开关覆盖 |
|---|---|---|---:|---:|---:|---:|
| 2026-08-18 | android_main | com.hfhy.waje.special | 214 | 214 | 0.0 | 1.0 |
| 2026-08-18 | android_transsion_new | com.hfhy.wajecasino.game | 332 | 332 | 0.0 | 1.0 |
| 2026-08-18 | android_transsion_old | com.hfhy.wajecasino.palmgame | 532 | 532 | 0.0 | 1.0 |
| 2026-08-19 | android_main | com.hfhy.waje.special | 532 | 532 | 0.0 | 1.0 |
| 2026-08-19 | android_transsion_new | com.hfhy.wajecasino.game | 843 | 843 | 0.0 | 1.0 |
| 2026-08-19 | android_transsion_old | com.hfhy.wajecasino.palmgame | 1.6k | 1.6k | 0.0 | 1.0 |
| 2026-08-20 | android_main | com.hfhy.waje.special | 665 | 665 | 0.0 | 1.0 |
| 2026-08-20 | android_transsion_new | com.hfhy.wajecasino.game | 1.2k | 1.2k | 0.0 | 1.0 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | 2.2k | 2.2k | 0.0 | 1.0 |
| 2026-08-21 | android_main | com.hfhy.waje.special | 920 | 920 | 0.0 | 1.0 |
| 2026-08-21 | android_transsion_new | com.hfhy.wajecasino.game | 1.5k | 1.5k | 0.0 | 1.0 |
| 2026-08-21 | android_transsion_old | com.hfhy.wajecasino.palmgame | 3.0k | 3.0k | 0.0 | 1.0 |
| 2026-08-22 | android_main | com.hfhy.waje.special | 1.3k | 1.3k | 0.0 | 1.0 |
| 2026-08-22 | android_transsion_new | com.hfhy.wajecasino.game | 2.0k | 2.0k | 0.0 | 1.0 |
| 2026-08-22 | android_transsion_old | com.hfhy.wajecasino.palmgame | 4.2k | 4.2k | 0.0 | 1.0 |
| 2026-08-23 | android_main | com.hfhy.waje.special | 2.4k | 2.4k | 0.0 | 1.0 |
| 2026-08-23 | android_transsion_new | com.hfhy.wajecasino.game | 3.2k | 3.2k | 0.0 | 1.0 |
| 2026-08-23 | android_transsion_old | com.hfhy.wajecasino.palmgame | 6.5k | 6.5k | 0.0 | 1.0 |
| 2026-08-24 | android_main | com.hfhy.waje.special | 6.6k | 6.6k | 0.0 | 1.0 |
| 2026-08-24 | android_transsion_new | com.hfhy.wajecasino.game | 8.1k | 8.1k | 0.0 | 1.0 |
| 2026-08-24 | android_transsion_old | com.hfhy.wajecasino.palmgame | 14.7k | 14.7k | 0.0 | 1.0 |
| 2026-08-25 | android_main | com.hfhy.waje.special | 236.0k | 236.0k | 0.0 | 1.0 |
| 2026-08-25 | android_transsion_new | com.hfhy.wajecasino.game | 81.6k | 81.6k | 0.0 | 1.0 |
| 2026-08-25 | android_transsion_old | com.hfhy.wajecasino.palmgame | 83.9k | 83.9k | 0.0 | 1.0 |
| 2026-08-26 | android_main | com.hfhy.waje.special | 52.9k | 52.9k | 0.0 | 1.0 |
| 2026-08-26 | android_transsion_new | com.hfhy.wajecasino.game | 9.3k | 9.3k | 0.0 | 1.0 |
| 2026-08-26 | android_transsion_old | com.hfhy.wajecasino.palmgame | 8.8k | 8.8k | 0.0 | 1.0 |

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
| 2026-08-22 | Android | com.hfhy.wajecasino.game | 2.14.0 | 27.1k | 249341.056 | 4230.914 | 0.9969965870307167 | eligible |
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
| 2026-08-23 | Android | com.hfhy.waje.special | 2.15.0 | 111.9k | 710235.405 | 2418.582 | 0.9990951396070321 | eligible |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.16.0 | 176.0k | 725723.239 | 2599.511 | 0.9992286975103367 | eligible |
| 2026-08-23 | Android | com.hfhy.waje.special | 2.17.0 | 1.19M | 711771.39 | 2219.407 | 0.9988240951735224 | eligible |
| 2026-08-23 | Android | com.hfhy.wajecasino.game | 2.14.0 | 976.8k | 390894.694 | 2760.525 | 0.9978494258670184 | eligible |
| 2026-08-23 | Android | com.hfhy.wajecasino.palmgame | 2.10.41 | 375 | N/A | N/A | 1.0 | sample_too_small |

## 设备、系统与网络维度排行

| 日期 | 端侧 | 维度 | 维度值 | 性能记录 | 轨迹 P95(ms) | 网络 P95(ms) | 网络成功率 | 样本状态 |
|---|---|---|---|---:|---:|---:|---:|---|
|  | android_main | carrier_bucket | MTN | 4.45M | 734017.754 | 1875.839 | 0.9994923006590902 | eligible |
|  | android_main | carrier_bucket | Airtel/ZAIN/Econet | 1.46M | 670138.101 | 2489.765 | 0.9993319017519694 | eligible |
|  | android_main | carrier_bucket | Glo Mobile | 1.12M | 691190.412 | 2349.77 | 0.999572093790928 | eligible |
|  | android_main | carrier_bucket | [MISSING] | 55.8k | 907659.421 | 2138.149 | 0.9993118476889552 | eligible |
|  | android_main | carrier_bucket | ETISALAT | 12.0k | 840644.339 | 2665.467 | 0.9997044917257684 | eligible |
|  | android_main | carrier_bucket | MTN/Spacetel | 1.4k | N/A | 1034.151 | 1.0 | eligible |
|  | android_main | carrier_bucket | T-Mobile | 678 | N/A | N/A | 0.9805352798053528 | eligible |
|  | android_main | carrier_bucket | UNKNOWN [62174] | 447 | N/A | N/A | 1.0 | sample_too_small |
|  | android_main | carrier_bucket | Vodafone | 362 | N/A | N/A | 1.0 | sample_too_small |
|  | android_main | carrier_bucket | UNKNOWN [40496] | 335 | N/A | N/A | 1.0 | sample_too_small |
|  | android_main | country | NG | 7.10M | 714776.27 | 2105.747 | 0.9994715014923308 | eligible |
|  | android_main | country | US | 2.4k | 517081.053 | 2315.782 | 1.0 | eligible |
|  | android_main | country | CA | 1.0k | N/A | N/A | 1.0 | eligible |
|  | android_main | country | BJ | 598 | N/A | N/A | 1.0 | eligible |
|  | android_main | country | GB | 594 | N/A | N/A | 1.0 | eligible |
|  | android_main | country | FR | 451 | N/A | N/A | 1.0 | sample_too_small |
|  | android_main | country | NL | 409 | N/A | N/A | 1.0 | sample_too_small |
|  | android_main | country | DE | 362 | N/A | N/A | 1.0 | sample_too_small |
|  | android_main | country | JP | 324 | N/A | N/A | 1.0 | sample_too_small |
|  | android_main | country | CN | 235 | N/A | N/A | 1.0 | sample_too_small |
|  | android_main | device_name | Samsung Galaxy A06 | 445.7k | 713745.823 | 1829.045 | 0.9995743065223144 | eligible |
|  | android_main | device_name | Samsung Galaxy A07 | 306.9k | 727023.705 | 1890.02 | 0.999685969767937 | eligible |
|  | android_main | device_name | Samsung Galaxy A05 | 247.6k | 766509.362 | 1979.12 | 0.9993946057282823 | eligible |
|  | android_main | device_name | Transsion TECNO SPARK Go 2 | 224.0k | 626251.923 | 2067.788 | 0.9998458407843621 | eligible |
|  | android_main | device_name | Transsion TECNO | 198.8k | 615305.381 | 2291.084 | 0.9994551351351352 | eligible |
|  | android_main | device_name | Xiaomi 2409BRN2CA | 170.1k | 859608.319 | 1832.364 | 0.9994808529114713 | eligible |
|  | android_main | device_name | Transsion TECNO SPARK Go 1 | 133.6k | 542855.238 | 2506.688 | 0.9997200839748076 | eligible |
|  | android_main | device_name | Xiaomi 25028RN03A | 131.7k | 799430.013 | 2428.184 | 0.999523029131913 | eligible |
|  | android_main | device_name | Transsion - Mediatek TECNO SPARK 40 | 131.0k | 724656.407 | 2120.902 | 0.9996298303829934 | eligible |
|  | android_main | device_name | INFINIX Infinix X6525 | 122.0k | 623441.512 | 1863.496 | 0.999662276258021 | eligible |
|  | android_main | network_type | LTE | 5.29M | 724123.369 | 1824.076 | 0.999500855675984 | eligible |
|  | android_main | network_type | WIFI | 632.6k | 668673.946 | 2393.55 | 0.9992568167610626 | eligible |
|  | android_main | network_type | HSPAP | 567.0k | 656432.606 | 4068.486 | 0.9995778232328038 | eligible |
|  | android_main | network_type | HSPA | 297.8k | 777626.37 | 2676.943 | 0.9990019420044131 | eligible |
|  | android_main | network_type | [MISSING] | 139.3k | 740903.389 | 3211.15 | 0.9995400977292326 | eligible |
|  | android_main | network_type | HSUPA | 89.2k | 809993.164 | 2383.825 | 0.9997544621777316 | eligible |
|  | android_main | network_type | UMTS | 62.6k | 704945.905 | 1820.17 | 0.9996674242004323 | eligible |
|  | android_main | network_type | EDGE | 18.4k | 700165.612 | 6523.629 | 0.9987153134635149 | eligible |
|  | android_main | network_type | GPRS | 5.3k | 687854.445 | 3996.894 | 1.0 | eligible |
|  | android_main | network_type | HSDPA | 1.8k | N/A | 6971.052 | 1.0 | eligible |
|  | android_main | os_version | 35 | 1.60M | 784537.062 | 1985.652 | 0.9995466281675739 | eligible |
|  | android_main | os_version | 34 | 1.36M | 645285.793 | 2194.466 | 0.9993586866735611 | eligible |
|  | android_main | os_version | 36 | 1.10M | 799471.196 | 1827.825 | 0.9995157185239956 | eligible |
|  | android_main | os_version | 33 | 783.7k | 695340.461 | 2025.514 | 0.9995070530214683 | eligible |
|  | android_main | os_version | 31 | 660.5k | 726431.597 | 2037.877 | 0.999303924813373 | eligible |
|  | android_main | os_version | 29 | 503.5k | 713333.961 | 2205.839 | 0.9995351214124396 | eligible |
|  | android_main | os_version | 30 | 471.9k | 676634.415 | 2220.404 | 0.9994534130352287 | eligible |
|  | android_main | os_version | 28 | 235.3k | 622300.449 | 2422.32 | 0.9993492031353947 | eligible |
|  | android_main | os_version | 27 | 189.3k | 602071.689 | 3383.217 | 0.9995913177731359 | eligible |
|  | android_main | os_version | 26 | 101.1k | 663985.609 | 2410.383 | 0.9995995528339979 | eligible |
|  | android_transsion_new | carrier_bucket | MTN | 2.43M | 421584.159 | 2332.471 | 0.998420400917291 | eligible |
|  | android_transsion_new | carrier_bucket | Airtel/ZAIN/Econet | 821.1k | 375440.288 | 2842.328 | 0.9985410587744894 | eligible |
|  | android_transsion_new | carrier_bucket | Glo Mobile | 614.1k | 429595.218 | 3089.42 | 0.9988472804944589 | eligible |
|  | android_transsion_new | carrier_bucket | [MISSING] | 11.6k | 401808.182 | 3121.947 | 0.9985577418357886 | eligible |
|  | android_transsion_new | carrier_bucket | ETISALAT | 5.7k | 440547.136 | 1757.868 | 1.0 | eligible |
|  | android_transsion_new | carrier_bucket | T-Mobile | 354 | N/A | N/A | 1.0 | sample_too_small |
|  | android_transsion_new | carrier_bucket | UNKNOWN [62174] | 310 | N/A | N/A | 1.0 | sample_too_small |
|  | android_transsion_new | carrier_bucket | Airtel/Zain/CelTel | 234 | N/A | N/A | 0.96875 | sample_too_small |
|  | android_transsion_new | carrier_bucket | O2 Ltd. | 120 | N/A | N/A | 1.0 | sample_too_small |
|  | android_transsion_new | carrier_bucket | UNKNOWN [62127] | 84 | N/A | N/A | 1.0 | sample_too_small |
|  | android_transsion_new | country | NG | 3.88M | 411392.068 | 2584.442 | 0.9985235503569032 | eligible |
|  | android_transsion_new | country | US | 2.3k | N/A | 5436.091 | 0.9897304236200257 | eligible |
|  | android_transsion_new | country | CA | 820 | N/A | N/A | 0.9976744186046511 | eligible |
|  | android_transsion_new | country | GB | 533 | N/A | N/A | 0.9941348973607038 | eligible |
|  | android_transsion_new | country | NE | 403 | N/A | N/A | 0.9791666666666666 | sample_too_small |
|  | android_transsion_new | country | DE | 298 | N/A | N/A | 1.0 | sample_too_small |
|  | android_transsion_new | country | CM | 222 | N/A | N/A | 1.0 | sample_too_small |
|  | android_transsion_new | country | BJ | 157 | N/A | N/A | 0.9866666666666667 | sample_too_small |
|  | android_transsion_new | country | NL | 151 | N/A | N/A | 1.0 | sample_too_small |
|  | android_transsion_new | country | FR | 139 | N/A | N/A | 1.0 | sample_too_small |
|  | android_transsion_new | device_name | Transsion TECNO SPARK Go 2 | 367.9k | 379585.473 | 2541.961 | 0.9983546956666198 | eligible |
|  | android_transsion_new | device_name | Transsion - Mediatek TECNO SPARK 40 | 219.4k | 539263.679 | 2277.318 | 0.9988826758112186 | eligible |
|  | android_transsion_new | device_name | INFINIX Infinix X6725 | 195.9k | 338907.845 | 2645.287 | 0.9985090728372465 | eligible |
|  | android_transsion_new | device_name | Transsion TECNO | 184.7k | 299160.517 | 2282.626 | 0.9984614290608899 | eligible |
|  | android_transsion_new | device_name | INFINIX Infinix X6728B | 173.7k | 573783.753 | 1802.974 | 0.9972881971701235 | eligible |
|  | android_transsion_new | device_name | Transsion TECNO SPARK Go 1 | 137.3k | 305748.638 | 2934.373 | 0.9983978522559972 | eligible |
|  | android_transsion_new | device_name | INFINIX Infinix X6525D | 114.9k | 245664.946 | 2858.109 | 0.9986221983823977 | eligible |
|  | android_transsion_new | device_name | INFINIX Infinix X6525 | 109.2k | 418900.301 | 2798.989 | 0.9988643600084908 | eligible |
|  | android_transsion_new | device_name | Transsion - Mediatek TECNO SPARK 30C | 86.3k | 387589.055 | 2357.758 | 0.9982034884500396 | eligible |
|  | android_transsion_new | device_name | Transsion - Unisoc TECNO POP 20 | 85.3k | 463987.635 | 2514.893 | 0.999117387466902 | eligible |

## Crashlytics 稳定性

- 当前只展示按 `event_id` 去重的事件量、按 `issue_id` 去重的问题数和 Fatal/Non-fatal 分类。
- 在官方字段、去重键、ANR 枚举和 Sessions 分母完成认证前，不计算崩溃率、ANR 率或受影响用户数。

| 日期 | 端侧 | 包体 | 版本 | 类型 | 去重事件 | 问题数 |
|---|---|---|---|---|---:|---:|
| 2026-08-20 | android_main | com.hfhy.waje.special | all_versions | non_fatal | 64 | 1 |
| 2026-08-20 | android_transsion_new | com.hfhy.wajecasino.game | all_versions | non_fatal | 5 | 1 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | all_versions | fatal | 34 | 2 |
| 2026-08-20 | android_transsion_old | com.hfhy.wajecasino.palmgame | all_versions | non_fatal | 1 | 1 |
| 2026-08-21 | android_main | com.hfhy.waje.special | all_versions | non_fatal | 86 | 1 |
| 2026-08-21 | android_transsion_new | com.hfhy.wajecasino.game | all_versions | non_fatal | 10 | 1 |
| 2026-08-21 | android_transsion_old | com.hfhy.wajecasino.palmgame | all_versions | fatal | 57 | 2 |
| 2026-08-21 | android_transsion_old | com.hfhy.wajecasino.palmgame | all_versions | non_fatal | 2 | 1 |
| 2026-08-22 | android_main | com.hfhy.waje.special | all_versions | non_fatal | 216 | 1 |
| 2026-08-22 | android_main | com.hfhy.waje.special | all_versions | fatal | 4 | 1 |
| 2026-08-22 | android_transsion_new | com.hfhy.wajecasino.game | all_versions | non_fatal | 18 | 1 |
| 2026-08-22 | android_transsion_old | com.hfhy.wajecasino.palmgame | all_versions | fatal | 78 | 2 |
| 2026-08-22 | android_transsion_old | com.hfhy.wajecasino.palmgame | all_versions | non_fatal | 18 | 2 |
| 2026-08-23 | android_main | com.hfhy.waje.special | all_versions | non_fatal | 1.5k | 1 |
| 2026-08-23 | android_main | com.hfhy.waje.special | all_versions | fatal | 1 | 1 |
| 2026-08-23 | android_transsion_new | com.hfhy.wajecasino.game | all_versions | non_fatal | 89 | 1 |
| 2026-08-23 | android_transsion_old | com.hfhy.wajecasino.palmgame | all_versions | non_fatal | 107 | 2 |
| 2026-08-23 | android_transsion_old | com.hfhy.wajecasino.palmgame | all_versions | fatal | 105 | 3 |
| 2026-08-24 | android_main | com.hfhy.waje.special | all_versions | non_fatal | 20.2k | 354 |
| 2026-08-24 | android_main | com.hfhy.waje.special | all_versions | fatal | 107 | 14 |
| 2026-08-24 | android_transsion_new | com.hfhy.wajecasino.game | all_versions | non_fatal | 1.4k | 85 |
| 2026-08-24 | android_transsion_new | com.hfhy.wajecasino.game | all_versions | fatal | 2 | 1 |
| 2026-08-24 | android_transsion_old | com.hfhy.wajecasino.palmgame | all_versions | non_fatal | 1.6k | 86 |
| 2026-08-24 | android_transsion_old | com.hfhy.wajecasino.palmgame | all_versions | fatal | 748 | 8 |
| 2026-08-25 | android_main | com.hfhy.waje.special | all_versions | non_fatal | 24.3k | 428 |
| 2026-08-25 | android_main | com.hfhy.waje.special | all_versions | fatal | 74 | 14 |
| 2026-08-25 | android_transsion_new | com.hfhy.wajecasino.game | all_versions | non_fatal | 1.7k | 98 |
| 2026-08-25 | android_transsion_new | com.hfhy.wajecasino.game | all_versions | fatal | 5 | 4 |
| 2026-08-25 | android_transsion_old | com.hfhy.wajecasino.palmgame | all_versions | non_fatal | 1.9k | 114 |
| 2026-08-25 | android_transsion_old | com.hfhy.wajecasino.palmgame | all_versions | fatal | 707 | 7 |
| 2026-08-26 | android_main | com.hfhy.waje.special | all_versions | non_fatal | 6.5k | 85 |
| 2026-08-26 | android_main | com.hfhy.waje.special | all_versions | fatal | 3 | 3 |
| 2026-08-26 | android_transsion_new | com.hfhy.wajecasino.game | all_versions | non_fatal | 366 | 25 |
| 2026-08-26 | android_transsion_new | com.hfhy.wajecasino.game | all_versions | fatal | 2 | 1 |
| 2026-08-26 | android_transsion_old | com.hfhy.wajecasino.palmgame | all_versions | non_fatal | 394 | 23 |
| 2026-08-26 | android_transsion_old | com.hfhy.wajecasino.palmgame | all_versions | fatal | 101 | 1 |

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
