import concurrent.futures,csv,io,json,re,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;out=P/'reference';out.mkdir(exist_ok=True)
targets=[('9cd78d','WajeSpecial-facebook',333),('xWsChb','WajeSpecial-googleadwords_int',333),('Cfkonh','WajeSpecial-Google商店',333),('25iiEi','WAJEIOS-AppStore商店',333),('GrWEoo','WAJEBETH5',312),('vkV1SD','wajeH5-facebook',235),('ef19NP','wajeH5ga-googlewords_int',235),('gjy6I1','PWA',411)]
def get(t):
    id,name,end=t;file=out/(id+'.json')
    if file.exists():r=json.loads(file.read_text())
    else:
        r=json.loads(subprocess.check_output(['/Users/robin/.local/node/bin/lark-cli','sheets','+csv-get','--spreadsheet-token','NJNms0exMh4PTvtV0cml1W9ogVd','--sheet-id',id,'--range',f'A1:AQ{end}','--as','user','--format','json']))
        file.write_text(json.dumps(r,ensure_ascii=False,indent=2))
    assert r['ok'] and not r['data']['has_more']
    lines=list(csv.reader(io.StringIO(re.sub(r'^\[row=\d+\] ','',r['data']['annotated_csv'],flags=re.M))))
    headers=lines[0];aug=[]
    for row in lines[1:]:
        if row and re.match(r'^2026/8/\d+$',row[0]):aug.append(dict(zip(headers,row)))
    assert len(aug)==31,(name,len(aug))
    return {'sheet':name,'revision':r['data']['revision'],'rows':aug}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(get,targets))
(P/'channel-reference.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print('Captured 8 complete August channel sheets')
