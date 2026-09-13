#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent;load=lambda n:json.loads((ROOT/n).read_text())
daily=load('queries/01_tc_daily_channel.result.json')['rows'];daily=[r for r in daily if r['row_type']=='daily'and'2026-09-04'<=r['biz_date']<='2026-09-10']
dist=load('queries/04_tc_distribution.result.json')['rows'];hour=load('queries/06_tc_3hour.result.json')['rows'];users=load('queries/07_tc_daily_users.result.json')['rows'];methods=load('queries/03_tc_hour_method.result.json')['rows'];clients=load('queries/08_tc_event_client.result.json')['rows']
target=next(r for r in daily if r['biz_date']=='2026-09-10');base=[r for r in daily if r['biz_date']<'2026-09-10']
avg=lambda rows,key:sum(r[key]for r in rows)/len(rows);R0,W0=avg(base,'recharge'),avg(base,'withdraw');R1,W1=target['recharge'],target['withdraw'];tc0=W0/R0;tc1=W1/R1
withdraw_effect=(W1-W0)/R1*100;recharge_effect=(W0/R1-W0/R0)*100
def daily_users(metric):
    rows=[r for r in users if r['metric']==metric];t=next(r for r in rows if r['biz_date']=='2026-09-10');b=[r for r in rows if r['biz_date']<'2026-09-10'];return {'target':t,**{f'base_{k}':avg(b,k)for k in ['users','transactions','amount','amount_per_user','transactions_per_user']}}
withdraw_user=daily_users('提现');recharge_user=daily_users('充值')
def stat(metric,kind='交易分布'):
    rows=[r for r in dist if r['metric']==metric and r['row_type']==kind];return next(r for r in rows if r['period']=='9月10日'),next(r for r in rows if r['period']=='9月4—9日')
withdraw_stat,withdraw_stat6=stat('提现');recharge_stat,recharge_stat6=stat('充值')
bands={}
for metric in ['充值','提现']:
    rows=[r for r in dist if r['metric']==metric and r['row_type']=='金额档位'];out=[]
    for band in ['<1千','1千—5千','5千—2万','2万—10万','10万及以上']:
        t=next(r for r in rows if r['period']=='9月10日'and r['bucket']==band);b=next(r for r in rows if r['period']=='9月4—9日'and r['bucket']==band);bavg=b['total_amount']/6;out.append({'band':band,'target_amount':t['total_amount'],'base_daily_avg':bavg,'increment':t['total_amount']-bavg,'change_pct':t['total_amount']/bavg-1})
    bands[metric]=out
withdraw_increase=W1-W0;high_withdraw=sum(r['increment']for r in bands['提现']if r['band']in['2万—10万','10万及以上'])
time_rows=[]
for band in sorted(set(r['time_band']for r in hour)):
    wt=next(r for r in hour if r['metric']=='提现'and r['period']=='9月10日'and r['time_band']==band);wb=next(r for r in hour if r['metric']=='提现'and r['period']=='9月4—9日'and r['time_band']==band);rt=next(r for r in hour if r['metric']=='充值'and r['period']=='9月10日'and r['time_band']==band);rb=next(r for r in hour if r['metric']=='充值'and r['period']=='9月4—9日'and r['time_band']==band)
    time_rows.append({'time_band':band,'withdraw_target':wt['amount'],'withdraw_base_daily_avg':wb['amount']/6,'withdraw_increment':wt['amount']-wb['amount']/6,'recharge_target':rt['amount'],'recharge_base_daily_avg':rb['amount']/6,'tc_target':wt['amount']/rt['amount'],'tc_base':(wb['amount']/6)/(rb['amount']/6)})
method_rows=[]
for name in sorted(set(r['bucket']for r in methods if r['row_type']=='方式'and r['metric']=='充值')):
    t=next(r for r in methods if r['row_type']=='方式'and r['metric']=='充值'and r['period']=='9月10日'and r['bucket']==name);b=next(r for r in methods if r['row_type']=='方式'and r['metric']=='充值'and r['period']=='9月4—9日'and r['bucket']==name);method_rows.append({'method':name,'target_amount':t['amount'],'base_daily_avg':b['amount']/6,'increment':t['amount']-b['amount']/6})
result={'generated_at':datetime.now(timezone.utc).isoformat(),'status':'diagnosed_with_declared_dimension_limits','business_date':'2026-09-10','timezone':'Africa/Lagos','comparison':'2026-09-04 through 2026-09-09 daily average','headline':{'tc_target':tc1,'tc_base_daily_average':tc0,'change_pp':(tc1-tc0)*100,'recharge_target':R1,'recharge_base_daily_average':R0,'recharge_change_pct':R1/R0-1,'withdraw_target':W1,'withdraw_base_daily_average':W0,'withdraw_change_pct':W1/W0-1,'withdraw_numerator_effect_pp':withdraw_effect,'recharge_denominator_effect_pp':recharge_effect},'frequency_and_value':{'withdraw_users_change_pct':withdraw_user['target']['users']/withdraw_user['base_users']-1,'withdraw_transactions_change_pct':withdraw_user['target']['transactions']/withdraw_user['base_transactions']-1,'withdraw_amount_per_user_change_pct':withdraw_user['target']['amount_per_user']/withdraw_user['base_amount_per_user']-1,'withdraw_transactions_per_user_change_pct':withdraw_user['target']['transactions_per_user']/withdraw_user['base_transactions_per_user']-1,'withdraw_mean_transaction_change_pct':withdraw_stat['mean_amount']/withdraw_stat6['mean_amount']-1,'recharge_users_change_pct':recharge_user['target']['users']/recharge_user['base_users']-1,'recharge_transactions_change_pct':recharge_user['target']['transactions']/recharge_user['base_transactions']-1,'recharge_amount_per_user_change_pct':recharge_user['target']['amount_per_user']/recharge_user['base_amount_per_user']-1,'recharge_mean_transaction_change_pct':recharge_stat['mean_amount']/recharge_stat6['mean_amount']-1},'concentration':{'withdraw_p99_target':withdraw_stat['p99'],'withdraw_p99_base':withdraw_stat6['p99'],'withdraw_top_1pct_share_target':withdraw_stat['top_1pct_share'],'withdraw_top_1pct_share_base':withdraw_stat6['top_1pct_share'],'withdraw_20k_plus_increment':high_withdraw,'withdraw_20k_plus_share_of_increment':high_withdraw/withdraw_increase,'recharge_p99_target':recharge_stat['p99'],'recharge_p99_base':recharge_stat6['p99'],'recharge_top_1pct_share_target':recharge_stat['top_1pct_share'],'recharge_top_1pct_share_base':recharge_stat6['top_1pct_share']},'amount_bands':bands,'three_hour':time_rows,'recharge_methods':sorted(method_rows,key=lambda r:r['increment'],reverse=True),'data_quality':{'server_partition_complete':True,'target_partition_last_modified':'2026-09-10T23:00:31.235Z','timestamp_parse':'13-digit epoch milliseconds; hourly conversion uses Africa/Lagos','hourly_local_time_source':'server event time converted to Africa/Lagos','channel_attribution':'blocked; no complete historical registration-channel dimension within approved scan scope','event_client_attribution':'blocked; all successful server money events have unknown client_type in this source','event_client_rows':clients,'raw_identifiers_returned':False,'causality':'accounting decomposition only; user motives and operational causes not observed'}}
(ROOT/'tc-2026-09-10-diagnostic.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
fmt=lambda v:f'{v*100:.1f}%';money=lambda v:f'{v/1e6:.2f}百万'
md=f'''# 9月10日TC超过83%的原因拆解

9月10日TC为{fmt(tc1)}，较9月4—9日日均{fmt(tc0)}高{(tc1-tc0)*100:.2f}个百分点。提现增加贡献+{withdraw_effect:.2f}个百分点，充值增加抵消{abs(recharge_effect):.2f}个百分点。

核心原因是大额提现集中：提现金额增长{fmt(W1/W0-1)}，提现用户增长{fmt(result['frequency_and_value']['withdraw_users_change_pct'])}，人均提现增长{fmt(result['frequency_and_value']['withdraw_amount_per_user_change_pct'])}。2万元以上提现贡献{fmt(high_withdraw/withdraw_increase)}的提现增量，提现前1%大额订单占比由{fmt(withdraw_stat6['top_1pct_share'])}升至{fmt(withdraw_stat['top_1pct_share'])}。

时段上，15:00—17:59提现增量最大，为{money(max(time_rows,key=lambda r:r['withdraw_increment'])['withdraw_increment'])}；其余增量分散在00:00—02:59、09:00—11:59和21:00—23:59，不是单一时段故障。

渠道归属未完整，不据此判断某个渠道导致高TC；用户动机、提现审核或活动影响仍需业务事实验证。'''
(ROOT/'tc-2026-09-10-diagnostic.md').write_text(md)
print(json.dumps({'status':result['status'],'tc':result['headline'],'concentration':result['concentration'],'top_time':max(time_rows,key=lambda r:r['withdraw_increment']),'top_methods':result['recharge_methods'][:3]},ensure_ascii=False))
