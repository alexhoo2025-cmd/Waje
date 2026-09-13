import json,shutil,copy
from pathlib import Path
P=Path(__file__).resolve().parent;R=P/'revisions/2026-09-10-concentration-style';R.mkdir(parents=True,exist_ok=True)
H=P.parents[2]/'output/html/Tada与PP-细分诊断-游戏深度回访与RTP-2026-09-09.html'
for p in (P/'artifact.json',P/'报告.md',P/'report.css',P/'last-approved-version.json',H):
    if not (R/p.name).exists():shutil.copy2(p,R/p.name)
a=json.loads((P/'artifact.json').read_text());before=copy.deepcopy(a)
line='差值按未四舍五入数据计算，正文保留1位小数；上表保留2位小数供查阅。'
b=next(b for b in a['manifest']['blocks'] if b['id']=='rtp-boundary');assert line in b['body'];b['body']=b['body'].replace(line+'\n\n','',1)
c=next(c for c in a['manifest']['charts'] if c['id']=='concentration')
old=c['subtitle'];c['subtitle']=old+' Tada用蓝色、PP用橙色；深色为前5款，浅色为其余游戏。'
(P/'artifact.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
md=(P/'报告.md').read_text();md=md.replace(line+'\n\n','',1).replace(old,c['subtitle'],1);(P/'报告.md').write_text(md)
css='''
/* Stable four-category order: APP Tada, APP PP, H5 Tada, H5 PP. */
:is(#concentration-block,[data-artifact-block-id="concentration-block"]) .recharts-bar .recharts-bar-rectangle path{fill:#1565ad!important;}
:is(#concentration-block,[data-artifact-block-id="concentration-block"]) .recharts-bar .recharts-bar-rectangle:nth-child(even) path{fill:#b65319!important;}
:is(#concentration-block,[data-artifact-block-id="concentration-block"]) .recharts-bar ~ .recharts-bar .recharts-bar-rectangle path{fill:#78b9ee!important;}
:is(#concentration-block,[data-artifact-block-id="concentration-block"]) .recharts-bar ~ .recharts-bar .recharts-bar-rectangle:nth-child(even) path{fill:#f4b079!important;}
'''
assert [r['组合'] for r in a['snapshot']['datasets']['concentration']]==['APP·Tada','APP·PP','H5·Tada','H5·PP']
(P/'report.css').write_text((P/'report.css').read_text()+css)
assert a['snapshot']==before['snapshot']
