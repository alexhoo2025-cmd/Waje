import collections,datetime,json,math
from pathlib import Path
P=Path(__file__).resolve().parent;load=lambda f:json.loads((P/f).read_text())
mapping=load('channels.json');den=load('01_origin_denominators.result.json')['rows'];ret=load('05_full_origin_returns.result.json')['rows'];aux=load('06_origin_reg_first.result.json')['rows'];ct=load('09_origin_ct.result.json')['rows'];overlap=load('07_key_overlap.result.json')['rows']
assert all(r['multiple_sheets']==0 and r['multiple_dates']==0 and r['multiple_counterparts']==0 for r in overlap)
cutoff=datetime.date(2026,9,9);keys=['APP','H5','PWA候选'];groups={g:[r['sheet'] for r in mapping if r['group']==g] for g in keys}
units={r['sheet']:[r['sheet']] for r in mapping};units.update(groups)
def counts(sheets,field,end='2026-08-31'):
    return sum(r[field] for r in den if r['sheet'] in sheets and r['cohort_date']<=end)
def auxcount(sheets,metric,end):return sum(r['users'] for r in aux if r['sheet'] in sheets and r['metric']==metric and r['cohort_date']<=end)
result=[]
for name,sheets in units.items():
    for pop in ['新增付费','首次付费','全部新增']:
        for mode in ['各日达标范围','固定8月1—26日']:
            for d in list(range(2,16))+([30] if mode=='各日达标范围' else []):
                rs=[r for r in ret if r['sheet'] in sheets and r['population']==pop and r['sample_mode']==mode and r['day_number']==d]
                assert len(rs)==len(sheets),(name,pop,mode,d)
                end=min('2026-08-31',str(cutoff-datetime.timedelta(days=d-1)))
                if mode=='固定8月1—26日':end=min(end,'2026-08-26')
                n=auxcount(sheets,'首充用户',end) if pop=='首次付费' else counts(sheets,'new_paid_xl_ids' if pop=='新增付费' else 'new_xl_ids',end)
                k=sum(r['returned_xl_ids'] for r in rs)
                if pop!='首次付费':assert n==sum(r['eligible_xl_ids'] for r in rs)
                assert 0<=k<=n and n>=10
                result.append({'unit':name,'population':pop,'sample_mode':mode,'day':d,'denominator':n,'returned':k,'rate_pct':100*k/n,'cohort_end':end})
for name in units:
 for pop in ['新增付费','首次付费','全部新增']:
  assert len({r['denominator'] for r in result if r['unit']==name and r['population']==pop and r['sample_mode']=='固定8月1—26日'})==1
summary=[]
for name,sheets in units.items():
    registered=auxcount(sheets,'注册用户','2026-08-31');paid=counts(sheets,'new_paid_xl_ids');first=auxcount(sheets,'首充用户','2026-08-31')
    summary.append({'unit':name,'new_xl_ids':counts(sheets,'new_xl_ids'),'registered_user_days':registered,'new_paid_xl_ids':paid,'first_pay_user_days':first,'new_paid_rate_pct':100*paid/registered,'first_pay_rate_pct':100*first/registered})
value=[]
for name,sheets in units.items():
 for day in [1,7,14,15,30]:
    end=min('2026-08-31',str(cutoff-datetime.timedelta(days=day-1)));n=counts(sheets,'new_xl_ids',end);total=sum(r['ct_'+str(day)] for r in ct if r['sheet'] in sheets and r['cohort_date']<=end)
    value.append({'unit':name,'day':day,'cohort_end':end,'new_xl_ids':n,'cumulative_ct':total,'mean_ct':total/n})
decay=[]
for name in keys:
 for pop in ['新增付费','首次付费']:
    rr=sorted([r for r in result if r['unit']==name and r['population']==pop and r['sample_mode']=='固定8月1—26日'],key=lambda x:x['day']);prev=100
    for r in rr:
        decay.append({'unit':name,'population':pop,'day':r['day'],'rate_pct':(prev-r['rate_pct'])/prev*100});prev=r['rate_pct']
out={'summary':summary,'retention':result,'value':value,'decay':decay,'groups':groups,'cutoff':'2026-09-09','qa':{'cross_channel_overlap':0,'all_rates_in_bounds':True,'fixed_denominators_constant':True,'origin_count_units_preserved':True,'old_report_baseline_not_compared_as_trend':True}}
(P/'analysis.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps({'summary':[r for r in summary if r['unit'] in keys],'value':[r for r in value if r['unit']in keys and r['day']in[15,30]]},ensure_ascii=False))
