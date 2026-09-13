# Waje报告规范升级｜交付与验收

版本：2026-09-09.1。实施范围仅为Waje项目；不重算业务数据，不改历史报告，不新建/重发飞书成品，不修改个人全局技能或插件缓存。

## 阅读入口

- [主规范](/Users/robin/Documents/wajetan_analyst/knowledge/05-运行/报告排版与配色规范-2026-09-07.md)：沿用原入口，扩展为分析、表述和视觉统一标准。
- [速查与措辞指南](/Users/robin/Documents/wajetan_analyst/knowledge/05-运行/分析报告速查与措辞指南-2026-09-09.md)：出稿前九问、图表选择、改写边界。
- [修改依据与版本台账](/Users/robin/Documents/wajetan_analyst/knowledge/05-运行/分析报告修改依据台账-2026-09-09.md)：19项要求/偏好/新增规则；12个基准条目，含分期索引；9份飞书现场修订核对。
- [四类模板与接口](/Users/robin/Documents/wajetan_analyst/knowledge/90-模板/分析报告/README.md)：经营对比、留存、调研、埋点/机制。

## 已启用的入口

```sh
npm run report:check -- --input path/to/artifact.json
node scripts/deliver_readable_report.mjs --input path/to/artifact.json --check-only
npm run report:deliver -- --input path/to/artifact.json --output path/to/report.html --receipt path/to/receipt.json
npm run test:report-quality
```

新增HTML交付默认先检查。Markdown/XML使用同一检查器做文本和结构检查，再沿用原发布及回读流程。缺省表格排序给提示；声明了不存在的排序字段才作为引用错误拦截。正文参数不会被自动改写，也不统一套用“注册当天”或“30天内”。

`AGENTS.md`、`CLAUDE.md`和知识索引已经指向新规范。旧调用方式与格式保留；缺少新结构化参数时明确提示人工复核，不假装已经认证口径。

## 本次验收

- 53项规则测试通过：含不同人群定义、零分母、RTP超过100%、百分点与相对变化、必要否定句、中文标题、占位符、例外范围、数据引用、已确认与待定冲突、输入不被改写等。
- 四类模拟样例：经营/留存/调研采用canonical artifact，机制采用Markdown与XML，未强制生成经营图。
- 三份HTML样例：1440px与390px、来源交互及浅深静态图表示通过；留存静态图百分数显示值单独核对。
- 12项历史基准做只读回归；问题保留为反例或待复核，原稿哈希不变。不能把“发现旧稿问题”写成“旧稿已修复”。
- 业务查询与新外部发布均为0；飞书仅只读获取已有版本。

机器结果见`validation-receipt.json`、`unit-tests.txt`；规则依据见`requirements-evidence.json`，版本基准见`baseline-registry.json`和`remote-final-style.json`。候选扫描覆盖项目相关文本文件，原始数据、逐字聊天、大文件及生成图谱排除；未明确匹配用户意见的候选不变成偏好。

## 边界与已发现的依赖问题

1. **检查不等于业务认证。** 只有声明的公式/跨表关系被计算核对；来源真实性、完整需求覆盖、未声明计算、成熟条件、因果、隐私完整性等仍需负责人复核。
2. **静态百分比显示存在共享导出器差异。** 曾观察到%轴配0.1等fraction标签；失败证据已保存。样例保留原始比例，另用明确的百分数显示字段并核对导出数值，不修改原始业务值。
3. **共享浏览器有间歇性就绪超时。** 已保留失败记录。生产入口只对指定探测超时最多重试一次，输入变化立即停止；数据/格式/溢出错误不重试。当前最后一轮实际验收通过，不意味着该外部运行时问题已根治。
4. **独立模型审查未完成。** task-60c466d4a79521a4f66d终止于auth_required。由主Agent执行本地测试、版本检查和实际渲染验证，不宣称双模型审查通过。

测试回执在每次启动时进入running，结束写passed/partial/failed；旧回执移入`validation-history/`，不会在新失败时保留旧的绿色状态作为本次结果。

## 后续维护

新增偏好先附来源和适用范围，再决定通用化或保留为报告参数。模板、机器规则和共享CSS分别维护职责；不用一个反例更改所有报告。新规则先补正反测试，再应用于未来产出；不要回改历史样板来让测试变绿。
