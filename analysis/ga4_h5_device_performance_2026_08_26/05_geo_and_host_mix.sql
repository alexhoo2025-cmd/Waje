WITH country_counts AS (
  SELECT 'country' AS dimension_group, COALESCE(geo.country, '(not set)') AS dimension_value, COUNT(*) AS event_count
  FROM `waje-analytics-readonly.analytics_504208609.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260820' AND '20260824'
  GROUP BY 1, 2
),
host_counts AS (
  SELECT 'hostname' AS dimension_group, COALESCE(device.web_info.hostname, event_dimensions.hostname, '(not set)') AS dimension_value, COUNT(*) AS event_count
  FROM `waje-analytics-readonly.analytics_504208609.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260820' AND '20260824'
  GROUP BY 1, 2
),
combined AS (
  SELECT * FROM country_counts
  UNION ALL
  SELECT * FROM host_counts
)
SELECT
  dimension_group,
  dimension_value,
  event_count,
  ROUND(SAFE_DIVIDE(event_count, SUM(event_count) OVER (PARTITION BY dimension_group)) * 100, 2) AS event_share_pct
FROM combined
QUALIFY ROW_NUMBER() OVER (PARTITION BY dimension_group ORDER BY event_count DESC) <= 12
ORDER BY dimension_group, event_count DESC;
