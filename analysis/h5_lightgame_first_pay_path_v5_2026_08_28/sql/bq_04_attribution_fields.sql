SELECT
  app_id,
  field_name,
  COALESCE(NULLIF(field_value, ''), '[blank]') AS field_value,
  action_type,
  COUNT(*) AS records,
  APPROX_COUNT_DISTINCT(user_id) AS users,
  MIN(target_day) AS first_day,
  MAX(target_day) AS last_day
FROM `wajenigeria.origin_hfyl.realtime_attribution_change`
WHERE target_day BETWEEN DATE '2026-06-16' AND DATE '2026-08-10'
GROUP BY app_id, field_name, field_value, action_type
HAVING users >= 30
ORDER BY users DESC;

