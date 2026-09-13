-- Aggregate-only mapping and first-pay completeness, one bounded daily snapshot.
WITH snapshots AS (
 SELECT target_day AS cohort_date, first_client_type, first_package_name, download_channel, user_id, first_pay_date
 FROM `wajenigeria.origin_hfyl.user_events`
 WHERE target_day = DATE '2026-09-03'
)
SELECT first_client_type,
  COALESCE(NULLIF(first_package_name,''),'(blank)') AS first_package_name,
  COALESCE(NULLIF(download_channel,''),'(blank)') AS download_channel,
  COUNT(DISTINCT user_id) AS users,
  COUNT(DISTINCT IF(first_pay_date IS NOT NULL,user_id,NULL)) AS first_pay_known_users,
  COUNT(DISTINCT IF(first_pay_date BETWEEN DATE '2026-06-01' AND DATE '2026-09-03',user_id,NULL)) AS in_scope_first_payers
FROM snapshots
WHERE cohort_date = DATE '2026-09-03'
GROUP BY first_client_type, first_package_name, download_channel
HAVING COUNT(DISTINCT user_id) >= 10
ORDER BY users DESC
LIMIT 3000;
