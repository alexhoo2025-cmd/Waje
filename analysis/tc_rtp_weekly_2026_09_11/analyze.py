#!/usr/bin/env python3
"""Recompute 7-day TC/RTP comparisons from aggregate-only reviewed sources."""
from __future__ import annotations
import csv,importlib.util,json,re
from collections import Counter,defaultdict
from datetime import date
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
PARSER=PROJECT/'analysis/tc_game_rtp_tracking_2026_09_02/build_tracking_report.py'
VALUES=PROJECT/'data/outputs/lifecycle_joint/2026-09-11/lark-after/values'
spec=importlib.util.spec_from_file_location('rtp_parser',PARSER);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
PREV=(date(2026,8,28),date(2026,9,3));CURR=(date(2026,9,4),date(2026,9,10));TREND=(PREV[0],CURR[1])
NEW_GAMES={'Hilo':date(2026,8,21),'Plinko':date(2026,8,21),'Tower':date(2026,8,25)}

def raw_rows(path,day):
    frame=pd.read_excel(path);frame.columns=[re.sub(r'\s+','',str(c or''))for c in frame.columns]
    out=[]
    for row in frame.to_dict('records'):
        row['日期']=day;row['游戏']=old.canonical_game(row.get('游戏')or row.get('游戏类型'));out.append(row)
    return out

def detail_row(r):
    life=str(r.get('生命周期')or'').strip()
    if life not in {'1','2','3','4'}:return None
    return {'date':r['日期'],'game':old.canonical_game(r.get('游戏')or r.get('游戏类型')),'lifecycle':int(life),'base_bet':old.number(r.get('基础下注额'))or 0.0,'base_actual_profit':old.number(r.get('基础实际盈利')),'complete_bet':old.number(r.get('完全下注额'))or 0.0,'complete_expected_profit':old.number(r.get('完全预期盈利')),'complete_actual_profit':old.number(r.get('完全实际盈利')),'complete_expected_return':old.number(r.get('预期回报比')),'bankruptcy':old.number(r.get('总破产保护金额'))or 0.0,'personal_control':old.number(r.get('总个人盈利控制金额'))or 0.0}

def aggregate_games(rows,start,end):
    selected=[r for r in rows if start<=r['date']<=end and r['complete_bet']>0]
    groups=defaultdict(list)
    for r in selected:groups[r['game']].append(r)
    games=[{'game':g,**old.aggregate(v)}for g,v in groups.items()];games.sort(key=lambda r:r['complete_bet'],reverse=True)
    return games,old.aggregate(selected)

def load_tc():
    rows=json.loads((ROOT/'queries/01_tc_daily_channel.result.json').read_text())['rows']
    daily=[r for r in rows if r['row_type']=='daily']
    def period(label):
        subset=[r for r in daily if r['period']==label];re=sum(r['recharge']for r in subset);wd=sum(r['withdraw']for r in subset)
        return {'days':len(subset),'recharge':re,'withdraw':wd,'tc':wd/re,'recharge_orders':sum(r['recharge_orders']for r in subset),'withdraw_orders':sum(r['withdraw_orders']for r in subset)}
    prev=period('基线：8月28日—9月3日');curr=period('本期：9月4—10日')
    # Reconcile the shared 9/1-7 dates against the previous report's Metabase snapshot.
    reference=list(csv.DictReader((PROJECT/'analysis/tc_game_rtp_weekly_2026_09_08/sources/metabase_tc_daily_2026-08-25_2026-09-07.csv').open()))
    by_date={r['biz_date']:r for r in daily};deltas=[]
    for ref in reference:
        if '2026-09-01'<=ref['business_date']<='2026-09-07':
            bq=by_date[ref['business_date']];rr=float(ref['success_recharge_amount']);ww=float(ref['success_withdraw_amount'])
            deltas.append({'date':ref['business_date'],'recharge_difference_pct':bq['recharge']/rr-1,'withdraw_difference_pct':bq['withdraw']/ww-1})
    total_amount=sum(r['recharge']+r['withdraw']for r in daily);unmatched=sum(r['unmatched_amount']for r in daily)
    return {'previous':prev,'current':curr,'change_pp':(curr['tc']-prev['tc'])*100,'recharge_change_pct':curr['recharge']/prev['recharge']-1,'withdraw_change_pct':curr['withdraw']/prev['withdraw']-1,'daily':daily,'reference_reconciliation':{'dates':deltas,'max_abs_recharge_difference_pct':max(abs(r['recharge_difference_pct'])for r in deltas),'max_abs_withdraw_difference_pct':max(abs(r['withdraw_difference_pct'])for r in deltas)},'channel_attribution':{'status':'blocked_incomplete_profile_join','unmatched_money_share':unmatched/total_amount,'reason':'同日画像只覆盖少量当日新增标识，不能用于全量注册渠道TC；参考报告渠道维度本期不更新。'}}

def main():
    game_rows=[old.game_row(r)for r in old.annotated_rows(VALUES/'aIE757.json')]
    detail_rows=[x for x in (detail_row(r)for r in old.annotated_rows(VALUES/'wjhify.json'))if x]
    # Latest online capture omits 9/3; restore that independently validated day from the archived source export.
    missing_day=date(2026,9,3);raw=PROJECT/'data/raw/lifecycle_joint/2026-09-08-report/2026-09-03'
    game_rows=[r for r in game_rows if r['date']!=missing_day]+[old.game_row(r)for r in raw_rows(raw/'game.xlsx',missing_day)]
    detail_rows=[r for r in detail_rows if r['date']!=missing_day]+[x for x in (detail_row(r)for r in raw_rows(raw/'detail.xlsx',missing_day))if x]
    period_games=[r for r in game_rows if PREV[0]<=r['date']<=CURR[1]]
    assert len(period_games)==14*31
    assert not [k for k,v in Counter((r['date'],r['game'])for r in period_games).items()if v>1]
    assert len([r for r in detail_rows if PREV[0]<=r['date']<=CURR[1]])==14*124
    prev_games,prev_all=aggregate_games(game_rows,*PREV);curr_games,curr_all=aggregate_games(game_rows,*CURR)
    assert prev_all['days']==curr_all['days']==7 and len(prev_games)==len(curr_games)==25
    pidx={r['game']:{**r,'rank':i+1}for i,r in enumerate(prev_games)};cidx={r['game']:{**r,'rank':i+1}for i,r in enumerate(curr_games)}
    total_delta=curr_all['complete_bet']-prev_all['complete_bet'];comparison=[]
    for name in sorted(set(pidx)&set(cidx)):
        p,c=pidx[name],cidx[name];delta=c['complete_bet']-p['complete_bet']
        comparison.append({'game':name,'complete_bet_prev':p['complete_bet'],'complete_bet_curr':c['complete_bet'],'bet_delta':delta,'bet_change_pct':c['complete_bet']/p['complete_bet']-1 if p['complete_bet']else None,'bet_delta_contribution_pct':delta/total_delta if total_delta else None,'bet_share_prev':p['complete_bet']/prev_all['complete_bet'],'bet_share_curr':c['complete_bet']/curr_all['complete_bet'],'bet_share_change_pp':(c['complete_bet']/curr_all['complete_bet']-p['complete_bet']/prev_all['complete_bet'])*100,'actual_rtp_prev':p['actual_rtp'],'actual_rtp_curr':c['actual_rtp'],'rtp_change_pp':(c['actual_rtp']-p['actual_rtp'])*100,'expected_rtp_curr':c['expected_rtp'],'actual_rtp_expected_subset_curr':c['actual_rtp_expected_subset'],'rtp_gap_curr_pp':c['rtp_gap_pp'],'expected_coverage_curr':c['expected_coverage'],'profit_vs_expected_curr':c['profit_vs_expected'],'rank_prev':p['rank'],'rank_curr':c['rank']})
    comparison.sort(key=lambda r:r['complete_bet_curr'],reverse=True)
    new_games=[]
    for game,launch in NEW_GAMES.items():
        p=pidx.get(game);c=cidx.get(game)
        current_lifecycle=[]
        for life in range(1,5):
            selected=[r for r in detail_rows if r['game']==game and r['lifecycle']==life and CURR[0]<=r['date']<=CURR[1] and r['complete_bet']>0]
            current_lifecycle.append({'game':game,'lifecycle':life,**old.aggregate(selected)})
        daily=[]
        for d in sorted({r['date']for r in game_rows if r['game']==game and CURR[0]<=r['date']<=CURR[1]}):
            daily.append({'date':d.isoformat(),**old.aggregate([r for r in game_rows if r['game']==game and r['date']==d and r['complete_bet']>0])})
        new_games.append({'game':game,'launch':launch.isoformat(),'previous':p,'current':c,'bet_change_pct':c['complete_bet']/p['complete_bet']-1 if p and p['complete_bet']else None,'rtp_change_pp':(c['actual_rtp']-p['actual_rtp'])*100 if p and c['actual_rtp']is not None and p['actual_rtp']is not None else None,'daily':daily,'lifecycle':current_lifecycle})
    anomalies=[r for r in curr_games if r['rtp_gap_pp']is not None and abs(r['rtp_gap_pp'])>=3]
    anomalies.sort(key=lambda r:abs(r.get('profit_vs_expected')or 0),reverse=True)
    coverage=json.loads((ROOT/'queries/02_source_coverage.result.json').read_text())['rows']
    assert len(coverage)==14 and all(r['total_rows']>0 for r in coverage)
    source_receipt=json.loads((PROJECT/'data/outputs/lifecycle_joint/2026-09-11/run-receipt.json').read_text())
    assert source_receipt['quality']['cross_table_reconciliation_passed'] and source_receipt['quality']['duplicate_keys_absent']
    tc=load_tc();assert tc['previous']['days']==tc['current']['days']==7
    result={'generated_at':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'status':'ready_with_channel_gap','windows':{'previous_week':[x.isoformat()for x in PREV],'current_week':[x.isoformat()for x in CURR],'timezone':'Asia/Hong_Kong'},'tc':tc,'game_overall':{'previous':prev_all,'current':curr_all,'bet_change_pct':curr_all['complete_bet']/prev_all['complete_bet']-1,'actual_rtp_change_pp':(curr_all['actual_rtp']-prev_all['actual_rtp'])*100,'expected_coverage_change_pp':(curr_all['expected_coverage']-prev_all['expected_coverage'])*100},'game_comparison':comparison,'bet_drivers':{'total_delta':total_delta,'positive':sorted([r for r in comparison if r['bet_delta']>0],key=lambda r:r['bet_delta'],reverse=True)[:7],'negative':sorted([r for r in comparison if r['bet_delta']<0],key=lambda r:r['bet_delta'])[:7]},'new_games':new_games,'anomalies':anomalies,'quality':{'lifecycle_source':source_receipt['source'],'lifecycle_source_status':source_receipt['status'],'game_rows':len(period_games),'detail_rows':14*124,'games':31,'server_event_partitions':14,'server_event_days_complete':True,'query_bytes':sum(e['actual_bytes']for e in json.loads((ROOT/'query-ledger.json').read_text())['entries']),'original_report_revision':48,'original_report_content_sha256':json.loads((ROOT/'reference/manifest.json').read_text())['content_sha256'],'blocked_dimensions':['注册渠道TC：本期无法从当前BigQuery画像在5 GiB单查询上限内完整归属'],'limitations':['缺少有效局数、最终结算状态、取消/退款、Bonus、配置版本和用户级大奖分布','部分游戏预期RTP覆盖不完整；实际-预期仅在有效预期范围内计算']}}
    (ROOT/'analysis-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str))
    print(json.dumps({'status':result['status'],'tc':result['tc'],'game_overall':result['game_overall'],'top_positive':result['bet_drivers']['positive'][:3],'top_negative':result['bet_drivers']['negative'][:3],'anomalies':result['anomalies'][:8]},ensure_ascii=False,default=str))
if __name__=='__main__':main()
