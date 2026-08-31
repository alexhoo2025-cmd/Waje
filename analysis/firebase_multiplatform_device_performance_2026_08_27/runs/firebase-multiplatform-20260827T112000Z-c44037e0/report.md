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

## 基于汇总结果的观察

以下是窗口级聚合的描述性观察，不是因果判断；性能和稳定性比率仍按质量门禁解释。

- 窗口汇总中 Android 各包 HTTP 成功率约为 99.85%～99.95%，现有 iOS 来源约为 87.97%；这只是描述性差异，尚未完成请求类别、错误码和来源映射核验。
- 原生轨迹 P95 当前按全部 DURATION_TRACE 汇总，未按 trace_category 拆分，因此不能直接解释为启动耗时或首页耗时。
- Crashlytics 窗口内去重事件量最高的是 android_main（53.1k 条）；这不是崩溃率，也不代表受影响用户数。
- 三个 Android 包的 Sessions Performance 开关覆盖均为 0%，但 Performance 表有大量记录；将其作为数据质量冲突，不据此判定性能未接入。
- H5 当前只返回 4 类标准行为事件（page_view, session_start, first_visit, user_engagement），没有 Web Vitals、白屏、核心请求或前端错误观测。

## 数据覆盖与质量

| 检查项 | 状态 | 说明 |
|---|---|---|
| gemini_mcp_preflight | `blocked` | MCP 未同时满足连接、信任和安全 View 白名单 |
| api_identity_preflight | `passed` | 通过 |
| query:source_inventory | `ok` |  |
| query:android_analytics_summary | `ok` |  |
| query:ios_analytics_summary | `ok` |  |
| query:h5_analytics_summary | `ok` |  |
| query:android_sessions_summary | `ok` |  |
| query:native_performance_summary | `ok` |  |
| query:native_performance_top3 | `ok` |  |
| query:crashlytics_stability_summary | `ok` |  |
| query:quality_freshness | `ok` |  |
| raw_row_output | `passed` | 仅保存聚合 JSON；未保存原始命令行输出 |
| h5_web_performance | `data_gap` | 当前 H5 Firebase Analytics 没有 Web Vitals、路由完成、请求耗时或前端错误字段 |
| cross_endpoint_trend_gate | `immature` | 每个端侧达到 7 个完整数据日后才允许发布趋势 |

## Firebase 数据集清单

| 数据集 | 表/视图数量 | 基础表 | 视图 |
|---|---:|---:|---:|
| waje_ng_firebase_android | 1 | 1 | 0 |
| waje_ng_firebase_android_crashlytics | 3 | 3 | 0 |
| waje_ng_firebase_android_messaging | 1 | 1 | 0 |
| waje_ng_firebase_android_performance | 3 | 3 | 0 |
| waje_ng_firebase_android_sessions | 3 | 3 | 0 |
| waje_ng_firebase_h5 | 8 | 8 | 0 |
| waje_ng_firebase_ios | 5 | 5 | 0 |
| waje_ng_firebase_ios_performance | 1 | 1 | 0 |

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

以下仅返回窗口级分类汇总；事件名只在 H5 的四类现有标准事件中保留。

| 端侧 | 包体/来源 | 事件分类 | 事件名桶 | 事件数 | 覆盖天数 |
|---|---|---|---|---:|---:|
| android | com.hfhy.waje.special | notification | 分类合计 | 1.37M | 1 |
| android | com.hfhy.waje.special | lifecycle | 分类合计 | 883.7k | 1 |
| android | com.hfhy.waje.special | other | 分类合计 | 392.0k | 1 |
| android | com.hfhy.waje.special | page_or_screen | 分类合计 | 350.8k | 1 |
| android | com.hfhy.waje.special | behavior_signal | 分类合计 | 153.6k | 1 |
| android | com.hfhy.wajecasino.game | lifecycle | 分类合计 | 419.3k | 1 |
| android | com.hfhy.wajecasino.game | notification | 分类合计 | 235.1k | 1 |
| android | com.hfhy.wajecasino.game | page_or_screen | 分类合计 | 154.8k | 1 |
| android | com.hfhy.wajecasino.game | other | 分类合计 | 41.0k | 1 |
| android | com.hfhy.wajecasino.palmgame | lifecycle | 分类合计 | 682.3k | 1 |
| android | com.hfhy.wajecasino.palmgame | notification | 分类合计 | 499.7k | 1 |
| android | com.hfhy.wajecasino.palmgame | page_or_screen | 分类合计 | 306.0k | 1 |
| android | com.hfhy.wajecasino.palmgame | other | 分类合计 | 91.2k | 1 |
| android | com.hfhy.wajecasino.palmgame | behavior_signal | 分类合计 | 22.5k | 1 |
| ios | com.wajegame.wajegame | lifecycle | 分类合计 | 126.9k | 5 |
| ios | com.wajegame.wajegame | other | 分类合计 | 59.7k | 4 |
| ios | com.wajegame.wajegame | page_or_screen | 分类合计 | 25.5k | 5 |
| ios | com.wajegame.wajegame | behavior_signal | 分类合计 | 24.2k | 1 |
| ios | com.wajegame.wajegame | notification | 分类合计 | 1.3k | 5 |
| h5 | waje_ng_firebase_h5 | page_or_screen | page_view | 3.96M | 8 |
| h5 | waje_ng_firebase_h5 | lifecycle | session_start | 3.03M | 8 |
| h5 | waje_ng_firebase_h5 | lifecycle | first_visit | 1.56M | 8 |
| h5 | waje_ng_firebase_h5 | lifecycle | user_engagement | 493.0k | 8 |

## Android Sessions 汇总

窗口级会话汇总；session_id 只在数据库内参与去重，不会返回。

| 端侧 | 包体 | 去标识化会话数 | Sessions 事件数 | Performance 开关覆盖 | Crashlytics 开关覆盖 |
|---|---|---:|---:|---:|---:|
| android_main | com.hfhy.waje.special | 301.5k | 301.5k | 0.0% | 100.0% |
| android_transsion_new | com.hfhy.wajecasino.game | 108.2k | 108.2k | 0.0% | 100.0% |
| android_transsion_old | com.hfhy.wajecasino.palmgame | 125.5k | 125.5k | 0.0% | 100.0% |

## 原生 Performance 汇总

窗口级端/包汇总；版本明细不作为默认返回。

| 端侧 | 包体 | 性能记录 | 轨迹 P50(ms) | 轨迹 P95(ms) | 轨迹 P99(ms) | 网络 P95(ms) | 网络成功率 | 样本状态 |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Android | com.hfhy.waje.special | 7.11M | 21,977 | 714,709 | 2,180,637 | 2,114 | 99.9% | eligible |
| Android | com.hfhy.wajecasino.game | 3.89M | 9,210 | 409,642 | 1,473,951 | 2,594 | 99.9% | eligible |
| Android | com.hfhy.wajecasino.palmgame | 4.47M | 7,285 | 439,041 | 1,726,069 | 2,971 | 99.9% | eligible |
| iOS | com.wajegame.wajegame | 2.45M | 8,873 | 431,742 | 1,411,844 | 1,730 | 88.0% | eligible |

## 设备、系统与网络维度 Top 3

仅返回每个端/包/维度的窗口级 Top 3 聚合值，不返回日期×版本明细。

| 端侧 | 包体 | 维度 | 维度值 | 性能记录 | 轨迹 P95(ms) | 网络 P95(ms) | 网络成功率 | 样本状态 |
|---|---|---|---|---:|---:|---:|---:|---|
| android_main | com.hfhy.waje.special | carrier_bucket | MTN | 4.45M | 733,116 | 1,876 | 99.9% | eligible |
| android_main | com.hfhy.waje.special | carrier_bucket | Airtel/ZAIN/Econet | 1.46M | 669,964 | 2,478 | 99.9% | eligible |
| android_main | com.hfhy.waje.special | carrier_bucket | Glo Mobile | 1.12M | 691,190 | 2,346 | 100.0% | eligible |
| android_main | com.hfhy.waje.special | country | NG | 7.10M | 713,872 | 2,106 | 99.9% | eligible |
| android_main | com.hfhy.waje.special | country | US | 2.4k | 517,081 | 2,316 | 100.0% | eligible |
| android_main | com.hfhy.waje.special | country | CA | 1.0k | N/A | N/A | 100.0% | eligible |
| android_main | com.hfhy.waje.special | device_name | Samsung Galaxy A06 | 445.7k | 713,402 | 1,829 | 100.0% | eligible |
| android_main | com.hfhy.waje.special | device_name | Samsung Galaxy A07 | 306.9k | 724,225 | 1,904 | 100.0% | eligible |
| android_main | com.hfhy.waje.special | device_name | Samsung Galaxy A05 | 247.6k | 763,862 | 1,984 | 99.9% | eligible |
| android_main | com.hfhy.waje.special | network_type | LTE | 5.29M | 719,026 | 1,821 | 100.0% | eligible |
| android_main | com.hfhy.waje.special | network_type | WIFI | 632.6k | 670,138 | 2,383 | 99.9% | eligible |
| android_main | com.hfhy.waje.special | network_type | HSPAP | 567.0k | 656,433 | 4,068 | 100.0% | eligible |
| android_main | com.hfhy.waje.special | os_version | 35 | 1.60M | 786,217 | 1,986 | 100.0% | eligible |
| android_main | com.hfhy.waje.special | os_version | 34 | 1.36M | 645,423 | 2,206 | 99.9% | eligible |
| android_main | com.hfhy.waje.special | os_version | 36 | 1.10M | 796,998 | 1,828 | 100.0% | eligible |
| android_transsion_new | com.hfhy.wajecasino.game | carrier_bucket | MTN | 2.43M | 421,584 | 2,332 | 99.8% | eligible |
| android_transsion_new | com.hfhy.wajecasino.game | carrier_bucket | Airtel/ZAIN/Econet | 821.1k | 375,440 | 2,842 | 99.9% | eligible |
| android_transsion_new | com.hfhy.wajecasino.game | carrier_bucket | Glo Mobile | 614.1k | 429,595 | 3,083 | 99.9% | eligible |
| android_transsion_new | com.hfhy.wajecasino.game | country | NG | 3.88M | 412,209 | 2,584 | 99.9% | eligible |
| android_transsion_new | com.hfhy.wajecasino.game | country | US | 2.3k | N/A | 5,436 | 99.0% | eligible |
| android_transsion_new | com.hfhy.wajecasino.game | country | CA | 820 | N/A | N/A | 99.8% | eligible |
| android_transsion_new | com.hfhy.wajecasino.game | device_name | Transsion TECNO SPARK Go 2 | 367.9k | 380,308 | 2,542 | 99.8% | eligible |
| android_transsion_new | com.hfhy.wajecasino.game | device_name | Transsion - Mediatek TECNO SPARK 40 | 219.4k | 539,264 | 2,277 | 99.9% | eligible |
| android_transsion_new | com.hfhy.wajecasino.game | device_name | INFINIX Infinix X6725 | 195.9k | 338,908 | 2,645 | 99.9% | eligible |
| android_transsion_new | com.hfhy.wajecasino.game | network_type | LTE | 2.86M | 459,486 | 2,224 | 99.9% | eligible |
| android_transsion_new | com.hfhy.wajecasino.game | network_type | WIFI | 357.0k | 449,486 | 3,200 | 99.8% | eligible |
| android_transsion_new | com.hfhy.wajecasino.game | network_type | HSPAP | 315.2k | 408,741 | 4,072 | 99.8% | eligible |
| android_transsion_new | com.hfhy.wajecasino.game | os_version | 35 | 1.44M | 458,539 | 2,354 | 99.8% | eligible |
| android_transsion_new | com.hfhy.wajecasino.game | os_version | 34 | 840.5k | 316,429 | 2,696 | 99.9% | eligible |
| android_transsion_new | com.hfhy.wajecasino.game | os_version | 33 | 477.7k | 425,444 | 2,626 | 99.9% | eligible |
| android_transsion_old | com.hfhy.wajecasino.palmgame | carrier_bucket | MTN | 2.73M | 442,659 | 2,747 | 99.9% | eligible |
| android_transsion_old | com.hfhy.wajecasino.palmgame | carrier_bucket | Airtel/ZAIN/Econet | 972.3k | 394,507 | 3,155 | 99.9% | eligible |
| android_transsion_old | com.hfhy.wajecasino.palmgame | carrier_bucket | Glo Mobile | 742.7k | 499,953 | 3,311 | 99.8% | eligible |
| android_transsion_old | com.hfhy.wajecasino.palmgame | country | NG | 4.46M | 439,114 | 2,961 | 99.9% | eligible |
| android_transsion_old | com.hfhy.wajecasino.palmgame | country | US | 2.4k | 208,614 | 9,514 | 99.9% | eligible |
| android_transsion_old | com.hfhy.wajecasino.palmgame | country | CA | 1.3k | N/A | 5,477 | 100.0% | eligible |
| android_transsion_old | com.hfhy.wajecasino.palmgame | device_name | Transsion TECNO SPARK Go 2 | 348.1k | 437,556 | 2,774 | 99.9% | eligible |
| android_transsion_old | com.hfhy.wajecasino.palmgame | device_name | Transsion TECNO | 265.3k | 319,338 | 2,869 | 99.9% | eligible |
| android_transsion_old | com.hfhy.wajecasino.palmgame | device_name | INFINIX Infinix X6725 | 188.7k | 425,032 | 3,109 | 99.9% | eligible |
| android_transsion_old | com.hfhy.wajecasino.palmgame | network_type | LTE | 3.21M | 519,470 | 2,536 | 99.9% | eligible |
| android_transsion_old | com.hfhy.wajecasino.palmgame | network_type | WIFI | 370.7k | 472,690 | 3,895 | 99.9% | eligible |
| android_transsion_old | com.hfhy.wajecasino.palmgame | network_type | HSPAP | 365.3k | 476,316 | 4,859 | 99.9% | eligible |
| android_transsion_old | com.hfhy.wajecasino.palmgame | os_version | 35 | 1.27M | 523,222 | 2,712 | 99.9% | eligible |
| android_transsion_old | com.hfhy.wajecasino.palmgame | os_version | 34 | 979.9k | 309,138 | 2,808 | 99.9% | eligible |
| android_transsion_old | com.hfhy.wajecasino.palmgame | os_version | 31 | 666.9k | 441,830 | 3,145 | 99.9% | eligible |
| ios_existing | com.wajegame.wajegame | carrier_bucket | [MISSING] | 2.45M | 431,742 | 1,730 | 88.0% | eligible |
| ios_existing | com.wajegame.wajegame | country | NG | 2.45M | 432,480 | 1,721 | 88.0% | eligible |
| ios_existing | com.wajegame.wajegame | country | US | 3.2k | N/A | 4,350 | 84.7% | eligible |
| ios_existing | com.wajegame.wajegame | country | PH | 267 | N/A | N/A | 100.0% | sample_too_small |
| ios_existing | com.wajegame.wajegame | device_name | iPhone XR | 346.1k | 395,136 | 1,743 | 88.8% | eligible |
| ios_existing | com.wajegame.wajegame | device_name | iPhone 11 | 328.6k | 462,384 | 1,783 | 89.2% | eligible |
| ios_existing | com.wajegame.wajegame | device_name | iPhone 12 Pro Max | 151.8k | 449,890 | 1,734 | 91.9% | eligible |
| ios_existing | com.wajegame.wajegame | network_type | LTE | 1.68M | 431,019 | 1,657 | 88.1% | eligible |
| ios_existing | com.wajegame.wajegame | network_type | WIFI | 460.0k | 462,370 | 1,852 | 87.7% | eligible |
| ios_existing | com.wajegame.wajegame | network_type | [MISSING] | 199.3k | 442,057 | 1,416 | 86.8% | eligible |
| ios_existing | com.wajegame.wajegame | os_version | 26.5 | 364.6k | 490,760 | 1,711 | 88.2% | eligible |
| ios_existing | com.wajegame.wajegame | os_version | 18.7 | 360.1k | 379,881 | 1,713 | 88.6% | eligible |
| ios_existing | com.wajegame.wajegame | os_version | 26.6 | 304.2k | 490,648 | 1,683 | 87.4% | eligible |

## Crashlytics 稳定性

- 当前只展示按 `event_id` 去重的事件量、按 `issue_id` 去重的问题数和 Fatal/Non-fatal 分类。
- 在官方字段、去重键、ANR 枚举和 Sessions 分母完成认证前，不计算崩溃率、ANR 率或受影响用户数。

| 端侧 | 包体 | 类型 | 去重事件 | 问题数 | 数据截止 |
|---|---|---|---:|---:|---|
| android_main | com.hfhy.waje.special | fatal | 189 | 21 | 2026-08-26 01:58:05 |
| android_main | com.hfhy.waje.special | non_fatal | 52.9k | 687 | 2026-08-26 07:12:23 |
| android_transsion_new | com.hfhy.wajecasino.game | fatal | 9 | 5 | 2026-08-26 00:38:50 |
| android_transsion_new | com.hfhy.wajecasino.game | non_fatal | 3.6k | 165 | 2026-08-26 07:11:44 |
| android_transsion_old | com.hfhy.wajecasino.palmgame | fatal | 1.8k | 9 | 2026-08-26 07:05:32 |
| android_transsion_old | com.hfhy.wajecasino.palmgame | non_fatal | 4.0k | 171 | 2026-08-26 07:01:20 |

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
