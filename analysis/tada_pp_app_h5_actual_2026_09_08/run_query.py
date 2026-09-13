"""Bounded, read-only Cloud BigQuery API runner. Only aggregate/metadata outputs."""
from pathlib import Path
import argparse,datetime,json,re,importlib.util,fcntl,hashlib
from google.cloud import bigquery

P=Path(__file__).resolve().parent
validator_path=Path('/Users/robin/.codex/skills/waje-bigquery-readonly/scripts/validate_readonly_sql.py')
spec=importlib.util.spec_from_file_location('readonly_validator',validator_path);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
# User explicitly confirmed this task-scoped increase on 2026-09-08.
# Global project/skill defaults are unchanged; prior scans count toward the total.
MAX_QUERY=64*1024**3;MAX_RUN=300*1024**3
FORBIDDEN_OUTPUT={'user_id','user_key','xl_id','uuid','order_no','order_id','bet_uid','serial_num','salt_key','client_ip','ip','email','email_address','phone','device_id','custom'}

def main():
    args=argparse.ArgumentParser();args.add_argument('sql');args.add_argument('--execute',action='store_true');opt=args.parse_args()
    file=Path(opt.sql).resolve();sql=file.read_text();errors=v.validate(sql)
    if errors:raise RuntimeError('; '.join(errors))
    if not re.search(r'\bLIMIT\s+([0-9]+)',sql,re.I):raise RuntimeError('Explicit bounded output required')
    existing=P/'queries';existing.mkdir(exist_ok=True)
    lock=(existing/'.runner.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    result_path=existing/(file.stem+'.result.json');receipt_path=existing/(file.stem+'.receipt.json')
    if opt.execute and result_path.exists():raise RuntimeError('Already executed snapshot; inspect existing result rather than overwrite')
    receipts=[json.loads(p.read_text()) for p in existing.glob('*.receipt.json')]
    if any(r.get('status')=='submitted' for r in receipts):
        raise RuntimeError('A submitted job requires authoritative readback before another execution')
    total=sum(r.get('actual_bytes_processed',0) or 0 for r in receipts)
    client=bigquery.Client(project='wajenigeria',location='europe-west4')
    dry=client.query(sql,job_config=bigquery.QueryJobConfig(dry_run=True,use_query_cache=False))
    est=dry.total_bytes_processed or 0
    rec={'query':str(file.relative_to(P)),'sql_sha256':hashlib.sha256(sql.encode()).hexdigest(),'project':'wajenigeria','location':'europe-west4','checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'dry_run_bytes':est,'prior_run_bytes':total,'max_query_bytes':MAX_QUERY,'max_task_bytes':MAX_RUN,'status':'dry_run_passed','production_mutations':False}
    if est>MAX_QUERY or total+est>MAX_RUN:
        rec['status']='blocked_cost';receipt_path.write_text(json.dumps(rec,indent=2));print(json.dumps(rec));return
    if opt.execute:
        job=client.query(sql,job_config=bigquery.QueryJobConfig(maximum_bytes_billed=MAX_QUERY,use_query_cache=True,labels={'purpose':'tada_pp_actual','mode':'readonly_aggregate'}))
        rec.update(status='submitted',job_id=job.job_id)
        receipt_path.write_text(json.dumps(rec,ensure_ascii=False,indent=2));print(json.dumps(rec),flush=True)
        rows=job.result(max_results=3001)
        if rows.total_rows>3000:raise RuntimeError('Aggregation output exceeds 3000 rows; do not truncate')
        keys={f.name for f in rows.schema}
        if keys&FORBIDDEN_OUTPUT:raise RuntimeError('Restricted output fields rejected')
        values=[dict(r) for r in rows]
        rec.update(status='executed',job_id=job.job_id,actual_bytes_processed=job.total_bytes_processed,actual_bytes_billed=job.total_bytes_billed,cache_hit=job.cache_hit,rows=len(values))
        result_path.write_text(json.dumps(values,ensure_ascii=False,indent=2,default=str))
        rec['result_sha256']=hashlib.sha256(result_path.read_bytes()).hexdigest()
    receipt_path.write_text(json.dumps(rec,ensure_ascii=False,indent=2,default=str));print(json.dumps(rec,ensure_ascii=False,default=str))

if __name__=='__main__':main()
