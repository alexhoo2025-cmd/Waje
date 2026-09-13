WITH events AS (
 SELECT target_day AS stat_date,user_id,is_accept,is_test_uid
 FROM `wajenigeria.origin_hfyl.realtime_event_server`
 WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-09-07'
   AND app_id=90006 AND event_type='AUDIT'
)
SELECT COUNT(1) AS audit_records,COUNT(DISTINCT user_id) AS audit_accounts,
 COUNTIF(is_accept=2) AS paid_out_status_records,
 COUNTIF(is_accept=1) AS status_1_records,
 COUNTIF(is_accept=3) AS status_3_records,
 COUNTIF(is_accept=0) AS rejected_status_records,
 COUNTIF(is_accept IS NULL) AS unknown_status_records,
 COUNT(DISTINCT IF(is_accept=2,stat_date,NULL)) AS paid_out_status_dates
FROM events WHERE stat_date BETWEEN DATE '2026-08-01' AND DATE '2026-09-07'
 AND (is_test_uid IS NULL OR is_test_uid!=1)
HAVING COUNT(DISTINCT user_id)>=10
LIMIT 10;
