"""Display adjacent changes of reported rates; distinguish changing cohorts."""
import base64,gzip,json,re,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;R=P/'revisions/2026-09-10-daily-decay-observed';R.mkdir(parents=True,exist_ok=True)
H=P/'prior_report.html'
if not (R/'before.html').exists():shutil.copy2(H,R/'before.html')
s=H.read_text();m=re.search(r'<template id="data-analytics-portable-artifact-payload-source"[^>]*>(.*?)</template>',s,re.S)
a=json.loads(gzip.decompress(base64.b64decode(m.group(1).strip())))
platforms=['Android','iOS','H5（不含PWA候选渠道）'];data=[]
for p in platforms:
    rs={r['day_number']:r for r in a['snapshot']['datasets']['new_curve'] if r['platform']==p}
    for d in range(2,15):
        r=rs[d];current=r['retained_users']/r['eligible_users']
        prior=1.0 if d==2 else rs[d-1]['retained_users']/rs[d-1]['eligible_users']
        same=d==2 or all(rs[d-1][k]==r[k] for k in ['eligible_users','eligible_cohort_start','eligible_cohort_end'])
        data.append({'platform':p,'day_number':d,'decline':(prior-current)/prior,'previous_rate':prior,'current_rate':current,'difference_pp':(prior-current)*100,'current_denominator':r['eligible_users'],'previous_denominator':r['eligible_users'] if d==2 else rs[d-1]['eligible_users'],'current_cohort_end':r['eligible_cohort_end'],'previous_cohort_end':r['eligible_cohort_end'] if d==2 else rs[d-1]['eligible_cohort_end'],'same_cohort':same,'baseline':'registration-day cohort=100%' if d==2 else 'saved observed retention'})
a['snapshot']['datasets']['new_decay_observed']=data
c=next(c for c in a['manifest']['charts'] if c['id']=='new-decay')
c.update(title='8月新增付费用户：第2—14日留存率观察值的逐日衰减',subtitle='第2日相对注册当日100%基准；第3—14日相对前一日。第5日起用户日期范围变化，节点仅供初步排查。',dataset='new_decay_observed',type='line')
c['encodings']['x']={'field':'day_number','type':'ordinal','label':'第N个自然日（与前一日比较）'}
c['encodings']['y']['label']='观察值相对衰减率';c['labels']={'values':'all'}
def block(id):return next(b for b in a['manifest']['blocks'] if b['id']==id)
def values(d):return '、'.join(p.replace('（不含PWA候选渠道）','')+' **'+f"{next(r['decline'] for r in data if r['platform']==p and r['day_number']==d)*100:.1f}%"+'**' for p in platforms)
block('new-decay-story')['body']='''### 8月新增付费用户：定位每日留存率下降较大的节点

**第2日是现有数据中下降最大的节点，第3日仍有明显下降。** 第2日相对注册当天的衰减率为'''+values(2)+'；第3日相对第2日为'+values(3)+'''。优先检查注册当日付费后到次日、以及次日到第3日的再次访问路径。

**计算方式：** （前一日留存率−当日留存率）÷前一日留存率。第1日是注册且成功付费的起点，采用100%队列基准；第2—14日取已保存的活跃留存率。正值表示下降，负值表示回升。这是留存比例的相对变化，不是前一天活跃用户的次日流失人数比例。

**读图范围：** 第2—4日均覆盖8月完整起点月份；第5日起纳入日期范围逐日缩小，第14日仅覆盖8月1—21日。后半段同时受到样本构成变化影响，图中的局部高点仅作为待验证线索。同一批用户的完整衰减曲线仍需统一批次重算，BigQuery授权尚未恢复。数据截止为2026年9月3日。'''
table='''### 逐日衰减率明细

| 观察日 | Android | iOS | H5（不含PWA候选渠道） | 当日纳入起点日期 | 与前日口径 |
| --- | --- | --- | --- | --- | --- |
'''
for d in range(2,15):
    rows=[next(r for r in data if r['platform']==p and r['day_number']==d) for p in platforms]
    table+='| 第'+str(d)+'日 | '+' | '.join(f"{r['decline']*100:.1f}%" for r in rows)+' | 8月1—'+str(int(rows[0]['current_cohort_end'][-2:]))+'日 | '+('起点100%基准' if d==2 else '相同' if rows[0]['same_cohort'] else '日期范围变化')+' |\n'
block('new-decay-detail')['body']=table
(R/'artifact.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
(R/'report.css').write_text((P/'revisions/2026-09-10-statistical-scope/report.css').read_text())
(R/'calculations.json').write_text(json.dumps({'status':'observed_rate_changes_only','fixed_cohort_complete':False,'new_query':False,'rows':data},ensure_ascii=False,indent=2))
