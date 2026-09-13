"""Deterministic calculations and cross-sheet evidence; no source workbooks written."""
from pathlib import Path
from collections import Counter
from functools import lru_cache
import json,re,statistics,openpyxl
P=Path(__file__).resolve().parent
def load(n):return json.loads((P/n).read_text())
def save(n,o):(P/n).write_text(json.dumps(o,ensure_ascii=False,indent=2,default=str))
def key(v):return re.sub(r'[^a-z0-9]','',str(v).lower())
ALIASES={'galsportbetting':'GSB','galsportsbetting':'GSB','galsports':'GSB','gsb':'GSB','galsport':'GSB','premier':'Premier Bet','premierbet':'Premier Bet','throne':'Throne Bet','thronebet':'Throne Bet','meridian':'Meridian Bet','meridianbet':'Meridian Bet','playmaster':'PM Bet','pmbet':'PM Bet','betpawa':'betPawa','sportybet':'SportyBet','sportpesa':'SportPesa','betway':'Betway','betika':'Betika','sokabet':'Sokabet','wasafi':'WasafiBet','wasafibet':'WasafiBet','gwalabet':'Gwala Bet','gwala':'Gwala Bet','mbet':'Mbet','winprincess':'WinPrincess Bet','winprincessbet':'WinPrincess Bet','888bet':'888Bet','parimatch':'Parimatch','leonbet':'LeonBet','wibet':'WiBet'}
def brand(v):return ALIASES.get(key(v),str(v).strip())
def grid(s):return {r['row']:r['cells'] for r in load('grid_'+s+'.json')}
def yn(v):
    t=str(v).strip().upper()
    return '有' if t=='YES' or v is True else '无' if t in ['NO','NIL'] or v is False else '未核实'
def numeric(v):
    if isinstance(v,(int,float)):return float(v)
    s=str(v).strip().upper().replace(',','')
    m=re.fullmatch(r'(\d+(?:\.\d+)?)\s*([KMB]?)',s)
    return float(m[1])*{'':1,'K':1e3,'M':1e6,'B':1e9}[m[2]] if m else None
def time_seconds(v):
    m=re.fullmatch(r'(\d+)\s*(sec|min)',str(v).strip(),re.I)
    return int(m[1])*(60 if m[2].lower()=='min' else 1) if m else None
def main():
    bs=load('brands.json'); pg=grid('Payment Methods'); ag=grid('Applications'); sg=grid('Spribe or LLC')
    payment=[]; apps=[]; supplier=[]; ladder=[]; retail=[]; alerts=[]; observations=[]
    for c,v in pg[4].items():
        if c=='A':continue
        row={'brand':brand(v),'min_deposit':pg[6].get(c),'min_withdraw':pg[19].get(c),'max_deposit':pg[7].get(c),'max_withdraw':pg[20].get(c),'deposit_seconds':time_seconds(pg[35].get(c)),'withdraw_seconds':time_seconds(pg[36].get(c)),'deposit_time_record':pg[35].get(c),'withdraw_time_record':pg[36].get(c),'source':f'Payment Methods!{c}4:{c}37'}
        for name,r in {'push':8,'paybill':9,'shortcode':10,'shop':11,'prepaid':12,'phone':13,'agent':14,'bank':15,'card':16,'ewallet':17,'deposit_fee':32,'withdraw_fee':33}.items():row[name]=pg[r].get(c)
        row['ratio']=row['min_withdraw']/row['min_deposit'];payment.append(row)
    for c,v in ag[4].items():
        if c=='A':continue
        apps.append({'brand':brand(v),'android':yn(ag[6].get(c)),'ios':yn(ag[13].get(c)),'playstore':yn(ag[10].get(c)),'appstore':yn(ag[17].get(c)),'source':f'Applications!{c}4:{c}17'})
    for r,row in sg.items():
        if r<2:continue
        supplier.append({'brand':brand(row['A']),'spribe':yn(row.get('B')),'llc':yn(row.get('C')),'related':row.get('E','未记录'),'source':f'Spribe or LLC!A{r}:E{r}'})
    lg=grid('Online Multibet')
    for c,v in lg[2].items():
        if c=='A':continue
        for r,row in lg.items():
            m=re.fullmatch(r'(\d+) games?',str(row.get('A','')).strip(),re.I)
            if not m:continue
            val=row.get(c);n=int(m[1]);ladder.append({'brand':brand(v),'legs':n,'bonus':val if isinstance(val,(float,int)) else None,'raw':val,'odds':lg[3].get(c),'source':f'Online Multibet!{c}{r}','quality':'跨表冲突' if brand(v) in ['SportyBet','SportPesa'] else '材料记录；非现行承诺'})
    bmap={b['brand']:b for b in bs}
    for r,row in grid('RETAIL').items():
        if r<5:continue
        name=brand(row['A']);retail.append({'brand':name,'online':bmap[name]['min_stake'],'retail':row['C'],'delta':row['C']-bmap[name]['min_stake'],'ratio':row['C']/bmap[name]['min_stake'],'source':f'RETAIL!C{r}; '+bmap[name]['source']})
    for r,row in grid('ALERTS').items():
        if r<4 or 'C' not in row:continue
        alerts.append({'brand':brand(row['C']),'stake_web':yn(row.get('D')),'stake_mobile':yn(row.get('E')),'deposit_web':yn(row.get('F')),'deposit_mobile':yn(row.get('G')),'source':f'ALERTS!C{r}:G{r}'})
    # All same-field minimum deposit observations, never resolve by averaging.
    for b in bs:observations.append({'brand':b['brand'],'value':b['min_deposit'],'cell':'ONLINE!'+b['min_deposit_cell']})
    for p in payment:observations.append({'brand':p['brand'],'value':p['min_deposit'],'cell':p['source'].split(':')[0].replace('4','6')})
    tg=grid('Transactions interval')
    for c,v in tg[1].items():
        if c!='A' and brand(v) in bmap:observations.append({'brand':brand(v),'value':tg[6].get(c),'cell':f'Transactions interval !{c}6'})
    conflicts=[]
    for name in bmap:
        o=[x for x in observations if x['brand']==name]
        if len(set(str(x['value']) for x in o))>1:conflicts.append({'brand':name,'field':'最低存款','observations':o})
    stats={
        'payments':{'brands':len(payment),'deposit_median':statistics.median(p['min_deposit'] for p in payment),'withdraw_median':statistics.median(p['min_withdraw'] for p in payment),'withdraw_gt_deposit':sum(p['min_withdraw']>p['min_deposit'] for p in payment),'withdraw_equal_deposit':sum(p['min_withdraw']==p['min_deposit'] for p in payment),'deposit_numeric_n':sum(p['deposit_seconds'] is not None for p in payment),'deposit_numeric_median':statistics.median(p['deposit_seconds'] for p in payment if p['deposit_seconds'] is not None),'withdraw_numeric_n':sum(p['withdraw_seconds'] is not None for p in payment),'withdraw_numeric_median':statistics.median(p['withdraw_seconds'] for p in payment if p['withdraw_seconds'] is not None)},
        'apps':{f:dict(Counter(a[f] for a in apps)) for f in ['android','ios','playstore','appstore']},
        'supplier':{f:dict(Counter(a[f] for a in supplier)) for f in ['spribe','llc']},
        'alerts':{f:dict(Counter(a[f] for a in alerts)) for f in ['stake_web','stake_mobile','deposit_web','deposit_mobile']}}
    save('normalized.json',{'brands':bs,'payment':payment,'apps':apps,'supplier':supplier,'ladder':ladder,'retail':retail,'alerts':alerts,'deposit_conflicts':conflicts,'stats':stats,'aliases':ALIASES})
    # Formula re-evaluation independent of stored caches, recursively following dependencies.
    cells=load('cells.json');d={(x['sheet'],x['cell']):x for x in cells if x['file']=='坦桑行业调研数据.xlsx'}
    def ref(st,current):
        if '!' in st:s,a=st.split('!');return s.strip("'"),a
        return current,st
    def rng(st,current):
        s,a=ref(st,current);a1,a2=a.split(':');lo,ro,hi,rhi=openpyxl.utils.range_boundaries(a)
        return [calc(s,f'{openpyxl.utils.get_column_letter(c)}{r}') for r in range(ro,rhi+1) for c in range(lo,hi+1)]
    @lru_cache(None)
    def calc(s,a):
        x=d.get((s,a),{});v=x.get('raw')
        if x.get('kind')!='f':return v
        f=v[1:]
        if not '(' in f:return calc(*ref(f,s))
        m=re.fullmatch(r'COUNTIF\((.+),"(.*)"\)',f)
        if m:return sum(str(z or '').upper()==m[2].upper() for z in rng(m[1],s))
        m=re.fullmatch(r'COUNTA\((.+?)\)(?:-COUNTIF\((.+),"(.*)"\))?',f)
        if m:return sum(z is not None for z in rng(m[1],s))-(sum(str(z or '').upper()==m[3].upper() for z in rng(m[2],s)) if m[2] else 0)
        m=re.fullmatch(r'IF\(OR\((\w+)="",\w+="NO"\),"NO","YES"\)',f)
        if m:return 'NO' if calc(s,m[1]) in [None,'','NO'] else 'YES'
        m=re.fullmatch(r'IF\((\w+)="YES","YES","NO"\)',f)
        if m:return 'YES' if str(calc(s,m[1])).upper()=='YES' else 'NO'
        raise ValueError(f)
    checks=[]
    for x in load('formulas.json'):
        val=calc(x['sheet'],x['cell']);checks.append({**x,'recomputed':val,'cache_match':val==x['cached'],'semantic_status':'派生指标按公式可复算；业务分类仍须复核'})
    save('formula_validation.json',checks)
    save('calculation_validation.json',{'formula_count':len(checks),'cache_matches':sum(x['cache_match'] for x in checks),'coverage':{'sheets':len(load('inventory.json')),'original_brands':len(bs),'payment_brands':len(payment),'apps_brands':len(apps),'supplier_brands':len(supplier),'ladder_brands':len(set(x['brand'] for x in ladder))},'deposit_conflicts':conflicts,'stats':stats})
    print(json.dumps({'stats':stats,'deposit_conflicts':conflicts,'formula_cache_matches':sum(x['cache_match'] for x in checks)},ensure_ascii=False))
if __name__=='__main__':main()
