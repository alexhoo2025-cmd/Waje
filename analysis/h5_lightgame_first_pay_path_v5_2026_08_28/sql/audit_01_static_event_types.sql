SELECT
  `事件类型` AS event_type,
  COUNT(*) AS event_rows
FROM (
  SELECT `事件类型`, `事件发生时间` AS event_time
  FROM `wajenigeria.pubwaje.user-events_2026-07-10_2026-08-10`
  WHERE DATE(`事件发生时间`, 'Africa/Lagos') BETWEEN DATE '2026-07-10' AND DATE '2026-08-10'
)
WHERE DATE(event_time, 'Africa/Lagos') BETWEEN DATE '2026-07-10' AND DATE '2026-08-10'
GROUP BY event_type
ORDER BY event_rows DESC
LIMIT 100;
