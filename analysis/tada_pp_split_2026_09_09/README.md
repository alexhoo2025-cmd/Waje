# Tada／PP双报告拆分

交付目标：新建两份自包含HTML，原报告及飞书文档不改动。

- 宏观报告：渠道×厂商×新老用户的下注规模、份额、人数、局次和成熟回访。
- 细分报告：游戏规模、头部与长尾、参与深度、RTP、可验证关联、游戏明细及回访边界。
- 冻结统计窗口：2026-08-01至2026-09-07，Africa/Lagos；注册渠道归属；新为行为日账号龄0—29天、老30天及以上，回访固定起点年龄。不是新增付费人群。
- 旧报告内容重组而非新数据期；不更新线上产品、数据表、排序或RTP配置，不创建飞书副本。
- 新增查询前置检查：BigQuery list_dataset_ids于2026-09-09返回Auth required，未执行数据查询。
- 独立审查已分派task-8437226218fd4b549e4c，终态auth_required，无审查意见；主Agent接管复算验收。
- 关联分析使用已保存的游戏级与日级聚合，明确区分关联、复玩强度与定日回访；不得将厂商回访重命名为单游戏回访。

结构遵循项目经营对比及留存模板；新报告使用统一灰蓝／浅蓝／浅紫分组、简短摘要、就近图表解读，完整长表放末尾。

## 交付与复算

- 宏观HTML：`output/html/Tada与PP-宏观对比-新老用户下注与回访-2026-09-09.html`，5张图、5个编号章节、3条摘要。
- 细分HTML：`output/html/Tada与PP-细分诊断-游戏深度回访与RTP-2026-09-09.html`，6张图、6个编号章节、3条摘要、1,081行可排序游戏明细。
- 两份正文与canonical数据分别保存在`macro/`、`detail/`；HTML自包含，CSV与Notebook是可选审计材料，不是页面运行依赖。
- `source-inventory.json`记录原版哈希与飞书修订号78；最终只读回查仍为78，未写入或创建飞书文档。
- `analysis-validation.json`与`completion-audit.json`记录13项完成核验；相关系数以两种独立的秩计算方式交叉验证。
- 目视检查了重点游戏横向对照、新用户回访柱形图、相关系数图和散点极值标注。散点横轴为RTP减100%的百分点差，保留真实RTP在源数据与极值表内。
- 宏观篇图形均为分组比较：两渠道×厂商，及仅三个成熟观察日的回访；选择分组柱形而非伪连续趋势。细分篇使用分组柱形、100%堆叠、横向条形和散点四种形式。
- 原报告的资源加载与资金/TC章节不再铺陈到两份新稿中，仍可回原版查阅；新稿围绕用户要求的宏观与游戏诊断主线。

复算：`python3 analysis/tada_pp_split_2026_09_09/analyze.py` → `python3 analysis/tada_pp_split_2026_09_09/build_reports.py`。Notebook生成与执行使用`.venv/bin/python analysis/tada_pp_split_2026_09_09/make_notebook.py`。

渲染使用原项目入口，分别传入`macro/artifact.json`或`detail/artifact.json`及相应`report.css`作为`--extra-css`，输出到上列新HTML路径。之后运行`python3 analysis/tada_pp_split_2026_09_09/audit.py`。原报告路径不得作为输出参数。

状态：两份拆分报告已完成并通过阅读验收；新增完整单游戏定日回访/用户层面因果研究仍需数据补齐。`detail`数据状态保留partial，表示具名数据缺项，不影响已验证图表与报告交付。

## 飞书版本（后续用户授权创建）

- 宏观篇：https://ksg964l11fam.sg.larksuite.com/docx/HWzVdQfWVoHhZRxiwcBlIJ55grh ，修订号4；5图、4表。
- 细分篇：https://ksg964l11fam.sg.larksuite.com/docx/UfNudBPJcoMUYxxlam2lEzWBgsd ，修订号5；6图、5表、1个完整1,081行游戏明细附件。
- 本次只转换格式，没有重算或扩大数据范围；旧综合文档未修改，未发送消息。
- 两篇全文回读，分别核对181/298个段落与154/261个表格单元格，配色及加粗保留。
- XML、Presentation Decision、创建和回读记录、交付回执保存于各篇目录的lark-*文件。CLI独占草稿目录在归档后删除。
