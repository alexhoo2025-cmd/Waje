"""Validate and report the live same-source comparison without certifying coverage."""
import json,math
from pathlib import Path
P=Path(__file__).resolve().parent
result=json.loads((P/'02_august_population_comparison.result.json').read_text());rows=result['rows']
get=lambda pop,plat,d,mode='各日达标范围':next(r for r in rows if r['population']==pop and r['platform']==plat and r['day_number']==d and r['sample_mode']==mode)
for r in rows:
    assert r['retained_users'] is None or 0<=r['retained_users']<=r['eligible_users']<=r['cohort_users']
    if r['retention_rate'] is not None:assert abs(r['retention_rate']-r['retained_users']/r['eligible_users'])<1e-12
    if r['population']=='新增付费用户':
        q=get('全部新增用户',r['platform'],r['day_number'],r['sample_mode']);assert r['eligible_users']<=q['eligible_users'] and r['retained_users']<=q['retained_users']
for pop in ['全部新增用户','新增付费用户']:
    for mode in ['各日达标范围','固定8月1—27日']:
        days=list(range(2,15)) + ([30] if mode=='各日达标范围' else [])
        for day in days:
            app,android,ios=[get(pop,p,day,mode) for p in ['APP（Android+iOS）','Android','iOS']]
            for k in ['cohort_users','eligible_users','retained_users']:assert app[k]==android[k]+ios[k]
        if mode=='固定8月1—27日':
            for plat in set(r['platform'] for r in rows):assert len({get(pop,plat,d,mode)['eligible_users'] for d in days})==1
table=[];chart=[];detail=[]
for plat in ['APP（Android+iOS）','Android','iOS','H5（不含PWA候选渠道）','PWA候选渠道']:
    for pop in ['全部新增用户','新增付费用户']:
        rs=[get(pop,plat,d) for d in [2,7,14]]
        table.append({'平台':plat,'人群':pop,'8月人数':rs[0]['cohort_users'],'次日':f"{rs[0]['retention_rate']*100:.1f}%",'第7日':f"{rs[1]['retention_rate']*100:.1f}%",'第14日':f"{rs[2]['retention_rate']*100:.1f}%",'第14日分母':rs[2]['eligible_users']})
        detail.extend({'平台':plat,'人群':pop,'观察日':r['day_number'],'分母':r['eligible_users'],'回访人数':r['retained_users'],'起点截至':r['eligible_cohort_end']} for r in rs)
    if plat!='PWA候选渠道':chart.append({'平台':plat,'全部新增用户':get('全部新增用户',plat,2)['retention_rate']*100,'新增付费用户':get('新增付费用户',plat,2)['retention_rate']*100})
source={'id':'live','label':'2026-09-10官方BigQuery客户端重新查询','path':'analysis/paid_retention_aug_refresh_2026_09_09/02_august_population_comparison.result.json','query':{'sql':(P/'02_august_population_comparison.sql').read_text(),'engine':'BigQuery','tables_used':['wajenigeria.origin_hfyl.user_events','wajenigeria.origin_hfyl.view_metaevent_order','wajenigeria.origin_hfyl.view_user_version_daily'],'description':'app_id=90006；画像和支付限制8月；回访截至9月9日。分母人群基于8月画像分区且注册日也在8月，不能视为已证明覆盖所有跨月画像记录。','executed_at':'2026-09-10','job_id':result['job_id']}}
title='8月新增与新增付费留存重查｜同源对比及覆盖问题'
body=[('title','# '+title),('summary','## 执行摘要\n\n**同一底表及日活来源下，新增付费用户的回访率高于全部新增用户。** APP次日为49.6%对19.8%；H5为19.2%对4.4%。这说明H5的19.2%不是误取了全部新增用户回访率；付费用户是全部新增用户的子集，差异不表示付费造成留存提高。\n\n**但H5日活来源存在明显覆盖差异，当前数值不能直接认证为最终业务留存。** 8月1日H5新增付费用户1,161人，次日在原日表匹配到201人、在业务活跃事件视图匹配到377人，176名事件回访用户未出现在日表中。\n\n**未直接覆盖原报告。** 下表是新执行查询的观察结果；业务活跃事件口径的全月重算预估11.78GiB，超过单条5GiB限制，未执行。'),('scope','## 1｜本次如何对齐\n\n仅查询Waje app_id=90006。画像与成功支付窗口为8月1—31日；支付要求pay_success且有订单号。新增付费为注册当日成功支付，全体新增包含其子集。使用相同首平台分类，PWA候选单列，账号回访允许发生在任意端。\n\n次日、第7日覆盖8月全月，第14日覆盖8月1—27日；固定批次2—14日结果另外保留在查询附件。日表每个日期均有记录，但这不证明H5回访覆盖完整。'),('findings','## 2｜先区分人群差异，再判断数据覆盖\n\n下图只比较同一来源内次日观察结果：APP与各子端的新增付费用户均高于全部新增用户。不同人群在付费意愿、渠道和体验上可能不同；H5两组同时偏低，需要继续核查日活来源，而不是只改分母标签。'),('risk','## 3｜已发现的两项质量问题\n\n**日活来源不一致。** 单日同一H5付费群体中，原日表201÷1,161＝17.3%，业务活跃事件377÷1,161＝32.5%；不能把单日32.5%外推全月，也不能尚未对齐就替换报告19.2%。原日表中的201人都出现在事件回访用户中。\n\n**画像分区日并非总与注册日期相同。** 8月画像分区有976,329名用户，其中25,228行注册日期在8月之外、139行注册日期缺失。本次已排除这些记录，但仍需确认是否存在8月注册、画像分区却在窗口外的用户。查询结果是当前有界底表范围，并非已证明注册人群无遗漏。\n\n**后续：** 优先寻找与业务活跃事件同口径的认证聚合源；如需执行预估11.78GiB的全月查询，须先获得明确的扫描上限调整授权。原渠道表的人群、渠道及回访定义也需同步对齐。')]
blocks=[{'id':i,'type':'markdown','body':b} for i,b in body[:3]]
blocks+=[{'id':'table','type':'table','tableId':'comparison'}, {'id':'findings','type':'markdown','body':body[3][1]},{'id':'chart','type':'chart','chartId':'rates'},{'id':'risk','type':'markdown','body':body[4][1]},{'id':'detail','type':'table','tableId':'counts'}]
sources=[source,{'id':'probe','label':'H5单日来源匹配核验','path':'analysis/paid_retention_aug_refresh_2026_09_09/04_h5_activity_source_probe.result.json','query':{'sql':(P/'04_h5_activity_source_probe.sql').read_text(),'engine':'BigQuery','tables_used':['wajenigeria.origin_hfyl.view_metaevent_active_events','wajenigeria.origin_hfyl.view_user_version_daily']} }]
a={'surface':'report','manifest':{'version':1,'surface':'report','title':title,'sources':sources,'cards':[],'blocks':blocks,'charts':[{'id':'rates','type':'bar','title':'同一日活来源下的次日回访率对比','sourceId':'live','dataset':'chart','encodings':{'x':{'field':'平台','type':'nominal'},'y':{'fields':['全部新增用户','新增付费用户'],'type':'quantitative','format':'number','unit':'%','label':'观察回访率（%）'}},'labels':{'values':'all'},'legend':{'position':'bottom'}}],'tables':[{'id':id,'title':ttl,'dataset':id,'sourceId':'live','columns':[{'field':k,'label':k,'type':'number' if isinstance(v,int) else 'text'} for k,v in rr[0].items()]}for id,ttl,rr in [('comparison','8月两类用户：同源回访率与分母',table),('counts','分子分母明细',detail)]]},'snapshot':{'version':1,'generatedAt':'2026-09-10T00:00:00+08:00','status':'partial','datasets':{'comparison':table,'chart':chart,'counts':detail}}}
(P/'comparison-artifact.json').write_text(json.dumps(a,ensure_ascii=False,indent=2));(P/'comparison-validation.json').write_text(json.dumps({'numeric_checks':'passed','fixed_cohort_denominators':'passed','app_subplatform_sum':'passed','population_subset':'passed','source_coverage':'not_certified','source_probe_difference':176,'old_report_updated':False},indent=2))
print(json.dumps(table,ensure_ascii=False))
