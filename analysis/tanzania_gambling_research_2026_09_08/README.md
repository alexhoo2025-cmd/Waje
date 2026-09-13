# 坦桑调研底稿与复算入口

报告截至2026年9月8日；原Excel观察日期未标明。原文件未修改。

## 交付与范围

- HTML：`output/html/坦桑尼亚博彩行业与产品调研报告-2026-09-08.html`
- 飞书地址与回读验收：`lark-verification.json`
- 同源正文：`report.md`；标准报告数据：`artifact.json`
- 原始输入：用户提供的两份Excel；19品牌、25表（含3隐藏表）。
- 官方核验：`external-evidence.json`，21项来源/访问记录。

## 可复算流程

使用带openpyxl的Python，从项目根依次执行：

```bash
python3 analysis/tanzania_gambling_research_2026_09_08/extract.py
python3 analysis/tanzania_gambling_research_2026_09_08/analyze.py
python3 analysis/tanzania_gambling_research_2026_09_08/build_report.py
python3 analysis/tanzania_gambling_research_2026_09_08/validate_analysis.py
```

`复算记录.ipynb`为短版审阅入口。当前环境没有Jupyter/nbformat，代码单元已通过顺序Python执行与断言；运行方式记录在notebook元数据，不声称已通过Jupyter内核测试。

## 来源、定义与状态

- `cells.json`：逐单元格原值/格式/公式/文件和工作表定位，保留空文本与缺项差异；不是清洗后的独立调查。
- `inventory.json`：25表状态与原文件哈希；`formula_validation.json`：265公式复算。
- `normalized.json`：品牌别名、支付门槛、应用、供应商、输入提示、串关与线下配对值。
- `cross_version_reconciliation.json`：两版ONLINE18共同品牌的378字段归一化一致；WinPrincess在加工版ONLINE缺、Profile补。
- 金额TZS；百分比与本金倍数分开；覆盖分母只含明确记录，未知不补零。
- `report-snapshot.sqlite3`及`query-verification.json`是本地报告快照读取，不是线上数据查询；原始计算在Python脚本。
- `sonnet-reviewed.md`保存独立审查候选与验收。主Agent更正了候选中过期/造假或厂商宣称的过度解释，正式结论以`report.md`为准。
- 宏观数据分别标明自然年、财年、全国与大陆；未获得当前GGR、市场份额或获客成本，不推算进入回报。

## 交付验证

`analysis-verification.json`、`html-delivery-receipt.json`、`visual-export-receipt.json`、`lark-verification.json`分别记录计算、离线HTML、同源图像与飞书API回读。仅向用户指定飞书文档写入报告；没有发消息或修改权限。
