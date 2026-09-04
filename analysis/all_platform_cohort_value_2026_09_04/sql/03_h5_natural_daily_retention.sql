-- Aggregate-only strict H5 natural retention by registration cohort date.
-- Day N means the Nth natural day: Day 2 = cohort_date + 1 day.
-- Return is any Waje daily-active record, not a same-package-only return.
WITH h5_cohort AS (
  SELECT DISTINCT
    target_day AS cohort_date,
    user_id
  FROM `wajenigeria.origin_hfyl.user_events`
  WHERE target_day BETWEEN DATE '2026-06-01' AND DATE '2026-08-31'
    AND SAFE.PARSE_DATE('%Y-%m-%d', register_day) = target_day
    AND first_package_name = 'com.wajegame.web'
    AND download_channel = 'PAWAJEBETH5'
    AND first_channel = 'PAWAJEBETH5'
    AND first_sub_channel = 'PAWAJEBETH5'
), active_source AS (
  SELECT
    target_day AS activity_date,
    user_id
  FROM `wajenigeria.origin_hfyl.realtime_edw_user_version_daily`
  WHERE target_day BETWEEN DATE '2026-06-01' AND DATE '2026-09-04'
), active_calendar AS (
  SELECT activity_date, COUNT(*) AS source_rows
  FROM active_source
  GROUP BY activity_date
), active_daily AS (
  SELECT DISTINCT activity_date, user_id
  FROM active_source
), daily AS (
  SELECT
    cohort_date,
    COUNT(DISTINCT h5_cohort.user_id) AS cohort_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort_date, INTERVAL 1 DAY), h5_cohort.user_id, NULL)) AS day_2_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort_date, INTERVAL 2 DAY), h5_cohort.user_id, NULL)) AS day_3_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort_date, INTERVAL 3 DAY), h5_cohort.user_id, NULL)) AS day_4_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort_date, INTERVAL 4 DAY), h5_cohort.user_id, NULL)) AS day_5_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort_date, INTERVAL 5 DAY), h5_cohort.user_id, NULL)) AS day_6_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort_date, INTERVAL 6 DAY), h5_cohort.user_id, NULL)) AS day_7_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort_date, INTERVAL 7 DAY), h5_cohort.user_id, NULL)) AS day_8_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort_date, INTERVAL 8 DAY), h5_cohort.user_id, NULL)) AS day_9_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort_date, INTERVAL 9 DAY), h5_cohort.user_id, NULL)) AS day_10_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort_date, INTERVAL 10 DAY), h5_cohort.user_id, NULL)) AS day_11_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort_date, INTERVAL 11 DAY), h5_cohort.user_id, NULL)) AS day_12_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort_date, INTERVAL 12 DAY), h5_cohort.user_id, NULL)) AS day_13_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort_date, INTERVAL 13 DAY), h5_cohort.user_id, NULL)) AS day_14_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort_date, INTERVAL 29 DAY), h5_cohort.user_id, NULL)) AS day_30_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort_date, INTERVAL 59 DAY), h5_cohort.user_id, NULL)) AS day_60_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort_date, INTERVAL 89 DAY), h5_cohort.user_id, NULL)) AS day_90_users
  FROM h5_cohort
  LEFT JOIN active_daily USING (user_id)
  GROUP BY cohort_date
)
SELECT
  cohort_date,
  cohort_users,
  IF(EXISTS(SELECT 1 FROM active_calendar WHERE activity_date = DATE_ADD(cohort_date, INTERVAL 1 DAY)), day_2_users, NULL) AS day_2_retained_users,
  IF(EXISTS(SELECT 1 FROM active_calendar WHERE activity_date = DATE_ADD(cohort_date, INTERVAL 1 DAY)), SAFE_DIVIDE(day_2_users, cohort_users), NULL) AS day_2_retention,
  IF(EXISTS(SELECT 1 FROM active_calendar WHERE activity_date = DATE_ADD(cohort_date, INTERVAL 2 DAY)), SAFE_DIVIDE(day_3_users, cohort_users), NULL) AS day_3_retention,
  IF(EXISTS(SELECT 1 FROM active_calendar WHERE activity_date = DATE_ADD(cohort_date, INTERVAL 3 DAY)), SAFE_DIVIDE(day_4_users, cohort_users), NULL) AS day_4_retention,
  IF(EXISTS(SELECT 1 FROM active_calendar WHERE activity_date = DATE_ADD(cohort_date, INTERVAL 4 DAY)), SAFE_DIVIDE(day_5_users, cohort_users), NULL) AS day_5_retention,
  IF(EXISTS(SELECT 1 FROM active_calendar WHERE activity_date = DATE_ADD(cohort_date, INTERVAL 5 DAY)), SAFE_DIVIDE(day_6_users, cohort_users), NULL) AS day_6_retention,
  IF(EXISTS(SELECT 1 FROM active_calendar WHERE activity_date = DATE_ADD(cohort_date, INTERVAL 6 DAY)), SAFE_DIVIDE(day_7_users, cohort_users), NULL) AS day_7_retention,
  IF(EXISTS(SELECT 1 FROM active_calendar WHERE activity_date = DATE_ADD(cohort_date, INTERVAL 7 DAY)), SAFE_DIVIDE(day_8_users, cohort_users), NULL) AS day_8_retention,
  IF(EXISTS(SELECT 1 FROM active_calendar WHERE activity_date = DATE_ADD(cohort_date, INTERVAL 8 DAY)), SAFE_DIVIDE(day_9_users, cohort_users), NULL) AS day_9_retention,
  IF(EXISTS(SELECT 1 FROM active_calendar WHERE activity_date = DATE_ADD(cohort_date, INTERVAL 9 DAY)), SAFE_DIVIDE(day_10_users, cohort_users), NULL) AS day_10_retention,
  IF(EXISTS(SELECT 1 FROM active_calendar WHERE activity_date = DATE_ADD(cohort_date, INTERVAL 10 DAY)), SAFE_DIVIDE(day_11_users, cohort_users), NULL) AS day_11_retention,
  IF(EXISTS(SELECT 1 FROM active_calendar WHERE activity_date = DATE_ADD(cohort_date, INTERVAL 11 DAY)), SAFE_DIVIDE(day_12_users, cohort_users), NULL) AS day_12_retention,
  IF(EXISTS(SELECT 1 FROM active_calendar WHERE activity_date = DATE_ADD(cohort_date, INTERVAL 12 DAY)), SAFE_DIVIDE(day_13_users, cohort_users), NULL) AS day_13_retention,
  IF(EXISTS(SELECT 1 FROM active_calendar WHERE activity_date = DATE_ADD(cohort_date, INTERVAL 13 DAY)), SAFE_DIVIDE(day_14_users, cohort_users), NULL) AS day_14_retention,
  IF(EXISTS(SELECT 1 FROM active_calendar WHERE activity_date = DATE_ADD(cohort_date, INTERVAL 29 DAY)), SAFE_DIVIDE(day_30_users, cohort_users), NULL) AS day_30_retention,
  IF(EXISTS(SELECT 1 FROM active_calendar WHERE activity_date = DATE_ADD(cohort_date, INTERVAL 59 DAY)), SAFE_DIVIDE(day_60_users, cohort_users), NULL) AS day_60_retention,
  IF(EXISTS(SELECT 1 FROM active_calendar WHERE activity_date = DATE_ADD(cohort_date, INTERVAL 89 DAY)), SAFE_DIVIDE(day_90_users, cohort_users), NULL) AS day_90_retention,
  DATE '2026-09-04' AS data_cutoff_date
FROM daily
WHERE cohort_date BETWEEN DATE '2026-06-01' AND DATE '2026-08-31'
  AND cohort_users >= 10
ORDER BY cohort_date;
