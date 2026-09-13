import json
from pathlib import Path
P=Path(__file__).resolve().parent
refs=json.loads((P/'channel-reference.json').read_text());den=json.loads((P/'01_origin_denominators.result.json').read_text())['rows'];aux=json.loads((P/'06_origin_reg_first.result.json').read_text())['rows'];ret=json.loads((P/'05_full_origin_returns.result.json').read_text())['rows']
num=lambda v:float(v.replace(',','').strip('%'))
pct=lambda v:num(v) if '%' in v else num(v)*100
results=[]
for ref in refs:
    sheet=ref['sheet'];rows=ref['rows'];d=[r for r in den if r['sheet']==sheet];q=[r for r in aux if r['sheet']==sheet and r['metric']=='首充用户']
    item={'sheet':sheet,'source_revision':ref['revision'],'new_count_delta':sum(r['new_xl_ids'] for r in d)-sum(num(r['新增人数']) for r in rows),'paid_count_delta':sum(r['new_paid_xl_ids'] for r in d)-sum(num(r['新增付费人数']) for r in rows),'first_pay_count_delta':sum(r['users'] for r in q)-sum(num(r['首充付费人数']) for r in rows),'rates':[]}
    for pop,weight,fields in [('新增付费','新增付费人数',[(2,'次留'),(7,'7日留')]),('首次付费','首充付费人数',[(2,'首充次留'),(7,'首充7日留')])]:
        for day,field in fields:
            srcrate=sum(num(r[weight])*pct(r[field]) for r in rows)/sum(num(r[weight]) for r in rows)
            r=next(r for r in ret if r['sheet']==sheet and r['population']==pop and r['sample_mode']=='各日达标范围' and r['day_number']==day)
            divisor=r['eligible_xl_ids'] if pop=='新增付费' else sum(r['users'] for r in q)
            actual=100*r['returned_xl_ids']/divisor
            item['rates'].append({'population':pop,'day':day,'reference_pct':srcrate,'queried_pct':actual,'difference_pp':actual-srcrate})
    results.append(item)
(P/'reference-reconciliation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print(json.dumps(results,ensure_ascii=False))
