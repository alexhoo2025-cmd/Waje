-- Aggregate-only Android Performance API smoke test for one complete Lagos day.
SELECT
  DATE(event_timestamp, 'Africa/Lagos') AS metric_date_lagos,
  'android_main' AS endpoint,
  'com.hfhy.waje.special' AS app_package,
  COUNT(*) AS performance_record_count,
  COUNTIF(event_type = 'DURATION_TRACE') AS duration_trace_count,
  COUNTIF(event_type = 'SCREEN_TRACE') AS screen_trace_count,
  COUNTIF(event_type = 'NETWORK_REQUEST') AS network_request_count,
  COUNT(DISTINCT NULLIF(app_display_version, '')) AS app_version_count,
  MAX(event_timestamp) AS data_cutoff_at
FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_waje_special_ANDROID`
WHERE DATE(event_timestamp, 'Africa/Lagos') = DATE '2026-08-26'
GROUP BY metric_date_lagos
LIMIT 100;
