"""Only derive adjacent-day rate decline where the cohort is identical."""
import base64,gzip,json,re,shutil,copy
from pathlib import Path
P=Path(__file__).resolve().parent;R=P/'revisions/2026-09-10-decay';R.mkdir(parents=True,exist_ok=True)
H=P/'prior_report.html'
if not (R/'before.html').exists():shutil.copy2(H,R/'before.html')
s=H.read_text();m=re.search(r'<template id="data-analytics-portable-artifact-payload-source"[^>]*>(.*?)</template>',s,re.S)
a=json.loads(gzip.decompress(base64.b64decode(m.group(1).strip())));rows=a['snapshot']['datasets']['new_curve'];data=[]
for p in sorted(set(r['platform'] for r in rows)):
    rs={r['day_number']:r for r in rows if r['platform']==p}
    for d in (3,4):
        x,y=rs[d-1],rs[d]
        for k in ['eligible_users','eligible_cohort_start','eligible_cohort_end']:assert x[k]==y[k]
        assert x['eligible_cohort_end']=='2026-08-31'
        px=x['retained_users']/x['eligible_users'];py=y['retained_users']/y['eligible_users']
        data.append({'platform':p,'interval':f'第{d-1}→{d}日','decline':(px-py)/px,'before_rate':px,'after_rate':py,'difference_pp':(px-py)*100,'eligible_users':x['eligible_users']})
a['snapshot']['datasets']['new_decay_comparable']=data
chart=copy.deepcopy(next(c for c in a['manifest']['charts'] if c['id']=='new_curve'))
chart.update(id='new-decay',title='8月新增付费用户：相邻日留存率衰减（已统一批次部分）',subtitle='8月1—31日注册当日付费用户；衰减率＝（前一日留存率−当日留存率）÷前一日留存率。',showDescription=True,type='bar',dataset='new_decay_comparable',labels={'values':'all'})
chart['encodings']['x'].update(field='interval',type='nominal',label='相邻观察日')
chart['encodings']['y'].update(field='decline',label='留存率相对衰减',format='percent')
a['manifest']['charts'].append(chart)
lines=['### 8月新增付费用户：逐日衰减补充（部分完成）','**衰减率表示留存比例相对前一日下降了多少。** 采用同一批8月1—31日注册当日付费用户，计算（前一日留存率−当日留存率）÷前一日留存率。回访允许发生在任意端；这一变化不等于前一天活跃用户中有多少人次日流失。']
for period in ['第2→3日','第3→4日']:
    group=[r for r in data if r['interval']==period]
    lines.append('**'+period+'：** '+'；'.join(r['platform']+'衰减**'+f"{r['decline']*100:.1f}%"+'**' for r in group)+'。')
lines.append('**第5—14日待统一批次重算。** 原曲线从第5日起使用不同成熟批次；需固定为8月1—21日起点用户后补齐第2—14日数据。当前保存结果为月度汇总，BigQuery授权尚未恢复，未将不同批次直接相除。数据截止沿用2026年9月3日。')
body='\n\n'.join(lines)
table='### 可比区间明细\n\n| 平台分组 | 区间 | 成熟样本 | 前日留存率 | 当日留存率 | 下降百分点 | 相对衰减率 |\n| --- | --- | --- | --- | --- | --- | --- |\n'
for r in data:table+=f"| {r['platform']} | {r['interval']} | {r['eligible_users']:,} | {r['before_rate']*100:.2f}% | {r['after_rate']*100:.2f}% | {r['difference_pp']:.2f} | {r['decline']*100:.1f}% |\n"
i=next(i for i,b in enumerate(a['manifest']['blocks']) if b.get('chartId')=='new_curve')
a['manifest']['blocks'][i+1:i+1]=[{'id':'new-decay-story','type':'markdown','body':body,'sourceId':'paid-cohorts'},{'id':'new-decay-chart','type':'chart','chartId':'new-decay'},{'id':'new-decay-detail','type':'markdown','body':table,'sourceId':'paid-cohorts'}]
(R/'artifact.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
(R/'report.css').write_text((P/'revisions/2026-09-10-long-summary/report.css').read_text())
(R/'calculations.json').write_text(json.dumps({'status':'partial','rows':data,'missing':'D5-D14 fixed cohort','blocker':'BigQuery Auth required'},ensure_ascii=False,indent=2))
print(json.dumps(data,ensure_ascii=False))
