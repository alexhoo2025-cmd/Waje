"""Evidence-bounded diagnostic; never changes the original reports or source sheet."""
import json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
compare=json.loads((P/'comparison.json').read_text())
old=json.loads((ROOT/'analysis/all_platform_cohort_value_2026_09_04/paid_retention_server_success_v1/13_paid_retention_server_success_2026-08.json').read_text())['aggregate_rows']
detail=[r for r in old if r['payer_group'].startswith('新增付费') and r['platform'].startswith('H5') and r['breakdown']=='包与渠道' and r['day_number']==2]
total=next(r for r in old if r['payer_group'].startswith('新增付费') and r['platform'].startswith('H5') and r['breakdown']=='平台' and r['day_number']==2)
assert total['retained_users']==6971 and total['eligible_users']==36356
assert abs(total['retained_users']/total['eligible_users']*100-19.1742765980856)<1e-9
top=sorted(detail,key=lambda r:r['eligible_users'],reverse=True)[:3]
distribution=[{'渠道':r['channel'],'付费人数':r['eligible_users']} for r in top]+[{'渠道':'其他H5渠道','付费人数':total['eligible_users']-sum(r['eligible_users'] for r in top)}]
table=[]
for r in compare:
    m=next(m for m in r['results'] if m['weight']=='新增付费人数' and m['field']=='次留' and m['end_day']==31)
    table.append({'来源':r['sheet'],'付费人数':int(m['denominator']),'8月次留':f"约{m['weighted_pct']:.1f}%",'说明':'按每日新增付费人数加权；源表百分比已四舍五入'})
table.append({'来源':'原报告H5汇总','付费人数':36356,'8月次留':'19.2%','说明':'6,971÷36,356；渠道集合及付费人群尚待跨来源核验'})
sources=[{'id':'sheet','label':'新包新增用户分析，revision 791','href':'https://ksg964l11fam.sg.larksuite.com/wiki/At8gwdbXUiPa0WkXvKqlSUNKg5d?sheet=GrWEoo','path':'analysis/h5_paid_retention_reconciliation_2026_09_10/comparison.json'}, {'id':'prior','label':'原报告8月成功付费留存聚合','path':'analysis/all_platform_cohort_value_2026_09_04/paid_retention_server_success_v1/13_paid_retention_server_success_2026-08.json','query':{'sql':(ROOT/'analysis/all_platform_cohort_value_2026_09_04/sql/13_paid_retention_server_success_2026-08.sql').read_text(),'engine':'BigQuery','metric_definitions':['付费人数为注册当日存在pay_success成功支付的用户；留存为账号任意端日活'],'tables_used':['wajenigeria.origin_hfyl.view_metaevent_order','wajenigeria.origin_hfyl.user_events','wajenigeria.origin_hfyl.view_user_version_daily']}}]
title='H5付费用户留存核验｜人群与来源差异'
blocks=[{'id':'title','type':'markdown','body':'# '+title}, {'id':'summary','type':'markdown','body':'## 执行摘要\n\n**SQL筛选的是成功付费用户，并非全部注册用户；但人群与渠道表是否一致尚未确认。** 原报告将注册日与支付成功日期相等作为新增付费条件；历史首次付费另有首充标记与画像日期条件。\n\n**19.2%的除法成立，业务含义尚未通过跨来源核验。** 原结果为6,971名回访用户÷36,356名符合SQL条件的付费用户。三张渠道表的8月次留均高于19.2%，应优先核验分母人群、渠道映射和回访覆盖。\n\n**不能将渠道表的高值直接替换为报告结果。** 两边渠道集合、人数不同，且7日/15日字段须核对日期偏移。BigQuery当前Auth required，未重新查询。'}, {'id':'compare','type':'markdown','body':'## 1｜先比较付费人数和次留\n\n以下仅定位来源差异，不作为同口径排名。三张子表均读取8月1—31日31条数据；次留按“新增付费人数”加权，未使用“新增人数”作权重。源表为展示率，复算结果标注为约数。'}, {'id':'compare-table','type':'table','tableId':'compare'}, {'id':'mix-note','type':'markdown','body':'## 2｜报告还包含其他H5渠道\n\n原报告H5分母36,356人并非上述三张子表简单合计。其最大渠道PAWAJEBETH5为14,159人，次留25.6%；PAWAJEH5为10,523人，次留10.1%。因此，不能仅凭三张子表都高于19.2%就证明算术加权错误。\n\n**疑点还存在于近似对应渠道内部。** WAJEBETH5子表8月新增付费13,471人、加权次留约46.5%；原报告PAWAJEBETH5为14,159人、25.6%。渠道名称关系需要核实，即使暂按对应关系比较，也显示人群和回访结果均未对齐，不能只用渠道组合解释。'}, {'id':'mix-chart','type':'chart','chartId':'mix'}, {'id':'next','type':'markdown','body':'## 3｜必须确认的付费人群契约\n\n- 新增付费：确认渠道表是否也要求注册当天支付成功，而非注册后累计成为付费用户。\n- 首次付费：确认是首充当天起点，还是注册批次中发生首充的用户；两者不可混用。\n- 回访：确认观察日活跃范围、身份关联及是否要求再次付费。\n- 渠道：逐一核对实际包体、媒体、渠道码和排除项。\n- 日期：报告第7日为起点后6天，第14日为起点后13天；表中的“7日留”“15日留”须查算法后对齐。\n\n**完成上述核验前，19.2%／8.0%／4.7%及其支撑的H5偏低结论应视为待核验。** 本次仅做诊断，未修改原飞书、原HTML或电子表格。'}]
a={'surface':'report','manifest':{'version':1,'surface':'report','title':title,'description':'原始人群筛选与跨来源差异审查；未完成线上重查','sources':sources,'blocks':blocks,'cards':[],'charts':[{'id':'mix','title':'原报告H5新增付费人数构成','type':'bar','dataset':'distribution','sourceId':'prior','encodings':{'x':{'field':'渠道','type':'nominal'},'y':{'field':'付费人数','type':'quantitative','format':'number','unit':'人','label':'付费人数（人）'}},'labels':{'values':'all'},'settings':{'sort':'none'}}],'tables':[{'id':'compare','title':'8月付费人群次留：来源核对','dataset':'comparison','sourceId':'sheet','columns':[{'field':f,'label':f,'type':'number' if f=='付费人数' else 'text'} for f in table[0]],'density':'spacious'}]},'snapshot':{'status':'partial','datasets':{'distribution':distribution,'comparison':table}}}
a['snapshot'].update(version=1,generatedAt='2026-09-10T19:37:00+08:00')
a['manifest']['sources'].append({'id':'comparison-source','label':'渠道表与原报告聚合交叉核验','path':'analysis/h5_paid_retention_reconciliation_2026_09_10/build_audit.py','query':{'description':'从飞书revision791的三张H5子表按新增付费人数加权，与原报告8月成功付费聚合并列检查；两边口径未对齐，不作为排名。','tables_used':['analysis/h5_paid_retention_reconciliation_2026_09_10/comparison.json','analysis/all_platform_cohort_value_2026_09_04/paid_retention_server_success_v1/13_paid_retention_server_success_2026-08.json']}})
a['manifest']['sources'][-1]['query']['sql']=sources[1]['query']['sql']
a['manifest']['sources'][-1]['query']['description']+=' 所附SQL仅为原报告来源；渠道表值来自飞书读取，跨来源加权与并列由本地Python完成，未执行新SQL。'
a['manifest']['tables'][0]['sourceId']='comparison-source'
(P/'artifact.json').write_text(json.dumps(a,ensure_ascii=False,indent=2))
(P/'核验摘要.md').write_text('\n\n'.join(b.get('body','') for b in blocks if b['type']=='markdown'))
