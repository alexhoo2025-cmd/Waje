import base64,gzip,json,re,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;R=P/'revisions/2026-09-10-d14';R.mkdir(parents=True,exist_ok=True)
H=P/'prior_report.html'
if not (R/'before.html').exists():shutil.copy2(H,R/'before.html')
s=H.read_text();m=re.search(r'<template id="data-analytics-portable-artifact-payload-source"[^>]*>(.*?)</template>',s,re.S)
a=json.loads(gzip.decompress(base64.b64decode(m.group(1).strip())))
def block(id):return next(b for b in a['manifest']['blocks'] if b['id']==id)
def row(ds,month,p):return next(r for r in a['snapshot']['datasets'][ds] if r['cohort_month']==month and r['platform']==p)
platforms=['Android','iOS','H5（不含PWA候选渠道）']
paragraphs=['**第14日留存：6月至7月，新增付费与首次付费用户在三个平台分组均有改善。**']
for ds,label in [('new_long','新增付费'),('first_long','首次付费')]:
    pieces=[]
    for p in platforms:
        x,y=row(ds,'2026-06',p),row(ds,'2026-07',p)
        assert x['d14_cohort_end']=='2026-06-30' and y['d14_cohort_end']=='2026-07-31'
        pieces.append(p.replace('（不含PWA候选渠道）','')+' **'+x['d14']+'→'+y['d14']+'**')
    paragraphs.append(label+'用户：'+'、'.join(pieces)+'。')
paragraphs.append('以上均覆盖完整起点月份。H5虽然改善，留存水平仍低于Android和iOS，应结合付费人数和渠道构成评估。')
d14=' '.join(paragraphs)
b=block('summary');parts=b['body'].split('\n\n');parts=[p for p in parts if not p.startswith('**第90日')]
index=next(i for i,p in enumerate(parts) if p.startswith('**第30日'));parts.insert(index,d14)
b['body']='\n\n'.join(parts).replace('8月第60／90日尚未到观察日','8月第60日尚未到观察日')
b=block('long-story');body=b['body'].replace('30／60／90日长留','第14／30／60日留存').replace('；6月第90日仅覆盖1—6日批次','')
body=body.replace('### 第60日与第90日：先看同一观察日的平台差异','### 第60日：6月完整批次的平台差异')
lines=[]
for line in body.splitlines():
    if line.startswith('|'):
        cells=line.strip('|').split('|');line='|'+'|'.join(cells[:4])+'|'
    lines.append(line)
body='\n'.join(lines).replace('第60／90日比例','第60日比例').replace('第90日数据先用于同批次的平台比较，暂不据此推断整月趋势。','')
intro='''### 第14日：完整月份对比与8月成熟部分

'''+d14+'''

8月第14日仅覆盖8月1—21日起点用户，下表单列观察值与成熟分母，不与6、7月完整月份直接计算环比。

| 人群 | 平台分组 | 6月第14日 | 7月第14日 | 8月第14日（1—21日批次） | 8月成熟分母 |
| --- | --- | --- | --- | --- | --- |
'''
for ds,label in [('new_long','新增付费'),('first_long','首次付费')]:
    for p in platforms:
        x,y,z=[row(ds,mon,p) for mon in ['2026-06','2026-07','2026-08']]
        assert z['d14_cohort_end']=='2026-08-21'
        intro+=f"| {label} | {p} | {x['d14']} | {y['d14']} | {z['d14'].replace('＊','')} | {z['d14_eligible_users']:,} |\n"
b['body']=body.split('\n\n',1)[0]+'\n\n'+intro+'\n'+body.split('\n\n',1)[1]
block('actions')['body']=block('actions')['body'].replace('第30／60／90日读数','第14／30／60日读数')
for t in a['manifest']['tables']:
    if t['id'] in ('new-long-table','first-long-table'):
        t['columns']=[c for c in t['columns'] if c.get('field')!='d90']
assert all('90日' not in b.get('body','') and '／90' not in b.get('body','') for b in a['manifest']['blocks'])
(R/'artifact.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
(R/'report.css').write_text((P/'revisions/2026-09-10-decay/report.css').read_text())
(R/'change.json').write_text(json.dumps({'removed':'D90 visible narrative and table columns','added':'D14 summary and cohort-aware comparison','source_cutoff':'2026-09-03','original_datasets_preserved':True,'new_query':False},indent=2))
