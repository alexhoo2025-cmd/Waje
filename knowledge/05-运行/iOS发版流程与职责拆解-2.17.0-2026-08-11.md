---
type: process_inventory
domain: release-management
platform: ios
product: Waje Game
source_platform: lark
source_title: IOS发版流程
source_version: 2.17.0
source_url: https://ksg964l11fam.sg.larksuite.com/wiki/S2YHwWu89iSCUPkl2uxlGccHgMh?fromScene=spaceOverview&sheet=XVCbmC
accessed: 2026-08-11
status: ingested
owner: analyst
tags: [waje-game, ios, release, app-store, testflight, testing, configuration]
---

# iOS 发版流程与职责拆解（2.17.0）

## 文档定位与边界

本条目将飞书《IOS发版流程》中选中的 **2.17.0** 页签整理为 iOS 发版基线。该工作簿同时维护 2.11.2 至 2.16.0 等历史页签，且当前页内仍可见 2.14.0、2.10.37 等历史备注；实际执行必须使用当期的版本号、构建号、变更单和审批记录覆盖历史示例。

- 原始流程：[IOS发版流程（飞书）](https://ksg964l11fam.sg.larksuite.com/wiki/S2YHwWu89iSCUPkl2uxlGccHgMh?fromScene=spaceOverview&sheet=XVCbmC)
- Android 对照：[[05-运行/Android发版流程与职责拆解-2.17.0-2026-08-11]]
- 关联资料：[[02-数据/发版报告资料入库-2026-08-04]]、[[01-产品/WajeGame PRD分级规范-试运行版v1.0-2026-08-04]]

> 原表提示：提审时间尽量安排在周一至周三。该提示作为排期参考，不替代当期商店审核窗口与业务发布决策。

## 一、iOS 端到端流程

```mermaid
flowchart LR
  A[发布输入确认\n分支、资源、配置、文案] --> B[TestRelease 包\n测试服与旧包兼容]
  B --> C[提审服配置\n屏蔽项、GPS/IP、提现]
  C --> D[Apple 提审\n送审通知与 TestFlight 回归]
  D --> E[审核通过\n更新策略、切线上、服务发布]
  E --> F[App Store 回归\nGrafana 追踪与奖励配置]
```

| 阶段 | 关键动作 | 放行条件 / 输出 | 主负责人 |
|---|---|---|---|
| 1. 发布输入确认 | 确认客户端/服务端分支、美术资源、数值与公告、英文文案和 Icon | 本版本发布内容与环境配置确认 | Kirito、Brooks、yxlmwei、Fcaptain、dora |
| 2. 测试服与预发 | 打 `testRelease` 包，完成兼容、功能、旧包、热更/强更及增量包测试 | QA checklist、线上一周活跃版本清单、兼容结论 | Kirito、James |
| 3. 提审服验证 | 更新提审服；配置提审状态；验证当前/旧包、提审服配置与 Release 底包 | 提审环境和回归结果 | Brooks、vito / Vito、Fcaptain、James |
| 4. Apple 提审与 TestFlight | 送审通过后通知测试；从 TestFlight 下载 Release 包连接提审服回归 | TestFlight 回归记录、提审状态确认 | Fcaptain、James |
| 5. 正式发布 | 确定热更/强更；提审后切线上；服务兼容处理和更新 | 线上服务、Release 包和配置同步发布 | Fcaptain、Brooks、Kirito |
| 6. 发布后验证 | 苹果商店最新包回归、热更/强更验证、Grafana 追踪、热更奖励配置 | 发布后验收与监控结论 | James、产品/服务器、Fcaptain |

## 二、详细执行清单

### 1. 测试服与 TestRelease

| 编号 | 任务 | 验收要点 | 负责人 |
|---|---|---|---|
| 1 | 测试服确认 | 客户端/服务端分支、美术资源、数值及更新公告、英文文案与 Icon 和当期需求一致 | Kirito / Brooks / yxlmwei / Fcaptain / dora |
| 2 | 打 `testRelease` 包 | 使用线上配置和功能；按要求走热更/强更测试路径；连接测试服；更新小游戏 | Kirito |
| 3 | 兼容性测试（小版本不提审时） | 覆盖技术提供的兼容版本；评估是否需要苹果提审 | James |
| 4 | 功能、活跃版本与测试服更新测试 | 执行 checklist；提供线上一周活跃版本；下载旧包验证热更/强更 | James |
| 5 | 提审服更新与配置 | 更新提审服至当期内容；配置 Apollo、更新公告和数值配置，并切为提审状态 | Brooks / vito |
| 6 | 当前/老包兼容测试 | 在 `testRelease` 环境使用上一版本包验证新服务；开关无法兼容时配置强制热更新 | James |
| 7 | `testRelease` 非提审状态与增量包检查 | 确认包连接提审服但处于非提审状态；检查插包/增量内容大小 | Fcaptain / Kirito |
| 8 | `testRelease` 底包全量回归 | 本次内容、既有功能及 checklist 全量回归；按上线要求测热更/强更 | James |

### 2. Release 构建与提审环境

| 编号 | 任务 | 验收要点 | 负责人 |
|---|---|---|---|
| 9 | 合并 Release 并打最终包 | 分支、版本号、构建号、包体与当期变更可追溯 | Kirito |
| 10 | 发布热更、H5 与子游戏更新（按需） | 明确需同步的热更版本、H5 内容与子游戏更新 | Kirito |
| 11 | Release 包提审状态与底包测试 | 提审包屏蔽项生效；提审服中的强更/热更策略遵循当期要求 | Fcaptain / James |
| 12 | 提审服 GPS/IP/提现配置 | 提审服开启 GPS、关闭 IP 限制并关闭提现；测试确认实际状态 | Fcaptain / Vito / James |
| 13 | 送审与 TestFlight 测试 | 送审通过后通知测试；TestFlight 下载 Release 包，连接提审服回归 | Fcaptain / James |

### 3. 审核通过与生产发布

| 编号 | 任务 | 验收要点 | 负责人 |
|---|---|---|---|
| 14 | 确定更新策略 | 明确本次使用热更或强更及对应配置 | Fcaptain |
| 15 | Release 包连线上与线上回归 | 提审后服务切至线上；从 TestFlight 包验证游戏与正式账号登录 | Fcaptain / James |
| 16 | 服务兼容与发布 | 不兼容时先处理线上数据兼容；兼容则直接更新，不兼容则停服维护；与策划确认后发布 | Brooks |
| 17 | Grafana 数据追踪 | 关注各项指标是否符合预期 | 产品、服务器 |
| 18 | 提审后配置上线 | 核验 Apollo、运营后台、公告、弹窗队列与维护信；服务发布后再按计划放开新版本配置 | Fcaptain |

### 4. App Store 验证与发布后收尾

| 编号 | 任务 | 验收要点 | 负责人 |
|---|---|---|---|
| 19 | 顾虑发布 | 在前置验证及运营条件满足时执行发布 | Kirito |
| 20 | 苹果商店最新包测试 | 从苹果商店下载最新包，执行功能回归 | James |
| 21 | 活跃版本与更新测试 | 提供线上一周活跃版本，验证热更/强更策略 | James |
| 22 | 热更奖励配置 | 按批准规则完成热更奖励配置并核验 | James（源表记录） |

## 三、人员职责地图

| 人员 / 角色 | 负责模块 | 核心职责 |
|---|---|---|
| **Kirito** | iOS 客户端构建与发布 | 客户端分支确认；`testRelease`/Release 包构建与分支合并；发布热更；确认 H5、子游戏同步更新；执行发布。 |
| **James** | iOS QA 与发布验收 | 兼容性、功能回归、旧包/活跃版本、热更/强更、提审环境、TestFlight、App Store 最新包、GPS/IP 和正式账号验证；维护 checklist。 |
| **Brooks** | 服务端发布与兼容 | 服务端分支确认；提审服更新；线上数据兼容处理、服务更新和停服维护。 |
| **Fcaptain** | 环境、配置与发布控制 | 测试服配置确认；提审/线上状态切换；GPS/IP/提现、更新策略、Apollo/运营后台/公告/弹窗/维护信和配置上线。 |
| **vito / Vito** | 提审配置 | 提审服配置、数值和公告配置，以及城市 IP 限制相关配置。 |
| **yxlmwei** | 美术资源 | 本版本美术资源确认。 |
| **dora** | 运营文案验收 | 英文文案、Icon 等运营内容与需求一致性确认。 |
| **产品、服务器** | 发布后监控 | 跟踪 Grafana 指标是否符合预期。 |

## 四、与 Android 流程的差异

| 维度 | iOS | Android |
|---|---|---|
| 商店验收 | TestFlight 回归后，再从苹果商店下载最新包验证 | Google Play 提交与商店最新包验证 |
| 提审排期 | 源表建议尽量安排在周一至周三 | 原表未记录同类排期建议 |
| 预发验证 | 明确 TestFlight 下载 Release 包并连接提审服 | 以 Release 包、提审服和 Google Play 为主 |
| 渠道包 | 当前 iOS 原表未列出渠道 CDN 刷新和多渠道包回归 | 明确 opay、palm、xender、whotgame 等渠道包 CDN 与回归 |
| 发布后奖励 | 原表列 James 负责热更奖励配置，需与配置权限确认 | 原表列 Fcaptain 负责热更奖励配置 |

## 五、关键控制点与优化建议

### 必须留存的放行证据

1. **构建可追溯**：版本号、iOS build number、代码 commit、包 hash、TestFlight build、商店提交记录必须关联到同一变更单。
2. **提审与线上隔离**：提审服/线上服的连接目标、功能屏蔽、GPS/IP、提现与支付相关配置要记录旧值、新值、执行人和回滚步骤。
3. **旧包兼容结论**：以线上一周活跃版本为测试基线；每个不兼容包必须明确功能开关或强制更新策略。
4. **生产发布顺序**：服务兼容处理完成后，才能同步放开新版本配置；TestFlight 与 App Store 包都应有独立回归结论。
5. **发布后可观测**：预设版本分布、启动/登录/游戏进入、更新成功、Crash/ANR、接口超时、支付/提现成功率等指标的阈值、告警人与观察窗口。

### 当前流程需补齐项

| 缺口 | 建议 |
|---|---|
| 主负责人之外没有审批和协作边界 | 每个版本单补 RACI、最终放行人、替补人和关键配置双人复核。 |
| 历史版本备注残留在 2.17.0 页签 | 每次从模板复制后清除旧版本号、旧服务器分支和旧包大小，避免误执行。 |
| 提审与线上配置未见统一差异清单 | 建立 iOS Release Manifest，列出 TestFlight build、App Store build、环境、配置 diff、回滚包和证据链接。 |
| 热更奖励负责人跨端不一致 | 明确奖励配置的系统权限拥有者、审批人和 QA 验证人；不要仅以原表单一负责人代替审批链。 |
| Grafana 只写“关注指标” | 将监控项、阈值、异常处理时限与发布后验收结论固化在发布单。 |

## 六、需人工确认的源表问题

1. 当前选中页签为 2.17.0，但备注中仍有“客户端版本 2.14.0”“本次为 2.10.37”等历史信息；发布前必须更新。
2. “release 包非提审状态”任务与事件描述中的环境表述存在歧义，应补充“包连接哪个服务、服务处于什么状态”的标准写法。
3. iOS 流程的支付备注中出现 Google Pay 相关历史说明，需由产品、客户端和合规确认是否仍适用，避免将历史审核策略直接复用。
4. 热更奖励配置由 James 负责的记录，与 Android 流程由 Fcaptain 负责的记录不同；需明确实际操作权限和审批责任。
5. 审核环境功能屏蔽、GPS/IP、提现与支付相关设置为版本化敏感配置，只能按当前需求及审批执行，不能作为默认配置照搬。

## 七、建议的单版本交付物

- [ ] `CHG-YYYY-NNNN` 变更单与发布范围
- [ ] iOS Release Manifest（版本、build number、commit、包 hash、TestFlight、App Store、环境、配置 diff、回滚）
- [ ] 兼容性矩阵（当前包、旧包、活跃版本）与 QA checklist
- [ ] 提审/线上配置双人核验及回滚记录
- [ ] TestFlight、App Store 最新包及正式账号回归证据
- [ ] 发布后 Grafana 监控、异常处置及热更奖励记录

