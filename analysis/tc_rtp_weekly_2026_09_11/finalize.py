#!/usr/bin/env python3
import hashlib,json,math
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent;PROJECT=ROOT.parents[1];load=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
D=load(ROOT/'analysis-results.json');tc=D['tc'];gp=D['game_overall'];games=D['game_comparison']
assert math.isclose(tc['previous']['tc'],tc['previous']['withdraw']/tc['previous']['recharge'],rel_tol=1e-12)
assert math.isclose(tc['current']['tc'],tc['current']['withdraw']/tc['current']['recharge'],rel_tol=1e-12)
assert math.isclose(tc['change_pp'],(tc['current']['tc']-tc['previous']['tc'])*100,abs_tol=1e-10)
assert math.isclose(gp['current']['complete_bet'],sum(r['complete_bet_curr']for r in games),rel_tol=1e-12)
assert math.isclose(gp['previous']['complete_bet'],sum(r['complete_bet_prev']for r in games),rel_tol=1e-12)
assert tc['reference_reconciliation']['max_abs_recharge_difference_pct']<0.002
assert tc['reference_reconciliation']['max_abs_withdraw_difference_pct']<0.004
assert tc['channel_attribution']['unmatched_money_share']>0.95 and tc['channel_attribution']['status']=='blocked_incomplete_profile_join'
ledger=load(ROOT/'query-ledger.json');assert all(e['status']=='completed'for e in ledger['entries']);assert sum(e['actual_bytes']for e in ledger['entries'])<ledger['limit_bytes']
for e in ledger['entries']:
    result=load(ROOT/'queries'/e['sql'].replace('.sql','.result.json'));assert result['job_id']==e['job_id']
visual=load(ROOT/'qa/visual-verification.json');assert visual['status']=='passed'and len(visual['results'])==4
lark=load(ROOT/'lark-delivery-receipt.json');assert lark['status']=='created_and_readback_verified'and all(v is True or k=='revision'for k,v in lark['checks'].items())
reference=load(ROOT/'reference/recheck.json');assert reference['matches_initial_capture']
build=load(ROOT/'report-app/dist/data-app-build.json');assert build['kind']=='separate-data-v1'
offline=PROJECT/'output/html/Waje-TC-RTP周度分析-截至2026-09-10.html';assert offline.exists()
receipt={'status':'complete_with_declared_channel_gap','completed_at':datetime.now(timezone.utc).isoformat(),'windows':D['windows'],'reference_report':{'revision':48,'content_sha256':reference['content_sha256'],'unchanged_during_run':True},'sources':{'bigquery':{'status':'completed','jobs':[{'sql':e['sql'],'job_id':e['job_id'],'bytes_processed':e['actual_bytes']}for e in ledger['entries']],'total_bytes_processed':sum(e['actual_bytes']for e in ledger['entries']),'audit_limit_bytes':ledger['limit_bytes']},'lifecycle':{'status':'validated','source':'GM Lifecycle Pool v2 (Joint)','run_receipt':'data/outputs/lifecycle_joint/2026-09-11/run-receipt.json','days':14,'games_per_day':31,'lifecycle_1_4_rows_per_day':124}},'quality':{'calculation_recomputed':True,'reference_reconciliation_passed':True,'desktop_mobile_light_dark_passed':True,'chart_count':5,'lark_full_readback_passed':True,'channel_tc':'blocked_incomplete_registration_channel_attribution','missing_not_zero':True,'independent_review':'cancelled_after_153_seconds_without_result; no acceptance claimed'},'deliverables':{'local_preview':'http://127.0.0.1:56868/','offline_html':str(offline.relative_to(PROJECT)),'offline_html_sha256':sha(offline),'markdown':str((ROOT/'report.md').relative_to(PROJECT)),'lark_url':lark['url'],'lark_revision':lark['revision_id'],'lark_readback_sha256':lark['readback_sha256']},'core_results':{'tc_current':tc['current']['tc'],'tc_change_pp':tc['change_pp'],'recharge_change_pct':tc['recharge_change_pct'],'withdraw_change_pct':tc['withdraw_change_pct'],'complete_bet_current':gp['current']['complete_bet'],'bet_change_pct':gp['bet_change_pct'],'actual_rtp_current':gp['current']['actual_rtp'],'actual_rtp_change_pp':gp['actual_rtp_change_pp'],'expected_coverage_current':gp['current']['expected_coverage'],'expected_subset_gap_pp':gp['current']['rtp_gap_pp']},'limitations':D['quality']['limitations']+D['quality']['blocked_dimensions']}
(ROOT/'final-delivery-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2));print(json.dumps({'status':receipt['status'],'bq_gib':receipt['sources']['bigquery']['total_bytes_processed']/1024**3,'offline_html':receipt['deliverables']['offline_html'],'lark_url':receipt['deliverables']['lark_url']},ensure_ascii=False))
