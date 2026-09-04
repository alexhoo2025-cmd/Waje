# Waje 设备与性能一期/二期示例工件

- 主 Markdown：`knowledge/02-数据/Waje多端设备与性能报表看板需求-V3-六模块-2026-09-02.md`
- HTML 阅读版：`output/html/Waje多端设备与性能报表看板需求-V3-六模块-2026-09-02.html`
- 一期数据：`actual_example_data.json`，来自已审阅聚合快照，窗口 `2026-08-20 through 2026-08-26`。
- 二期数据：`simulated_example_data.json`，固定演示场景 `phase2_dashboard_layout_v1`，不对应生产。
- 指标目录：`metric_catalog.json`；看板规格：`dashboard_example_spec.json`；来源映射：`source_mapping.json`。
- 本轮只更新本地文档和结构化工件；不修改 BigQuery、Firebase、Metabase、Ares 或生产埋点。

## 复跑

```bash
python3 scripts/build_device_performance_examples.py
```
