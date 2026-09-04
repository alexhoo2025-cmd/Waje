-- Aggregate-only mapping check for H5 Web registration cohorts and source channels.
WITH user_snapshot AS (
  SELECT
    target_day AS cohort_date,
    user_id,
    register_day,
    first_package_name,
    download_channel,
    first_channel,
    first_sub_channel,
    first_client_type
  FROM `wajenigeria.origin_hfyl.user_events`
)
SELECT
  cohort_date,
  COALESCE(NULLIF(first_package_name, ''), '(blank)') AS first_package_name,
  COALESCE(NULLIF(download_channel, ''), '(blank)') AS download_channel,
  COALESCE(NULLIF(first_channel, ''), '(blank)') AS first_channel,
  COALESCE(NULLIF(first_sub_channel, ''), '(blank)') AS first_sub_channel,
  first_client_type,
  APPROX_COUNT_DISTINCT(user_id) AS approx_registered_users
FROM user_snapshot
WHERE cohort_date BETWEEN DATE '2026-08-20' AND DATE '2026-08-27'
  AND SAFE.PARSE_DATE('%Y-%m-%d', register_day) = cohort_date
  AND first_package_name = 'com.wajegame.web'
GROUP BY cohort_date, first_package_name, download_channel, first_channel, first_sub_channel, first_client_type
HAVING APPROX_COUNT_DISTINCT(user_id) >= 10
ORDER BY cohort_date, approx_registered_users DESC
LIMIT 500;
