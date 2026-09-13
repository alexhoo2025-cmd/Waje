"""Normalize audience-facing eligibility terms, preserving data and source SQL."""
import base64,gzip,json,re,shutil,copy
from pathlib import Path
P=Path(__file__).resolve().parent;R=P/'revisions/2026-09-10-statistical-scope';R.mkdir(parents=True,exist_ok=True)
H=P/'prior_report.html'
if not (R/'before.html').exists():shutil.copy2(H,R/'before.html')
s=H.read_text();m=re.search(r'<template id="data-analytics-portable-artifact-payload-source"[^>]*>(.*?)</template>',s,re.S)
a=json.loads(gzip.decompress(base64.b64decode(m.group(1).strip())));before=copy.deepcopy(a)
pairs=[
('尚未到观察日，保留未成熟状态','未达到统计口径，暂不展示留存率'),
('＊表示部分批次已成熟；未成熟不补零。','＊表示仅部分注册或首充日期的用户达到统计口径；未达到统计口径的数据不填零。这里的统计口径指满足对应留存日的观察时长要求。'),
('不同成熟批次','不同的达标日期范围'),
('先看成熟批次','仅统计达到观察时长要求的用户'),
('长留看成熟批次','长留按统计口径比较'),
('8月成熟部分','8月达到统计口径的部分'),
('8月成熟分母','8月纳入统计人数'),
('成熟分母','纳入统计人数'),
('成熟样本','纳入统计人数'),
('尚未成熟','尚未达到统计口径'),
('未成熟','未达到统计口径'),
('已成熟','已达到统计口径'),
('成熟批次','达到统计口径的用户批次'),
('未到观察日','未达到统计口径'),
('已到观察日的批次','达到统计口径的用户批次'),
]
def norm(s):
    for x,y in pairs:s=s.replace(x,y)
    return s
changes=[]
for category in ['blocks','charts','tables','cards']:
    for item in a['manifest'].get(category,[]):
        for key in ['body','title','subtitle','description']:
            if isinstance(item.get(key),str):
                old=item[key];item[key]=norm(old)
                if old!=item[key]:changes.append(category+'.'+item['id']+'.'+key)
        for col in item.get('columns',[]):
            if 'label' in col:col['label']=norm(col['label'])
for rows in a['snapshot']['datasets'].values():
    for row in rows:
        for k,v in row.items():
            if v in ('未到观察日','未成熟','尚未成熟') if isinstance(v,str) else False:row[k]='未达到统计口径'
for b in a['manifest']['blocks']:assert '成熟' not in b.get('body','')
def numeric(obj):
    if isinstance(obj,dict):return {k:numeric(v) for k,v in obj.items() if not isinstance(v,str)}
    if isinstance(obj,list):return [numeric(v) for v in obj]
    return obj
assert numeric(a['snapshot'])==numeric(before['snapshot'])
(R/'artifact.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
(R/'report.css').write_text((P/'revisions/2026-09-10-d14/report.css').read_text())
(R/'change.json').write_text(json.dumps({'changed_fields':changes,'numeric_values_unchanged':True,'source_sql_unchanged':a['manifest']['sources']==before['manifest']['sources'],'status_semantics_unchanged':True},ensure_ascii=False,indent=2))
