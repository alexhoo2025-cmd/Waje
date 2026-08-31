SELECT
  event_type,
  CAST(play_id AS STRING) AS play_id,
  COUNT(*) AS event_rows,
  APPROX_COUNT_DISTINCT(user_id) AS users,
  MIN(event_date) AS first_day,
  MAX(event_date) AS last_day
FROM (
  SELECT event_type, play_id, user_id, target_day AS event_date
  FROM `wajenigeria.origin_hfyl.view_metaevent_gamestart`
  WHERE app_id = 90006
    AND target_day BETWEEN DATE '2026-06-09' AND DATE '2026-08-10'
)
WHERE event_date BETWEEN DATE '2026-06-09' AND DATE '2026-08-10'
GROUP BY event_type, play_id
ORDER BY event_rows DESC;
