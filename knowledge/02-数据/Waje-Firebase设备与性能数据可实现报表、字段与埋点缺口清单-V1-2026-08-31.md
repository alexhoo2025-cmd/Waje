# Waje Firebase 设备与性能数据可实现报表、字段与埋点缺口清单 V1

更新：2026-08-31（HKT）｜范围：Android 主包、传音老包、传音新包、iOS、H5｜数据原则：仅聚合数据

## 结论

- Android 三个生产包可先上线“原生性能、设备网络分层、Crashlytics 问题诊断”三类报表，但仅能作为 `provisional` 试运行：当前 P95 是全部原生 trace 的窗口汇总，不能直接命名为启动或首页耗时；Crashlytics 只能展示问题、事件和单问题影响范围，尚不能计算崩溃率或 ANR 率。
- iOS 只达到早期观察条件，数据覆盖少于 7 个完整日，不能发布跨端趋势或版本排名结论。
- H5 已有 `page_view`、`session_start`、`first_visit`、`user_engagement` 的 8 天行为基线，但没有 Web Vitals、白屏、前端错误、核心请求、游戏就绪和可下注链路；不可用行为事件代替网页性能。
- 企业 BigQuery MCP 当前为 `blocked_authentication`。本清单引用 2026-08-27 已验收的 Firebase-only 聚合快照和 2026-08-31 只读 Crashlytics 聚合复核；上线后需要重新运行认证聚合查询刷新数据。

## 端侧可用性

| 端侧/包体 | 当前实际数据 | 当前可配置 | 状态 | 不能下结论 |
|---|---|---|---|---|
| Android 主包 `com.hfhy.waje.special` | 7 日 Performance、会话聚合、Crashlytics | 原生 trace P50/P95/P99、网络 P95、HTTP 成功率、帧率、issue/版本/设备 | `provisional` | 崩溃率、业务成功率、启动/首页单点耗时 |
| 传音老包 `com.hfhy.wajecasino.palmgame` | 同上 | 同上 | `provisional` | 同上 |
| 传音新包 `com.hfhy.wajecasino.game` | 同上 | 同上 | `provisional` | 同上 |
| iOS `com.wajegame.wajegame` | 5 日 Analytics、早期 Performance | 覆盖、记录量、trace/网络/屏幕记录量 | `immature` | 趋势、版本对比、跨端对比 |
| H5 | 4 类 GA4/Firebase 行为事件，8 日 | 访问、会话、新访、互动及接入连续性 | `provisional_behavior_only` | 加载速度、白屏、JS 错误、弱网、游戏可玩率 |

## 可立即配置的报表

### 01 数据健康与覆盖（P0）

筛选：日期、端、包体、版本、数据状态。

指标：数据截止时间、完整日数、事件/Performance 记录数、版本覆盖、数据延迟、字段完整度状态。

可定位：SDK 未接入、包体或版本缺失、数据中断、刷新延迟、筛选无效。缺失、延迟和未成熟均显示状态，不显示为 0。

### 02 Android 原生性能（P0）

筛选：日期、包体、版本、国家、设备型号、OS、网络类型、运营商、trace 类别、质量状态。

| 指标 | 算法 | 展示门槛 | 边界 |
|---|---|---:|---|
| 原生 trace P50/P95/P99 | 有效 `DURATION_TRACE.duration_ms` 的分位数 | 有效样本 ≥500 | 未拆 trace 类别时，不命名为启动/首页 |
| 网络 P95 | 有效 `NETWORK_REQUEST.response_completed_ms` 的 P95 | 有效样本 ≥500 | 不等于登录、充值、下注成功耗时 |
| HTTP 成功率 | HTTP 200—399 / 有响应码网络请求 | 有效样本 ≥500 | 不等于业务接口成功率 |
| 慢帧/冻结帧 | `SCREEN_TRACE` 的 trace 加权均值 | 有效样本 ≥500 | 不是用户占比 |

可定位：特定包、版本、低端机、OS、运营商或网络类型的性能回归。

### 03 Crashlytics 稳定性（P0）

筛选：日期、包体、版本、问题类型、设备、OS。

指标：Top Issue、Fatal/ANR/Non-fatal 事件量、单 issue 影响用户数、单 issue 会话数、首次/最近版本、设备和系统分布。

2026-08-24 00:00—2026-08-31 00:00 UTC 的只读聚合显示：传音老包 `BuildConfigHelper.getBuildConfigBoolean` 为启动早期 Fatal，高频且 98% 发生于会话首秒，应由研发优先核查初始化与构建流程。该结论只说明故障范围，不能直接证明付费或留存下降。

### 04 H5 行为基线（P1）

筛选：日期、国家、来源/媒介（如当前可用）、事件分类、数据状态。

指标：`page_view`、`session_start`、`first_visit`、`user_engagement` 的事件量、覆盖天数、日趋势和事件结构。

可定位：H5 Analytics 是否持续入库、访问/会话结构是否突变。不能定位页面加载慢、白屏、JS 错误、接口超时、弱网恢复、游戏可玩率或付费链路。

### 05 iOS 早期观测（P1）

只展示 Performance 记录量、trace/网络/屏幕记录量、版本/设备覆盖和网络响应码。达到连续 7 个完整日、完成来源映射核验后才开放趋势和版本比较。

### 06 设备、版本与网络排行（P1）

每次只选择一个排行维度：设备、OS、运营商或网络类型。展示记录量、P95、网络成功率和数据状态；去标识化会话少于 10 的小分组隐藏，P95 样本少于 500 显示 `N/A`。

## 字段与普通看板边界

| 字段/指标 | 来源 | 当前端 | 普通看板 | 说明 |
|---|---|---|---|---|
| `metric_date_lagos` | 认证聚合层 | 全端 | 是 | 统一业务日；不得使用采集落库时间替代 |
| 端、包体、版本、国家 | Analytics/Performance 聚合 | 全端 | 是 | H5 未采集的维度显示“未采集” |
| 设备、OS、网络、运营商 | Performance 聚合 | 原生 | 是 | 仅聚合排行与分层 |
| trace 类别、记录量、时延、HTTP 状态 | Performance 聚合 | 原生 | 是 | 有效样本门槛后展示 |
| issue 类型、事件量、单 issue 影响范围 | Crashlytics 聚合 | 原生 | 是 | 不跨包相加用户数 |
| `page_view`、`session_start`、`first_visit`、`user_engagement` | H5 Analytics | H5 | 是 | 仅行为基线 |
| 用户/会话/设备唯一 ID、URL、堆栈、订单、支付金额 | 原始源 | 全端 | 否 | 禁止进入普通看板与导出 |

## H5 必须补齐的上报

| 优先级 | 事件/字段组 | 必要字段 | 解锁指标 |
|---|---|---|---|
| P0 | `H5_SESSION_START` | `session_id`、`surface_type`、`web_version`、`release_id`、渠道、国家 | H5 会话与版本覆盖 |
| P0 | `H5_NAVIGATION_PERF` | FCP、LCP、INP、CLS、TTFB、资源量、Long Task、页面 | Web Vitals、首屏与页面质量 |
| P0 | `H5_CLIENT_ERROR` | 错误类型、阶段、错误码、页面重载、白/黑屏标记 | 白屏/前端错误与版本回归 |
| P0 | `H5_CORE_REQUEST` | `trace_id`、业务步骤、时延、HTTP/业务状态、超时、重试 | 登录/余额/充值/下注/结算请求 SLO |
| P1 | `H5_GAME_READY`、`H5_BET_READY` | `game_id`、厂家、游戏版本、配置、ready 耗时 | 游戏可玩率、可下注耗时 |
| P1 | `H5_NETWORK_CHANGE`、`H5_RECOVERY_RESULT` | 网络类型、运营商、切换、恢复结果、重试次数 | 弱网、断网重连、恢复能力 |
| P2 | 服务端认证事实 | 业务日、渠道/包体、游戏、最终状态、关联键 | 性能—首充—留存、游戏/下注/结算真实漏斗 |

## 验收与发布门槛

1. 所有卡片可见公式、分母、时区、数据截止时间和质量状态。
2. 所有 Dashboard 筛选器逐卡绑定；H5 无字段时显示“未采集”，不应筛成 0。
3. P95/P99 需至少 500 个有效样本；小分组至少 10 个去标识化会话。
4. 跨端趋势需各端至少 7 个完整日；iOS 在此之前只做数据健康观察。
5. “崩溃率、ANR 率、白屏率、充值成功率、游戏可玩率”没有认证分母时必须显示 `blocked`。
6. H5 采用新事件后，需在弱网、网络切换、后台恢复、重复点击和低端安卓场景完成事件验收；客户端行为与服务端最终状态关联率不低于 98%。

## 更新限制

本版使用 2026-08-27 Firebase-only 聚合基线与 2026-08-31 Crashlytics 只读聚合；当前企业 BigQuery MCP 为 `blocked_authentication`，因此不把旧快照写成实时数据。权限恢复后按同一字段矩阵重跑认证聚合并更新所有状态、数据截止日和趋势。
