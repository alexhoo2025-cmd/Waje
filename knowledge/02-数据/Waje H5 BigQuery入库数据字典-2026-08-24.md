---
type: h5_bigquery_schema_dictionary
updated: 2026-08-24
project: waje-analytics-readonly
dataset: analytics_504208609
platform: WEB
stream_id: "12134390945"
status: certified
tags: [H5, GA4, BigQuery, schema, data-dictionary]
---

# Waje H5 BigQuery 入库数据字典

> 适用范围：Waje H5 的 GA4 原生 BigQuery 日表。本文仅描述已核验的 Web Analytics 行为数据与字段结构；不包含其他端的数据源或统计。

## 1. 当前入库概览

- 数据集：`analytics_504208609`；区域：US。
- 平台：`WEB`；数据流：`12134390945`。
- 已核验日表结构一致：原始 GA4 schema 为 31 个顶层字段、217 个字段路径。
- 本阅读版保留 208 个 H5 相关字段路径；已排除 9 个无 Web 语义的标准字段。

| 日表 | 事件行数 | 事件名称数 | 事件日期 | 过期时间 |
|---|---:|---:|---|---|
| `events_20260820` | 166,451 | 24 | 20260820 | 2026-10-20 15:34:56（UTC+8） |
| `events_20260821` | 166,055 | 24 | 20260821 | 2026-10-21 15:38:18（UTC+8） |
| `events_20260822` | 163,270 | 24 | 20260822 | 2026-10-22 14:54:48（UTC+8） |

## 2. H5 字段结构与使用范围

| 分组 | 代表字段 | 说明 |
|---|---|---|
| 事件标识与时间 | `event_date`、`event_timestamp`、`event_name`、`batch_*` | 事件名称、发生时间与批次排序 |
| 事件参数 | `event_params[]` | 自定义参数容器；需用事件名与参数键共同解释 |
| 设备与浏览器 | `device.*`、`device.web_info.*` | 终端、系统、浏览器、语言与 Host |
| 地理位置 | `geo.*` | 国家、地区、城市与都会区 |
| 流量与归因 | `traffic_source.*`、`collected_traffic_source.*`、`session_traffic_source_last_click.*` | UTM、广告点击与会话归因 |
| 电商与商品 | `ecommerce.*`、`items[]` | 交易、商品、收入与退款；以服务端事实复核 |
| 用户与隐私 | `user_*`、`user_properties[]`、`privacy_info.*` | 受控聚合、生命周期与存储同意状态 |

## 3. 完整 H5 字段字典（208 个字段路径）



| 字段 | 类型 | 结构 | 分组 | 含义 | H5 当前状态 | 隐私/使用边界 |
|---|---|---|---|---|---|---|
| `batch_event_index` | `INT64` | 标量 | 批次与排序 | 批次内事件序号。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `batch_ordering_id` | `INT64` | 标量 | 批次与排序 | 批次排序标识。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `batch_page_id` | `INT64` | 标量 | 批次与页面关联 | 页面批次/页面关联标识。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `collected_traffic_source` | `STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, manual_source_platform STRING, manual_creative_format STRING, manual_marketing_tactic STRING, gclid STRING, dclid STRING, srsltid STRING>` | 嵌套结构 | 采集归因 | 事件采集时得到的 UTM 与广告点击信息。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `collected_traffic_source.dclid` | `STRING` | 标量 | 采集归因 | 广告点击标识；受限归因字段。 | schema存在；未输出字段值 | 受限归因标识；仅授权分析 |
| `collected_traffic_source.gclid` | `STRING` | 标量 | 采集归因 | 广告点击标识；受限归因字段。 | schema存在；未输出字段值 | 受限归因标识；仅授权分析 |
| `collected_traffic_source.manual_campaign_id` | `STRING` | 标量 | 采集归因 | 手工活动标识或名称。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `collected_traffic_source.manual_campaign_name` | `STRING` | 标量 | 采集归因 | 手工活动标识或名称。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `collected_traffic_source.manual_content` | `STRING` | 标量 | 采集归因 | 采集归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `collected_traffic_source.manual_creative_format` | `STRING` | 标量 | 采集归因 | 采集归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `collected_traffic_source.manual_marketing_tactic` | `STRING` | 标量 | 采集归因 | 采集归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `collected_traffic_source.manual_medium` | `STRING` | 标量 | 采集归因 | 手工媒介。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `collected_traffic_source.manual_source` | `STRING` | 标量 | 采集归因 | 手工来源或采集来源。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `collected_traffic_source.manual_source_platform` | `STRING` | 标量 | 采集归因 | 采集归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `collected_traffic_source.manual_term` | `STRING` | 标量 | 采集归因 | 采集归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `collected_traffic_source.srsltid` | `STRING` | 标量 | 采集归因 | 广告点击标识；受限归因字段。 | schema存在；未输出字段值 | 受限归因标识；仅授权分析 |
| `device` | `STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, mobile_marketing_name STRING, mobile_os_hardware_model STRING, operating_system STRING, operating_system_version STRING, vendor_id STRING, advertising_id STRING, language STRING, is_limited_ad_tracking STRING, time_zone_offset_seconds INT64, browser STRING, browser_version STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>` | 嵌套结构 | 设备与浏览器 | 设备与浏览器结构。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `device.browser` | `STRING` | 标量 | 设备与浏览器 | 浏览器名称。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `device.browser_version` | `STRING` | 标量 | 设备与浏览器 | 浏览器版本。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `device.category` | `STRING` | 标量 | 设备与浏览器 | 终端类别，如 mobile、desktop、tablet。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `device.language` | `STRING` | 标量 | 设备与浏览器 | 设备或浏览器语言。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `device.mobile_brand_name` | `STRING` | 标量 | 设备与浏览器 | 移动设备品牌。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `device.mobile_marketing_name` | `STRING` | 标量 | 设备与浏览器 | 移动设备营销名称。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `device.mobile_model_name` | `STRING` | 标量 | 设备与浏览器 | 移动设备型号。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `device.mobile_os_hardware_model` | `STRING` | 标量 | 设备与浏览器 | 移动设备硬件型号。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `device.operating_system` | `STRING` | 标量 | 设备与浏览器 | 操作系统名称。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `device.operating_system_version` | `STRING` | 标量 | 设备与浏览器 | 操作系统版本。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `device.time_zone_offset_seconds` | `INT64` | 标量 | 设备与浏览器 | 设备时区偏移秒数。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `device.web_info` | `STRUCT<browser STRING, browser_version STRING, hostname STRING>` | 嵌套结构 | 设备与浏览器 | Web 设备扩展信息。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `device.web_info.browser` | `STRING` | 标量 | 设备与浏览器 | Web 浏览器名称。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `device.web_info.browser_version` | `STRING` | 标量 | 设备与浏览器 | Web 浏览器版本。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `device.web_info.hostname` | `STRING` | 标量 | 设备与浏览器 | Web Host。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `ecommerce` | `STRUCT<total_item_quantity INT64, purchase_revenue_in_usd FLOAT64, purchase_revenue FLOAT64, refund_value_in_usd FLOAT64, refund_value FLOAT64, shipping_value_in_usd FLOAT64, shipping_value FLOAT64, tax_value_in_usd FLOAT64, tax_value FLOAT64, unique_items INT64, transaction_id STRING>` | 嵌套结构 | 电商与商品 | GA4 电商交易结构。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `ecommerce.purchase_revenue` | `FLOAT64` | 标量 | 电商与商品 | 购买收入。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `ecommerce.purchase_revenue_in_usd` | `FLOAT64` | 标量 | 电商与商品 | 购买收入美元折算。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `ecommerce.refund_value` | `FLOAT64` | 标量 | 电商与商品 | 退款金额。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `ecommerce.refund_value_in_usd` | `FLOAT64` | 标量 | 电商与商品 | 退款金额美元折算。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `ecommerce.shipping_value` | `FLOAT64` | 标量 | 电商与商品 | 电商交易子字段。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `ecommerce.shipping_value_in_usd` | `FLOAT64` | 标量 | 电商与商品 | 电商交易子字段。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `ecommerce.tax_value` | `FLOAT64` | 标量 | 电商与商品 | 电商交易子字段。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `ecommerce.tax_value_in_usd` | `FLOAT64` | 标量 | 电商与商品 | 电商交易子字段。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `ecommerce.total_item_quantity` | `INT64` | 标量 | 电商与商品 | 交易商品总数量。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `ecommerce.transaction_id` | `STRING` | 标量 | 电商与商品 | 交易标识，需与服务端事实对账。 | schema存在；未输出字段值 | 受限标识；禁止直接输出，只做脱敏聚合/对账 |
| `ecommerce.unique_items` | `INT64` | 标量 | 电商与商品 | 交易中不同商品数。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `event_bundle_sequence_id` | `INT64` | 标量 | 事件标识与时间 | 客户端事件批次序号。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `event_date` | `STRING` | 标量 | 事件标识与时间 | GA4 导出业务日期；按 Property 时区解释。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `event_dimensions` | `STRUCT<hostname STRING>` | 嵌套结构 | 页面 Host | 事件维度扩展结构。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `event_dimensions.hostname` | `STRING` | 标量 | 页面 Host | 事件所属 Host。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `event_name` | `STRING` | 标量 | 事件标识与时间 | 事件名称；标准事件或 Waje 自定义事件。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `event_original_occurrence_timestamp` | `INT64` | 标量 | 事件标识与时间 | 事件原始发生时间。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `event_params` | `ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>` | 重复数组 | 事件参数 | 事件参数数组；含义由 event_name 与参数 key 共同决定。 | 已观察容器；键值含义 provisional | 可用于聚合分析；不输出原始值 |
| `event_params.key` | `STRING` | 标量 | 事件参数 | 事件参数名称。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `event_params.value` | `STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>` | 嵌套结构 | 事件参数 | 参数值容器，按实际类型读取。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `event_params.value.double_value` | `FLOAT64` | 标量 | 事件参数 | 双精度参数值。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `event_params.value.float_value` | `FLOAT64` | 标量 | 事件参数 | 浮点参数值。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `event_params.value.int_value` | `INT64` | 标量 | 事件参数 | 整数参数值。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `event_params.value.string_value` | `STRING` | 标量 | 事件参数 | 字符串参数值。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `event_previous_timestamp` | `INT64` | 标量 | 事件标识与时间 | 同一用户上一次事件时间。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `event_server_timestamp_offset` | `INT64` | 标量 | 事件标识与时间 | 客户端与服务端时间偏移。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `event_timestamp` | `INT64` | 标量 | 事件标识与时间 | 事件发生时间，Unix 微秒时间戳。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `event_value_in_usd` | `FLOAT64` | 标量 | 事件价值 | 事件价值的美元折算字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `geo` | `STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>` | 嵌套结构 | 地理位置 | 地理位置结构。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `geo.city` | `STRING` | 标量 | 地理位置 | 城市。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `geo.continent` | `STRING` | 标量 | 地理位置 | 大洲。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `geo.country` | `STRING` | 标量 | 地理位置 | 国家。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `geo.metro` | `STRING` | 标量 | 地理位置 | 都会区。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `geo.region` | `STRING` | 标量 | 地理位置 | 地区/州。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `geo.sub_continent` | `STRING` | 标量 | 地理位置 | 次大洲。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `is_active_user` | `BOOL` | 标量 | 用户生命周期 | GA4 标准嵌套字段；按字段路径和事件上下文解释。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `items` | `ARRAY<STRUCT<item_id STRING, item_name STRING, item_brand STRING, item_variant STRING, item_category STRING, item_category2 STRING, item_category3 STRING, item_category4 STRING, item_category5 STRING, price_in_usd FLOAT64, price FLOAT64, quantity INT64, item_revenue_in_usd FLOAT64, item_revenue FLOAT64, item_refund_in_usd FLOAT64, item_refund FLOAT64, coupon STRING, affiliation STRING, location_id STRING, item_list_id STRING, item_list_name STRING, item_list_index STRING, promotion_id STRING, promotion_name STRING, creative_name STRING, creative_slot STRING, item_params ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>>>` | 重复数组 | 电商与商品 | 商品明细数组；展开时需防止行数膨胀。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `items.affiliation` | `STRING` | 标量 | 电商与商品 | 商品明细子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `items.coupon` | `STRING` | 标量 | 电商与商品 | 优惠券。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `items.creative_name` | `STRING` | 标量 | 电商与商品 | 商品明细子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `items.creative_slot` | `STRING` | 标量 | 电商与商品 | 商品明细子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `items.item_brand` | `STRING` | 标量 | 电商与商品 | 商品品牌。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `items.item_category` | `STRING` | 标量 | 电商与商品 | 商品一级分类。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `items.item_category2` | `STRING` | 标量 | 电商与商品 | 商品明细子字段。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `items.item_category3` | `STRING` | 标量 | 电商与商品 | 商品明细子字段。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `items.item_category4` | `STRING` | 标量 | 电商与商品 | 商品明细子字段。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `items.item_category5` | `STRING` | 标量 | 电商与商品 | 商品明细子字段。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `items.item_id` | `STRING` | 标量 | 电商与商品 | 商品标识。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `items.item_list_id` | `STRING` | 标量 | 电商与商品 | 商品明细子字段。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `items.item_list_index` | `STRING` | 标量 | 电商与商品 | 商品明细子字段。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `items.item_list_name` | `STRING` | 标量 | 电商与商品 | 商品明细子字段。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `items.item_name` | `STRING` | 标量 | 电商与商品 | 商品名称。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `items.item_params` | `ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>` | 重复数组 | 电商与商品 | 商品级自定义参数。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `items.item_params.key` | `STRING` | 标量 | 电商与商品 | 商品明细子字段。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `items.item_params.value` | `STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>` | 嵌套结构 | 电商与商品 | 商品明细子字段。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `items.item_params.value.double_value` | `FLOAT64` | 标量 | 电商与商品 | 商品明细子字段。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `items.item_params.value.float_value` | `FLOAT64` | 标量 | 电商与商品 | 商品明细子字段。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `items.item_params.value.int_value` | `INT64` | 标量 | 电商与商品 | 商品明细子字段。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `items.item_params.value.string_value` | `STRING` | 标量 | 电商与商品 | 商品明细子字段。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `items.item_refund` | `FLOAT64` | 标量 | 电商与商品 | 商品退款。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `items.item_refund_in_usd` | `FLOAT64` | 标量 | 电商与商品 | 商品明细子字段。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `items.item_revenue` | `FLOAT64` | 标量 | 电商与商品 | 商品收入。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `items.item_revenue_in_usd` | `FLOAT64` | 标量 | 电商与商品 | 商品明细子字段。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `items.item_variant` | `STRING` | 标量 | 电商与商品 | 商品变体。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `items.location_id` | `STRING` | 标量 | 电商与商品 | 商品明细子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `items.price` | `FLOAT64` | 标量 | 电商与商品 | 商品价格。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `items.price_in_usd` | `FLOAT64` | 标量 | 电商与商品 | 商品美元价格。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `items.promotion_id` | `STRING` | 标量 | 电商与商品 | 促销标识。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `items.promotion_name` | `STRING` | 标量 | 电商与商品 | 促销名称。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `items.quantity` | `INT64` | 标量 | 电商与商品 | 商品数量。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `platform` | `STRING` | 标量 | 平台与流 | 事件平台；当前 H5 表为 WEB。 | 已观察：WEB | 可用于聚合分析；不输出原始值 |
| `privacy_info` | `STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>` | 嵌套结构 | 隐私状态 | Analytics/Ads 存储和临时令牌状态。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `privacy_info.ads_storage` | `STRING` | 标量 | 隐私状态 | 广告存储同意状态。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `privacy_info.analytics_storage` | `STRING` | 标量 | 隐私状态 | Analytics 存储同意状态。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `privacy_info.uses_transient_token` | `STRING` | 标量 | 隐私状态 | 是否使用临时令牌。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `publisher` | `STRUCT<ad_revenue_in_usd FLOAT64, ad_format STRING, ad_source_name STRING, ad_unit_id STRING>` | 嵌套结构 | 广告发布 | 广告发布与广告收入结构。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `publisher.ad_format` | `STRING` | 标量 | 广告发布 | 广告格式。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `publisher.ad_revenue_in_usd` | `FLOAT64` | 标量 | 广告发布 | 广告收入美元值。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `publisher.ad_source_name` | `STRING` | 标量 | 广告发布 | 广告来源名称。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `publisher.ad_unit_id` | `STRING` | 标量 | 广告发布 | 广告单元标识。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `session_traffic_source_last_click` | `STRUCT<manual_campaign STRUCT<campaign_id STRING, campaign_name STRING, source STRING, medium STRING, term STRING, content STRING, source_platform STRING, creative_format STRING, marketing_tactic STRING>, google_ads_campaign STRUCT<customer_id STRING, account_name STRING, campaign_id STRING, campaign_name STRING, ad_group_id STRING, ad_group_name STRING>, cross_channel_campaign STRUCT<campaign_id STRING, campaign_name STRING, source STRING, medium STRING, source_platform STRING, default_channel_group STRING, primary_channel_group STRING>, sa360_campaign STRUCT<campaign_id STRING, campaign_name STRING, source STRING, medium STRING, ad_group_id STRING, ad_group_name STRING, creative_format STRING, engine_account_name STRING, engine_account_type STRING, manager_account_name STRING>, cm360_campaign STRUCT<campaign_id STRING, campaign_name STRING, source STRING, medium STRING, account_id STRING, account_name STRING, advertiser_id STRING, advertiser_name STRING, creative_id STRING, creative_format STRING, creative_name STRING, creative_type STRING, creative_type_id STRING, creative_version STRING, placement_id STRING, placement_cost_structure STRING, placement_name STRING, rendering_id STRING, site_id STRING, site_name STRING>, dv360_campaign STRUCT<campaign_id STRING, campaign_name STRING, source STRING, medium STRING, advertiser_id STRING, advertiser_name STRING, creative_id STRING, creative_format STRING, creative_name STRING, exchange_id STRING, exchange_name STRING, insertion_order_id STRING, insertion_order_name STRING, line_item_id STRING, line_item_name STRING, partner_id STRING, partner_name STRING>>` | 嵌套结构 | 会话归因 | 会话末次点击归因结构。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.cm360_campaign` | `STRUCT<campaign_id STRING, campaign_name STRING, source STRING, medium STRING, account_id STRING, account_name STRING, advertiser_id STRING, advertiser_name STRING, creative_id STRING, creative_format STRING, creative_name STRING, creative_type STRING, creative_type_id STRING, creative_version STRING, placement_id STRING, placement_cost_structure STRING, placement_name STRING, rendering_id STRING, site_id STRING, site_name STRING>` | 嵌套结构 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.cm360_campaign.account_id` | `STRING` | 标量 | 会话归因 | 广告账户/广告组标识。 | schema存在；未输出字段值 | 受限归因标识；仅授权分析 |
| `session_traffic_source_last_click.cm360_campaign.account_name` | `STRING` | 标量 | 会话归因 | 广告账户/广告组名称。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.cm360_campaign.advertiser_id` | `STRING` | 标量 | 会话归因 | 广告账户/广告组标识。 | schema存在；未输出字段值 | 受限归因标识；仅授权分析 |
| `session_traffic_source_last_click.cm360_campaign.advertiser_name` | `STRING` | 标量 | 会话归因 | 广告账户/广告组名称。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.cm360_campaign.campaign_id` | `STRING` | 标量 | 会话归因 | 归因活动 ID。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.cm360_campaign.campaign_name` | `STRING` | 标量 | 会话归因 | 归因活动名称。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.cm360_campaign.creative_format` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.cm360_campaign.creative_id` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 受限归因标识；仅授权分析 |
| `session_traffic_source_last_click.cm360_campaign.creative_name` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.cm360_campaign.creative_type` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |

| `session_traffic_source_last_click.cm360_campaign.creative_type_id` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.cm360_campaign.creative_version` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.cm360_campaign.medium` | `STRING` | 标量 | 会话归因 | 归因媒介。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.cm360_campaign.placement_cost_structure` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.cm360_campaign.placement_id` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 受限归因标识；仅授权分析 |
| `session_traffic_source_last_click.cm360_campaign.placement_name` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.cm360_campaign.rendering_id` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.cm360_campaign.site_id` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.cm360_campaign.site_name` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.cm360_campaign.source` | `STRING` | 标量 | 会话归因 | 归因来源。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.cross_channel_campaign` | `STRUCT<campaign_id STRING, campaign_name STRING, source STRING, medium STRING, source_platform STRING, default_channel_group STRING, primary_channel_group STRING>` | 嵌套结构 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.cross_channel_campaign.campaign_id` | `STRING` | 标量 | 会话归因 | 归因活动 ID。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.cross_channel_campaign.campaign_name` | `STRING` | 标量 | 会话归因 | 归因活动名称。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.cross_channel_campaign.default_channel_group` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.cross_channel_campaign.medium` | `STRING` | 标量 | 会话归因 | 归因媒介。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.cross_channel_campaign.primary_channel_group` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.cross_channel_campaign.source` | `STRING` | 标量 | 会话归因 | 归因来源。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.cross_channel_campaign.source_platform` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.dv360_campaign` | `STRUCT<campaign_id STRING, campaign_name STRING, source STRING, medium STRING, advertiser_id STRING, advertiser_name STRING, creative_id STRING, creative_format STRING, creative_name STRING, exchange_id STRING, exchange_name STRING, insertion_order_id STRING, insertion_order_name STRING, line_item_id STRING, line_item_name STRING, partner_id STRING, partner_name STRING>` | 嵌套结构 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.dv360_campaign.advertiser_id` | `STRING` | 标量 | 会话归因 | 广告账户/广告组标识。 | schema存在；未输出字段值 | 受限归因标识；仅授权分析 |
| `session_traffic_source_last_click.dv360_campaign.advertiser_name` | `STRING` | 标量 | 会话归因 | 广告账户/广告组名称。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.dv360_campaign.campaign_id` | `STRING` | 标量 | 会话归因 | 归因活动 ID。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.dv360_campaign.campaign_name` | `STRING` | 标量 | 会话归因 | 归因活动名称。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.dv360_campaign.creative_format` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.dv360_campaign.creative_id` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 受限归因标识；仅授权分析 |
| `session_traffic_source_last_click.dv360_campaign.creative_name` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.dv360_campaign.exchange_id` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.dv360_campaign.exchange_name` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.dv360_campaign.insertion_order_id` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.dv360_campaign.insertion_order_name` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.dv360_campaign.line_item_id` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `session_traffic_source_last_click.dv360_campaign.line_item_name` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 交易/商业字段；按权限聚合 |
| `session_traffic_source_last_click.dv360_campaign.medium` | `STRING` | 标量 | 会话归因 | 归因媒介。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.dv360_campaign.partner_id` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.dv360_campaign.partner_name` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.dv360_campaign.source` | `STRING` | 标量 | 会话归因 | 归因来源。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.google_ads_campaign` | `STRUCT<customer_id STRING, account_name STRING, campaign_id STRING, campaign_name STRING, ad_group_id STRING, ad_group_name STRING>` | 嵌套结构 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.google_ads_campaign.account_name` | `STRING` | 标量 | 会话归因 | 广告账户/广告组名称。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.google_ads_campaign.ad_group_id` | `STRING` | 标量 | 会话归因 | 广告账户/广告组标识。 | schema存在；未输出字段值 | 受限归因标识；仅授权分析 |
| `session_traffic_source_last_click.google_ads_campaign.ad_group_name` | `STRING` | 标量 | 会话归因 | 广告账户/广告组名称。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.google_ads_campaign.campaign_id` | `STRING` | 标量 | 会话归因 | 归因活动 ID。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.google_ads_campaign.campaign_name` | `STRING` | 标量 | 会话归因 | 归因活动名称。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.google_ads_campaign.customer_id` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.manual_campaign` | `STRUCT<campaign_id STRING, campaign_name STRING, source STRING, medium STRING, term STRING, content STRING, source_platform STRING, creative_format STRING, marketing_tactic STRING>` | 嵌套结构 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.manual_campaign.campaign_id` | `STRING` | 标量 | 会话归因 | 归因活动 ID。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.manual_campaign.campaign_name` | `STRING` | 标量 | 会话归因 | 归因活动名称。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.manual_campaign.content` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.manual_campaign.creative_format` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.manual_campaign.marketing_tactic` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.manual_campaign.medium` | `STRING` | 标量 | 会话归因 | 归因媒介。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.manual_campaign.source` | `STRING` | 标量 | 会话归因 | 归因来源。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.manual_campaign.source_platform` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.manual_campaign.term` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.sa360_campaign` | `STRUCT<campaign_id STRING, campaign_name STRING, source STRING, medium STRING, ad_group_id STRING, ad_group_name STRING, creative_format STRING, engine_account_name STRING, engine_account_type STRING, manager_account_name STRING>` | 嵌套结构 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.sa360_campaign.ad_group_id` | `STRING` | 标量 | 会话归因 | 广告账户/广告组标识。 | schema存在；未输出字段值 | 受限归因标识；仅授权分析 |
| `session_traffic_source_last_click.sa360_campaign.ad_group_name` | `STRING` | 标量 | 会话归因 | 广告账户/广告组名称。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.sa360_campaign.campaign_id` | `STRING` | 标量 | 会话归因 | 归因活动 ID。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.sa360_campaign.campaign_name` | `STRING` | 标量 | 会话归因 | 归因活动名称。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.sa360_campaign.creative_format` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.sa360_campaign.engine_account_name` | `STRING` | 标量 | 会话归因 | 广告账户/广告组名称。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.sa360_campaign.engine_account_type` | `STRING` | 标量 | 会话归因 | 会话末次点击归因子字段。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.sa360_campaign.manager_account_name` | `STRING` | 标量 | 会话归因 | 广告账户/广告组名称。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.sa360_campaign.medium` | `STRING` | 标量 | 会话归因 | 归因媒介。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `session_traffic_source_last_click.sa360_campaign.source` | `STRING` | 标量 | 会话归因 | 归因来源。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `stream_id` | `STRING` | 标量 | 平台与流 | GA4 数据流标识；当前为 H5 Web stream 12134390945。 | 已观察：12134390945 | 可用于聚合分析；不输出原始值 |
| `traffic_source` | `STRUCT<name STRING, medium STRING, source STRING>` | 嵌套结构 | 用户来源 | 用户来源、媒介和名称结构。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `traffic_source.medium` | `STRING` | 标量 | 用户来源 | 首次媒介。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `traffic_source.name` | `STRING` | 标量 | 用户来源 | 首次来源活动或名称。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `traffic_source.source` | `STRING` | 标量 | 用户来源 | 首次来源。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `user_first_touch_timestamp` | `INT64` | 标量 | 用户生命周期 | 用户首次触点时间。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `user_id` | `STRING` | 标量 | 用户标识 | 登录用户业务标识；高敏感，禁止直接输出。 | schema存在；未输出字段值 | 受限标识；禁止直接输出，只做脱敏聚合/对账 |
| `user_ltv` | `STRUCT<revenue FLOAT64, currency STRING>` | 嵌套结构 | 用户生命周期 | GA4 用户生命周期价值结构。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `user_ltv.currency` | `STRING` | 标量 | 用户生命周期 | 生命周期收入货币。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `user_ltv.revenue` | `FLOAT64` | 标量 | 用户生命周期 | 用户生命周期收入。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `user_properties` | `ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>` | 重复数组 | 用户属性 | 用户属性数组。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `user_properties.key` | `STRING` | 标量 | 用户属性 | 用户属性名称。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `user_properties.value` | `STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>` | 嵌套结构 | 用户属性 | 用户属性值容器。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `user_properties.value.double_value` | `FLOAT64` | 标量 | 用户属性 | 用户属性子字段；仅受控聚合使用。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `user_properties.value.float_value` | `FLOAT64` | 标量 | 用户属性 | 用户属性子字段；仅受控聚合使用。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `user_properties.value.int_value` | `INT64` | 标量 | 用户属性 | 用户属性子字段；仅受控聚合使用。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `user_properties.value.set_timestamp_micros` | `INT64` | 标量 | 用户属性 | 属性设置时间。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `user_properties.value.string_value` | `STRING` | 标量 | 用户属性 | 用户属性子字段；仅受控聚合使用。 | schema存在；未输出字段值 | 可用于聚合分析；不输出原始值 |
| `user_pseudo_id` | `STRING` | 标量 | 用户标识 | GA4 伪匿名设备/用户标识；仅允许受控聚合。 | schema存在；未输出字段值 | 受限标识；禁止直接输出，只做脱敏聚合/对账 |



## 4. 最新 H5 事件参数键

| 参数键 | 次数 | 含义 | 状态 |
|---|---:|---|---|
| `page_location` | 159,171 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `ga_session_id` | 159,171 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `batch_page_id` | 159,171 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `ga_session_number` | 159,171 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `batch_ordering_id` | 159,171 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `session_engaged` | 159,171 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `page_title` | 159,143 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `engaged_session_event` | 158,139 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `page_referrer` | 127,760 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `engagement_time_msec` | 121,009 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `ignore_referrer` | 115,191 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `percent_scrolled` | 23,178 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `medium` | 6,847 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `campaign` | 6,847 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `source` | 6,847 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `entrances` | 6,164 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `term` | 5,948 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `gad_source` | 3,944 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `gad_campaignid` | 3,944 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `gclid` | 3,935 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `value` | 3,475 | 参数值容器，按实际类型读取。 | provisional |
| `first_field_type` | 3,354 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `first_field_position` | 3,354 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `form_length` | 3,354 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `form_destination` | 3,349 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `firebase_conversion` | 1,906 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `currency` | 1,170 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `campaign_id` | 108 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |
| `content` | 108 | 事件参数子字段；需结合事件名称和参数键解释。 | provisional |

## 5. 隐私与数据使用边界

- 仅使用字段名、类型、结构和聚合覆盖；不输出 `user_id`、`user_pseudo_id`、交易标识、广告点击标识或任何原始事件值。
- `event_params`、`user_properties` 与 `items` 均为重复结构。展开时必须先确定事件、会话或业务事实粒度，避免行数被重复数组放大。
- `recharge`、`withdraw`、`value`、`ecommerce.*` 只代表埋点行为或 GA4 电商字段；订单成功、资产到账、退款与金额以服务端账务事实为准。

## 6. H5 性能边界

GA4 日表可说明 H5 访问、互动、设备、浏览器、地理与归因行为；它不等同 H5 Web Performance 原始数据。当前未观察到 `web_vitals`、LCP、INP、CLS、FCP、TTFB、页面加载、网络延迟或前端错误事件，因此性能状态仍为 `data_gap`。

## 7. 可复跑与更新

- H5 schema SQL：`analysis/h5_bigquery_schema_inventory_2026_08_24/schema_inventory.sql`
- H5 机器结果：`analysis/h5_bigquery_schema_inventory_2026_08_24/schema_inventory.json`
- H5 运行凭证：`analysis/h5_bigquery_schema_inventory_2026_08_24/run_receipt.json`
- 每日新增 `events_YYYYMMDD` 后，先核验表存在、schema 一致性、`platform=WEB` 与 `stream_id=12134390945`，再刷新字段和参数键覆盖。
