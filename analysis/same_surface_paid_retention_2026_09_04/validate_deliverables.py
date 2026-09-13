import json
import math
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parent
def main():
    a=json.loads((ROOT/'artifact.json').read_text());m=a['manifest'];d=a['snapshot']['datasets'];checks=[]
    def check(name,ok):checks.append({'check':name,'status':'passed' if ok else 'failed'})
    rows=d['recent_raw']
    check('cohort keys unique',len(rows)==len({(r['payer_group'],r['cohort_date'],r['anchor_client'],r['day_number']) for r in rows}))
    check('state counts conserve the cohort',all(r['cohort_users']==sum(r[k] for k in ['same_surface_users','unknown_return_surface_users','no_observed_return_users','unknown_anchor_users','immature_users']) for r in rows))
    check('same surface never exceeds account return',all(r['same_surface_users']<=r['account_return_users']<=r['mature_users'] for r in rows))
    check('immature values excluded from observed rates',all(r['mature_users']>0 for r in d['recent_daily']))
    check('unidentified first payer anchors not named APP H5 or PWA',all(r['origin_surface']=='起点端未识别' for r in rows if r['payer_group']=='首次付费'))
    check('APP components remain separate',{r['platform'] for r in d['app_comparison']}=={'Android','iOS'})
    recent=[r for r in rows if r['origin_surface']=='APP' and r['day_number']==2 and r['mature_users']>0]
    n=sum(r['mature_users'] for r in recent);num=sum(r['same_surface_users'] for r in recent)
    check('headline recalculated',n==5242 and num==2578 and math.isclose(num/n,.49179702403662723))
    check('all dimension cells meet privacy threshold',all(r['users']>=10 for r in d['app_dimensions']))
    check('dimension rates reproducible',all(math.isclose(r['observed_same_app_rate'],r['same_app_users']/r['users']) for r in d['app_dimensions']))
    for dim in ['首日包名','首笔金额相对分组']:
        rr=[r for r in d['app_dimensions'] if r['dimension']==dim]
        check(dim+' reconciles latest cohort',sum(r['users'] for r in rr)==2655 and sum(r['same_app_users'] for r in rr)==1355)
    text='\n'.join(b.get('body','') for b in m['blocks'])
    check('partial status and meaning explicit',all(s in text for s in ['阶段','不是同端留存','首次付费','未识别','未执行']))
    check('no excluded channel module',not re.search(r'phoenix|phenix|firebase|h5phx',json.dumps(a),re.I))
    root=ET.fromstring('<doc>'+(ROOT/'lark_release_candidate.xml').read_text()+'</doc>')
    check('Lark table and figure parity',len(root.findall('.//table'))==len(m['tables']) and len(root.findall('.//img'))==len(m['charts']))
    xmltext=''.join(root.itertext())
    check('key facts match Lark',all(s in xmltext for s in ['49.18%','5,242','2,578','11,246,238','61.7GiB']))
    table_map={t['id']:t for t in m['tables']}
    declared=[table_map[b['tableId']] for b in m['blocks'] if b['type']=='table']
    for spec,table in zip(declared,root.findall('.//table')):
        expected=len(d[spec['dataset']]);actual=len(table.findall('./tbody/tr'))
        check(spec['id']+' row parity',expected==actual)
    browser=json.loads((ROOT/'browser_verification.json').read_text())
    check('HTML desktop narrow and source interaction',browser.get('ok') and browser.get('viewports')==[1440,390] and browser.get('sourceDialog')=='passed')
    tests=subprocess.run(['.venv/bin/python','-m','unittest','discover','-s',str(ROOT.relative_to(ROOT.parents[1])),'-p','test_*.py'],cwd=ROOT.parents[1],capture_output=True,text=True)
    check('20 boundary tests passed',tests.returncode==0 and 'Ran 20 tests' in tests.stderr)
    ledger=json.loads((ROOT/'query_ledger.json').read_text());total=sum(e['accounted_bytes'] for e in ledger['entries'])
    check('execution budget enforced',total<=ledger['limit_bytes'])
    result={'status':'partial' if all(c['status']=='passed' for c in checks) else 'needs_revision','checks':checks,
      'query_accounted_bytes':total,'constraints':['Historical full-surface query is dry-run only, exceeds limits.','No verified H5/PWA runtime discriminator.','No usable first-pay actual-surface marker in probed window.','Same-cohort LTV not recomputed.'],
      'scope':'9月近期实际端观察；6—8月历史账号背景，非同端结果。'}
    (ROOT/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':result['status'],'checks':len(checks),'failures':[c['check'] for c in checks if c['status']=='failed']},ensure_ascii=False))
    return 0 if result['status']=='partial' else 1
if __name__=='__main__':raise SystemExit(main())
