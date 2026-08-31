---
type: metabase_schema_dictionary
date: 2026-08-26
schema: ApolloPortalDB
status: observed_metadata
source_engine: mysql_style_information_schema_export
---

# Metabase 数据字典｜ApolloPortalDB

> 证据边界：本分册来自可见 `information_schema` 定义。字段值、默认值、连接参数、敏感字段原文均未保存；字段用途和数据层标记中“命名推断”均需由业务 Owner 或数据开发补证。

## 1. Schema 概览

- 表：**16** 张；字段：**126** 个。
- 数据层：配置元数据（命名推断）。
- 外键、分区、索引明细、行数、更新时刻、保留周期：本次未导出，不能推断。

## 2. 表清单

| 表 | 类型 | 字段数 | 业务域（命名推断） | 受控字段候选数 | 表说明 |
|---|---|---:|---|---:|---|
| `App` | BASE TABLE | 12 | 配置 / 平台 | 1 | 应用表 |
| `AppNamespace` | BASE TABLE | 11 | 配置 / 平台 | 0 | 应用namespace定义 |
| `Authorities` | BASE TABLE | 3 | 用户 / 账号 | 0 | — |
| `Consumer` | BASE TABLE | 12 | 配置 / 平台 | 1 | 开放API消费者 |
| `ConsumerAudit` | BASE TABLE | 6 | 日志 / 数据质量 | 0 | consumer审计表 |
| `ConsumerRole` | BASE TABLE | 8 | 配置 / 平台 | 0 | consumer和role的绑定表 |
| `ConsumerToken` | BASE TABLE | 9 | 配置 / 平台 | 2 | [已脱敏：敏感字段说明不进入知识库] |
| `Favorite` | BASE TABLE | 9 | 配置 / 平台 | 0 | 应用收藏表 |
| `Permission` | BASE TABLE | 8 | 配置 / 平台 | 0 | permission表 |
| `Role` | BASE TABLE | 7 | 配置 / 平台 | 0 | 角色表 |
| `RolePermission` | BASE TABLE | 8 | 配置 / 平台 | 0 | 角色和权限的绑定表 |
| `SPRING_SESSION` | BASE TABLE | 7 | 配置 / 平台 | 0 | — |
| `SPRING_SESSION_ATTRIBUTES` | BASE TABLE | 3 | 配置 / 平台 | 0 | — |
| `ServerConfig` | BASE TABLE | 9 | 配置 / 平台 | 0 | 配置服务自身配置 |
| `UserRole` | BASE TABLE | 8 | 用户 / 账号 | 0 | 用户和role的绑定表 |
| `Users` | BASE TABLE | 6 | 用户 / 账号 | 2 | 用户表 |

## 3. 逐表字段定义

### App

- 表类型：`BASE TABLE`；字段数：12；数据层：配置元数据（命名推断）。
- 业务域：配置 / 平台（`inferred_name_only`）；建议：配置、版本、字典和开关关联；不作为主统计事实源。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 主键 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `AppId` | `varchar(500)` | NO | `MUL` | 业务属性 | AppID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `Name` | `varchar(500)` | NO | `MUL` | 业务属性 | 应用名 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `OrgId` | `varchar(32)` | NO | `NONE` | 业务属性 | 部门Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `OrgName` | `varchar(64)` | NO | `NONE` | 业务属性 | 部门名字 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `OwnerName` | `varchar(500)` | NO | `NONE` | 业务属性 | ownerName | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `varchar(500)` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 8 | `IsDeleted` | `bit(1)` | NO | `NONE` | 业务属性 | 1: deleted, 0: normal | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `DataChange_CreatedBy` | `varchar(64)` | NO | `NONE` | 时间 | 创建人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `DataChange_LastModifiedBy` | `varchar(64)` | YES | `NONE` | 时间 | 最后修改人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `DataChange_LastTime` | `timestamp` | YES | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### AppNamespace

- 表类型：`BASE TABLE`；字段数：11；数据层：配置元数据（命名推断）。
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
| 8 | `DataChange_CreatedBy` | `varchar(64)` | NO | `NONE` | 时间 | 创建人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `DataChange_LastModifiedBy` | `varchar(64)` | YES | `NONE` | 时间 | 最后修改人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `DataChange_LastTime` | `timestamp` | YES | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### Authorities

- 表类型：`BASE TABLE`；字段数：3；数据层：配置元数据（命名推断）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 自增Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `Username` | `varchar(64)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `Authority` | `varchar(50)` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### Consumer

- 表类型：`BASE TABLE`；字段数：12；数据层：配置元数据（命名推断）。
- 业务域：配置 / 平台（`inferred_name_only`）；建议：配置、版本、字典和开关关联；不作为主统计事实源。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 自增Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `AppId` | `varchar(500)` | NO | `MUL` | 业务属性 | AppID | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `Name` | `varchar(500)` | NO | `NONE` | 业务属性 | 应用名 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `OrgId` | `varchar(32)` | NO | `NONE` | 业务属性 | 部门Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `OrgName` | `varchar(64)` | NO | `NONE` | 业务属性 | 部门名字 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `OwnerName` | `varchar(500)` | NO | `NONE` | 业务属性 | ownerName | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `varchar(500)` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 8 | `IsDeleted` | `bit(1)` | NO | `NONE` | 业务属性 | 1: deleted, 0: normal | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `DataChange_CreatedBy` | `varchar(64)` | NO | `NONE` | 时间 | 创建人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 10 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 11 | `DataChange_LastModifiedBy` | `varchar(64)` | YES | `NONE` | 时间 | 最后修改人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 12 | `DataChange_LastTime` | `timestamp` | YES | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ConsumerAudit

- 表类型：`BASE TABLE`；字段数：6；数据层：配置元数据（命名推断）。
- 业务域：日志 / 数据质量（`inferred_name_only`）；建议：入库延迟、错误、重试和数据质量排障；需明确日志保留周期。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 自增Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `ConsumerId` | `int unsigned` | YES | `MUL` | 业务属性 | Consumer Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `Uri` | `varchar(1024)` | NO | `NONE` | 业务属性 | 访问的Uri | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `Method` | `varchar(16)` | NO | `NONE` | 业务属性 | 访问的Method | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `DataChange_LastTime` | `timestamp` | YES | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ConsumerRole

- 表类型：`BASE TABLE`；字段数：8；数据层：配置元数据（命名推断）。
- 业务域：配置 / 平台（`inferred_name_only`）；建议：配置、版本、字典和开关关联；不作为主统计事实源。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 自增Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `ConsumerId` | `int unsigned` | YES | `MUL` | 业务属性 | Consumer Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `RoleId` | `int unsigned` | YES | `MUL` | 业务属性 | Role Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `IsDeleted` | `bit(1)` | NO | `NONE` | 业务属性 | 1: deleted, 0: normal | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `DataChange_CreatedBy` | `varchar(64)` | YES | `NONE` | 时间 | 创建人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `DataChange_LastModifiedBy` | `varchar(64)` | YES | `NONE` | 时间 | 最后修改人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `DataChange_LastTime` | `timestamp` | YES | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### ConsumerToken

- 表类型：`BASE TABLE`；字段数：9；数据层：配置元数据（命名推断）。
- 业务域：配置 / 平台（`inferred_name_only`）；建议：配置、版本、字典和开关关联；不作为主统计事实源。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 自增Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `ConsumerId` | `int unsigned` | YES | `NONE` | 业务属性 | ConsumerId | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | [REDACTED:CREDENTIAL_OR_SECRET] | `varchar(128)` | NO | `UNI` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 禁止展示、导出或进入分析产物 |
| 4 | [REDACTED:CREDENTIAL_OR_SECRET] | `datetime` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 禁止展示、导出或进入分析产物 |
| 5 | `IsDeleted` | `bit(1)` | NO | `NONE` | 业务属性 | 1: deleted, 0: normal | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `DataChange_CreatedBy` | `varchar(64)` | NO | `NONE` | 时间 | 创建人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `DataChange_LastModifiedBy` | `varchar(64)` | YES | `NONE` | 时间 | 最后修改人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `DataChange_LastTime` | `timestamp` | YES | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### Favorite

- 表类型：`BASE TABLE`；字段数：9；数据层：配置元数据（命名推断）。
- 业务域：配置 / 平台（`inferred_name_only`）；建议：配置、版本、字典和开关关联；不作为主统计事实源。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 主键 | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `UserId` | `varchar(32)` | NO | `MUL` | 业务属性 | 收藏的用户 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `AppId` | `varchar(500)` | NO | `MUL` | 业务属性 | AppID | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `Position` | `int` | NO | `NONE` | 业务属性 | 收藏顺序 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `IsDeleted` | `bit(1)` | NO | `NONE` | 业务属性 | 1: deleted, 0: normal | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `DataChange_CreatedBy` | `varchar(64)` | NO | `NONE` | 时间 | 创建人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `DataChange_LastModifiedBy` | `varchar(64)` | YES | `NONE` | 时间 | 最后修改人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `DataChange_LastTime` | `timestamp` | YES | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### Permission

- 表类型：`BASE TABLE`；字段数：8；数据层：配置元数据（命名推断）。
- 业务域：配置 / 平台（`inferred_name_only`）；建议：配置、版本、字典和开关关联；不作为主统计事实源。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 自增Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `PermissionType` | `varchar(32)` | NO | `NONE` | 状态 / 枚举 | 权限类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `TargetId` | `varchar(256)` | NO | `MUL` | 业务属性 | 权限对象类型 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `IsDeleted` | `bit(1)` | NO | `NONE` | 业务属性 | 1: deleted, 0: normal | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `DataChange_CreatedBy` | `varchar(64)` | NO | `NONE` | 时间 | 创建人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `DataChange_LastModifiedBy` | `varchar(64)` | YES | `NONE` | 时间 | 最后修改人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `DataChange_LastTime` | `timestamp` | YES | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### Role

- 表类型：`BASE TABLE`；字段数：7；数据层：配置元数据（命名推断）。
- 业务域：配置 / 平台（`inferred_name_only`）；建议：配置、版本、字典和开关关联；不作为主统计事实源。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 自增Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `RoleName` | `varchar(256)` | NO | `MUL` | 业务属性 | Role name | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `IsDeleted` | `bit(1)` | NO | `NONE` | 业务属性 | 1: deleted, 0: normal | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `DataChange_CreatedBy` | `varchar(64)` | NO | `NONE` | 时间 | 创建人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `DataChange_LastModifiedBy` | `varchar(64)` | YES | `NONE` | 时间 | 最后修改人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `DataChange_LastTime` | `timestamp` | YES | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### RolePermission

- 表类型：`BASE TABLE`；字段数：8；数据层：配置元数据（命名推断）。
- 业务域：配置 / 平台（`inferred_name_only`）；建议：配置、版本、字典和开关关联；不作为主统计事实源。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 自增Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `RoleId` | `int unsigned` | YES | `MUL` | 业务属性 | Role Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `PermissionId` | `int unsigned` | YES | `MUL` | 业务属性 | Permission Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `IsDeleted` | `bit(1)` | NO | `NONE` | 业务属性 | 1: deleted, 0: normal | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `DataChange_CreatedBy` | `varchar(64)` | NO | `NONE` | 时间 | 创建人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `DataChange_LastModifiedBy` | `varchar(64)` | YES | `NONE` | 时间 | 最后修改人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `DataChange_LastTime` | `timestamp` | YES | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### SPRING_SESSION

- 表类型：`BASE TABLE`；字段数：7；数据层：配置元数据（命名推断）。
- 业务域：配置 / 平台（`inferred_name_only`）；建议：配置、版本、字典和开关关联；不作为主统计事实源。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `PRIMARY_ID` | `char(36)` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `SESSION_ID` | `char(36)` | NO | `UNI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `CREATION_TIME` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `LAST_ACCESS_TIME` | `bigint` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `MAX_INACTIVE_INTERVAL` | `int` | NO | `NONE` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `EXPIRY_TIME` | `bigint` | NO | `MUL` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `PRINCIPAL_NAME` | `varchar(100)` | YES | `MUL` | 业务属性 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### SPRING_SESSION_ATTRIBUTES

- 表类型：`BASE TABLE`；字段数：3；数据层：配置元数据（命名推断）。
- 业务域：配置 / 平台（`inferred_name_only`）；建议：配置、版本、字典和开关关联；不作为主统计事实源。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `SESSION_PRIMARY_ID` | `char(36)` | NO | `PRI` | 标识 / 关联 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `ATTRIBUTE_NAME` | `varchar(100)` | NO | `PRI` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `ATTRIBUTE_BYTES` | `blob` | NO | `NONE` | 时间 | — | 允许在授权范围内做聚合分析；不输出字段值 |

### ServerConfig

- 表类型：`BASE TABLE`；字段数：9；数据层：配置元数据（命名推断）。
- 业务域：配置 / 平台（`inferred_name_only`）；建议：配置、版本、字典和开关关联；不作为主统计事实源。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 自增Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `Key` | `varchar(64)` | NO | `MUL` | 业务属性 | 配置项Key | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `Value` | `varchar(2048)` | NO | `NONE` | 业务属性 | 配置项值 | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `Comment` | `varchar(1024)` | YES | `NONE` | 业务属性 | 注释 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `IsDeleted` | `bit(1)` | NO | `NONE` | 业务属性 | 1: deleted, 0: normal | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `DataChange_CreatedBy` | `varchar(64)` | NO | `NONE` | 时间 | 创建人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `DataChange_LastModifiedBy` | `varchar(64)` | YES | `NONE` | 时间 | 最后修改人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 9 | `DataChange_LastTime` | `timestamp` | YES | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### UserRole

- 表类型：`BASE TABLE`；字段数：8；数据层：配置元数据（命名推断）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 自增Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `UserId` | `varchar(128)` | YES | `MUL` | 业务属性 | 用户身份标识 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | `RoleId` | `int unsigned` | YES | `MUL` | 业务属性 | Role Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 4 | `IsDeleted` | `bit(1)` | NO | `NONE` | 业务属性 | 1: deleted, 0: normal | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | `DataChange_CreatedBy` | `varchar(64)` | YES | `NONE` | 时间 | 创建人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 6 | `DataChange_CreatedTime` | `timestamp` | NO | `NONE` | 时间 | 创建时间 | 允许在授权范围内做聚合分析；不输出字段值 |
| 7 | `DataChange_LastModifiedBy` | `varchar(64)` | YES | `NONE` | 时间 | 最后修改人邮箱前缀 | 允许在授权范围内做聚合分析；不输出字段值 |
| 8 | `DataChange_LastTime` | `timestamp` | YES | `MUL` | 时间 | 最后修改时间 | 允许在授权范围内做聚合分析；不输出字段值 |

### Users

- 表类型：`BASE TABLE`；字段数：6；数据层：配置元数据（命名推断）。
- 业务域：用户 / 账号（`inferred_name_only`）；建议：注册、登录与生命周期聚合；禁止导出可识别身份字段。
- 关系状态：主键/普通索引标记来自 `COLUMN_KEY`；外键关系未导出，不能据字段命名假定关联。

| 序号 | 字段 | 类型 | 可空 | 键标记 | 字段分组 | 字段说明 | 使用边界 |
|---:|---|---|---|---|---|---|---|
| 1 | `Id` | `int unsigned` | NO | `PRI` | 标识 / 关联 | 自增Id | 允许在授权范围内做聚合分析；不输出字段值 |
| 2 | `Username` | `varchar(64)` | NO | `NONE` | 业务属性 | 用户登陆账号 | 允许在授权范围内做聚合分析；不输出字段值 |
| 3 | [REDACTED:CREDENTIAL_OR_SECRET] | `varchar(512)` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 禁止展示、导出或进入分析产物 |
| 4 | `UserDisplayName` | `varchar(512)` | NO | `NONE` | 游戏 / 玩法 | 用户名称 | 允许在授权范围内做聚合分析；不输出字段值 |
| 5 | [REDACTED:KYC_PERSONAL_IDENTIFIER_OR_BIOMETRIC] | `varchar(64)` | NO | `NONE` | 敏感字段 | [已脱敏：敏感字段说明不进入知识库] | 受限；仅脱敏聚合或伪标识下钻 |
| 6 | `Enabled` | `tinyint` | YES | `NONE` | 业务属性 | 是否有效 | 允许在授权范围内做聚合分析；不输出字段值 |
