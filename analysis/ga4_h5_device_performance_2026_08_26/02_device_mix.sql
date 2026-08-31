WITH base AS (
  SELECT
    device.category AS device_category,
    device.operating_system AS operating_system,
    COALESCE(device.web_info.browser, device.browser, '(not set)') AS browser
  FROM `waje-analytics-readonly.analytics_504208609.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260820' AND '20260824'
),
counts AS (
  SELECT 'device_category' AS dimension_group, COALESCE(device_category, '(not set)') AS dimension_value, COUNT(*) AS event_count
  FROM base GROUP BY 1, 2
  UNION ALL
  SELECT 'operating_system', COALESCE(operating_system, '(not set)'), COUNT(*)
  FROM base GROUP BY 1, 2
  UNION ALL
  SELECT 'browser', browser, COUNT(*)
  FROM base GROUP BY 1, 2
)
SELECT
  dimension_group,
  dimension_value,
  event_count,
  ROUND(SAFE_DIVIDE(event_count, SUM(event_count) OVER (PARTITION BY dimension_group)) * 100, 2) AS event_share_pct
FROM counts
QUALIFY ROW_NUMBER() OVER (PARTITION BY dimension_group ORDER BY event_count DESC) <= 12
ORDER BY dimension_group, event_count DESC;
