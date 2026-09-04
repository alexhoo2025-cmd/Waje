-- Read-only administrator validation. Run after the mart refresh and view creation.
SELECT
  table_name,
  table_type,
  creation_time
FROM `wajenigeria.agent_analytics.INFORMATION_SCHEMA.TABLES`
WHERE table_name IN (
  'vw_firebase_endpoint_coverage_daily_safe',
  'vw_firebase_event_session_daily_safe',
  'vw_firebase_native_performance_daily_safe',
  'vw_firebase_stability_daily_safe',
  'vw_firebase_h5_behavior_daily_safe'
)
ORDER BY table_name;

SELECT
  table_name,
  ARRAY_AGG(column_name ORDER BY ordinal_position) AS columns
FROM `wajenigeria.agent_analytics.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name LIKE 'vw_firebase_%_safe'
GROUP BY table_name
ORDER BY table_name;

-- Expected: aggregate-only output, a complete-day flag, cutoff, status, and version.
SELECT
  metric_date_lagos,
  endpoint,
  app_package,
  quality_status,
  complete_day,
  data_cutoff_at,
  metric_definition_version
FROM `wajenigeria.agent_analytics.vw_firebase_endpoint_coverage_daily_safe`
WHERE metric_date_lagos BETWEEN DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 7 DAY)
  AND DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 1 DAY)
LIMIT 100;
