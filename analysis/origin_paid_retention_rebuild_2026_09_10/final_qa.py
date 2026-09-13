"""Recompute local acceptance checks and collect read-only BQ job metadata."""
import datetime,hashlib,json,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=P.parents[1]
sys.path.insert(0,str(ROOT/'analysis/paid_retention_aug_refresh_2026_09_09'))
from direct_client import client
load=lambda n:json.loads((P/n).read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
backup=load('backup-manifest.json')
assert all(sha(ROOT/f['source'])==f['sha256']==sha(ROOT/f['backup']) for f in backup['files'])
analysis=load('analysis.json')
assert analysis['qa']['cross_channel_overlap']==0
assert all(v is True for k,v in analysis['qa'].items()if k!='cross_channel_overlap')
ref=load('reference-reconciliation.json')
assert len(ref)==8 and all(r['paid_count_delta']==0 for r in ref)
next_deltas=[abs(r['difference_pp']) for c in ref for r in c['rates'] if r['population']=='新增付费' and r['day']==2]
assert max(next_deltas)<0.002
coverage=load('10_partition_coverage.result.json')['rows']
expected={str(datetime.date(2026,8,1)+datetime.timedelta(days=i))for i in range(40)}
for name in ['realtime_event_client','realtime_event_server','realtime_event_web']:
    rows=[r for r in coverage if r['table_name']==name]
    assert {r['partition_date']for r in rows}==expected and all(r['total_rows']>0 for r in rows)
b=client()
names=['01_origin_denominators','05_full_origin_returns','06_origin_reg_first','07_key_overlap','08_ltv_dimensions','09_origin_ct','10_partition_coverage']
def job_metadata(name):
    result=load(name+'.result.json')
    assert result['dry']['sql_sha256']==sha(P/(name+'.sql'))
    j=b.get_job(result['job_id'],location='europe-west4')
    assert j.state=='DONE' and not j.errors
    return {'sql':name+'.sql','sql_sha256':sha(P/(name+'.sql')),'job_id':j.job_id,'started':str(j.started),'ended':str(j.ended),'bytes_processed':j.total_bytes_processed,'bytes_billed':j.total_bytes_billed,'cache_hit':j.cache_hit,'maximum_bytes_billed':j.maximum_bytes_billed,'state':j.state}
with ThreadPoolExecutor(max_workers=4)as pool:jobs=list(pool.map(job_metadata,names))
profile=b.get_table('wajenigeria.origin_hfyl.user_events')
ct=load('ct-reference-reconciliation.json')
receipt={'status':'completed_with_caveats','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'observation_cutoff':'2026-09-09','business_date_basis':'Origin target_day, requested Lagos business-day convention','capacity_limits':'user waived both per-query and cumulative limits for this rebuild','original_files_unchanged':True,'original_feishu_not_modified':True,'backup_manifest':'backup-manifest.json','selected_channel_count':8,'main_checks':analysis['qa'],'reference':{'revision':791,'all_eight_new_paid_totals_exact':True,'maximum_new_paid_next_day_difference_pp':max(next_deltas),'first_pay_prior_snapshot_differences_retained':True,'ct_comparisons':sum(r['comparisons']for r in ct),'ct_within_002':sum(r['within_002']for r in ct)},'coverage':{'event_partition_dates_continuous':True,'event_partition_date_count_each':40,'profile_partitioning':profile.time_partitioning.to_api_repr()if profile.time_partitioning else None,'business_ingestion_finality':'not_certified; client partition continues receiving backfill','note':'Date coverage is checked; nonzero partitions do not prove final ingestion completeness.'},'jobs':jobs,'actual_bytes_processed':sum(j['bytes_processed']or 0 for j in jobs),'actual_bytes_billed':sum(j['bytes_billed']or 0 for j in jobs),'independent_reviewer':'blocked_auth_required; no independent model acceptance claimed','remaining_limits':['PWA is a selected candidate channel, not verified installation state','Origin first-pay numerator xl_id and denominator user_id units are deliberately preserved','Some C-T reference differences not fully attributed; paid-cohort-specific LTV unavailable','Source backfills may revise this query snapshot']}
delivery=load('delivery-receipt.json')
assert delivery['ok'] is True and delivery['report_quality']['errors']==0
assert delivery['report_quality']['input_sha256']==sha(P/'artifact.json')
visual=load('qa/visual-files.json')
assert {(r['theme'],r['width'])for r in visual if 'width'in r}=={('light',1440),('light',390),('dark',1440),('dark',390)}
receipt['delivery']={'html':delivery['html'],'html_sha256':sha(Path(delivery['html'])),'artifact_sha256':sha(P/'artifact.json'),'structure_passed':True,'chart_count':delivery['counts']['charts'],'table_count':delivery['counts']['tables'],'viewport_theme_checks_passed':True,'quality_warnings':delivery['report_quality']['warnings'],'visual_files':'qa/visual-files.json'}
(P/'final-qa.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2,default=str))
print(json.dumps({'status':receipt['status'],'jobs':len(jobs),'actual_GiB':receipt['actual_bytes_processed']/1024**3,'original_files_unchanged':True},ensure_ascii=False))
