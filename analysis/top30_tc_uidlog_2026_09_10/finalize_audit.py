import json
from pathlib import Path
P=Path(__file__).resolve().parent
stages=[]
for name,status in [
 ('query-receipt.json','superseded_reason_field'),
 ('query-receipt-v2.json','superseded_source_grain'),
 ('query-receipt-v3.json','superseded_play_marker_grain'),
 ('query-receipt-final.json','accepted')
]:
 d=json.loads((P/name).read_text());q=d['query'];stages.append({'receipt':name,'status':status,'job_id':q['job_id'],'bytes_processed':q['bytes_processed'],'result_rows':q['result_rows'],'sql':q['sql'],'window':q['date']})
total=sum(x['bytes_processed'] for x in stages)
final=json.loads((P/'aggregate-result-final.json').read_text());overall=next(r for r in final if r['section']=='总体')
assets=[r for r in final if r['section']=='资产'];codes=[r for r in final if r['section']=='变动代码']
assert overall['user_count']==30 and overall['event_count']==98031
assert sum(r['event_count'] for r in assets)==97971
assert total<25*1024**3
receipt={'status':'complete_with_mapping_limit','task_window':'2026-09-10','final_query_mode':'one batched parameterized SQL for 30 selected users','final_result':'aggregate only; no UIDs persisted','stages':stages,'total_bytes_processed':total,'total_gib_processed':total/1024**3,'within_audit_limit':True,'accepted_job_id':stages[-1]['job_id'],'checks':{'selected_users_matched':overall['user_count'],'all_events':overall['event_count'],'displayed_asset_events':sum(r['event_count']for r in assets),'suppressed_asset_events':overall['event_count']-sum(r['event_count']for r in assets),'shared_code_coverage':sum(r['event_count']for r in codes)/overall['event_count'],'cross_asset_amounts_not_summed':True},'limits':['BigQuery raw event does not contain the dashboard Chinese asset/reason dictionary','GET/COST are directional technical labels, not verified business reasons','Groups with fewer than 10 users are suppressed','Source Excel TC gap is the selection basis and may cover a wider period than 2026-09-10']}
(P/'audit-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
print(json.dumps({'status':receipt['status'],'total_gib':receipt['total_gib_processed'],'events':overall['event_count'],'coverage':receipt['checks']['shared_code_coverage']}))
