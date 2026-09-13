from pathlib import Path
ROOT=Path(__file__).resolve().parent
base=(ROOT/'sql/04_same_surface_recent.sql').read_text().split(', state_flags AS (')[0]
tail=""", first_day_events AS (
 SELECT target_day AS cohort_date,user_id,client_type,SAFE_CAST(time AS INT64) AS event_ms,
  COALESCE(NULLIF(app_version,''),'未记录') AS app_version,
  COALESCE(NULLIF(package_name,''),'未记录') AS package_name,
  COALESCE(NULLIF(device_model,''),'未记录') AS device_model
 FROM `wajenigeria.origin_hfyl.view_event_client`
 WHERE target_day BETWEEN DATE '2026-09-01' AND DATE '2026-09-02' AND app_id=90006
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
  AND o.day_number=2 AND o.mature
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
 DATE '2026-09-01' AS cohort_start,DATE '2026-09-02' AS cohort_end,DATE '2026-09-03' AS data_cutoff_date
FROM dimensions
GROUP BY anchor_client,dimension,value
HAVING COUNT(*)>=10
ORDER BY dimension,anchor_client,users DESC
LIMIT 3000;
"""
(ROOT/'sql/06_recent_app_dimensions.sql').write_text(base+tail,encoding='utf-8')
latest=(base+tail).replace("WHERE target_day BETWEEN DATE '2026-09-01' AND DATE '2026-09-02' AND app_id=90006", "WHERE target_day = DATE '2026-09-02' AND app_id=90006")
latest=latest.replace("AND o.day_number=2 AND o.mature", "AND o.day_number=2 AND o.mature AND o.cohort_date=DATE '2026-09-02'")
latest=latest.replace("DATE '2026-09-01' AS cohort_start", "DATE '2026-09-02' AS cohort_start")
(ROOT/'sql/06b_latest_app_dimensions.sql').write_text(latest,encoding='utf-8')
(ROOT/'sql/06c_latest_app_dimensions_bounded.sql').write_text(latest.replace('2026-09-01','2026-09-02'),encoding='utf-8')
