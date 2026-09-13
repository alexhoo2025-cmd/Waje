# Tada／PP全期分析工件

统计期：2026年8月1日至9月7日，Africa/Lagos。主报告已交付，整体证据状态为**带明确缺口分享（partial）**。

## 阅读入口

- [飞书报告](https://ksg964l11fam.sg.larksuite.com/docx/MUmUdKO7ko3hKIxY822lBXJQggg)
- [自包含HTML](/Users/robin/Documents/wajetan_analyst/output/html/Tada与PP-APP-H5下注与回访对比-2026-09-08.html)
- [Markdown正文](/Users/robin/Documents/wajetan_analyst/analysis/tada_pp_app_h5_actual_2026_09_08/报告.md)
- [复算Notebook](/Users/robin/Documents/wajetan_analyst/analysis/tada_pp_app_h5_actual_2026_09_08/复算与验收.ipynb)

## 可复算来源

| 工件 | 内容 |
| --- | --- |
| `scope.json`、`scan-authorization.json` | 用户确认的窗口、动态账号龄、渠道归属与本专项查询额度 |
| `metadata-inventory.json` | 已核验的数据目录和字段，不含用户明细 |
| `sql/`、`queries/` | 实际查询、聚合结果与扫描回执；未执行查询保留明确状态 |
| `money-reconciliation.json` | 单日源值与起源报表金额及局数对账 |
| `channel-mapping.json` / `.csv` | 渠道命名候选映射、待确认项与依据 |
| `core-corrected.json` | 扣除已定位重复记录后的核心聚合 |
| `analysis-results.json` | 分组份额、回访、游戏构成、资源、充值与算术分解 |
| `final-validation.json` | 独立逐日对账、分母、成熟窗口和报告校验结果 |
| `artifact.json` | HTML、Markdown、飞书的统一内容及数据来源 |
| `delivery-receipt.json` | HTML桌面／窄屏／来源交互验收 |
| `lark-delivery-receipt.json` | 飞书全文回读、328个表格单元格核对、7图和3附件验收 |
| `lark-source.xml`、`lark-assets/` | 飞书内容源与共享渲染器导出的真实图表 |
| `共同游戏对照.csv`、`回访分子分母.csv`、`四组合新老用户.csv` | 可供筛选复核的聚合附件 |

## 本地复算

在项目根目录运行以下命令，只使用已保存的聚合数据，不新增BigQuery扫描：

```sh
./.venv/bin/python analysis/tada_pp_app_h5_actual_2026_09_08/analyze_results.py
./.venv/bin/python analysis/tada_pp_app_h5_actual_2026_09_08/build_validation_notebook.py
```

Notebook已用项目虚拟环境从首个代码单元执行到末尾。所需nbformat、nbclient、ipykernel安装在项目`.venv`，未改变线上服务。

这些脚本面向本次快照，不是定时取数任务。重新取数须另行确认日期、字段及剩余额度；不要把执行`run_query.py --execute`当作免费本地复算。累计扫描含前期探查，不能换目录重置额度。

## 未完成的计划项

- 最终到账TC：需提供到账事实，或确认AUDIT状态与钱包币种／单位的准确映射。
- 严格现金／奖励拆分RTP与逐笔下注次数：当前联运事件字段不足，不能用近似指标冒充。
- 实际运行端迁移、曝光与加载因果链：渠道命名无法替代行为端和同次打开标识。
- 大额用户分位、自然／投放、入口位置等进一步交叉拆解：本轮尚未完成。
- Sonnet独立审查：任务`task-c789431b0aee0e33e373`因授权缺失阻塞，无审查结果。

以上缺口已在报告相应位置说明。HTML和飞书均保留它们，未填零或编造完成。已交付主报告不等于所有计划维度都已闭环。

## 修改与发布约束

原始查询结果和旧方案保留原样。飞书文档已创建一次；后续修改应更新上述同一文档并回读，不能重复创建替代。原临时草稿已另存`lark-source.xml`，清理临时工作目录不会删除报告或核验记录。
