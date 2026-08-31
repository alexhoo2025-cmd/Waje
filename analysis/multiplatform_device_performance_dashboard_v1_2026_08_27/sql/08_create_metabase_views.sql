-- These views are the only intended Metabase source objects.
-- Grant Metabase read access only to this dataset after data-owner review.

CREATE OR REPLACE VIEW `wajenigeria.waje_device_performance_mart.vw_metabase_endpoint_health` AS
SELECT
  metric_date_lagos,
  endpoint,
  platform,
  app_package,
  source_name,
  source_record_count,
  distinct_session_count,
  session_start_event_count,
  event_name_count,
  data_cutoff_at,
  source_freshness_lag_minutes,
  complete_day,
  quality_status,
  quality_note,
  metric_definition_version
FROM `wajenigeria.waje_device_performance_mart.mart_endpoint_coverage_daily`;

CREATE OR REPLACE VIEW `wajenigeria.waje_device_performance_mart.vw_metabase_native_performance` AS
SELECT
  metric_date_lagos,
  endpoint,
  platform,
  app_package,
  app_version,
  country,
  device_name,
  os_version,
  carrier_bucket,
  network_type,
  performance_record_count,
  duration_trace_count,
  duration_trace_p95_ms,
  screen_trace_count,
  slow_frame_ratio_trace_mean,
  frozen_frame_ratio_trace_mean,
  network_request_count,
  network_response_count,
  network_success_count,
  network_success_rate,
  network_p95_ms,
  data_cutoff_at,
  complete_day,
  quality_status,
  metric_definition_version
FROM `wajenigeria.waje_device_performance_mart.mart_native_performance_daily`;

CREATE OR REPLACE VIEW `wajenigeria.waje_device_performance_mart.vw_metabase_event_session` AS
SELECT
  metric_date_lagos,
  endpoint,
  platform,
  app_package,
  firebase_stream_id,
  app_version,
  event_category,
  core_role,
  include_in_engagement,
  include_in_client_behavior_funnel,
  SUM(event_count) AS event_count,
  SUM(session_start_event_count) AS session_start_event_count,
  MAX(event_data_cutoff_at) AS data_cutoff_at,
  LOGICAL_AND(complete_day) AS complete_day,
  MAX(quality_status) AS quality_status,
  metric_definition_version
FROM `wajenigeria.waje_device_performance_mart.mart_event_session_daily`
GROUP BY metric_date_lagos, endpoint, platform, app_package, firebase_stream_id, app_version,
  event_category, core_role, include_in_engagement, include_in_client_behavior_funnel, metric_definition_version;

CREATE OR REPLACE VIEW `wajenigeria.waje_device_performance_mart.vw_metabase_core_funnel` AS
SELECT
  metric_date_lagos,
  endpoint,
  platform,
  app_package,
  app_version,
  funnel_stage,
  stage_kind,
  stage_event_count,
  source_is_server,
  business_success_confirmed,
  data_cutoff_at,
  complete_day,
  quality_status,
  quality_note,
  metric_definition_version
FROM `wajenigeria.waje_device_performance_mart.mart_core_funnel_daily`
UNION ALL
SELECT
  metric_date_lagos,
  endpoint,
  NULL AS platform,
  NULL AS app_package,
  NULL AS app_version,
  metric_name AS funnel_stage,
  'status' AS stage_kind,
  NULL AS stage_event_count,
  FALSE AS source_is_server,
  FALSE AS business_success_confirmed,
  NULL AS data_cutoff_at,
  FALSE AS complete_day,
  status AS quality_status,
  CONCAT(reason, ' | ', owner_action) AS quality_note,
  'v1' AS metric_definition_version
FROM `wajenigeria.waje_device_performance_mart.mart_metric_status`
WHERE metric_domain = 'core_funnel';

CREATE OR REPLACE VIEW `wajenigeria.waje_device_performance_mart.vw_metabase_stability_and_quality` AS
SELECT
  metric_date_lagos,
  endpoint,
  platform,
  app_package,
  'crashlytics_export_coverage' AS metric_domain,
  CAST(crashlytics_export_record_count AS FLOAT64) AS metric_value,
  data_cutoff_at,
  complete_day,
  quality_status,
  quality_note,
  metric_definition_version
FROM `wajenigeria.waje_device_performance_mart.mart_stability_daily`
UNION ALL
SELECT
  metric_date_lagos,
  endpoint,
  platform,
  app_package,
  'fatal_event_count' AS metric_domain,
  CAST(fatal_event_count AS FLOAT64) AS metric_value,
  data_cutoff_at,
  complete_day,
  quality_status,
  quality_note,
  metric_definition_version
FROM `wajenigeria.waje_device_performance_mart.mart_stability_daily`
UNION ALL
SELECT
  metric_date_lagos,
  endpoint,
  platform,
  app_package,
  'nonfatal_event_count' AS metric_domain,
  CAST(nonfatal_event_count AS FLOAT64) AS metric_value,
  data_cutoff_at,
  complete_day,
  quality_status,
  quality_note,
  metric_definition_version
FROM `wajenigeria.waje_device_performance_mart.mart_stability_daily`
UNION ALL
SELECT
  metric_date_lagos,
  endpoint,
  platform,
  app_package,
  'issue_count' AS metric_domain,
  CAST(issue_count AS FLOAT64) AS metric_value,
  data_cutoff_at,
  complete_day,
  quality_status,
  quality_note,
  metric_definition_version
FROM `wajenigeria.waje_device_performance_mart.mart_stability_daily`
UNION ALL
SELECT
  metric_date_lagos,
  endpoint,
  NULL AS platform,
  NULL AS app_package,
  metric_domain,
  NULL AS metric_value,
  NULL AS data_cutoff_at,
  FALSE AS complete_day,
  status AS quality_status,
  CONCAT(reason, ' | ', owner_action) AS quality_note,
  'v1' AS metric_definition_version
FROM `wajenigeria.waje_device_performance_mart.mart_metric_status`
WHERE metric_domain IN ('performance', 'stability', 'data_quality', 'source_mapping');

CREATE OR REPLACE VIEW `wajenigeria.waje_device_performance_mart.vw_metabase_native_performance_15m` AS
SELECT
  bucket_start_utc,
  endpoint,
  platform,
  app_package,
  app_version,
  trace_category,
  performance_record_count,
  duration_trace_count,
  network_request_count,
  network_response_count,
  network_success_count,
  latest_event_timestamp,
  source_freshness_lag_minutes,
  freshness_status,
  metric_definition_version
FROM `wajenigeria.waje_device_performance_mart.mart_native_performance_15m`;
