# 全平台用户生命周期与付费价值分析刷新（2026-09-04）

> 最新交付入口已转至 `analysis/same_surface_paid_retention_2026_09_04/`：按用户确认的实际端口径生成阶段版HTML与飞书文档。本目录原查询保留为历史账号回访背景，不应再次运行旧HTML生成器覆盖最新同端报告。

## 当前有效版本：付费用户留存专题

报告已按用户最新要求改为新增付费、首次付费用户留存主线，最终使用 `payer_focus.py`。

- 主证据：`paid_retention_server_success_v1/` 三个月聚合结果；`paid_retention_denominators_v1/` 同口径注册分母；`paid_cohort_dictionary_history/` 历史日活覆盖和渠道字典。
- **纠正原支付语义：** `order_success` 是创建订单信号，不能作为成功付费。当前查询使用服务端 `view_metaevent_order.is_success='pay_success'`；历史首充同时核对首充标记与画像日期。旧付费率、ARPU和付费人数结论不再用于当前报告。
- 历史+实时日活统一使用 `view_user_version_daily`，已确认6月有历史记录；旧“6月日活缺失”只适用于旧的实时表查询，不应套用到新付费留存。
- 当前“新增付费”暂定注册当日成功付费，待业务确认窗口。PWA三个候选渠道分别列示，平台映射待确认，不输出正式PWA整体结论。
- 仅辅助保留独立H5联运LTV，不冒充付费人群专属LTV。原 `analysis_summary.json`、旧SQL/回执以及 `artifact_before_paid_focus.json` 是历史审计工件，不是当前付费数据源。
- 当前数值验证回执为 `paid_focus_validation.json`；`validate_report.py` 自动路由至新校验。下方原版本说明仅供历史参考。
- 本次已执行聚合查询累计处理20,422,810,325字节（约19.02GiB），没有线上写入。单条成本门槛拦截的查询未执行；替代源按新文件留痕。

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
