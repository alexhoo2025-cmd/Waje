---
type: configuration-checklist
domain: firebase-bigquery
status: blocked_authentication
updated: 2026-08-21
project: waje-special
target: waje-analytics-readonly
---

# Waje Android Firebase → BigQuery Sandbox 导入配置清单

## 当前状态

| 检查项 | 结果 | 说明 |
|---|---|---|
| Firebase 项目 | `waje-special` | 活动项目已核对 |
| Billing | 未开启 | 本清单不升级 Blaze、不绑定企业 Billing |
| 覆盖范围 | 3 个 Android 生产包 | 主包、传音老包、传音新包 |
| SDK 配置 | 可读取 | App ID 与包名映射以注册表为准；配置可读不等于每项 SDK 已初始化 |
| Crashlytics | 三包均有真实事件 | 可继续做聚合审计 |
| Performance | 主包/老包有轨迹；新包为 `data_gap` | 新包无数据不能解释为性能正常 |
| 企业 BigQuery `wajenigeria` | `blocked_authentication` | 只读连接认证缺失，未假设数据集、表或新鲜度 |
| Sandbox 目标 | `waje-analytics-readonly` | 需由有权限的 Firebase/Google Cloud 管理员人工配置 |

## 人工配置步骤

1. 登录 Firebase Console，确认项目为 `waje-special`。
2. 进入 Project settings → Integrations → BigQuery，选择 Sandbox 目标项目 `waje-analytics-readonly`。
3. 区域保持 US；不要创建个人 Cloud Billing 或免费试用账单。
4. 在 Performance Monitoring 导出配置中只选择三个 Android App：
   - `com.hfhy.waje.special`
   - `com.hfhy.wajecasino.palmgame`
   - `com.hfhy.wajecasino.game`
5. 保持每日同步；不把新包的无数据状态改写为“正常”。
6. 配置后等待首次传播，最长按约 48 小时观察；允许的历史回补不超过近 30 天。
7. 在 BigQuery 中确认实际生成的数据集和表名后，再使用只读审计 SQL；不要根据预期名称直接写查询或建表。

## 权限清单

- Firebase Owner 或 Firebase Admin：查看/管理 Firebase 与 BigQuery 集成。
- 目标 GCP 项目 Owner，或等价的项目查看、IAM 检查、服务启用和 BigQuery 配置权限。
- BigQuery API 已启用。
- 如控制台返回 Google 创建的服务代理或服务账号缺少权限，只记录错误中的主体与缺失角色，先由项目管理员最小授权；不自行扩大权限。

## 留存与风险

- Sandbox 表、视图和分区默认受 60 天过期限制；不适合作为长期企业事实层。
- Firebase Performance 导出无数据时，依次排查 App 选择、版本/时间窗口、SDK 初始化、采集开关、处理延迟和权限；不得统一解释为“没有异常”。
- Firebase Performance 只覆盖 App 端性能；H5 Web Performance、Web Vitals、白屏和 JS 错误不由本清单补齐。
- 本清单不修改 Firebase 配置、Remote Config、Crashlytics Issue、个人 Performance 面板或企业 Billing。

## 验收清单

- [ ] 三个 Android App 均被选中，未混入 iOS/H5。
- [ ] 配置页面显示每日同步，无意外事件过滤。
- [ ] 首个导出数据集/表出现后记录实际名称、区域、创建时间和字段结构。
- [ ] 最近稳定日期存在数据，且连续日期无异常断档。
- [ ] 每包/版本覆盖与 Crashlytics/发版记录能够对应。
- [ ] 导出审计结果只保留元数据和聚合结果，不落盘用户/设备标识或原始事件行。

## 相关材料

- [Android Firebase 接入与数据现状审计](./Waje%20Android%20Firebase接入与数据现状审计-2026-08-21.md)
- [Firebase Performance 导出到 BigQuery](https://firebase.google.com/docs/perf-mon/bigquery-export)
- [Firebase 数据导出到 BigQuery](https://firebase.google.com/docs/projects/bigquery-export)
- [BigQuery Sandbox](https://cloud.google.com/bigquery/docs/sandbox)
