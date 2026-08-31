-- Admin-run scheduled query. All percentile and ratio calculations happen in BigQuery.
DECLARE refresh_start_date DATE DEFAULT DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 30 DAY);
DECLARE refresh_end_date DATE DEFAULT DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 1 DAY);

CREATE OR REPLACE TABLE `wajenigeria.waje_device_performance_mart.mart_native_performance_daily`
PARTITION BY metric_date_lagos
CLUSTER BY endpoint, app_package, app_version, country, device_name, os_version, network_type
AS
WITH raw_performance AS (
  SELECT 'android_main' AS endpoint, 'Android' AS platform, 'com.hfhy.waje.special' AS app_package, event_timestamp, app_display_version, country, device_name, os_version, carrier, radio_type, event_type, network_info.response_code AS response_code, SAFE_DIVIDE(network_info.response_completed_time_us, 1000.0) AS response_completed_ms, SAFE_DIVIDE(trace_info.duration_us, 1000.0) AS duration_ms, trace_info.screen_info.slow_frame_ratio AS slow_frame_ratio, trace_info.screen_info.frozen_frame_ratio AS frozen_frame_ratio
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_waje_special_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN refresh_start_date AND refresh_end_date
  UNION ALL
  SELECT 'android_transsion_old', 'Android', 'com.hfhy.wajecasino.palmgame', event_timestamp, app_display_version, country, device_name, os_version, carrier, radio_type, event_type, network_info.response_code, SAFE_DIVIDE(network_info.response_completed_time_us, 1000.0), SAFE_DIVIDE(trace_info.duration_us, 1000.0), trace_info.screen_info.slow_frame_ratio, trace_info.screen_info.frozen_frame_ratio
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_palmgame_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN refresh_start_date AND refresh_end_date
  UNION ALL
  SELECT 'android_transsion_new', 'Android', 'com.hfhy.wajecasino.game', event_timestamp, app_display_version, country, device_name, os_version, carrier, radio_type, event_type, network_info.response_code, SAFE_DIVIDE(network_info.response_completed_time_us, 1000.0), SAFE_DIVIDE(trace_info.duration_us, 1000.0), trace_info.screen_info.slow_frame_ratio, trace_info.screen_info.frozen_frame_ratio
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_game_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN refresh_start_date AND refresh_end_date
  UNION ALL
  SELECT 'ios_existing', 'iOS', 'com.wajegame.wajegame', event_timestamp, app_display_version, country, device_name, os_version, carrier, radio_type, event_type, network_info.response_code, SAFE_DIVIDE(network_info.response_completed_time_us, 1000.0), SAFE_DIVIDE(trace_info.duration_us, 1000.0), trace_info.screen_info.slow_frame_ratio, trace_info.screen_info.frozen_frame_ratio
  FROM `wajenigeria.waje_ng_firebase_ios_performance.com_wajegame_wajegame_IOS`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN refresh_start_date AND refresh_end_date
), normalized AS (
  SELECT
    DATE(event_timestamp, 'Africa/Lagos') AS metric_date_lagos,
    endpoint,
    platform,
    app_package,
    COALESCE(NULLIF(app_display_version, ''), 'unknown') AS app_version,
    COALESCE(NULLIF(country, ''), 'unknown') AS country,
    COALESCE(NULLIF(device_name, ''), 'unknown') AS device_name,
    COALESCE(NULLIF(os_version, ''), 'unknown') AS os_version,
    COALESCE(NULLIF(carrier, ''), 'unknown') AS carrier_bucket,
    COALESCE(NULLIF(radio_type, ''), 'unknown') AS network_type,
    event_timestamp,
    event_type,
    response_code,
    response_completed_ms,
    duration_ms,
    slow_frame_ratio,
    frozen_frame_ratio
  FROM raw_performance
  WHERE event_type IN ('DURATION_TRACE', 'SCREEN_TRACE', 'NETWORK_REQUEST', 'TRACE_METRIC')
)
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
  COUNT(*) AS performance_record_count,
  COUNTIF(event_type = 'DURATION_TRACE' AND duration_ms >= 0) AS duration_sample_count,
  IF(COUNTIF(event_type = 'DURATION_TRACE' AND duration_ms >= 0) >= 500, APPROX_QUANTILES(IF(event_type = 'DURATION_TRACE' AND duration_ms >= 0, duration_ms, NULL), 100 IGNORE NULLS)[SAFE_OFFSET(90)], NULL) AS duration_p90_ms,
  COUNTIF(event_type = 'SCREEN_TRACE') AS screen_trace_count,
  AVG(IF(event_type = 'SCREEN_TRACE' AND slow_frame_ratio BETWEEN 0 AND 1, slow_frame_ratio, NULL)) AS slow_frame_ratio_trace_mean,
  AVG(IF(event_type = 'SCREEN_TRACE' AND frozen_frame_ratio BETWEEN 0 AND 1, frozen_frame_ratio, NULL)) AS frozen_frame_ratio_trace_mean,
  COUNTIF(event_type = 'NETWORK_REQUEST') AS network_request_count,
  COUNTIF(event_type = 'NETWORK_REQUEST' AND response_code IS NOT NULL) AS network_response_count,
  COUNTIF(event_type = 'NETWORK_REQUEST' AND response_code BETWEEN 200 AND 399) AS network_success_count,
  SAFE_DIVIDE(COUNTIF(event_type = 'NETWORK_REQUEST' AND response_code BETWEEN 200 AND 399), COUNTIF(event_type = 'NETWORK_REQUEST' AND response_code IS NOT NULL)) AS network_success_rate,
  COUNTIF(event_type = 'NETWORK_REQUEST' AND response_completed_ms >= 0) AS network_sample_count,
  IF(COUNTIF(event_type = 'NETWORK_REQUEST' AND response_completed_ms >= 0) >= 500, APPROX_QUANTILES(IF(event_type = 'NETWORK_REQUEST' AND response_completed_ms >= 0, response_completed_ms, NULL), 100 IGNORE NULLS)[SAFE_OFFSET(90)], NULL) AS network_p90_ms,
  MAX(event_timestamp) AS data_cutoff_at,
  metric_date_lagos < CURRENT_DATE('Africa/Lagos') AS complete_day,
  CASE WHEN metric_date_lagos >= CURRENT_DATE('Africa/Lagos') - 6 THEN 'immature' ELSE 'provisional' END AS quality_status,
  'v1_p90' AS metric_definition_version,
  'firebase_performance' AS source_name,
  CURRENT_TIMESTAMP() AS refreshed_at
FROM normalized
GROUP BY metric_date_lagos, endpoint, platform, app_package, app_version, country, device_name, os_version, carrier_bucket, network_type;
