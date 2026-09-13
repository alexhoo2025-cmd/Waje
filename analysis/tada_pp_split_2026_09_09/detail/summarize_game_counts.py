"""Add a table interpretation using unrounded aggregate data."""
import copy,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;R=P/'revisions/2026-09-10-game-counts-summary';R.mkdir(parents=True,exist_ok=True)
H=P.parents[2]/'output/html/Tada与PP-细分诊断-游戏深度回访与RTP-2026-09-09.html'
for p in (P/'artifact.json',P/'报告.md',P/'report.css',P/'last-approved-version.json',H):
    if not (R/p.name).exists():shutil.copy2(p,R/p.name)
a=json.loads((P/'artifact.json').read_text());before=copy.deepcopy(a)
data=json.loads((P.parent/'data.json').read_text())['counts']
def row(p,v):return next(r for r in data if r['platform']==p and r['provider']==v)
at,ap,ht,hp=[row(p,v) for p,v in [('APP','Tada'),('APP','PP'),('H5','Tada'),('H5','PP')]]
metrics={'app_full_avg_ratio':at['avg_game_stake']/ap['avg_game_stake'],'h5_full_avg_ratio':ht['avg_game_stake']/hp['avg_game_stake'],'app_remaining_avg_ratio':at['remaining_avg']/ap['remaining_avg'],'h5_remaining_avg_ratio':ht['remaining_avg']/hp['remaining_avg'],'tada_app_h5_avg_ratio':at['avg_game_stake']/ht['avg_game_stake'],'pp_app_h5_avg_ratio':ap['avg_game_stake']/hp['avg_game_stake']}
for r in data:
    assert abs(r['stake']/r['game_count']-r['avg_game_stake'])<1e-5
    assert abs(r['remaining_stake']/r['remaining_count']-r['remaining_avg'])<1e-5
body=f'''### 数据总结：Tada每款游戏承接的下注额更高，APP的差距更大

**游戏数量：PP更多；平均每款下注额：Tada更高。** APP有下注记录的游戏为Tada **161款**、PP **415款**，平均每款下注额分别为**23,976.55万**、**323.96万**，Tada为PP的**{metrics['app_full_avg_ratio']:.1f}倍**。H5分别有**160款**、**415款**，平均每款下注额为**5,661.85万**、**112.48万**，相差**{metrics['h5_full_avg_ratio']:.1f}倍**。

**剔除前5款后，两家厂商的平均每款下注额都下降，Tada与PP的倍数差距进一步扩大。** APP从全量的**{metrics['app_full_avg_ratio']:.1f}倍**扩大至**{metrics['app_remaining_avg_ratio']:.1f}倍**；H5从**{metrics['h5_full_avg_ratio']:.1f}倍**扩大至**{metrics['h5_remaining_avg_ratio']:.1f}倍**。剩余游戏仍保留Tada在APP **{100-at['top5_pct']:.1f}%**、H5 **{100-ht['top5_pct']:.1f}%**的下注额；PP分别保留**{100-ap['top5_pct']:.1f}%**、**{100-hp['top5_pct']:.1f}%**。Tada的较大下注规模也体现在前5款以外的游戏中。

**同一厂商比较渠道，APP的平均每款下注额也更高。** 全量口径下，Tada的APP为H5的**{metrics['tada_app_h5_avg_ratio']:.1f}倍**，PP为**{metrics['pp_app_h5_avg_ratio']:.1f}倍**。后续应结合下注人数、人均深度和游戏曝光，区分渠道用户规模与游戏参与表现的影响。

这里的“平均每款”是该范围合计下注额÷有下注记录的游戏数，描述各自游戏组合的平均表现。所有倍数按未四舍五入汇总计算，金额沿用报表单位。'''
block={'id':'game-counts-summary','type':'markdown','body':body,'sourceId':'split'}
i=next(i for i,b in enumerate(a['manifest']['blocks']) if b['id']=='game-counts')
a['manifest']['blocks'].insert(i+1,block)
check=copy.deepcopy(a);check['manifest']['blocks'].pop(i+1);assert check==before
(P/'artifact.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
md=(P/'报告.md').read_text();anchor=before['manifest']['blocks'][i]['body'];assert anchor in md
(P/'报告.md').write_text(md.replace(anchor,anchor+'\n\n'+body,1))
css='\n/* Interpretation adjacent to game counts: same emphasis palette. */\n'
css+=':is(#game-counts-summary,[data-artifact-block-id="game-counts-summary"]) .rich-markdown p strong:not(:first-child){color:var(--u-key)!important;background:var(--u-bg);border-radius:3px;padding:0 2px;}\n'
(P/'report.css').write_text((P/'report.css').read_text()+css)
(R/'calculations.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2))
