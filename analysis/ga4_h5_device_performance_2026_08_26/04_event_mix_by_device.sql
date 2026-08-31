WITH counts AS (
  SELECT
    COALESCE(device.category, '(not set)') AS device_category,
    event_name,
    COUNT(*) AS event_count
  FROM `waje-analytics-readonly.analytics_504208609.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260820' AND '20260824'
  GROUP BY 1, 2
)
SELECT
  device_category,
  event_name,
  event_count,
  ROUND(SAFE_DIVIDE(event_count, SUM(event_count) OVER (PARTITION BY device_category)) * 100, 2) AS event_share_within_device_pct
FROM counts
QUALIFY ROW_NUMBER() OVER (PARTITION BY device_category ORDER BY event_count DESC) <= 10
ORDER BY device_category, event_count DESC;
