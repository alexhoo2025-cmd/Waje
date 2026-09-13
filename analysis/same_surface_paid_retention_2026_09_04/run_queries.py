"""One audited run budget; append-only receipts for approved aggregate SELECTs."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from google.cloud import bigquery

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'all_platform_cohort_value_2026_09_04'))
from run_readonly_queries import execute

def main():
    parser=argparse.ArgumentParser();parser.add_argument('files',nargs='+');parser.add_argument('--dry-only',action='store_true')
    args=parser.parse_args();out=ROOT/'results';out.mkdir(exist_ok=True)
    ledger_path=ROOT/'query_ledger.json'
    ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else {'project':'wajenigeria','limit_bytes':25*1024**3,'entries':[]}
    client=bigquery.Client(project='wajenigeria',location='europe-west4')
    for filename in args.files:
        path=ROOT/'sql'/filename;dest=out/(path.stem+('.dry.json' if args.dry_only else '.json'))
        if dest.exists():
            print(json.dumps({'file':filename,'status':'existing_receipt_not_overwritten'}));continue
        spent=sum(e.get('accounted_bytes',0) for e in ledger['entries'])
        if args.dry_only:
            job=client.query(path.read_text(),job_config=bigquery.QueryJobConfig(dry_run=True,use_query_cache=False),location='europe-west4')
            result={'status':'dry_run_only','dry_bytes':int(job.total_bytes_processed or 0),'query_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        else:
            try:result,_=execute(client,path,spent)
            except Exception as exc:result={'status':'query_failed','error_type':type(exc).__name__,'error':str(exc)[:500]}
            charged=max(result.get('execution',{}).get('bytes_processed',0),result.get('dry_run',{}).get('bytes_processed',0)) if result.get('status')=='ok' else 0
            ledger['entries'].append({'sql':filename,'status':result['status'],'accounted_bytes':charged,'job_id':result.get('execution',{}).get('job_id')})
            ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2),encoding='utf-8')
        dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'file':filename,'status':result['status'],'dry_bytes':result.get('dry_bytes',result.get('dry_run',{}).get('bytes_processed')),'error':result.get('error'),'rows':result.get('execution',{}).get('row_count')},ensure_ascii=False),flush=True)
        if result['status'] not in ('ok','no_data','dry_run_only'):return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
