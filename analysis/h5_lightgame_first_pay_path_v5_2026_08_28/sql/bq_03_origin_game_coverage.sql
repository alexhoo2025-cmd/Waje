SELECT
  app_id,
  client_type,
  COALESCE(NULLIF(package_channel, ''), '[blank]') AS package_channel,
  game_type,
  play_id,
  COUNT(*) AS game_start_events,
  APPROX_COUNT_DISTINCT(user_id) AS users,
  COUNTIF(SAFE_CAST(time AS INT64) IS NOT NULL) AS numeric_time_events,
  MIN(target_day) AS first_day,
  MAX(target_day) AS last_day
FROM `wajenigeria.origin_hfyl.view_metaevent_gamestart`
WHERE target_day BETWEEN DATE '2026-06-16' AND DATE '2026-08-25'
GROUP BY app_id, client_type, package_channel, game_type, play_id
HAVING users >= 30
ORDER BY users DESC;

