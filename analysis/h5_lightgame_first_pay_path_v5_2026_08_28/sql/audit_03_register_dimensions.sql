SELECT
  client_type,
  COALESCE(NULLIF(package_channel, ''), '(blank)') AS package_channel,
  COUNT(*) AS register_events,
  APPROX_COUNT_DISTINCT(user_id) AS users,
  MIN(event_date) AS first_day,
  MAX(event_date) AS last_day
FROM (
  SELECT client_type, package_channel, user_id, target_day AS event_date
  FROM `wajenigeria.origin_hfyl.view_metaevent_register`
  WHERE app_id = 90006
    AND target_day BETWEEN DATE '2026-06-16' AND DATE '2026-08-10'
)
WHERE event_date BETWEEN DATE '2026-06-16' AND DATE '2026-08-10'
GROUP BY client_type, package_channel
HAVING users >= 10
ORDER BY register_events DESC;
