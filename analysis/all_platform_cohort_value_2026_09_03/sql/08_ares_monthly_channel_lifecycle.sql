-- Aggregate-only monthly lifecycle, value, and payment comparison by channel.
-- LTV values are weighted by the source's new-user count; no user/order rows are returned.
WITH base AS (
  SELECT
    target_day AS cohort_date,
    FORMAT_DATE('%Y-%m', target_day) AS cohort_month,
    COALESCE(NULLIF(channel, ''), '(blank)') AS channel,
    COALESCE(NULLIF(sub_channel, ''), '(blank)') AS sub_channel,
    CASE
      WHEN UPPER(COALESCE(channel, '')) LIKE '%H5%' THEN 'H5'
      WHEN UPPER(COALESCE(channel, '')) LIKE '%IOS%' THEN 'iOS'
      WHEN UPPER(COALESCE(channel, '')) LIKE '%PALM%' OR UPPER(COALESCE(channel, '')) LIKE '%WAJE%' THEN 'Android/Other'
      ELSE 'Unknown'
    END AS platform_group,
    COALESCE(today_newusers, new_users_today, 0) AS new_users,
    COALESCE(day_2_retainusers, 0) AS day_2_retainusers,
    COALESCE(day_3_retainusers, 0) AS day_3_retainusers,
    COALESCE(day_4_retainusers, 0) AS day_4_retainusers,
    COALESCE(day_5_retainusers, 0) AS day_5_retainusers,
    COALESCE(day_6_retainusers, 0) AS day_6_retainusers,
    COALESCE(day_7_retainusers, 0) AS day_7_retainusers,
    COALESCE(day_8_retainusers, 0) AS day_8_retainusers,
    COALESCE(day_14_retainusers, 0) AS day_14_retainusers,
    COALESCE(day_30_retainusers, 0) AS day_30_retainusers,
    COALESCE(day_60_retainusers, 0) AS day_60_retainusers,
    COALESCE(ltv_1, 0) AS ltv_1,
    COALESCE(ltv_2, 0) AS ltv_2,
    COALESCE(ltv_3, 0) AS ltv_3,
    COALESCE(ltv_4, 0) AS ltv_4,
    COALESCE(ltv_5, 0) AS ltv_5,
    COALESCE(ltv_6, 0) AS ltv_6,
    COALESCE(ltv_7, 0) AS ltv_7,
    COALESCE(ltv_8, 0) AS ltv_8,
    COALESCE(ltv_9, 0) AS ltv_9,
    COALESCE(ltv_10, 0) AS ltv_10,
    COALESCE(ltv_11, 0) AS ltv_11,
    COALESCE(ltv_12, 0) AS ltv_12,
    COALESCE(ltv_13, 0) AS ltv_13,
    COALESCE(ltv_14, 0) AS ltv_14,
    COALESCE(ltv_30, 0) AS ltv_30,
    COALESCE(ltv_60, 0) AS ltv_60,
    COALESCE(ltv_90, 0) AS ltv_90,
    COALESCE(pay_users_count, 0) AS pay_users_count,
    COALESCE(pay_amount, 0) AS pay_amount,
    COALESCE(first_pay_users, 0) AS first_pay_users,
    COALESCE(first_pay_amount, 0) AS first_pay_amount
  FROM `wajenigeria.ares_hfyl.user_activety_indicators_downloadchannel`
)
SELECT
  cohort_month,
  platform_group,
  channel,
  sub_channel,
  SUM(new_users) AS new_users,
  SUM(IF(cohort_date <= DATE '2026-09-01', new_users, 0)) AS mature_new_users_day_2,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-09-01', day_2_retainusers, 0)), SUM(IF(cohort_date <= DATE '2026-09-01', new_users, 0))) AS day_2_retention,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-31', day_3_retainusers, 0)), SUM(IF(cohort_date <= DATE '2026-08-31', new_users, 0))) AS day_3_retention,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-30', day_4_retainusers, 0)), SUM(IF(cohort_date <= DATE '2026-08-30', new_users, 0))) AS day_4_retention,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-29', day_5_retainusers, 0)), SUM(IF(cohort_date <= DATE '2026-08-29', new_users, 0))) AS day_5_retention,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-28', day_6_retainusers, 0)), SUM(IF(cohort_date <= DATE '2026-08-28', new_users, 0))) AS day_6_retention,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-27', day_7_retainusers, 0)), SUM(IF(cohort_date <= DATE '2026-08-27', new_users, 0))) AS day_7_retention,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-26', day_8_retainusers, 0)), SUM(IF(cohort_date <= DATE '2026-08-26', new_users, 0))) AS day_8_retention,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-20', day_14_retainusers, 0)), SUM(IF(cohort_date <= DATE '2026-08-20', new_users, 0))) AS day_14_retention,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-04', day_30_retainusers, 0)), SUM(IF(cohort_date <= DATE '2026-08-04', new_users, 0))) AS day_30_retention,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-07-05', day_60_retainusers, 0)), SUM(IF(cohort_date <= DATE '2026-07-05', new_users, 0))) AS day_60_retention,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-09-02', ltv_1, 0)), SUM(IF(cohort_date <= DATE '2026-09-02', new_users, 0))) AS source_ltv_1_per_new_user,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-09-01', ltv_2, 0)), SUM(IF(cohort_date <= DATE '2026-09-01', new_users, 0))) AS source_ltv_2_per_new_user,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-31', ltv_3, 0)), SUM(IF(cohort_date <= DATE '2026-08-31', new_users, 0))) AS source_ltv_3_per_new_user,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-30', ltv_4, 0)), SUM(IF(cohort_date <= DATE '2026-08-30', new_users, 0))) AS source_ltv_4_per_new_user,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-29', ltv_5, 0)), SUM(IF(cohort_date <= DATE '2026-08-29', new_users, 0))) AS source_ltv_5_per_new_user,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-28', ltv_6, 0)), SUM(IF(cohort_date <= DATE '2026-08-28', new_users, 0))) AS source_ltv_6_per_new_user,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-27', ltv_7, 0)), SUM(IF(cohort_date <= DATE '2026-08-27', new_users, 0))) AS source_ltv_7_per_new_user,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-26', ltv_8, 0)), SUM(IF(cohort_date <= DATE '2026-08-26', new_users, 0))) AS source_ltv_8_per_new_user,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-25', ltv_9, 0)), SUM(IF(cohort_date <= DATE '2026-08-25', new_users, 0))) AS source_ltv_9_per_new_user,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-24', ltv_10, 0)), SUM(IF(cohort_date <= DATE '2026-08-24', new_users, 0))) AS source_ltv_10_per_new_user,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-23', ltv_11, 0)), SUM(IF(cohort_date <= DATE '2026-08-23', new_users, 0))) AS source_ltv_11_per_new_user,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-22', ltv_12, 0)), SUM(IF(cohort_date <= DATE '2026-08-22', new_users, 0))) AS source_ltv_12_per_new_user,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-21', ltv_13, 0)), SUM(IF(cohort_date <= DATE '2026-08-21', new_users, 0))) AS source_ltv_13_per_new_user,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-20', ltv_14, 0)), SUM(IF(cohort_date <= DATE '2026-08-20', new_users, 0))) AS source_ltv_14_per_new_user,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-08-04', ltv_30, 0)), SUM(IF(cohort_date <= DATE '2026-08-04', new_users, 0))) AS source_ltv_30_per_new_user,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-07-05', ltv_60, 0)), SUM(IF(cohort_date <= DATE '2026-07-05', new_users, 0))) AS source_ltv_60_per_new_user,
  SAFE_DIVIDE(SUM(IF(cohort_date <= DATE '2026-06-05', ltv_90, 0)), SUM(IF(cohort_date <= DATE '2026-06-05', new_users, 0))) AS source_ltv_90_per_new_user,
  SUM(pay_users_count) AS pay_users_count,
  SUM(pay_amount) AS pay_amount,
  SAFE_DIVIDE(SUM(pay_users_count), SUM(new_users)) AS source_pay_user_rate,
  SAFE_DIVIDE(SUM(pay_amount), SUM(new_users)) AS source_pay_arpu,
  SAFE_DIVIDE(SUM(pay_amount), SUM(pay_users_count)) AS source_pay_arppu,
  SUM(first_pay_users) AS first_pay_users,
  SUM(first_pay_amount) AS first_pay_amount
FROM base
WHERE cohort_date BETWEEN DATE '2026-06-01' AND DATE '2026-09-02'
GROUP BY cohort_month, platform_group, channel, sub_channel
HAVING SUM(base.new_users) >= 10
ORDER BY cohort_month, new_users DESC
LIMIT 3000;
