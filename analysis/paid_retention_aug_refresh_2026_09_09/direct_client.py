"""User-approved official BigQuery client, aggregate-only audit controls."""
import json,warnings,subprocess,hashlib,datetime
from pathlib import Path
import google.auth
from google.auth.transport.requests import AuthorizedSession
from google.cloud import bigquery
ROOT=Path(__file__).resolve().parent
def client():
    warnings.filterwarnings('ignore',category=UserWarning)
    c,_=google.auth.load_credentials_from_file('/Users/robin/.config/gcloud-waje-readonly/application_default_credentials.json')
    c=c.with_quota_project(None)
    response=AuthorizedSession(c).get('https://www.googleapis.com/oauth2/v2/userinfo',timeout=20)
    if response.status_code!=200 or response.json().get('email')!='robin@afuruika.net':raise RuntimeError('Enterprise identity verification failed')
    return bigquery.Client(project='wajenigeria',credentials=c,location='europe-west4')
def query(path,execute=False,allow_large_query=False,unlimited_capacity=False):
    path=Path(path);sql=path.read_text();out=path.with_suffix('.result.json');drypath=path.with_suffix('.dry.json')
    import sys
    sys.path.insert(0,str(ROOT.parents[1]/'scripts'))
    from check_query_window import check
    window_check=check(path)
    if execute and out.exists():
        saved=json.loads(out.read_text())
        if saved.get('dry',{}).get('sql_sha256')!=hashlib.sha256(path.read_bytes()).hexdigest():
            raise RuntimeError('SQL changed after execution; preserve the old receipt and use a new query version before rerunning')
        return saved
    validator='/Users/robin/.codex/skills/waje-bigquery-readonly/scripts/validate_readonly_sql.py'
    subprocess.run([str(Path('/Users/robin/Documents/wajetan_analyst/.venv/bin/python')),validator,str(path)],check=True,capture_output=True)
    b=client();dry=b.query(sql,job_config=bigquery.QueryJobConfig(dry_run=True,use_query_cache=False),location='europe-west4')
    estimate=int(dry.total_bytes_processed or 0);lp=ROOT/'direct-query-ledger.json';ledger=json.loads(lp.read_text()) if lp.exists() else {'limit':25*1024**3,'entries':[]}
    used=sum(e['accounted_bytes'] for e in ledger['entries'])
    per_query_limit=25*1024**3-used if allow_large_query else 5*1024**3
    info={'sql_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'window_check':window_check,'estimated_bytes':estimate,'prior_accounted_bytes':used,'per_query_limit_waived_by_user':allow_large_query or unlimited_capacity,'all_capacity_limits_waived_by_user':unlimited_capacity,'allowed':unlimited_capacity or (estimate<=per_query_limit and used+estimate<=25*1024**3)}
    drypath.write_text(json.dumps(info,indent=2))
    if not execute or not info['allowed']:return info
    entry={'sql':path.name,'accounted_bytes':estimate,'status':'reserved'};ledger['entries'].append(entry);lp.write_text(json.dumps(ledger,indent=2))
    config=bigquery.QueryJobConfig(use_query_cache=False,labels={'purpose':'paid-retention-audit'})
    if not unlimited_capacity:config.maximum_bytes_billed=per_query_limit
    try:
        job=b.query(sql,job_config=config,location='europe-west4')
    except Exception as e:
        entry.update(status='submission_failed',accounted_bytes=0,error_type=type(e).__name__)
        lp.write_text(json.dumps(ledger,indent=2));raise
    rows=[dict(r.items()) for r in job.result(timeout=180)];assert len(rows)<=3000
    entry.update(status='completed',job_id=job.job_id,accounted_bytes=max(estimate,int(job.total_bytes_processed or 0)))
    lp.write_text(json.dumps(ledger,indent=2));result={'dry':info,'job_id':job.job_id,'bytes':job.total_bytes_processed,'rows':rows}
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str));return result
if __name__=='__main__':
    b=client();names=['user_events','view_metaevent_order','view_user_version_daily','realtime_edw_user_version_daily','view_metaevent_active_events']
    result={}
    for name in names:
        try:
            t=b.get_table('wajenigeria.origin_hfyl.'+name,timeout=30)
            result[name]={'type':t.table_type,'location':t.location,'bytes':t.num_bytes,'rows':t.num_rows,'partitioning':t.time_partitioning.to_api_repr() if t.time_partitioning else None,'view_query':t.view_query,'schema':[{'name':f.name,'type':f.field_type} for f in t.schema]}
        except Exception as e:result[name]={'error':str(e)[:500]}
    (ROOT/'direct-source-metadata.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str))
    print(json.dumps(result,ensure_ascii=False,default=str))
