"""Recompute reviewed report datasets; retain source snapshots unchanged."""
from pathlib import Path
from decimal import Decimal as D
from datetime import date,timedelta
from itertools import permutations
import json,csv,statistics,collections,copy

P=Path(__file__).resolve().parent
def load(name):return json.loads((P/'queries'/f'{name}.result.json').read_text())
def write(name,value):(P/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,default=str)+'\n')
def num(x):return D(str(x or 0))
def week(day):
    d=date.fromisoformat(day);return (d-timedelta(days=d.weekday())).isoformat()

def main():
    raw=load('14_full_core');core=copy.deepcopy(raw);corrections=load('21_targeted_duplicate_corrections')
    assert all(x['duplicate_records_with_conflicting_amounts']==0 for x in corrections)
    cc=[x for x in corrections if x['correction_grain']=='core_correction']
    assert sum(x['duplicate_records'] for x in cc)==sum(x['duplicate_records'] for x in corrections if x['correction_grain']=='quality_total')==72
    money_map={'effective_stake_source_units':'duplicate_stake_source_units','settlement_source_units':'duplicate_settlement_source_units',
               'extra_source_units':'duplicate_extra_source_units','refund_source_units':'duplicate_refund_source_units'}
    def matches(r,c):
        if r['product_mode']!=c['product_mode']:return False
        if r['time_grain']=='daily' and r['date_key']!=c['stat_date']:return False
        if r['time_grain']=='weekly' and r['date_key']!=week(c['stat_date']):return False
        if r['segment_grain']=='platform' and r['platform_group']!=c['platform']:return False
        if r['segment_grain']=='subplatform' and r['platform_group']!=c['channel_platform']:return False
        if r['provider_group']!='all_games' and r['provider_group']!=c['provider']:return False
        if r['age_segment']!='all_ages' and r['age_segment']!=c['age_group']:return False
        return True
    for r in core:
        applicable=[c for c in cc if matches(r,c)]
        for field,cf in money_map.items():r[field]=str(num(r[field])-sum((num(c[cf]) for c in applicable),D(0)))
        r['settlement_records']-=sum(c['duplicate_records'] for c in applicable)
        r['positive_stake_records']-=sum(c['duplicate_positive_records'] for c in applicable)
        r['stake']=float(num(r['effective_stake_source_units'])/100)
        r['payout']=float(num(r['settlement_source_units'])/100)
        r['settlement_rtp']=r['payout']/r['stake'] if r['stake'] else None
        r['gaming_margin']=float((num(r['effective_stake_source_units'])-num(r['settlement_source_units']))/100)
        r['avg_rounds_per_bettor']=r['positive_stake_records']/r['bettors'] if r['bettors'] else None
        r['avg_stake_per_round']=r['stake']/r['positive_stake_records'] if r['positive_stake_records'] else None
    write('core-corrected.json',core)
    active=load('16_full_active_base');returns=load('18_full_return');finance=load('22_full_finance')
    def get(plat,provider,age='all_ages',grain='platform'):
        return next(r for r in core if r['product_mode']=='Waje' and r['time_grain']=='period' and r['segment_grain']==grain and r['platform_group']==plat and r['provider_group']==provider and r['age_segment']==age)
    def getactive(plat,age='all_ages'):
        return next(r['active_accounts'] for r in active if r['time_grain']=='period' and r['segment_grain']=='platform' and r['platform_group']==plat and r['age_segment']==age)
    overview=[]
    for plat in ['APP','H5']:
        for age in ['all_ages','new_30d','old_over_30d']:
            pair=sum(get(plat,p,age)['stake'] for p in ['Tada','PP']);denom=get(plat,'all_games',age)['stake']
            for provider in ['Tada','PP']:
                r=copy.deepcopy(get(plat,provider,age));r.update(platform=plat,provider=provider,age=age,
                    active_accounts=getactive(plat,age),all_game_stake=denom,pair_stake=pair,
                    all_game_share=r['stake']/denom,pair_share=r['stake']/pair,
                    penetration=r['bettors']/getactive(plat,age),combo=f'{plat} · {provider}')
                assert 0<=r['penetration']<=1
                overview.append(r)
    daily=[]
    for r in core:
        if r['product_mode']=='Waje' and r['time_grain']=='daily' and r['segment_grain']=='platform' and r['platform_group'] in ['APP','H5']:
            d=copy.deepcopy(r);d['platform']=r['platform_group'];d['provider']=r['provider_group'];daily.append(d)
    for r in daily:
        if r['provider']!='all_games':
            r['all_game_share']=r['stake']/next(x['stake'] for x in daily if x['date_key']==r['date_key'] and x['platform']==r['platform'] and x['provider']=='all_games')
    assert all(len([r for r in daily if r['platform']==p and r['provider']==v])==38 for p in ['APP','H5'] for v in ['Tada','PP','all_games'])
    rr=[]
    for r in returns:
        assert r['same_provider_return_accounts']+r['other_provider_only_accounts']+r['no_observed_bet_accounts']==r['eligible_accounts']
        assert 0<=r['any_origin_day_game_return_accounts']<=r['same_provider_return_accounts']<=r['eligible_accounts']
        if r['platform'] in ['APP','H5']:
            x=copy.deepcopy(r);x['return_rate']=x['same_provider_return_accounts']/x['eligible_accounts'];x['combo']=f"{x['platform']} · {x['provider']}";rr.append(x)
    games=copy.deepcopy(load('17_full_games'));gc=[x for x in corrections if x['correction_grain']=='game_correction' and x['product_mode']=='Waje']
    dictionary={r['game_id']:r for r in csv.DictReader(Path('analysis/game_code_dictionary_2026_08_31/game_code_name_mapping.csv').open())}
    for r in games:
        cs=[c for c in gc if c['provider']==r['provider'] and c['play_id']==r['play_id'] and (c['platform']==r['platform_group'] or r['platform_group']=='APP_H5_combined' and c['platform'] in ['APP','H5'])]
        r['effective_stake_source_units']=str(num(r['effective_stake_source_units'])-sum((num(c['duplicate_stake_source_units']) for c in cs),D(0)))
        r['settlement_source_units']=str(num(r['settlement_source_units'])-sum((num(c['duplicate_settlement_source_units']) for c in cs),D(0)))
        r['positive_stake_records']-=sum(c['duplicate_positive_records'] for c in cs)
        gid=str(r['play_id']-9110000);ref=dictionary.get(gid,{})
        r.update(game_id=gid,game_name=ref.get('game_name',f'游戏{gid}'),category=ref.get('game_type','未匹配品类').upper(),
          size_mb=float(ref['game_size_mb']) if ref.get('game_size_mb') else None,
          stake=float(num(r['effective_stake_source_units'])/100),payout=float(num(r['settlement_source_units'])/100),dictionary_matched=bool(ref))
        r['rtp']=r['payout']/r['stake'] if r['stake'] else None
    categories=[];heads=[];sizes=[];common_games=[]
    for plat in ['APP','H5']:
        for provider in ['Tada','PP']:
            rows=[r for r in games if r['platform_group']==plat and r['provider']==provider];total=get(plat,provider)['stake']
            for cat in sorted({r['category'] for r in rows}):
                a=[r for r in rows if r['category']==cat];stake=sum(r['stake'] for r in a)
                categories.append({'platform':plat,'provider':provider,'category':cat,'stake':stake,'provider_stake':total,'share':stake/total,'released_game_count':len(a)})
            rows.sort(key=lambda r:r['stake'],reverse=True)
            head5=sum(r['stake'] for r in rows[:5]);head10=sum(r['stake'] for r in rows[:10]);released=sum(r['stake'] for r in rows)
            heads.append({'platform':plat,'provider':provider,'total_stake':total,'top5_stake':head5,'top5_share':head5/total,
              'top10_share':head10/total,'excluding_top5_stake':total-head5,'released_stake_coverage':released/total,
              'catalogue_stake_coverage':sum(r['stake'] for r in rows if r['dictionary_matched'])/total})
            for rank,r in enumerate(rows):r['rank']=rank+1;r['provider_share']=r['stake']/total
    for provider in ['Tada','PP']:
        rows=[r for r in games if r['platform_group']=='APP_H5_combined' and r['provider']==provider and r['size_mb'] is not None]
        sizes.append({'provider':provider,'matched_games':len(rows),'median_mb':statistics.median(r['size_mb'] for r in rows),
            'min_mb':min(r['size_mb'] for r in rows),'max_mb':max(r['size_mb'] for r in rows),
            'stake_weighted_mb':sum(r['stake']*r['size_mb'] for r in rows)/sum(r['stake'] for r in rows)})
        app={r['game_id']:r for r in games if r['platform_group']=='APP' and r['provider']==provider}
        h5={r['game_id']:r for r in games if r['platform_group']=='H5' and r['provider']==provider}
        for gid in app.keys()&h5.keys():
            a,b=app[gid],h5[gid]
            common_games.append({'provider':provider,'game_id':gid,'game_name':a['game_name'],'category':a['category'],
                'app_stake':a['stake'],'h5_stake':b['stake'],'app_bettors':a['bettors'],'h5_bettors':b['bettors'],
                'app_rtp':a['rtp'],'h5_rtp':b['rtp'],'app_share':a['stake']/get('APP',provider)['stake'],
                'h5_share':b['stake']/get('H5',provider)['stake'],'size_mb':a['size_mb']})
    decomp=[]
    for plat in ['APP','H5']:
        a=get(plat,'PP');b=get(plat,'Tada');names=['下注人数','人均下注局次','局均下注金额']
        lo=[a['bettors'],a['avg_rounds_per_bettor'],a['avg_stake_per_round']]
        hi=[b['bettors'],b['avg_rounds_per_bettor'],b['avg_stake_per_round']]
        contributions=[0.,0.,0.]
        def product(v):return v[0]*v[1]*v[2]
        for order in permutations(range(3)):
            values=lo.copy()
            for i in order:
                before=product(values);values[i]=hi[i];contributions[i]+=(product(values)-before)/6
        assert abs(sum(contributions)-(b['stake']-a['stake']))<0.001
        for i,name in enumerate(names):decomp.append({'platform':plat,'driver':name,'contribution':contributions[i],
            'share_of_gap':contributions[i]/(b['stake']-a['stake']),'tada_pp_ratio':hi[i]/lo[i],
            'pp_stake':a['stake'],'tada_stake':b['stake'],'gap':b['stake']-a['stake']})
    return_mix=[]
    for provider in ['Tada','PP']:
        for obs in [2,7,30]:
            cells={}
            for plat in ['APP','H5']:
                for age in ['new_30d','old_over_30d']:
                    cells[plat,age]=next(r for r in rr if r['platform']==plat and r['provider']==provider and r['sample_mode']=='common_30d' and r['cohort_scope']=='summary' and r['age_segment']==age and r['observation_day']==obs)
            totals={plat:sum(cells[plat,a]['eligible_accounts'] for a in ['new_30d','old_over_30d']) for plat in ['APP','H5']}
            mix=within=0.0
            for age in ['new_30d','old_over_30d']:
                a,b=cells['APP',age],cells['H5',age]
                wa,wb=a['eligible_accounts']/totals['APP'],b['eligible_accounts']/totals['H5']
                mix+=(wa-wb)*(a['return_rate']+b['return_rate'])/2
                within+=(a['return_rate']-b['return_rate'])*(wa+wb)/2
            rates={plat:sum(cells[plat,a]['same_provider_return_accounts'] for a in ['new_30d','old_over_30d'])/totals[plat] for plat in ['APP','H5']}
            assert abs(mix+within-rates['APP']+rates['H5'])<1e-12
            return_mix.append({'provider':provider,'day':obs,'app_rate_known_age':rates['APP'],'h5_rate_known_age':rates['H5'],
                'gap':rates['APP']-rates['H5'],'mix_effect':mix,'within_age_effect':within,
                'app_eligible_known_age':totals['APP'],'h5_eligible_known_age':totals['H5']})
    quality={
      'status':'core_results_validated_with_named_gaps', 'window':['2026-08-01','2026-09-07'],
      'main_mode':'mode_id=11 Waje; WajeCoin and other modes separately excluded',
      'duplicate_correction_applied':True,'waje_duplicate_records_removed':67,
      'conflicting_duplicate_amounts':0,'returns_state_sum_checks':len(returns),
      'key_grain':'business_date × account × game × round × hand',
      'main_channel_unmapped_stake_share':get('unmapped','all_games')['stake']/get('all_platforms','all_games',grain='all_platforms')['stake'],
      'pwa_named_stake_share':get('PWA_named','all_games')['stake']/get('all_platforms','all_games',grain='all_platforms')['stake'],
      'formal_tc':'not_certified; final bank payout status and wallet currency mapping required',
      'rtp':'settlement return ratio; cash/reward assets not separable in joint GAMEEND',
      'same_game_return':'any game played on the origin day; not arbitrary minimum game ID',
      'causality':'channel attribution and game catalogue size do not establish runtime or loading causality',
      'independent_review':'Sonnet auth_required; no reviewer result',
    }
    finance_out=[r for r in finance if r['time_grain']=='period' and r['event_type']=='ORDER' and r['platform_group'] in ['APP','H5'] and r['age_segment'] in ['all_ages','new_30d','old_over_30d']]
    out={'overview':overview,'daily':daily,'returns':rr,'games':games,'categories':categories,'heads':heads,'sizes':sizes,
         'common_games':common_games,'decomposition':decomp,'return_age_decomposition':return_mix,'finance':finance_out,'quality':quality}
    write('analysis-results.json',out);write('analytical-validation.json',quality)
    print(json.dumps({'overview_rows':len(overview),'daily_rows':len(daily),'return_rows':len(rr),'games':len(games),
      'heads':heads,'sizes':sizes,'decomposition':decomp,'quality':quality},ensure_ascii=False,default=str))

if __name__=='__main__':main()
