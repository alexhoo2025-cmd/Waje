-- Aggregate-only account-level retention for the strictly mapped H5 natural cohort.
-- Retention is any observed Waje daily-active record; package-level return is not inferred.
WITH profile_daily AS (
  SELECT
    target_day AS cohort_date,
    user_id,
    register_day,
    first_package_name,
    download_channel,
    first_channel,
    first_sub_channel
  FROM `wajenigeria.origin_hfyl.user_events`
), h5_natural_cohort AS (
  SELECT DISTINCT
    cohort_date,
    user_id
  FROM profile_daily
  WHERE cohort_date BETWEEN DATE '2026-08-01' AND DATE '2026-08-31'
    AND SAFE.PARSE_DATE('%Y-%m-%d', register_day) = cohort_date
    AND first_package_name = 'com.wajegame.web'
    AND download_channel = 'PAWAJEBETH5'
    AND first_channel = 'PAWAJEBETH5'
    AND first_sub_channel = 'PAWAJEBETH5'
), active_daily AS (
  SELECT DISTINCT
    target_day AS activity_date,
    user_id
  FROM `wajenigeria.origin_hfyl.realtime_edw_user_version_daily`
  WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-09-02'
), retention AS (
  SELECT
    h5_natural_cohort.cohort_date,
    COUNT(DISTINCT h5_natural_cohort.user_id) AS cohort_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(h5_natural_cohort.cohort_date, INTERVAL 1 DAY), h5_natural_cohort.user_id, NULL)) AS day_2_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(h5_natural_cohort.cohort_date, INTERVAL 2 DAY), h5_natural_cohort.user_id, NULL)) AS day_3_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(h5_natural_cohort.cohort_date, INTERVAL 3 DAY), h5_natural_cohort.user_id, NULL)) AS day_4_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(h5_natural_cohort.cohort_date, INTERVAL 4 DAY), h5_natural_cohort.user_id, NULL)) AS day_5_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(h5_natural_cohort.cohort_date, INTERVAL 5 DAY), h5_natural_cohort.user_id, NULL)) AS day_6_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(h5_natural_cohort.cohort_date, INTERVAL 6 DAY), h5_natural_cohort.user_id, NULL)) AS day_7_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(h5_natural_cohort.cohort_date, INTERVAL 7 DAY), h5_natural_cohort.user_id, NULL)) AS day_8_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(h5_natural_cohort.cohort_date, INTERVAL 8 DAY), h5_natural_cohort.user_id, NULL)) AS day_9_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(h5_natural_cohort.cohort_date, INTERVAL 9 DAY), h5_natural_cohort.user_id, NULL)) AS day_10_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(h5_natural_cohort.cohort_date, INTERVAL 10 DAY), h5_natural_cohort.user_id, NULL)) AS day_11_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(h5_natural_cohort.cohort_date, INTERVAL 11 DAY), h5_natural_cohort.user_id, NULL)) AS day_12_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(h5_natural_cohort.cohort_date, INTERVAL 12 DAY), h5_natural_cohort.user_id, NULL)) AS day_13_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(h5_natural_cohort.cohort_date, INTERVAL 13 DAY), h5_natural_cohort.user_id, NULL)) AS day_14_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(h5_natural_cohort.cohort_date, INTERVAL 29 DAY), h5_natural_cohort.user_id, NULL)) AS day_30_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(h5_natural_cohort.cohort_date, INTERVAL 59 DAY), h5_natural_cohort.user_id, NULL)) AS day_60_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(h5_natural_cohort.cohort_date, INTERVAL 89 DAY), h5_natural_cohort.user_id, NULL)) AS day_90_users
  FROM h5_natural_cohort
  LEFT JOIN active_daily USING (user_id)
  GROUP BY h5_natural_cohort.cohort_date
)
SELECT
  cohort_date,
  cohort_users,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 1 DAY) AND DATE_ADD(cohort_date, INTERVAL 1 DAY) >= DATE '2026-06-30', day_2_users, NULL) AS day_2_retained_users,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 1 DAY) AND DATE_ADD(cohort_date, INTERVAL 1 DAY) >= DATE '2026-06-30', SAFE_DIVIDE(day_2_users, cohort_users), NULL) AS day_2_retention,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 2 DAY) AND DATE_ADD(cohort_date, INTERVAL 2 DAY) >= DATE '2026-06-30', SAFE_DIVIDE(day_3_users, cohort_users), NULL) AS day_3_retention,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 3 DAY) AND DATE_ADD(cohort_date, INTERVAL 3 DAY) >= DATE '2026-06-30', SAFE_DIVIDE(day_4_users, cohort_users), NULL) AS day_4_retention,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 4 DAY) AND DATE_ADD(cohort_date, INTERVAL 4 DAY) >= DATE '2026-06-30', SAFE_DIVIDE(day_5_users, cohort_users), NULL) AS day_5_retention,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 5 DAY) AND DATE_ADD(cohort_date, INTERVAL 5 DAY) >= DATE '2026-06-30', SAFE_DIVIDE(day_6_users, cohort_users), NULL) AS day_6_retention,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 6 DAY) AND DATE_ADD(cohort_date, INTERVAL 6 DAY) >= DATE '2026-06-30', SAFE_DIVIDE(day_7_users, cohort_users), NULL) AS day_7_retention,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 7 DAY) AND DATE_ADD(cohort_date, INTERVAL 7 DAY) >= DATE '2026-06-30', SAFE_DIVIDE(day_8_users, cohort_users), NULL) AS day_8_retention,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 8 DAY) AND DATE_ADD(cohort_date, INTERVAL 8 DAY) >= DATE '2026-06-30', SAFE_DIVIDE(day_9_users, cohort_users), NULL) AS day_9_retention,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 9 DAY) AND DATE_ADD(cohort_date, INTERVAL 9 DAY) >= DATE '2026-06-30', SAFE_DIVIDE(day_10_users, cohort_users), NULL) AS day_10_retention,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 10 DAY) AND DATE_ADD(cohort_date, INTERVAL 10 DAY) >= DATE '2026-06-30', SAFE_DIVIDE(day_11_users, cohort_users), NULL) AS day_11_retention,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 11 DAY) AND DATE_ADD(cohort_date, INTERVAL 11 DAY) >= DATE '2026-06-30', SAFE_DIVIDE(day_12_users, cohort_users), NULL) AS day_12_retention,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 12 DAY) AND DATE_ADD(cohort_date, INTERVAL 12 DAY) >= DATE '2026-06-30', SAFE_DIVIDE(day_13_users, cohort_users), NULL) AS day_13_retention,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 13 DAY) AND DATE_ADD(cohort_date, INTERVAL 13 DAY) >= DATE '2026-06-30', SAFE_DIVIDE(day_14_users, cohort_users), NULL) AS day_14_retention,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 29 DAY) AND DATE_ADD(cohort_date, INTERVAL 29 DAY) >= DATE '2026-06-30', SAFE_DIVIDE(day_30_users, cohort_users), NULL) AS day_30_retention,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 59 DAY) AND DATE_ADD(cohort_date, INTERVAL 59 DAY) >= DATE '2026-06-30', SAFE_DIVIDE(day_60_users, cohort_users), NULL) AS day_60_retention,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 89 DAY) AND DATE_ADD(cohort_date, INTERVAL 89 DAY) >= DATE '2026-06-30', SAFE_DIVIDE(day_90_users, cohort_users), NULL) AS day_90_retention,
  DATE '2026-09-02' AS data_cutoff_date
FROM retention
WHERE cohort_users >= 10
ORDER BY cohort_date;
