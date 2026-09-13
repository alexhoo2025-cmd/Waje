"""Clarify the selected head-game comparison, preserving all other edits."""
import copy,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;R=P/'revisions/2026-09-10-heads'
R.mkdir(parents=True,exist_ok=True)
H=P.parents[2]/'output/html/Tada与PP-细分诊断-游戏深度回访与RTP-2026-09-09.html'
for p in (P/'artifact.json',P/'报告.md',P/'last-approved-version.json',H):
    if not (R/p.name).exists():shutil.copy2(p,R/p.name)
a=json.loads((P/'artifact.json').read_text());before=copy.deepcopy(a)
b=next(x for x in a['manifest']['blocks'] if x['id']=='heads');old=b['body']
b['body']='''## 02｜剔除前5款游戏后，Tada其余游戏的下注额仍明显高于PP

**在APP渠道，剔除各自下注额最高的5款游戏后，Tada剩余游戏的合计下注额为PP的32.1倍。** Tada剩余156款游戏，合计下注294.56亿；PP剩余410款，合计下注9.17亿。

**按平均每款游戏计算，Tada为PP的84.4倍。** Tada平均每款下注额约18,881.80万，PP约223.64万。计算方式为“剩余游戏合计下注额÷剩余游戏数”，比较的是两家厂商各自游戏组合的平均水平。

**PP的下注额更集中在前5款游戏。** APP前5款占各自厂商下注额的比例，Tada为23.7%、PP为31.8%；H5分别为31.4%、34.1%。因此，剔除前5款后，PP保留下来的下注额比例更低，APP中Tada与PP的合计下注额之比由28.7倍扩大到32.1倍。

下图按同一渠道、同一厂商的全部下注额作为100%；“前5款”分别按该渠道内该厂商的下注额排名确定。金额沿用原报表单位。'''
md=(P/'报告.md').read_text();assert old in md
(P/'报告.md').write_text(md.replace(old,b['body'],1))
(P/'artifact.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
next(x for x in before['manifest']['blocks'] if x['id']=='heads')['body']=b['body'];assert before==a
(R/'change.json').write_text(json.dumps({'changed_block':'heads','other_content_unchanged':True,'data_unchanged':True,'feishu_updated':False},ensure_ascii=False,indent=2))
