-- Admin-run scheduled query. Unpivots one approved ranking dimension at a time.
-- The source is already aggregate-only; no raw event or unique device identifier is exposed.
CREATE OR REPLACE TABLE `wajenigeria.waje_device_performance_mart.mart_native_performance_rank_daily`
PARTITION BY metric_date_lagos
CLUSTER BY endpoint, rank_dimension, rank_value
AS
WITH base AS (
  SELECT
    metric_date_lagos,
    endpoint,
    platform,
    app_package,
    app_version,
    performance_record_count,
    duration_sample_count,
    duration_p90_ms,
    network_sample_count,
    network_p90_ms,
    network_success_rate,
    slow_frame_ratio_trace_mean,
    frozen_frame_ratio_trace_mean,
    data_cutoff_at,
    complete_day,
    quality_status,
    device_name,
    os_version,
    network_type,
    carrier_bucket
  FROM `wajenigeria.waje_device_performance_mart.mart_native_performance_daily`
  WHERE metric_date_lagos BETWEEN DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 30 DAY) AND DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 1 DAY)
)
SELECT metric_date_lagos, endpoint, platform, app_package, app_version, 'device_name' AS rank_dimension, device_name AS rank_value, performance_record_count, duration_sample_count, duration_p90_ms, network_sample_count, network_p90_ms, network_success_rate, slow_frame_ratio_trace_mean, frozen_frame_ratio_trace_mean, data_cutoff_at, complete_day, quality_status
FROM base
UNION ALL
SELECT metric_date_lagos, endpoint, platform, app_package, app_version, 'os_version', os_version, performance_record_count, duration_sample_count, duration_p90_ms, network_sample_count, network_p90_ms, network_success_rate, slow_frame_ratio_trace_mean, frozen_frame_ratio_trace_mean, data_cutoff_at, complete_day, quality_status
FROM base
UNION ALL
SELECT metric_date_lagos, endpoint, platform, app_package, app_version, 'network_type', network_type, performance_record_count, duration_sample_count, duration_p90_ms, network_sample_count, network_p90_ms, network_success_rate, slow_frame_ratio_trace_mean, frozen_frame_ratio_trace_mean, data_cutoff_at, complete_day, quality_status
FROM base
UNION ALL
SELECT metric_date_lagos, endpoint, platform, app_package, app_version, 'carrier_bucket', carrier_bucket, performance_record_count, duration_sample_count, duration_p90_ms, network_sample_count, network_p90_ms, network_success_rate, slow_frame_ratio_trace_mean, frozen_frame_ratio_trace_mean, data_cutoff_at, complete_day, quality_status
FROM base;
