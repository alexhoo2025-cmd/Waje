# 起源设备监控五页版报表优化需求与具体报表示例

本目录保存飞书需求文档的本地可追溯材料。

- `source-audit.json`：起源报告 #134 的当前页签、筛选、可见数值和缺口审计。
- `wireframes/`：五张静态报表示例，按“筛选区 → KPI → 图表 → 明细表”布局。
- `generate_wireframes.py`：生成线框的可复跑脚本。
- `lark-delivery-receipt.json`：飞书创建、迁移和回读完成后写入。

数据仅使用聚合值。当前 BigQuery MCP 为 `blocked_authentication`；任何无法当场刷新验证的数值均在文档中标注窗口和快照状态，不按实时数据描述。
