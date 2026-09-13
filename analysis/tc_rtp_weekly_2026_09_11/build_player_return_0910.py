#!/usr/bin/env python3
import importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent;PROJECT=ROOT.parents[1];source=PROJECT/'data/outputs/lifecycle_joint/2026-09-11/lark-after/values/aIE757.json'
spec=importlib.util.spec_from_file_location('rtp',PROJECT/'analysis/tc_game_rtp_tracking_2026_09_02/build_tracking_report.py');rtp=importlib.util.module_from_spec(spec);spec.loader.exec_module(rtp)
rows=[]
for raw in rtp.annotated_rows(source):
    if raw['日期'].isoformat()!='2026-09-10':continue
    r=rtp.game_row(raw);bet=r['complete_bet'];profit=r['complete_actual_profit']
    if not bet or profit is None:continue
    rows.append({'game':r['game'],'complete_bet':bet,'platform_actual_profit':profit,'player_gross_return':bet-profit,'player_net_gain':max(-profit,0),'actual_rtp':1-profit/bet})
gross_total=sum(r['player_gross_return']for r in rows);net_total=sum(r['player_net_gain']for r in rows)
for r in rows:r['gross_return_share']=r['player_gross_return']/gross_total
gross=sorted(rows,key=lambda r:r['player_gross_return'],reverse=True);net=sorted([r for r in rows if r['player_net_gain']>0],key=lambda r:r['player_net_gain'],reverse=True)
weekly=json.loads((ROOT/'analysis-results.json').read_text())['game_comparison'];weekly_net=[]
for r in weekly:
    profit=r['complete_bet_curr']*(1-r['actual_rtp_curr'])
    if profit<0:weekly_net.append({'game':r['game'],'period':'2026-09-04/2026-09-10','platform_actual_profit':profit,'player_net_gain':-profit,'complete_bet':r['complete_bet_curr'],'actual_rtp':r['actual_rtp_curr']})
weekly_net.sort(key=lambda r:r['player_net_gain'],reverse=True)
result={'generated_at':datetime.now(timezone.utc).isoformat(),'status':'validated_aggregate_only','business_date':'2026-09-10','timezone':'Africa/Lagos','definitions':{'player_gross_return':'完全下注额减完全实际盈利；相当于玩家总回收金额，包含返还本金。','player_net_gain':'同一游戏汇总后平台实际盈利为负的绝对值；表示该游戏整体玩家净赢，不代表单个玩家收益。'},'daily':{'game_count_with_bet':len(rows),'gross_return_total':gross_total,'net_gain_total':net_total,'gross_return_ranking':gross,'net_gain_ranking':net},'weekly_net_gain_ranking':weekly_net,'boundary':'游戏回收与提现属于不同事实表，当前没有在合规聚合层建立同一用户/钱包的游戏结算至提现归因；不能把游戏回收额直接解释为9月10日提现来源。'}
(ROOT/'player-return-2026-09-10.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
def amt(v):return f'{v/1e8:.2f}亿'if abs(v)>=1e8 else f'{v/1e4:.2f}万'if abs(v)>=1e4 else f'{v:,.0f}'
md=['# 9月10日玩家回收与净赢贡献','',f'玩家总回收额最高的是 **{gross[0]["game"]}**：{amt(gross[0]["player_gross_return"])}，占当日全部游戏回收额{gross[0]["gross_return_share"]*100:.1f}%。此口径包含本金回收。','',f'按玩家净赢口径，当日只有 **{net[0]["game"]}** 在游戏汇总层面表现为玩家整体净赢：{amt(net[0]["player_net_gain"])}，实际RTP {net[0]["actual_rtp"]*100:.2f}%。','',f'过去7天玩家整体净赢最多的是 **{weekly_net[0]["game"]}**：{amt(weekly_net[0]["player_net_gain"])}；其次是{weekly_net[1]["game"]} {amt(weekly_net[1]["player_net_gain"])}。','',result['boundary']]
(ROOT/'player-return-2026-09-10.md').write_text('\n'.join(md))
print(json.dumps({'gross_top':gross[:5],'daily_net':net,'weekly_net':weekly_net},ensure_ascii=False))
