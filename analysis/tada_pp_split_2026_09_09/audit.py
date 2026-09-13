from pathlib import Path
import json,hashlib,math,statistics
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
def read(p):return json.loads(p.read_text())
data=read(P/'data.json');inventory=read(P/'source-inventory.json');checks=[]
for f in inventory['files']:
 actual=hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest();assert actual==f['sha256'];checks.append({'requirement':'保留原版本','evidence':f['path'],'passed':True})
for slug in ['macro','detail']:
 a=read(P/slug/'artifact.json');rec=read(P/slug/'delivery-receipt.json');assert rec['ok'] and rec['stages']['verification']=='passed';assert rec['report_quality']['errors']==0
 assert rec['report_quality']['input_sha256']==hashlib.sha256((P/slug/'artifact.json').read_bytes()).hexdigest()
 assert len(a['manifest']['blocks'][1]['body'].split('\n\n'))==4
 assert '2026-08-01' in a['manifest']['reportContract']['period'];assert a['manifest']['reportContract']['timezone']=='Africa/Lagos'
 assert (P/slug/'报告.md').exists();checks.append({'requirement':slug+'的结构/渲染/来源/窄屏','evidence':slug+'/delivery-receipt.json','passed':True})
macro=read(P/'macro/artifact.json');detail=read(P/'detail/artifact.json')
assert len(macro['manifest']['charts'])==5;assert len(detail['manifest']['charts'])==6
for age in ['new_30d','old_over_30d']:
 assert len(macro['snapshot']['datasets']['table-'+age])==4
 assert len(macro['snapshot']['datasets']['ret-'+age])==3
checks.append({'requirement':'宏观按新老与APP/H5×厂商分组展示下注/局次/人数/份额/回访','evidence':'macro/artifact.json table-new_30d/table-old_over_30d/ret-new_30d/ret-old_over_30d','passed':True})
assert len(detail['snapshot']['datasets']['all-games'])==len(data['games'])==1081
assert len(detail['snapshot']['datasets']['game-profiles'])==10
assert len(detail['snapshot']['datasets']['correlation'])==4
assert len(detail['snapshot']['datasets']['rtp-replay'])==110
assert len(detail['snapshot']['datasets']['return-layers'])==4
checks.append({'requirement':'细分游戏/人均深度/RTP/关联/回访集合/完整明细','evidence':'detail/artifact.json','passed':True})
# Independent rank implementation: count lower and equal observations, not sorted tie blocks.
def rank2(x):return [1+sum(b<a for b in x)+(sum(b==a for b in x)-1)/2 for a in x]
def corr2(x,y):
 a=rank2(x);b=rank2(y);ma=statistics.mean(a);mb=statistics.mean(b)
 return sum((x-ma)*(y-mb) for x,y in zip(a,b))/math.sqrt(sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b))
for group in [r for r in data['correlations'] if r['min_bettors']==100 and r['scope']=='全部已展示品类']:
 sample=[r for r in data['scatter'] if r['platform']==group['platform'] and r['provider']==group['provider']]
 assert len(sample)==group['n']
 for field,key in [('stake','rho_stake_rtp'),('days_per_bettor','rho_days_rtp'),('per_bettor','rho_per_bettor_rtp'),('rounds_per_bettor','rho_rounds_rtp')]:assert abs(corr2([r[field] for r in sample],[r['rtp_pct'] for r in sample])-group[key])<1e-12
checks.append({'requirement':'关联独立算法复算','evidence':'audit.py lower/equal rank algorithm vs analyze.py sorted tie ranks','passed':True})
for g in data['games']:
 if g['bettors']:
  assert 1<=g['days_per_bettor']<=38
  assert g['rounds_per_bettor']>=1
  assert abs(g['per_bettor']*g['bettors']-g['stake'])<max(1e-5,abs(g['stake'])*1e-12)
nb=read(P/'复算与校验.ipynb');code=[c for c in nb['cells'] if c['cell_type']=='code'];assert all(c.get('execution_count') for c in code);assert not any(o.get('output_type')=='error' for c in code for o in c.get('outputs',[]))
checks.append({'requirement':'可复算数据与执行笔记','evidence':'复算与校验.ipynb/data.json/关联复算.csv','passed':True})
text=(P/'detail/报告.md').read_text();assert '下注笔数' in text and '单款游戏' in text and '未取得授权连接' in text and '因果' in text
checks.append({'requirement':'缺口明确不伪造','evidence':'detail/报告.md section 01/05','passed':True})
result={'status':'passed_with_explicit_data_limits','checks':checks,'scope':'best-effort source-backed split; not completion of unavailable new warehouse research','required_files':[str(P/'macro/artifact.json'),str(P/'detail/artifact.json')],'limits':['单游戏独立起点定日回访尚未取得；首日游戏集合回访明确标注','原始下注笔数不可靠，报告仅使用有效局次','游戏级相关和复玩强度不作为用户级RTP回访因果','BigQuery与独立Sonnet审查均授权受限，未执行新增数据查询或获得独立意见'],'original_lark_writes':0}
(P/'completion-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({'status':result['status'],'checks':len(checks),'games':len(data['games'])},ensure_ascii=False))
