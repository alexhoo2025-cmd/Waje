-- Android Analytics event/device mix. Event counts only; no user-level identifiers are returned.
WITH events AS (
  SELECT
    PARSE_DATE('%Y%m%d', _TABLE_SUFFIX) AS metric_date_lagos,
    COALESCE(NULLIF(app_info.id, ''), 'unknown') AS app_package,
    COALESCE(NULLIF(app_info.version, ''), 'unknown') AS app_version,
    COALESCE(NULLIF(device.category, ''), 'unknown') AS device_category,
    COALESCE(NULLIF(device.mobile_brand_name, ''), 'unknown') AS device_brand,
    COALESCE(NULLIF(device.mobile_model_name, ''), 'unknown') AS device_model,
    COALESCE(NULLIF(device.operating_system_version, ''), 'unknown') AS os_version,
    event_name
  FROM `wajenigeria.waje_ng_firebase_android.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260820' AND '20260826'
    AND platform = 'ANDROID'
    AND app_info.id IN (
      'com.hfhy.waje.special',
      'com.hfhy.wajecasino.palmgame',
      'com.hfhy.wajecasino.game'
    )
), grouped AS (
  SELECT
    metric_date_lagos,
    app_package,
    app_version,
    device_category,
    device_brand,
    device_model,
    os_version,
    event_name,
    COUNT(*) AS event_count
  FROM events
  GROUP BY metric_date_lagos, app_package, app_version, device_category, device_brand, device_model, os_version, event_name
  HAVING COUNT(*) >= 10
)
SELECT
  metric_date_lagos,
  app_package,
  app_version,
  device_category,
  device_brand,
  device_model,
  os_version,
  event_name,
  event_count,
  SAFE_DIVIDE(
    event_count,
    SUM(event_count) OVER (PARTITION BY metric_date_lagos, app_package)
  ) AS event_share_within_package_day
FROM grouped
ORDER BY metric_date_lagos, app_package, event_count DESC
LIMIT 3000;
