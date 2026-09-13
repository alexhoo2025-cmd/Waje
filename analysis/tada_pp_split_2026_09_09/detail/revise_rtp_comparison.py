"""Add a source-backed RTP comparison adjacent to the existing table."""
import copy,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;R=P/'revisions/2026-09-10-rtp-comparison'
R.mkdir(parents=True,exist_ok=True)
H=P.parents[2]/'output/html/Tada与PP-细分诊断-游戏深度回访与RTP-2026-09-09.html'
for p in (P/'artifact.json',P/'报告.md',P/'last-approved-version.json',H):
    if not (R/p.name).exists():shutil.copy2(p,R/p.name)
a=json.loads((P/'artifact.json').read_text());before=copy.deepcopy(a)
rows=a['snapshot']['datasets']['calculation_core']
def rtp(channel,vendor,age):
    r=next(r for r in rows if r['group']==f'{channel}·{vendor}·{age}')
    assert abs(r['payout']/r['stake']-r['rtp'])<1e-10
    return r['rtp']*100
new='new_30d';old='old_over_30d';parts=[]
for channel in ('APP','H5'):
    tn,pn=rtp(channel,'Tada',new),rtp(channel,'PP',new)
    to,po=rtp(channel,'Tada',old),rtp(channel,'PP',old)
    parts.append(f'- **{channel}：** 新用户RTP为Tada {tn:.1f}%、PP {pn:.1f}%，Tada高{tn-pn:.1f}个百分点；老用户为{to:.1f}%、{po:.1f}%，Tada高{to-po:.1f}个百分点。')
ta=abs(rtp('APP','Tada',new)-rtp('APP','Tada',old))
th=abs(rtp('H5','Tada',new)-rtp('H5','Tada',old))
assert ta<.1 and th<.1
pa=rtp('APP','PP',old)-rtp('APP','PP',new)
ph=rtp('H5','PP',new)-rtp('H5','PP',old)
body='''### RTP对比：Tada整体更高，PP的新老用户差异更明显

**在APP和H5，新用户、老用户的结算RTP均为Tada更高。** 同渠道、同一新老用户类别的对比如下：

'''+ '\n'.join(parts)+f'''

**Tada的新老用户RTP接近，两个渠道的差距均不足0.1个百分点。** PP的差异方向随渠道变化：APP老用户比新用户高{pa:.1f}个百分点；H5新用户比老用户高{ph:.1f}个百分点。四种渠道与人群组合中，H5老用户的厂商差距最大，Tada比PP高{rtp('H5','Tada',old)-rtp('H5','PP',old):.1f}个百分点。

**建议优先下钻H5老用户的游戏构成。** 先按游戏品类比较两家厂商，再在各厂商内部比较同款游戏的新老用户RTP、下注深度和回访，核查游戏选择与参与方式的差异。当前比较描述实际结算表现，RTP对下注和回访的影响仍需验证。

差值按未四舍五入数据计算，正文保留1位小数；上表保留2位小数供查阅。

'''
b=next(b for b in a['manifest']['blocks'] if b['id']=='rtp-boundary');previous=b['body'];b['body']=body+previous
md=(P/'报告.md').read_text();assert previous in md
(P/'报告.md').write_text(md.replace(previous,b['body'],1))
(P/'artifact.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
next(b for b in before['manifest']['blocks'] if b['id']=='rtp-boundary')['body']=b['body']
assert before==a
(R/'change.json').write_text(json.dumps({'changed_block':'rtp-boundary','calculations':'payout/stake verified; differences from unrounded ratios','other_content_unchanged':True,'feishu_updated':False},ensure_ascii=False,indent=2))
