-- Daily Android Performance metric recomputation.
-- P90 is NULL when the eligible sample count is below 500; no imputation is performed.
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
    COUNT(*) AS performance_record_count,
    COUNTIF(event_type = 'DURATION_TRACE' AND duration_ms >= 0) AS duration_sample_count,
    IF(
      COUNTIF(event_type = 'DURATION_TRACE' AND duration_ms >= 0) >= 500,
      APPROX_QUANTILES(IF(event_type = 'DURATION_TRACE' AND duration_ms >= 0, duration_ms, NULL), 100 IGNORE NULLS)[SAFE_OFFSET(90)],
      NULL
    ) AS duration_p90_ms,
    COUNTIF(event_type = 'SCREEN_TRACE') AS screen_trace_count,
    COUNTIF(event_type = 'SCREEN_TRACE' AND slow_frame_ratio BETWEEN 0 AND 1) AS slow_frame_valid_count,
    AVG(IF(event_type = 'SCREEN_TRACE' AND slow_frame_ratio BETWEEN 0 AND 1, slow_frame_ratio, NULL)) AS slow_frame_ratio_trace_mean,
    COUNTIF(event_type = 'SCREEN_TRACE' AND frozen_frame_ratio BETWEEN 0 AND 1) AS frozen_frame_valid_count,
    AVG(IF(event_type = 'SCREEN_TRACE' AND frozen_frame_ratio BETWEEN 0 AND 1, frozen_frame_ratio, NULL)) AS frozen_frame_ratio_trace_mean,
    COUNTIF(event_type = 'NETWORK_REQUEST') AS network_request_count,
    COUNTIF(event_type = 'NETWORK_REQUEST' AND response_code IS NOT NULL) AS network_response_count,
    COUNTIF(event_type = 'NETWORK_REQUEST' AND response_code BETWEEN 200 AND 399) AS network_success_count,
    SAFE_DIVIDE(
      COUNTIF(event_type = 'NETWORK_REQUEST' AND response_code BETWEEN 200 AND 399),
      COUNTIF(event_type = 'NETWORK_REQUEST' AND response_code IS NOT NULL)
    ) AS network_success_rate,
    COUNTIF(event_type = 'NETWORK_REQUEST' AND response_completed_ms >= 0) AS network_sample_count,
    IF(
      COUNTIF(event_type = 'NETWORK_REQUEST' AND response_completed_ms >= 0) >= 500,
      APPROX_QUANTILES(IF(event_type = 'NETWORK_REQUEST' AND response_completed_ms >= 0, response_completed_ms, NULL), 100 IGNORE NULLS)[SAFE_OFFSET(90)],
      NULL
    ) AS network_p90_ms,
    MAX(event_timestamp) AS data_cutoff_at
  FROM raw_performance
  GROUP BY metric_date_lagos, endpoint, app_package
)
SELECT
  metric_date_lagos,
  endpoint,
  app_package,
  performance_record_count,
  duration_sample_count,
  duration_p90_ms,
  screen_trace_count,
  slow_frame_valid_count,
  slow_frame_ratio_trace_mean,
  frozen_frame_valid_count,
  frozen_frame_ratio_trace_mean,
  network_request_count,
  network_response_count,
  network_success_count,
  network_success_rate,
  network_sample_count,
  network_p90_ms,
  data_cutoff_at,
  IF(metric_date_lagos < CURRENT_DATE('Africa/Lagos'), TRUE, FALSE) AS complete_day,
  CASE
    WHEN duration_sample_count < 500 AND network_sample_count < 500 THEN 'sample_too_small_for_both_p90'
    WHEN duration_sample_count < 500 THEN 'duration_p90_sample_too_small'
    WHEN network_sample_count < 500 THEN 'network_p90_sample_too_small'
    ELSE 'p90_eligible'
  END AS quality_status
FROM daily
ORDER BY metric_date_lagos, endpoint
LIMIT 3000;
