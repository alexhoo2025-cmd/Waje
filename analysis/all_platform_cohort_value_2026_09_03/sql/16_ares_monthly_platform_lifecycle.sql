-- Aggregate-only maturity-aware lifecycle and value comparison at platform level.
WITH base AS (
  SELECT
    target_day AS cohort_date,
    FORMAT_DATE('%Y-%m', target_day) AS cohort_month,
    CASE
      WHEN UPPER(COALESCE(channel, '')) LIKE '%H5%' THEN 'H5'
      WHEN UPPER(COALESCE(channel, '')) LIKE '%IOS%' THEN 'iOS'
      WHEN UPPER(COALESCE(channel, '')) LIKE '%PALM%' OR UPPER(COALESCE(channel, '')) LIKE '%WAJE%' THEN 'Android'
      ELSE 'Unknown'
    END AS platform,
    COALESCE(today_newusers, new_users_today, 0) AS new_users,
    COALESCE(day_2_retainusers, 0) AS d2,
    COALESCE(day_7_retainusers, 0) AS d7,
    COALESCE(day_14_retainusers, 0) AS d14,
    COALESCE(day_30_retainusers, 0) AS d30,
    COALESCE(day_60_retainusers, 0) AS d60,
    COALESCE(ltv_1, 0) AS ltv1,
    COALESCE(ltv_7, 0) AS ltv7,
    COALESCE(ltv_14, 0) AS ltv14,
    COALESCE(ltv_30, 0) AS ltv30,
    COALESCE(ltv_60, 0) AS ltv60,
    COALESCE(ltv_90, 0) AS ltv90,
    COALESCE(pay_users_count, 0) AS pay_users,
    COALESCE(pay_amount, 0) AS pay_amount
  FROM `wajenigeria.ares_hfyl.user_activety_indicators_downloadchannel`
)
SELECT
  cohort_month,
  platform,
  SUM(new_users) AS new_users,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-09-01', d2, 0)), SUM(IF(cohort_date <= DATE '2026-09-01', new_users, 0))) AS d2_retention,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-27', d7, 0)), SUM(IF(cohort_date <= DATE '2026-08-27', new_users, 0))) AS d7_retention,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-20', d14, 0)), SUM(IF(cohort_date <= DATE '2026-08-20', new_users, 0))) AS d14_retention,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-04', d30, 0)), SUM(IF(cohort_date <= DATE '2026-08-04', new_users, 0))) AS d30_retention,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-07-05', d60, 0)), SUM(IF(cohort_date <= DATE '2026-07-05', new_users, 0))) AS d60_retention,
  SAFE_DIVIDE(SUM(ltv1), SUM(new_users)) AS source_ltv_1_per_new_user,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-27', ltv7, 0)), SUM(IF(cohort_date <= DATE '2026-08-27', new_users, 0))) AS source_ltv_7_per_new_user,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-20', ltv14, 0)), SUM(IF(cohort_date <= DATE '2026-08-20', new_users, 0))) AS source_ltv_14_per_new_user,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-04', ltv30, 0)), SUM(IF(cohort_date <= DATE '2026-08-04', new_users, 0))) AS source_ltv_30_per_new_user,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-07-05', ltv60, 0)), SUM(IF(cohort_date <= DATE '2026-07-05', new_users, 0))) AS source_ltv_60_per_new_user,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-06-05', ltv90, 0)), SUM(IF(cohort_date <= DATE '2026-06-05', new_users, 0))) AS source_ltv_90_per_new_user,
  SUM(pay_users) AS source_pay_user_days,
  SUM(pay_amount) AS source_pay_amount,
  SAFE_DIVIDE(SUM(pay_amount), SUM(new_users)) AS source_pay_arpu,
  SAFE_DIVIDE(SUM(pay_amount), SUM(pay_users)) AS source_pay_arppu
FROM base
WHERE cohort_date BETWEEN DATE '2026-06-01' AND DATE '2026-09-02'
GROUP BY cohort_month, platform
HAVING SUM(base.new_users) >= 10
ORDER BY cohort_month, platform;
