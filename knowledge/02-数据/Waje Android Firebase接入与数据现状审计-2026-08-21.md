---
type: audit-report
domain: firebase
status: partial
updated: 2026-08-21
project: waje-special
scope: [android, crashlytics, analytics, performance]
time_window: 2026-08-15 00:00 - 2026-08-21 11:50 Asia/Hong_Kong
evidence_status: firebase_environment_verified_crashlytics_verified_analytics_aggregate_performance_segmented
tags: [Firebase, Android, Crashlytics, Analytics, Performance, Waje Special, 传音包, 数据质量]
---

# Waje Android Firebase 接入与数据现状审计

> 审计时间：2026-08-21 11:50（Asia/Hong_Kong）  
> 范围：`waje-special` 项目下三个 Android 生产包；iOS、H5 不纳入本轮结论。  
> 证据边界：只读核查 Firebase 环境、SDK 配置、Crashlytics、Analytics 概览和 Performance 控制台；未修改配置、权限、Issue 状态或个人视图，未保存凭据、Cookie、Token 或用户明细。

## Executive Summary

- **接入基础是成立的。**三个 Android 包的 Firebase App ID 与包名映射可读取，Crashlytics 三包均有真实事件；因此不是“Firebase 没注册”或“完全没有 SDK 数据”。
- **稳定性风险集中在启动和 Cocos 游戏链路。**主包有 147,233 次非致命异常、多个 ANR；传音老包的启动期 Fatal NPE 达 6,213 次且 98% 发生在会话首秒；传音新包仍主要显示 2.14.0 数据，版本覆盖需要优先核对。
- **Performance 接入不均衡。**主包和老包能看到启动/网络轨迹，新包在当前 7 日窗口与所选版本没有有效 Performance 数据；这应标记为“数据覆盖缺口”，不能解释为性能正常。
- **Analytics 有量但不能直接做包体结论。**Firebase 概览页可见 7 日约 250 万活跃用户、事件和注册/充值类事件，但页面按项目/多 App 汇总展示；收入卡为 `$0.00`，不能当作业务收入为零，应继续以 BQ/Ares/订单事实为准。

## 1. 审计对象与证据状态

| 对象 | 包名 | Firebase App ID | SDK 配置 | Crashlytics | Analytics | Performance |
|---|---|---|---|---|---|---|
| Android 主包 / Waje Special | `com.hfhy.waje.special` | `1:128692700786:android:e0ca00db9431011afea4eb` | 已读取且包名匹配 | 有真实数据 | 有项目级汇总数据 | **有数据** |
| 传音老包 / Waje Casino | `com.hfhy.wajecasino.palmgame` | `1:128692700786:android:cc43a6abd8fd9fc4fea4eb` | 已读取且包名匹配 | 有真实数据 | 单包口径未被当前概览可靠隔离 | **有数据** |
| 传音新包 / Waje Game | `com.hfhy.wajecasino.game` | `1:128692700786:android:63d7e4b8a16eec53fea4eb` | 已读取且包名匹配 | 有真实数据 | 单包口径未被当前概览可靠隔离 | **当前窗口无数据** |

### 读法

- “已读取 SDK 配置”只证明 Firebase 项目、App ID 和包名配置可获得；不等于每个 SDK 产品均已正确初始化。
- “有真实数据”以 Crashlytics/Performance 返回事件或样本为准；`No data` 单独标为缺口，需排除版本、时间窗、采集开关、处理延迟和筛选条件。
- Crashlytics 的 `eventsCount` 是异常事件次数，`impactedUsersCount` 是该问题影响用户数，不能跨问题相加当成全局用户数。

## 2. Crashlytics：三包均已接入，但主包和老包存在启动/游戏链路风险

### 2.1 重点问题

| 包体 | 类型 | 主要问题 | 事件数 | 影响用户 | 版本证据 | 优先级 |
|---|---|---|---:|---:|---|---|
| Waje Casino | FATAL | `BuildConfigHelper.getBuildConfigBoolean`：Context 为空导致 NPE | 6,213 | 2,075 | 首见/最近均为 2.17.0；98% 首秒发生 | **P0** |
| Waje Special | NON_FATAL | Cocos `FirebaseMgr.logException`：`on` 访问 null | 147,233 | 31,848 | 2.13.0–2.17.0 | P1 |
| Waje Special | ANR | `std::__ndk1::mutex::lock` 慢操作 | 4,035 | 2,199 | 2.13.0–2.17.0 | P1 |
| Waje Special | ANR | `MessageQueue.nativePollOnce` 根因未知 | 2,230 | 1,520 | 2.13.0–2.17.0 | P1 |
| Waje Special | FATAL | `Cocos2dxActivity.onLoadNativeLibraries` 找不到 `libcocos2djs.so` | 182 | 40 | 最近 2.17.0 | P1，发布门禁关注 |
| Waje Casino | NON_FATAL | Fish 子游戏 `t.isDelimited is not a function` | 6,052 | 1,731 | 最近 2.17.0 | P1 |
| Waje Casino | NON_FATAL | BottleSpin `cfg` 为空 | 1,997 | 480 | 最近 2.15.0 | P1 |
| Waje Game | NON_FATAL | `CompSlotsCell` 渲染时 state 为空 | 7,607 | 2,358 | 首见/最近均为 2.14.0 | P1 |
| Waje Game | ANR | `libcocos2djs.so` mutex lock | 675 | 382 | 首见/最近均为 2.14.0 | P1 |

### 2.2 现象解释

1. **传音老包启动 Fatal 是当前最紧急问题。**问题集中在 2.17.0，且 98% 在会话首秒发生，优先检查 `BuildConfigHelper` 初始化时机、Application/Context 生命周期和分包/渠道构建差异。
2. **主包异常量大，但 NON_FATAL 不等于全部阻断。**147,233 次表明异常捕获或 Cocos JS/原生桥接存在高频问题；需按游戏、页面、版本和用户漏斗复核是否阻断进入游戏、下注或结算。
3. **`libcocos2djs.so` 缺失属于安装/ABI/拆包链路风险。**虽然影响用户数暂时较小，但首秒 Fatal 对启动成功率敏感；应在 Android 8–16、arm64/armeabi-v7a、分包安装路径做发布前回归。
4. **传音新包的版本证据不足。**Crashlytics 主要数据集中在 2.14.0，当前未看到可用的 2.17.0 事件量；不能据此认定新包已更新或未更新，需要与发版清单、实际 APK `versionCode` 和 Firebase App ID 逐项核对。

## 3. Performance：主包可观测，老包可观测但监控卡不足，新包待补证

### 3.1 当前可见指标

| 包体 | 指标 | 当前值 | 样本/状态 | 解释 |
|---|---|---:|---|---|
| Waje Special | App start time | 2.94s | 有数据；90 分位视图 | 最近 7 日与前 7 日基本持平 |
| Waje Special | `uc/v1/check/account` 响应 | 3.34s | 成功率 100% | 网络成功不等于业务登录成功 |
| Waje Special | `uc/v1/check/account` 成功率 | 100% | 有数据 | 建议与业务登录成功事件对账 |
| Waje Special | `update.waje-special.com/**` 响应 | 4.52s | 139K samples | 最近 7 日约上升 20%，需关注更新/资源加载体验 |
| Waje Special | `prod-atlas-api.wgame2025.com/*` 成功率 | 97.88% | 660 samples | 低于纯网络成功目标，需按接口和错误码下钻 |
| Waje Casino | App start time | 2.69s | 有数据；90 分位视图 | 比前 7 日慢约 1% |
| Waje Casino | `uc/v1/login/tourist` 响应 | 9.18s | 4.4K samples | 游客登录链路偏慢，需和进入大厅/注册转化联查 |
| Waje Casino | `updata.whot.eu321.com/**` 响应 | 10.21s | 7.6K samples | 游戏资源/更新链路偏慢，影响弱网首进风险 |
| Waje Game | App start time、网络轨迹 | — | 当前 7 日无有效数据 | 标记为接入/版本/采集缺口，不判定为性能正常 |

### 3.2 监控结构问题

- 主包已有 6 个个人监控卡，但其中 AIHelp 初始化请求没有数据，不应作为 Waje 核心业务性能卡；建议替换为游戏初始化、余额初始化、下注接口或充值接口中已真实采集的轨迹。
- 老包目前主要只有 App start time 卡，核心登录、游戏进入、更新和支付链路缺少固定卡片。
- 三个包当前都显示“未设置 Performance 告警”的提示。至少应对 App start、核心配置接口、登录/游戏初始化接口配置版本和成功率告警。
- `Response`/`Success` 是网络性能口径，不能直接替代登录、充值、下注、结算等业务成功率；业务判断必须回到 Ares/BQ 服务端事实。

## 4. Analytics：有真实行为事件，但包体隔离和收入口径不足

Firebase Analytics 概览页在最近 28 日窗口显示：30 日活跃用户约 680 万、7 日约 250 万、1 日约 50.2 万；实时卡约 3,655 人，主要国家为 Nigeria。页面同时列出 Waje Special、Waje Casino、Waje Game 三个 Android 应用，说明当前页面承载的是项目级/多 App 汇总视图，不能直接把这些数字归属于某一个包。

### 4.1 已看到的事件

| 事件 | 概览事件量 | 业务含义边界 |
|---|---:|---|
| `notification_receive` | 47M | 通知接收次数，不是用户数 |
| `user_engagement` | 39M | 自动/标准互动事件 |
| `screen_view` | 24M | 页面/屏幕浏览次数 |
| `notification_dismiss` | 16M | 通知关闭次数 |
| `session_start` | 15M | 会话开始次数 |
| `rechargeAndWithdrawTotalTimes` | 4.7M | 自定义充值/提现相关事件次数，需与订单事实对账 |
| `first_open` | 3.9M | 首次打开次数，不等同注册用户 |
| `register` | 383K | 注册事件次数，需去重并与服务端注册事实核对 |
| `recharge` / `rechargeDollar` | 3.2M | 自定义充值事件次数/金额类事件，不能直接当成功订单金额 |

### 4.2 重要缺口

- Analytics 的 `Total revenue`、`Purchase revenue`、`Total ad revenue` 当前均显示 `$0.00`。这只能说明 Firebase 标准收入口径未形成可用数据，不能说明 Waje 没有充值收入或广告收入。
- 当前概览没有提供可审计的“包体 × 版本 × 渠道”明细；需要 GA4 Explore、GA4 Data API 或 BigQuery 导出按 `app_id/app_version/package/channel` 拆分。
- Firebase 事件数是行为观测，不替代 Waje 认证财务、生命周期、RTP、充值和提现数据；最终业务结论继续使用 BQ/Ares/GM 服务端事实。

## 5. 结论与行动优先级

### P0：先处理会阻断启动或误导经营判断的问题

1. **传音老包 2.17.0 启动 Fatal。**修复 Context 生命周期问题，完成冷启动、热启动、进程被杀恢复和不同渠道包回归。
2. **主包 native 库缺失 Fatal。**核查 APK/AAB split、ABI、安装来源和 `libcocos2djs.so` 打包完整性；把“首秒 Fatal”纳入发版门禁。
3. **冻结 Firebase 收入卡的经营解释。**Firebase `$0.00` 不能进入收入、LTV、ROI 或支付成功结论；以订单成功、资产到账、退款和提现事实重新对账。

### P1：恢复新包覆盖并建立可持续监控

1. **核对 Waje Game 的实际上线版本和 Firebase App ID。**对比发版记录、APK `applicationId/versionCode`、`google-services` 映射和 Crashlytics 最近事件；如当前线上版本不是 2.14.0，优先排查新版为何未上报。
2. **补齐主包/老包核心 Performance 卡。**启动、配置、游客/密码登录、游戏初始化、余额初始化、下注/结算和充值接口各至少保留一个真实 trace；删除或降级 AIHelp、NTP 等非核心轨迹。
3. **拆分 Analytics 包体口径。**将 Firebase/GA4 数据按 App ID、版本、包名、渠道和国家导出，与 BQ/Ares 的注册、活跃、充值成功和游戏行为做日级对账。
4. **处理主包高频异常和 ANR。**优先按 `game_id/page/module/app_version/device/OS` 分层；高频 NON_FATAL 只有在映射到核心漏斗后才能升级为业务 P0。
5. **打开版本和核心接口告警。**Performance 无告警状态不应长期存在；设置新版本启动、核心接口响应/成功率、采样量不足和数据断流告警。

## 6. 建议的自动化验收规则

| 规则 | 触发条件 | 结果 |
|---|---|---|
| 包体映射 | `applicationId`、Firebase App ID、包名任一不一致 | 阻断发布，P0 |
| Crashlytics 新版本烟测 | 发布后 24h 内无新版本 Crashlytics 事件 | 标记 `data_gap`，P1；不是“无异常” |
| 启动 Fatal | 首秒 Fatal 影响用户或事件较前稳定版明显上升 | 发布门禁，P0/P1 |
| Performance 新版本覆盖 | 7 日内 App start 或核心接口样本为 0 | 标记 `performance_gap`，P1 |
| Analytics 事件对账 | `register/recharge` 与服务端事实差异超过约定阈值 | 进入数据质量排查，禁止直接用于经营结论 |
| Performance 样本量 | 核心 trace 样本量不足或连续 24h 无数据 | 触发采集/版本/配置检查 |

## 7. 待研发/数据团队确认

- `com.hfhy.wajecasino.game` 当前线上实际版本、Firebase Performance SDK 是否启用、采集开关是否被远程配置关闭。
- 三个包的 Firebase Analytics 数据流/GA4 数据流是否分开，是否已配置 BigQuery 导出；当前 Firebase 概览不能替代此确认。
- `recharge`、`rechargeDollar`、`rechargeAndWithdrawTotalTimes` 的事件触发时机、去重键、成功/失败枚举和金额单位。
- Crashlytics 的 Cocos JS 异常是否已按游戏、页面、版本和 `trace_id` 写入自定义键；否则无法把异常量映射到 GAMESTART/GAMEEND/支付漏斗。
- 主包和老包 Performance 个人卡是否需要沉淀为团队共享监控；本轮没有修改任何个人视图或告警配置。

## 8. 来源与审计边界

- Firebase 项目环境：`waje-special`；本地项目目录 `/Users/robin/Documents/wajetan_analyst`；当前环境配置和活动项目已核对。
- Crashlytics：三个 Android App ID 的 `topIssues`、`topVersions`、`topOperatingSystems`、`topAndroidDevices`，窗口为 2026-08-15 00:00 至 2026-08-21 11:50（香港时间）。
- Analytics：Firebase Console Analytics Dashboard，概览窗口为 2026-07-24 至 2026-08-20；页面显示多 App 汇总。
- Performance：Firebase Console Performance，三个 Android App 的最近 7 日视图（2026-08-15 至 2026-08-21），90 分位；主包/老包有数据，新包当前无有效数据。
- 本报告不读取或保存 Firebase 密钥、浏览器 Cookie、密码、Token、用户明细、设备标识或完整事件原文。

关联资料：

- [[Waje全链路数据需求与埋点设计总表-2026-08-11]]
- [[Waje埋点事件与属性字典-2026-08-11]]
- [[Waje版本体验与福利风控验证SOP-2026-08-14]]
- [[Agent项目背景与知识图谱快速上手-2026-08-17]]
