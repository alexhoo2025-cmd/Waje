-- The Agent Runtime identity receives BigQuery Data Viewer only on this dataset.
-- These views expose only daily/window aggregate facts; no source table is an Agent Runtime source.

CREATE OR REPLACE VIEW `wajenigeria.agent_analytics.vw_firebase_endpoint_coverage_daily_safe` AS
SELECT
  metric_date_lagos, endpoint, platform, app_package, source_name,
  source_record_count, distinct_session_count, session_start_event_count,
  event_name_count, data_cutoff_at, source_freshness_lag_minutes,
  complete_day, quality_status, quality_note, metric_definition_version
FROM `wajenigeria.waje_device_performance_mart.mart_endpoint_coverage_daily`;

CREATE OR REPLACE VIEW `wajenigeria.agent_analytics.vw_firebase_event_session_daily_safe` AS
SELECT
  metric_date_lagos,
  endpoint,
  platform,
  app_package,
  app_version,
  event_category,
  CASE
    WHEN event_name IN ('session_start', 'first_visit', 'first_open', 'user_engagement', 'page_view', 'screen_view', 'register', 'recharge', 'withdraw', 'firstCharge') THEN event_name
    WHEN STARTS_WITH(event_name, 'notification_') THEN 'notification_other'
    ELSE 'other'
  END AS event_name_bucket,
  SUM(event_count) AS event_count,
  SUM(session_start_event_count) AS session_start_event_count,
  CAST(NULL AS INT64) AS distinct_session_count,
  MAX(event_data_cutoff_at) AS data_cutoff_at,
  LOGICAL_AND(complete_day) AS complete_day,
  MAX(quality_status) AS quality_status,
  MAX(metric_definition_version) AS metric_definition_version
FROM `wajenigeria.waje_device_performance_mart.mart_event_session_daily`
GROUP BY metric_date_lagos, endpoint, platform, app_package, app_version, event_category, event_name_bucket;

CREATE OR REPLACE VIEW `wajenigeria.agent_analytics.vw_firebase_native_performance_daily_safe` AS
SELECT
  metric_date_lagos, endpoint, platform, app_package, app_version,
  'overview' AS analysis_dimension,
  'all' AS analysis_value,
  performance_record_count, duration_trace_count, duration_trace_p95_ms,
  screen_trace_count, slow_frame_ratio, frozen_frame_ratio,
  network_request_count, network_response_count, network_success_count,
  network_success_rate, network_p95_ms, data_cutoff_at, complete_day,
  quality_status, metric_definition_version
FROM `wajenigeria.waje_device_performance_mart.mart_native_performance_agent_overview_daily`
UNION ALL
SELECT
  metric_date_lagos, endpoint, platform, app_package, app_version,
  analysis_dimension, analysis_value, performance_record_count,
  duration_trace_count, duration_trace_p95_ms, screen_trace_count,
  slow_frame_ratio, frozen_frame_ratio, network_request_count,
  network_response_count, network_success_count, network_success_rate,
  network_p95_ms, data_cutoff_at, complete_day, quality_status,
  metric_definition_version
FROM `wajenigeria.waje_device_performance_mart.mart_native_performance_agent_rank_daily`;

CREATE OR REPLACE VIEW `wajenigeria.agent_analytics.vw_firebase_stability_daily_safe` AS
SELECT
  metric_date_lagos, endpoint, platform, app_package, app_version,
  CONCAT(device_manufacturer, ' / ', device_model) AS device_name_bucket,
  os_version,
  'fatal' AS error_type,
  crashlytics_export_record_count AS export_record_count,
  fatal_event_count AS dedup_event_count,
  issue_count,
  data_cutoff_at, complete_day, quality_status, quality_note,
  metric_definition_version
FROM `wajenigeria.waje_device_performance_mart.mart_stability_daily`
UNION ALL
SELECT
  metric_date_lagos, endpoint, platform, app_package, app_version,
  CONCAT(device_manufacturer, ' / ', device_model), os_version,
  'non_fatal', crashlytics_export_record_count, nonfatal_event_count,
  issue_count, data_cutoff_at, complete_day, quality_status, quality_note,
  metric_definition_version
FROM `wajenigeria.waje_device_performance_mart.mart_stability_daily`;

CREATE OR REPLACE VIEW `wajenigeria.agent_analytics.vw_firebase_h5_behavior_daily_safe` AS
WITH h5_behavior AS (
  SELECT
    metric_date_lagos, endpoint, app_package, app_version, event_category,
    event_name_bucket, event_count, data_cutoff_at, complete_day,
    metric_definition_version
  FROM `wajenigeria.agent_analytics.vw_firebase_event_session_daily_safe`
  WHERE endpoint = 'h5'
), h5_coverage AS (
  SELECT
    endpoint,
    app_package,
    COUNT(DISTINCT metric_date_lagos) AS covered_days
  FROM h5_behavior
  GROUP BY endpoint, app_package
)
SELECT
  h5.metric_date_lagos, h5.endpoint, h5.app_package, h5.app_version,
  h5.event_category, h5.event_name_bucket, h5.event_count,
  coverage.covered_days, h5.data_cutoff_at, h5.complete_day,
  'data_gap' AS quality_status,
  'H5 has Firebase behavior coverage only. Web Vitals, white/black screen, core request latency, client error, game_ready and bet_ready are not collected.' AS missing_reason,
  h5.metric_definition_version
FROM h5_behavior AS h5
JOIN h5_coverage AS coverage
  USING (endpoint, app_package);
