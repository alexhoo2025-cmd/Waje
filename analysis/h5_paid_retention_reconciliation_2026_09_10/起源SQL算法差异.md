# 起源与原报告：H5付费留存算法差异

## 执行摘要

**已确认存在算法差异，不能用“都是BigQuery”视为同口径。** 起源的新增付费条件为target_day等于first_pay_date，按xl_id去重；原报告按register_day与成功支付日期相同筛选，按user_id去重。

**回访口径也不同。** 起源用app_id＋xl_id关联业务活跃事件视图，原报告用user_id关联用户日活表。此前单日核验已显示日表与业务活跃事件存在覆盖差异，但该探查仍按user_id，尚未完整复现起源的xl_id算法。

**该文件是含参数的SQL模板／诊断文本，尚非已验证的最终执行SQL。** 文件保留3个参数占位符，末尾包含Calcite解析警告。可以确认模板算法，不能仅凭这段警告判断起源整个查询失败或确认其结果无误。

## 核心公式与解释

起源新增付费分母：统计窗口内，满足DATE(u.target_day)=DATE(u.first_pay_date)的去重xl_id数。

起源新增付费次留分子：同一条件下的画像记录，与活跃事件按app_id、xl_id关联，活跃日相对target_day的DATE_DIFF＋1＝2，再统计去重活跃xl_id。

因此它不直接要求“register_day等于支付成功事件日期”。target_day能否当作注册日、first_pay_date是否表示同一业务口径的成功首充，都要独立核验。此前画像检查已确认target_day并不总等于register_day。

原报告次留分母：8月register_day当天存在pay_success成功支付的去重user_id；次日回访在view_user_version_daily里按user_id匹配。新增付费条件在原SQL中不额外要求is_first_buy=true；历史首次付费另有独立分支。

| 比较项 | 起源模板 | 原报告SQL | 影响 |
| --- | --- | --- | --- |
| 新增付费人群 | DATE(target_day)=DATE(first_pay_date) | register_date=成功支付日期，pay_success | 起点字段不同；是否首充条件不同，不能视为同一群体 |
| 新增付费去重单位 | COUNT(DISTINCT xl_id) | 按user_id建立一人一行 | xl_id与user_id映射尚待核验，分母可能不同 |
| 回访关联 | app_id + xl_id | user_id；早期SQL未显式限定app_id | 缺失user_id的活跃事件可能仍有xl_id；原查询范围也需限定90006 |
| 回访记录 | view_metaevent_active_events | view_user_version_daily | 不是BigQuery平台差异，而是业务活跃定义与覆盖差异 |
| 次留／7日留 | DATE_DIFF+1=2／7 | 起点+1天／+6天 | 对同一起点而言日期偏移一致 |
| 两周观察日 | 15日留：起点+14天 | 第14日：起点+13天 | 相差一天，应重算相同观察日后比较 |
| 渠道筛选 | download_channel IN ($CHANNEL_PACKAGE$) | first_client_type=3且排除3个PWA候选渠道 | 所选分包与全部H5集合不同；需取得参数实际值 |
| 首次付费留存 | 分母：view_event_pay首充标记下去重user_id；分子：活跃xl_id | 成功订单首充标记+画像首充日；分子分母都按user_id | 起源首充指标自身也须核验xl_id与user_id的一致性 |
| 未达观察时长 | 活跃读取到结束日+59；未显式标记达标分母 | 原先以日活日期存在判断eligible | 两者都需补完整性和观察日门禁，界面0不可直接视为真实零 |
| 新增付费率 | 分子是首日首充xl_id数；分母是注册事件user_id数 | 注册日成功付费user_id数／注册画像user_id数 | 来源和计数单位均不同；付费率不能直接对账 |
| LTV／C-T | track_hfyl.user_ltv的ltv_n-audit_n，data_type=1，除以新增xl_id数 | 独立H5联运生命周期来源 | 起源此列是新增群体的累计C-T均值，不是付费群体专属LTV |

## 对H5结果的影响与修正顺序

1. 先对齐起源的参数值：日期、分包渠道、应用及启用的归因筛选。不要将当前选择的wajebetH5与全部H5汇总直接比较。
2. 以同一小窗口逐层对账：target_day与register_day、首日首充与注册当日成功支付、xl_id与user_id；统计两类标识映射的一对多、多对一和缺失情况，全部只输出聚合。
3. 固定同一群体及同一关联键，再单独比较业务活跃事件与用户日活表，从而量化每项算法差异；不要同时修改所有条件后把差额归给某一项。
4. 次留与7日可按相同日期偏移对齐；15日留需要与第15日比较，不能继续与第14日混用。
5. 起源首充留存的分子使用xl_id、分母使用user_id，须验证两者在选中群体的一致性；未达口径的零值暂不进入结论。

**当前结论：原报告19.2%／8.0%／4.7%与起源渠道表不具备直接可比性。** 已确认上述算法不同，但尚未量化各差异的独立贡献。此次为静态SQL审查，未执行模板、未扩大查询窗口、未修改原报告。