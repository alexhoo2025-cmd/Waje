-- Android Performance device and OS mix. Only aggregate groups with >=10 records are retained.
WITH raw_performance AS (
  SELECT
    'android_main' AS endpoint,
    'com.hfhy.waje.special' AS app_package,
    event_timestamp,
    COALESCE(NULLIF(device_name, ''), 'unknown') AS device_name,
    COALESCE(NULLIF(os_version, ''), 'unknown') AS os_version,
    event_type
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_waje_special_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-20' AND DATE '2026-08-26'

  UNION ALL

  SELECT
    'android_transsion_old',
    'com.hfhy.wajecasino.palmgame',
    event_timestamp,
    COALESCE(NULLIF(device_name, ''), 'unknown'),
    COALESCE(NULLIF(os_version, ''), 'unknown'),
    event_type
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_palmgame_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-20' AND DATE '2026-08-26'

  UNION ALL

  SELECT
    'android_transsion_new',
    'com.hfhy.wajecasino.game',
    event_timestamp,
    COALESCE(NULLIF(device_name, ''), 'unknown'),
    COALESCE(NULLIF(os_version, ''), 'unknown'),
    event_type
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_game_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-20' AND DATE '2026-08-26'
), grouped AS (
  SELECT
    DATE(event_timestamp, 'Africa/Lagos') AS metric_date_lagos,
    endpoint,
    app_package,
    device_name,
    os_version,
    COUNT(*) AS performance_record_count,
    COUNTIF(event_type = 'DURATION_TRACE') AS duration_trace_count,
    COUNTIF(event_type = 'SCREEN_TRACE') AS screen_trace_count,
    COUNTIF(event_type = 'NETWORK_REQUEST') AS network_request_count
  FROM raw_performance
  GROUP BY metric_date_lagos, endpoint, app_package, device_name, os_version
  HAVING COUNT(*) >= 10
)
SELECT
  metric_date_lagos,
  endpoint,
  app_package,
  device_name,
  os_version,
  performance_record_count,
  duration_trace_count,
  screen_trace_count,
  network_request_count,
  SAFE_DIVIDE(performance_record_count, SUM(performance_record_count) OVER (PARTITION BY metric_date_lagos, endpoint)) AS record_share
FROM grouped
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY metric_date_lagos, endpoint
  ORDER BY performance_record_count DESC, device_name, os_version
) <= 50
ORDER BY metric_date_lagos, endpoint, performance_record_count DESC
LIMIT 3000;
