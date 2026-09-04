-- Aggregate-only coverage check for the partitioned user_xlid profile on payment days.
WITH profile_daily AS (
  SELECT
    target_day AS cohort_date,
    user_id,
    register_day,
    first_pay_date,
    first_package_name,
    download_channel,
    first_client_type
  FROM `wajenigeria.origin_hfyl.user_xlid`
)
SELECT
  cohort_date AS target_day,
  COUNT(*) AS profile_rows,
  APPROX_COUNT_DISTINCT(user_id) AS approx_subject_count,
  COUNTIF(SAFE.PARSE_DATE('%Y-%m-%d', register_day) = cohort_date) AS registered_same_day_rows,
  COUNTIF(first_pay_date IS NOT NULL AND first_pay_date != '') AS nonblank_first_pay_date_rows,
  COUNTIF(first_package_name IS NOT NULL AND first_package_name != '') AS nonblank_first_package_rows,
  COUNTIF(download_channel IS NOT NULL AND download_channel != '') AS nonblank_download_channel_rows
FROM profile_daily
WHERE cohort_date BETWEEN DATE '2026-08-27' AND DATE '2026-09-02'
GROUP BY cohort_date
ORDER BY target_day;
