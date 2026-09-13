#!/usr/bin/env python3
"""Task-local aggregate-only BigQuery runner with a fresh 25 GiB audit ledger."""
from __future__ import annotations
import datetime,hashlib,json,os,subprocess,sys,warnings
from pathlib import Path
import google.auth
from google.auth.transport.requests import AuthorizedSession
from google.cloud import bigquery

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
PER_QUERY=5*1024**3
AUDIT_LIMIT=25*1024**3

def client():
    warnings.filterwarnings('ignore',category=UserWarning)
    credentials,_=google.auth.load_credentials_from_file('/Users/robin/.config/gcloud-waje-readonly/application_default_credentials.json')
    credentials=credentials.with_quota_project(None)
    identity=AuthorizedSession(credentials).get('https://www.googleapis.com/oauth2/v2/userinfo',timeout=20)
    if identity.status_code!=200 or identity.json().get('email')!='robin@afuruika.net':
        raise RuntimeError('Enterprise identity verification failed')
    return bigquery.Client(project='wajenigeria',credentials=credentials,location='europe-west4')

def run(sql_path:str,execute:bool=False):
    path=Path(sql_path).resolve();sql=path.read_text();digest=hashlib.sha256(path.read_bytes()).hexdigest()
    scope_path=path.with_suffix('.scope.json')
    subprocess.run([sys.executable,str(PROJECT/'scripts/check_query_window.py'),str(path)],check=True)
    subprocess.run([sys.executable,'/Users/robin/.codex/skills/waje-bigquery-readonly/scripts/validate_readonly_sql.py',str(path)],check=True)
    b=client();dry=b.query(sql,job_config=bigquery.QueryJobConfig(dry_run=True,use_query_cache=False),location='europe-west4')
    estimate=int(dry.total_bytes_processed or 0)
    ledger_path=ROOT/os.environ.get('WAJE_BQ_LEDGER_NAME','query-ledger.json');ledger=json.loads(ledger_path.read_text())if ledger_path.exists()else{'limit_bytes':AUDIT_LIMIT,'entries':[]}
    used=sum(e.get('actual_bytes',0)for e in ledger['entries']if e.get('status')=='completed')
    allowed=estimate<=PER_QUERY and used+estimate<=AUDIT_LIMIT
    dry_receipt={'sql_sha256':digest,'scope':json.loads(scope_path.read_text()),'estimated_bytes':estimate,'prior_actual_bytes':used,'per_query_limit_bytes':PER_QUERY,'audit_limit_bytes':AUDIT_LIMIT,'allowed':allowed}
    path.with_suffix('.dry.json').write_text(json.dumps(dry_receipt,indent=2))
    if not execute or not allowed:return dry_receipt
    result_path=path.with_suffix('.result.json')
    if result_path.exists():
        saved=json.loads(result_path.read_text())
        if saved.get('dry',{}).get('sql_sha256')!=digest:raise RuntimeError('SQL changed after execution; use a new query version')
        return saved
    config=bigquery.QueryJobConfig(use_query_cache=False,maximum_bytes_billed=PER_QUERY,labels={'purpose':'rtc-rtp-weekly'})
    job=b.query(sql,job_config=config,location='europe-west4');rows=[dict(r.items())for r in job.result(timeout=180)]
    if len(rows)>3000:raise RuntimeError('Aggregate result exceeded 3000 rows')
    entry={'sql':path.name,'sql_sha256':digest,'job_id':job.job_id,'status':'completed','actual_bytes':int(job.total_bytes_processed or 0),'started':str(job.started),'ended':str(job.ended)}
    ledger['entries'].append(entry);ledger_path.write_text(json.dumps(ledger,indent=2))
    result={'dry':dry_receipt,'job_id':job.job_id,'bytes_processed':job.total_bytes_processed,'bytes_billed':job.total_bytes_billed,'rows':rows}
    result_path.write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str))
    return result

if __name__=='__main__':
    result=run(sys.argv[1],execute='--execute'in sys.argv[2:])
    print(json.dumps({k:v for k,v in result.items()if k!='rows'},ensure_ascii=False,indent=2,default=str))
    if 'rows'in result:print(json.dumps({'row_count':len(result['rows'])},ensure_ascii=False))
