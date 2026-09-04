-- Aggregate-only account-level retention by first platform.
-- Day N means the Nth natural day: Day 2 = cohort_date + 1 day.
WITH cohort AS (
  SELECT DISTINCT
    target_day AS cohort_date,
    user_id,
    CASE first_client_type
      WHEN 3 THEN 'H5'
      WHEN 2 THEN 'Android'
      WHEN 1 THEN 'iOS'
      ELSE 'Unknown'
    END AS platform
  FROM `wajenigeria.origin_hfyl.user_events`
  WHERE target_day BETWEEN DATE '2026-06-01' AND DATE '2026-08-31'
    AND SAFE.PARSE_DATE('%Y-%m-%d', register_day) = target_day
), active_source AS (
  SELECT target_day AS activity_date, user_id
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
    platform,
    COUNT(DISTINCT cohort.user_id) AS cohort_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort_date, INTERVAL 1 DAY), cohort.user_id, NULL)) AS day_2_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort_date, INTERVAL 2 DAY), cohort.user_id, NULL)) AS day_3_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort_date, INTERVAL 6 DAY), cohort.user_id, NULL)) AS day_7_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort_date, INTERVAL 13 DAY), cohort.user_id, NULL)) AS day_14_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort_date, INTERVAL 29 DAY), cohort.user_id, NULL)) AS day_30_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort_date, INTERVAL 59 DAY), cohort.user_id, NULL)) AS day_60_users,
    COUNT(DISTINCT IF(active_daily.activity_date = DATE_ADD(cohort_date, INTERVAL 89 DAY), cohort.user_id, NULL)) AS day_90_users
  FROM cohort
  LEFT JOIN active_daily USING (user_id)
  GROUP BY cohort_date, platform
)
SELECT
  cohort_date,
  platform,
  cohort_users,
  IF(EXISTS(SELECT 1 FROM active_calendar WHERE activity_date = DATE_ADD(cohort_date, INTERVAL 1 DAY)), SAFE_DIVIDE(day_2_users, cohort_users), NULL) AS day_2_retention,
  IF(EXISTS(SELECT 1 FROM active_calendar WHERE activity_date = DATE_ADD(cohort_date, INTERVAL 2 DAY)), SAFE_DIVIDE(day_3_users, cohort_users), NULL) AS day_3_retention,
  IF(EXISTS(SELECT 1 FROM active_calendar WHERE activity_date = DATE_ADD(cohort_date, INTERVAL 6 DAY)), SAFE_DIVIDE(day_7_users, cohort_users), NULL) AS day_7_retention,
  IF(EXISTS(SELECT 1 FROM active_calendar WHERE activity_date = DATE_ADD(cohort_date, INTERVAL 13 DAY)), SAFE_DIVIDE(day_14_users, cohort_users), NULL) AS day_14_retention,
  IF(EXISTS(SELECT 1 FROM active_calendar WHERE activity_date = DATE_ADD(cohort_date, INTERVAL 29 DAY)), SAFE_DIVIDE(day_30_users, cohort_users), NULL) AS day_30_retention,
  IF(EXISTS(SELECT 1 FROM active_calendar WHERE activity_date = DATE_ADD(cohort_date, INTERVAL 59 DAY)), SAFE_DIVIDE(day_60_users, cohort_users), NULL) AS day_60_retention,
  IF(EXISTS(SELECT 1 FROM active_calendar WHERE activity_date = DATE_ADD(cohort_date, INTERVAL 89 DAY)), SAFE_DIVIDE(day_90_users, cohort_users), NULL) AS day_90_retention,
  DATE '2026-09-04' AS data_cutoff_date
FROM daily
WHERE cohort_date BETWEEN DATE '2026-06-01' AND DATE '2026-08-31'
  AND cohort_users >= 10
ORDER BY cohort_date, platform;
