-- Formula and value-domain checks for Android Performance.
-- A returned row is a quality signal, not a user/device detail record.
WITH raw_performance AS (
  SELECT
    'android_main' AS endpoint,
    'com.hfhy.waje.special' AS app_package,
    event_timestamp,
    event_type,
    SAFE_DIVIDE(network_info.response_completed_time_us, 1000.0) AS response_completed_ms,
    SAFE_DIVIDE(trace_info.duration_us, 1000.0) AS duration_ms,
    trace_info.screen_info.slow_frame_ratio AS slow_frame_ratio,
    trace_info.screen_info.frozen_frame_ratio AS frozen_frame_ratio,
    network_info.response_code AS response_code
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_waje_special_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-20' AND DATE '2026-08-26'

  UNION ALL

  SELECT
    'android_transsion_old',
    'com.hfhy.wajecasino.palmgame',
    event_timestamp,
    event_type,
    SAFE_DIVIDE(network_info.response_completed_time_us, 1000.0),
    SAFE_DIVIDE(trace_info.duration_us, 1000.0),
    trace_info.screen_info.slow_frame_ratio,
    trace_info.screen_info.frozen_frame_ratio,
    network_info.response_code
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_palmgame_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-20' AND DATE '2026-08-26'

  UNION ALL

  SELECT
    'android_transsion_new',
    'com.hfhy.wajecasino.game',
    event_timestamp,
    event_type,
    SAFE_DIVIDE(network_info.response_completed_time_us, 1000.0),
    SAFE_DIVIDE(trace_info.duration_us, 1000.0),
    trace_info.screen_info.slow_frame_ratio,
    trace_info.screen_info.frozen_frame_ratio,
    network_info.response_code
  FROM `wajenigeria.waje_ng_firebase_android_performance.com_hfhy_wajecasino_game_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-20' AND DATE '2026-08-26'
), daily AS (
  SELECT
    DATE(event_timestamp, 'Africa/Lagos') AS metric_date_lagos,
    endpoint,
    app_package,
    COUNT(*) AS raw_record_count,
    COUNTIF(event_type IN ('DURATION_TRACE', 'SCREEN_TRACE', 'NETWORK_REQUEST', 'TRACE_METRIC')) AS supported_event_record_count,
    COUNTIF(event_type NOT IN ('DURATION_TRACE', 'SCREEN_TRACE', 'NETWORK_REQUEST', 'TRACE_METRIC') OR event_type IS NULL) AS unsupported_or_null_event_count,
    COUNTIF(event_type = 'DURATION_TRACE' AND duration_ms < 0) AS negative_duration_count,
    COUNTIF(event_type = 'NETWORK_REQUEST' AND response_completed_ms < 0) AS negative_network_latency_count,
    COUNTIF(event_type = 'SCREEN_TRACE' AND (slow_frame_ratio < 0 OR slow_frame_ratio > 1 OR frozen_frame_ratio < 0 OR frozen_frame_ratio > 1)) AS invalid_frame_ratio_count,
    COUNTIF(event_type = 'NETWORK_REQUEST' AND response_code IS NULL) AS missing_response_code_count,
    COUNTIF(event_type = 'DURATION_TRACE') + COUNTIF(event_type = 'SCREEN_TRACE') + COUNTIF(event_type = 'NETWORK_REQUEST') + COUNTIF(event_type = 'TRACE_METRIC') AS component_record_count
  FROM raw_performance
  GROUP BY metric_date_lagos, endpoint, app_package
)
SELECT
  metric_date_lagos,
  endpoint,
  app_package,
  raw_record_count,
  supported_event_record_count,
  unsupported_or_null_event_count,
  component_record_count,
  raw_record_count - supported_event_record_count - unsupported_or_null_event_count AS additive_reconciliation_delta,
  negative_duration_count,
  negative_network_latency_count,
  invalid_frame_ratio_count,
  missing_response_code_count,
  CASE
    WHEN raw_record_count = 0 THEN 'no_data'
    WHEN raw_record_count != component_record_count + unsupported_or_null_event_count THEN 'event_type_sum_mismatch'
    WHEN negative_duration_count > 0 OR negative_network_latency_count > 0 OR invalid_frame_ratio_count > 0 THEN 'value_domain_warning'
    ELSE 'basic_formula_checks_pass'
  END AS quality_status
FROM daily
ORDER BY metric_date_lagos, endpoint
LIMIT 3000;
