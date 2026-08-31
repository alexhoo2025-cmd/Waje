-- Read-only quality checks. Run after mart refreshes and before publishing a daily dashboard snapshot.

-- 1. Per-endpoint source coverage and freshness. A missing or delayed source is never displayed as zero.
SELECT
  metric_date_lagos,
  endpoint,
  app_package,
  source_name,
  source_record_count,
  distinct_session_count,
  session_start_event_count,
  data_cutoff_at,
  source_freshness_lag_minutes,
  complete_day,
  quality_status,
  quality_note
FROM `wajenigeria.waje_device_performance_mart.mart_endpoint_coverage_daily`
WHERE metric_date_lagos >= DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 14 DAY)
ORDER BY metric_date_lagos DESC, endpoint, source_name;

-- 2. Cross-end comparability gate: do not publish a cross-end trend unless each included endpoint has seven complete days.
SELECT
  endpoint,
  COUNT(DISTINCT metric_date_lagos) AS complete_day_count,
  MIN(metric_date_lagos) AS first_complete_day,
  MAX(metric_date_lagos) AS latest_complete_day,
  CASE WHEN COUNT(DISTINCT metric_date_lagos) >= 7 THEN 'eligible_for_endpoint_trend' ELSE 'immature_no_cross_endpoint_comparison' END AS comparison_status
FROM `wajenigeria.waje_device_performance_mart.mart_endpoint_coverage_daily`
WHERE source_name = 'firebase_analytics'
  AND complete_day
  AND metric_date_lagos >= DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 14 DAY)
GROUP BY endpoint;

-- 3. Android Sessions/Performance data-quality conflict. Actual Performance record presence takes precedence.
WITH session_flags AS (
  SELECT
    'android_main' AS endpoint,
    DATE(event_timestamp, 'Africa/Lagos') AS metric_date_lagos,
    LOGICAL_OR(performance_data_collection_enabled) AS session_flag_performance_enabled
  FROM `wajenigeria.waje_ng_firebase_android_sessions.com_hfhy_waje_special_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') >= DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 14 DAY)
  GROUP BY metric_date_lagos
  UNION ALL
  SELECT 'android_transsion_old', DATE(event_timestamp, 'Africa/Lagos'), LOGICAL_OR(performance_data_collection_enabled)
  FROM `wajenigeria.waje_ng_firebase_android_sessions.com_hfhy_wajecasino_palmgame_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') >= DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 14 DAY)
  GROUP BY metric_date_lagos
  UNION ALL
  SELECT 'android_transsion_new', DATE(event_timestamp, 'Africa/Lagos'), LOGICAL_OR(performance_data_collection_enabled)
  FROM `wajenigeria.waje_ng_firebase_android_sessions.com_hfhy_wajecasino_game_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') >= DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 14 DAY)
  GROUP BY metric_date_lagos
), performance_presence AS (
  SELECT metric_date_lagos, endpoint, SUM(performance_record_count) AS performance_record_count
  FROM `wajenigeria.waje_device_performance_mart.mart_native_performance_daily`
  WHERE metric_date_lagos >= DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 14 DAY)
  GROUP BY metric_date_lagos, endpoint
)
SELECT
  flags.metric_date_lagos,
  flags.endpoint,
  flags.session_flag_performance_enabled,
  COALESCE(performance.performance_record_count, 0) AS performance_record_count,
  CASE WHEN NOT flags.session_flag_performance_enabled AND COALESCE(performance.performance_record_count, 0) > 0 THEN 'quality_warning_flag_conflicts_with_performance_table' ELSE 'ok' END AS status
FROM session_flags AS flags
LEFT JOIN performance_presence AS performance
  USING (metric_date_lagos, endpoint)
ORDER BY metric_date_lagos DESC, endpoint;

-- 4. Percentile sample gate. NULL P95 is expected when a group has fewer than 500 eligible observations.
SELECT
  metric_date_lagos,
  endpoint,
  app_package,
  app_version,
  device_name,
  duration_trace_count,
  network_request_count,
  duration_trace_p95_ms,
  network_p95_ms,
  CASE WHEN duration_trace_count < 500 OR network_request_count < 500 THEN 'sample_too_small' ELSE 'eligible' END AS sample_status
FROM `wajenigeria.waje_device_performance_mart.mart_native_performance_daily`
WHERE metric_date_lagos >= DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 14 DAY);
