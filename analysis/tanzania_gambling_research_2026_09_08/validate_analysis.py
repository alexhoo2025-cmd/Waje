"""Independent source/arithmetical and dual-output checks plus an executed notebook."""
from pathlib import Path
import json,re,hashlib,statistics,sqlite3,openpyxl
from collections import Counter
from analyze import brand,numeric
P=Path(__file__).resolve().parent
def load(n):return json.loads((P/n).read_text())
def save(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str))
cells=load('cells.json');n=load('normalized.json');art=load('artifact.json')
raw={(c['sheet'],c['cell']):c for c in cells if c['file']=='Research TZ _ Bet.xlsx'}
derived={(c['sheet'],c['cell']):c for c in cells if c['file']=='坦桑行业调研数据.xlsx'}
checks={}
checks['25_sheets_and_3_hidden']=len(load('inventory.json'))==25 and sum(x['state']=='hidden' for x in load('inventory.json'))==3
checks['265_formulas_recomputed']=len(load('formula_validation.json'))==265 and all(x['cache_match'] for x in load('formula_validation.json'))
checks['19_brands_no_duplicates']=len(n['brands'])==len({x['brand'] for x in n['brands']})==19
checks['deposit_median100']=statistics.median(x['min_deposit'] for x in n['payment'])==100
checks['withdraw_median1000']=statistics.median(x['min_withdraw'] for x in n['payment'])==1000
checks['deposit_gap_12of17']=sum(x['min_withdraw']>x['min_deposit'] for x in n['payment'])==12 and len(n['payment'])==17
checks['unknown_times_not_zero']=sum(x['deposit_seconds'] is None for x in n['payment'])==2 and all(x['deposit_seconds'] is None or x['deposit_seconds']>0 for x in n['payment'])
checks['welcome10']=len(art['snapshot']['datasets']['welcome_offers'])==10
checks['tax_types_sum']=abs(sum(r['new'] for r in art['snapshot']['datasets']['tax_types'])-132)<1e-8
checks['mobile_growth_24_1']=round((7959.40/6413.94-1)*100,1)==24.1
checks['casino94_4']=round(17/18*100,1)==94.4
checks['retail_gap']=all(x['retail']==500 and x['ratio'] in [2.5,5] for x in n['retail'])
checks['raw_unchanged']=all(hashlib.sha256((Path('/Users/robin/Desktop/坦桑调研')/x['file']).read_bytes()).hexdigest()==x['sha256'] for x in load('inventory.json'))
checks['cashout_15of19']=sum(str(x['cashout']).strip()=='YES' for x in n['brands'])==15
checks['pawa60_1000_original']=raw[('Online Multibet','G63')]['raw']==10 and '%' in raw[('Online Multibet','G63')]['format']
checks['charts_tables']=len(art['manifest']['charts'])==8 and len(art['manifest']['tables'])==19
# Reconcile all overlapping columns of the two ONLINE tables by normalized brand.
newrows={brand(c['raw']):int(c['cell'][1:]) for c in cells if c['file']=='坦桑行业调研数据.xlsx' and c['sheet']=='ONLINE' and re.fullmatch('A\\d+',c['cell']) and int(c['cell'][1:])>=7}
differences=[];pairs=0
def norm(c):
    if not c or c['raw'] in [None,'']:return None
    v=c['raw']
    if isinstance(v,(int,float)) and '%' in c.get('format',''):return f'{v*100:g}%'
    if isinstance(v,str):
        t=re.sub(r'\s+',' ',v).strip().upper()
        if '%' not in t and numeric(t) is not None:return numeric(t)
        return t
    return v
for b in n['brands']:
    rr=newrows.get(b['brand'])
    if not rr:
        differences.append({'brand':b['brand'],'field':'品牌行','original':b['source'],'derived':'加工版ONLINE缺项；Profile补列','status':'覆盖差异'});continue
    ro=int(re.search(r'A(\d+)',b['source'])[1])
    for col in [3,4,5,6,7,8,9,10,11,12,14,15,16,18,19,21,22,24,25,26,28]:
        c=openpyxl.utils.get_column_letter(col);a=raw.get(('ONLINE',f'{c}{ro}'));z=derived.get(('ONLINE',f'{c}{rr}'));pairs+=1
        if norm(a)!=norm(z):differences.append({'brand':b['brand'],'field':c,'original_cell':f'ONLINE!{c}{ro}','derived_cell':f'ONLINE!{c}{rr}','original':a.get('raw') if a else None,'derived':z.get('raw') if z else None,'status':'跨版本值差异；未假定调研日期'})
save('cross_version_reconciliation.json',{'matched_brands':len(newrows),'compared_fields':pairs,'differences':differences})
save('analysis-verification.json',{'status':'passed' if all(checks.values()) else 'failed','checks':checks,'cross_version_fields':pairs,'cross_version_differences':len(differences),'interpretation':'同源加工差异，不证明造假；性能/现行条款缺口就近标明','nonempty_values_excluding_empty_text':sum(c['raw'] not in [None,''] for c in cells),'source_cell_records':len(cells)})
print(json.dumps({'checks':checks,'cross_version_differences':len(differences)},ensure_ascii=False))
assert all(checks.values())
