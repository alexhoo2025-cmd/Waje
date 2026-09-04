-- Aggregate-only H5 natural lifecycle retention and cumulative LTV.
-- The H5 natural source mapping is PAWAJEBETH5 / PAWAJEBETH501.
-- A lifecycle day is the Nth natural day: Day 2 = cohort_date + 1 day.
WITH base AS (
  SELECT
    target_day AS cohort_date,
    FORMAT_DATE('%Y-%m', target_day) AS cohort_month,
    COALESCE(today_newusers, new_users_today, 0) AS new_users,
    day_2_retainusers,
    day_3_retainusers,
    day_4_retainusers,
    day_5_retainusers,
    day_6_retainusers,
    day_7_retainusers,
    day_8_retainusers,
    day_14_retainusers,
    day_30_retainusers,
    day_60_retainusers,
    ltv_1, ltv_2, ltv_3, ltv_4, ltv_5, ltv_6, ltv_7,
    ltv_8, ltv_9, ltv_10, ltv_11, ltv_12, ltv_13, ltv_14,
    ltv_30, ltv_60, ltv_90
  FROM `wajenigeria.ares_hfyl.user_activety_indicators_downloadchannel`
  WHERE target_day BETWEEN DATE '2026-06-01' AND DATE '2026-08-31'
    AND channel = 'PAWAJEBETH5'
    AND sub_channel = 'PAWAJEBETH501'
), monthly AS (
  SELECT
    cohort_month,
    SUM(new_users) AS new_users,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-09-03', day_2_retainusers, NULL)), SUM(IF(cohort_date <= DATE '2026-09-03', new_users, NULL))) AS day_2_retention,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-09-02', day_3_retainusers, NULL)), SUM(IF(cohort_date <= DATE '2026-09-02', new_users, NULL))) AS day_3_retention,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-09-01', day_4_retainusers, NULL)), SUM(IF(cohort_date <= DATE '2026-09-01', new_users, NULL))) AS day_4_retention,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-31', day_5_retainusers, NULL)), SUM(IF(cohort_date <= DATE '2026-08-31', new_users, NULL))) AS day_5_retention,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-30', day_6_retainusers, NULL)), SUM(IF(cohort_date <= DATE '2026-08-30', new_users, NULL))) AS day_6_retention,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-29', day_7_retainusers, NULL)), SUM(IF(cohort_date <= DATE '2026-08-29', new_users, NULL))) AS day_7_retention,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-28', day_8_retainusers, NULL)), SUM(IF(cohort_date <= DATE '2026-08-28', new_users, NULL))) AS day_8_retention,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-22', day_14_retainusers, NULL)), SUM(IF(cohort_date <= DATE '2026-08-22', new_users, NULL))) AS day_14_retention,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-06', day_30_retainusers, NULL)), SUM(IF(cohort_date <= DATE '2026-08-06', new_users, NULL))) AS day_30_retention,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-07-07', day_60_retainusers, NULL)), SUM(IF(cohort_date <= DATE '2026-07-07', new_users, NULL))) AS day_60_retention,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-09-04', ltv_1, NULL)), SUM(IF(cohort_date <= DATE '2026-09-04', new_users, NULL))) AS ltv_1,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-09-03', ltv_2, NULL)), SUM(IF(cohort_date <= DATE '2026-09-03', new_users, NULL))) AS ltv_2,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-09-02', ltv_3, NULL)), SUM(IF(cohort_date <= DATE '2026-09-02', new_users, NULL))) AS ltv_3,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-09-01', ltv_4, NULL)), SUM(IF(cohort_date <= DATE '2026-09-01', new_users, NULL))) AS ltv_4,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-31', ltv_5, NULL)), SUM(IF(cohort_date <= DATE '2026-08-31', new_users, NULL))) AS ltv_5,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-30', ltv_6, NULL)), SUM(IF(cohort_date <= DATE '2026-08-30', new_users, NULL))) AS ltv_6,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-29', ltv_7, NULL)), SUM(IF(cohort_date <= DATE '2026-08-29', new_users, NULL))) AS ltv_7,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-28', ltv_8, NULL)), SUM(IF(cohort_date <= DATE '2026-08-28', new_users, NULL))) AS ltv_8,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-27', ltv_9, NULL)), SUM(IF(cohort_date <= DATE '2026-08-27', new_users, NULL))) AS ltv_9,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-26', ltv_10, NULL)), SUM(IF(cohort_date <= DATE '2026-08-26', new_users, NULL))) AS ltv_10,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-25', ltv_11, NULL)), SUM(IF(cohort_date <= DATE '2026-08-25', new_users, NULL))) AS ltv_11,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-24', ltv_12, NULL)), SUM(IF(cohort_date <= DATE '2026-08-24', new_users, NULL))) AS ltv_12,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-23', ltv_13, NULL)), SUM(IF(cohort_date <= DATE '2026-08-23', new_users, NULL))) AS ltv_13,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-22', ltv_14, NULL)), SUM(IF(cohort_date <= DATE '2026-08-22', new_users, NULL))) AS ltv_14,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-06', ltv_30, NULL)), SUM(IF(cohort_date <= DATE '2026-08-06', new_users, NULL))) AS ltv_30,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-07-07', ltv_60, NULL)), SUM(IF(cohort_date <= DATE '2026-07-07', new_users, NULL))) AS ltv_60,
    SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-06-07', ltv_90, NULL)), SUM(IF(cohort_date <= DATE '2026-06-07', new_users, NULL))) AS ltv_90
  FROM base
  GROUP BY cohort_month
)
SELECT
  cohort_month,
  new_users,
  day_2_retention, day_3_retention, day_4_retention, day_5_retention,
  day_6_retention, day_7_retention, day_8_retention, day_14_retention,
  day_30_retention, day_60_retention,
  ltv_1, ltv_2, ltv_3, ltv_4, ltv_5, ltv_6, ltv_7, ltv_8, ltv_9,
  ltv_10, ltv_11, ltv_12, ltv_13, ltv_14, ltv_30, ltv_60, ltv_90,
  DATE '2026-09-04' AS data_cutoff_date
FROM monthly
WHERE cohort_month BETWEEN '2026-06' AND '2026-08'
ORDER BY cohort_month;
