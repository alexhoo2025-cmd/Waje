-- Aggregate-only coverage and key-quality check for profile snapshot and daily active facts.
WITH profile_snapshot AS (
  SELECT
    target_day AS cohort_date,
    user_id,
    register_day,
    first_pay_date,
    first_package_name,
    download_channel,
    first_client_type
  FROM `wajenigeria.origin_hfyl.user_events`
), active_daily AS (
  SELECT
    target_day AS cohort_date,
    user_id,
    app_id
  FROM `wajenigeria.origin_hfyl.realtime_edw_user_version_daily`
)
SELECT
  'profile_snapshot_2026_09_02' AS result_type,
  MIN(cohort_date) AS min_target_day,
  MAX(cohort_date) AS max_target_day,
  COUNT(*) AS row_count,
  APPROX_COUNT_DISTINCT(user_id) AS approx_subject_count,
  COUNTIF(register_day IS NOT NULL AND register_day != '') AS nonblank_register_day_count,
  COUNTIF(first_pay_date IS NOT NULL) AS nonblank_first_pay_date_count,
  COUNTIF(first_package_name IS NOT NULL AND first_package_name != '') AS nonblank_package_count,
  COUNTIF(download_channel IS NOT NULL AND download_channel != '') AS nonblank_channel_count
FROM profile_snapshot
WHERE cohort_date = DATE '2026-09-02'
UNION ALL
SELECT
  'active_daily_2026_06_01_to_2026_09_02' AS result_type,
  MIN(cohort_date) AS min_target_day,
  MAX(cohort_date) AS max_target_day,
  COUNT(*) AS row_count,
  APPROX_COUNT_DISTINCT(user_id) AS approx_subject_count,
  CAST(NULL AS INT64) AS nonblank_register_day_count,
  CAST(NULL AS INT64) AS nonblank_first_pay_date_count,
  CAST(NULL AS INT64) AS nonblank_package_count,
  CAST(NULL AS INT64) AS nonblank_channel_count
FROM active_daily
WHERE cohort_date BETWEEN DATE '2026-06-01' AND DATE '2026-09-02';
