-- Aggregate-only freshness check for the next complete source date.
WITH ares AS (
  SELECT target_day AS cohort_date, new_users_today AS value
  FROM `wajenigeria.ares_hfyl.user_activety_indicators_downloadchannel`
), ltv AS (
  SELECT target_day AS cohort_date, ltv_1 AS value
  FROM `wajenigeria.track_hfyl.user_ltv`
), profile AS (
  SELECT target_day AS cohort_date, user_id
  FROM `wajenigeria.origin_hfyl.user_xlid`
), active AS (
  SELECT target_day AS cohort_date, user_id
  FROM `wajenigeria.origin_hfyl.realtime_edw_user_version_daily`
), payments AS (
  SELECT target_day AS cohort_date, user_id, order_no
  FROM `wajenigeria.origin_hfyl.view_event_pay`
  WHERE event_type = 'order_success'
)
SELECT 'ares_lifecycle' AS source_name, COUNT(*) AS row_count, CAST(NULL AS INT64) AS approx_subject_count
FROM ares WHERE cohort_date = DATE '2026-09-03'
UNION ALL
SELECT 'track_ltv' AS source_name, COUNT(*) AS row_count, CAST(NULL AS INT64) AS approx_subject_count
FROM ltv WHERE cohort_date = DATE '2026-09-03'
UNION ALL
SELECT 'user_profile' AS source_name, COUNT(*) AS row_count, APPROX_COUNT_DISTINCT(user_id) AS approx_subject_count
FROM profile WHERE cohort_date = DATE '2026-09-03'
UNION ALL
SELECT 'daily_active' AS source_name, COUNT(*) AS row_count, APPROX_COUNT_DISTINCT(user_id) AS approx_subject_count
FROM active WHERE cohort_date = DATE '2026-09-03'
UNION ALL
SELECT 'success_orders' AS source_name, COUNT(*) AS row_count, APPROX_COUNT_DISTINCT(user_id) AS approx_subject_count
FROM payments WHERE cohort_date = DATE '2026-09-03'
ORDER BY source_name;
