-- Exact daily single-dimension ranks calculated from raw Performance events.
-- This prevents a percentile-of-percentile error in device/version/network rankings.
DECLARE refresh_start_date DATE DEFAULT DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 30 DAY);
DECLARE refresh_end_date DATE DEFAULT DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 1 DAY);

CREATE TABLE IF NOT EXISTS `wajenigeria.waje_device_performance_mart.mart_native_performance_rank_daily` (
  metric_date_lagos DATE NOT NULL,
  endpoint STRING NOT NULL,
  platform STRING NOT NULL,
  app_package STRING NOT NULL,
  app_version STRING NOT NULL,
  rank_dimension STRING NOT NULL,
  rank_value STRING NOT NULL,
  performance_record_count INT64 NOT NULL,
  duration_trace_count INT64 NOT NULL,
  duration_trace_p95_ms FLOAT64,
  screen_trace_count INT64 NOT NULL,
  slow_frame_ratio_trace_mean FLOAT64,
  frozen_frame_ratio_trace_mean FLOAT64,
  network_request_count INT64 NOT NULL,
  network_response_count INT64 NOT NULL,
  network_success_count INT64 NOT NULL,
  network_success_rate FLOAT64,
  network_p95_ms FLOAT64,
  data_cutoff_at TIMESTAMP,
  complete_day BOOL NOT NULL,
  quality_status STRING NOT NULL,
  metric_definition_version STRING NOT NULL,
  refreshed_at TIMESTAMP NOT NULL
)
PARTITION BY metric_date_lagos
CLUSTER BY endpoint, app_package, app_version, rank_dimension, rank_value
OPTIONS(description = 'Exact raw-event performance percentile and rate aggregates for one ranking dimension at a time.');

DELETE FROM `wajenigeria.waje_device_performance_mart.mart_native_performance_rank_daily`
WHERE metric_date_lagos BETWEEN refresh_start_date AND refresh_end_date;

INSERT INTO `wajenigeria.waje_device_performance_mart.mart_native_performance_rank_daily`
WITH raw_performance AS (
  SELECT 'android_main' AS endpoint, 'Android' AS platform, 'com.hfhy.waje.special' AS app_package, event_timestamp, app_display_version, device_name, os_version, carrier, radio_type, event_type, network_info.response_code AS response_code, SAFE_DIVIDE(network_info.response_completed_time_us, 1000.0) AS response_completed_ms, SAFE_DIVIDE(trace_info.duration_us, 1000.0) AS duration_ms, trace_info.screen_info.slow_frame_ratio AS slow_frame_ratio, trace_info.screen_info.frozen_frame_ratio AS frozen_frame_ratio
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_waje_special_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN refresh_start_date AND refresh_end_date
  UNION ALL
  SELECT 'android_transsion_old', 'Android', 'com.hfhy.wajecasino.palmgame', event_timestamp, app_display_version, device_name, os_version, carrier, radio_type, event_type, network_info.response_code, SAFE_DIVIDE(network_info.response_completed_time_us, 1000.0), SAFE_DIVIDE(trace_info.duration_us, 1000.0), trace_info.screen_info.slow_frame_ratio, trace_info.screen_info.frozen_frame_ratio
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_palmgame_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN refresh_start_date AND refresh_end_date
  UNION ALL
  SELECT 'android_transsion_new', 'Android', 'com.hfhy.wajecasino.game', event_timestamp, app_display_version, device_name, os_version, carrier, radio_type, event_type, network_info.response_code, SAFE_DIVIDE(network_info.response_completed_time_us, 1000.0), SAFE_DIVIDE(trace_info.duration_us, 1000.0), trace_info.screen_info.slow_frame_ratio, trace_info.screen_info.frozen_frame_ratio
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_game_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN refresh_start_date AND refresh_end_date
  UNION ALL
  SELECT 'ios_existing', 'iOS', 'com.wajegame.wajegame', event_timestamp, app_display_version, device_name, os_version, carrier, radio_type, event_type, network_info.response_code, SAFE_DIVIDE(network_info.response_completed_time_us, 1000.0), SAFE_DIVIDE(trace_info.duration_us, 1000.0), trace_info.screen_info.slow_frame_ratio, trace_info.screen_info.frozen_frame_ratio
  FROM `wajenigeria.waje_ng_firebase_ios_performance.com_wajegame_wajegame_IOS`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN refresh_start_date AND refresh_end_date
), unpivoted AS (
  SELECT
    DATE(event_timestamp, 'Africa/Lagos') AS metric_date_lagos,
    endpoint,
    platform,
    app_package,
    COALESCE(NULLIF(app_display_version, ''), 'unknown') AS app_version,
    dimension.rank_dimension,
    dimension.rank_value,
    event_timestamp,
    event_type,
    response_code,
    response_completed_ms,
    duration_ms,
    slow_frame_ratio,
    frozen_frame_ratio
  FROM raw_performance,
  UNNEST([
    STRUCT('device_name' AS rank_dimension, COALESCE(NULLIF(device_name, ''), 'unknown') AS rank_value),
    STRUCT('os_version', COALESCE(NULLIF(os_version, ''), 'unknown')),
    STRUCT('network_type', COALESCE(NULLIF(radio_type, ''), 'unknown')),
    STRUCT('carrier_bucket', COALESCE(NULLIF(carrier, ''), 'unknown'))
  ]) AS dimension
)
SELECT
  metric_date_lagos,
  endpoint,
  platform,
  app_package,
  app_version,
  rank_dimension,
  rank_value,
  COUNT(*) AS performance_record_count,
  COUNTIF(event_type = 'DURATION_TRACE' AND duration_ms >= 0) AS duration_trace_count,
  IF(COUNTIF(event_type = 'DURATION_TRACE' AND duration_ms >= 0) >= 500, APPROX_QUANTILES(IF(event_type = 'DURATION_TRACE' AND duration_ms >= 0, duration_ms, NULL), 100 IGNORE NULLS)[SAFE_OFFSET(95)], NULL) AS duration_trace_p95_ms,
  COUNTIF(event_type = 'SCREEN_TRACE') AS screen_trace_count,
  AVG(IF(event_type = 'SCREEN_TRACE' AND slow_frame_ratio BETWEEN 0 AND 1, slow_frame_ratio, NULL)) AS slow_frame_ratio_trace_mean,
  AVG(IF(event_type = 'SCREEN_TRACE' AND frozen_frame_ratio BETWEEN 0 AND 1, frozen_frame_ratio, NULL)) AS frozen_frame_ratio_trace_mean,
  COUNTIF(event_type = 'NETWORK_REQUEST') AS network_request_count,
  COUNTIF(event_type = 'NETWORK_REQUEST' AND response_code IS NOT NULL) AS network_response_count,
  COUNTIF(event_type = 'NETWORK_REQUEST' AND response_code BETWEEN 200 AND 399) AS network_success_count,
  SAFE_DIVIDE(COUNTIF(event_type = 'NETWORK_REQUEST' AND response_code BETWEEN 200 AND 399), COUNTIF(event_type = 'NETWORK_REQUEST' AND response_code IS NOT NULL)) AS network_success_rate,
  IF(COUNTIF(event_type = 'NETWORK_REQUEST' AND response_completed_ms >= 0) >= 500, APPROX_QUANTILES(IF(event_type = 'NETWORK_REQUEST' AND response_completed_ms >= 0, response_completed_ms, NULL), 100 IGNORE NULLS)[SAFE_OFFSET(95)], NULL) AS network_p95_ms,
  MAX(event_timestamp) AS data_cutoff_at,
  metric_date_lagos < CURRENT_DATE('Africa/Lagos') AS complete_day,
  IF(metric_date_lagos >= CURRENT_DATE('Africa/Lagos') - 6, 'immature', 'provisional') AS quality_status,
  'v1' AS metric_definition_version,
  CURRENT_TIMESTAMP() AS refreshed_at
FROM unpivoted
GROUP BY metric_date_lagos, endpoint, platform, app_package, app_version, rank_dimension, rank_value, complete_day, quality_status;
