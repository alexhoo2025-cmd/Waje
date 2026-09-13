"""Static comparison of user-supplied Origin SQL template and prior executed SQL."""
import datetime,hashlib,json,re,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
attachment=Path('/Users/robin/.codex/attachments/775f368b-b0dc-4ca4-af52-353ec207ad58/pasted-text.txt')
original=attachment.read_text();decoded=json.loads(original)
assert decoded.startswith('SQL:') and 'DB: BIG_QUERY' in decoded
sql,diagnostic=decoded[4:].split('DB: BIG_QUERY',1)
sql=sql.rstrip().removesuffix('\\r\\n').rstrip()
(P/'origin-supplied.txt').write_text(original)
(P/'origin-template.sql').write_text(sql+'\n')
(P/'origin-diagnostic.txt').write_text('DB: BIG_QUERY'+diagnostic)
assert 'COUNT' in sql.upper() and 'DATE(u.target_day) = DATE(u.first_pay_date)' in sql
assert 'a.app_id = u.app_id and a.xl_id = u.xl_id' in sql
comparison=[
{'比较项':'新增付费人群','起源模板':'DATE(target_day)=DATE(first_pay_date)','原报告SQL':'register_date=成功支付日期，pay_success','影响':'起点字段不同；是否首充条件不同，不能视为同一群体'},
{'比较项':'新增付费去重单位','起源模板':'COUNT(DISTINCT xl_id)','原报告SQL':'按user_id建立一人一行','影响':'xl_id与user_id映射尚待核验，分母可能不同'},
{'比较项':'回访关联','起源模板':'app_id + xl_id','原报告SQL':'user_id；早期SQL未显式限定app_id','影响':'缺失user_id的活跃事件可能仍有xl_id；原查询范围也需限定90006'},
{'比较项':'回访记录','起源模板':'view_metaevent_active_events','原报告SQL':'view_user_version_daily','影响':'不是BigQuery平台差异，而是业务活跃定义与覆盖差异'},
{'比较项':'次留／7日留','起源模板':'DATE_DIFF+1=2／7','原报告SQL':'起点+1天／+6天','影响':'对同一起点而言日期偏移一致'},
{'比较项':'两周观察日','起源模板':'15日留：起点+14天','原报告SQL':'第14日：起点+13天','影响':'相差一天，应重算相同观察日后比较'},
{'比较项':'渠道筛选','起源模板':'download_channel IN ($CHANNEL_PACKAGE$)','原报告SQL':'first_client_type=3且排除3个PWA候选渠道','影响':'所选分包与全部H5集合不同；需取得参数实际值'},
{'比较项':'首次付费留存','起源模板':'分母：view_event_pay首充标记下去重user_id；分子：活跃xl_id','原报告SQL':'成功订单首充标记+画像首充日；分子分母都按user_id','影响':'起源首充指标自身也须核验xl_id与user_id的一致性'},
{'比较项':'未达观察时长','起源模板':'活跃读取到结束日+59；未显式标记达标分母','原报告SQL':'原先以日活日期存在判断eligible','影响':'两者都需补完整性和观察日门禁，界面0不可直接视为真实零'},
{'比较项':'新增付费率','起源模板':'分子是首日首充xl_id数；分母是注册事件user_id数','原报告SQL':'注册日成功付费user_id数／注册画像user_id数','影响':'来源和计数单位均不同；付费率不能直接对账'},
{'比较项':'LTV／C-T','起源模板':'track_hfyl.user_ltv的ltv_n-audit_n，data_type=1，除以新增xl_id数','原报告SQL':'独立H5联运生命周期来源','影响':'起源此列是新增群体的累计C-T均值，不是付费群体专属LTV'},
]
for n in ['origin-template.sql','origin-diagnostic.txt']:assert (P/n).stat().st_size>0
evidence={'source_sha256':hashlib.sha256(attachment.read_bytes()).hexdigest(),'source_type':'User-pasted warnings SQL template','parameters':sorted(set(re.findall(r'\$[A-Z_0-9]+\$',sql))),'contains_calcite_parser_warning':'SqlParseException' in diagnostic,'execution_verified':False,'source_original_preserved':True,'comparison':comparison}
(P/'origin-algorithm-comparison.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2))
title='起源与原报告：H5付费留存算法差异'
summary='''## 执行摘要

**已确认存在算法差异，不能用“都是BigQuery”视为同口径。** 起源的新增付费条件为target_day等于first_pay_date，按xl_id去重；原报告按register_day与成功支付日期相同筛选，按user_id去重。

**回访口径也不同。** 起源用app_id＋xl_id关联业务活跃事件视图，原报告用user_id关联用户日活表。此前单日核验已显示日表与业务活跃事件存在覆盖差异，但该探查仍按user_id，尚未完整复现起源的xl_id算法。

**该文件是含参数的SQL模板／诊断文本，尚非已验证的最终执行SQL。** 文件保留3个参数占位符，末尾包含Calcite解析警告。可以确认模板算法，不能仅凭这段警告判断起源整个查询失败或确认其结果无误。'''
meaning='''## 核心公式与解释

起源新增付费分母：统计窗口内，满足DATE(u.target_day)=DATE(u.first_pay_date)的去重xl_id数。

起源新增付费次留分子：同一条件下的画像记录，与活跃事件按app_id、xl_id关联，活跃日相对target_day的DATE_DIFF＋1＝2，再统计去重活跃xl_id。

因此它不直接要求“register_day等于支付成功事件日期”。target_day能否当作注册日、first_pay_date是否表示同一业务口径的成功首充，都要独立核验。此前画像检查已确认target_day并不总等于register_day。

原报告次留分母：8月register_day当天存在pay_success成功支付的去重user_id；次日回访在view_user_version_daily里按user_id匹配。新增付费条件在原SQL中不额外要求is_first_buy=true；历史首次付费另有独立分支。'''
next_steps='''## 对H5结果的影响与修正顺序

1. 先对齐起源的参数值：日期、分包渠道、应用及启用的归因筛选。不要将当前选择的wajebetH5与全部H5汇总直接比较。
2. 以同一小窗口逐层对账：target_day与register_day、首日首充与注册当日成功支付、xl_id与user_id；统计两类标识映射的一对多、多对一和缺失情况，全部只输出聚合。
3. 固定同一群体及同一关联键，再单独比较业务活跃事件与用户日活表，从而量化每项算法差异；不要同时修改所有条件后把差额归给某一项。
4. 次留与7日可按相同日期偏移对齐；15日留需要与第15日比较，不能继续与第14日混用。
5. 起源首充留存的分子使用xl_id、分母使用user_id，须验证两者在选中群体的一致性；未达口径的零值暂不进入结论。

**当前结论：原报告19.2%／8.0%／4.7%与起源渠道表不具备直接可比性。** 已确认上述算法不同，但尚未量化各差异的独立贡献。此次为静态SQL审查，未执行模板、未扩大查询窗口、未修改原报告。'''
blocks=[{'id':'title','type':'markdown','body':'# '+title},{'id':'summary','type':'markdown','body':summary},{'id':'formula','type':'markdown','body':meaning},{'id':'differences','type':'table','tableId':'differences'},{'id':'next','type':'markdown','body':next_steps}]
source={'id':'code','label':'用户提供的起源SQL模板与已执行原报告SQL','path':'analysis/h5_paid_retention_reconciliation_2026_09_10/origin-algorithm-comparison.json','query':{'engine':'Static SQL review','sql':(ROOT/'analysis/all_platform_cohort_value_2026_09_04/sql/13_paid_retention_server_success_2026-08.sql').read_text(),'description':'表格为静态代码审查，不是新增查询结果。所附SQL是此前实际执行的原报告SQL；起源模板见origin-template.sql，含未替换参数及独立诊断警告。未执行用户提供模板。','tables_used':['analysis/h5_paid_retention_reconciliation_2026_09_10/origin-template.sql','analysis/all_platform_cohort_value_2026_09_04/sql/13_paid_retention_server_success_2026-08.sql']}}
a={'surface':'report','manifest':{'version':1,'surface':'report','title':title,'sources':[source],'cards':[],'charts':[],'blocks':blocks,'tables':[{'id':'differences','title':'逐项算法差异','sourceId':'code','dataset':'differences','columns':[{'field':k,'label':k,'type':'text'} for k in comparison[0]],'density':'spacious'}],'reportContract':{'type':'mechanism','language':'zh','population':'SQL算法静态审查；非新增用户统计结果','period':'按用户提供的起源参数化模板及2026-09-04原报告SQL进行比较','timezone':'来源日期类型；具体时区转换另行核验','metrics':[],'assertions':[]}},'snapshot':{'version':1,'generatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'partial','datasets':{'differences':comparison}}}
(P/'algorithm-artifact.json').write_text(json.dumps(a,ensure_ascii=False,indent=2))
md='# '+title+'\n\n'+summary+'\n\n'+meaning+'\n\n| 比较项 | 起源模板 | 原报告SQL | 影响 |\n| --- | --- | --- | --- |\n'+'\n'.join('| '+' | '.join(r.values())+' |' for r in comparison)+'\n\n'+next_steps
(P/'起源SQL算法差异.md').write_text(md)
print(json.dumps({'sql_chars':len(sql),'comparison_rows':len(comparison),'template_not_final_execution':True}))
