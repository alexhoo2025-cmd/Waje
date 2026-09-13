-- Aggregate-only observed same-surface retention, source business day Africa/Lagos.
WITH s AS (
 SELECT target_day AS cohort_date,user_id,event_type,client_type,SAFE_CAST(time AS INT64) AS event_ms,
   is_success,is_first_buy,order_no,pay_amount,noun_type,package_channel
 FROM `wajenigeria.origin_hfyl.view_event_server`
 WHERE target_day BETWEEN DATE '2026-09-02' AND DATE '2026-09-03'
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
 WHERE target_day BETWEEN DATE '2026-09-02' AND DATE '2026-09-03' AND app_id=90006
  AND event_type IN ('AL','AQ','PV','PD','LOGIN','REGISTER','GAMESTART','GAMEEND')
  AND user_id IS NOT NULL AND user_id!=''
 GROUP BY activity_date,user_id,client_type
), web_activity AS (
 SELECT target_day AS activity_date,user_id,CAST(0 AS INT64) AS client_type
 FROM `wajenigeria.origin_hfyl.view_event_web`
 WHERE target_day BETWEEN DATE '2026-09-02' AND DATE '2026-09-03' AND app_id=90006
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
 WHERE target_day BETWEEN DATE '2026-09-02' AND DATE '2026-09-03' AND app_id=90006
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
), first_day_events AS (
 SELECT target_day AS cohort_date,user_id,client_type,SAFE_CAST(time AS INT64) AS event_ms,
  COALESCE(NULLIF(app_version,''),'未记录') AS app_version,
  COALESCE(NULLIF(package_name,''),'未记录') AS package_name,
  COALESCE(NULLIF(device_model,''),'未记录') AS device_model
 FROM `wajenigeria.origin_hfyl.view_event_client`
 WHERE target_day = DATE '2026-09-02' AND app_id=90006
  AND event_type IN ('AL','AQ','PV') AND client_type IN (1,2)
), features AS (
 SELECT r.user_id,r.registration_date AS cohort_date,
  ARRAY_AGG(STRUCT(e.app_version,e.package_name,e.device_model) ORDER BY e.event_ms LIMIT 1)[OFFSET(0)] AS f
 FROM registered r JOIN first_day_events e
  ON r.user_id=e.user_id AND r.registration_date=e.cohort_date AND e.client_type=r.anchor.client_type
 WHERE e.event_ms>=r.anchor.event_ms
 GROUP BY r.user_id,r.registration_date
), first_amounts AS (
 SELECT user_id,cohort_date,ARRAY_AGG(amount ORDER BY event_ms LIMIT 1)[OFFSET(0)] AS amount
 FROM success_orders GROUP BY user_id,cohort_date
), users AS (
 SELECT o.user_id,o.anchor_client,o.cohort_date,
  o.android OR o.ios AS same_app,
  ((o.android OR o.ios)=FALSE) AND o.unknown_surface AS unknown_return,
  COALESCE(f.f.app_version,'未记录') AS app_version,COALESCE(f.f.package_name,'未记录') AS package_name,
  COALESCE(f.f.device_model,'未记录') AS device_model,
  NTILE(4) OVER (PARTITION BY o.anchor_client ORDER BY a.amount,o.user_id) AS amount_quartile
 FROM observations o LEFT JOIN features f ON o.user_id=f.user_id AND o.cohort_date=f.cohort_date
 JOIN first_amounts a ON o.user_id=a.user_id AND o.cohort_date=a.cohort_date
 WHERE o.payer_group='新增付费' AND o.anchor_client IN (1,2) AND NOT o.anchor_conflict
  AND o.day_number=2 AND o.mature AND o.cohort_date=DATE '2026-09-02'
), dimensions AS (
 SELECT user_id,anchor_client,same_app,unknown_return,dim.name AS dimension,dim.value AS value
 FROM users CROSS JOIN UNNEST([
  STRUCT('首日版本' AS name,app_version AS value),STRUCT('首日包名',package_name),
  STRUCT('首日设备型号',device_model),STRUCT('首笔金额相对分组',CONCAT('第',CAST(amount_quartile AS STRING),'四分位组'))
 ]) AS dim
)
SELECT anchor_client,dimension,value,COUNT(*) AS users,
 COUNTIF(same_app) AS same_app_users,COUNTIF(unknown_return) AS unknown_return_users,
 SAFE_DIVIDE(COUNTIF(same_app),COUNT(*)) AS observed_same_app_rate,
 DATE '2026-09-02' AS cohort_start,DATE '2026-09-02' AS cohort_end,DATE '2026-09-03' AS data_cutoff_date
FROM dimensions
GROUP BY anchor_client,dimension,value
HAVING COUNT(*)>=10
ORDER BY dimension,anchor_client,users DESC
LIMIT 3000;
