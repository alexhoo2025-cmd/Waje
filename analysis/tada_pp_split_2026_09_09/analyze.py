"""Read-only source analysis; outputs only to the new split-report directory."""
from pathlib import Path
import json, csv, math, statistics, hashlib
from collections import defaultdict

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
SRC=ROOT/'analysis/tada_pp_app_h5_actual_2026_09_08'
def load(name): return json.loads((SRC/name).read_text())
def save(name,obj): (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def near(a,b): assert abs(a-b)<=max(1e-6,abs(b)*1e-10),(a,b)
def ranks(vals):
    order=sorted(range(len(vals)),key=lambda i:vals[i]); out=[0.0]*len(vals); i=0
    while i<len(vals):
        j=i+1
        while j<len(vals) and vals[order[j]]==vals[order[i]]: j+=1
        for k in range(i,j): out[order[k]]=(i+j-1)/2+1
        i=j
    return out
def pearson(x,y):
    if len(x)<3:return None
    mx=statistics.mean(x);my=statistics.mean(y)
    den=math.sqrt(sum((v-mx)**2 for v in x)*sum((v-my)**2 for v in y))
    return sum((a-mx)*(b-my) for a,b in zip(x,y))/den if den else None
def spearman(rows,x,y): return pearson(ranks([r[x] for r in rows]),ranks([r[y] for r in rows]))

def main():
    a=load('analysis-results.json');core=load('core-corrected.json');games=a['games']; rawreturns=load('queries/18_full_return.result.json')
    overview=[]
    for r in a['overview']:
        c=next(c for c in core if c['product_mode']=='Waje' and c['time_grain']=='period' and c['segment_grain']=='platform' and c['platform_group']==r['platform'] and c['provider_group']==r['provider'] and c['age_segment']==r['age'])
        near(c['stake'],r['stake']);near(c['payout']/c['stake'],r['settlement_rtp']);near(r['bettors']/r['active_accounts'],r['penetration']);near(r['stake']/r['all_game_stake'],r['all_game_share'])
        overview.append({**r,'stake_yi':r['stake']/1e8,'rounds_wan':r['positive_stake_records']/1e4,'per_bettor_wan':r['stake']/r['bettors']/1e4,'active_days_per_bettor':r['betting_user_days']/r['bettors']})
    returns=[]
    for r in rawreturns:
        if r['platform'] not in ['APP','H5'] or r['cohort_scope']!='summary': continue
        assert r['same_provider_return_accounts']+r['other_provider_only_accounts']+r['no_observed_bet_accounts']==r['eligible_accounts']
        assert 0<=r['any_origin_day_game_return_accounts']<=r['same_provider_return_accounts']
        returns.append({**r,'return_pct':r['same_provider_return_accounts']/r['eligible_accounts']*100,'initial_games_pct':r['any_origin_day_game_return_accounts']/r['eligible_accounts']*100})
    for p in ['APP','H5']:
        for v in ['Tada','PP']:
            for age in ['all_ages','new_30d','old_over_30d']:
                rr=[r for r in returns if r['platform']==p and r['provider']==v and r['age_segment']==age and r['sample_mode']=='common_30d']
                assert len(rr)==5 and len({r['eligible_accounts'] for r in rr})==1
    game_rows=[]
    for r in games:
        if r['platform_group'] not in ['APP','H5']:continue
        n=r['bettors']; rounds=r['positive_stake_records']; stake=r['stake']
        near(stake,float(r['effective_stake_source_units'])/100)
        game_rows.append({**r,'platform':r['platform_group'],'family':'Slot' if r['category'] in ['SLOT','VIDEO SLOT'] else 'Fish' if r['category']=='FISH' else '其他/未匹配','stake_yi':stake/1e8,'per_bettor':stake/n if n else None,'per_bettor_wan':stake/n/1e4 if n else None,'rounds_per_bettor':rounds/n if n else None,'days_per_bettor':r['betting_user_days']/n if n else None,'stake_per_round':stake/rounds if rounds else None,'rtp_pct':r['payout']/stake*100 if stake else None,'mean_game_label':r['game_name']+' ['+r['game_id']+']'})
    counts=[]
    for p in ['APP','H5']:
        for v in ['Tada','PP']:
            r=next(r for r in overview if r['platform']==p and r['provider']==v and r['age']=='all_ages'); g=sorted([g for g in game_rows if g['platform']==p and g['provider']==v],key=lambda g:g['stake'],reverse=True)
            h=sum(x['stake'] for x in g[:5]); near(h,next(hd['top5_stake'] for hd in a['heads'] if hd['platform']==p and hd['provider']==v))
            counts.append({'platform':p,'provider':v,'game_count':r['played_game_count'],'listed_count':len(g),'stake':r['stake'],'listed_stake':sum(g['stake'] for g in g),'coverage':sum(g['stake'] for g in g)/r['stake'],'top5_stake':h,'top5_pct':h/r['stake']*100,'remaining_stake':r['stake']-h,'remaining_count':r['played_game_count']-5,'avg_game_stake':r['stake']/r['played_game_count'],'remaining_avg':(r['stake']-h)/(r['played_game_count']-5)})
    correlations=[];scatter=[]
    for p in ['APP','H5']:
        for v in ['Tada','PP']:
            allg=[g for g in game_rows if g['platform']==p and g['provider']==v and g['stake']>0 and g['bettors']>0 and g['observed_betting_days']>=14]
            for threshold in [30,100,300]:
                sample=[g for g in allg if g['bettors']>=threshold]
                for scope,subset in [('全部已展示品类',sample),('仅Slot',[g for g in sample if g['family']=='Slot']),('剔除组内前5款',sorted(sample,key=lambda g:g['stake'],reverse=True)[5:])]:
                    correlations.append({'platform':p,'provider':v,'min_bettors':threshold,'scope':scope,'n':len(subset),'rho_stake_rtp':spearman(subset,'stake','rtp_pct'),'rho_days_rtp':spearman(subset,'days_per_bettor','rtp_pct'),'rho_rounds_rtp':spearman(subset,'rounds_per_bettor','rtp_pct'),'rho_per_bettor_rtp':spearman(subset,'per_bettor','rtp_pct')})
                if threshold==100:scatter.extend(sample)
    # Same-game cross-channel differences retain each channel's own exact account denominator.
    keyed={(g['provider'],g['game_id'],g['platform']):g for g in game_rows}
    paired=[]
    for (v,gid,p),x in keyed.items():
        if p!='APP' or (v,gid,'H5') not in keyed:continue
        y=keyed[v,gid,'H5']
        if not x['bettors'] or not y['bettors'] or x['stake']<=0 or y['stake']<=0:continue
        paired.append({'provider':v,'game_id':gid,'game_name':x['game_name'],'family':x['family'],'app_stake':x['stake'],'h5_stake':y['stake'],'app_bettors':x['bettors'],'h5_bettors':y['bettors'],'app_per_bettor':x['per_bettor'],'h5_per_bettor':y['per_bettor'],'mean_ratio':x['per_bettor']/y['per_bettor'],'app_rtp':x['rtp_pct'],'h5_rtp':y['rtp_pct'],'rtp_gap_pp':x['rtp_pct']-y['rtp_pct'],'app_days':x['days_per_bettor'],'h5_days':y['days_per_bettor'],'days_gap':x['days_per_bettor']-y['days_per_bettor'],'app_observed_days':x['observed_betting_days'],'h5_observed_days':y['observed_betting_days']})
    daily=[]
    for r in a['daily']:
        if r['provider'] not in ['Tada','PP']:continue
        daily.append({**r,'per_bettor':r['stake']/r['bettors'],'rtp_pct':r['payout']/r['stake']*100})
    daily_corr=[]
    for p in ['APP','H5']:
        for v in ['Tada','PP']:
            rr=sorted([r for r in daily if r['platform']==p and r['provider']==v],key=lambda r:r['date_key']);assert len(rr)==38
            daily_corr.append({'platform':p,'provider':v,'n':38,'rho_stake_rtp':spearman(rr,'stake','rtp_pct'),'rho_per_bettor_rtp':spearman(rr,'per_bettor','rtp_pct'),'rtp_min':min(r['rtp_pct'] for r in rr),'rtp_max':max(r['rtp_pct'] for r in rr)})
    # Golden tests for deterministic correlation implementation.
    assert ranks([1,1,3])==[1.5,1.5,3.0]
    near(spearman([{'a':1,'b':3},{'a':2,'b':2},{'a':3,'b':1}],'a','b'),-1)
    preservation=[]
    for row in json.loads((OUT/'source-inventory.json').read_text())['files']:
        actual=hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest();assert actual==row['sha256'];preservation.append({'path':row['path'],'unchanged':True})
    out={'overview':overview,'returns':returns,'games':game_rows,'counts':counts,'correlations':correlations,'scatter':scatter,'paired':paired,'daily':daily,'daily_correlations':daily_corr,'categories':a['categories'],'decomposition':a['decomposition'],'return_age_decomposition':a['return_age_decomposition'],'quality':a['quality']}
    save('data.json',out);save('analysis-validation.json',{'status':'passed','overview_groups':len(overview),'game_rows':len(game_rows),'correlation_cases':len(correlations),'return_groups':len(returns),'same_game_pairs':len(paired),'rank_unit_tests':'passed','original_preservation':preservation,'additional_queries':'blocked_authentication','independent_review':'auth_required','same_game_fixed_day_return':'unavailable_in_saved_aggregates'})
    for name,rows in [('游戏明细.csv',game_rows),('同游戏跨渠道.csv',paired),('关联复算.csv',correlations)]:
        with (OUT/name).open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps({'counts':counts,'correlations':[r for r in correlations if r['min_bettors']==100 and r['scope']=='全部已展示品类'],'daily':daily_corr,'scatter_ranges':{'rtp':[min(r['rtp_pct'] for r in scatter),max(r['rtp_pct'] for r in scatter)],'days':[min(r['days_per_bettor'] for r in scatter),max(r['days_per_bettor'] for r in scatter)]}},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
