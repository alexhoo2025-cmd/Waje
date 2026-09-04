-- Aggregate-only account-level retention by first platform.
-- Replace cohort date literals per month before execution.
WITH profile_daily AS (
  SELECT
    target_day AS cohort_date,
    user_id,
    register_day,
    first_client_type
  FROM `wajenigeria.origin_hfyl.user_events`
), cohort AS (
  SELECT DISTINCT
    cohort_date,
    user_id,
    CASE first_client_type WHEN 3 THEN 'H5' WHEN 2 THEN 'Android' WHEN 1 THEN 'iOS' ELSE 'Unknown' END AS platform
  FROM profile_daily
  WHERE cohort_date BETWEEN DATE '2026-08-01' AND DATE '2026-08-31'
    AND SAFE.PARSE_DATE('%Y-%m-%d', register_day) = cohort_date
), active_daily AS (
  SELECT DISTINCT
    target_day AS activity_date,
    user_id
  FROM `wajenigeria.origin_hfyl.realtime_edw_user_version_daily`
  WHERE target_day BETWEEN DATE '2026-06-01' AND DATE '2026-09-02'
), retention AS (
  SELECT
    cohort.cohort_date,
    cohort.platform,
    COUNT(DISTINCT cohort.user_id) AS cohort_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort.cohort_date, INTERVAL 1 DAY), cohort.user_id, NULL)) AS d2_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort.cohort_date, INTERVAL 6 DAY), cohort.user_id, NULL)) AS d7_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort.cohort_date, INTERVAL 13 DAY), cohort.user_id, NULL)) AS d14_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort.cohort_date, INTERVAL 29 DAY), cohort.user_id, NULL)) AS d30_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort.cohort_date, INTERVAL 59 DAY), cohort.user_id, NULL)) AS d60_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort.cohort_date, INTERVAL 89 DAY), cohort.user_id, NULL)) AS d90_users
  FROM cohort
  LEFT JOIN active_daily USING (user_id)
  GROUP BY cohort.cohort_date, cohort.platform
)
SELECT
  cohort_date,
  platform,
  cohort_users,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 1 DAY) AND DATE_ADD(cohort_date, INTERVAL 1 DAY) >= DATE '2026-06-30', SAFE_DIVIDE(d2_users, cohort_users), NULL) AS d2_retention,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 6 DAY) AND DATE_ADD(cohort_date, INTERVAL 6 DAY) >= DATE '2026-06-30', SAFE_DIVIDE(d7_users, cohort_users), NULL) AS d7_retention,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 13 DAY) AND DATE_ADD(cohort_date, INTERVAL 13 DAY) >= DATE '2026-06-30', SAFE_DIVIDE(d14_users, cohort_users), NULL) AS d14_retention,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 29 DAY) AND DATE_ADD(cohort_date, INTERVAL 29 DAY) >= DATE '2026-06-30', SAFE_DIVIDE(d30_users, cohort_users), NULL) AS d30_retention,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 59 DAY) AND DATE_ADD(cohort_date, INTERVAL 59 DAY) >= DATE '2026-06-30', SAFE_DIVIDE(d60_users, cohort_users), NULL) AS d60_retention,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 89 DAY) AND DATE_ADD(cohort_date, INTERVAL 89 DAY) >= DATE '2026-06-30', SAFE_DIVIDE(d90_users, cohort_users), NULL) AS d90_retention,
  DATE '2026-09-02' AS data_cutoff_date
FROM retention
WHERE cohort_users >= 10
ORDER BY cohort_date, platform;
