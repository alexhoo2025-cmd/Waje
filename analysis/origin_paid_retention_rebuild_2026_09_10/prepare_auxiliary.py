import json
from pathlib import Path
P=Path(__file__).resolve().parent;m=json.loads((P/'channels.json').read_text())
case='CASE '+' '.join("WHEN download_channel='%s'%s THEN '%s'"%(r['download_channel'],'' if r['first_media'] is None else f" AND first_media={r['first_media']}",r['sheet'])for r in m)+' ELSE NULL END'
codes=','.join("'"+c+"'"for c in sorted(set(r['download_channel'] for r in m)))
sql=f"""WITH mapping_raw AS (
SELECT user_id,xl_id,target_day,DATE(first_pay_date) AS first_pay_date,{case} AS sheet
FROM `wajenigeria.origin_hfyl.user_events`
WHERE app_id=90006 AND target_day<=DATE '2026-09-09' AND download_channel IN ({codes})
), mapping AS (SELECT user_id,xl_id,target_day,first_pay_date,sheet FROM mapping_raw WHERE sheet IS NOT NULL),
registers AS (
SELECT target_day AS cohort_date,xl_id,user_id
FROM `wajenigeria.origin_hfyl.view_event_register`
WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-08-31' AND app_id=90006
), first_pay AS (
SELECT target_day AS cohort_date,user_id
FROM `wajenigeria.origin_hfyl.view_event_pay`
WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-08-31' AND app_id=90006
AND event_type='pay_success' AND is_first_buy IS TRUE
GROUP BY cohort_date,user_id
), facts AS (
SELECT r.cohort_date,m.sheet,'注册用户' AS metric,r.user_id
FROM registers r JOIN mapping m ON r.xl_id=m.xl_id
UNION ALL
SELECT p.cohort_date,m.sheet,'首充用户' AS metric,p.user_id
FROM first_pay p JOIN mapping m ON p.user_id=m.user_id
)
SELECT cohort_date,sheet,metric,COUNT(DISTINCT user_id) AS users
FROM facts WHERE cohort_date BETWEEN DATE '2026-08-01' AND DATE '2026-08-31'
GROUP BY cohort_date,sheet,metric
HAVING COUNT(DISTINCT user_id)>=10
ORDER BY cohort_date,sheet,metric LIMIT 3000;
"""
(P/'06_origin_reg_first.sql').write_text(sql);(P/'06_origin_reg_first.scope.json').write_text(json.dumps({'start':'2026-08-01','end':'2026-09-09','purpose':'Origin registration-event denominator and successful first-pay denominator; profile lookup may include earlier-created users required by first-pay definition'}))
qa=f"""WITH p AS (
SELECT target_day AS cohort_date,DATE(first_pay_date) AS first_pay_date,xl_id,user_id,{case} AS sheet
FROM `wajenigeria.origin_hfyl.user_events`
WHERE app_id=90006 AND target_day<=DATE '2026-09-09'
AND (target_day BETWEEN DATE '2026-08-01' AND DATE '2026-08-31' OR DATE(first_pay_date) BETWEEN DATE '2026-08-01' AND DATE '2026-08-31')
), keys AS (
SELECT 'xl_id' AS key_type,xl_id AS key,COUNT(DISTINCT sheet) AS sheet_count,COUNT(DISTINCT cohort_date) AS date_count,COUNT(DISTINCT user_id) AS counterpart_count
FROM p WHERE sheet IS NOT NULL AND xl_id IS NOT NULL GROUP BY xl_id
UNION ALL
SELECT 'user_id',user_id,COUNT(DISTINCT sheet),COUNT(DISTINCT cohort_date),COUNT(DISTINCT xl_id)
FROM p WHERE sheet IS NOT NULL AND user_id IS NOT NULL AND user_id!='' GROUP BY user_id
)
SELECT key_type,COUNT(*) AS keys,COUNTIF(sheet_count>1) AS multiple_sheets,COUNTIF(date_count>1) AS multiple_dates,COUNTIF(counterpart_count>1) AS multiple_counterparts
FROM keys GROUP BY key_type HAVING COUNT(*)>=10 LIMIT 10;
"""
(P/'07_key_overlap.sql').write_text(qa);(P/'07_key_overlap.scope.json').write_text(json.dumps({'start':'2026-08-01','end':'2026-09-09','purpose':'Check cross-sheet identity overlap before aggregating eight Origin channel filters'}))
