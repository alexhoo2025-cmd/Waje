# Waje Firebase 多端设备与性能汇总

本目录实现 Firebase-only 的 Android、iOS、H5 聚合收集。默认只返回窗口级汇总，不下载日期×版本×设备的明细行。

## 当前最新运行

```text
运行：runs/firebase-multiplatform-20260827T112000Z-c44037e0/
状态：quality_warning
路径：api_fallback
Gemini：blocked_external_prerequisites（MCP trust=false，active_allowed_views=0）
BigQuery API：ok
窗口：Android/iOS 2026-08-20～2026-08-26；H5 2026-08-14～2026-08-21
时区：Africa/Lagos
Dry Run：约 2.68 GB
```

入口索引：`latest_run.json`。当前查询包返回 127 行聚合结果（含元数据与质量检查），没有下载原始事件或用户明细。

Gemini 能力审计：`/Users/robin/Documents/wajetan_analyst/analysis/gemini_cli_audit_2026_08_27/report.html`。审计结论为 CLI/ADC 可用，但 Vertex `aiplatform.endpoints.predict` 和 MCP 安全 View 门禁尚未通过。模型名称只作为有序偏好：不可用时自动尝试 `config/gemini-enterprise.json` 中的备选模型，最后可让 CLI 使用企业默认模型；IAM 错误不会通过换模型规避。

## 紧凑输出内容

- Firebase 数据集清单：8 个数据集的对象数量与类型；表字段数量来自元数据查询。
- Android / iOS Analytics：端 × 包 × 事件分类的窗口汇总，不展开事件参数或版本明细。
- H5 Analytics：四类现有标准事件的窗口汇总。
- Android Sessions：每个包的去标识化会话总数与采集开关覆盖。
- Android / iOS Performance：每个端/包一行，包含记录量、轨迹 P50/P95/P99、网络 P95、成功率和慢帧/冻结帧字段。
- 性能维度：每个端/包/维度只保留窗口级 Top 3 聚合值。
- Crashlytics：每个 Android 包按 Fatal/Non-fatal 汇总去重事件量和问题数；不计算崩溃率。

## 执行

```bash
python3 scripts/run_gemini_multiplatform_firebase_analysis.py \
  --date-from 2026-08-20 \
  --date-to 2026-08-26 \
  --route gemini_first \
  --source-scope firebase_only \
  --report-format html,md,json
```

脚本先检查企业 Gemini MCP；MCP 未同时满足连接、信任和安全 View 白名单时，不调用模型查询，转为本机 BigQuery API 固定聚合包，并在回执中记录 `api_fallback`。所有 SQL 先 Dry Run，单查询不超过 5 GiB，单次运行不超过 25 GiB，结果上限 500 行。

## 主要文件

- `runs/<run-id>/report.html`：阅读版汇总报告。
- `runs/<run-id>/report.md`：可审阅 Markdown 报告。
- `runs/<run-id>/artifact.json`：聚合结果、状态、质量检查和建议。
- `runs/<run-id>/run_receipt.json`：身份、路由、扫描量、行数、错误和远端写入状态。
- `sql/summary/`：紧凑汇总 SQL；`sql/` 根目录保留较细粒度的历史诊断模板，但不属于默认执行路径。
- `tools/firebase_multiplatform_policy.py`：Firebase-only SQL 守卫。
- `scripts/run_gemini_multiplatform_firebase_analysis.py`：Gemini 优先、API 复核与报告编排器。

## 边界

- 不写入 BigQuery、Firebase、Metabase 或飞书。
- 不读取或保存原始事件行、用户标识、设备唯一标识、广告标识、Cookie、Token、URL、请求/响应正文、订单或错误堆栈。
- H5 Web Vitals、白屏、核心请求、前端错误、游戏就绪和可下注当前为 `data_gap` / `blocked`。
- `quality_warning` 表示 API 聚合可用但 Gemini MCP 尚未通过安全门禁或仍存在成熟度/数据缺口，不代表所有指标已经达到正式生产口径。
