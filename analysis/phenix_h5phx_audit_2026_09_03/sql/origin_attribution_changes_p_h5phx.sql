-- Exact h5phx marker audit in Origin attribution changes.
-- Field names, field values and user identifiers are not returned.
WITH date_bounds AS (
  SELECT DATE '2026-08-27' AS event_date
)
SELECT
  target_day,
  COUNT(*) AS attribution_change_count,
  APPROX_COUNT_DISTINCT(IF(user_id IS NULL OR user_id = '', NULL, user_id)) AS approx_subject_count,
  COUNTIF(REGEXP_CONTAINS(LOWER(COALESCE(field_value, '')), r'(^|[^a-z0-9])(h5phx|phenix)([^a-z0-9]|$)')) AS h5phx_value_match_count
FROM `wajenigeria.origin_hfyl.realtime_attribution_change`
CROSS JOIN date_bounds
WHERE target_day BETWEEN event_date AND DATE '2026-09-01'
GROUP BY target_day
HAVING APPROX_COUNT_DISTINCT(IF(user_id IS NULL OR user_id = '', NULL, user_id)) >= 10
ORDER BY target_day
LIMIT 3000
