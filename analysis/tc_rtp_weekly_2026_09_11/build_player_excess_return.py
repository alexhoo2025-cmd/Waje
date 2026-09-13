#!/usr/bin/env python3
import importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent;PROJECT=ROOT.parents[1];source=PROJECT/'data/outputs/lifecycle_joint/2026-09-11/lark-after/values/aIE757.json'
spec=importlib.util.spec_from_file_location('rtp',PROJECT/'analysis/tc_game_rtp_tracking_2026_09_02/build_tracking_report.py');rtp=importlib.util.module_from_spec(spec);spec.loader.exec_module(rtp)
daily=[]
for raw in rtp.annotated_rows(source):
    if raw['日期'].isoformat()!='2026-09-10':continue
    row=rtp.game_row(raw)
    if not rtp.valid_expected(row):continue
    bet=row['complete_bet'];expected=row['complete_expected_profit'];actual=row['complete_actual_profit'];excess=expected-actual
    daily.append({'game':row['game'],'complete_bet':bet,'expected_platform_profit':expected,'actual_platform_profit':actual,'player_excess_return':excess,'actual_rtp':1-actual/bet,'expected_rtp':1-expected/bet,'rtp_gap_pp':excess/bet*100})
daily.sort(key=lambda r:r['player_excess_return'],reverse=True)
weekly_source=json.loads((ROOT/'analysis-results.json').read_text())['game_comparison'];weekly=[]
for row in weekly_source:
    if row['profit_vs_expected_curr'] is None:continue
    weekly.append({'game':row['game'],'complete_bet':row['complete_bet_curr'],'player_excess_return':-row['profit_vs_expected_curr'],'actual_rtp':row['actual_rtp_curr'],'expected_rtp':row['expected_rtp_curr'],'rtp_gap_pp':row['rtp_gap_curr_pp']})
weekly.sort(key=lambda r:r['player_excess_return'],reverse=True)
positive_daily=sum(r['player_excess_return']for r in daily if r['player_excess_return']>0);net_daily=sum(r['player_excess_return']for r in daily);positive_weekly=sum(r['player_excess_return']for r in weekly if r['player_excess_return']>0);net_weekly=sum(r['player_excess_return']for r in weekly)
for rows,total in [(daily,positive_daily),(weekly,positive_weekly)]:
    for r in rows:r['share_of_positive_excess']=r['player_excess_return']/total if r['player_excess_return']>0 else None
result={'generated_at':datetime.now(timezone.utc).isoformat(),'status':'validated_aggregate_only','definition':'玩家超额收益=实际玩家回收额-预期玩家回收额=预期平台盈利-实际平台盈利；仅纳入预期RTP有效的游戏。','daily':{'date':'2026-09-10','timezone':'Africa/Lagos','positive_excess_total':positive_daily,'negative_offset_total':net_daily-positive_daily,'net_excess_total':net_daily,'eligible_bet':sum(r['complete_bet']for r in daily),'ranking':daily},'weekly':{'window':'2026-09-04/2026-09-10','positive_excess_total':positive_weekly,'negative_offset_total':net_weekly-positive_weekly,'net_excess_total':net_weekly,'ranking':weekly},'excluded':['Tada、OMG和PP等缺少有效预期RTP的游戏不参与排名。'],'boundary':'超额收益是游戏结算相对预期的金额差，不等于实际提现；当前没有游戏结算到提现的用户级归因。'}
(ROOT/'player-excess-return-2026-09-10.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
def amt(v):return f'{v/1e4:.2f}万'if abs(v)>=1e4 else f'{v:,.0f}'
top=daily[0];week=weekly[0]
(ROOT/'player-excess-return-2026-09-10.md').write_text(f'''# 9月10日玩家超额收益贡献

玩家超额收益＝预期平台盈利－实际平台盈利，仅纳入预期RTP有效的游戏。

9月10日贡献最大的是 **{top['game']}**：{amt(top['player_excess_return'])}，占正向超额收益{top['share_of_positive_excess']*100:.1f}%；实际RTP {top['actual_rtp']*100:.2f}%，预期RTP {top['expected_rtp']*100:.2f}%。

9月4—10日累计贡献最大仍是 **{week['game']}**：{amt(week['player_excess_return'])}。EasyWin因偏离幅度大位列第三，但绝对金额低于Roulette和Whot。

{result['boundary']}''')
print(json.dumps({'daily_top':daily[:8],'daily_positive_total':positive_daily,'daily_net':net_daily,'weekly_top':weekly[:8],'weekly_positive_total':positive_weekly,'weekly_net':net_weekly},ensure_ascii=False))
