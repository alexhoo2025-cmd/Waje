WITH counts AS (
  SELECT event_name, COUNT(*) AS event_count
  FROM `waje-analytics-readonly.analytics_504208609.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260820' AND '20260824'
  GROUP BY event_name
)
SELECT
  event_name,
  event_count,
  ROUND(SAFE_DIVIDE(event_count, SUM(event_count) OVER ()) * 100, 2) AS event_share_pct
FROM counts
ORDER BY event_count DESC;
