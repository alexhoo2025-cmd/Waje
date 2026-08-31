-- Native Performance single-dimension breakdown. Values are aggregate
-- dimensions (device model, OS, country, carrier, network), not unique IDs.
WITH raw_performance AS (
  SELECT 'android_main' AS endpoint, 'Android' AS platform, 'com.hfhy.waje.special' AS app_package, event_timestamp, app_display_version, country, device_name, os_version, carrier, radio_type, event_type, network_info.response_code AS response_code, SAFE_DIVIDE(network_info.response_completed_time_us, 1000.0) AS response_completed_ms, SAFE_DIVIDE(trace_info.duration_us, 1000.0) AS duration_ms
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_waje_special_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '__PERF_START__' AND DATE '__PERF_END__'
  UNION ALL
  SELECT 'android_transsion_old', 'Android', 'com.hfhy.wajecasino.palmgame', event_timestamp, app_display_version, country, device_name, os_version, carrier, radio_type, event_type, network_info.response_code, SAFE_DIVIDE(network_info.response_completed_time_us, 1000.0), SAFE_DIVIDE(trace_info.duration_us, 1000.0)
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_palmgame_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '__PERF_START__' AND DATE '__PERF_END__'
  UNION ALL
  SELECT 'android_transsion_new', 'Android', 'com.hfhy.wajecasino.game', event_timestamp, app_display_version, country, device_name, os_version, carrier, radio_type, event_type, network_info.response_code, SAFE_DIVIDE(network_info.response_completed_time_us, 1000.0), SAFE_DIVIDE(trace_info.duration_us, 1000.0)
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_game_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '__PERF_START__' AND DATE '__PERF_END__'
  UNION ALL
  SELECT 'ios_existing', 'iOS', 'com.wajegame.wajegame', event_timestamp, app_display_version, country, device_name, os_version, carrier, radio_type, event_type, network_info.response_code, SAFE_DIVIDE(network_info.response_completed_time_us, 1000.0), SAFE_DIVIDE(trace_info.duration_us, 1000.0)
  FROM `wajenigeria.waje_ng_firebase_ios_performance.com_wajegame_wajegame_IOS`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '__PERF_START__' AND DATE '__PERF_END__'
), expanded AS (
  SELECT
    DATE(event_timestamp, 'Africa/Lagos') AS metric_date_lagos,
    endpoint, platform, app_package,
    COALESCE(NULLIF(app_display_version, ''), 'unknown') AS app_version,
    dimension.rank_dimension,
    dimension.rank_value,
    event_type, response_code, response_completed_ms, duration_ms
  FROM raw_performance,
  UNNEST([
    STRUCT('device_name' AS rank_dimension, COALESCE(NULLIF(device_name, ''), 'unknown') AS rank_value),
    STRUCT('os_version', COALESCE(NULLIF(os_version, ''), 'unknown')),
    STRUCT('country', COALESCE(NULLIF(country, ''), 'unknown')),
    STRUCT('carrier_bucket', COALESCE(NULLIF(carrier, ''), 'unknown')),
    STRUCT('network_type', COALESCE(NULLIF(radio_type, ''), 'unknown'))
  ]) AS dimension
), aggregate AS (
  -- Window-level Top 10 per endpoint/package/ranking dimension. This is a
  -- compact diagnostic summary, not a downloadable event/detail table.
  SELECT
    endpoint,
    platform,
    app_package,
    'all_versions' AS app_version,
    rank_dimension,
    rank_value,
    COUNT(*) AS performance_record_count,
    COUNTIF(event_type = 'DURATION_TRACE' AND duration_ms >= 0) AS duration_trace_count,
    COUNTIF(event_type = 'NETWORK_REQUEST') AS network_request_count,
    COUNTIF(event_type = 'NETWORK_REQUEST' AND response_code IS NOT NULL) AS network_response_count,
    COUNTIF(event_type = 'NETWORK_REQUEST' AND response_code BETWEEN 200 AND 399) AS network_success_count,
    SAFE_DIVIDE(COUNTIF(event_type = 'NETWORK_REQUEST' AND response_code BETWEEN 200 AND 399), COUNTIF(event_type = 'NETWORK_REQUEST' AND response_code IS NOT NULL)) AS network_success_rate,
    IF(COUNTIF(event_type = 'DURATION_TRACE' AND duration_ms >= 0) >= 500, APPROX_QUANTILES(IF(event_type = 'DURATION_TRACE' AND duration_ms >= 0, duration_ms, NULL), 100 IGNORE NULLS)[SAFE_OFFSET(95)], NULL) AS duration_trace_p95_ms,
    IF(COUNTIF(event_type = 'NETWORK_REQUEST' AND response_completed_ms >= 0) >= 500, APPROX_QUANTILES(IF(event_type = 'NETWORK_REQUEST' AND response_completed_ms >= 0, response_completed_ms, NULL), 100 IGNORE NULLS)[SAFE_OFFSET(95)], NULL) AS network_p95_ms,
    IF(COUNT(*) >= 500, 'eligible', 'sample_too_small') AS sample_status
  FROM expanded
  GROUP BY endpoint, platform, app_package, rank_dimension, rank_value
  HAVING COUNT(*) >= 10
), ranked AS (
  SELECT aggregate.*, ROW_NUMBER() OVER (PARTITION BY endpoint, app_package, rank_dimension ORDER BY performance_record_count DESC, rank_value) AS rank_position
  FROM aggregate
)
SELECT
  endpoint, platform, app_package, app_version, rank_dimension, rank_value,
  performance_record_count, duration_trace_count, network_request_count,
  network_response_count, network_success_count, network_success_rate,
  duration_trace_p95_ms, network_p95_ms, sample_status
FROM ranked
WHERE rank_position <= 10
ORDER BY endpoint, rank_dimension, rank_position
LIMIT 500;
