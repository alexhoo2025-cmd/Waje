import json,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;R=P/'revisions/2026-09-10-association-note';R.mkdir(parents=True,exist_ok=True)
H=P.parents[2]/'output/html/Tada与PP-细分诊断-游戏深度回访与RTP-2026-09-09.html'
for p in (P/'artifact.json',P/'报告.md',P/'last-approved-version.json',H):
    if not (R/p.name).exists():shutil.copy2(p,R/p.name)
a=json.loads((P/'artifact.json').read_text());b=next(b for b in a['manifest']['blocks'] if b['id']=='association')
old='，不把四组混成一条相关线。使用Spearman秩相关（**−1**到1）：越接近1，排名越同向，0附近代表单调关系弱。'
assert old in b['body'];b['body']=b['body'].replace(old,'。',1)
(P/'artifact.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
md=(P/'报告.md').read_text();assert old in md;(P/'报告.md').write_text(md.replace(old,'。',1))
