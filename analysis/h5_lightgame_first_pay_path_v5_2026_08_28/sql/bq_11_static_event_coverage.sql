SELECT
  `事件类型` AS event_type,
  COUNT(*) AS event_rows,
  APPROX_COUNT_DISTINCT(`用户id`) AS users,
  MIN(`事件发生时间`) AS first_event_time,
  MAX(`事件发生时间`) AS last_event_time
FROM `wajenigeria.pubwaje.user-events_2026-07-10_2026-08-10`
GROUP BY event_type
ORDER BY event_rows DESC;

