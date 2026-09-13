# 分析报告模板与检查接口

四类骨架只固定阅读任务，不预设业务结论：[经营对比](01-经营对比与指标诊断.md)、[留存](02-留存与生命周期.md)、[调研](03-行业与竞品调研.md)、[埋点与机制](04-埋点机制与方案讲解.md)。填完参数再绘图，模拟验收样例不当作业务源。

最终HTML默认交付为可离线阅读的单文件，采用[2026-09-11单文件HTML样式参考](单文件HTML样式参考-2026-09-11.md)与主规范中的同日补充：围绕核心议题，全文观点/关键数据高亮，峰值标注清晰，变化并入对应指标列。参考样式不继承样例的业务口径或结论。

## 新artifact的最小声明

在现有`manifest`下添加`reportContract`；共享渲染器继续使用原`blocks/charts/tables/sources`，不增加第二套数据实现：

```json
{
  "type": "business",
  "language": "zh",
  "population": "{{本报告实际人群与端归属}}",
  "period": "{{统计范围及比较范围}}",
  "timezone": "{{业务时区或静态资料的时间解释}}",
  "metrics": [
    {"dataset":"comparison", "field":"rate", "kind":"ratio", "unit":"%", "scale":"fraction", "definition":"参与人数除以同组活跃人数", "denominator":"同组活跃人数", "min":0, "max":1}
  ],
  "assertions": [
    {"kind":"ratio", "dataset":"comparison", "numerator":"participants", "denominator":"active", "actual":"rate"}
  ],
  "decisions": {"new_user":{"status":"confirmed", "value":"按本任务确认填写"}},
  "openQuestions": []
}
```

`type`支持business、retention、research、mechanism和generic；mechanism不要求经营数据。旧artifact没有声明时提示兼容检查，不凭模板猜口径。语言默认为中文；明确要求英文的报告可以声明language=en。

上例是填写说明，不是可交付成品。标题与关键口径中的`{{…}}`、`[待填写]`等明确占位符会被拦截；指标确实未知时应填写具体缺口说明并限制相关结论，而非用占位符冒充参数。

比例`fraction`使用0.58表示58%；若值为58，声明`percent_points`并使用number和%单位。RTP可超过100%，只有确有业务上限的指标才声明max=1。

当前共享导出器的部分静态图可能保留fraction数值而未转换标签。若轴标为%却显示0.58，应判为显示错误，不能仅凭结构验证通过就交付。可保留原始`rate=0.58`，另加`rate_pct=58`用于图表，声明percent_points、number及%轴单位，并核对导出的实际标签；不要自动改写原始业务比例。测试样例保留了原值及显示字段的数学核对。

### 可执行断言

- `ratio`：同一数据集逐行`numerator / denominator = actual`；零分母期望null。
- `difference_pp`：`(after-before)×100 = actual`，before/after为fraction。
- `relative_change`：`after / before - 1 = actual`，结果为fraction；零基线期望null。
- `equal`：`left/right`各为`{dataset, field, where}`，where须唯一定位一行；用于图表、表格、摘要数据之间的精确核对。
- `sum`：left为需要求和的数据集字段，right须唯一定位合计；可用where限定相同口径。
- `tolerance`为非负绝对容差，默认1e-8；声明无效也会拦截，不会悄悄跳过。

这些断言只验证已声明关系。不能因此声称所有正文数字、查询分母、因果和数据真实性已经自动验证。

## 检查与交付

```sh
node scripts/check_report_quality.mjs --input path/to/artifact.json
node scripts/check_report_quality.mjs --input path/to/report.md
node scripts/check_report_quality.mjs --input path/to/report.xml
node scripts/deliver_readable_report.mjs --input path/to/artifact.json --check-only
node scripts/deliver_readable_report.mjs --input path/to/artifact.json --output path/to/report.html --receipt path/to/receipt.json
```

退出码1表示拦截，0表示没有未豁免硬错误；0不代表所有人工和视觉检查完成。JSON的coverage逐项保留未验证状态。`--check-only`不渲染、不发布、不查询业务数据；除显式`--receipt`外不写文件。

## 限定例外

`--exceptions path/to/exceptions.json`接收数组；每项须有`report_sha256`、`rule_id`、精确`location`、`reason`、`approved_by`及`approval_reference:{path,sha256}`。批准文件必须在项目内，哈希匹配，不支持位置通配符。格式、引用、计算与隐私等不可豁免规则见策略配置。检查器只核验记录及范围，不认证批准人的真实身份；批准真实性仍需人工负责。

## 飞书与原流程

飞书XML先运行文本检查，再沿用已有创建/更新与全文回读流程。保留同一份artifact或数据快照，图表导出失败应换为等价可用形式；不得新造数字图填位。未授权时不自动发布。旧HTML入口保留作兼容，不批量迁移旧脚本或重发历史报告。
