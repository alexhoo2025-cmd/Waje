-- Exact download_channel=h5phx aggregate check in the Origin user view.
-- Only channel-level counts are returned.
WITH date_bounds AS (
  SELECT DATE '2026-08-27' AS event_date
)
SELECT
  target_day,
  LOWER(download_channel) AS observed_download_channel,
  COUNT(*) AS row_count,
  APPROX_COUNT_DISTINCT(IF(user_id IS NULL OR user_id = '', NULL, user_id)) AS approx_subject_count,
  COUNTIF(first_pay_date IS NOT NULL) AS first_pay_presence_count,
  COUNTIF(active_days IS NOT NULL AND active_days > 0) AS active_days_present_count
FROM `wajenigeria.origin_hfyl.user_events`
CROSS JOIN date_bounds
WHERE target_day BETWEEN event_date AND DATE '2026-09-01'
  AND LOWER(download_channel) IN ('h5phx', 'wajeh5phx', 'phenix')
GROUP BY target_day, observed_download_channel
HAVING APPROX_COUNT_DISTINCT(IF(user_id IS NULL OR user_id = '', NULL, user_id)) >= 10
ORDER BY target_day, observed_download_channel
LIMIT 3000
