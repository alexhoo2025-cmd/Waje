"""Narrow user-requested wording revision; preserve all other report content."""
import json,shutil,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
R=P/'revisions/2026-09-10-summary'
R.mkdir(parents=True,exist_ok=True)
H=P.parents[2]/'output/html/Tada与PP-细分诊断-游戏深度回访与RTP-2026-09-09.html'
for p in (P/'artifact.json',P/'报告.md',H):
    dest=R/p.name
    if not dest.exists():shutil.copy2(p,dest)
a=json.loads((P/'artifact.json').read_text())
b=next(b for b in a['manifest']['blocks'] if b['id']=='summary')
old=b['body']
new='''## 执行摘要

**剔除头部游戏后，Tada仍有较大的下注规模优势。** APP有下注记录的游戏，Tada为161款、PP为415款。剔除各自下注额前5款后，Tada其余游戏的合计下注额为PP的32.1倍。

**Tada的APP人均下注额更高，结算RTP也略高。** Tada人均下注额约26.64万，PP约3.80万；结算RTP分别为96.94%和95.99%。RTP对下注差异的影响仍需进一步验证。

**优先验证H5端Tada游戏的RTP与下注表现的关联。** 在110款样本游戏中，RTP与下注额、下注活跃天数的相关系数分别约为0.46和0.40（秩相关）。按日观察时关联较弱，建议先验证，再评估参数调整。'''
assert 'Tada的优势不限于' in old
b['body']=new
(P/'artifact.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
md=(P/'报告.md').read_text();assert old in md
(P/'报告.md').write_text(md.replace(old,new,1))
before=json.loads((R/'artifact.json').read_text())
next(x for x in before['manifest']['blocks'] if x['id']=='summary')['body']=new
assert before==a,'Unrelated change'
(R/'change.json').write_text(json.dumps({'scope':'summary only','before':old,'after':new,'other_content_unchanged':True,'feishu_updated':False},ensure_ascii=False,indent=2))
print('Only summary changed; backup saved')
