-- Native Firebase Performance aggregates for Android and the existing iOS
-- source. Trace/request names are not selected.
WITH raw_performance AS (
  SELECT
    'android_main' AS endpoint,
    'Android' AS platform,
    'com.hfhy.waje.special' AS app_package,
    event_timestamp,
    app_display_version,
    country,
    device_name,
    os_version,
    carrier,
    radio_type,
    event_type,
    network_info.response_code AS response_code,
    SAFE_DIVIDE(network_info.response_completed_time_us, 1000.0) AS response_completed_ms,
    SAFE_DIVIDE(trace_info.duration_us, 1000.0) AS duration_ms,
    trace_info.screen_info.slow_frame_ratio AS slow_frame_ratio,
    trace_info.screen_info.frozen_frame_ratio AS frozen_frame_ratio
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_waje_special_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '__PERF_START__' AND DATE '__PERF_END__'

  UNION ALL

  SELECT
    'android_transsion_old', 'Android', 'com.hfhy.wajecasino.palmgame', event_timestamp,
    app_display_version, country, device_name, os_version, carrier, radio_type, event_type,
    network_info.response_code, SAFE_DIVIDE(network_info.response_completed_time_us, 1000.0),
    SAFE_DIVIDE(trace_info.duration_us, 1000.0), trace_info.screen_info.slow_frame_ratio,
    trace_info.screen_info.frozen_frame_ratio
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_palmgame_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '__PERF_START__' AND DATE '__PERF_END__'

  UNION ALL

  SELECT
    'android_transsion_new', 'Android', 'com.hfhy.wajecasino.game', event_timestamp,
    app_display_version, country, device_name, os_version, carrier, radio_type, event_type,
    network_info.response_code, SAFE_DIVIDE(network_info.response_completed_time_us, 1000.0),
    SAFE_DIVIDE(trace_info.duration_us, 1000.0), trace_info.screen_info.slow_frame_ratio,
    trace_info.screen_info.frozen_frame_ratio
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_game_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '__PERF_START__' AND DATE '__PERF_END__'

  UNION ALL

  SELECT
    'ios_existing', 'iOS', 'com.wajegame.wajegame', event_timestamp,
    app_display_version, country, device_name, os_version, carrier, radio_type, event_type,
    network_info.response_code, SAFE_DIVIDE(network_info.response_completed_time_us, 1000.0),
    SAFE_DIVIDE(trace_info.duration_us, 1000.0), trace_info.screen_info.slow_frame_ratio,
    trace_info.screen_info.frozen_frame_ratio
  FROM `wajenigeria.waje_ng_firebase_ios_performance.com_wajegame_wajegame_IOS`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '__PERF_START__' AND DATE '__PERF_END__'
), daily AS (
  SELECT
    DATE(event_timestamp, 'Africa/Lagos') AS metric_date_lagos,
    endpoint,
    platform,
    app_package,
    COALESCE(NULLIF(app_display_version, ''), 'unknown') AS app_version,
    COUNT(*) AS performance_record_count,
    COUNTIF(event_type = 'DURATION_TRACE' AND duration_ms >= 0) AS duration_trace_count,
    COUNTIF(event_type = 'SCREEN_TRACE') AS screen_trace_count,
    COUNTIF(event_type = 'NETWORK_REQUEST') AS network_request_count,
    COUNTIF(event_type = 'NETWORK_REQUEST' AND response_code IS NOT NULL) AS network_response_count,
    COUNTIF(event_type = 'NETWORK_REQUEST' AND response_code BETWEEN 200 AND 399) AS network_success_count,
    IF(COUNTIF(event_type = 'DURATION_TRACE' AND duration_ms >= 0) >= 500,
      APPROX_QUANTILES(IF(event_type = 'DURATION_TRACE' AND duration_ms >= 0, duration_ms, NULL), 100 IGNORE NULLS)[SAFE_OFFSET(50)], NULL) AS duration_trace_p50_ms,
    IF(COUNTIF(event_type = 'DURATION_TRACE' AND duration_ms >= 0) >= 500,
      APPROX_QUANTILES(IF(event_type = 'DURATION_TRACE' AND duration_ms >= 0, duration_ms, NULL), 100 IGNORE NULLS)[SAFE_OFFSET(95)], NULL) AS duration_trace_p95_ms,
    IF(COUNTIF(event_type = 'DURATION_TRACE' AND duration_ms >= 0) >= 500,
      APPROX_QUANTILES(IF(event_type = 'DURATION_TRACE' AND duration_ms >= 0, duration_ms, NULL), 100 IGNORE NULLS)[SAFE_OFFSET(99)], NULL) AS duration_trace_p99_ms,
    IF(COUNTIF(event_type = 'NETWORK_REQUEST' AND response_completed_ms >= 0) >= 500,
      APPROX_QUANTILES(IF(event_type = 'NETWORK_REQUEST' AND response_completed_ms >= 0, response_completed_ms, NULL), 100 IGNORE NULLS)[SAFE_OFFSET(50)], NULL) AS network_p50_ms,
    IF(COUNTIF(event_type = 'NETWORK_REQUEST' AND response_completed_ms >= 0) >= 500,
      APPROX_QUANTILES(IF(event_type = 'NETWORK_REQUEST' AND response_completed_ms >= 0, response_completed_ms, NULL), 100 IGNORE NULLS)[SAFE_OFFSET(95)], NULL) AS network_p95_ms,
    IF(COUNTIF(event_type = 'NETWORK_REQUEST' AND response_completed_ms >= 0) >= 500,
      APPROX_QUANTILES(IF(event_type = 'NETWORK_REQUEST' AND response_completed_ms >= 0, response_completed_ms, NULL), 100 IGNORE NULLS)[SAFE_OFFSET(99)], NULL) AS network_p99_ms,
    AVG(IF(event_type = 'SCREEN_TRACE' AND slow_frame_ratio BETWEEN 0 AND 1, slow_frame_ratio, NULL)) AS slow_frame_ratio_trace_mean,
    AVG(IF(event_type = 'SCREEN_TRACE' AND frozen_frame_ratio BETWEEN 0 AND 1, frozen_frame_ratio, NULL)) AS frozen_frame_ratio_trace_mean,
    MAX(event_timestamp) AS data_cutoff_at
  FROM raw_performance
  GROUP BY metric_date_lagos, endpoint, platform, app_package, app_version
)
SELECT
  metric_date_lagos, endpoint, platform, app_package, app_version,
  performance_record_count, duration_trace_count, screen_trace_count,
  network_request_count, network_response_count, network_success_count,
  SAFE_DIVIDE(network_success_count, network_response_count) AS network_success_rate,
  duration_trace_p50_ms, duration_trace_p95_ms, duration_trace_p99_ms,
  network_p50_ms, network_p95_ms, network_p99_ms,
  slow_frame_ratio_trace_mean, frozen_frame_ratio_trace_mean,
  data_cutoff_at,
  metric_date_lagos < CURRENT_DATE('Africa/Lagos') AS complete_day,
  IF(duration_trace_count >= 500 AND network_request_count >= 500, 'eligible', 'sample_too_small') AS sample_status
FROM daily
ORDER BY metric_date_lagos, endpoint, app_package, app_version
LIMIT 500;
