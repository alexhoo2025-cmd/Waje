"""Remove requested subtitle clause and color provider labels only."""
import copy,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;R=P/'revisions/2026-09-10-provider-style'
R.mkdir(parents=True,exist_ok=True)
H=P.parents[2]/'output/html/Tada与PP-细分诊断-游戏深度回访与RTP-2026-09-09.html'
for p in (P/'artifact.json',P/'报告.md',P/'report.css',P/'last-approved-version.json',H):
    if not (R/p.name).exists():shutil.copy2(p,R/p.name)
a=json.loads((P/'artifact.json').read_text());before=copy.deepcopy(a)
c=next(c for c in a['manifest']['charts'] if c['id']=='mean-stake')
old='按同组厂商去重下注人数计算；金额不是净投入或收益。';new='按同组厂商去重下注人数计算。'
assert c['subtitle']==old;c['subtitle']=new
table=next(b for b in a['manifest']['blocks'] if b['id']=='depth-metrics')['body']
rows=[l for l in table.splitlines() if l.startswith('| ')][2:]
assert len(rows)==12
for i,row in enumerate(rows):assert ('Tada' if i%2==0 else 'PP') in row.split('|')[2]
(P/'artifact.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
md=(P/'报告.md').read_text();assert old in md
(P/'报告.md').write_text(md.replace(old,new,1))
css='''
/* Provider labels: retain age-group backgrounds and readable light/dark colors. */
:root{--detail-tada-text:#155ca8;--detail-pp-text:#a6440c;}
@media(prefers-color-scheme:dark){:root{--detail-tada-text:#7cc4ff;--detail-pp-text:#ffb47a;}}
:is(#depth-metrics,[data-artifact-block-id="depth-metrics"]) tbody tr:nth-child(odd) td:nth-child(2){color:var(--detail-tada-text)!important;font-weight:700;}
:is(#depth-metrics,[data-artifact-block-id="depth-metrics"]) tbody tr:nth-child(even) td:nth-child(2){color:var(--detail-pp-text)!important;font-weight:700;}
'''
(P/'report.css').write_text((P/'report.css').read_text()+css)
next(c for c in before['manifest']['charts'] if c['id']=='mean-stake')['subtitle']=new
assert before==a
(R/'change.json').write_text(json.dumps({'subtitle':new,'provider_styles':'Tada blue / PP orange; combination column only','other_content_unchanged':True,'data_unchanged':True,'feishu_updated':False},ensure_ascii=False,indent=2))
