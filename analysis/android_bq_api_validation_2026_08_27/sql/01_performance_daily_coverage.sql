-- Daily Android Performance coverage. Aggregate-only; no trace name or URL is selected.
WITH raw_performance AS (
  SELECT
    'android_main' AS endpoint,
    'com.hfhy.waje.special' AS app_package,
    event_timestamp,
    app_display_version,
    event_type
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_waje_special_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-20' AND DATE '2026-08-26'

  UNION ALL

  SELECT
    'android_transsion_old',
    'com.hfhy.wajecasino.palmgame',
    event_timestamp,
    app_display_version,
    event_type
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_palmgame_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-20' AND DATE '2026-08-26'

  UNION ALL

  SELECT
    'android_transsion_new',
    'com.hfhy.wajecasino.game',
    event_timestamp,
    app_display_version,
    event_type
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_game_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-20' AND DATE '2026-08-26'
), daily AS (
  SELECT
    DATE(event_timestamp, 'Africa/Lagos') AS metric_date_lagos,
    endpoint,
    app_package,
    COUNT(*) AS performance_record_count,
    COUNTIF(event_type = 'DURATION_TRACE') AS duration_trace_count,
    COUNTIF(event_type = 'SCREEN_TRACE') AS screen_trace_count,
    COUNTIF(event_type = 'NETWORK_REQUEST') AS network_request_count,
    COUNTIF(event_type = 'TRACE_METRIC') AS trace_metric_count,
    COUNT(DISTINCT NULLIF(app_display_version, '')) AS app_version_count,
    MIN(event_timestamp) AS first_event_timestamp,
    MAX(event_timestamp) AS last_event_timestamp
  FROM raw_performance
  GROUP BY metric_date_lagos, endpoint, app_package
)
SELECT
  metric_date_lagos,
  endpoint,
  app_package,
  performance_record_count,
  duration_trace_count,
  screen_trace_count,
  network_request_count,
  trace_metric_count,
  app_version_count,
  first_event_timestamp,
  last_event_timestamp,
  IF(last_event_timestamp IS NULL, 'no_data', 'observed') AS coverage_status
FROM daily
ORDER BY metric_date_lagos, endpoint
LIMIT 3000;
