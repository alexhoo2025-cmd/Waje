import csv,datetime,json
from pathlib import Path
P=Path(__file__).resolve().parent;d=json.loads((P/'analysis.json').read_text());mapping=json.loads((P/'channels.json').read_text())
short={'WajeSpecial-facebook':'APP·Facebook','WajeSpecial-googleadwords_int':'APP·Google广告','WajeSpecial-Google商店':'APP·Google商店','WAJEIOS-AppStore商店':'iOS·App Store','WAJEBETH5':'WajeBet H5','wajeH5-facebook':'H5·Facebook','wajeH5ga-googlewords_int':'H5·Google广告','PWA':'PWA·Facebook','APP':'APP（4渠道）','H5':'H5（3渠道）','PWA候选':'PWA候选（1渠道）'}
get=lambda u,p,n,mode='各日达标范围':next(r for r in d['retention'] if r['unit']==u and r['population']==p and r['day']==n and r['sample_mode']==mode)
sm=lambda u:next(r for r in d['summary'] if r['unit']==u)
f=lambda n:f'{n:,.0f}'
pct=lambda n:f'{n:.1f}%'
title='8月付费用户留存与价值分析｜起源口径重查版'
source={'id':'origin','label':'BigQuery按起源公式重新查询；观察截至2026年9月9日','path':'analysis/origin_paid_retention_rebuild_2026_09_10/analysis.json','query':{'engine':'BigQuery + aggregate-only Python recomputation','sql':(P/'05_full_origin_returns.sql').read_text(),'description':'复用起源target_day/first_pay_date/xl_id定义；合并等价事件UNION，仅改变扫描方式。月度分子分母由每日互斥批次汇总；首充用户分母和注册用户分母来自06查询，C-T来自09查询，再由analyze.py计算。','tables_used':['wajenigeria.origin_hfyl.user_events','wajenigeria.origin_hfyl.view_metaevent_active_events','wajenigeria.origin_hfyl.view_event_pay','wajenigeria.origin_hfyl.view_event_register','wajenigeria.track_hfyl.user_ltv','wajenigeria.ares_hfyl.app_channel_media_package'],'supporting_queries':[{'path':str(q.relative_to(P.parents[1])),'sql':q.read_text()}for q in [P/'01_origin_denominators.sql',P/'06_origin_reg_first.sql',P/'07_key_overlap.sql',P/'09_origin_ct.sql']],'metric_definitions':['新增付费留存=同日起点首充标识的观察日活跃xl_id数/对应起点去重xl_id数','首次付费留存=首充起点观察日活跃xl_id数/对应起点成功首充user_id数，沿用起源混合计数单位','累计C-T每新增标识=SUM(ltv_N-audit_N)/新增xl_id，报表原单位','衰减率=(前日留存率-当日留存率)/前日留存率；固定批次内计算']}}
m={'version':1,'surface':'report','title':title,'description':'8个选定渠道｜8月起点｜观察截至9月9日｜旧报告独立保留','sources':[source],'blocks':[],'charts':[],'tables':[],'cards':[],'reportContract':{'type':'business','language':'zh','population':'起源八个选定渠道；新增付费为画像起点日=首充日按xl_id去重；首次付费沿用起源支付事件user_id分母','period':'8月1—31日起点；截至2026-09-09；15日到8/26，30日到8/11；固定曲线8/1—26日','timezone':'Africa/Lagos业务日；沿用源表target_day日期字段','metrics':[],'assertions':[]}}
ds={};css=[':root{--app:#eaf3ff;--h5:#fff1e5;--pwa:#f1edfa;--peak:#fff0bf;}@media(prefers-color-scheme:dark){:root{--app:#20384f;--h5:#453426;--pwa:#342d46;--peak:#5b4520;}}','.chart-bar-value-label{font-size:10px!important;}']
def md(id,text):m['blocks'].append({'id':id,'type':'markdown','body':text,'sourceId':'origin'})
def table(id,title,rows):
    ds[id]=rows;m['tables'].append({'id':id,'title':title,'dataset':id,'sourceId':'origin','density':'spacious','columns':[{'field':k,'label':k,'type':'number' if isinstance(v,(int,float)) else 'text','format':'number'}for k,v in rows[0].items()]});m['blocks'].append({'id':id+'-block','type':'table','tableId':id})
def chart(id,title,rows,x,fields,unit,subtitle):
    rows=[{k:(round(v,1)if k in fields and isinstance(v,(int,float))else v)for k,v in row.items()}for row in rows]
    ds[id]=rows;m['charts'].append({'id':id,'title':title,'subtitle':subtitle,'showDescription':True,'type':'bar','dataset':id,'sourceId':'origin','layout':'full','encodings':{'x':{'field':x,'type':'nominal'},'y':{'fields':fields,'type':'quantitative','format':'number','unit':unit,'label':unit}},'labels':{'values':'all'},'legend':{'position':'bottom'},'settings':{'sort':'none','categoryLabelPolicy':'wrap'},'palette':{'kind':'categorical','name':'blue-gold-orange-olive'}});m['blocks'].append({'id':id+'-block','type':'chart','chartId':id})
md('title','# '+title)
md('summary','''## 执行摘要

**按起源口径重查，选定H5渠道的新增付费回访明显高于旧稿数值。** 次日／第7日／第15日：APP四渠道为**54.3%／21.4%／13.5%**，H5三渠道为**39.3%／12.7%／6.7%**。这是算法和渠道范围重新对齐后的结果，不能把与旧稿的差额解释为业务增长。

**H5内部应优先排查Facebook渠道。** H5 Facebook次留**27.1%**、7日留存**7.0%**；WajeBet H5为**46.5%／16.1%**，H5 Google为**45.7%／15.0%**。同属H5的差异较大，应先按来源渠道和付费后路径定位。

**APP优势同时体现在规模与较长期回访。** 选定APP渠道新增付费标识**52,453个**，H5为**25,722个**；8月1—11日起点的第30日回访分别为**8.4%和3.9%**。两类付费人群继续分开统计，不互相替代。

**价值参考采用同一C-T公式，但不属于付费群体专属LTV。** 第15日累计C-T／新增标识，选定APP渠道约**522.45**、H5约**188.66**（报表原单位）。后续应结合人群构成和投放成本评估，不直接视为净收益或投放回报。''')
md('scope','''## 1｜本次比较范围与统计口径

**只看8月起点，观察截至2026年9月9日。** APP由3个WajeSpecial媒体渠道及iOS App Store组成；H5包括WajeBet H5、H5 Facebook、H5 Google；PWA Facebook单列。下文APP／H5均指这些选定渠道，不代表全平台或实际回访端。

- **新增付费：** 画像日期target_day与first_pay_date相同，按xl_id去重。为便于阅读简称“新增付费”，不再混同为按register_day筛选的注册当日付费账号。
- **全部新增：** 画像起点target_day在8月，按xl_id去重，包含未付费标识；不等同于注册事件账号。
- **首次付费：** 起点为首充日；分母是支付成功且带首充标记的去重user_id，回访分子按xl_id计数，保留起源原公式。
- **回访：** 业务活跃事件按app_id＋xl_id关联，允许发生在任意端。第1日为起点日；次留为第2日，7日留为第7日，15日留为第15日。
- **达标范围：** 次日与第7日纳入8月全月；第15日到8月26日，第30日到8月11日。8月第60日未达到统计口径，本版不展示；不再展示第90日。

固定批次图统一使用8月1—26日起点。各观察日最大达标范围的表格与固定批次图用途不同，均就近标明。

**数据状态：** 三类活跃事件在8月1日至9月9日的分区均无缺日，客户端仍有回补。本版为截至9月9日的查询快照，不代表来源已经封账。''')
md('overall','''## 2｜先看规模：APP较大，H5付费群体回访高于全部新增

按本次八渠道去重检查，xl_id及非空user_id未发现跨渠道重复，可分别汇总；两类付费人群之间有重叠，不能相加。新增付费与全部新增使用同一xl_id口径：选定APP次留为54.3%对26.5%，H5为39.3%对11.0%。这属于人群差异，不能解释为付费本身提高留存。

起源“新增付费率”＝新增付费xl_id数÷注册事件user_id数；首充率＝首充user_id数÷注册事件user_id数。两项均沿用来源公式，新增标识数不作这两项比例的分母。''')
table('scale','选定渠道规模与起源付费率',[{'范围':short[u],'新增标识数':sm(u)['new_xl_ids'],'注册事件账号数':sm(u)['registered_user_days'],'新增付费标识数':sm(u)['new_paid_xl_ids'],'历史首充账号数':sm(u)['first_pay_user_days'],'新增付费率':pct(sm(u)['new_paid_rate_pct']),'首充付费率':pct(sm(u)['first_pay_rate_pct'])}for u in d['groups']])
table('new-vs-paid','全部新增与新增付费：同口径回访比较',[{'范围':short[u],'人群':pop,'8月分母':get(u,pop,2)['denominator'],**{f'第{n}日':pct(get(u,pop,n)['rate_pct'])for n in [2,7,15]},'第15日分母':get(u,pop,15)['denominator']}for u in d['groups']for pop in ['全部新增','新增付费']])
chart('group-retention','新增付费回访：选定渠道汇总',[{'范围':short[u],**{f'第{n}日':get(u,'新增付费',n)['rate_pct']for n in [2,7,15]}}for u in d['groups']],'范围',['第2日','第7日','第15日'],'回访率（%）','次日／第7日为8月全月，第15日为8月1—26日；按各日达标分母计算。')
md('channels','''## 3｜H5内部差异较大，Facebook渠道应优先核查

H5 Facebook贡献三条H5渠道约**36.9%**的新增付费标识，但第7日留存仅**7.0%**；WajeBet H5和H5 Google分别为**16.1%和15.0%**。应优先比较入口、首日游戏参与、支付体验和再次访问方式，而不是将H5整体视为同一种用户质量。

APP侧Google广告、Google商店与iOS App Store的新增付费第7日留存在21.8%—23.1%，APP Facebook为16.4%。这些是渠道相关差异，尚未控制投放策略与用户构成。''')
for pop,tid in [('新增付费','new-paid'),('首次付费','first-paid')]:
    table(tid,pop+'：八渠道核心数据',[{'渠道':short[r['sheet']],'8月分母':get(r['sheet'],pop,2)['denominator'],**{f'第{n}日':pct(get(r['sheet'],pop,n)['rate_pct'])for n in [2,7,15,30]},'第15日分母':get(r['sheet'],pop,15)['denominator'],'第30日分母':get(r['sheet'],pop,30)['denominator']}for r in mapping])
chart('channel-d7','第7日回访：两类付费人群',[{'渠道':short[r['sheet']],**{pop:get(r['sheet'],pop,7)['rate_pct']for pop in ['新增付费','首次付费']}}for r in mapping],'渠道',['新增付费','首次付费'],'回访率（%）','8月全月起点；首次付费沿用起源分子xl_id／分母user_id的公式。')
md('first-note','''**历史首充群体也呈现相似的渠道差异。** 选定APP的次日／7日／15日为54.3%／22.6%／14.8%，H5为41.5%／14.4%／8.3%。这两类群体定义及计数单位不同，分别展示，不将差额解释为同一用户随生命周期发生的变化。''')
md('fixed','''## 4｜固定起点批次，定位前几日衰减

以下统一使用8月1—26日起点，平台内各观察日分母保持一致，已去除旧版曲线的样本日期范围变化影响。关键观察日用柱形图直接标数值，完整逐日读数附在明细中。

衰减率＝（前一日回访率－当日回访率）÷前一日回访率；第2日相对起点100%基准。它描述比例变化，不是前一天活跃用户的次日个体流失率。优先检查起点到次日及随后两三天，再追踪首周和两周表现。''')
chart('fixed-key','固定批次新增付费：关键观察日',[{'观察日':f'第{n}日',**{short[u]:get(u,'新增付费',n,'固定8月1—26日')['rate_pct']for u in d['groups']}}for n in [2,3,7,15]],'观察日',[short[u]for u in d['groups']],'回访率（%）','共同起点8月1—26日；同一范围、同一分母。')
chart('h5-decay','H5选定渠道：固定批次逐日衰减',[{'观察日':f'第{r["day"]}日','衰减率':r['rate_pct']}for r in d['decay'] if r['unit']=='H5' and r['population']=='新增付费'],'观察日',['衰减率'],'相对衰减率（%）','8月1—26日新增付费；与前一观察日比较，正值表示下降。')
md('decay-note','''**固定批次仍显示前两次回访是重点。** H5第2日相对起点下降60.7%，第3日相对第2日再下降41.0%；APP对应为45.8%和31.5%。应优先核查付费后到次日、以及次日到第3日的访问路径。该结果是比例变化，不能直接认定某项产品体验导致流失。''')
table('decay-detail','固定批次：新增付费逐日衰减',[{'观察日':f'第{n}日',**{short[u]:pct(next(r['rate_pct']for r in d['decay'] if r['unit']==u and r['population']=='新增付费' and r['day']==n))for u in d['groups']}}for n in range(2,16)])
md('value','''## 5｜同公式价值参考：APP累计C-T／新增标识更高

按起源“累计利润(C-T)”公式，选定APP第15日为**522.45**，H5为**188.66**，PWA候选渠道为**409.51**；第30日分别为**731.11／229.21／468.83**。同一观察日使用相同起点日期范围，APP的该项均值更高。

该指标来自track_hfyl.user_ltv，按data_type=1累计ltv_N−audit_N后除以新增xl_id数，金额沿用报表原单位。它属于全部新增群体的价值参考，不是付费用户专属LTV，也没有纳入本报告未取得的投放成本。第15日和第30日的起点范围不同，不直接计算同批价值增长。

**价值指标暂作辅助参考。** 渠道媒体按当前字典映射；与来源表旧快照的1,344项可比字段中，1,287项差异不超过0.02报表单位，其余差异尚未逐项归因。不据此单独形成资源投入结论；APP／H5付费群体专属LTV仍未取得。''')
chart('ct-value','累计C-T／新增标识',[{'范围':short[u],**{f'第{n}日':next(r['mean_ct']for r in d['value']if r['unit']==u and r['day']==n)for n in [15,30]}}for u in d['groups']],'范围',['第15日','第30日'],'报表原单位／新增标识','第15日：8月1—26日；第30日：8月1—11日。')
table('ct-detail','八渠道累计价值参考',[{'渠道':short[r['sheet']],**{f'第{n}日C-T／新增标识':f"{next(v['mean_ct']for v in d['value']if v['unit']==r['sheet'] and v['day']==n):,.2f}"for n in [15,30]}}for r in mapping])
md('actions','''## 6｜总结建议

1. **先排查H5 Facebook，再推广有效路径。** 与WajeBet H5、H5 Google比较首日付费后的再次访问入口、游戏参与和首周体验；用固定批次的次日、7日、15日持续评估。
2. **APP Facebook单独优化。** 同属APP，其7日回访低于Google广告、Google商店和iOS App Store；先控制渠道构成与投放条件，再判断产品原因。
3. **留存与价值联合观察。** 同时看新增付费规模、固定批次回访和同公式C-T，不因单一高比例或较高均值直接调整资源。
4. **本版替代旧稿的统计结论，而非展示业务环比。** 本次按起源重查并重新定义渠道范围，旧6、7月和旧H5 19.2%结果仅归档，不参与本版趋势比较。

核验说明：八渠道新增付费人数与参考表合计一致，次留差异在展示精度内；首次付费结果较早期快照存在小幅修订。参考表部分百分数以小数形式保存，已统一尺度后比较。源数据会回补，以上为本次查询快照。''')
# Full numerator/denominator records remain downloadable and source-backed.
with (P/'留存分子分母与范围.csv').open('w',newline='',encoding='utf-8-sig') as out:
    w=csv.DictWriter(out,fieldnames=list(d['retention'][0]));w.writeheader();w.writerows(d['retention'])
with (P/'八渠道规模与价值.csv').open('w',newline='',encoding='utf-8-sig') as out:
    w=csv.DictWriter(out,fieldnames=list(d['summary'][0]));w.writeheader();w.writerows(d['summary'])
for t in m['tables']:
    # Source rows and numeric fields preserved; CSS styles only the fixed presentation order.
    css.append(f'[data-artifact-id="{t["id"]}"] table{{width:100%!important;}}')
css.append('#summary{border:1px solid #82a7fc;border-left:5px solid #4e96da;border-radius:14px;}')
a={'surface':'report','manifest':m,'snapshot':{'version':1,'generatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'partial','datasets':ds}}
if (P/'final-qa.json').exists():
    audit=json.loads((P/'final-qa.json').read_text())
    source['query']['executed_at']=next(j['ended']for j in audit['jobs']if j['sql']=='05_full_origin_returns.sql')
    source['query']['description']+=' 查询时间与扫描回执见同目录final-qa.json；当前版保留持续回补和价值参考差异限制。'
(P/'artifact.json').write_text(json.dumps(a,ensure_ascii=False,indent=2));(P/'report.css').write_text('\n'.join(css))
def markdown_table(rows):
    keys=list(rows[0]);escape=lambda v:str(v).replace('|','\\|').replace('\n',' ')
    return '\n'.join(['| '+' | '.join(keys)+' |','| '+' | '.join(['---']*len(keys))+' |']+['| '+' | '.join(escape(row.get(k,''))for k in keys)+' |'for row in rows])
markdown=[]
for block in m['blocks']:
    if block['type']=='markdown':markdown.append(block['body'])
    else:
        key=block.get('tableId',block.get('chartId'))
        spec=next(s for s in m['tables']+m['charts']if s['id']==key)
        markdown.append('### '+spec['title']+'\n\n'+spec.get('subtitle','')+'\n\n'+markdown_table(ds[key]))
(P/'报告.md').write_text('\n\n'.join(markdown))
(P/'chart-map.json').write_text(json.dumps([{'id':c['id'],'family':c['type'],'question':c['title'],'purpose':'Discrete comparable periods or category comparison; not an interpolated trend','dataset':c['dataset']}for c in m['charts']],ensure_ascii=False,indent=2))
print(json.dumps({'blocks':len(m['blocks']),'charts':len(m['charts']),'tables':len(m['tables'])}))
