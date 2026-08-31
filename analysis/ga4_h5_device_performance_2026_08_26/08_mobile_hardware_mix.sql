WITH base AS (
  SELECT
    COALESCE(device.mobile_brand_name, '(not set)') AS mobile_brand_name,
    COALESCE(device.mobile_model_name, '(not set)') AS mobile_model_name,
    COALESCE(device.operating_system_version, '(not set)') AS operating_system_version
  FROM `waje-analytics-readonly.analytics_504208609.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260820' AND '20260824'
    AND device.category = 'mobile'
),
counts AS (
  SELECT 'brand' AS dimension_group, mobile_brand_name AS dimension_value, COUNT(*) AS event_count
  FROM base GROUP BY 1, 2
  UNION ALL
  SELECT 'model', mobile_model_name, COUNT(*)
  FROM base GROUP BY 1, 2
  UNION ALL
  SELECT 'os_version', operating_system_version, COUNT(*)
  FROM base GROUP BY 1, 2
)
SELECT
  dimension_group,
  dimension_value,
  event_count,
  ROUND(SAFE_DIVIDE(event_count, SUM(event_count) OVER (PARTITION BY dimension_group)) * 100, 2) AS event_share_pct
FROM counts
QUALIFY ROW_NUMBER() OVER (PARTITION BY dimension_group ORDER BY event_count DESC) <= 15
ORDER BY dimension_group, event_count DESC;
