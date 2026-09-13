"""Archive the current approved report before an auth-gated August refresh."""
import datetime,hashlib,json,subprocess,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
R=P/'baseline';R.mkdir(exist_ok=True)
cli='/Users/robin/.local/node/bin/lark-cli'
response=json.loads(subprocess.check_output([cli,'docs','+fetch','--doc','VNpkdi9cBozl5bxanMrlTNNJg4d','--detail','full','--as','user','--format','json']))
assert response.get('ok'),response
doc=response['data']['document'];snapshot=R/f"lark-revision-{doc['revision_id']}.json"
if snapshot.exists():assert json.loads(snapshot.read_text())==response,'Existing revision differs'
else:snapshot.write_text(json.dumps(response,ensure_ascii=False,indent=2)+'\n')
sources=[ROOT/'analysis/same_surface_paid_retention_2026_09_04/historical/prior_report.html',ROOT/'output/html/Waje-付费用户留存分析-APP-H5-PWA候选渠道-2026-09-10.html']
files=[]
for n,src in enumerate(sources):
    if src.exists():
        target=R/f'html-{n}.html'
        if not target.exists():shutil.copy2(src,target)
        files.append({'source':str(src.relative_to(ROOT)),'backup':str(target.relative_to(ROOT)),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
status={'status':'blocked_authentication','checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'auth_probe':{'tool':'bigquery_waje.list_dataset_ids','projectId':'wajenigeria','result':'Auth required'},'source_document':doc['document_id'],'source_revision':doc['revision_id'],'source_content_sha256':hashlib.sha256(doc['content'].encode()).hexdigest(),'backups':files,'formal_query_executed':False,'report_changed':False,'cohort_month':'2026-08','observation_cutoff_requested':'2026-09-09','timezone':'Africa/Lagos','baseline_months_unchanged':['2026-06','2026-07'],'curve_cohort':['2026-08-01','2026-08-27'],'eligibility_end_by_day':{'2':'2026-08-31','7':'2026-08-31','14':'2026-08-27','30':'2026-08-11','60':None},'per_query_limit_bytes':5*1024**3,'run_limit_bytes':25*1024**3,'minimum_eligible_users':10}
(P/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':status['status'],'revision':doc['revision_id'],'backups':len(files),'report_changed':False}))
