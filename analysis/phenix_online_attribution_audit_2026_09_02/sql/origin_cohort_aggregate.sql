-- Origin cohort retention aggregate cross-check for the Phenix window.
-- Retention fields are precomputed aggregate ratios; no cohort user rows are returned.
WITH date_bounds AS (
  SELECT DATE '2026-08-27' AS event_date
), cohort AS (
  SELECT
    'new_user' AS cohort_type,
    target_day,
    download_channel,
    initial_user_count,
    d2_retention,
    d3_retention,
    d7_retention
  FROM `wajenigeria.bigdata.daily_new_user_retention`
  CROSS JOIN date_bounds
  WHERE target_day BETWEEN event_date AND DATE '2026-09-02'
  UNION ALL
  SELECT
    'first_pay' AS cohort_type,
    target_day,
    download_channel,
    initial_user_count,
    d2_retention,
    d3_retention,
    d7_retention
  FROM `wajenigeria.bigdata.first_pay_retention`
  CROSS JOIN date_bounds
  WHERE target_day BETWEEN event_date AND DATE '2026-09-02'
)
SELECT
  cohort_type,
  target_day,
  download_channel,
  SUM(initial_user_count) AS cohort_users,
  SAFE_DIVIDE(
    SUM(IF(d2_retention IS NOT NULL, initial_user_count * d2_retention, 0)),
    SUM(IF(d2_retention IS NOT NULL, initial_user_count, 0))
  ) AS weighted_d2_retention,
  SAFE_DIVIDE(
    SUM(IF(d3_retention IS NOT NULL, initial_user_count * d3_retention, 0)),
    SUM(IF(d3_retention IS NOT NULL, initial_user_count, 0))
  ) AS weighted_d3_retention,
  SAFE_DIVIDE(
    SUM(IF(d7_retention IS NOT NULL, initial_user_count * d7_retention, 0)),
    SUM(IF(d7_retention IS NOT NULL, initial_user_count, 0))
  ) AS weighted_d7_retention,
  COUNT(*) AS source_row_count
FROM cohort
GROUP BY cohort_type, target_day, download_channel
ORDER BY cohort_type, target_day, download_channel
