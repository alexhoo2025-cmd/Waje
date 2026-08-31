-- Single-dimension rank view. Percentiles are calculated from raw Performance
-- events in mart_native_performance_rank_daily, not from pre-aggregated percentiles.
CREATE OR REPLACE VIEW `wajenigeria.waje_device_performance_mart.vw_metabase_native_performance_rank` AS
SELECT
  metric_date_lagos,
  endpoint,
  platform,
  app_package,
  app_version,
  rank_dimension,
  rank_value,
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
FROM `wajenigeria.waje_device_performance_mart.mart_native_performance_rank_daily`;
