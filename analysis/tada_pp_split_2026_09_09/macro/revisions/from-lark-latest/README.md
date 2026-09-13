# 飞书定稿同步 HTML

来源：宏观报告 HWzVdQfWVoHhZRxiwcBlIJ55grh，revision 181。此次用户要求同步已认可的内容和排版，不重新分析或编辑飞书。

- `readback.json`：本次完整飞书来源。
- `sync.py`：从冻结回读生成 canonical artifact 和可读文本，保留原数据快照、5个原生图表及4个带颜色/合并单元格的静态表格。
- `before-*`：同步前备份，不覆盖。
- `html-receipt.json`：HTML渲染与桌面/窄屏检查。
- `exceptions.json`：仅允许保留用户认可的同义摘要标题“分析报告概要”；不豁免数据或组件检查。

后续应以最新飞书回读同步宏观版本。旧 `build_reports.py` 与 `active_source_review/macro-patch.json` 早于此定稿，直接重建会丢失飞书手工调整；请勿以旧生成器覆盖本次定稿。此次没有修改细分报告或原始合并报告。

同步忠实保留飞书正文，包括尚待核实的活跃分母状态。同步不代表新增业务数据核验，也没有将“待核”恢复为确定值。
