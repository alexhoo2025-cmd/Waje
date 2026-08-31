# Waje H5 轻量化游戏首充用户路径分析 V5

本目录用于复现“先付费—后游戏”专题分析。分析只输出聚合结果；用户键仅可在受控数据库查询的 CTE 和 JOIN 中使用，不得写入本地结果、飞书或知识库。

## 固定窗口

- 上线前注册/首充批次：2026-06-16 至 2026-07-13。
- 上线后注册/首充批次：2026-07-14 至 2026-08-10。
- 两个窗口均为 28 天；首充用户继续观察至 T0+15 天。
- 业务时区目标：Africa/Lagos（UTC+1）；数据库会话时区未验收前不得发布日级结论。

## 执行顺序

1. Metabase预检已完成，结果见 `preflight_findings.md`。
2. `sql/01`至`04`是指标逻辑草案；由于`risk_recharge`历史覆盖不足，**不得直接用其空结果发布正式结论**。
3. 先由企业BigQuery或数据开发认证聚合视图提供完整的历史首充事实，再将草案中的首充CTE切换到认证源。
4. 每个查询只保存聚合结果到 `results/`，再运行 `build_analysis.py` 和 `validate_outputs.py`。

## 当前状态

- Metabase：正式外部实例 `http://35.181.27.61:3001/browse` 已登录并完成聚合预检；历史首充覆盖不足。
- BigQuery：`robin@afuruika.net` 已完成ADC授权，`wajenigeria`可见；本轮通过BigQuery API/CLI执行只读聚合查询。MCP仍保持独立OAuth的`Auth required`状态。
- 起源：登录可用；既有审计确认 H5 游戏报表筛选与 GAMEEND 质量仍需复核。
- 已生成等长15天H5/PWA代理首充路径结果和三张图；状态为`provisional_partial`。
- D0—D15复玩、复充、轻量化单游戏和渠道拆分仍未完成，不以空值代替。
