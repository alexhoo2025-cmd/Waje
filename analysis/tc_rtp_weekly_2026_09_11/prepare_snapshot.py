#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent;D=json.loads((ROOT/'analysis-results.json').read_text())
sql=(ROOT/'queries/01_tc_daily_channel.sql').read_text()
tc_source={'label':'Waje BigQuery服务端资金事件｜9月4—10日对比8月28日—9月3日','sql':sql,'tables':['wajenigeria.origin_hfyl.view_event_server'],'filters':['app_id=90006','日期：2026-08-28至2026-09-10','成功充值：ORDER且pay_success','提现：WITHDRAW服务端事件'],'executedAt':json.loads((ROOT/'queries/01_tc_daily_channel.result.json').read_text())['job_id'],'metricDefinitions':[{'label':'TC','definition':'成功提现金额除以成功现金充值金额；按窗口金额加权。','componentIds':['summary','tc-overview','tc-daily','tc-table'],'sourceLineage':[{'tables':['wajenigeria.origin_hfyl.view_event_server']}]},{'label':'成功充值与提现','definition':'服务端成功事件按交易号去重后的金额；不等于收入或净利润。','componentIds':['summary','tc-overview','tc-daily','tc-table'],'sourceLineage':[{'tables':['wajenigeria.origin_hfyl.view_event_server']}]}]}
rtp_source={'label':'GM Lifecycle Pool v2 (Joint)｜9月4—10日对比8月28日—9月3日','files':['data/outputs/lifecycle_joint/2026-09-11/新包生命周期V2 - 含联运2026.9.4-9.10_Joint修正版.xlsx','data/raw/lifecycle_joint/2026-09-08-report/2026-09-03/game.xlsx','data/raw/lifecycle_joint/2026-09-08-report/2026-09-03/detail.xlsx'],'filters':['两个连续7天窗口','31款游戏源行；25款有下注','生命周期1—4'],'executedAt':'2026-09-11T10:54:47+08:00','metricDefinitions':[{'label':'实际RTP','definition':'1减去完全实际盈利除以完全下注额；按金额加权。','componentIds':['summary','game-overview','game-scatter','game-table','new-games','new-game-daily','lifecycle','anomalies'],'sourceLineage':[{'files':['data/outputs/lifecycle_joint/2026-09-11/新包生命周期V2 - 含联运2026.9.4-9.10_Joint修正版.xlsx']}]},{'label':'实际与预期RTP差异','definition':'仅在预期RTP有效的下注范围内，用实际RTP减预期RTP，单位为百分点。','componentIds':['summary','game-scatter','game-table','new-games','lifecycle','anomalies'],'sourceLineage':[{'files':['data/outputs/lifecycle_joint/2026-09-11/新包生命周期V2 - 含联运2026.9.4-9.10_Joint修正版.xlsx']}]}]}
week=[{'period':'基线 8/28—9/3',**D['tc']['previous']},{'period':'本期 9/4—10',**D['tc']['current']}]
game_rows=[]
for r in D['game_comparison']:
    game_rows.append({'game':r['game'],'bet_prev':r['complete_bet_prev'],'bet_curr':r['complete_bet_curr'],'bet_change_pct':r['bet_change_pct'],'bet_delta':r['bet_delta'],'share_prev':r['bet_share_prev'],'share_curr':r['bet_share_curr'],'share_change_pp':r['bet_share_change_pp'],'rtp_prev':r['actual_rtp_prev'],'rtp_curr':r['actual_rtp_curr'],'rtp_change_pp':r['rtp_change_pp'],'expected_rtp_curr':r['expected_rtp_curr'],'rtp_gap_curr_pp':r['rtp_gap_curr_pp'],'expected_coverage_curr':r['expected_coverage_curr'],'rank_prev':r['rank_prev'],'rank_curr':r['rank_curr']})
new_rows=[];daily=[];life=[]
for g in D['new_games']:
    p,c=g['previous'],g['current'];new_rows.append({'game':g['game'],'launch':g['launch'],'bet_prev':p['complete_bet'],'bet_curr':c['complete_bet'],'bet_change_pct':g['bet_change_pct'],'rtp_prev':p['actual_rtp'],'rtp_curr':c['actual_rtp'],'rtp_change_pp':g['rtp_change_pp'],'expected_rtp_curr':c['expected_rtp'],'rtp_gap_curr_pp':c['rtp_gap_pp']})
    daily.extend({'game':g['game'],**r}for r in g['daily']);life.extend(g['lifecycle'])
queries={
 'tc_week':{'rows':week,'source':tc_source},
 'tc_daily':{'rows':[{'date':r['biz_date'],'period':r['period'],'recharge':r['recharge'],'withdraw':r['withdraw'],'tc_rate':r['tc_rate']}for r in D['tc']['daily']],'source':tc_source},
 'game_compare':{'rows':game_rows,'source':rtp_source},
 'new_games':{'rows':new_rows,'source':rtp_source},
 'new_game_daily':{'rows':daily,'source':rtp_source},
 'lifecycle':{'rows':life,'source':rtp_source},
 'anomalies':{'rows':[{'game':r['game'],'bet':r['complete_bet'],'actual_rtp':r['actual_rtp'],'expected_rtp':r['expected_rtp'],'gap_pp':r['rtp_gap_pp'],'profit_vs_expected':r['profit_vs_expected']}for r in D['anomalies']],'source':rtp_source}
}
snapshot={'surface':'report','title':'Waje TC回升，但EasyWin、Tower与Hilo仍需复核','generatedAt':D['generated_at'],'asOf':'2026-09-10T23:59:59+08:00','buildStatus':'creating','status':'provisional','queries':queries,'notes':['注册渠道TC因当前BigQuery画像无法完整归属，本期不展示，未以未知渠道数据替代。','服务器资金分区与生命周期四表均覆盖至9月10日；源表仍可能回补。']}
(ROOT/'reviewed-snapshot.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2,default=str))
print(json.dumps({'queries':list(queries),'rows':{k:len(v['rows'])for k,v in queries.items()}},ensure_ascii=False))
