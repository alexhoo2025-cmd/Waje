# BigQuery Python API 客户端可用性验证

## 目的

验证本机 Python `google-cloud-bigquery` 客户端能否使用项目 `wajenigeria` 的
ADC 身份，以 `europe-west4` 区域执行安卓设备/性能只读查询。

这不是把 `remote_udf_conn` 当作登录凭证。普通 BigQuery 表查询直接使用 OAuth/ADC
身份；`remote_udf_conn` 仅在 SQL 调用远程函数或远程模型时参与执行。

## 已安装环境

```text
Python：项目隔离环境 .venv
google-cloud-bigquery：3.44.0
项目：wajenigeria
查询区域：europe-west4
业务时区：Africa/Lagos
```

安装依赖：

```bash
./.venv/bin/python -m pip install -r analysis/android_bq_api_client_2026_08_27/requirements.txt
```

## 测试内容

1. 客户端库导入和版本检查；
2. ADC 凭证解析和刷新；
3. `INFORMATION_SCHEMA.COLUMNS` 元数据查询 dry run；
4. Android 主包单日 Performance 聚合 dry run；
5. dry run 通过后执行单日 Performance 聚合；
6. 记录 Job ID、扫描字节数、返回行数、数据截止时间和错误状态；
7. 不输出原始 Performance 记录、用户标识、设备唯一标识、URL、请求/响应正文或堆栈。

## 执行

默认只做 dry run；需要执行实际只读聚合时显式加入 `--execute`：

```bash
./.venv/bin/python analysis/android_bq_api_client_2026_08_27/test_bigquery_client.py \
  --execute \
  --output analysis/android_bq_api_client_2026_08_27/client-test-receipt.json
```

如果本地 ADC 未授权，脚本返回 `blocked_authentication`，不会把它解释成无数据。
本机 Google Cloud Console 的浏览器登录也不等于本地 Python ADC 已授权。

## 安全和成本门槛

- 只执行 `SELECT`；
- 查询带日期条件；
- 查询前先 dry run；
- 单条查询最大扫描量为 5 GiB；
- 只返回元数据或聚合结果；
- 不保存 access token、refresh token、服务账号密钥或完整凭证路径；
- 不创建表、视图、Dataform repository 或远程函数；
- 不修改 `remote_udf_conn` 或任何生产配置。

