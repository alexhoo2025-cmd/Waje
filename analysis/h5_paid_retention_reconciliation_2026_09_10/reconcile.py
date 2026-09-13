"""Read-only source capture and cohort-weighted reconciliation; no report writes."""
import concurrent.futures,csv,datetime,io,json,re,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;cli='/Users/robin/.local/node/bin/lark-cli';token='NJNms0exMh4PTvtV0cml1W9ogVd'
targets=[('GrWEoo','WAJEBETH5','A1:BA312'),('vkV1SD','wajeH5-facebook','A1:AR235'),('ef19NP','wajeH5ga-googlewords_int','A1:AR235')]
def collect(t):
    id,name,area=t
    raw=json.loads(subprocess.check_output([cli,'sheets','+csv-get','--spreadsheet-token',token,'--sheet-id',id,'--range',area,'--as','user','--format','json']))
    assert raw.get('ok') and not raw['data'].get('has_more'),name
    (P/(id+'.json')).write_text(json.dumps(raw,ensure_ascii=False,indent=2))
    data=raw['data'];s=re.sub(r'^\[row=\d+\] ','',data['annotated_csv'],flags=re.M);records=list(csv.reader(io.StringIO(s)));headers=records[0]
    rows=[]
    for r in records[1:]:
        if not r:continue
        try:d=datetime.datetime.strptime(r[0],'%Y/%m/%d').date()
        except ValueError:continue
        if d.year==2026 and d.month==8:rows.append((d,{headers[i]:v for i,v in enumerate(r) if i<len(headers)}))
    def num(v):return float(v.replace(',','').strip('%'))
    out={'sheet':name,'sheet_id':id,'revision':data.get('revision'),'august_rows':len(rows),'min':str(min(d for d,r in rows)),'max':str(max(d for d,r in rows)),'headers':headers,'results':[]}
    for weight,fields in [('新增付费人数',['次留','3日留','7日留','15日留']),('首充付费人数',['首充次留','首充3日留','首充7日留','首充15日留'])]:
        for end in [21,27,28,31]:
            selected=[r for d,r in rows if d.day<=end]
            for field in fields:
                valid=[r for r in selected if r.get(field) and r.get(weight)]
                denominator=sum(num(r[weight]) for r in valid)
                val=sum(num(r[weight])*num(r[field]) for r in valid)/denominator if denominator else None
                out['results'].append({'weight':weight,'field':field,'end_day':end,'rows':len(valid),'denominator':denominator,'weighted_pct':val})
    out['august_first_three']=[r for d,r in rows[:3]]
    return out
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(collect,targets))
(P/'comparison.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
for r in results:
    print(r['sheet'],r['august_rows'],r['revision'])
    print(json.dumps([x for x in r['results'] if x['end_day']==31],ensure_ascii=False))
    print(json.dumps(r['august_first_three'][:1],ensure_ascii=False))
