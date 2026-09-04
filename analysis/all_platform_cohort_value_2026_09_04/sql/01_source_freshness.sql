-- Aggregate-only source freshness and latest-complete-date probe.
-- No users, orders, transactions, or other row-level facts are returned.
WITH source_dates AS (
  SELECT 'ares_lifecycle' AS source_name, target_day AS cohort_date
  FROM `wajenigeria.ares_hfyl.user_activety_indicators_downloadchannel`
  WHERE target_day BETWEEN DATE '2026-08-28' AND DATE '2026-09-04'
  UNION ALL
  SELECT 'track_ltv' AS source_name, target_day AS cohort_date
  FROM `wajenigeria.track_hfyl.user_ltv`
  WHERE target_day BETWEEN DATE '2026-08-28' AND DATE '2026-09-04'
  UNION ALL
  SELECT 'registration_profile' AS source_name, target_day AS cohort_date
  FROM `wajenigeria.origin_hfyl.user_events`
  WHERE target_day BETWEEN DATE '2026-08-28' AND DATE '2026-09-04'
  UNION ALL
  SELECT 'daily_active' AS source_name, target_day AS cohort_date
  FROM `wajenigeria.origin_hfyl.realtime_edw_user_version_daily`
  WHERE target_day BETWEEN DATE '2026-08-28' AND DATE '2026-09-04'
  UNION ALL
  SELECT 'success_orders' AS source_name, target_day AS cohort_date
  FROM `wajenigeria.origin_hfyl.view_event_pay`
  WHERE target_day BETWEEN DATE '2026-08-28' AND DATE '2026-09-04'
    AND event_type = 'order_success'
)
SELECT
  source_name,
  MIN(cohort_date) AS first_seen_date,
  MAX(cohort_date) AS latest_seen_date,
  COUNT(*) AS row_count,
  COUNT(DISTINCT cohort_date) AS distinct_date_count
FROM source_dates
WHERE cohort_date BETWEEN DATE '2026-08-28' AND DATE '2026-09-04'
GROUP BY source_name
ORDER BY source_name;
