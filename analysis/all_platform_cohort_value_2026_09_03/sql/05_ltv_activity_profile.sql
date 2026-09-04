-- Aggregate-only profile of LTV and activity-retention aggregates by current dimensions.
WITH ltv_base AS (
  SELECT
    target_day AS cohort_date,
    app_id,
    data_type,
    download_channel,
    first_channel,
    first_sub_channel,
    ltv_1,
    ltv_7,
    ltv_14,
    ltv_30,
    ltv_60,
    ltv_90
  FROM `wajenigeria.track_hfyl.user_ltv`
), activity_base AS (
  SELECT
    target_day AS cohort_date,
    channel,
    sub_channel,
    traffic_source_type,
    new_users_today,
    today_newusers,
    day_2_retainusers,
    day_7_retainusers,
    day_14_retainusers,
    day_30_retainusers,
    day_60_retainusers,
    ltv_1,
    ltv_7,
    ltv_14,
    ltv_30,
    ltv_60,
    ltv_90,
    pay_users_count,
    pay_amount,
    first_pay_users,
    first_pay_amount
  FROM `wajenigeria.ares_hfyl.user_activety_indicators_downloadchannel`
)
SELECT
  'ltv_dimension' AS result_type,
  CAST(cohort_date AS STRING) AS target_day,
  CAST(app_id AS STRING) AS dimension_1,
  CAST(data_type AS STRING) AS dimension_2,
  COALESCE(NULLIF(download_channel, ''), '(blank)') AS dimension_3,
  COUNT(*) AS source_rows,
  SUM(COALESCE(ltv_1, 0)) AS metric_1,
  SUM(COALESCE(ltv_7, 0)) AS metric_7,
  SUM(COALESCE(ltv_14, 0)) AS metric_14,
  SUM(COALESCE(ltv_30, 0)) AS metric_30,
  SUM(COALESCE(ltv_60, 0)) AS metric_60,
  SUM(COALESCE(ltv_90, 0)) AS metric_90
FROM ltv_base
WHERE cohort_date BETWEEN DATE '2026-08-27' AND DATE '2026-09-02'
GROUP BY cohort_date, app_id, data_type, download_channel
UNION ALL
SELECT
  'activity_dimension' AS result_type,
  CAST(cohort_date AS STRING) AS target_day,
  COALESCE(NULLIF(channel, ''), '(blank)') AS dimension_1,
  COALESCE(NULLIF(sub_channel, ''), '(blank)') AS dimension_2,
  COALESCE(NULLIF(traffic_source_type, ''), '(blank)') AS dimension_3,
  COUNT(*) AS source_rows,
  SUM(COALESCE(today_newusers, new_users_today, 0)) AS metric_1,
  SUM(COALESCE(day_7_retainusers, 0)) AS metric_7,
  SUM(COALESCE(day_14_retainusers, 0)) AS metric_14,
  SUM(COALESCE(day_30_retainusers, 0)) AS metric_30,
  SUM(COALESCE(day_60_retainusers, 0)) AS metric_60,
  SUM(COALESCE(pay_amount, 0)) AS metric_90
FROM activity_base
WHERE cohort_date BETWEEN DATE '2026-08-27' AND DATE '2026-09-02'
GROUP BY cohort_date, channel, sub_channel, traffic_source_type
ORDER BY result_type, target_day, source_rows DESC
LIMIT 3000;
