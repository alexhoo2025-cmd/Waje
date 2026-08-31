---
type: metabase_schema_dictionary
date: 2026-08-26
schema: ApolloConfigDB
status: observed_metadata
source_engine: mysql_style_information_schema_export
---

# Metabase 数据字典｜ApolloConfigDB

> 证据边界：本分册来自可见 `information_schema` 定义。字段值、默认值、连接参数、敏感字段原文均未保存；字段用途和数据层标记中“命名推断”均需由业务 Owner 或数据开发补证。

## 1. Schema 概览

- 表：**17** 张；字段：**180** 个。
- 数据层：配置元数据（命名推断）。
- 外键、分区、索引明细、行数、更新时刻、保留周期：本次未导出，不能推断。

## 2. 表清单

| 表 | 类型 | 字段数 | 业务域（命名推断） | 受控字段候选数 | 表说明 |
|---|---|---:|---|---:|---|
| `AccessKey` | BASE TABLE | 10 | 配置 / 平台 | 1 | 访问密钥 |
| `App` | BASE TABLE | 13 | 配置 / 平台 | 1 | 应用表 |
| `AppNamespace` | BASE TABLE | 12 | 配置 / 平台 | 0 | 应用namespace定义 |
| `Audit` | BASE TABLE | 11 | 日志 / 数据质量 | 0 | 日志审计表 |
| `Cluster` | BASE TABLE | 10 | 配置 / 平台 | 0 | 集群 |
| `Commit` | BASE TABLE | 12 | 配置 / 平台 | 0 | commit 历史表 |
| `GrayReleaseRule` | BASE TABLE | 14 | 配置 / 平台 | 0 | 灰度规则表 |
| `Instance` | BASE TABLE | 7 | 配置 / 平台 | 0 | 使用配置的应用实例 |
| `InstanceConfig` | BASE TABLE | 9 | 配置 / 平台 | 0 | 应用实例的配置信息 |
| `Item` | BASE TABLE | 13 | 配置 / 平台 | 0 | 配置项目 |
| `Namespace` | BASE TABLE | 10 | 配置 / 平台 | 0 | 命名空间 |
| `NamespaceLock` | BASE TABLE | 8 | 配置 / 平台 | 0 | namespace的编辑锁 |
| `Release` | BASE TABLE | 15 | 配置 / 平台 | 0 | 发布 |
| `ReleaseHistory` | BASE TABLE | 15 | 配置 / 平台 | 0 | 发布历史 |
| `ReleaseMessage` | BASE TABLE | 3 | 运营 / 消息 | 0 | 发布消息 |
| `ServerConfig` | BASE TABLE | 11 | 配置 / 平台 | 0 | 配置服务自身配置 |
| `ServiceRegistry` | BASE TABLE | 7 | 配置 / 平台 | 0 | 注册中心 |

## 3. 逐表字段定义

### AccessKey

- 表类型：`BASE TABLE`；字段数：10；数据层：配置元数据（命名推断）。
- 业务域：配置 / 平台（`inferred_name_only`）；建议：配置、版本、字典和开关关联；不作为主统计事实源。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 自增主键 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `AppId` | `varchar(64)` | NO | `MUL` | 业务属性 | AppID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | [REDACTED:CREDENTIAL_OR_SECRET] | `varchar(128)` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 禁止展示、导出或进入分析产物 |
| 4 | `IsEnabled` | `bit(1)` | NO | `NONE` | 业务属性 | 1: enabled, 0: disabled | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `IsDeleted` | `bit(1)` | NO | `NONE` | 业务属性 | 1: deleted, 0: normal | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `DeletedAt` | `bigint` | NO | `NONE` | 时间 | Delete timestamp based on milliseconds | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `DataChange_CreatedBy` | `varchar(64)` | NO | `NONE` | 时间 | 创建人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `DataChange_LastModifiedBy` | `varchar(64)` | YES | `NONE` | 时间 | 最后修改人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `DataChange_LastTime` | `timestamp` | NO | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### App

- 表类型：`BASE TABLE`；字段数：13；数据层：配置元数据（命名推断）。
- 业务域：配置 / 平台（`inferred_name_only`）；建议：配置、版本、字典和开关关联；不作为主统计事实源。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 主键 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `AppId` | `varchar(64)` | NO | `MUL` | 业务属性 | AppID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `Name` | `varchar(500)` | NO | `MUL` | 业务属性 | 应用名 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `OrgId` | `varchar(32)` | NO | `NONE` | 业务属性 | 部门Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `OrgName` | `varchar(64)` | NO | `NONE` | 业务属性 | 部门名字 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `OwnerName` | `varchar(500)` | NO | `NONE` | 业务属性 | ownerName | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `varchar(500)` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 8 | `IsDeleted` | `bit(1)` | NO | `NONE` | 业务属性 | 1: deleted, 0: normal | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `DeletedAt` | `bigint` | NO | `NONE` | 时间 | Delete timestamp based on milliseconds | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `DataChange_CreatedBy` | `varchar(64)` | NO | `NONE` | 时间 | 创建人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `DataChange_LastModifiedBy` | `varchar(64)` | YES | `NONE` | 时间 | 最后修改人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `DataChange_LastTime` | `timestamp` | YES | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### AppNamespace

- 表类型：`BASE TABLE`；字段数：12；数据层：配置元数据（命名推断）。
- 业务域：配置 / 平台（`inferred_name_only`）；建议：配置、版本、字典和开关关联；不作为主统计事实源。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 自增主键 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `Name` | `varchar(32)` | NO | `MUL` | 业务属性 | namespace名字，注意，需要全局唯一 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `AppId` | `varchar(64)` | NO | `MUL` | 业务属性 | app id | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `Format` | `varchar(32)` | NO | `NONE` | 时间 | namespace的format类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `IsPublic` | `bit(1)` | NO | `NONE` | 业务属性 | namespace是否为公共 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `Comment` | `varchar(64)` | NO | `NONE` | 业务属性 | 注释 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `IsDeleted` | `bit(1)` | NO | `NONE` | 业务属性 | 1: deleted, 0: normal | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `DeletedAt` | `bigint` | NO | `NONE` | 时间 | Delete timestamp based on milliseconds | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `DataChange_CreatedBy` | `varchar(64)` | NO | `NONE` | 时间 | 创建人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `DataChange_LastModifiedBy` | `varchar(64)` | YES | `NONE` | 时间 | 最后修改人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `DataChange_LastTime` | `timestamp` | YES | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### Audit

- 表类型：`BASE TABLE`；字段数：11；数据层：配置元数据（命名推断）。
- 业务域：日志 / 数据质量（`inferred_name_only`）；建议：入库延迟、错误、重试和数据质量排障；需明确日志保留周期。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 主键 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `EntityName` | `varchar(50)` | NO | `NONE` | 业务属性 | 表名 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `EntityId` | `int unsigned` | YES | `NONE` | 业务属性 | 记录ID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `OpName` | `varchar(50)` | NO | `NONE` | 业务属性 | 操作类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `Comment` | `varchar(500)` | YES | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `IsDeleted` | `bit(1)` | NO | `NONE` | 业务属性 | 1: deleted, 0: normal | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `DeletedAt` | `bigint` | NO | `NONE` | 时间 | Delete timestamp based on milliseconds | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `DataChange_CreatedBy` | `varchar(64)` | NO | `NONE` | 时间 | 创建人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `DataChange_LastModifiedBy` | `varchar(64)` | YES | `NONE` | 时间 | 最后修改人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `DataChange_LastTime` | `timestamp` | YES | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### Cluster

- 表类型：`BASE TABLE`；字段数：10；数据层：配置元数据（命名推断）。
- 业务域：配置 / 平台（`inferred_name_only`）；建议：配置、版本、字典和开关关联；不作为主统计事实源。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 自增主键 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `Name` | `varchar(32)` | NO | `NONE` | 业务属性 | 集群名字 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `AppId` | `varchar(64)` | NO | `MUL` | 业务属性 | App id | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `ParentClusterId` | `int unsigned` | NO | `MUL` | 业务属性 | 父cluster | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `IsDeleted` | `bit(1)` | NO | `NONE` | 业务属性 | 1: deleted, 0: normal | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `DeletedAt` | `bigint` | NO | `NONE` | 时间 | Delete timestamp based on milliseconds | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `DataChange_CreatedBy` | `varchar(64)` | NO | `NONE` | 时间 | 创建人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `DataChange_LastModifiedBy` | `varchar(64)` | YES | `NONE` | 时间 | 最后修改人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `DataChange_LastTime` | `timestamp` | YES | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### Commit

- 表类型：`BASE TABLE`；字段数：12；数据层：配置元数据（命名推断）。
- 业务域：配置 / 平台（`inferred_name_only`）；建议：配置、版本、字典和开关关联；不作为主统计事实源。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 主键 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `ChangeSets` | `longtext` | NO | `NONE` | 业务属性 | 修改变更集 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `AppId` | `varchar(64)` | NO | `MUL` | 业务属性 | AppID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `ClusterName` | `varchar(500)` | NO | `MUL` | 业务属性 | ClusterName | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `NamespaceName` | `varchar(500)` | NO | `MUL` | 业务属性 | namespaceName | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `Comment` | `varchar(500)` | YES | `NONE` | 业务属性 | 备注 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `IsDeleted` | `bit(1)` | NO | `NONE` | 业务属性 | 1: deleted, 0: normal | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `DeletedAt` | `bigint` | NO | `NONE` | 时间 | Delete timestamp based on milliseconds | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `DataChange_CreatedBy` | `varchar(64)` | NO | `NONE` | 时间 | 创建人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `DataChange_LastModifiedBy` | `varchar(64)` | YES | `NONE` | 时间 | 最后修改人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `DataChange_LastTime` | `timestamp` | YES | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### GrayReleaseRule

- 表类型：`BASE TABLE`；字段数：14；数据层：配置元数据（命名推断）。
- 业务域：配置 / 平台（`inferred_name_only`）；建议：配置、版本、字典和开关关联；不作为主统计事实源。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 主键 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `AppId` | `varchar(64)` | NO | `MUL` | 业务属性 | AppID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `ClusterName` | `varchar(32)` | NO | `NONE` | 业务属性 | Cluster Name | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `NamespaceName` | `varchar(32)` | NO | `NONE` | 业务属性 | Namespace Name | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `BranchName` | `varchar(32)` | NO | `NONE` | 业务属性 | branch name | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `Rules` | `varchar(16000)` | YES | `NONE` | 业务属性 | 灰度规则 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `ReleaseId` | `int unsigned` | NO | `NONE` | 业务属性 | 灰度对应的release | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `BranchStatus` | `tinyint` | YES | `NONE` | 时间 | 灰度分支状态: 0:删除分支,1:正在使用的规则 2：全量发布 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `IsDeleted` | `bit(1)` | NO | `NONE` | 业务属性 | 1: deleted, 0: normal | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `DeletedAt` | `bigint` | NO | `NONE` | 时间 | Delete timestamp based on milliseconds | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `DataChange_CreatedBy` | `varchar(64)` | NO | `NONE` | 时间 | 创建人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `DataChange_LastModifiedBy` | `varchar(64)` | YES | `NONE` | 时间 | 最后修改人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `DataChange_LastTime` | `timestamp` | YES | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### Instance

- 表类型：`BASE TABLE`；字段数：7；数据层：配置元数据（命名推断）。
- 业务域：配置 / 平台（`inferred_name_only`）；建议：配置、版本、字典和开关关联；不作为主统计事实源。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 自增Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `AppId` | `varchar(64)` | NO | `MUL` | 业务属性 | AppID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `ClusterName` | `varchar(32)` | NO | `NONE` | 业务属性 | ClusterName | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `DataCenter` | `varchar(64)` | NO | `NONE` | 时间 | Data Center Name | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `Ip` | `varchar(32)` | NO | `MUL` | 业务属性 | instance ip | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `DataChange_LastTime` | `timestamp` | NO | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### InstanceConfig

- 表类型：`BASE TABLE`；字段数：9；数据层：配置元数据（命名推断）。
- 业务域：配置 / 平台（`inferred_name_only`）；建议：配置、版本、字典和开关关联；不作为主统计事实源。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 自增Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `InstanceId` | `int unsigned` | YES | `MUL` | 业务属性 | Instance Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `ConfigAppId` | `varchar(64)` | NO | `MUL` | 业务属性 | Config App Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `ConfigClusterName` | `varchar(32)` | NO | `NONE` | 业务属性 | Config Cluster Name | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `ConfigNamespaceName` | `varchar(32)` | NO | `NONE` | 业务属性 | Config Namespace Name | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `ReleaseKey` | `varchar(64)` | NO | `MUL` | 业务属性 | 发布的Key | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `ReleaseDeliveryTime` | `timestamp` | YES | `NONE` | 时间 | 配置获取时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `DataChange_LastTime` | `timestamp` | NO | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### Item

- 表类型：`BASE TABLE`；字段数：13；数据层：配置元数据（命名推断）。
- 业务域：配置 / 平台（`inferred_name_only`）；建议：配置、版本、字典和开关关联；不作为主统计事实源。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 自增Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `NamespaceId` | `int unsigned` | NO | `MUL` | 业务属性 | 集群NamespaceId | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `Key` | `varchar(128)` | NO | `NONE` | 业务属性 | 配置项Key | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `Type` | `tinyint unsigned` | NO | `NONE` | 状态 / 枚举 | 配置项类型，0: String，1: Number，2: Boolean，3: JSON | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `Value` | `longtext` | NO | `NONE` | 业务属性 | 配置项值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `Comment` | `varchar(1024)` | YES | `NONE` | 业务属性 | 注释 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `LineNum` | `int unsigned` | YES | `NONE` | 业务属性 | 行号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `IsDeleted` | `bit(1)` | NO | `NONE` | 业务属性 | 1: deleted, 0: normal | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `DeletedAt` | `bigint` | NO | `NONE` | 时间 | Delete timestamp based on milliseconds | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `DataChange_CreatedBy` | `varchar(64)` | NO | `NONE` | 时间 | 创建人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `DataChange_LastModifiedBy` | `varchar(64)` | YES | `NONE` | 时间 | 最后修改人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `DataChange_LastTime` | `timestamp` | YES | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### Namespace

- 表类型：`BASE TABLE`；字段数：10；数据层：配置元数据（命名推断）。
- 业务域：配置 / 平台（`inferred_name_only`）；建议：配置、版本、字典和开关关联；不作为主统计事实源。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 自增主键 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `AppId` | `varchar(64)` | NO | `MUL` | 业务属性 | AppID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `ClusterName` | `varchar(500)` | NO | `NONE` | 业务属性 | Cluster Name | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `NamespaceName` | `varchar(500)` | NO | `MUL` | 业务属性 | Namespace Name | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `IsDeleted` | `bit(1)` | NO | `NONE` | 业务属性 | 1: deleted, 0: normal | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `DeletedAt` | `bigint` | NO | `NONE` | 时间 | Delete timestamp based on milliseconds | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `DataChange_CreatedBy` | `varchar(64)` | NO | `NONE` | 时间 | 创建人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `DataChange_LastModifiedBy` | `varchar(64)` | YES | `NONE` | 时间 | 最后修改人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `DataChange_LastTime` | `timestamp` | YES | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### NamespaceLock

- 表类型：`BASE TABLE`；字段数：8；数据层：配置元数据（命名推断）。
- 业务域：配置 / 平台（`inferred_name_only`）；建议：配置、版本、字典和开关关联；不作为主统计事实源。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 自增id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `NamespaceId` | `int unsigned` | NO | `MUL` | 业务属性 | 集群NamespaceId | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `DataChange_CreatedBy` | `varchar(64)` | NO | `NONE` | 时间 | 创建人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `DataChange_LastModifiedBy` | `varchar(64)` | YES | `NONE` | 时间 | 最后修改人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `DataChange_LastTime` | `timestamp` | YES | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `IsDeleted` | `bit(1)` | YES | `NONE` | 业务属性 | 软删除 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `DeletedAt` | `bigint` | NO | `NONE` | 时间 | Delete timestamp based on milliseconds | 允许在授权范围内做聚合分析；不输出字段值 |

### Release

- 表类型：`BASE TABLE`；字段数：15；数据层：配置元数据（命名推断）。
- 业务域：配置 / 平台（`inferred_name_only`）；建议：配置、版本、字典和开关关联；不作为主统计事实源。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 自增主键 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `ReleaseKey` | `varchar(64)` | NO | `MUL` | 业务属性 | 发布的Key | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `Name` | `varchar(64)` | NO | `NONE` | 业务属性 | 发布名字 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `Comment` | `varchar(256)` | YES | `NONE` | 业务属性 | 发布说明 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `AppId` | `varchar(64)` | NO | `MUL` | 业务属性 | AppID | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `ClusterName` | `varchar(500)` | NO | `NONE` | 业务属性 | ClusterName | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `NamespaceName` | `varchar(500)` | NO | `NONE` | 业务属性 | namespaceName | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `Configurations` | `longtext` | NO | `NONE` | 时间 | 发布配置 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `IsAbandoned` | `bit(1)` | NO | `NONE` | 业务属性 | 是否废弃 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `IsDeleted` | `bit(1)` | NO | `NONE` | 业务属性 | 1: deleted, 0: normal | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `DeletedAt` | `bigint` | NO | `NONE` | 时间 | Delete timestamp based on milliseconds | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `DataChange_CreatedBy` | `varchar(64)` | NO | `NONE` | 时间 | 创建人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `DataChange_LastModifiedBy` | `varchar(64)` | YES | `NONE` | 时间 | 最后修改人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `DataChange_LastTime` | `timestamp` | YES | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ReleaseHistory

- 表类型：`BASE TABLE`；字段数：15；数据层：配置元数据（命名推断）。
- 业务域：配置 / 平台（`inferred_name_only`）；建议：配置、版本、字典和开关关联；不作为主统计事实源。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 自增Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `AppId` | `varchar(64)` | NO | `MUL` | 业务属性 | AppID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `ClusterName` | `varchar(32)` | NO | `NONE` | 业务属性 | ClusterName | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `NamespaceName` | `varchar(32)` | NO | `NONE` | 业务属性 | namespaceName | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `BranchName` | `varchar(32)` | NO | `NONE` | 业务属性 | 发布分支名 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `ReleaseId` | `int unsigned` | NO | `MUL` | 业务属性 | 关联的Release Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `PreviousReleaseId` | `int unsigned` | NO | `MUL` | 业务属性 | 前一次发布的ReleaseId | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `Operation` | `tinyint unsigned` | NO | `NONE` | 时间 | 发布类型，0: 普通发布，1: 回滚，2: 灰度发布，3: 灰度规则更新，4: 灰度合并回主分支发布，5: 主分支发布灰度自动发布，6: 主分支回滚灰度自动发布，7: 放弃灰度 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `OperationContext` | `longtext` | NO | `NONE` | 时间 | 发布上下文信息 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `IsDeleted` | `bit(1)` | NO | `NONE` | 业务属性 | 1: deleted, 0: normal | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `DeletedAt` | `bigint` | NO | `NONE` | 时间 | Delete timestamp based on milliseconds | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `DataChange_CreatedBy` | `varchar(64)` | NO | `NONE` | 时间 | 创建人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 13 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 14 | `DataChange_LastModifiedBy` | `varchar(64)` | YES | `NONE` | 时间 | 最后修改人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 15 | `DataChange_LastTime` | `timestamp` | YES | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ReleaseMessage

- 表类型：`BASE TABLE`；字段数：3；数据层：配置元数据（命名推断）。
- 业务域：运营 / 消息（`inferred_name_only`）；建议：消息触达、发送结果与运营触发分析；不得输出接收人身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 自增主键 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `Message` | `varchar(1024)` | NO | `MUL` | 业务属性 | 发布的消息内容 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `DataChange_LastTime` | `timestamp` | NO | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ServerConfig

- 表类型：`BASE TABLE`；字段数：11；数据层：配置元数据（命名推断）。
- 业务域：配置 / 平台（`inferred_name_only`）；建议：配置、版本、字典和开关关联；不作为主统计事实源。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 自增Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `Key` | `varchar(64)` | NO | `MUL` | 业务属性 | 配置项Key | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `Cluster` | `varchar(32)` | NO | `NONE` | 业务属性 | 配置对应的集群，default为不针对特定的集群 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `Value` | `varchar(2048)` | NO | `NONE` | 业务属性 | 配置项值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `Comment` | `varchar(1024)` | YES | `NONE` | 业务属性 | 注释 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `IsDeleted` | `bit(1)` | NO | `NONE` | 业务属性 | 1: deleted, 0: normal | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `DeletedAt` | `bigint` | NO | `NONE` | 时间 | Delete timestamp based on milliseconds | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `DataChange_CreatedBy` | `varchar(64)` | NO | `NONE` | 时间 | 创建人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `DataChange_LastModifiedBy` | `varchar(64)` | YES | `NONE` | 时间 | 最后修改人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `DataChange_LastTime` | `timestamp` | YES | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ServiceRegistry

- 表类型：`BASE TABLE`；字段数：7；数据层：配置元数据（命名推断）。
- 业务域：配置 / 平台（`inferred_name_only`）；建议：配置、版本、字典和开关关联；不作为主统计事实源。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 自增Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `ServiceName` | `varchar(64)` | NO | `MUL` | 业务属性 | 服务名 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `Uri` | `varchar(64)` | NO | `NONE` | 业务属性 | 服务地址 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `Cluster` | `varchar(64)` | NO | `NONE` | 业务属性 | 集群，可以用来标识apollo.cluster或者网络分区 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `Metadata` | `varchar(1024)` | NO | `NONE` | 时间 | 元数据，key value结构的json object，为了方面后面扩展功能而不需要修改表结构 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `DataChange_LastTime` | `timestamp` | NO | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |
