# Source Inventory

## Coverage

- Coverage level: 页面级基线，覆盖导航结构、数据统计、用户分析、报表集市、埋点管理和主要当前快照。
- Sources checked: 起源平台首页、tracking-web 数据统计页面、用户分析页面、报表集市嵌入报表、数据管理页面。
- Missing high-value lanes: 底层明细表/数仓、SQL、ETL/调度、埋点 SDK 代码、支付/提现原始对账、正式指标文档、报表 owner/权限说明。
- Rejected or lower-confidence candidates: 页面截图中的视觉推断、默认 `No Data` 结果、2023–2024 年未更新的用户分群与字典配置；这些只能作为线索，不能作为当前事实口径。

## Sources

| Source | Type | Locator | Permission Status | Last Checked | Supports | Gaps Or Caveats | Automation Eligible | Update Boundary |
|---|---|---|---|---|---|---|---|---|
| 起源平台登录入口 | Web platform | https://datagrowth.trackares.com/manager/homepage | 可登录；首页提示部分页面无权限 | 2026-08-03 | 产品入口、账号可见范围 | 不保存凭据；首页/业务看板权限不足 | 否 | 仅人工复核 |
| 数据统计 | Web reports | /tracking-web/dataStatistics/* | 可读 | 2026-08-03 | 日活、留存、LTV、ROI、付费、资产、页面、模块、启动、终端 | 底层公式和表不可见 | 否 | 仅人工复核；保留页面快照 |
| 用户分析 | Web analysis | /tracking-web/users/analyze/* | 可读 | 2026-08-03 | 预警、分群、用户轨迹 | 分群数据明显过期；预警为空 | 否 | 仅人工复核；不自动写入 |
| 报表集市 | Embedded dashboards | /tracking-web/iframe/* + shareDashboard iframe | 可读部分报表 | 2026-08-03 | 70 个报表条目、运营周报、TC、游戏、增长和经济指标 | `BQ-` 为 BigQuery 新引擎版本；非 BQ 旧版本将逐步废弃；部分默认 `No Data` | 否 | 仅人工复核；不改外部报表 |
| GM 用户/资料库 | GM admin | https://auth.wgame2025.com/if/user/#/library | 入口已确认 | 2026-08-06 | 用户/账号资料及后台管理能力 | 可见模块依账号权限而定 | 否 | 仅人工复核；不改外部配置 |
| GM Lifecycle Pool V2 | GM lifecycle/RTP | https://prod-ac.waje-special.com:8443/sys/dynamic/lifecyclev2/pool | 当前独立查询；规划整合至起源平台 | 2026-08-06 | 生命周期池、游戏 RTP、基础真实回报比、实时/历史查询 | `Lifecycle Pool`、`v2`、`v2 (Joint)` 需按自研/联运范围区分；整合前需完成口径、映射、权限和 7–14 天并行核对 | 否 | 仅人工复核；记录查询口径 |
| 数据质量 | Web quality report | /tracking-web/burying/buryingPoint/dataQuality | 可读 | 2026-08-03 | 接收、入库、异常、抛弃、事件级异常 | 只覆盖页面展示窗口；无历史趋势接口 | 否 | 仅人工复核；异常先提案 |
| 埋点管理 | Metadata console | /tracking-web/burying/* | 可读大部分字典 | 2026-08-03 | 元事件、虚拟事件、用户/事件属性、页面/模块/参数、汇率 | 部分页面默认无数据；定义更新时间不一 | 否 | 不自动改字典 |
| 项目现有知识库 | Local files | knowledge/02-数据/* | 可读写 | 2026-08-03 | 既有数据平台和埋点上下文 | 多为 seed，需要平台实测校准 | 是（本地） | 只更新项目资料，不改外部平台 |

## Source Precedence

1. 底层事实表、ETL、测试和正式指标文档（当前未提供）。
2. 数据质量、元事件、属性和页面/模块字典等平台定义页面。
3. 数据统计明细和可验证的报表集市明细。
4. 页面截图、默认筛选和当前快照推断。

## Recheck Triggers

- 数据统计页面更新时间发生变化或默认日期跨过新日。
- GAMEEND 异常率、ROI NaN、LTV30=0 等问题被修复或发生变化。
- 用户分群、事件属性、页面/模块字典更新时间更新。
- BQ 与非 BQ 报表的刷新延迟、迁移负责人、口径差异或下线时间发生变化。
