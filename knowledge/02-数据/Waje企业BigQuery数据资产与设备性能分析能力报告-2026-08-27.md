# Waje 企业 BigQuery 数据资产与设备性能分析能力报告

## 执行摘要

- 当前企业账号在 `wajenigeria` 中可见 **14 个数据集、217 个表/视图/外部表和 9,795 条字段路径**。这一结论来自只读元数据查询，不代表数据行、时效或完整性已经通过审计。
- H5 内部网页事件与页面流量汇总可支持浏览器、系统、品牌/型号、页面、版本、停留、退出和资源体积等分层；但目前没有核心网页指标、资源时序、HTTP 响应或前端错误字段，性能结论为 `data_gap`。
- iOS 已出现 5 张 Analytics 日表和 1 张 Firebase Performance 表。Performance schema 可支持网络时延、响应码、轨迹时长、慢帧和冻结帧分析，但表刚创建，实际数据量、连续性和字段填充率尚未验证。
- 当前未发现 Firebase H5、iOS Crashlytics、iOS Messaging 目录下的对象，也未发现 Firebase Android Analytics/Performance 对象。不要把这种“当前目录无对象”写成产品无数据或性能正常。

## 已核验资产

| 项目 | 结果 |
|---|---:|
| 可见数据集 | 14 |
| 表/视图/外部表 | 217 |
| 基础表 / 视图 / 外部表 | 142 / 62 / 13 |
| 字段路径 | 9,795 |
| 真正原生性能表 | 1（iOS） |

## 设备与性能可用性

### H5 网页终端与行为

已发现网页事件和页面流量汇总 schema。可按浏览器、浏览器版本、设备品牌/型号、操作系统、屏幕/视口、页面、事件、版本、来源和日期做聚合分层；`event_duration`、`page_resource_size`、`stay_time`、`exit_count` 可作为体验代理。

边界：这些字段不能替代 LCP、INP、CLS、FCP、TTFB、接口时延、HTTP 响应率或前端错误率。

### iOS Analytics 与原生性能

`waje_ng_firebase_ios` 含 5 张命名为 `events_YYYYMMDD` 的日表，单表 217 条字段路径，可用于版本、系统、设备、地域、归因和行为事件的聚合切片。

`waje_ng_firebase_ios_performance.com_wajegame_wajegame_IOS` 含 30 条字段路径，涵盖版本、设备、系统、运营商、网络类型、事件类型、网络响应码和时序、轨迹时长、慢帧与冻结帧。它是当前唯一已发现的真实性能 schema，但尚需入库质量审计。

### Android 与 Crashlytics

内部起源客户端事件 schema 中有应用版本、包名、设备、系统、运营商、网络和异常原因等字段，可作为受限终端/异常代理；但当前企业库未发现专用 Firebase Android Analytics/Performance 对象，iOS Crashlytics 目录也没有对象。因此 Android 原生性能与正式稳定性专题仍然是缺口。

## 最小落地路线

1. 对 iOS Performance 表做近 7 个完整日的分区、行数、空值、版本、事件类型和网络/轨迹覆盖审计。
2. 完成三个 Android 包的 Firebase Analytics、Performance 与 Crashlytics 导出核验。
3. H5 接入核心网页指标、资源时序、核心接口和前端错误，并产出脱敏聚合表。
4. 建立按日×端×版本×页面/事件的授权聚合视图，再接入 Gemini 的只读 MCP。

## 审计边界

本报告只读取 `wajenigeria` 的 INFORMATION_SCHEMA 元数据；没有读取业务表行、用户/设备标识、订单、支付或日志内容。字段存在不等于已填充、口径正确或质量已达生产可用。
