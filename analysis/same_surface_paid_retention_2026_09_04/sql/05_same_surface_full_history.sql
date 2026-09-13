-- Aggregate-only observed same-surface retention, source business day Africa/Lagos.
WITH s AS (
 SELECT target_day AS cohort_date,user_id,event_type,client_type,SAFE_CAST(time AS INT64) AS event_ms,
   is_success,is_first_buy,order_no,pay_amount,noun_type,package_channel
 FROM `wajenigeria.origin_hfyl.view_event_server`
 WHERE target_day BETWEEN DATE '2026-06-01' AND DATE '2026-09-03'
   AND app_id=90006 AND event_type IN ('REGISTER','ORDER','LOGIN','LOGOUT')
   AND user_id IS NOT NULL AND user_id!=''
), registered AS (
 SELECT user_id,MIN(cohort_date) AS registration_date,
   ARRAY_AGG(STRUCT(client_type,event_ms,package_channel) ORDER BY event_ms LIMIT 1)[OFFSET(0)] AS anchor,
   COUNT(DISTINCT client_type) AS registration_client_variants
 FROM s WHERE event_type='REGISTER' AND event_ms>0
 GROUP BY user_id
), success_orders AS (
 SELECT user_id,cohort_date,order_no,MIN(event_ms) AS event_ms,
  MAX(pay_amount) AS amount,LOGICAL_OR(is_first_buy) AS first_flag,
  ARRAY_AGG(client_type ORDER BY event_ms LIMIT 1)[OFFSET(0)] AS client_type,
  COUNT(DISTINCT client_type) AS client_variants
 FROM s WHERE event_type='ORDER' AND is_success='pay_success' AND order_no IS NOT NULL AND order_no!='' AND event_ms>0
 GROUP BY user_id,cohort_date,order_no
), paid_days AS (
 SELECT user_id,cohort_date,MIN(event_ms) AS first_paid_ms,COUNT(*) AS orders
 FROM success_orders GROUP BY user_id,cohort_date
), first_payments AS (
 SELECT user_id,MIN(cohort_date) AS cohort_date,
  ARRAY_AGG(STRUCT(client_type,event_ms) ORDER BY event_ms LIMIT 1)[OFFSET(0)] AS anchor,
  COUNT(DISTINCT cohort_date) AS first_flag_dates
 FROM success_orders WHERE first_flag GROUP BY user_id
), anchors AS (
 SELECT r.user_id,r.registration_date AS cohort_date,'新增付费' AS payer_group,r.anchor.client_type AS anchor_client,
  r.anchor.package_channel AS anchor_channel,r.registration_client_variants>1 AS anchor_conflict
 FROM registered r JOIN paid_days p ON r.user_id=p.user_id AND r.registration_date=p.cohort_date
 WHERE p.first_paid_ms>=r.anchor.event_ms
 UNION ALL
 SELECT user_id,cohort_date,'首次付费' AS payer_group,anchor.client_type AS anchor_client,
  CAST(NULL AS STRING) AS anchor_channel,first_flag_dates>1 AS anchor_conflict
 FROM first_payments
), client_activity AS (
 SELECT target_day AS activity_date,user_id,client_type
 FROM `wajenigeria.origin_hfyl.view_event_client`
 WHERE target_day BETWEEN DATE '2026-06-01' AND DATE '2026-09-03' AND app_id=90006
  AND event_type IN ('AL','AQ','PV','PD','LOGIN','REGISTER','GAMESTART','GAMEEND')
  AND user_id IS NOT NULL AND user_id!=''
 GROUP BY activity_date,user_id,client_type
), web_activity AS (
 SELECT target_day AS activity_date,user_id,CAST(0 AS INT64) AS client_type
 FROM `wajenigeria.origin_hfyl.view_event_web`
 WHERE target_day BETWEEN DATE '2026-06-01' AND DATE '2026-09-03' AND app_id=90006
  AND event_type IN ('AL','AQ','PV','PD') AND user_id IS NOT NULL AND user_id!=''
 GROUP BY activity_date,user_id
), typed_activity AS (
 SELECT activity_date,user_id,client_type FROM client_activity
 UNION ALL SELECT activity_date,user_id,client_type FROM web_activity
 UNION ALL SELECT cohort_date,user_id,client_type FROM s WHERE event_type IN ('LOGIN','LOGOUT','REGISTER')
), daily AS (
 SELECT activity_date,user_id,
  LOGICAL_OR(client_type=2) AS android,LOGICAL_OR(client_type=1) AS ios,
  LOGICAL_OR(client_type NOT IN (1,2) OR client_type IS NULL) AS unknown_surface
 FROM typed_activity GROUP BY activity_date,user_id
), account_activity AS (
 SELECT target_day AS activity_date,user_id
 FROM `wajenigeria.origin_hfyl.view_user_version_daily`
 WHERE target_day BETWEEN DATE '2026-06-01' AND DATE '2026-09-03' AND app_id=90006
 GROUP BY activity_date,user_id
), observations AS (
 SELECT a.user_id,a.payer_group,a.cohort_date,a.anchor_client,a.anchor_conflict,
  COALESCE(a.anchor_channel,'未记录') AS anchor_channel,d AS day_number,
  DATE_ADD(a.cohort_date,INTERVAL d-1 DAY)<=DATE '2026-09-03' AS mature,
  IFNULL(x.android,FALSE) AS android,IFNULL(x.ios,FALSE) AS ios,
  IFNULL(x.unknown_surface,FALSE) OR (t.user_id IS NOT NULL AND x.user_id IS NULL) AS unknown_surface,
  x.user_id IS NOT NULL OR t.user_id IS NOT NULL AS any_return
 FROM anchors a CROSS JOIN UNNEST([2,3,4,5,6,7,8,9,10,11,12,13,14,30,60,90]) AS d
 LEFT JOIN daily x ON x.user_id=a.user_id AND x.activity_date=DATE_ADD(a.cohort_date,INTERVAL d-1 DAY)
 LEFT JOIN account_activity t ON t.user_id=a.user_id AND t.activity_date=DATE_ADD(a.cohort_date,INTERVAL d-1 DAY)
), state_flags AS (
 SELECT user_id,payer_group,cohort_date,anchor_client,anchor_conflict,anchor_channel,day_number,mature,any_return,
  CASE WHEN anchor_client IN (1,2) AND NOT anchor_conflict THEN 'APP'
       WHEN anchor_client=3 AND NOT anchor_conflict THEN '网页运行形态未识别'
       ELSE '起点端未识别' END AS origin_surface,
  CASE WHEN NOT mature THEN '未成熟'
       WHEN anchor_conflict OR anchor_client NOT IN (1,2) OR anchor_client IS NULL THEN '起点端未识别'
       WHEN android OR ios THEN '同端已确认'
       WHEN unknown_surface THEN '回访端未识别'
       WHEN any_return THEN '回访端未识别'
       ELSE '未观察到回访' END AS app_state,
  CASE WHEN NOT mature THEN '未成熟'
       WHEN anchor_conflict OR anchor_client NOT IN (1,2) OR anchor_client IS NULL THEN '起点端未识别'
       WHEN android AND ios THEN '同子端且跨子端'
       WHEN (anchor_client=2 AND android) OR (anchor_client=1 AND ios) THEN '同子端已确认'
       WHEN unknown_surface THEN '回访端未识别'
       WHEN (anchor_client=2 AND ios) OR (anchor_client=1 AND android) THEN '仅跨APP子端'
       WHEN any_return THEN '回访端未识别'
       ELSE '未观察到回访' END AS sub_state
 FROM observations
)
SELECT payer_group,FORMAT_DATE('%Y-%m',cohort_date) AS cohort_month,origin_surface,anchor_client,day_number,
 COUNT(*) AS cohort_users,
 COUNTIF(app_state!='未成熟') AS mature_users,
 COUNTIF(app_state='同端已确认') AS same_surface_users,
 COUNTIF(app_state='回访端未识别') AS unknown_return_surface_users,
 COUNTIF(app_state='未观察到回访') AS no_observed_return_users,
 COUNTIF(app_state='起点端未识别') AS unknown_anchor_users,
 COUNTIF(app_state='未成熟') AS immature_users,
 COUNTIF(sub_state='同子端且跨子端') AS same_and_other_subplatform_users,
 COUNTIF(sub_state='同子端已确认') AS same_subplatform_users,
 COUNTIF(sub_state='仅跨APP子端') AS only_other_subplatform_users,
 COUNTIF(sub_state='回访端未识别') AS unknown_subplatform_users,
 COUNTIF(any_return) AS account_return_users,
 DATE '2026-09-03' AS data_cutoff_date
FROM state_flags
WHERE cohort_date BETWEEN DATE '2026-06-01' AND DATE '2026-09-03'
GROUP BY payer_group,cohort_month,origin_surface,anchor_client,day_number
HAVING COUNT(*)>=10
ORDER BY payer_group,cohort_month,anchor_client,day_number
LIMIT 3000;
