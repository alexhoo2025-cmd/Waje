SELECT
  event_name,
  COUNT(*) AS event_rows,
  APPROX_COUNT_DISTINCT(user_pseudo_id) AS users
FROM `waje-analytics-readonly.analytics_504208609.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20260821' AND '20260827'
GROUP BY event_name
ORDER BY event_rows DESC
LIMIT 100;
