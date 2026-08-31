# BigQuery API 验证所需权限

## 当前阻断

受控只读工具调用项目 `wajenigeria` 的 `list_dataset_ids` 返回：

```text
Auth required
```

这表示本线程当前没有可用的 BigQuery API/MCP 身份。不能将其解释为数据集不存在或
安卓数据为空。

## 最小权限建议

对执行只读聚合的身份，仅申请：

- 项目级 `bigquery.jobs.create`；
- 目标批准数据集或授权聚合视图的 `bigquery.tables.getData`；
- 元数据检查所需的 `bigquery.tables.get` / `bigquery.tables.list`；
- 如需使用连接中的 Remote Function，再单独申请 `bigquery.connections.use`，本次普通表聚合不需要该权限。

不申请 `Data Editor`、`Data Owner` 或写入/导出权限。身份使用 OAuth/ADC 或受控服务
账号，不在聊天或仓库保存 JSON 密钥、Cookie 或 Token。

## 授权恢复后的验证顺序

1. 重新执行 `list_dataset_ids(projectId=wajenigeria)`；
2. 核对 `waje_ng_firebase_android_performance`、`waje_ng_firebase_android_sessions`、
   `waje_ng_firebase_android` 的实际位置和对象；
3. 用 `00_metadata_columns.sql` 核对字段；
4. 对 `01`–`07` 逐条 dry run；
5. 只执行预算内的聚合查询；
6. 回读结果并生成 `live-query-receipt.json`、`query-results.json` 和最终
   `validation-report.json`。

