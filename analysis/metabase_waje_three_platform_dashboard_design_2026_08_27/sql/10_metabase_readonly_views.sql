-- Admin-run only. Metabase should sync only these views and never raw Firebase/Origin tables.
CREATE OR REPLACE VIEW `wajenigeria.waje_device_performance_mart.vw_metabase_endpoint_health` AS
SELECT metric_date_lagos, endpoint, platform, app_package, source_name, source_record_count,
  distinct_session_count, network_request_count, data_cutoff_at, complete_day, quality_status
FROM `wajenigeria.waje_device_performance_mart.mart_endpoint_coverage_daily`;

CREATE OR REPLACE VIEW `wajenigeria.waje_device_performance_mart.vw_metabase_native_performance` AS
SELECT metric_date_lagos, endpoint, platform, app_package, app_version, country, device_name,
  os_version, carrier_bucket, network_type, performance_record_count, duration_sample_count,
  duration_p90_ms, screen_trace_count, slow_frame_ratio_trace_mean,
  frozen_frame_ratio_trace_mean, network_request_count, network_response_count,
  network_success_count, network_success_rate, network_sample_count, network_p90_ms,
  data_cutoff_at, complete_day, quality_status, metric_definition_version, source_name
FROM `wajenigeria.waje_device_performance_mart.mart_native_performance_daily`;

CREATE OR REPLACE VIEW `wajenigeria.waje_device_performance_mart.vw_metabase_event_session` AS
SELECT metric_date_lagos, endpoint, platform, app_package, app_version, event_name,
  event_category, event_count, session_start_event_count, event_data_cutoff_at,
  complete_day, quality_status
FROM `wajenigeria.waje_device_performance_mart.mart_event_session_daily`;

CREATE OR REPLACE VIEW `wajenigeria.waje_device_performance_mart.vw_metabase_stability_and_quality` AS
SELECT metric_date_lagos, endpoint, platform, app_package, app_version, issue_type,
  event_count, issue_count, distinct_event_id_count, data_cutoff_at, complete_day, quality_status
FROM `wajenigeria.waje_device_performance_mart.mart_stability_quality_daily`;

CREATE OR REPLACE VIEW `wajenigeria.waje_device_performance_mart.vw_metabase_native_performance_rank` AS
SELECT metric_date_lagos, endpoint, platform, app_package, app_version, rank_dimension,
  rank_value, performance_record_count, duration_sample_count, duration_p90_ms,
  network_sample_count, network_p90_ms, network_success_rate,
  slow_frame_ratio_trace_mean, frozen_frame_ratio_trace_mean, data_cutoff_at,
  complete_day, quality_status
FROM `wajenigeria.waje_device_performance_mart.mart_native_performance_rank_daily`;

CREATE OR REPLACE VIEW `wajenigeria.waje_device_performance_mart.vw_metabase_native_performance_15m` AS
SELECT metric_date_lagos, bucket_start_at, endpoint, platform, app_package,
  event_bucket, performance_record_count, response_code_count,
  network_success_count, data_cutoff_at
FROM `wajenigeria.waje_device_performance_mart.mart_native_performance_15m`;

-- vw_metabase_core_funnel remains intentionally uncreated until the approved
-- server-fact aggregate view is registered; the dashboard must show blocked.
