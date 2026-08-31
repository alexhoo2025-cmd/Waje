---
type: app_firebase_analytics_bigquery_dictionary_status
project: waje-special
updated: 2026-08-24
status: export_pending_with_official_schema_reference
scope: [android, firebase, analytics, associated_bigquery]
---

# Waje App Firebase Analytics 与关联 BigQuery 数据字典（参考结构已整理）

> 范围限于三个 Android 生产包的 Firebase / BigQuery 数据。本轮不读取数据量或原始事件。字段分为两层：**实例已核验**（项目、包名、数据流和导出配置）与 **官方参考结构**（字段与类型）；首张实例表出现后，以 `INFORMATION_SCHEMA` 的实际 schema 为准补充覆盖情况。

## 1. 当前结论

- Firebase 项目 `waje-special` 和三个 Android App 映射已核验。
- Firebase 已关联 Google Analytics Property `470712959`，三个 Android 数据流已确认。
- GA4 报表读取被 `Missing permissions` 阻断，未读取事件、版本、包体或用户汇总指标。
- Firebase BigQuery Link 已启用；App Analytics 已保存为仅三个 Android 包、Daily 导出、关闭广告标识符。
- 当前关联项目为 `waje-special`，区域 `europe-west4`；预期 Analytics 数据集为 `analytics_470712959`，但尚未创建。
- 已整理 GA4 Analytics、Firebase Performance、Crashlytics 和 Firebase Sessions 的官方参考表结构、字段与类型；它们不是当前实例表的存在性证明。

## 2. 配置复核：为什么当前不能读取

| 核验点 | 实际结果 | 结论 |
|---|---|---|
| Firebase 项目 | `waje-special` 可通过 Firebase MCP 读取 | 项目和 Android App 注册正常。 |
| Google Analytics | Property `470712959` 与三个 Android Stream 可见 | 数据流关联存在。 |
| GA4 报表页 | `Missing permissions` | 当前身份不能读取 Analytics 指标、事件或维度。 |
| Firebase BigQuery Integration | linked | 已进入 Manage 页面并读取现有导出产品。 |
| 导出范围 | saved_pending_first_daily_export | 已保存为仅三个 Android 包、Daily、无广告标识符。 |
| 关联 BigQuery 项目 | `waje-special` | Firebase 导出数据集不在 `waje-analytics-readonly`。 |

**配置结论：**此前未形成可验证回执；本次已确认 Firebase Link 与 App Analytics 导出设置存在，并已将导出范围收敛为三个 Android 包。`analytics_470712959` 尚未创建，等待首个每日导出；如果超过 48 小时仍未出现，再按 GA4 导出服务账号、BigQuery API、区域策略和日志排查。

## 3. 当前可用的 App 数据字典

| App | 包名 | Firebase App ID | GA4 Stream ID | 状态 |
|---|---|---|---:|---|
| Waje Special | `com.hfhy.waje.special` | `1:128692700786:android:e0ca00db9431011afea4eb` | 10068369856 | ACTIVE |
| Waje Casino | `com.hfhy.wajecasino.palmgame` | `1:128692700786:android:cc43a6abd8fd9fc4fea4eb` | 11103507430 | ACTIVE |
| Waje Game | `com.hfhy.wajecasino.game` | `1:128692700786:android:63d7e4b8a16eec53fea4eb` | 14405888142 | ACTIVE |

Google Analytics Property：`470712959`。本映射仅证明项目、Android 包与数据流存在；不等于事件、版本维度或 BigQuery 导出已经可用。

## 4. Analytics 汇总状态

| 检查项 | 结果 | 说明 |
|---|---|---|
| Firebase Google Analytics 关联 | verified | 项目设置页显示 Enabled，并可读取 Property 与 Stream 映射。 |
| GA4 指标与事件 | blocked_permission | Property 页面提示 Missing permissions。 |
| 包体/版本/渠道分析 | blocked_permission | 未取得真实事件或维度，不生成汇总值。 |
| 收入、充值、注册统计 | not_read | 需在 GA4 读取权限恢复后，与服务端业务事实对账。 |

## 5. 关联 BigQuery 状态

| 检查项 | 结果 | 说明 |
|---|---|---|
| Firebase BigQuery Integration | linked_pending_data | Link 已启用，当前为 BigQuery Sandbox。 |
| 关联项目 / 区域 | `waje-special` / `europe-west4` | Analytics 数据集按当前 Link 在源项目中创建。 |
| Analytics 数据集 | `analytics_470712959` 未创建 | 需要首个 Daily sync 才能核验表与 schema。 |
| 已存在 Firebase 产品数据集 | `firebase_crashlytics`、`firebase_sessions`、`firebase_performance`、`firebase_messaging`、`firebase_imported_segments` | 均位于 `waje-special` / `europe-west4`。 |
| App BigQuery 实例表与 schema | pending_first_daily_export | 当前未发现可读取的实例表；下方已给出官方参考 schema，待首批表生成后逐项核验。 |

## 6. 已保存的 Analytics 导出配置

| 项目 | 已保存设置 |
|---|---|
| 导出 App | `com.hfhy.waje.special`、`com.hfhy.wajecasino.palmgame`、`com.hfhy.wajecasino.game` |
| 未导出 App | `com.wajegame.wajegame`、Waje Special Web |
| 导出模式 | Daily 开启；Streaming 关闭 |
| 广告标识符 | 关闭 |
| 区域 | `europe-west4` |
| 预期数据集 | `analytics_470712959` |
| 首批传播 | 等待下一个每日同步；最长按 48 小时核验 |

## 7. 首批数据出现后的固定收集顺序

1. 在 `waje-special` / `europe-west4` 核验 `analytics_470712959` 是否出现。
2. 盘点数据集中的每日表、表结构、最新完整日期和每日行数。
3. 用 `stream_id`、`app_info.id`、版本字段区分三个 Android 包。
4. 用本报告的官方参考字典与实际 `INFORMATION_SCHEMA` 逐项核对，记录新增、缺失及自定义字段，再补充包体×版本×事件的汇总统计。
5. 若 48 小时后仍无数据集，核验 GA4 导出服务账号、BigQuery API、区域组织策略和 Logs Explorer 错误。
6. 注册、充值、收入、提现等 Analytics 事件只作行为核验；最终业务结果以服务端订单、资产与账务事实为准。

## 8. 数据边界

- 不读取或保存用户标识、广告标识、设备标识、原始事件行、交易明细、Cookie、Token 或密钥。
- 不将 Firebase 已注册、Analytics 已关联或 Firebase 控制台页面可见误写为 BigQuery 导出成功。
- 不将 Analytics 事件次数解释为唯一用户、成功订单或收入。

## 9. 可复跑资产

- [数据源状态 JSON](../../analysis/app_firebase_analytics_bigquery_collection_2026_08_24/source_status.json)
- [官方参考 schema JSON](../../analysis/app_firebase_analytics_bigquery_collection_2026_08_24/schema_reference.json)
- 后续 BigQuery 查询只能在实际关联项目和表名确认后新增；本轮不查询数据。

## 10. 官方参考表目录（实例待生成）

| 产品 | 数据集 | 表命名 / 结构 | 记录粒度 | 三个 Android 包的区分方式 | 当前状态 |
|---|---|---|---|---|---|
| Google Analytics for Firebase | `analytics_470712959` | `events_YYYYMMDD`（Daily） | 事件导出记录 | `stream_id`、`app_info.id`、`app_info.firebase_app_id`、`app_info.version`、`platform` | `reference_only`；导出已保存，数据集待生成 |
| Firebase Performance | `firebase_performance` | Firebase 按 App 生成表，实际表名以首次出现的元数据为准 | 单条 Performance 事件 | App 表、`app_display_version`、`app_build_version` | `reference_only`；不据此断言当前有表 |
| Crashlytics | `firebase_crashlytics` | 包名中的 `.` 替换为 `_`，后缀 `_ANDROID` | 单个崩溃／非致命异常／ANR 事件 | 每个包独立表；`bundle_identifier`、`application.*` | `reference_only`；只描述官方命名规则 |
| Firebase Sessions | `firebase_sessions` | 同样按包名替换字符并加 `_ANDROID` | 单个 session event | 每个包独立表；`application.*` | `reference_only` |

Analytics 日表由三个 App 共用一个数据集；Daily 表可能在事件发生日后继续更新至多 3 天。当前为 Sandbox，仅 Daily，不会生成 `events_intraday_YYYYMMDD`。[GA4 官方 schema](https://support.google.com/analytics/answer/7029846?hl=en)

### 10.1 已知 App 与官方表名映射

| App | 包名 | GA4 Stream ID | Crashlytics / Sessions 官方命名模式 |
|---|---|---:|---|
| Waje Special | `com.hfhy.waje.special` | 10068369856 | `com_hfhy_waje_special_ANDROID` |
| Waje Casino | `com.hfhy.wajecasino.palmgame` | 11103507430 | `com_hfhy_wajecasino_palmgame_ANDROID` |
| Waje Game | `com.hfhy.wajecasino.game` | 14405888142 | `com_hfhy_wajecasino_game_ANDROID` |

表名映射仅适用于 Crashlytics / Sessions 已启用并实际生成表的情形；Analytics 通过同一 `events_YYYYMMDD` 中的流与 App 字段区分，不会为每个包生成独立日表。

## 11. Google Analytics for Firebase：`events_YYYYMMDD` 参考字段字典

### 11.1 事件、时间与 App 归属

| 字段 | BigQuery 类型 | 含义 / 使用边界 |
|---|---|---|
| `event_date` | `STRING` | App 注册时区中的事件日期，格式 `YYYYMMDD`。 |
| `event_timestamp` | `INT64` | Analytics 接收事件的 UTC 微秒时间戳。 |
| `event_name` | `STRING` | 事件名；自定义事件的业务含义须由埋点契约确认。 |
| `event_previous_timestamp` / `event_original_occurrence_timestamp` / `event_server_timestamp_offset` | `INT64` | 客户端事件顺序、原始发生时间与上传延迟辅助字段。 |
| `event_bundle_sequence_id` / `batch_event_index` / `batch_ordering_id` / `batch_page_id` | `INT64` | 批次与顺序字段；用于排查上报顺序，不用于业务 KPI。 |
| `event_value_in_usd` | `FLOAT64` | `value` 参数折算美元；不等同于服务器确认收入。 |
| `platform` | `STRING` | 数据流平台，三个本次目标包应为 `ANDROID`。 |
| `stream_id` | `STRING` | 数据流 ID；与上表的三个 Stream ID 对应。 |
| `app_info` | `STRUCT` | Native App 信息容器。 |
| `app_info.id` | `STRING` | Android 包名；用于包体隔离。 |
| `app_info.firebase_app_id` | `STRING` | Firebase App ID；用于跨包精确隔离。 |
| `app_info.version` | `STRING` | Android `versionName`。 |
| `app_info.install_source` / `app_info.install_store` | `STRING` | 安装来源／商店信息；仅在实际填充时分析。 |

### 11.2 事件参数、用户属性与隐私字段

| 字段 | BigQuery 类型 | 含义 / 使用边界 |
|---|---|---|
| `event_params` | `ARRAY&lt;STRUCT&gt;` | 每个事件的标准／自定义参数集合；必须 `UNNEST` 后按 `key` 读取。 |
| `event_params.key` | `STRING` | 参数名。 |
| `event_params.value.string_value` | `STRING` | 字符串参数值。 |
| `event_params.value.int_value` | `INT64` | 整数参数值。 |
| `event_params.value.double_value` / `float_value` | `FLOAT64` | 浮点参数值；`float_value` 在官方说明中通常未使用。 |
| `user_properties` | `ARRAY&lt;STRUCT&gt;` | 用户属性键值集合；自定义属性含义需由业务确认。 |
| `user_properties.key` | `STRING` | 用户属性名。 |
| `user_properties.value.string_value` / `int_value` / `double_value` / `float_value` | `STRING` / `INT64` / `FLOAT64` / `FLOAT64` | 用户属性值的联合类型。 |
| `user_properties.value.set_timestamp_micros` | `INT64` | 属性最后设置时间（微秒）。 |
| `user_id` / `user_pseudo_id` | `STRING` | 用户／伪用户标识；本专题不读取、导出或作为报表明细。 |
| `user_first_touch_timestamp` | `INT64` | 首次打开 App 的微秒时间。 |
| `is_active_user` | `BOOLEAN` | 当日是否活跃，仅 Daily 表填充。 |
| `user_ltv.revenue` / `user_ltv.currency` | `FLOAT64` / `STRING` | 生命周期价值与币种；不得替代服务端账务。 |
| `privacy_info.analytics_storage` / `ads_storage` / `uses_transient_token` | `STRING` | 同意状态及临时 token 采集标记；仅用于口径和合规审计。 |

### 11.3 设备、地域、获客与归因

| 字段组 | BigQuery 类型 | 包含的叶子字段 | 用途 |
|---|---|---|---|
| `device` | `STRUCT` | `category`、`mobile_brand_name`、`mobile_model_name`、`mobile_marketing_name`、`mobile_os_hardware_model`、`operating_system`、`operating_system_version`、`language`、`time_zone_offset_seconds` | 设备／系统分层与低端机兼容性分析。 |
| `device.advertising_id` / `vendor_id` / `is_limited_ad_tracking` | `STRING` / `STRING` / `BOOLEAN` | 广告标识及限制标记；本次导出已关闭广告标识符，且不可作明细或拼接身份使用。 |
| `geo` | `STRUCT` | `continent`、`sub_continent`、`country`、`region`、`metro`、`city`，均为 `STRING` | IP 推断的地域，用于聚合地域分析。 |
| `traffic_source` | `STRUCT` | `name`、`medium`、`source`，均为 `STRING` | 首次获客来源；不会随之后的 campaign 改写。 |
| `collected_traffic_source` | `STRUCT` | `manual_campaign_id`、`manual_campaign_name`、`manual_source`、`manual_medium`、`manual_term`、`manual_content`、`manual_source_platform`、`manual_creative_format`、`manual_marketing_tactic`、`gclid`、`dclid`、`srsltid`，均为 `STRING` | 本次采集时携带的 UTM／点击标识。 |
| `session_traffic_source_last_click` | `STRUCT` | `manual_campaign`、`google_ads_campaign`、`cross_channel_campaign`、`sa360_campaign`、`cm360_campaign`、`dv360_campaign` 子结构；其标识／名称／来源／媒介叶子字段均为 `STRING` | 最近点击会话归因；相关广告平台未接入时通常为空。 |

### 11.4 电商与商品字段

| 字段组 | BigQuery 类型 | 说明 / 边界 |
|---|---|---|
| `ecommerce` | `STRUCT` | `total_item_quantity`、`unique_items` 为 `INT64`；`purchase_revenue[_in_usd]`、`refund_value[_in_usd]`、`shipping_value[_in_usd]`、`tax_value[_in_usd]` 为 `FLOAT64`；`transaction_id` 为 `STRING`。仅在对应电商事件填充。 |
| `items` | `ARRAY&lt;STRUCT&gt;` | 商品数组；`item_id`、`item_name`、`item_brand`、分类、券、促销、列表及创意字段为 `STRING`；价格／收入／退款字段为 `FLOAT64`；`quantity` 为 `INT64`。 |
| `items.item_params` | `ARRAY&lt;STRUCT&gt;` | 商品自定义参数；`key` 为 `STRING`，`value.string_value`／`int_value`／`double_value`／`float_value` 分别为 `STRING`／`INT64`／`FLOAT64`／`FLOAT64`。 |
| `publisher` | `STRUCT` | AdMob 相关字段：`ad_revenue_in_usd` 为 `FLOAT64`，`ad_format`、`ad_source_name`、`ad_unit_id` 为 `STRING`；未接入时为空。 |

上述是 GA4 原生导出的标准结构。`event_params`、`user_properties` 和 `items.item_params` 的**实际 key 列表**由 Waje 客户端埋点决定，不能在没有实例表时预填。[GA4 官方字段定义](https://support.google.com/analytics/answer/7029846?hl=en)

## 12. Firebase Performance：`firebase_performance` 参考字段字典

Performance 是 Android／Apple 原生产品，非 H5 Web Performance。每条记录为一个 Performance 事件；实际 App 表名、分区和是否有数据需等实例表出现后核验。

| 字段 | BigQuery 类型 | 含义 |
|---|---|---|
| `event_timestamp` | `TIMESTAMP` | 客户端事件开始时间。 |
| `app_display_version` / `app_build_version` | `STRING` | Android `versionName`／`versionCode`。 |
| `os_version` / `device_name` / `country` / `carrier` / `radio_type` | `STRING` | 操作系统、设备、国家、运营商和网络制式。 |
| `custom_attributes` | `ARRAY&lt;RECORD&gt;` | 自定义属性；`key`、`value` 均为 `STRING`。 |
| `event_type` / `event_name` / `parent_trace_name` | `STRING` | 事件类别、Trace／指标名称、父 Trace 名称（仅 `TRACE_METRIC`）。 |
| `trace_info.duration_us` | `INT64` | Duration／Screen／Metric 对应 Trace 的时长，微秒。 |
| `trace_info.screen_info.slow_frame_ratio` / `frozen_frame_ratio` | `FLOAT64` | Screen Trace 慢帧／冻结帧占比。 |
| `trace_info.metric_info.metric_value` | `INT64` | 自定义 Trace 指标值。 |
| `network_info.response_code` | `INT64` | HTTP 状态码。 |
| `network_info.response_mime_type` / `request_http_method` | `STRING` | 响应 MIME、请求方法。 |
| `network_info.request_payload_bytes` / `response_payload_bytes` | `INT64` | 请求／响应体积（字节）。 |
| `network_info.request_completed_time_us` / `response_initiated_time_us` / `response_completed_time_us` | `INT64` | 相对 `event_timestamp` 的网络阶段耗时（微秒）。 |

`event_type` 的官方枚举为 `DURATION_TRACE`、`SCREEN_TRACE`、`TRACE_METRIC`、`NETWORK_REQUEST`。其中 `_app_start` 是常用启动 Trace；网络、屏幕和自定义 Trace 是否出现取决于 SDK 和客户端实际采集。[Performance 官方 schema](https://firebase.google.com/docs/perf-mon/bigquery-export?hl=en)

## 13. Crashlytics 与 Firebase Sessions：参考字段字典

### 13.1 Crashlytics：`firebase_crashlytics.<package>_ANDROID`

| 字段组 | BigQuery 类型 | 说明 / 隐私边界 |
|---|---|---|
| `event_id` / `issue_id` / `variant_id` / `error_type` | `STRING` | 事件、问题、变体与类型（如 `FATAL`、`NON_FATAL`、`ANR`）。 |
| `event_timestamp` | `TIMESTAMP` | 故障发生时间。 |
| `bundle_identifier` / `platform` / `process_state` / `crashlytics_sdk_versions` | `STRING` | 包名、平台、前后台状态、SDK 版本。 |
| `application.build_version` / `application.display_version` | `STRING` | App 构建号／展示版本。 |
| `device.architecture` / `manufacturer` / `model` / `operating_system.*` | `STRING`（结构体叶子） | 设备和系统分层。 |
| `memory.free` / `memory.used` / `storage.free` / `storage.used` | `INT64` | 内存／存储字节数。 |
| `blame_frame`、`exceptions`、`threads` | `RECORD` / `REPEATED RECORD` | 归因帧、Android 异常链与线程／堆栈；帧的地址／行号／偏移为 `INT64`，其余符号字段多为 `STRING`。 |
| `breadcrumbs` / `logs` / `custom_keys` | `REPEATED RECORD` | 分别是 Analytics 面包屑、日志和开发者自定义键值。不得导出或展示可能包含用户信息的值。 |
| `installation_uuid` / `firebase_session_id` / `user.id` | `STRING` | 安装／会话／App 用户标识；仅作受控审计字段，不读取明细。 |

### 13.2 Firebase Sessions：`firebase_sessions.<package>_ANDROID`

| 字段 | BigQuery 类型 | 说明 |
|---|---|---|
| `instance_id` / `session_id` / `first_session_id` | `STRING` | 安装和会话标识；不得输出明细。 |
| `session_index` | `INTEGER` | 冷启动后的会话序号。 |
| `event_type` | `STRING` | 会话事件类型，如 `SESSION_START`。 |
| `event_timestamp` / `received_timestamp` | `TIMESTAMP` | 发生／服务端接收时间。 |
| `performance_data_collection_enabled` / `crashlytics_data_collection_enabled` | `BOOLEAN` | 会话发生时对应 SDK 数据采集是否启用。 |
| `application.build_version` / `application.display_version` | `STRING` | App 版本。 |
| `device.model` / `device.manufacturer` | `STRING` | 设备信息。 |
| `operating_system.display_version` / `name` / `type` / `device_type` | `STRING` | 系统与设备类别。 |

Crashlytics 表中每行代表一个错误事件；Sessions 表中每行代表一个 session event。完整嵌套字段以 [Crashlytics / Sessions 官方 schema](https://firebase.google.com/docs/crashlytics/bigquery-dataset-schema) 为准。

## 14. 实例表生成后的核验规则

1. 仅查询 `waje-special`、区域 `europe-west4` 的 `INFORMATION_SCHEMA`，获取表清单和字段路径；不读取原始事件行。
2. 核对 Analytics 每条记录的 `platform='ANDROID'`，并以 `stream_id` + `app_info.firebase_app_id` 与三个已知 App 映射对齐。
3. 记录实际字段相对本参考的新增、弃用、空字段和自定义参数 key；不将“参考字段存在”误写成“已经采集”。
4. 对任何用户／安装／广告／交易标识字段，结果仅保留聚合或覆盖率，不落盘字段值。
