"""Immutable backup of the latest source reports for an independent rebuild."""
import datetime,hashlib,json,shutil,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
folder=P/'original-backup';folder.mkdir(exist_ok=True)
paths=[ROOT/'analysis/same_surface_paid_retention_2026_09_04/historical/prior_report.html',ROOT/'output/html/Waje-付费用户留存分析-APP-H5-PWA候选渠道-2026-09-10.html',ROOT/'analysis/h5_paid_retention_reconciliation_2026_09_10/origin-template.sql',ROOT/'analysis/h5_paid_retention_reconciliation_2026_09_10/origin-supplied.txt']
items=[]
for n,path in enumerate(paths):
    dst=folder/f'{n}-{path.name}'
    if not dst.exists():shutil.copy2(path,dst)
    items.append({'source':str(path.relative_to(ROOT)),'backup':str(dst.relative_to(ROOT)),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest()})
read=json.loads(subprocess.check_output(['/Users/robin/.local/node/bin/lark-cli','docs','+fetch','--doc','VNpkdi9cBozl5bxanMrlTNNJg4d','--detail','full','--as','user','--format','json']))
assert read.get('ok');rev=read['data']['document']['revision_id'];dst=folder/f'feishu-revision-{rev}.json'
if not dst.exists():dst.write_text(json.dumps(read,ensure_ascii=False,indent=2))
manifest={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':items,'feishu_revision':rev,'feishu_backup':str(dst.relative_to(ROOT)),'originals_changed':False,'new_report_status':'scope_confirmation_and_parameter_validation_pending','database_query_executed':False}
(P/'backup-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print(json.dumps({'backup_files':len(items)+1,'feishu_revision':rev,'originals_changed':False}))
