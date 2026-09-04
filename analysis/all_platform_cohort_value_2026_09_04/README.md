# 全平台用户生命周期与付费价值分析刷新（2026-09-04）

本目录是对 2026-09-03 全平台 cohort 报告的独立刷新运行。

- 仅调用 `wajenigeria` Cloud BigQuery 的只读聚合查询。
- 每条 SQL 先干跑；单条最多 5 GiB、整次最多 25 GiB。
- 不保存用户、订单、设备、支付参考号、URL 或凭据。
- 最终报告只使用各来源的最新完整日期；未成熟 cohort 显示为 `N/A`，不以零值补齐。

## 交付物

- `artifact.json`：可移植 HTML 报告的 canonical 数据、来源与图表合同。
- `analysis_summary.json`：已复算的月度 H5、APP、付费与 Phoenix 聚合摘要。
- `validation_report.json` / `validation_report.md`：数据、cohort 键、加权计算和 HTML 自包含性验证回执。
- `results/`：服务器侧生命周期、留存和严格 H5 成功支付 cohort 查询结果。
- `payment_segmentation/`：首包/首渠道下的新增付费、首充、老付费和复充分层聚合。
- `firebase_diagnosis/`：Phoenix `p=h5phx` Firebase 客户端回访与事件契约诊断。

## 当前数据状态

- 起源、Ares 与 Lifecycle 服务器侧聚合来源均已覆盖至 `2026-09-04`。
- Phoenix Firebase 完整日表仅到 `2026-09-02`；它只用于客户端行为诊断，不能计算成功付费率。
- 8 月 H5 PAWAJEBETH5 的首充、期初老付费和复充有完整月度去重值；新增注册付费仅有两个独立半月窗口，不能相加为整月去重人数。
- APP 端包含留存与付费阶段对照。LTV 来源暂不具备经验证的首平台映射，报告不将渠道字段强转为 Android/iOS/H5 LTV。

## 复跑顺序

1. 使用项目 `.venv` 和有效 ADC 运行 `run_readonly_queries.py` 的指定 SQL；每条 SQL 先由 `validate_readonly_sql.py` 校验。
2. 执行 `summarize_results.py`，再执行 `build_report_artifact.py`。
3. 运行 `node build_report_html.mjs`，通过官方读取器生成带参考报告主题的 HTML，并检查桌面、窄屏与来源交互；随后运行 `validate_report.py`。

专题范围已排除 Phoenix/Firebase 展示内容，原始独立审计文件保留。主题层已修复旧版顶栏 `100vw` 导致的横向溢出；桌面 1440px、窄屏 390px 与来源按钮交互均已通过检查。最终 HTML 无外部 HTTP(S) 依赖。
