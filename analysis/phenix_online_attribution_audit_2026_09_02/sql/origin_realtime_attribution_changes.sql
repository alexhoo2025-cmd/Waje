-- Origin realtime attribution-change coverage, aggregated by field name only.
-- Field values and user identifiers are intentionally omitted.
WITH date_bounds AS (
  SELECT DATE '2026-08-27' AS event_date
)
SELECT
  target_day,
  CASE
    WHEN REGEXP_CONTAINS(LOWER(COALESCE(field_name, '')), r'(email|phone|mobile|face|biometric|idfa|gaid|mac|device|user[_-]?id|identity)')
      THEN 'restricted_identity_or_device'
    WHEN REGEXP_CONTAINS(LOWER(COALESCE(field_name, '')), r'(channel|media|campaign|source|referrer|package|cpa|traffic|link)')
      THEN 'attribution_or_acquisition'
    ELSE 'other_attribute'
  END AS field_category,
  COALESCE(NULLIF(action_type, ''), '(blank)') AS action_type,
  COUNT(*) AS attribution_change_count,
  APPROX_COUNT_DISTINCT(IF(user_id IS NULL OR user_id = '', NULL, user_id)) AS approx_subject_count
FROM `wajenigeria.origin_hfyl.realtime_attribution_change`
CROSS JOIN date_bounds
WHERE target_day BETWEEN event_date AND DATE '2026-09-01'
GROUP BY target_day, field_name, action_type
HAVING APPROX_COUNT_DISTINCT(IF(user_id IS NULL OR user_id = '', NULL, user_id)) >= 10
ORDER BY target_day, attribution_change_count DESC, field_name
LIMIT 3000
